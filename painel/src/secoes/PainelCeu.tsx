/* Gerado do handoff do Claude Design (seção ceu) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function PainelCeu({ m }: { m: Modelo }) {
  const { ceu, lay, openCeu } = m
  return (
    <>
{/* CÉU */}
          <div onClick={openCeu} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.ceu.s}`, order: `${lay.ceu.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title={ceu.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${ceu.sev.c}`, color: `${ceu.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{ceu.sev.i} {ceu.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Céu</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{ceu.count}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
              <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{ceu.hero}</span>
              <span style={{fontSize: '11px', color: 'var(--tx2)'}}>aeronaves sobre a cidade</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', flexDirection: 'column', gap: '5px', fontSize: '11px', color: 'var(--tx2)'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--bd3)', paddingBottom: '4px'}}><span>SDU e GIG · pousos/h</span><span style={{fontFamily: "'JetBrains Mono',monospace", color: 'var(--tx3)'}}>—</span></div>
              <div style={{lineHeight: '1.35', color: 'var(--tx3)'}}>{ceu.nota}</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--live)', animation: 'pulse 2s infinite'}}></span>FONTE: ADSB.LOL · AO VIVO
            </div>
          </div>
    </>
  )
}
