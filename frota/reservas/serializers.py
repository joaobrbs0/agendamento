from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.utils import timezone
from rest_framework import serializers

from .models import Reserva, Veiculo


class VeiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = ["id", "placa", "modelo"]


class ReservaSerializer(serializers.ModelSerializer):
    # Na entrada o front manda "inicio" e "fim"; o banco guarda um intervalo só.
    inicio = serializers.DateTimeField(write_only=True)
    fim = serializers.DateTimeField(write_only=True)
    veiculo = serializers.PrimaryKeyRelatedField(
        queryset=Veiculo.objects.filter(ativo=True))
    veiculo_nome = serializers.SerializerMethodField()
    solicitante_nome = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            "id", "veiculo", "veiculo_nome", "solicitante_nome",
            "inicio", "fim", "destino", "passageiros", "status",
            "motivo_recusa", "km_saida", "km_retorno", "criado_em",
        ]
        read_only_fields = [
            "status", "motivo_recusa", "km_saida", "km_retorno", "criado_em",
        ]

    def get_veiculo_nome(self, r):
        return str(r.veiculo)

    def get_solicitante_nome(self, r):
        return r.solicitante.get_full_name() or r.solicitante.get_username()

    def to_representation(self, r):
        dados = super().to_representation(r)
        dados["inicio"] = timezone.localtime(r.periodo.lower).isoformat()
        dados["fim"] = timezone.localtime(r.periodo.upper).isoformat()
        return dados

    def create(self, dados):
        inicio, fim = dados.pop("inicio"), dados.pop("fim")
        r = Reserva(
            periodo=DateTimeTZRange(inicio, fim),
            solicitante=self.context["request"].user,
            **dados,
        )
        try:
            r.clean()  # mesmas regras do admin: fim > início, não ser no passado
        except DjangoValidationError as e:
            raise serializers.ValidationError({"detail": " ".join(e.messages)})
        r.save()
        return r
