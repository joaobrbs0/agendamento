"""Interface de teste: calendário compartilhado no Google Agenda.

    pip install flask google-api-python-client google-auth-oauthlib
    python auth.py     # uma vez
    python app.py      # abre a porta 5000
"""
import calendar
import os
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, flash, redirect, render_template_string, request, url_for
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TZ = "America/Sao_Paulo"
CAL_FILE = "calendar_id.txt"
CAL_NAME = "Agenda Compartilhada "
PAPEIS = {"owner": "dono", "writer": "edita", "reader": "só vê",
          "freeBusyReader": "só ocupado/livre"}
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]

app = Flask(__name__)
app.secret_key = "teste-local"


def servico():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(Request())
        with open("token.json", "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def agenda_id(svc):
    """Usa a agenda salva ou cria uma nova na primeira vez."""
    if os.path.exists(CAL_FILE):
        return open(CAL_FILE).read().strip()
    cal = svc.calendars().insert(body={"summary": CAL_NAME, "timeZone": TZ}).execute()
    with open(CAL_FILE, "w") as f:
        f.write(cal["id"])
    return cal["id"]


def motivo(e):
    return getattr(e, "reason", None) or str(e)


@app.route("/")
def index():
    tz = ZoneInfo(TZ)
    hoje = date.today()

    # mês exibido (?mes=2026-11) e dia selecionado (?dia=2026-11-05)
    try:
        ano, m = map(int, request.args.get("mes", f"{hoje:%Y-%m}").split("-"))
        date(ano, m, 1)
    except ValueError:
        ano, m = hoje.year, hoje.month
    mes_atual = f"{ano:04d}-{m:02d}"
    try:
        dia = date.fromisoformat(request.args.get("dia", "")).isoformat()
    except ValueError:
        dia = ""

    ant = f"{date(ano, m, 1) - timedelta(days=1):%Y-%m}"
    prox = f"{date(ano, m, 28) + timedelta(days=4):%Y-%m}"

    semanas = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, m)
    t_min = datetime.combine(semanas[0][0], time.min, tzinfo=tz).isoformat()
    t_max = datetime.combine(semanas[-1][-1] + timedelta(days=1), time.min,
                             tzinfo=tz).isoformat()

    svc = servico()
    cid = agenda_id(svc)
    itens = svc.events().list(
        calendarId=cid, timeMin=t_min, timeMax=t_max, singleEvents=True,
        orderBy="startTime", maxResults=250,
    ).execute().get("items", [])

    por_dia = {}
    for e in itens:
        ini = e["start"].get("dateTime")
        if ini:
            i = datetime.fromisoformat(ini).astimezone(tz)
            f = datetime.fromisoformat(e["end"]["dateTime"]).astimezone(tz)
            d, hora = i.date(), f"{i:%H:%M} às {f:%H:%M}"
        else:
            d, hora = date.fromisoformat(e["start"]["date"]), "dia inteiro"
        por_dia.setdefault(d.isoformat(), []).append({
            "id": e["id"], "titulo": e.get("summary", "(sem título)"),
            "hora": hora, "desc": e.get("description", ""),
        })

    celulas = []
    for semana in semanas:
        for d in semana:
            iso = d.isoformat()
            qtd = len(por_dia.get(iso, []))
            celulas.append({
                "iso": iso, "dia": d.day, "mes": f"{d:%Y-%m}", "qtd": qtd,
                "fora": d.month != m, "hoje": d == hoje, "sel": iso == dia,
                "rotulo": f"{d.day} de {MESES[d.month - 1]}, "
                          + (f"{qtd} evento{'s' if qtd > 1 else ''}" if qtd else "sem eventos"),
            })

    chaves = [dia] if dia else sorted(k for k in por_dia if k.startswith(mes_atual))
    lista = [(f"{DIAS[date.fromisoformat(k).weekday()]}, {date.fromisoformat(k):%d/%m/%Y}",
              por_dia[k]) for k in chaves if por_dia.get(k)]
    titulo_lista = (f"Eventos de {date.fromisoformat(dia):%d/%m/%Y}" if dia
                    else f"Eventos de {MESES[m - 1]}")

    acl = svc.acl().list(calendarId=cid).execute().get("items", [])
    pessoas = [{"email": a["scope"].get("value", ""),
                "papel": PAPEIS.get(a["role"], a["role"])}
               for a in acl if a["scope"]["type"] == "user"]

    return render_template_string(
        PAGINA, nome=CAL_NAME, pessoas=pessoas, celulas=celulas, lista=lista,
        titulo_lista=titulo_lista, titulo_mes=f"{MESES[m - 1]} de {ano}",
        ant=ant, prox=prox, mes_atual=mes_atual, dia=dia,
        form_dia=dia or hoje.isoformat(),
    )


@app.post("/evento")
def novo_evento():
    f = request.form
    if f["fim"] <= f["inicio"]:
        flash("O horário de fim precisa ser depois do início.")
        return redirect(url_for("index", mes=f["dia"][:7], dia=f["dia"]))
    try:
        svc = servico()
        svc.events().insert(calendarId=agenda_id(svc), body={
            "summary": f["titulo"], "description": f.get("descricao", ""),
            "start": {"dateTime": f"{f['dia']}T{f['inicio']}:00", "timeZone": TZ},
            "end": {"dateTime": f"{f['dia']}T{f['fim']}:00", "timeZone": TZ},
        }).execute()
        flash("Evento salvo.")
    except HttpError as e:
        flash(f"Não foi possível salvar o evento: {motivo(e)}")
    return redirect(url_for("index", mes=f["dia"][:7], dia=f["dia"]))


@app.post("/evento/<eid>/excluir")
def excluir(eid):
    try:
        svc = servico()
        svc.events().delete(calendarId=agenda_id(svc), eventId=eid).execute()
        flash("Evento excluído.")
    except HttpError as e:
        flash(f"Não foi possível excluir: {motivo(e)}")
    return redirect(url_for("index", mes=request.form.get("mes") or None,
                            dia=request.form.get("dia") or None))


@app.post("/compartilhar")
def compartilhar():
    f = request.form
    try:
        svc = servico()
        svc.acl().insert(calendarId=agenda_id(svc), sendNotifications=True, body={
            "role": f["papel"], "scope": {"type": "user", "value": f["email"].strip()},
        }).execute()
        flash(f"Agenda compartilhada com {f['email'].strip()}.")
    except HttpError as e:
        flash(f"Não foi possível compartilhar: {motivo(e)}")
    return redirect(url_for("index"))


PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ nome }}</title>
<style>
  :root{--bg:#eef2f4;--ink:#14202b;--mute:#5b6b78;--line:#d3dce2;--card:#fff;--acc:#0b6e69;--bad:#b3261e}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
  header{padding:28px 24px 8px;max-width:1040px;margin:0 auto}
  h1{margin:0;font-size:1.6rem;letter-spacing:-.01em}
  header p{margin:4px 0 0;color:var(--mute)}
  a{color:var(--acc)}
  main{display:grid;grid-template-columns:320px 1fr;gap:24px;max-width:1040px;margin:16px auto 48px;padding:0 24px}
  @media(max-width:820px){main{grid-template-columns:1fr}}
  section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin-bottom:20px}
  h2{margin:0 0 12px;font-size:1.05rem}
  label{display:block;font-size:.9rem;color:var(--mute);margin:10px 0 4px}
  input,select,textarea{width:100%;padding:8px 10px;font:inherit;color:var(--ink);background:#fff;border:1px solid var(--line);border-radius:6px}
  input:focus,select:focus,textarea:focus,button:focus-visible,a:focus-visible{outline:2px solid var(--acc);outline-offset:1px}
  .par{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  button{margin-top:14px;padding:9px 14px;font:inherit;font-weight:600;color:#fff;background:var(--acc);border:0;border-radius:6px;cursor:pointer}
  button.sec{margin:0;padding:4px 10px;font-weight:500;color:var(--bad);background:none;border:1px solid var(--line)}
  .aviso{background:#fff8e1;border:1px solid #ecd58a;border-radius:8px;padding:10px 14px;margin-bottom:16px}
  .topo{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
  .topo h2{margin:0;text-transform:capitalize}
  .nav{padding:0 12px;font-size:1.4rem;line-height:1.6;text-decoration:none;border:1px solid var(--line);border-radius:6px}
  .grade{display:grid;grid-template-columns:repeat(7,1fr);gap:4px}
  .cab{text-align:center;font-size:.8rem;color:var(--mute);padding:2px 0}
  .dia-c{display:flex;flex-direction:column;justify-content:space-between;min-height:62px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;color:var(--ink);text-decoration:none;background:#fff}
  .dia-c.fora{background:transparent;color:#8fa0ac}
  .dia-c.tem{background:#e0f0ee;border-color:#8fc4be;font-weight:700}
  .dia-c.hoje{box-shadow:inset 0 0 0 2px var(--ink)}
  .dia-c.sel{outline:3px solid var(--acc);outline-offset:1px}
  .q{align-self:flex-end;min-width:22px;text-align:center;font-size:.75rem;font-weight:600;color:#fff;background:var(--acc);border-radius:999px;padding:0 7px}
  @media(max-width:520px){.dia-c{min-height:46px;padding:4px 5px}}
  .leg{margin:10px 0 0;font-size:.88rem;color:var(--mute)}
  .dia{margin:14px 0 4px;font-size:.95rem;font-weight:700}
  .evento{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;padding:10px 0;border-top:1px solid var(--line)}
  .evento strong{display:block}
  .evento span,.vazio,.pessoa span{color:var(--mute);font-size:.92rem}
  .pessoa{display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid var(--line)}
  .pessoa:first-of-type{border-top:0}
</style></head><body>
<header>
  <h1>{{ nome }}</h1>
  <p>Eventos criados aqui aparecem no Google Agenda de quem tem acesso. <a href="https://calendar.google.com/calendar/u/0/r" target="_blank" rel="noopener">Abrir o Google Agenda</a></p>
</header>
<main>
  <div>
    {% with msgs = get_flashed_messages() %}{% for m in msgs %}<div class="aviso">{{ m }}</div>{% endfor %}{% endwith %}
    <section>
      <h2>Novo evento</h2>
      <form method="post" action="/evento">
        <label for="titulo">Título</label><input id="titulo" name="titulo" required>
        <label for="dia">Dia</label><input id="dia" name="dia" type="date" value="{{ form_dia }}" required>
        <div class="par">
          <div><label for="inicio">Início</label><input id="inicio" name="inicio" type="time" value="14:00" required></div>
          <div><label for="fim">Fim</label><input id="fim" name="fim" type="time" value="15:00" required></div>
        </div>
        <label for="descricao">Descrição (opcional)</label><textarea id="descricao" name="descricao" rows="2"></textarea>
        <button>Salvar evento</button>
      </form>
    </section>
    <section>
      <h2>Compartilhar a agenda</h2>
      <form method="post" action="/compartilhar">
        <label for="email">E-mail da pessoa</label><input id="email" name="email" type="email" required>
        <label for="papel">Permissão</label>
        <select id="papel" name="papel">
          <option value="reader">Só vê os eventos</option>
          <option value="writer">Cria e edita eventos</option>
        </select>
        <button>Compartilhar</button>
      </form>
    </section>
  </div>
  <div>
    <section>
      <div class="topo">
        <a class="nav" href="{{ url_for('index', mes=ant) }}" aria-label="Mês anterior">&lsaquo;</a>
        <h2>{{ titulo_mes }}</h2>
        <a class="nav" href="{{ url_for('index', mes=prox) }}" aria-label="Próximo mês">&rsaquo;</a>
      </div>
      <div class="grade">
        {% for n in ['dom','seg','ter','qua','qui','sex','sáb'] %}<div class="cab">{{ n }}</div>{% endfor %}
        {% for c in celulas %}
          <a class="dia-c{% if c.fora %} fora{% endif %}{% if c.qtd %} tem{% endif %}{% if c.hoje %} hoje{% endif %}{% if c.sel %} sel{% endif %}"
             href="{{ url_for('index', mes=c.mes, dia=c.iso) }}" aria-label="{{ c.rotulo }}">
            <span>{{ c.dia }}</span>{% if c.qtd %}<span class="q">{{ c.qtd }}</span>{% endif %}
          </a>
        {% endfor %}
      </div>
      <p class="leg">Dias com evento ficam destacados e mostram a quantidade. Clique em um dia para ver os eventos e criar um novo nele.
        {% if dia %}<a href="{{ url_for('index', mes=mes_atual) }}">Ver o mês todo</a>{% endif %}</p>
    </section>
    <section>
      <h2>{{ titulo_lista }}</h2>
      {% for rotulo, evs in lista %}
        {% if not dia %}<div class="dia">{{ rotulo }}</div>{% endif %}
        {% for e in evs %}
          <div class="evento">
            <div><strong>{{ e.titulo }}</strong><span>{{ e.hora }}{% if e.desc %} · {{ e.desc }}{% endif %}</span></div>
            <form method="post" action="/evento/{{ e.id }}/excluir">
              <input type="hidden" name="mes" value="{{ mes_atual }}"><input type="hidden" name="dia" value="{{ dia }}">
              <button class="sec">Excluir</button>
            </form>
          </div>
        {% endfor %}
      {% else %}
        <p class="vazio">{{ 'Nenhum evento neste dia.' if dia else 'Nenhum evento neste mês.' }} Use o formulário ao lado para criar um.</p>
      {% endfor %}
    </section>
    <section>
      <h2>Quem tem acesso</h2>
      {% for p in pessoas %}<div class="pessoa">{{ p.email }}<span>{{ p.papel }}</span></div>{% endfor %}
    </section>
  </div>
</main>
</body></html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
