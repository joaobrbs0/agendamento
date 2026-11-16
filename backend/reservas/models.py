from django.conf import settings
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.db.models import Q
from django.utils import timezone


BLOQUEIAM = ["aprovada", "em_uso"]


class Veiculo(models.Model):
    placa = models.CharField(max_length=8, unique=True)
    modelo = models.CharField(max_length=80)
    ativo = models.BooleanField(default=True)
    google_calendar_id = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.modelo} ({self.placa})"


class Reserva(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADA = "aprovada", "Aprovada"
        EM_USO = "em_uso", "Em uso"
        CONCLUIDA = "concluida", "Concluída"
        RECUSADA = "recusada", "Recusada"
        CANCELADA = "cancelada", "Cancelada"

    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT)
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reservas")
    periodo = DateTimeRangeField()
    destino = models.CharField(max_length=200)
    passageiros = models.PositiveSmallIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices,
                              default=Status.PENDENTE)

    decidido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="reservas_decididas")
    decidido_em = models.DateTimeField(null=True, blank=True)
    motivo_recusa = models.CharField(max_length=300, blank=True)

    km_saida = models.PositiveIntegerField(null=True, blank=True)
    km_retorno = models.PositiveIntegerField(null=True, blank=True)

    google_event_id = models.CharField(max_length=100, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [("aprovar_reserva", "Pode aprovar ou recusar reservas")]
        constraints = [ExclusionConstraint(
            name="sem_sobreposicao_por_veiculo",
            expressions=[("veiculo", RangeOperators.EQUAL),
                         ("periodo", RangeOperators.OVERLAPS)],
            condition=Q(status__in=BLOQUEIAM),
        )]

    def __str__(self):
        return f"{self.veiculo} - {self.solicitante} ({self.status})"

    def clean(self):
        p = self.periodo
        if not (p and p.lower and p.upper):
            raise ValidationError("Informe início e fim.")
        if p.upper <= p.lower:
            raise ValidationError("O fim precisa ser depois do início.")
        if p.lower < timezone.now():
            raise ValidationError("O início não pode estar no passado.")
        conflito = Reserva.objects.filter(
            veiculo=self.veiculo, status__in=BLOQUEIAM, periodo__overlap=p,
        ).exclude(pk=self.pk)
        if conflito.exists():
            raise ValidationError("O veículo já está reservado nesse período.")



    def _exigir(self, *permitidos):
        if self.status not in permitidos:
            raise ValidationError(f"Ação inválida para uma reserva {self.status}.")

    def aprovar(self, gestor):
        from . import servicos
        self._exigir(self.Status.PENDENTE)
        self.status = self.Status.APROVADA
        self.decidido_por, self.decidido_em = gestor, timezone.now()
        try:
            with transaction.atomic():
                self.save(update_fields=["status", "decidido_por", "decidido_em"])
        except IntegrityError:
            self.status = self.Status.PENDENTE
            raise ValidationError(
                "Já existe uma reserva aprovada para esse veículo nesse período.")
        transaction.on_commit(lambda: servicos.espelhar(self.pk))

    def recusar(self, gestor, motivo=""):
        self._exigir(self.Status.PENDENTE)
        self.status = self.Status.RECUSADA
        self.decidido_por, self.decidido_em = gestor, timezone.now()
        self.motivo_recusa = motivo
        self.save(update_fields=["status", "decidido_por", "decidido_em", "motivo_recusa"])

    def cancelar(self):
        from . import servicos
        self._exigir(self.Status.PENDENTE, self.Status.APROVADA)
        tinha_evento = bool(self.google_event_id)
        self.status = self.Status.CANCELADA
        self.save(update_fields=["status"])
        if tinha_evento:
            transaction.on_commit(lambda: servicos.remover(self.pk))

    def retirar(self, km_saida):
        self._exigir(self.Status.APROVADA)
        self.status, self.km_saida = self.Status.EM_USO, km_saida
        self.save(update_fields=["status", "km_saida"])

    def devolver(self, km_retorno):
        self._exigir(self.Status.EM_USO)
        if self.km_saida is not None and km_retorno < self.km_saida:
            raise ValidationError("A quilometragem de retorno é menor que a de saída.")
        self.status, self.km_retorno = self.Status.CONCLUIDA, km_retorno
        self.save(update_fields=["status", "km_retorno"])
