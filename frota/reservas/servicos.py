"""Espelha as reservas aprovadas no Google Agenda (uma agenda por veículo).

Usa só uma conta de serviço (sem Workspace e sem delegação). A agenda do
veículo pertence à conta de serviço e é compartilhada com o solicitante,
que a recebe ao lado das agendas dele.

O banco é a fonte da verdade: se o Google falhar, a reserva continua válida
e o erro só vai para o log.

Em settings.py:
    GOOGLE_SA_FILE = "/caminho/fora/do/repo/google_sa.json"  # chave da conta de serviço
"""
import logging

from django.conf import settings
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .models import Reserva

log = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
TZ = "America/Sao_Paulo"


def _svc():
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_SA_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _agenda_do_veiculo(svc, veiculo):
    """Cria a agenda do veículo na primeira vez e guarda o ID."""
    if not veiculo.google_calendar_id:
        cal = svc.calendars().insert(body={
            "summary": f"Frota - {veiculo.modelo} ({veiculo.placa})",
            "timeZone": TZ,
        }).execute()
        veiculo.google_calendar_id = cal["id"]
        veiculo.save(update_fields=["google_calendar_id"])
    return veiculo.google_calendar_id


def _compartilhar(svc, cal_id, email, papel="writer"):
    """Dá acesso à agenda do veículo (e atualiza o papel se já tinha acesso)."""
    try:
        svc.acl().insert(
            calendarId=cal_id,
            body={"role": papel, "scope": {"type": "user", "value": email}},
            sendNotifications=True,
        ).execute()
    except HttpError as e:
        if e.resp.status != 409:
            raise
        # já tinha acesso: atualiza o papel
        svc.acl().patch(
            calendarId=cal_id,
            ruleId=f"user:{email}",
            body={"role": papel},
        ).execute()


def espelhar(reserva_id):
    try:
        r = Reserva.objects.select_related("veiculo", "solicitante").get(pk=reserva_id)
        if r.status != Reserva.Status.APROVADA or r.google_event_id:
            return
        svc = _svc()
        cal_id = _agenda_do_veiculo(svc, r.veiculo)
        nome = r.solicitante.get_full_name() or r.solicitante.get_username()
        corpo = {
            "summary": f"{r.veiculo.placa} - {nome}",
            "description": f"Destino: {r.destino}\nPassageiros: {r.passageiros}",
            "start": {"dateTime": r.periodo.lower.isoformat(), "timeZone": TZ},
            "end": {"dateTime": r.periodo.upper.isoformat(), "timeZone": TZ},
        }
        if r.solicitante.email:
            _compartilhar(svc, cal_id, r.solicitante.email)
        ev = svc.events().insert(calendarId=cal_id, body=corpo).execute()
        Reserva.objects.filter(pk=r.pk).update(google_event_id=ev["id"])
    except Exception:
        log.exception("Falha ao espelhar a reserva %s no Google Agenda", reserva_id)


def remover(reserva_id):
    try:
        r = Reserva.objects.select_related("veiculo").get(pk=reserva_id)
        if not (r.google_event_id and r.veiculo.google_calendar_id):
            return
        try:
            _svc().events().delete(
                calendarId=r.veiculo.google_calendar_id,
                eventId=r.google_event_id,
            ).execute()
        except HttpError as e:
            if e.resp.status not in (404, 410):  # já apagado no Google
                raise
        Reserva.objects.filter(pk=r.pk).update(google_event_id="")
    except Exception:
        log.exception("Falha ao remover a reserva %s do Google Agenda", reserva_id)
