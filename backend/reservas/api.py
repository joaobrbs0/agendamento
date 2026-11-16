from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BLOQUEIAM, Reserva, Veiculo
from .serializers import ReservaSerializer, VeiculoSerializer

PERMISSAO_GESTOR = "reservas.aprovar_reserva"


def eh_gestor(user):
    return user.has_perm(PERMISSAO_GESTOR)


def _data(valor, nome):
    dt = parse_datetime(valor)
    if dt is None:
        raise serializers.ValidationError({nome: "Data inválida."})
    return timezone.make_aware(dt) if timezone.is_naive(dt) else dt


def _km(request):
    try:
        km = int(request.data.get("km"))
    except (TypeError, ValueError):
        raise serializers.ValidationError({"km": "Informe a quilometragem."})
    if km < 0:
        raise serializers.ValidationError({"km": "Quilometragem inválida."})
    return km


class EuView(APIView):
    """Dados do usuário logado; o front usa para saber se mostra o painel do gestor."""

    def get(self, request):
        u = request.user
        return Response({
            "id": u.id,
            "usuario": u.get_username(),
            "nome": u.get_full_name() or u.get_username(),
            "gestor": eh_gestor(u),
        })


class VeiculoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Veiculo.objects.filter(ativo=True).order_by("modelo")
    serializer_class = VeiculoSerializer


class ReservaViewSet(mixins.CreateModelMixin, mixins.ListModelMixin,
                     mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Gestor vê tudo. Os demais veem as próprias reservas e as que bloqueiam
    veículo (aprovadas e em uso), para o calendário mostrar a disponibilidade.

    Filtros na listagem: ?veiculo=ID  ?status=pendente,aprovada  ?minhas=1
    ?inicio=...&fim=... (reservas que encostam nesse intervalo, ISO 8601)
    """
    serializer_class = ReservaSerializer

    def get_queryset(self):
        u = self.request.user
        qs = Reserva.objects.select_related("veiculo", "solicitante")
        if not eh_gestor(u):
            qs = qs.filter(Q(solicitante=u) | Q(status__in=BLOQUEIAM))
        p = self.request.query_params
        if p.get("veiculo", "").isdigit():
            qs = qs.filter(veiculo_id=int(p["veiculo"]))
        if p.get("status"):
            qs = qs.filter(status__in=p["status"].split(","))
        if p.get("minhas") == "1":
            qs = qs.filter(solicitante=u)
        if p.get("inicio") and p.get("fim"):
            qs = qs.filter(periodo__overlap=DateTimeTZRange(
                _data(p["inicio"], "inicio"), _data(p["fim"], "fim")))
        return qs.order_by("-criado_em")

    # --- ações ---------------------------------------------------------

    def _exigir_gestor(self):
        if not eh_gestor(self.request.user):
            raise PermissionDenied("Você não tem permissão para esta ação.")

    def _rodar(self, reserva, acao):
        try:
            acao(reserva)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"detail": " ".join(e.messages)})
        reserva.refresh_from_db()
        return Response(self.get_serializer(reserva).data)

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        self._exigir_gestor()
        return self._rodar(self.get_object(), lambda r: r.aprovar(request.user))

    @action(detail=True, methods=["post"])
    def recusar(self, request, pk=None):
        self._exigir_gestor()
        motivo = str(request.data.get("motivo", ""))[:300]
        return self._rodar(
            self.get_object(), lambda r: r.recusar(request.user, motivo))

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        r = self.get_object()
        if r.solicitante_id != request.user.id and not eh_gestor(request.user):
            raise PermissionDenied("Só quem pediu a reserva pode cancelá-la.")
        return self._rodar(r, lambda x: x.cancelar())

    @action(detail=True, methods=["post"])
    def retirar(self, request, pk=None):
        self._exigir_gestor()
        km = _km(request)
        return self._rodar(self.get_object(), lambda r: r.retirar(km))

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        self._exigir_gestor()
        km = _km(request)
        return self._rodar(self.get_object(), lambda r: r.devolver(km))
