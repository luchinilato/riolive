/* Gerado do handoff do Claude Design (seção status) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function VistaStatus({ m }: { m: Modelo }) {
  const { ar, isStatus, sources } = m
  return (
    <>
{/* ================= STATUS ================= */}
    {Boolean(isStatus) && (<>
      <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'auto', padding: '16px'}}>
        <div style={{display: 'flex', alignItems: 'flex-end', gap: '16px', marginBottom: '14px'}}>
          <div>
            <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '22px', fontWeight: '600'}}>Status das fontes</div>
            <div style={{fontSize: '12px', color: 'var(--tx2)', marginTop: '4px'}}>Toda fonte que alimenta o painel, seu estado atual e o histórico de 30 dias. Se algo está fora do ar, está aqui.</div>
          </div>
          <div style={{marginLeft: 'auto', display: 'flex', gap: '8px'}}>
            <div style={{padding: '8px 12px', border: '1px solid var(--ok-bd)', borderRadius: '8px', background: 'var(--ok-bg)'}}><span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '18px', color: 'var(--s1)'}}>11</span> <span style={{fontSize: '11px', color: 'var(--tx2)'}}>online</span></div>
            <div style={{padding: '8px 12px', border: '1px solid var(--warn-bd)', borderRadius: '8px', background: 'var(--warn-bg)'}}><span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '18px', color: 'var(--s2)'}}>1</span> <span style={{fontSize: '11px', color: 'var(--tx2)'}}>degradada</span></div>
            <div style={{padding: '8px 12px', border: '1px solid var(--bd)', borderRadius: '8px'}}><span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '18px', color: 'var(--tx)'}}>99,4%</span> <span style={{fontSize: '11px', color: 'var(--tx2)'}}>uptime 30 d</span></div>
          </div>
        </div>
        <div style={{border: '1px solid var(--bd)', borderRadius: '10px', overflow: 'hidden', background: 'var(--card)'}}>
          <div style={{display: 'grid', gridTemplateColumns: '1.6fr 1.2fr .9fr 1fr 1.4fr', gap: '12px', padding: '9px 14px', borderBottom: '1px solid var(--bd)', background: 'var(--bg2)', fontSize: '10px', letterSpacing: '.1em', color: 'var(--tx3)', textTransform: 'uppercase', fontWeight: '600'}}>
            <span>Fonte</span><span>Órgão</span><span>Estado</span><span>Última leitura</span><span>Uptime 30 dias</span>
          </div>
          {(sources as any[]).map((s: any, sI: number) => (<React.Fragment key={sI}>
            <div style={{display: 'grid', gridTemplateColumns: '1.6fr 1.2fr .9fr 1fr 1.4fr', gap: '12px', padding: '10px 14px', borderBottom: '1px solid var(--bd3)', alignItems: 'center'}}>
              <span style={{fontSize: '12px', color: 'var(--tx)'}}>{s.n}</span>
              <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{s.org}</span>
              <span style={{display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: `${s.c}`}}>{s.i} {s.state}</span>
              <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', color: `${s.agec}`}}>{s.age}</span>
              <span style={{display: 'flex', gap: '2px', alignItems: 'center'}}>
                {(s.bars as any[]).map((b: any, bI: number) => (<React.Fragment key={bI}>
                  <span style={{flex: '1', height: '16px', borderRadius: '1px', background: `${b}`}}></span>
                </React.Fragment>))}
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)', marginLeft: '6px'}}>{s.up}</span>
              </span>
            </div>
          </React.Fragment>))}
        </div>
        <div style={{marginTop: '12px', fontSize: '11px', color: 'var(--tx3)', lineHeight: '1.5'}}>Congelada = a fonte responde, mas devolve o mesmo valor há mais tempo que o seu intervalo esperado de atualização. Nesses casos o painel mostra a última leitura válida com aviso, nunca um número obsoleto como se fosse atual.</div>
      </div>
    </>)}
    </>
  )
}
