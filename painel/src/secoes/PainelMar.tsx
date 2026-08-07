/* Gerado do handoff do Claude Design (seção mar) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { BarraRegua } from '../componentes/Regua'

export function PainelMar({ m }: { m: Modelo }) {
  const { lay, mar, openMar } = m
  return (
    <>
{/* MAR E PRAIAS */}
          <div onClick={openMar} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.mar.s}`, order: `${lay.mar.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={mar.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${mar.sev.c}`, color: `${mar.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{mar.sev.i} {mar.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Mar e praias</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{mar.count ?? ''}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
              <span style={{flex: '0 0 auto', whiteSpace: 'nowrap', fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: `${mar.hc}`}}>{mar.hero}</span>
              <span style={{minWidth: '0', fontSize: '11px', color: 'var(--tx2)'}}>{mar.heroSub}</span>
            </div>
            <BarraRegua regua={mar.regua} />
            <div style={{flex: '1 1 auto', minHeight: '0', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column', gap: '6px'}}>
              <div style={{display: 'flex', gap: '6px'}}>
                <div style={{flex: '1', border: '1px solid var(--bd2)', borderRadius: '6px', padding: '6px 8px'}}>
                  <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '20px', color: 'var(--s1)', lineHeight: '1'}}>{mar.proprias}</div>
                  <div style={{fontSize: '10px', color: 'var(--tx2)', marginTop: '2px'}}>próprias</div>
                </div>
                <div style={{flex: '1', border: '1px solid var(--bd2)', borderRadius: '6px', padding: '6px 8px'}}>
                  <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '20px', color: 'var(--s3)', lineHeight: '1'}}>{mar.improprias}</div>
                  <div style={{fontSize: '10px', color: 'var(--tx2)', marginTop: '2px'}}>impróprias</div>
                </div>
              </div>
              <div style={{fontSize: '11px', color: 'var(--tx2)', lineHeight: '1.4'}}>{mar.list}</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>OPEN-METEO MARINE · COPACABANA
            </div>
          </div>
    </>
  )
}
