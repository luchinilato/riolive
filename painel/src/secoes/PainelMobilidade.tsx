/* Gerado do handoff do Claude Design (seção mobilidade) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { BarraRegua } from '../componentes/Regua'

export function PainelMobilidade({ m }: { m: Modelo }) {
  const { fleetDots, lay, mob, openMob } = m
  return (
    <>
{/* MOBILIDADE */}
          <div onClick={openMob} style={{background: 'var(--card)', border: `1px solid ${mob.bd}`, borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.mob.s}`, order: `${lay.mob.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px', flex: '0 0 auto'}}>
              <span title={mob.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: `1px solid ${mob.sev.c}`, color: `${mob.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{mob.sev.i} {mob.sev.n}</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Mobilidade</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{mob.count}</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', gap: '12px', overflow: 'hidden'}}>
              <div style={{flex: '1 1 0', minWidth: '0', display: 'flex', flexDirection: 'column', gap: '6px'}}>
                <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
                  <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '30px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1'}}>{mob.hero}</span>
                  <span style={{fontSize: '11px', color: 'var(--tx2)'}}>veículos</span>
                </div>
                <div style={{fontSize: '11px', color: 'var(--tx2)', lineHeight: '1.4'}}>{mob.sub}</div>
                <BarraRegua regua={mob.regua} />
                <div style={{display: 'flex', alignItems: 'flex-start', gap: '6px', padding: '6px 8px', borderRadius: '6px', background: `${mob.warnBg}`, border: `1px solid ${mob.warnBd}`, fontSize: '11px', color: `${mob.warnC}`, lineHeight: '1.35'}}>
                  <span>⚠</span><span>{mob.warn}</span>
                </div>
                <div style={{marginTop: 'auto', display: 'flex', gap: '10px', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)', borderTop: '1px solid var(--bd2)', paddingTop: '6px'}}>
                  <span><span style={{color: `${mob.m1}`}}>●</span> L1</span><span><span style={{color: `${mob.m2}`}}>●</span> L2</span><span><span style={{color: `${mob.m4}`}}>●</span> L4</span><span style={{color: 'var(--tx3)'}}>{mob.metro}</span>
                </div>
              </div>
              <div style={{flex: '0 0 96px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--bg2)', position: 'relative', overflow: 'hidden', backgroundImage: 'linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px)', backgroundSize: '12px 12px'}}>
                {(fleetDots as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
                  <span style={{position: 'absolute', left: `${p.x}%`, top: `${p.y}%`, width: '2px', height: '2px', borderRadius: '50%', background: `${p.c}`}}></span>
                </React.Fragment>))}
                <div style={{position: 'absolute', left: '6px', bottom: '5px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>FROTA</div>
              </div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--live)', animation: 'pulse 2s infinite'}}></span>FONTE: SMTR + METRÔRIO · AO VIVO (1 MIN)
            </div>
          </div>
    </>
  )
}
