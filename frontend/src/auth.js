import { reactive } from 'vue'
import { api, tokens, ErroApi } from './api'

export const sessao = reactive({ usuario: null })

export async function entrar(usuario, senha) {
  try {
    const d = await api('/login/', {
      metodo: 'POST',
      corpo: { username: usuario, password: senha },
      semRenovar: true,
    })
    tokens.salvar(d.access, d.refresh)
  } catch (e) {
    if (e instanceof ErroApi && e.status === 401) {
      throw new ErroApi('Usuário ou senha incorretos.', 401)
    }
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
