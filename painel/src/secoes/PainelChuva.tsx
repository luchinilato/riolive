/* Gerado do handoff do Claude Design (seção chuva) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { BarraRegua } from '../componentes/Regua'

export function PainelChuva({ m }: { m: Modelo }) {
  const { chuva, lay, openChuva, ramp } = m
  return (
    <>
{/* CHUVA E ÁGUA */}
          <div onClick={openChuva} style={{background: 'var(--card)', border: `1px solid ${chuva.bd}`, borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.chuva.s}`, order: `${lay.chuva.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', flex: '0 0 auto'}}>
              <span title={chuva.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${chuva.sev.c}`, color: `${chuva.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{chuva.sev.i} {chuva.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Chuva e água</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{chuva.count}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', gap: '12px', overflow: 'hidden'}}>
              <div style={{flex: '1 1 0', minWidth: '0', minHeight: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: '5px'}}>
                <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
                  <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '32px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: `${chuva.hc}`}}>{chuva.hero}</span>
                  <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '14px', color: 'var(--tx2)'}}>mm/h</span>
                </div>
                <div style={{fontSize: '12px', color: 'var(--tx2)', lineHeight: '1.35'}}>{chuva.sub}</div>
                <BarraRegua regua={chuva.regua} />
                <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end'}}>
                  <div style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.08em', marginBottom: '3px'}}>CHUVA 24H · MM</div>
                  <svg viewBox="0 0 220 34" preserveAspectRatio="none" style={{width: '100%', height: '30px', display: 'block'}}>
                    <line x1="0" y1="33" x2="220" y2="33" stroke="var(--bd)" strokeWidth="1"></line>
                    <line x1="0" y1="17" x2="220" y2="17" stroke="var(--card2)" strokeWidth="1"></line>
                    <polyline points={chuva.spark} fill="none" stroke="#149cc6" strokeWidth="2" strokeLinejoin="round"></polyline>
                  </svg>
                </div>
                <div style={{flex: '0 0 auto', fontSize: '11px', color: 'var(--tx2)', borderTop: '1px solid var(--bd2)', paddingTop: '6px', lineHeight: '1.35'}}>{chuva.rios}</div>
              </div>
              <div style={{flex: '0 0 132px', display: 'flex', flexDirection: 'column', gap: '4px'}}>
                <div style={{flex: '1 1 auto', borderRadius: '6px', border: '1px solid var(--bd)', position: 'relative', overflow: 'hidden', background: 'var(--bg2)', backgroundImage: 'linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px)', backgroundSize: '14px 14px'}}>
                  <div style={{position: 'absolute', left: '12%', top: '22%', width: '34%', height: '30%', borderRadius: '50%', background: `${chuva.echo1}`, filter: 'blur(5px)'}}></div>
                  <div style={{position: 'absolute', left: '52%', top: '44%', width: '26%', height: '26%', borderRadius: '50%', background: `${chuva.echo2}`, filter: 'blur(5px)'}}></div>
                  <div style={{position: 'absolute', left: '8px', bottom: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>RADAR</div>
                </div>
                <div style={{display: 'flex', gap: '2px', alignItems: 'center'}}>
                  {(ramp as any[]).map((c: any, cI: number) => (<React.Fragment key={cI}>
                    <span style={{flex: '1', height: '5px', background: `${c}`, borderRadius: '1px'}}></span>
                  </React.Fragment>))}
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', marginLeft: '4px'}}>mm/h</span>
                </div>
              </div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', flex: '0 0 auto', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>FONTE: ALERTA RIO + ANA · HÁ 4 MIN
            </div>
          </div>
    </>
  )
}
