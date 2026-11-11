<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'
import { ROTULO_STATUS, fmtDataHora } from '../formatar'

const ABAS = [
  { chave: 'pendente', titulo: 'Pendentes' },
  { chave: 'aprovada', titulo: 'Aprovadas (aguardando retirada)' },
  { chave: 'em_uso', titulo: 'Em uso' },
]

const route = useRoute()
const aba = ref(ABAS.some((a) => a.chave === route.query.aba) ? route.query.aba : 'pendente')
const reservas = ref([])
const erro = ref('')
const carregando = ref(false)
const motivos = reactive({})
const kms = reactive({})

async function carregar() {
  erro.value = ''
  carregando.value = true
  try {
    const lista = await api('/reservas/', { params: { status: aba.value } })
    // Pendentes: mais antigas primeiro. As demais: por data de saída.
    reservas.value = lista.sort((a, b) =>
      aba.value === 'pendente'
        ? new Date(a.criado_em) - new Date(b.criado_em)
        : new Date(a.inicio) - new Date(b.inicio))
  } catch (e) {
    erro.value = e.message
  } finally {
    carregando.value = false
  }
}

async function acao(r, nome, corpo) {
  erro.value = ''
  try {
    await api(`/reservas/${r.id}/${nome}/`, { metodo: 'POST', corpo })
    await carregar()
  } catch (e) {
    erro.value = e.message
  }
}

const aprovar = (r) => acao(r, 'aprovar')
const recusar = (r) => acao(r, 'recusar', { motivo: motivos[r.id] || '' })
const retirar = (r) => acao(r, 'retirar', { km: Number(kms[r.id]) })
const devolver = (r) => acao(r, 'devolver', { km: Number(kms[r.id]) })

const kmValido = (r) => kms[r.id] !== undefined && kms[r.id] !== '' && Number(kms[r.id]) >= 0

watch(aba, carregar)
onMounted(carregar)
</script>

<template>
  <div class="cabeca-pagina">
    <h1>Gestão de reservas</h1>
    <p>Aprove, recuse e acompanhe retiradas e devoluções.</p>
  </div>

  <div class="abas">
    <button
      v-for="a in ABAS"
      :key="a.chave"
      :class="{ ativa: aba === a.chave }"
      @click="aba = a.chave"
    >
      {{ a.titulo }}
    </button>
  </div>

  <p v-if="erro" class="erro">{{ erro }}</p>
  <p v-if="carregando" class="pequeno">Carregando…</p>
  <p v-else-if="!reservas.length" class="vazio">Nada por aqui.</p>

  <div class="grade-cartoes">
  <div v-for="r in reservas" :key="r.id" class="cartao">
    <div class="cabeca-reserva">
      <strong>{{ r.veiculo_nome }}</strong>
      <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
    </div>
    <div>{{ r.solicitante_nome }}</div>
    <div>{{ fmtDataHora(r.inicio) }} → {{ fmtDataHora(r.fim) }}</div>
    <div class="pequeno">Destino: {{ r.destino }} · {{ r.passageiros }} passageiro(s)</div>
    <div v-if="r.km_saida !== null" class="pequeno">Km de saída: {{ r.km_saida }}</div>

    <div v-if="r.status === 'pendente'" class="acoes">
      <button class="ok" @click="aprovar(r)">Aprovar</button>
      <input v-model="motivos[r.id]" placeholder="Motivo (opcional)" maxlength="300" />
      <button class="perigo" @click="recusar(r)">Recusar</button>
    </div>

    <div v-else-if="r.status === 'aprovada'" class="acoes">
      <input v-model="kms[r.id]" type="number" min="0" placeholder="Km de saída" />
      <button :disabled="!kmValido(r)" @click="retirar(r)">Registrar retirada</button>
      <button class="sec" @click="acao(r, 'cancelar')">Cancelar</button>
    </div>

    <div v-else-if="r.status === 'em_uso'" class="acoes">
      <input v-model="kms[r.id]" type="number" min="0" placeholder="Km de retorno" />
      <button :disabled="!kmValido(r)" @click="devolver(r)">Registrar devolução</button>
    </div>
  </div>
  </div>
</template>
