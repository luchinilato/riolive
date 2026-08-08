/* Gerado do handoff do Claude Design (seção seguranca) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { Recorte } from '../componentes/Recorte'

export function PainelSeguranca({ m }: { m: Modelo }) {
  const { hexes, lay, openSeguranca, seguranca, segurancaIspLinha } = m
  return (
    <>
{/* SEGURANÇA */}
          <div onClick={openSeguranca} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.seguranca.s}`, order: `${lay.seguranca.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={seguranca.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${seguranca.sev.c}`, color: `${seguranca.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{seguranca.sev.i} {seguranca.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Segurança</span>
              <Recorte marca={m.recortes?.seguranca} />
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{seguranca.count}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', flexDirection: 'column', gap: '6px', overflow: 'hidden'}}>
              <div style={{display: 'flex', alignItems: 'baseline', gap: '6px', minWidth: '0'}}>
                <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{seguranca.hero}</span>
                <span style={{fontSize: '11px', color: 'var(--tx2)', minWidth: '0'}}>ocorrências de tiro · 24 h</span>
              </div>
              <div style={{fontSize: '11px', color: 'var(--tx2)', lineHeight: '1.4'}}>{seguranca.sub}</div>
              <div style={{flex: '1 1 auto', minHeight: '30px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--bg2)', position: 'relative', overflow: 'hidden'}}>
                {(hexes as any[]).map((h: any, hI: number) => (<React.Fragment key={hI}>
                  <span style={{position: 'absolute', left: `${h.x}%`, top: `${h.y}%`, width: '13px', height: '13px', background: `${h.c}`, clipPath: 'polygon(25% 5%,75% 5%,100% 50%,75% 95%,25% 95%,0% 50%)'}}></span>
                </React.Fragment>))}
                <div style={{position: 'absolute', left: '6px', bottom: '5px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>H3 · 24H</div>
              </div>
              <div style={{flex: '0 0 auto', fontSize: '10px', color: 'var(--tx2)', lineHeight: '1.3'}}>{segurancaIspLinha ?? 'série mensal do ISP desde 2003 no dossiê'}</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: FOGO CRUZADO + ISP · HÁ 12 MIN
            </div>
          </div>
    </>
  )
}
