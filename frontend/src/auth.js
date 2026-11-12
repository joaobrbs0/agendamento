import { reactive } from 'vue'
import { api, tokens } from './api'

export const sessao = reactive({ usuario: null })

export async function entrarComGoogle(credencial) {
  try {
    const d = await api('/login/google/', {
      metodo: 'POST',
      corpo: { credential: credencial },
      semRenovar: true,
    })
    tokens.salvar(d.access, d.refresh)
  } catch (e) {
    sair()
    throw e
  }
  await carregarEu()
}

export async function carregarEu() {
  sessao.usuario = await api('/eu/')
  return sessao.usuario
}

export function sair() {
  tokens.limpar()
  sessao.usuario = null
}