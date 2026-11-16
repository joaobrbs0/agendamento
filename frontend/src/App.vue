<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { sessao, sair } from './auth'
import Icone from './components/Icone.vue'

const route = useRoute()
const router = useRouter()
const menuAberto = ref(false)

const logado = computed(() => Boolean(sessao.usuario) && !route.meta.publica)
const admin = computed(() => route.meta.area === 'admin')
const paginaAtual = computed(() => {
  const atual = [...itens.value].find((item) => item.para === route.path)
  return atual?.texto || 'Área de trabalho'
})

const itens = computed(() => admin.value
  ? [
      { para: '/admin', icone: 'painel', texto: 'Visão geral' },
      { para: '/admin/calendario', icone: 'calendario', texto: 'Calendário da frota' },
      { para: '/admin/gestao', icone: 'gestao', texto: 'Gestão de reservas' },
      { para: '/admin/veiculos', icone: 'carro', texto: 'Cadastro de veículos' },
    ]
  : [
      { para: '/', icone: 'calendario', texto: 'Calendário' },
      { para: '/nova', icone: 'nova', texto: 'Solicitar veículo' },
      { para: '/minhas', icone: 'minhas', texto: 'Minhas solicitações' },
    ])

watch(() => route.fullPath, () => { menuAberto.value = false })

function deslogar() {
  sair()
  router.push({ name: 'login' })
}
</script>

<template>
  <div v-if="logado" class="app">
    <header class="topo">
      <button class="btn-menu" aria-label="Abrir menu" @click="menuAberto = !menuAberto">
        <Icone nome="menu" />
      </button>
      <div class="marca">
        <span class="brasao"><Icone nome="escudo" /></span>
        <span class="marca-texto">
          <strong>Prefeitura de Joinville</strong>
          <small>Secretaria de Educação · Gestão de Transporte</small>
        </span>
      </div>
      <div class="topo-contexto">SISTEMA DE GESTÃO DE VEÍCULOS</div>
      <div class="usuario">
        <span class="quem">
          {{ sessao.usuario.nome }}
          <small>{{ admin ? 'GESTÃO ADMINISTRATIVA' : 'ÁREA DO SOLICITANTE' }}</small>
        </span>
        <span class="avatar"><Icone nome="usuario" /></span>
      </div>
    </header>

    <div :class="['fundo-menu', { aberta: menuAberto }]" @click="menuAberto = false" />

    <aside :class="['lateral', { aberta: menuAberto }]">
      <div class="lateral-identificacao">
        <span class="lateral-sobretitulo">AMBIENTE DE TRABALHO</span>
        <strong>{{ admin ? 'Administração' : 'Solicitações' }}</strong>
        <small>{{ admin ? 'Controle operacional da frota' : 'Acesso aos serviços de transporte' }}</small>
      </div>
      <div class="nav-titulo">MENU PRINCIPAL</div>
      <nav>
        <RouterLink v-for="i in itens" :key="i.para" :to="i.para" :exact-active-class="'router-link-exact-active'">
          <Icone :nome="i.icone" /> <span>{{ i.texto }}</span>
        </RouterLink>
      </nav>
      <div class="rodape">
        <div class="rodape-unidade">
          <span class="unidade-indicador" />
          <span><strong>Secretaria de Educação</strong><small>Prefeitura de Joinville</small></span>
        </div>
        <RouterLink v-if="sessao.usuario.gestor" :to="admin ? '/' : '/admin'">
          <Icone nome="troca" /> {{ admin ? 'Acessar área do usuário' : 'Acessar administração' }}
        </RouterLink>
        <button class="item" @click="deslogar"><Icone nome="sair" /> Encerrar sessão</button>
      </div>
    </aside>

    <main class="conteudo">
      <div class="trilha-pagina">
        <span>Secretaria de Educação</span><span class="trilha-separador">/</span><strong>{{ paginaAtual }}</strong>
      </div>
      <RouterView :key="route.fullPath" />
      <footer class="rodape-conteudo">Sistema de Gestão de Veículos <span>·</span> Prefeitura de Joinville</footer>
    </main>
  </div>

  <RouterView v-else />
</template>
