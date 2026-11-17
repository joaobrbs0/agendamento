<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'

const veiculos = ref([])
const form = reactive({ placa: '', modelo: '' })
const erro = ref('')
const sucesso = ref('')
const enviando = ref(false)
const excluindoId = ref(null)
const manutencaoId = ref(null)

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
async function excluir(v) {
  if (!window.confirm(`Excluir o veículo ${v.modelo} (${v.placa})? Essa ação remove o veículo da frota.`)) return
  erro.value = ''
  sucesso.value = ''
  excluindoId.value = v.id
  try {
    await api(`/veiculos/${v.id}/`, { metodo: 'DELETE' })
    sucesso.value = `Veículo ${v.modelo} (${v.placa}) excluído.`
    await carregar()
  } catch (e) { erro.value = e.message }
  finally { excluindoId.value = null }
}
async function alternarManutencao(v) {
  let motivo = ''
  if (!v.em_manutencao) {
    motivo = window.prompt(`Enviar ${v.modelo} (${v.placa}) para manutenção.\nMotivo (opcional):`)
    if (motivo === null) return
  }
  erro.value = ''
  sucesso.value = ''
  manutencaoId.value = v.id
  try {
    const r = await api(`/veiculos/${v.id}/manutencao/`, {
      metodo: 'POST',
      corpo: { em_manutencao: !v.em_manutencao, motivo },
    })
    sucesso.value = r.em_manutencao
      ? `Veículo ${r.modelo} (${r.placa}) enviado para manutenção.`
        + (r.reservas_afetadas ? ` Atenção: ${r.reservas_afetadas} reserva(s) pendente(s) ou aprovada(s) continuam registradas para ele; revise-as na Gestão de reservas.` : '')
      : `Veículo ${r.modelo} (${r.placa}) liberado para reservas.`
    await carregar()
  } catch (e) { erro.value = e.message }
  finally { manutencaoId.value = null }
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
          <small v-if="v.em_manutencao && v.motivo_manutencao">Motivo: {{ v.motivo_manutencao }}</small>
        </div>
        <span :class="['frota-tag', { 'frota-tag-manutencao': v.em_manutencao }]">
          {{ v.em_manutencao ? 'Em manutenção' : 'Disponível' }}
        </span>
        <button class="sec" :disabled="manutencaoId === v.id" @click="alternarManutencao(v)">
          {{ manutencaoId === v.id ? 'Salvando…' : (v.em_manutencao ? 'Liberar veículo' : 'Enviar p/ manutenção') }}
        </button>
        <button class="perigo" :disabled="excluindoId === v.id" @click="excluir(v)">
          {{ excluindoId === v.id ? 'Excluindo…' : 'Excluir' }}
        </button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.frota-tag-manutencao { background: #fdf0d5; color: #8a5a00; }
</style>
