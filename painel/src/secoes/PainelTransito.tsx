/* Gerado do handoff do Claude Design (seção transito) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { BarraRegua } from '../componentes/Regua'
import { Recorte } from '../componentes/Recorte'

export function PainelTransito({ m }: { m: Modelo }) {
  const { lay, openTransito, transito } = m
  return (
    <>
{/* TRÂNSITO */}
          <div onClick={openTransito} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.transito.s}`, order: `${lay.transito.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={transito.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${transito.sev.c}`, color: `${transito.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{transito.sev.i} {transito.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Trânsito</span>
              <Recorte marca={m.recortes?.transito} />
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{transito.count}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
              <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{transito.hero}</span>
              <span style={{fontSize: '11px', color: 'var(--tx2)'}}>km/h médios</span>
            </div>
            <div style={{fontSize: '11px', color: 'var(--tx2)'}}>{transito.sub}</div>
                <BarraRegua regua={transito.regua} />
            <div style={{flex: '1 1 auto', minHeight: '0', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column', gap: '1px'}}>
              {(transito.rows as any[]).map((r: any, rI: number) => (<React.Fragment key={rI}>
                <div style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '3px 0', borderBottom: '1px solid var(--bd3)'}}>
                  <span style={{flex: '1 1 auto', minWidth: '0', fontSize: '11px', color: 'var(--tx)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{r.n}</span>
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', color: 'var(--tx)'}}>{r.v}</span>
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: `${r.dc}`, width: '10px'}}>{r.d}</span>
                </div>
              </React.Fragment>))}
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: SMTR/TOMTOM · HÁ 5 MIN
            </div>
          </div>
    </>
  )
}
