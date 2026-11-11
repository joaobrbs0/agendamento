<script setup>
import { ref, reactive, onMounted } from 'vue'
import { api } from '../api'
import { ROTULO_STATUS, fmtDataHora, fmtHora, somarDias } from '../formatar'

const contagem = reactive({ pendente: null, aprovada: null, em_uso: null })
const pendentes = ref([])
const hoje = ref([])
const erro = ref('')

async function carregar() {
  erro.value = ''
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
  }
}

onMounted(carregar)
</script>

<template>
  <div class="cabeca-pagina">
    <h1>Painel administrativo</h1>
    <p>Visão geral das reservas da frota.</p>
  </div>

  <p v-if="erro" class="erro">{{ erro }}</p>

  <div class="estatisticas">
    <RouterLink class="estat amarelo" to="/admin/gestao">
      <div class="num">{{ contagem.pendente ?? '–' }}</div>
      <div class="rot">Pendentes de aprovação</div>
    </RouterLink>
    <RouterLink class="estat verde" to="/admin/gestao?aba=aprovada">
      <div class="num">{{ contagem.aprovada ?? '–' }}</div>
      <div class="rot">Aprovadas, aguardando retirada</div>
    </RouterLink>
    <RouterLink class="estat azul" to="/admin/gestao?aba=em_uso">
      <div class="num">{{ contagem.em_uso ?? '–' }}</div>
      <div class="rot">Veículos em uso</div>
    </RouterLink>
  </div>

  <div class="duas-colunas">
    <div class="cartao">
      <h2>Pedidos pendentes mais antigos</h2>
      <p v-if="!pendentes.length" class="vazio">Nenhum pedido pendente.</p>
      <ul class="lista-simples">
        <li v-for="r in pendentes" :key="r.id">
          <span>
            <strong>{{ r.veiculo_nome }}</strong><br />
            <span class="pequeno">{{ r.solicitante_nome }} · {{ fmtDataHora(r.inicio) }}</span>
          </span>
          <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
        </li>
      </ul>
      <div class="acoes">
        <RouterLink to="/admin/gestao"><button>Analisar pedidos</button></RouterLink>
      </div>
    </div>

    <div class="cartao">
      <h2>Saídas e usos de hoje</h2>
      <p v-if="!hoje.length" class="vazio">Nenhuma reserva ativa hoje.</p>
      <ul class="lista-simples">
        <li v-for="r in hoje" :key="r.id">
          <span>
            <strong>{{ r.veiculo_nome }}</strong><br />
            <span class="pequeno">{{ r.solicitante_nome }} · {{ fmtHora(r.inicio) }} às {{ fmtHora(r.fim) }}</span>
          </span>
          <span :class="['selo', r.status]">{{ ROTULO_STATUS[r.status] }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
