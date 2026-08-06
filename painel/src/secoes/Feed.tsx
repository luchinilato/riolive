/* Gerado do handoff do Claude Design (seção feed) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Feed({ m }: { m: Modelo }) {
  const { abn, feed, feedCount, toggleAbnormal } = m
  return (
    <>
{/* FEED */}
        <div style={{flex: '0 0 320px', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
          <div style={{flex: '0 0 auto', padding: '10px 12px', borderBottom: '1px solid var(--bd2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <span style={{width: '6px', height: '6px', borderRadius: '50%', background: 'var(--live)', animation: 'pulse 2s infinite'}}></span>
            <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>Agora na cidade</span>
            <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{feedCount}</span>
          </div>
          <div style={{flex: '0 0 auto', padding: '8px 12px', borderBottom: '1px solid var(--bd2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <div onClick={toggleAbnormal} style={{width: '28px', height: '16px', borderRadius: '8px', background: `${abn.track}`, position: 'relative', cursor: 'pointer', transition: 'background .15s'}}>
              <span style={{position: 'absolute', top: '2px', left: `${abn.x}px`, width: '12px', height: '12px', borderRadius: '50%', background: 'var(--tx)', transition: 'left .15s'}}></span>
            </div>
            <span onClick={toggleAbnormal} style={{fontSize: '11px', color: `${abn.c}`, cursor: 'pointer'}}>só o anormal <span style={{color: 'var(--tx3)'}}>(severidade ≥ 2)</span></span>
          </div>
          <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'auto', position: 'relative'}}>
            {(feed as any[]).map((f: any, fI: number) => (<React.Fragment key={fI}>
              <div style={{display: 'flex', gap: '9px', padding: '9px 12px', borderBottom: '1px solid var(--bd3)', cursor: 'pointer'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', flex: '0 0 34px', paddingTop: '1px'}}>{f.h}</span>
                <span style={{flex: '0 0 auto', paddingTop: '1px', fontSize: '9px', color: `${f.sev.c}`}}>{f.sev.i}</span>
                <span style={{flex: '1 1 auto', minWidth: '0', fontSize: '11.5px', color: 'var(--tx)', lineHeight: '1.4', textWrap: 'pretty'}}>{f.txt}<span style={{color: 'var(--tx3)'}}> · {f.src}</span></span>
              </div>
            </React.Fragment>))}
          </div>
          <div style={{flex: '0 0 auto', height: '22px', marginTop: '-22px', pointerEvents: 'none', background: 'linear-gradient(180deg,transparent,var(--card))'}}></div>
        </div>
    </>
  )
}
