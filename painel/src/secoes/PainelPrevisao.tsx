/* Gerado do handoff do Claude Design (seção previsao) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { Recorte } from '../componentes/Recorte'

export function PainelPrevisao({ m }: { m: Modelo }) {
  const { lay, openPrevisao, previsao } = m
  return (
    <>
{/* PREVISÃO */}
          <div onClick={openPrevisao} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.previsao.s}`, order: `${lay.previsao.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={previsao.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${previsao.sev.c}`, color: `${previsao.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{previsao.sev.i} {previsao.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Previsão</span>
              <Recorte marca={m.recortes?.previsao} />
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>12H</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px', minWidth: '0'}}>
              <span style={{flex: '0 0 auto', whiteSpace: 'nowrap', fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{previsao.hero}</span>
              <span style={{minWidth: '0', fontSize: '11px', color: 'var(--tx2)'}}>{previsao.heroSub}</span>
            </div>
            <div style={{fontSize: '11px', color: 'var(--tx2)'}}>umidade 58% · vento 18 km/h SE</div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', alignItems: 'flex-end', gap: '3px', paddingTop: '4px'}}>
              {(previsao.hours as any[]).map((h: any, hI: number) => (<React.Fragment key={hI}>
                <div style={{flex: '1', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px', minWidth: '0'}}>
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx2)'}}>{h.t}</span>
                  <span style={{width: '100%', background: '#c08428', borderRadius: '2px', height: `${h.bar}px`}}></span>
                  <span style={{width: '100%', background: '#149cc6', borderRadius: '2px', height: `${h.rain}px`, opacity: '.8'}}></span>
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>{h.h}</span>
                </div>
              </React.Fragment>))}
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: OPEN-METEO · RODADA DE 14H
            </div>
          </div>
    </>
  )
}
