<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '../api'
import { ROTULO_STATUS, fmtDataHora, fmtHora, somarDias } from '../formatar'

const contagem = reactive({ pendente: null, aprovada: null, em_uso: null })
const pendentes = ref([])
const hoje = ref([])
const erro = ref('')
const atualizando = ref(false)

const totalAcompanhado = computed(() =>
  [contagem.pendente, contagem.aprovada, contagem.em_uso].every(v => v !== null)
    ? contagem.pendente + contagem.aprovada + contagem.em_uso
    : null,
)
const dataAtual = computed(() => new Intl.DateTimeFormat('pt-BR', {
  weekday: 'long', day: '2-digit', month: 'long', year: 'numeric',
}).format(new Date()))

async function carregar() {
  erro.value = ''
  atualizando.value = true
  try {
    const ini = new Date()
    ini.setHours(0, 0, 0, 0)
    const [p, a, e, h] = await Promise.all([
      api('/reservas/', { params: { status: 'pendente' } }),
      api('/reservas/', { params: { status: 'aprovada' } }),
      api('/reservas/', { params: { status: 'em_uso' } }),
      api('/reservas/', {
        params: {
          inicio: ini.toISOString(),
          fim: somarDias(ini, 1).toISOString(),
          status: 'aprovada,em_uso',
        },
      }),
    ])
    contagem.pendente = p.length
    contagem.aprovada = a.length
    contagem.em_uso = e.length
    pendentes.value = p
      .sort((x, y) => new Date(x.criado_em) - new Date(y.criado_em))
      .slice(0, 5)
    hoje.value = h.sort((x, y) => new Date(x.inicio) - new Date(y.inicio))
  } catch (e) {
    erro.value = e.message
  } finally {
    atualizando.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <div class="painel-cabecalho">
    <div class="cabeca-pagina">
      <span class="painel-sobretitulo">GESTÃO DA FROTA · SECRETARIA DE EDUCAÇÃO</span>
      <h1>Painel administrativo</h1>
      <p>Acompanhamento operacional das solicitações e da utilização dos veículos.</p>
    </div>
    <div class="painel-data">
      <span>REFERÊNCIA</span>
      <strong>{{ dataAtual }}</strong>
      <button class="sec painel-atualizar" :disabled="atualizando" @click="carregar">
        <span aria-hidden="true">↻</span> {{ atualizando ? 'Atualizando' : 'Atualizar dados' }}
      </button>
    </div>
  </div>

  <p v-if="erro" class="erro painel-erro" role="alert">{{ erro }}</p>

  <section class="painel-resumo" aria-label="Indicadores de reservas">
    <div class="painel-secao-titulo">
      <div><span class="painel-sobretitulo">RESUMO OPERACIONAL</span><h2>Indicadores de reservas</h2></div>
      <span class="painel-total" v-if="totalAcompanhado !== null">{{ totalAcompanhado }} registros acompanhados</span>
    </div>
    <div class="estatisticas">
      <RouterLink class="estat amarelo" to="/admin/gestao">
        <span class="estat-icone" aria-hidden="true">◷</span>
        <span class="estat-conteudo"><span class="estat-rotulo">Aguardando análise</span><strong class="num">{{ contagem.pendente ?? '–' }}</strong><span class="estat-ajuda">Solicitações pendentes de aprovação</span></span>
        <span class="estat-seta" aria-hidden="true">↗</span>
      </RouterLink>
      <RouterLink class="estat verde" to="/admin/gestao?aba=aprovada">
        <span class="estat-icone" aria-hidden="true">✓</span>
        <span class="estat-conteudo"><span class="estat-rotulo">Aprovadas</span><strong class="num">{{ contagem.aprovada ?? '–' }}</strong><span class="estat-ajuda">Aguardando retirada do veículo</span></span>
        <span class="estat-seta" aria-hidden="true">↗</span>
      </RouterLink>
      <RouterLink class="estat azul" to="/admin/gestao?aba=em_uso">
        <span class="estat-icone" aria-hidden="true">▣</span>
        <span class="estat-conteudo"><span class="estat-rotulo">Em utilização</span><strong class="num">{{ contagem.em_uso ?? '–' }}</strong><span class="estat-ajuda">Veículos atualmente em uso</span></span>
        <span class="estat-seta" aria-hidden="true">↗</span>
      </RouterLink>
    </div>
  </section>

  <section class="painel-operacao">
    <div class="painel-secao-titulo">
      <div><span class="painel-sobretitulo">ACOMPANHAMENTO</span><h2>Atividades da frota</h2></div>
      <RouterLink class="painel-link" to="/admin/gestao">Acessar gestão completa <span aria-hidden="true">→</span></RouterLink>
    </div>
    <div class="duas-colunas painel-colunas">
      <section class="cartao painel-lista">
        <div class="painel-card-cabecalho"><div><h2>Solicitações pendentes</h2><p>Pedidos mais antigos que aguardam avaliação.</p></div><span class="painel-contador">{{ pendentes.length }}</span></div>
        <ul v-if="pendentes.length" class="lista-simples">
          <li v-for="r in pendentes" :key="r.id">
            <span class="painel-item-principal"><strong>{{ r.veiculo_nome }}</strong><span class="pequeno">{{ r.solicitante_nome }} · {{ fmtDataHora(r.inicio) }}</span></span>
            <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
          </li>
        </ul>
        <div v-else class="painel-vazio"><span class="painel-vazio-icone">✓</span><strong>Nenhuma solicitação pendente</strong><span>Não há pedidos aguardando aprovação neste momento.</span></div>
        <div class="acoes"><RouterLink to="/admin/gestao" class="painel-acao-secundaria">Revisar solicitações <span aria-hidden="true">→</span></RouterLink></div>
      </section>

      <section class="cartao painel-lista">
        <div class="painel-card-cabecalho"><div><h2>Movimentações de hoje</h2><p>Reservas aprovadas e veículos em utilização.</p></div><span class="painel-contador">{{ hoje.length }}</span></div>
        <ul v-if="hoje.length" class="lista-simples">
          <li v-for="r in hoje" :key="r.id">
            <span class="painel-item-principal"><strong>{{ r.veiculo_nome }}</strong><span class="pequeno">{{ r.solicitante_nome }} · {{ fmtHora(r.inicio) }} às {{ fmtHora(r.fim) }}</span></span>
            <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
          </li>
        </ul>
        <div v-else class="painel-vazio"><span class="painel-vazio-icone">—</span><strong>Nenhuma movimentação prevista</strong><span>Não há reservas ativas para hoje.</span></div>
        <div class="acoes"><RouterLink to="/admin/calendario" class="painel-acao-secundaria">Consultar calendário <span aria-hidden="true">→</span></RouterLink></div>
      </section>
    </div>
  </section>
</template>
