/* Gerado do handoff do Claude Design (seção navios) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function PainelNavios({ m }: { m: Modelo }) {
  const { lay, openNavios } = m
  return (
    <>
{/* NAVIOS · DEGRADADO */}
          <div onClick={openNavios} style={{background: 'var(--card)', border: '1px solid var(--warn-bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.navios.s}`, order: `${lay.navios.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: '1px solid var(--s2)', color: 'var(--s2)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>◆ 2</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Navios (AIS)</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>BAÍA</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'flex-start', gap: '6px', padding: '6px 8px', borderRadius: '6px', background: 'var(--warn-bg)', border: '1px solid var(--warn-bd)', fontSize: '11px', color: 'var(--warn-tx)', lineHeight: '1.35'}}>
              <span>⚠</span><span>Fonte degradada desde 05/08. Exibindo a última leitura válida — não é o estado atual.</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: '4px', opacity: '.62'}}>
              <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
                <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '24px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: 'var(--tx2)'}}>38</span>
                <span style={{fontSize: '11px', color: 'var(--tx3)'}}>embarcações na Baía</span>
              </div>
              <div style={{fontSize: '11px', color: 'var(--tx3)'}}>12 fundeadas · 6 atracadas no Porto · 20 em trânsito</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--s2)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s2)'}}></span>FONTE: AISSTREAM · LEITURA DE HÁ 19 H
            </div>
          </div>
    </>
  )
}
