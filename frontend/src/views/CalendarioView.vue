<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../api'
import {
  ROTULO_STATUS, fmtDataHora, fmtHora, fmtDiaCurto,
  mesmoDia, segundaDaSemana, somarDias,
} from '../formatar'

const veiculos = ref([])
const veiculoId = ref('')
const semana = ref(segundaDaSemana(new Date()))
const reservas = ref([])
const erro = ref('')
const carregando = ref(false)

const dias = computed(() => Array.from({ length: 7 }, (_, i) => somarDias(semana.value, i)))

function doDia(dia) {
  const ini = new Date(dia)
  ini.setHours(0, 0, 0, 0)
  const fim = somarDias(ini, 1)
  return reservas.value
    .filter((r) => new Date(r.inicio) < fim && new Date(r.fim) > ini)
    .sort((a, b) => new Date(a.inicio) - new Date(b.inicio))
}

function horario(r, dia) {
  const ini = new Date(r.inicio)
  const fim = new Date(r.fim)
  if (mesmoDia(ini, fim)) return `${fmtHora(r.inicio)} às ${fmtHora(r.fim)}`
  return `${fmtDataHora(r.inicio)} até ${fmtDataHora(r.fim)}`
}

async function carregar() {
  if (!veiculoId.value) return
  erro.value = ''
  carregando.value = true
  try {
    reservas.value = await api('/reservas/', {
      params: {
        veiculo: veiculoId.value,
        inicio: semana.value.toISOString(),
        fim: somarDias(semana.value, 7).toISOString(),
        status: 'pendente,aprovada,em_uso',
      },
    })
  } catch (e) {
    erro.value = e.message
  } finally {
    carregando.value = false
  }
}

function mudarSemana(n) {
  semana.value = somarDias(semana.value, n * 7)
}

onMounted(async () => {
  try {
    veiculos.value = await api('/veiculos/')
    if (veiculos.value.length) veiculoId.value = String(veiculos.value[0].id)
  } catch (e) {
    erro.value = e.message
  }
})

watch([veiculoId, semana], carregar)
</script>

<template>
  <h1>Calendário de disponibilidade</h1>

  <div class="cartao linha">
    <label>
      <span>Veículo</span>
      <select v-model="veiculoId">
        <option v-for="v in veiculos" :key="v.id" :value="String(v.id)">
          {{ v.modelo }} ({{ v.placa }})
        </option>
      </select>
    </label>
    <button class="sec" @click="mudarSemana(-1)">‹ Semana anterior</button>
    <button class="sec" @click="semana = segundaDaSemana(new Date())">Hoje</button>
    <button class="sec" @click="mudarSemana(1)">Próxima semana ›</button>
  </div>

  <p v-if="erro" class="erro">{{ erro }}</p>
  <p v-if="!veiculos.length && !erro" class="vazio">Nenhum veículo cadastrado.</p>

  <div v-if="veiculoId" class="cartao">
    <p v-if="carregando" class="pequeno">Carregando…</p>
    <div v-for="dia in dias" :key="dia.toISOString()" class="dia">
      <h2>{{ fmtDiaCurto(dia) }}</h2>
      <p v-if="!doDia(dia).length" class="vazio">Livre.</p>
      <div v-for="r in doDia(dia)" :key="r.id" class="item-dia">
        <strong>{{ horario(r, dia) }}</strong>
        · {{ r.solicitante_nome }}
        <span v-if="r.destino"> · {{ r.destino }}</span>
        <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
      </div>
    </div>
  </div>
</template>
