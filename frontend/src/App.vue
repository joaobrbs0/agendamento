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

const itens = computed(() => admin.value
  ? [
      { para: '/admin', icone: 'painel', texto: 'Painel' },
      { para: '/admin/calendario', icone: 'calendario', texto: 'Calendário' },
      { para: '/admin/gestao', icone: 'gestao', texto: 'Gestão de reservas' },
    ]
  : [
      { para: '/', icone: 'calendario', texto: 'Calendário' },
      { para: '/nova', icone: 'nova', texto: 'Nova reserva' },
      { para: '/minhas', icone: 'minhas', texto: 'Minhas reservas' },
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
          <small>Reserva de Veículos</small>
        </span>
      </div>
      <div class="usuario">
        <span class="quem">
          {{ sessao.usuario.nome }}
          <small>{{ admin ? 'Administrador' : 'Usuário' }}</small>
        </span>
        <span class="avatar"><Icone nome="usuario" /></span>
      </div>
    </header>

    <div :class="['fundo-menu', { aberta: menuAberto }]" @click="menuAberto = false" />

    <aside :class="['lateral', { aberta: menuAberto }]">
      <div class="titulo">
        {{ admin ? 'Painel administrativo' : 'Minha área' }}
        <small>{{ admin ? 'Gestão da frota' : 'Reservas de veículos' }}</small>
      </div>
      <nav>
        <RouterLink v-for="i in itens" :key="i.para" :to="i.para">
          <Icone :nome="i.icone" /> {{ i.texto }}
        </RouterLink>
      </nav>
      <div class="rodape">
        <RouterLink v-if="sessao.usuario.gestor" :to="admin ? '/' : '/admin'">
          <Icone nome="troca" /> {{ admin ? 'Ir para a área do usuário' : 'Ir para o painel admin' }}
        </RouterLink>
        <button class="item" @click="deslogar"><Icone nome="sair" /> Sair</button>
      </div>
    </aside>

    <main class="conteudo">
      <RouterView :key="route.fullPath" />
    </main>
  </div>

  <RouterView v-else />
</template>
