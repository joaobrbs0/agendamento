export const ROTULO_STATUS = {
  pendente: 'Pendente',
  aprovada: 'Aprovada',
  em_uso: 'Em uso',
  concluida: 'Concluída',
  recusada: 'Recusada',
  cancelada: 'Cancelada',
}

const dh = new Intl.DateTimeFormat('pt-BR', {
  day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit',
})
const hora = new Intl.DateTimeFormat('pt-BR', { hour: '2-digit', minute: '2-digit' })
const diaCurto = new Intl.DateTimeFormat('pt-BR', {
  weekday: 'short', day: '2-digit', month: '2-digit',
})

export const fmtDataHora = (iso) => dh.format(new Date(iso))
export const fmtHora = (iso) => hora.format(new Date(iso))
export const fmtDiaCurto = (d) => diaCurto.format(d)

export function mesmoDia(a, b) {
  return a.getFullYear() === b.getFullYear()
    && a.getMonth() === b.getMonth()
    && a.getDate() === b.getDate()
}

// Segunda-feira 00:00 (horário local) da semana da data informada.
export function segundaDaSemana(data) {
  const d = new Date(data)
  d.setHours(0, 0, 0, 0)
  const deslocamento = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - deslocamento)
  return d
}

export function somarDias(data, n) {
  const d = new Date(data)
  d.setDate(d.getDate() + n)
  return d
}

// Valor de <input type="datetime-local"> -> ISO em UTC para a API.
export const localParaIso = (valor) => new Date(valor).toISOString()
