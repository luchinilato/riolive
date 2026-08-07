/* Rotas reais (History API): todo recorte é um link — requisito do produto. */

import type { EstadoUi } from './modelo/tipos'

const TEMAS = [
  'chuva', 'mobilidade', 'transito', 'previsao', 'seguranca', 'ar',
  'mar', 'ceu', 'queimadas', 'cidade', 'navios',
]

export function estadoDaUrl(): Partial<EstadoUi> {
  const caminho = window.location.pathname
  const consulta = new URLSearchParams(window.location.search)
  const comum: Partial<EstadoUi> = {
    zone: consulta.get('zona'),
    period: (consulta.get('periodo') as EstadoUi['period']) ?? '24h',
  }
  if (caminho === '/mapa') return { ...comum, route: 'mapa', dossier: null }
  if (caminho === '/status') return { ...comum, route: 'status', dossier: null }
  if (caminho === '/nerds') return { ...comum, route: 'nerds', dossier: null }
  const tema = caminho.slice(1)
  if (TEMAS.includes(tema)) return { ...comum, route: tema, dossier: tema }
  return { ...comum, route: 'home', dossier: null }
}

export function urlDoEstado(ui: EstadoUi): string {
  const consulta = new URLSearchParams()
  if (ui.zone) consulta.set('zona', ui.zone)
  if (ui.dossier && ui.period !== '24h') consulta.set('periodo', ui.period)
  const caminho = ui.route === 'home' ? '/' : `/${ui.route}`
  const s = consulta.toString()
  return caminho + (s ? `?${s}` : '')
}
