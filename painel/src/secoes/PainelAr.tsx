/* Gerado do handoff do Claude Design (seção ar) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { BarraRegua } from '../componentes/Regua'
import { Recorte } from '../componentes/Recorte'

export function PainelAr({ m }: { m: Modelo }) {
  const { ar, lay, openAr } = m
  return (
    <>
{/* QUALIDADE DO AR */}
          <div onClick={openAr} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.ar.s}`, order: `${lay.ar.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={ar.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${ar.sev.c}`, color: `${ar.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{ar.sev.i} {ar.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Qualidade do ar</span>
              <Recorte marca={m.recortes?.ar} />
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
              <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '28px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: `${ar.hc}`}}>{ar.hero}</span>
              <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{ar.heroSub}</span>
            </div>
            <BarraRegua regua={ar.regua} />
            <div style={{flex: '1 1 auto', minHeight: '0', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column', gap: '6px', paddingTop: '2px'}}>
              {(ar.rows as any[]).map((r: any, rI: number) => (<React.Fragment key={rI}>
                <div style={{display: 'flex', flexDirection: 'column', gap: '3px'}}>
                  <div style={{display: 'flex', justifyContent: 'space-between', fontSize: '11px'}}><span style={{color: 'var(--tx)'}}>{r.n}</span><span style={{fontFamily: "'JetBrains Mono',monospace", color: 'var(--tx2)'}}>{r.v}</span></div>
                  <div style={{height: '4px', background: 'var(--bd2)', borderRadius: '2px', overflow: 'hidden'}}><span style={{display: 'block', height: '4px', width: `${r.p}%`, background: `${r.c}`}}></span></div>
                </div>
              </React.Fragment>))}
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: OPENAQ · HÁ 20 MIN
            </div>
          </div>
    </>
  )
}
