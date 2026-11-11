<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import Icone from '../components/Icone.vue'
import {
  ROTULO_STATUS, fmtDataHora, fmtHora, fmtMesAno, fmtDiaLongo,
  mesmoDia, segundaDaSemana, somarDias, primeiroDoMes, chaveDia,
} from '../formatar'

const route = useRoute()
const router = useRouter()
const ehAdmin = computed(() => route.meta.area === 'admin')

const DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
const MAX_CHIPS = 3

const hoje = new Date()
hoje.setHours(0, 0, 0, 0)

const veiculos = ref([])
const veiculoId = ref('')
const mes = ref(primeiroDoMes(hoje))
const selecionado = ref(new Date(hoje))
const reservas = ref([])
const erro = ref('')
const carregando = ref(false)

const grade = computed(() => {
  const ini = segundaDaSemana(mes.value)
  const total = somarDias(ini, 35).getMonth() === mes.value.getMonth() ? 42 : 35
  return Array.from({ length: total }, (_, i) => somarDias(ini, i))
})

function reservasDoDia(dia) {
  const ini = new Date(dia)
  ini.setHours(0, 0, 0, 0)
  const fim = somarDias(ini, 1)
  return reservas.value
    .filter((r) => new Date(r.inicio) < fim && new Date(r.fim) > ini)
    .sort((a, b) => new Date(a.inicio) - new Date(b.inicio))
}

const porDia = computed(() => {
  const m = {}
  for (const d of grade.value) m[chaveDia(d)] = reservasDoDia(d)
  return m
})

const doSelecionado = computed(() => porDia.value[chaveDia(selecionado.value)] || reservasDoDia(selecionado.value))
const selecionadoNoPassado = computed(() => selecionado.value < hoje)

function horario(r) {
  const ini = new Date(r.inicio)
  const fim = new Date(r.fim)
  if (mesmoDia(ini, fim)) return `${fmtHora(r.inicio)} às ${fmtHora(r.fim)}`
  return `${fmtDataHora(r.inicio)} até ${fmtDataHora(r.fim)}`
}

function rotuloChip(r, dia) {
  const quando = mesmoDia(new Date(r.inicio), dia) ? fmtHora(r.inicio) : '…'
  return `${quando} ${r.solicitante_nome}`
}

async function carregar() {
  if (!veiculoId.value) return
  erro.value = ''
  carregando.value = true
  try {
    reservas.value = await api('/reservas/', {
      params: {
        veiculo: veiculoId.value,
        inicio: grade.value[0].toISOString(),
        fim: somarDias(grade.value[0], grade.value.length).toISOString(),
        status: 'pendente,aprovada,em_uso',
      },
    })
  } catch (e) {
    erro.value = e.message
  } finally {
    carregando.value = false
  }
}

function mudarMes(n) {
  mes.value = new Date(mes.value.getFullYear(), mes.value.getMonth() + n, 1)
  const ehMesAtual = mes.value.getTime() === primeiroDoMes(hoje).getTime()
  selecionado.value = ehMesAtual ? new Date(hoje) : new Date(mes.value)
}

function irParaHoje() {
  mes.value = primeiroDoMes(hoje)
  selecionado.value = new Date(hoje)
}

function reservarNoDia() {
  router.push({ name: 'nova', query: { data: chaveDia(selecionado.value) } })
}

onMounted(async () => {
  try {
    veiculos.value = await api('/veiculos/')
    if (veiculos.value.length) veiculoId.value = String(veiculos.value[0].id)
  } catch (e) {
    erro.value = e.message
  }
})

watch([veiculoId, mes], carregar)
</script>

<template>
  <div class="cabeca-pagina">
    <h1>Calendário de disponibilidade</h1>
    <p>Clique em um dia para ver as reservas do veículo.</p>
  </div>

  <div class="cal-barra">
    <button class="sec btn-icone" aria-label="Mês anterior" @click="mudarMes(-1)"><Icone nome="esq" /></button>
    <span class="mes">{{ fmtMesAno(mes) }}</span>
    <button class="sec btn-icone" aria-label="Próximo mês" @click="mudarMes(1)"><Icone nome="dir" /></button>
    <button class="sec" @click="irParaHoje">Hoje</button>
    <span class="espaco" />
    <select v-model="veiculoId" aria-label="Veículo">
      <option v-for="v in veiculos" :key="v.id" :value="String(v.id)">
        {{ v.modelo }} ({{ v.placa }})
      </option>
    </select>
  </div>

  <p v-if="erro" class="erro">{{ erro }}</p>
  <p v-if="!veiculos.length && !erro" class="vazio">Nenhum veículo cadastrado.</p>

  <div v-if="veiculoId" class="cal">
    <div>
      <div class="cartao cal-quadro">
        <div class="cal-grade">
          <div v-for="d in DIAS_SEMANA" :key="d" class="cal-cab">{{ d }}</div>
          <button
            v-for="dia in grade"
            :key="chaveDia(dia)"
            :class="[
              'cal-dia',
              {
                fora: dia.getMonth() !== mes.getMonth(),
                hoje: mesmoDia(dia, hoje),
                selecionado: mesmoDia(dia, selecionado),
              },
            ]"
            @click="selecionado = new Date(dia)"
          >
            <span class="num">{{ dia.getDate() }}</span>
            <span
              v-for="r in (porDia[chaveDia(dia)] || []).slice(0, MAX_CHIPS)"
              :key="r.id"
              :class="['chip', r.status]"
            >{{ rotuloChip(r, dia) }}</span>
            <span v-if="(porDia[chaveDia(dia)] || []).length > MAX_CHIPS" class="mais">
              +{{ porDia[chaveDia(dia)].length - MAX_CHIPS }} mais
            </span>
          </button>
        </div>
      </div>
      <div class="cal-legenda">
        <span><i class="pendente" /> Pendente</span>
        <span><i class="aprovada" /> Aprovada</span>
        <span><i class="em_uso" /> Em uso</span>
        <span v-if="carregando">Carregando…</span>
      </div>
    </div>

    <aside class="cartao cal-detalhe">
      <h2>{{ fmtDiaLongo(selecionado) }}</h2>
      <p v-if="!doSelecionado.length" class="vazio">Nenhuma reserva. Veículo livre neste dia.</p>
      <div v-for="r in doSelecionado" :key="r.id" class="item-dia">
        <div class="linha-info">
          <span class="hora">{{ horario(r) }}</span>
          <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
        </div>
        <div>{{ r.solicitante_nome }}</div>
        <div v-if="r.destino" class="pequeno">Destino: {{ r.destino }}</div>
      </div>
      <div class="acoes">
        <button v-if="!ehAdmin" :disabled="selecionadoNoPassado" @click="reservarNoDia">
          Reservar neste dia
        </button>
        <RouterLink v-else to="/admin/gestao"><button class="sec">Ir para a gestão</button></RouterLink>
      </div>
    </aside>
  </div>
</template>
