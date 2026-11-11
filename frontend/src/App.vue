<script setup>
import { useRouter } from 'vue-router'
import { sessao, sair } from './auth'

const router = useRouter()

function deslogar() {
  sair()
  router.push({ name: 'login' })
}
</script>

<template>
  <header v-if="sessao.usuario" class="topo">
    <strong class="marca">Frota</strong>
    <nav>
      <RouterLink to="/">Calendário</RouterLink>
      <RouterLink to="/nova">Nova reserva</RouterLink>
      <RouterLink to="/minhas">Minhas reservas</RouterLink>
      <RouterLink v-if="sessao.usuario.gestor" to="/gestao">Gestão</RouterLink>
    </nav>
    <span class="usuario">
      {{ sessao.usuario.nome }}
      <button class="link" @click="deslogar">Sair</button>
    </span>
  </header>
  <main class="conteudo">
    <RouterView />
  </main>
</template>
