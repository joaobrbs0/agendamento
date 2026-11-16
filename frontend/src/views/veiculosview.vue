<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'

const veiculos = ref([])
const form = reactive({ placa: '', modelo: '' })
const erro = ref('')
const sucesso = ref('')
const enviando = ref(false)

async function carregar() {
  try { veiculos.value = await api('/veiculos/') }
  catch (e) { erro.value = e.message }
}
async function cadastrar() {
  erro.value = ''
  sucesso.value = ''
  enviando.value = true
  try {
    const v = await api('/veiculos/', { metodo: 'POST', corpo: { placa: form.placa, modelo: form.modelo } })
    sucesso.value = `Veículo ${v.modelo} (${v.placa}) cadastrado.`
    form.placa = ''
    form.modelo = ''
    await carregar()
  } catch (e) { erro.value = e.message }
  finally { enviando.value = false }
}
onMounted(carregar)
</script>

<template>
  <div class="pagina-intro">
    <div>
      <div class="contexto">Administração da frota</div>
      <div class="cabeca-pagina">
        <h1>Cadastro de veículos</h1>
        <p class="apoio">Mantenha os veículos vinculados à frota institucional atualizados.</p>
      </div>
    </div>
  </div>

  <section class="cartao secao-frota">
    <div class="cartao-cabecalho">
      <h2>Incluir veículo na frota</h2>
      <p>Informe os dados de identificação do veículo para realizar o cadastro.</p>
    </div>
    <div class="linha">
      <label>
        <span>Placa</span>
        <input v-model="form.placa" maxlength="8" placeholder="ABC1D23" @keyup.enter="cadastrar" />
      </label>
      <label>
        <span>Modelo</span>
        <input v-model="form.modelo" maxlength="80" placeholder="Ex.: Fiat Strada" @keyup.enter="cadastrar" />
      </label>
      <button :disabled="enviando || !form.placa.trim() || !form.modelo.trim()" @click="cadastrar">
        {{ enviando ? 'Cadastrando…' : 'Cadastrar veículo' }}
      </button>
    </div>
    <p v-if="erro" class="erro">{{ erro }}</p>
    <p v-if="sucesso" class="sucesso">{{ sucesso }}</p>
  </section>

  <section class="cartao secao-frota">
    <div class="cartao-cabecalho">
      <h2>Frota cadastrada</h2>
      <p>{{ veiculos.length }} veículo(s) registrado(s) no sistema.</p>
    </div>
    <div v-if="!veiculos.length" class="estado-vazio">
      <strong>Nenhum veículo cadastrado</strong>
      Os veículos incluídos serão apresentados nesta relação.
    </div>
    <div v-else class="frota-lista">
      <article v-for="v in veiculos" :key="v.id" class="frota-item">
        <div class="frota-icone" aria-hidden="true">▣</div>
        <div class="frota-info">
          <strong>{{ v.modelo }}</strong>
          <small>Placa: {{ v.placa }}</small>
        </div>
        <span class="frota-tag">Cadastrado</span>
      </article>
    </div>
  </section>
</template>
