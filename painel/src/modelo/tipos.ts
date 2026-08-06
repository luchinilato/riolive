/* Tipos do view-model — o contrato entre a lógica e as seções gerado do handoff.
   Pragmático nesta fase: o modelo é um dicionário; tipagem fina vem com a estabilização. */

export type Modelo = Record<string, any>

export interface EstadoUi {
  theme: 'escuro' | 'claro'
  mode: 'calmo' | 'crise'
  zone: string | null
  route: string
  dossier: string | null
  onlyAbn: boolean
  paused: boolean
  copied: boolean
  quoted: boolean
  zonePicker: boolean
  device: 'desktop' | 'mobile'
  mtab: 'cards' | 'feed'
  period: '24h' | '7d' | '30d'
  preset?: string
  vw?: number
  vh?: number
}

export interface Acoes {
  defina: (parcial: Partial<EstadoUi>) => void
  aplicarTema: (t: 'escuro' | 'claro') => void
  piscar: (k: 'copied' | 'quoted') => void
}
