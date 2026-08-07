/* Gerado do handoff do Claude Design (seção ticker) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Ticker({ m }: { m: Modelo }) {
  const { pauseTicker, resumeTicker, tickerLoop, tickerState } = m
  return (
    <>
{/* ================= TICKER ================= */}
    <div onMouseEnter={pauseTicker} onMouseLeave={resumeTicker} style={{flex: '0 0 30px', height: '30px', borderBottom: '1px solid var(--bd)', background: 'var(--bg2)', overflow: 'hidden', position: 'relative', display: 'flex', alignItems: 'center'}}>
      <div style={{position: 'absolute', left: '0', top: '0', bottom: '0', width: '44px', zIndex: '2', background: 'linear-gradient(90deg,var(--bg2),transparent)'}}></div>
      <div style={{position: 'absolute', right: '0', top: '0', bottom: '0', width: '44px', zIndex: '2', background: 'linear-gradient(270deg,var(--bg2),transparent)'}}></div>
      <div style={{display: 'flex', width: 'max-content', animation: 'tick 62s linear infinite', animationPlayState: `${tickerState}`}}>
        {(tickerLoop as any[]).map((t: any, tI: number) => (<React.Fragment key={tI}>
          <div style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '0 14px', borderRight: '1px solid var(--bd2)', whiteSpace: 'nowrap', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', letterSpacing: '.04em'}}>
            <span style={{color: 'var(--tx3)'}}>{t.k}</span>
            <span style={{color: 'var(--tx)', fontWeight: '500'}}>{t.v}</span>
            <span style={{color: `${t.dc}`}}>{t.d}</span>
          </div>
        </React.Fragment>))}
      </div>
    </div>
    </>
  )
}
