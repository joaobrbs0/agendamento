import { createRouter, createWebHistory } from 'vue-router'
import { tokens } from './api'
import { sessao, carregarEu, sair } from './auth'

import LoginView from './views/LoginView.vue'
import CalendarioView from './views/CalendarioView.vue'
import NovaReservaView from './views/NovaReservaView.vue'
import MinhasView from './views/MinhasView.vue'
import GestaoView from './views/GestaoView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { publica: true } },
    { path: '/', name: 'calendario', component: CalendarioView },
    { path: '/nova', name: 'nova', component: NovaReservaView },
    { path: '/minhas', name: 'minhas', component: MinhasView },
    { path: '/gestao', name: 'gestao', component: GestaoView, meta: { gestor: true } },
    { path: '/:resto(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.publica) {
    if (tokens.acesso && to.name === 'login') return { name: 'calendario' }
    return true
  }
  if (!tokens.acesso) return { name: 'login' }
  if (!sessao.usuario) {
    try {
      await carregarEu()
    } catch {
      sair()
      return { name: 'login' }
    }
  }
  if (to.meta.gestor && !sessao.usuario.gestor) return { name: 'calendario' }
  return true
})

window.addEventListener('frota:sessao-expirada', () => {
  sair()
  router.push({ name: 'login' })
})

export default router
