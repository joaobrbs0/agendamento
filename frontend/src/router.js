import { createRouter, createWebHistory } from 'vue-router'
import { tokens } from './api'
import { sessao, carregarEu, sair } from './auth'

import LoginView from './views/LoginView.vue'
import CalendarioView from './views/CalendarioView.vue'
import NovaReservaView from './views/NovaReservaView.vue'
import MinhasView from './views/MinhasView.vue'
import PainelView from './views/PainelView.vue'
import GestaoView from './views/GestaoView.vue'
import VeiculosView from './views/veiculosview.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', name: 'login', component: LoginView, meta: { publica: true } },

    // Acesso do usuário
    { path: '/', name: 'calendario', component: CalendarioView, meta: { area: 'usuario' } },
    { path: '/nova', name: 'nova', component: NovaReservaView, meta: { area: 'usuario' } },
    { path: '/minhas', name: 'minhas', component: MinhasView, meta: { area: 'usuario' } },

    // Acesso do administrador (gestor)
    { path: '/admin', name: 'painel', component: PainelView, meta: { area: 'admin' } },
    { path: '/admin/calendario', name: 'admin-calendario', component: CalendarioView, meta: { area: 'admin' } },
    { path: '/admin/gestao', name: 'gestao', component: GestaoView, meta: { area: 'admin' } },
    { path: '/admin/veiculos', name: 'veiculos', component: VeiculosView, meta: { area: 'admin' } },

    { path: '/:resto(.*)*', redirect: '/' },
  ],
})

router.beforeEach(async (to) => {
  if (to.meta.publica) {
    if (tokens.acesso && to.name === 'login') {
      try {
        if (!sessao.usuario) await carregarEu()
        return { name: sessao.usuario.gestor ? 'painel' : 'calendario' }
      } catch {
        sair()
      }
    }
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
  if (to.meta.area === 'admin' && !sessao.usuario.gestor) return { name: 'calendario' }
  return true
})

window.addEventListener('frota:sessao-expirada', () => {
  sair()
  router.push({ name: 'login' })
})

export default router
