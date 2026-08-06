/* Cockpit do painel — estrutura raiz portada do handoff do Claude Design. */

import { useEffect, useState } from 'react'
import type { EstadoUi } from './modelo/tipos'
import { modeloBase } from './modelo/base'
import { aplicarDadosReais, useDadosReais } from './modelo/dadosReais'
import { Cabecalho } from './secoes/Cabecalho'
import { Ticker } from './secoes/Ticker'
import { PainelChuva } from './secoes/PainelChuva'
import { PainelMobilidade } from './secoes/PainelMobilidade'
import { PainelTransito } from './secoes/PainelTransito'
import { PainelPrevisao } from './secoes/PainelPrevisao'
import { PainelSeguranca } from './secoes/PainelSeguranca'
import { PainelAr } from './secoes/PainelAr'
import { PainelMar } from './secoes/PainelMar'
import { PainelCeu } from './secoes/PainelCeu'
import { PainelMemoria } from './secoes/PainelMemoria'
import { PainelQueimadas } from './secoes/PainelQueimadas'
import { PainelCidadeViva } from './secoes/PainelCidadeViva'
import { PainelNavios } from './secoes/PainelNavios'
import { Feed } from './secoes/Feed'
import { VistaMapa } from './secoes/VistaMapa'
import { VistaStatus } from './secoes/VistaStatus'
import { VistaMobile } from './secoes/VistaMobile'
import { Rodape } from './secoes/Rodape'
import { Dossie } from './secoes/Dossie'

const ESTADO_INICIAL: EstadoUi = {
  theme: 'escuro', mode: 'calmo', zone: null, route: 'home', dossier: null,
  onlyAbn: false, paused: false, copied: false, quoted: false, zonePicker: false,
  device: 'desktop', mtab: 'cards', period: '24h',
}

export default function App() {
  const [ui, setUi] = useState<EstadoUi>(ESTADO_INICIAL)

  useEffect(() => {
    const medir = () => setUi((u) => ({ ...u, vw: window.innerWidth, vh: window.innerHeight }))
    medir()
    window.addEventListener('resize', medir)
    return () => window.removeEventListener('resize', medir)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.tema = ui.theme
  }, [ui.theme])

  const acoes = {
    defina: (parcial: Partial<EstadoUi>) => setUi((u) => ({ ...u, ...parcial })),
    aplicarTema: (t: 'escuro' | 'claro') => setUi((u) => ({ ...u, theme: t })),
    piscar: (k: 'copied' | 'quoted') => {
      setUi((u) => ({ ...u, [k]: true }))
      setTimeout(() => setUi((u) => ({ ...u, [k]: false })), 1400)
    },
  }

  const dados = useDadosReais(ui)
  const m = aplicarDadosReais(modeloBase(ui, acoes), dados)

  const emDossie = m.dossier != null

  // ≤640px: pilha rolável (DEC do layout) — sem o palco escalado do desktop
  if ((ui.vw ?? 1440) <= 640) {
    return <VistaMobile m={m} />
  }

  return (
    <div style={{ height: '100vh', width: '100%', overflow: 'hidden', background: 'var(--bg)',
      color: 'var(--tx)', fontFamily: 'Inter,system-ui,sans-serif', fontSize: '12px',
      display: 'flex', flexDirection: 'column', fontFeatureSettings: "'tnum' 1" }}>
      <div style={{ width: '100vw', height: '100vh', overflow: 'hidden' }}>
        <div style={{ width: `${m.stage.w}px`, height: `${m.stage.h}px`, transform: m.stage.t,
          transformOrigin: 'top left', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

          <Cabecalho m={m} />
          <Ticker m={m} />

          {emDossie ? (
            <Dossie m={m} />
          ) : m.isMapa ? (
            <VistaMapa m={m} />
          ) : m.isStatus ? (
            <VistaStatus m={m} />
          ) : (
            <div style={{ flex: '1 1 auto', minHeight: 0, display: 'flex', gap: '12px', padding: '12px 16px' }}>
              <div style={{ flex: '1 1 auto', minWidth: 0, display: 'grid',
                gridTemplateColumns: 'repeat(5,1fr)', gridTemplateRows: 'repeat(3,1fr)', gap: '12px' }}>
                <PainelChuva m={m} />
                <PainelMobilidade m={m} />
                <PainelTransito m={m} />
                <PainelPrevisao m={m} />
                <PainelSeguranca m={m} />
                <PainelAr m={m} />
                <PainelMar m={m} />
                <PainelCeu m={m} />
                <PainelMemoria m={m} />
                <PainelQueimadas m={m} />
                <PainelCidadeViva m={m} />
                <PainelNavios m={m} />
              </div>
              <Feed m={m} />
            </div>
          )}

          <Rodape m={m} />
        </div>
      </div>
    </div>
  )
}
