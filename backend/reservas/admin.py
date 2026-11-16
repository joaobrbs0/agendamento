from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Reserva, Veiculo


@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "modelo", "ativo")


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ("veiculo", "solicitante", "periodo", "destino", "status")
    list_filter = ("status", "veiculo")
    readonly_fields = ("decidido_por", "decidido_em", "google_event_id")
    actions = ["aprovar_selecionadas", "recusar_selecionadas"]

    def _aplicar(self, request, queryset, acao, texto_ok):
        feitas = 0
        for r in queryset:
            try:
                acao(r)
                feitas += 1
            except ValidationError as e:
                self.message_user(request, f"{r}: {' '.join(e.messages)}",
                                  messages.ERROR)
        if feitas:
            self.message_user(request, f"{feitas} reserva(s) {texto_ok}.")

    @admin.action(description="Aprovar reservas selecionadas")
    def aprovar_selecionadas(self, request, queryset):
        if not request.user.has_perm("reservas.aprovar_reserva"):
            self.message_user(request, "Você não tem permissão para aprovar.",
                              messages.ERROR)
            return
        self._aplicar(request, queryset, lambda r: r.aprovar(request.user), "aprovada(s)")

    @admin.action(description="Recusar reservas selecionadas")
    def recusar_selecionadas(self, request, queryset):
        if not request.user.has_perm("reservas.aprovar_reserva"):
            self.message_user(request, "Você não tem permissão para recusar.",
                              messages.ERROR)
            return
        self._aplicar(request, queryset, lambda r: r.recusar(request.user), "recusada(s)")
