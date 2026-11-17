<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { fmtDataHora, localParaIso } from '../formatar'

const route = useRoute()
const router = useRouter()
const veiculos = ref([])
const form = ref({ veiculo: '', inicio: '', fim: '', destino: '', passageiros: 1 })
const conflitos = ref([])
const erro = ref('')
const enviando = ref(false)

const periodoValido = computed(() => {
  const { inicio, fim } = form.value
  return Boolean(inicio && fim) && new Date(fim) > new Date(inicio)
})

async function verificarConflitos() {
  conflitos.value = []
  if (!form.value.veiculo || !periodoValido.value) return
  try {
    conflitos.value = await api('/reservas/', { params: {
      veiculo: form.value.veiculo, inicio: localParaIso(form.value.inicio),
      fim: localParaIso(form.value.fim), status: 'aprovada,em_uso',
    } })
  } catch { conflitos.value = [] }
}

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    await api('/reservas/', { metodo: 'POST', corpo: {
      veiculo: Number(form.value.veiculo), inicio: localParaIso(form.value.inicio),
      fim: localParaIso(form.value.fim), destino: form.value.destino.trim(),
      passageiros: Number(form.value.passageiros),
    } })
    router.push({ name: 'minhas' })
  } catch (e) { erro.value = e.message }
  finally { enviando.value = false }
}

onMounted(async () => {
  const dia = route.query.data
  if (typeof dia === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(dia)) {
    form.value.inicio = `${dia}T08:00`
    form.value.fim = `${dia}T17:00`
  }
  try {
    veiculos.value = await api('/veiculos/')
    const livre = veiculos.value.find(v => !v.em_manutencao)
    if (livre) form.value.veiculo = String(livre.id)
  } catch (e) { erro.value = e.message }
})
watch(() => [form.value.veiculo, form.value.inicio, form.value.fim], verificarConflitos)
</script>

<template>
  <div class="pagina-intro">
    <div>
      <div class="contexto">Solicitações de transporte</div>
      <div class="cabeca-pagina">
        <h1>Nova reserva</h1>
        <p class="apoio">Informe os dados do deslocamento para encaminhar sua solicitação.</p>
      </div>
    </div>
  </div>

  <section class="cartao form-reserva">
    <div class="cartao-cabecalho">
      <h2>Dados da solicitação</h2>
      <p>Preencha as informações do veículo, período e finalidade do deslocamento.</p>
    </div>

    <div class="form-grid">
      <label class="campo-largo">
        <span>Veículo solicitado</span>
        <select v-model="form.veiculo">
          <option value="" disabled>Selecione um veículo</option>
          <option v-for="v in veiculos" :key="v.id" :value="String(v.id)" :disabled="v.em_manutencao">
            {{ v.modelo }} ({{ v.placa }}){{ v.em_manutencao ? ' — em manutenção' : '' }}
          </option>
        </select>
      </label>

      <label>
        <span>Data e horário de saída</span>
        <input v-model="form.inicio" type="datetime-local" />
      </label>
      <label>
        <span>Data e horário de retorno</span>
        <input v-model="form.fim" type="datetime-local" />
      </label>

      <p v-if="form.inicio && form.fim && !periodoValido" class="erro campo-largo">
        O retorno precisa ser posterior à saída.
      </p>
      <div v-if="conflitos.length" class="aviso campo-largo">
        <strong>Atenção: conflito de agenda identificado.</strong>
        <div v-for="c in conflitos" :key="c.id">
          Reserva existente: {{ fmtDataHora(c.inicio) }} a {{ fmtDataHora(c.fim) }}.
        </div>
        A disponibilidade deverá ser considerada na análise do pedido.
      </div>

      <label class="campo-largo">
        <span>Destino / finalidade do deslocamento</span>
        <input v-model="form.destino" maxlength="200" placeholder="Informe o destino ou a finalidade" />
      </label>
      <label>
        <span>Quantidade de passageiros</span>
        <input v-model="form.passageiros" type="number" min="1" max="60" />
      </label>
    </div>

    <p v-if="erro" class="erro">{{ erro }}</p>
    <div class="form-acoes">
      <button :disabled="enviando || !form.veiculo || !periodoValido || !form.destino.trim()" @click="enviar">
        {{ enviando ? 'Enviando solicitação…' : 'Encaminhar solicitação' }}
      </button>
      <span class="nota">A solicitação será encaminhada para análise da gestão.</span>
    </div>
  </section>
</template>
