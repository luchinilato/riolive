/* Gerado do handoff do Claude Design (seção memoria) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { Recorte } from '../componentes/Recorte'

export function PainelMemoria({ m }: { m: Modelo }) {
  const { copyQuote, lay, memoria, quoteLabel } = m
  return (
    <>
{/* CARTÃO DE MEMÓRIA */}
          <div style={{background: 'var(--hero-grad)', border: '1px solid var(--hero-bd)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', gridColumn: `span ${lay.memoria.s}`, order: `${lay.memoria.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--live-tx)', textTransform: 'uppercase'}}>Memória da cidade</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>SÉRIE 1997–2026</span>
              <Recorte marca={m.recortes?.memoria} />
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', gap: '14px', alignItems: 'stretch', overflow: 'hidden'}}>
              <div style={{flex: '1 1 0', minWidth: '0', minHeight: '0', overflowY: 'auto', overflowX: 'hidden'}}>
                <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '17px', fontWeight: '500', lineHeight: '1.3', color: 'var(--tx)', textWrap: 'pretty'}}>{memoria.quote1} <span style={{color: 'var(--live-tx)'}}>{memoria.quoteHi}</span> {memoria.quote2}</div>
                <div style={{fontSize: '11px', color: 'var(--tx2)', marginTop: '7px', lineHeight: '1.4'}}>{memoria.sub}</div>
              </div>
              <div style={{flex: '0 0 170px', display: 'flex', flexDirection: 'column', gap: '4px'}}>
                <div style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.08em'}}>AGOSTO · MM ACUMULADOS</div>
                <div style={{display: 'flex', alignItems: 'flex-end', gap: '3px', height: '56px'}}>
                  {(memoria.bars as any[]).map((b: any, bI: number) => (<React.Fragment key={bI}>
                    <span style={{flex: '1', background: `${b.c}`, height: `${b.h}%`, borderRadius: '1px'}}></span>
                  </React.Fragment>))}
                </div>
                <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}><span>2017</span><span>2026</span></div>
              </div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', borderTop: '1px solid var(--hero-bd)', paddingTop: '8px'}}>
              <div onClick={copyQuote} style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 9px', borderRadius: '6px', background: 'var(--brand)', border: '1px solid var(--brand2)', color: 'var(--on-brand)', fontSize: '11px', fontWeight: '500', cursor: 'pointer'}}>⧉ {quoteLabel}</div>
              <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>FONTE: ALERTA RIO (SÉRIE HISTÓRICA) · HÁ 4 MIN</span>
            </div>
          </div>
    </>
  )
}
