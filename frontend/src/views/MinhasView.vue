<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { ROTULO_STATUS, fmtDataHora } from '../formatar'

const reservas = ref([])
const erro = ref('')
const carregando = ref(true)

async function carregar() {
  erro.value = ''
  try { reservas.value = await api('/reservas/', { params: { minhas: 1 } }) }
  catch (e) { erro.value = e.message }
  finally { carregando.value = false }
}
async function cancelar(r) {
  if (!confirm('Cancelar esta reserva?')) return
  erro.value = ''
  try {
    await api(`/reservas/${r.id}/cancelar/`, { metodo: 'POST' })
    await carregar()
  } catch (e) { erro.value = e.message }
}
const podeCancelar = (r) => r.status === 'pendente' || r.status === 'aprovada'
onMounted(carregar)
</script>

<template>
  <div class="pagina-intro">
    <div>
      <div class="contexto">Área do solicitante</div>
      <div class="cabeca-pagina">
        <h1>Minhas reservas</h1>
        <p class="apoio">Acompanhe suas solicitações e consulte as informações de cada deslocamento.</p>
      </div>
    </div>
  </div>

  <p v-if="erro" class="erro">{{ erro }}</p>
  <div v-if="carregando" class="cartao pequeno">Carregando suas solicitações…</div>
  <div v-else-if="!reservas.length" class="estado-vazio">
    <strong>Nenhuma solicitação encontrada</strong>
    Você ainda não possui reservas registradas.
  </div>

  <div v-else class="grade-cartoes">
    <article v-for="r in reservas" :key="r.id" class="cartao reserva-card">
      <header class="reserva-card-topo">
        <div>
          <div class="contexto">Veículo reservado</div>
          <strong>{{ r.veiculo_nome }}</strong>
        </div>
        <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
      </header>
      <div class="reserva-card-corpo">
        <div class="reserva-periodo">{{ fmtDataHora(r.inicio) }} <span aria-hidden="true">→</span> {{ fmtDataHora(r.fim) }}</div>
        <div class="reserva-dados">
          <div class="reserva-dado">
            <small>Destino / finalidade</small>
            <strong>{{ r.destino || 'Não informado' }}</strong>
          </div>
          <div class="reserva-dado">
            <small>Passageiros</small>
            <strong>{{ r.passageiros }}</strong>
          </div>
          <div v-if="r.km_saida !== null" class="reserva-dado">
            <small>Quilometragem de saída</small>
            <strong>{{ r.km_saida }}</strong>
          </div>
          <div v-if="r.km_retorno !== null" class="reserva-dado">
            <small>Quilometragem de retorno</small>
            <strong>{{ r.km_retorno }}</strong>
          </div>
        </div>
        <p v-if="r.motivo_recusa" class="erro">Motivo da recusa: {{ r.motivo_recusa }}</p>
      </div>
      <div v-if="podeCancelar(r)" class="acoes">
        <button class="sec" @click="cancelar(r)">Cancelar solicitação</button>
      </div>
    </article>
  </div>
</template>
