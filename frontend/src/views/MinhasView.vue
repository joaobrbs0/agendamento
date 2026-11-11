<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { ROTULO_STATUS, fmtDataHora } from '../formatar'

const reservas = ref([])
const erro = ref('')
const carregando = ref(true)

async function carregar() {
  erro.value = ''
  try {
    reservas.value = await api('/reservas/', { params: { minhas: 1 } })
  } catch (e) {
    erro.value = e.message
  } finally {
    carregando.value = false
  }
}

async function cancelar(r) {
  if (!confirm('Cancelar esta reserva?')) return
  erro.value = ''
  try {
    await api(`/reservas/${r.id}/cancelar/`, { metodo: 'POST' })
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

const podeCancelar = (r) => r.status === 'pendente' || r.status === 'aprovada'

onMounted(carregar)
</script>

<template>
  <div class="cabeca-pagina">
    <h1>Minhas reservas</h1>
    <p>Acompanhe o status dos seus pedidos.</p>
  </div>
  <p v-if="erro" class="erro">{{ erro }}</p>
  <p v-if="carregando" class="pequeno">Carregando…</p>
  <p v-else-if="!reservas.length" class="vazio">Você ainda não fez nenhuma reserva.</p>

  <div class="grade-cartoes">
  <div v-for="r in reservas" :key="r.id" class="cartao">
    <div class="cabeca-reserva">
      <strong>{{ r.veiculo_nome }}</strong>
      <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
    </div>
    <div>{{ fmtDataHora(r.inicio) }} → {{ fmtDataHora(r.fim) }}</div>
    <div class="pequeno">Destino: {{ r.destino }} · {{ r.passageiros }} passageiro(s)</div>
    <div v-if="r.motivo_recusa" class="erro">Motivo da recusa: {{ r.motivo_recusa }}</div>
    <div v-if="r.km_saida !== null" class="pequeno">
      Km saída: {{ r.km_saida }}<span v-if="r.km_retorno !== null"> · Km retorno: {{ r.km_retorno }}</span>
    </div>
    <div v-if="podeCancelar(r)" class="acoes">
      <button class="sec" @click="cancelar(r)">Cancelar reserva</button>
    </div>
  </div>
  </div>
</template>
