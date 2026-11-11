<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { fmtDataHora, localParaIso } from '../formatar'

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
    conflitos.value = await api('/reservas/', {
      params: {
        veiculo: form.value.veiculo,
        inicio: localParaIso(form.value.inicio),
        fim: localParaIso(form.value.fim),
        status: 'aprovada,em_uso',
      },
    })
  } catch {
    conflitos.value = []
  }
}

async function enviar() {
  erro.value = ''
  enviando.value = true
  try {
    await api('/reservas/', {
      metodo: 'POST',
      corpo: {
        veiculo: Number(form.value.veiculo),
        inicio: localParaIso(form.value.inicio),
        fim: localParaIso(form.value.fim),
        destino: form.value.destino.trim(),
        passageiros: Number(form.value.passageiros),
      },
    })
    router.push({ name: 'minhas' })
  } catch (e) {
    erro.value = e.message
  } finally {
    enviando.value = false
  }
}

onMounted(async () => {
  try {
    veiculos.value = await api('/veiculos/')
    if (veiculos.value.length) form.value.veiculo = String(veiculos.value[0].id)
  } catch (e) {
    erro.value = e.message
  }
})

watch(() => [form.value.veiculo, form.value.inicio, form.value.fim], verificarConflitos)
</script>

<template>
  <h1>Nova reserva</h1>

  <div class="cartao">
    <label>
      <span>Veículo</span>
      <select v-model="form.veiculo">
        <option v-for="v in veiculos" :key="v.id" :value="String(v.id)">
          {{ v.modelo }} ({{ v.placa }})
        </option>
      </select>
    </label>

    <div class="linha">
      <label>
        <span>Saída</span>
        <input v-model="form.inicio" type="datetime-local" />
      </label>
      <label>
        <span>Retorno</span>
        <input v-model="form.fim" type="datetime-local" />
      </label>
    </div>

    <p v-if="form.inicio && form.fim && !periodoValido" class="erro">
      O retorno precisa ser depois da saída.
    </p>
    <p v-if="conflitos.length" class="aviso">
      O veículo já tem reserva nesse período:
      <span v-for="c in conflitos" :key="c.id">
        {{ fmtDataHora(c.inicio) }} a {{ fmtDataHora(c.fim) }};
      </span>
      Seu pedido pode ser recusado.
    </p>

    <label>
      <span>Destino</span>
      <input v-model="form.destino" maxlength="200" />
    </label>
    <label>
      <span>Passageiros</span>
      <input v-model="form.passageiros" type="number" min="1" max="60" />
    </label>

    <p v-if="erro" class="erro">{{ erro }}</p>
    <button
      :disabled="enviando || !form.veiculo || !periodoValido || !form.destino.trim()"
      @click="enviar"
    >
      Solicitar reserva
    </button>
  </div>
</template>
