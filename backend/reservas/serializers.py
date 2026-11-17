from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.backends.postgresql.psycopg_any import DateTimeTZRange
from django.utils import timezone
from rest_framework import serializers
import re 

from .models import Reserva, Veiculo


class VeiculoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Veiculo
        fields = ["id", "placa", "modelo", "em_manutencao", "motivo_manutencao"]
        read_only_fields = ["em_manutencao", "motivo_manutencao"]
        # A unicidade é checada em validate_placa, depois de normalizar o texto.
        extra_kwargs = {"placa": {"validators": []}}

    def validate_placa(self, valor):
        placa = re.sub(r"[\s-]", "", valor).upper()
        # Padrão antigo (ABC1234) e Mercosul (ABC1D23)
        if not re.fullmatch(r"[A-Z]{3}\d[A-Z0-9]\d{2}", placa):
            raise serializers.ValidationError("Placa inválida. Use ABC1234 ou ABC1D23.")
        if Veiculo.objects.filter(placa__iexact=placa).exists():
            raise serializers.ValidationError("Já existe um veículo com essa placa.")
        return placa

    def validate_modelo(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError("Informe o modelo do veículo.")
        return valor


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

    def validate_veiculo(self, veiculo):
        if veiculo.em_manutencao:
            raise serializers.ValidationError(
                "Este veículo está em manutenção e não pode ser reservado.")
        return veiculo

    def get_veiculo_nome(self, r):
        return str(r.veiculo)

    def get_solicitante_nome(self, r):
        return r.solicitante.get_full_name() or r.solicitante.get_username()

    def to_representation(self, r):
        request = self.context.get("request")
        if (request is not None and not self.context.get("gestor")
                and r.solicitante_id != request.user.id):
            return {
                "id": r.id,
                "veiculo": r.veiculo_id,
                "inicio": timezone.localtime(r.periodo.lower).isoformat(),
                "fim": timezone.localtime(r.periodo.upper).isoformat(),
            }
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
