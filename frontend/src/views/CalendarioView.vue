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
const MAX_CHIPS = 2
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
  const fimMes = new Date(mes.value.getFullYear(), mes.value.getMonth() + 1, 0)
  const totalDias = Math.ceil((fimMes.getDate() + ((ini.getDay() + 6) % 7)) / 7) * 7
  return Array.from({ length: totalDias }, (_, i) => somarDias(ini, i))
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
const reservasNoMes = computed(() => reservas.value.filter(r => {
  const inicio = new Date(r.inicio)
  return inicio.getMonth() === mes.value.getMonth() && inicio.getFullYear() === mes.value.getFullYear()
}))
const resumoMes = computed(() => ({
  total: reservasNoMes.value.length,
  pendentes: reservasNoMes.value.filter(r => r.status === 'pendente').length,
  aprovadas: reservasNoMes.value.filter(r => r.status === 'aprovada').length,
  emUso: reservasNoMes.value.filter(r => r.status === 'em_uso').length,
}))
function horario(r) {
  const ini = new Date(r.inicio)
  const fim = new Date(r.fim)
  if (mesmoDia(ini, fim)) return `${fmtHora(r.inicio)} às ${fmtHora(r.fim)}`
  return `${fmtDataHora(r.inicio)} até ${fmtDataHora(r.fim)}`
}
function rotuloChip(r, dia) {
  const quando = mesmoDia(new Date(r.inicio), dia) ? fmtHora(r.inicio) : 'Continua'
  return `${quando} · ${ehAdmin.value ? r.solicitante_nome : 'Reservado'}`
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
        status: ehAdmin.value ? 'pendente,aprovada,em_uso' : 'aprovada,em_uso',
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
  <div class="cabeca-pagina calendario-cabecalho">
    <div><span class="painel-sobretitulo">GESTÃO DA FROTA</span><h1>Calendário de disponibilidade</h1><p>Consulte a ocupação dos veículos e acompanhe as reservas por período.</p></div>
    <span v-if="carregando" class="cal-atualizando"><span class="cal-ponto-pulso"></span> Atualizando agenda</span>
  </div>

  <p v-if="erro" class="erro" role="alert">{{ erro }}</p>
  <div v-if="!veiculos.length && !erro" class="cartao cal-sem-veiculos"><strong>Nenhum veículo cadastrado</strong><p>Cadastre um veículo para consultar a disponibilidade da frota.</p></div>

  <template v-if="veiculoId">
    <p v-if="veiculos.find(v => String(v.id) === veiculoId)?.em_manutencao" class="erro">
      Este veículo está em manutenção e não aceita novas reservas<template v-if="veiculos.find(v => String(v.id) === veiculoId)?.motivo_manutencao">: {{ veiculos.find(v => String(v.id) === veiculoId).motivo_manutencao }}</template>.
    </p>
    <section class="cal-resumo" aria-label="Resumo do mês">
      <div class="cal-resumo-veiculo"><span class="cal-resumo-icone">▣</span><span><small>VEÍCULO SELECIONADO</small><strong>{{ veiculos.find(v => String(v.id) === veiculoId)?.modelo }} <span>({{ veiculos.find(v => String(v.id) === veiculoId)?.placa }})</span></strong></span></div>
      <div class="cal-resumo-item"><small>RESERVAS NO MÊS</small><strong>{{ resumoMes.total }}</strong></div>
      <div v-if="ehAdmin" class="cal-resumo-item"><small>PENDENTES</small><strong>{{ resumoMes.pendentes }}</strong></div>
      <div v-if="ehAdmin" class="cal-resumo-item"><small>CONFIRMADAS</small><strong>{{ resumoMes.aprovadas + resumoMes.emUso }}</strong></div>
    </section>

    <div class="cal-controles">
      <div class="cal-navegacao">
        <button class="sec btn-icone" aria-label="Mês anterior" @click="mudarMes(-1)"><Icone nome="esq" /></button>
        <h2>{{ fmtMesAno(mes) }}</h2>
        <button class="sec btn-icone" aria-label="Próximo mês" @click="mudarMes(1)"><Icone nome="dir" /></button>
        <button class="sec cal-hoje" @click="irParaHoje">Hoje</button>
      </div>
      <label class="cal-seletor"><span>Visualizar veículo</span><select v-model="veiculoId" aria-label="Veículo"><option v-for="v in veiculos" :key="v.id" :value="String(v.id)">{{ v.modelo }} ({{ v.placa }})</option></select></label>
    </div>

    <div class="cal-layout">
      <section class="cartao cal-quadro" aria-label="Calendário mensal">
        <div class="cal-grade">
          <div v-for="d in DIAS_SEMANA" :key="d" class="cal-cab">{{ d }}</div>
          <button v-for="dia in grade" :key="chaveDia(dia)" :class="['cal-dia', {
            fora: dia.getMonth() !== mes.getMonth(),
            hoje: mesmoDia(dia, hoje),
            selecionado: mesmoDia(dia, selecionado),
            'com-reserva': (porDia[chaveDia(dia)] || []).length,
          }]" :aria-label="`${fmtDiaLongo(dia)}, ${(porDia[chaveDia(dia)] || []).length} reservas`" :aria-pressed="mesmoDia(dia, selecionado)" @click="selecionado = new Date(dia)">
            <span class="cal-dia-topo"><span class="num">{{ dia.getDate() }}</span><span v-if="(porDia[chaveDia(dia)] || []).length" class="cal-qtd">{{ (porDia[chaveDia(dia)] || []).length }}</span></span>
            <span v-for="r in (porDia[chaveDia(dia)] || []).slice(0, MAX_CHIPS)" :key="r.id" :class="['chip', ehAdmin ? r.status : 'reservado']">{{ rotuloChip(r, dia) }}</span>
            <span v-if="(porDia[chaveDia(dia)] || []).length > MAX_CHIPS" class="mais">+{{ (porDia[chaveDia(dia)] || []).length - MAX_CHIPS }} outras</span>
            <span v-if="!(porDia[chaveDia(dia)] || []).length && dia.getMonth() === mes.getMonth()" class="cal-dia-livre">Disponível</span>
          </button>
        </div>
      </section>

      <aside class="cartao cal-detalhe">
        <div class="cal-detalhe-cabecalho"><div><span class="painel-sobretitulo">AGENDA DO DIA</span><h2>{{ fmtDiaLongo(selecionado) }}</h2></div><span class="cal-detalhe-total">{{ doSelecionado.length }}</span></div>
        <div class="cal-detalhe-corpo">
          <div v-if="!doSelecionado.length" class="cal-dia-vazio"><span>✓</span><strong>Veículo disponível</strong><p>Nenhuma reserva identificada para esta data.</p></div>
          <div v-for="r in doSelecionado" :key="r.id" class="item-dia">
            <div class="linha-info"><span class="hora">{{ horario(r) }}</span><span v-if="ehAdmin" :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span><span v-else class="selo reservado">Reservado</span></div>
            <template v-if="ehAdmin">
              <strong class="cal-solicitante">{{ r.solicitante_nome }}</strong>
              <div v-if="r.destino" class="pequeno">Destino: {{ r.destino }}</div>
            </template>
          </div>
        </div>
        <div class="cal-detalhe-acoes">
          <button v-if="!ehAdmin" :disabled="selecionadoNoPassado" @click="reservarNoDia">Solicitar reserva</button>
          <RouterLink v-else to="/admin/gestao" class="cal-link-gestao">Acessar gestão de reservas <span aria-hidden="true">→</span></RouterLink>
        </div>
      </aside>
    </div>
    <div class="cal-legenda"><strong>Legenda</strong><template v-if="ehAdmin"><span><i class="pendente" /> Pendente</span><span><i class="aprovada" /> Aprovada</span><span><i class="em_uso" /> Em utilização</span></template><span v-else><i class="reservado" /> Reservado</span><span><i class="livre" /> Disponível</span></div>
  </template>
</template>
