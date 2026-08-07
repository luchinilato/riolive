/* Gerado do handoff do Claude Design (seção queimadas) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function PainelQueimadas({ m }: { m: Modelo }) {
  const { lay, openQueimadas, queimadasHero, queimadasSub, queimadasTexto } = m
  return (
    <>
{/* QUEIMADAS */}
          <div onClick={openQueimadas} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.queimadas.s}`, order: `${lay.queimadas.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: '1px solid var(--s1)', color: 'var(--s1)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>● 1</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Queimadas</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>3H</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
              <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{queimadasHero ?? '0'}</span>
              <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{queimadasSub ?? 'focos no município · 3 h'}</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', fontSize: '11px', color: 'var(--tx2)', lineHeight: '1.45'}}>{queimadasTexto ?? 'Detecção por satélite do INPE, atualizada a cada 10 minutos.'}</div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: INPE · HÁ 8 MIN
            </div>
          </div>
    </>
  )
}
