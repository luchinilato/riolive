/* Rotas reais (History API): todo recorte é um link — requisito do produto. */

import type { EstadoUi } from './modelo/tipos'

const TEMAS = [
  'chuva', 'mobilidade', 'transito', 'previsao', 'seguranca', 'ar',
  'mar', 'ceu', 'queimadas', 'cidade', 'navios',
]

/* As mesmas quatro que a API aceita. Zona escrita errada na URL vira cidade
   inteira, não erro: link torto não deve deixar o painel em branco, e a API
   recusaria com 422 uma zona que ela não conhece. */
export const ZONAS = ['centro', 'sul', 'norte', 'oeste']

export function estadoDaUrl(): Partial<EstadoUi> {
  const caminho = window.location.pathname
  const consulta = new URLSearchParams(window.location.search)
  const zona = consulta.get('zona')
  const comum: Partial<EstadoUi> = {
    zone: zona && ZONAS.includes(zona) ? zona : null,
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
