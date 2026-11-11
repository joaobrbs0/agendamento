const BASE = '/api'
const CHAVE_ACESSO = 'frota_access'
const CHAVE_REFRESH = 'frota_refresh'

export const tokens = {
  get acesso() { return localStorage.getItem(CHAVE_ACESSO) },
  get refresh() { return localStorage.getItem(CHAVE_REFRESH) },
  salvar(acesso, refresh) {
    if (acesso) localStorage.setItem(CHAVE_ACESSO, acesso)
    if (refresh) localStorage.setItem(CHAVE_REFRESH, refresh)
  },
  limpar() {
    localStorage.removeItem(CHAVE_ACESSO)
    localStorage.removeItem(CHAVE_REFRESH)
  },
}

export class ErroApi extends Error {
  constructor(mensagem, status, dados) {
    super(mensagem)
    this.status = status
    this.dados = dados
  }
}

// Transforma as respostas de erro do DRF em um texto só.
function mensagemDeErro(dados, status) {
  if (!dados) return `Erro ${status}.`
  if (typeof dados === 'string') return dados
  if (dados.detail) return String(dados.detail)
  const partes = []
  for (const [campo, valor] of Object.entries(dados)) {
    const texto = Array.isArray(valor) ? valor.join(' ') : String(valor)
    partes.push(campo === 'non_field_errors' ? texto : `${campo}: ${texto}`)
  }
  return partes.join(' ') || `Erro ${status}.`
}

let renovando = null

async function renovar() {
  if (!tokens.refresh) return false
  if (!renovando) {
    renovando = fetch(`${BASE}/login/renovar/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: tokens.refresh }),
    })
      .then(async (r) => {
        if (!r.ok) return false
        const d = await r.json()
        tokens.salvar(d.access, d.refresh)
        return true
      })
      .catch(() => false)
      .finally(() => { renovando = null })
  }
  return renovando
}

async function enviar(caminho, { metodo, corpo, params }) {
  let url = `${BASE}${caminho}`
  if (params) {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') qs.set(k, v)
    }
    const texto = qs.toString()
    if (texto) url += `?${texto}`
  }
  const headers = { 'Content-Type': 'application/json' }
  if (tokens.acesso) headers.Authorization = `Bearer ${tokens.acesso}`
  return fetch(url, {
    method: metodo,
    headers,
    body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
  })
}

export async function api(caminho, { metodo = 'GET', corpo, params, semRenovar = false } = {}) {
  let resp = await enviar(caminho, { metodo, corpo, params })

  if (resp.status === 401 && !semRenovar) {
    if (await renovar()) {
      resp = await enviar(caminho, { metodo, corpo, params })
    }
  }

  let dados = null
  const texto = await resp.text()
  if (texto) {
    try { dados = JSON.parse(texto) } catch { dados = texto }
  }

  if (!resp.ok) {
    if (resp.status === 401 && !semRenovar) {
      tokens.limpar()
      window.dispatchEvent(new Event('frota:sessao-expirada'))
    }
    throw new ErroApi(mensagemDeErro(dados, resp.status), resp.status, dados)
  }
  return dados
}
