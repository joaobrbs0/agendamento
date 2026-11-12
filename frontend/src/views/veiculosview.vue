<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'

const veiculos = ref([])
const form = reactive({ placa: '', modelo: '' })
const erro = ref('')
const sucesso = ref('')
const enviando = ref(false)

async function carregar() {
  try {
    veiculos.value = await api('/veiculos/')
  } catch (e) {
    erro.value = e.message
  }
}

async function cadastrar() {
  erro.value = ''
  sucesso.value = ''
  enviando.value = true
  try {
    const v = await api('/veiculos/', {
      metodo: 'POST',
      corpo: { placa: form.placa, modelo: form.modelo },
    })
    sucesso.value = `Veículo ${v.modelo} (${v.placa}) cadastrado.`
    form.placa = ''
    form.modelo = ''
    await carregar()
  } catch (e) {
    erro.value = e.message
  } finally {
    enviando.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <div class="cabeca-pagina">
    <h1>Veículos</h1>
    <p>Cadastre novos veículos da frota.</p>
  </div>

  <div class="cartao">
    <h2>Novo veículo</h2>
    <div class="linha">
      <label>
        <span>Placa</span>
        <input v-model="form.placa" maxlength="8" placeholder="ABC1D23" @keyup.enter="cadastrar" />
      </label>
      <label>
        <span>Modelo</span>
        <input v-model="form.modelo" maxlength="80" placeholder="Ex.: Fiat Uno" @keyup.enter="cadastrar" />
      </label>
      <button :disabled="enviando || !form.placa || !form.modelo" @click="cadastrar">
        Cadastrar
      </button>
    </div>
    <p v-if="erro" class="erro">{{ erro }}</p>
    <p v-if="sucesso" class="sucesso">{{ sucesso }}</p>
  </div>

  <div class="cartao">
    <h2>Frota cadastrada</h2>
    <p v-if="!veiculos.length" class="vazio">Nenhum veículo cadastrado.</p>
    <ul class="lista-simples">
      <li v-for="v in veiculos" :key="v.id">
        <strong>{{ v.modelo }}</strong>
        <span class="pequeno">{{ v.placa }}</span>
      </li>
    </ul>
  </div>
</template>