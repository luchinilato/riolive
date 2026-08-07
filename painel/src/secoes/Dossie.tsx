/* Gerado do handoff do Claude Design (seção dossie) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Dossie({ m }: { m: Modelo }) {
  const { ar, closeDossier, copyLabel, copyLink, copyQuote, dossier, gridY, periods, quoteLabel } = m
  return (
    <>
{/* ================= CARTÃO EXPANDIDO (DOSSIÊ) ================= */}
    {Boolean(dossier) && (<>
      <div style={{position: 'fixed', inset: '0', zIndex: '80', background: 'var(--bg)', display: 'flex', flexDirection: 'column', animation: 'expandIn .26s cubic-bezier(.2,.7,.3,1)'}}>
        <div style={{flex: '0 0 auto', display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderBottom: '1px solid var(--bd)'}}>
          <span onClick={closeDossier} style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '6px 10px', border: '1px solid var(--bd)', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: 'var(--tx2)', whiteSpace: 'nowrap'}}>← Voltar</span>
          <span style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '2px 6px', borderRadius: '4px', border: `1px solid ${dossier.sev.c}`, color: `${dossier.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{dossier.sev.i} {dossier.sev.n}</span>
          <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '20px', fontWeight: '600'}}>{dossier.title}</span>
          <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', padding: '3px 7px', border: '1px solid var(--bd)', borderRadius: '4px'}}>{dossier.route}</span>
          <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px'}}>
            {(periods as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
              <span onClick={p.pick} style={{padding: '5px 11px', borderRadius: '6px', border: `1px solid ${p.bd}`, background: `${p.bg}`, color: `${p.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', cursor: 'pointer'}}>{p.label}</span>
            </React.Fragment>))}
            <span onClick={copyLink} style={{padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '11px', color: 'var(--live-tx)'}}>⧉ {copyLabel}</span>
          </div>
        </div>

        <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'auto', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px'}}>
          <div style={{display: 'flex', gap: '12px'}}>
            {(dossier.kpis as any[]).map((k: any, kI: number) => (<React.Fragment key={kI}>
              <div style={{flex: '1', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px'}}>
                <div style={{fontSize: '10px', letterSpacing: '.1em', color: 'var(--tx3)', textTransform: 'uppercase', fontWeight: '600'}}>{k.l}</div>
                <div style={{display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px'}}>
                  <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '28px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: `${k.c}`}}>{k.v}</span>
                  <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{k.u}</span>
                </div>
                <div style={{fontSize: '11px', color: 'var(--tx2)', marginTop: '6px'}}>{k.d}</div>
              </div>
            </React.Fragment>))}
          </div>

          <div style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.chartTitle}</span>
              <span style={{display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto', fontSize: '11px', color: 'var(--tx2)'}}>
                <span style={{display: 'flex', alignItems: 'center', gap: '5px'}}><span style={{width: '12px', height: '2px', background: '#149cc6'}}></span>{dossier.s1}</span>
                <span style={{display: 'flex', alignItems: 'center', gap: '5px'}}><span style={{width: '12px', height: '2px', background: '#c08428'}}></span>{dossier.s2}</span>
              </span>
            </div>
            <div style={{position: 'relative', height: '210px'}}>
              <svg viewBox="0 0 1000 210" preserveAspectRatio="none" style={{width: '100%', height: '210px', display: 'block'}}>
                {(gridY as any[]).map((g: any, gI: number) => (<React.Fragment key={gI}>
                  <line x1="0" y1={g} x2="1000" y2={g} stroke="var(--bd2)" strokeWidth="1"></line>
                </React.Fragment>))}
                <rect x={dossier.annX} y="0" width={dossier.annW} height="210" fill="rgba(205,64,72,.13)"></rect>
                <polyline points={dossier.series2} fill="none" stroke="#c08428" strokeWidth="2" strokeDasharray="4 4"></polyline>
                <polyline points={dossier.series1} fill="none" stroke="#149cc6" strokeWidth="2" strokeLinejoin="round"></polyline>
              </svg>
              <div style={{position: 'absolute', left: `${dossier.annLeft}%`, top: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--s4)', letterSpacing: '.05em'}}>{dossier.annLabel}</div>
              <div style={{position: 'absolute', left: '26%', top: '34%', background: 'var(--card2)', border: '1px solid var(--bd-strong)', borderRadius: '6px', padding: '7px 9px', fontSize: '11px', boxShadow: 'var(--shadow)'}}>
                <div style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)'}}>{dossier.tipTime}</div>
                <div style={{display: 'flex', gap: '10px', marginTop: '4px'}}><span style={{color: 'var(--tx)'}}>{dossier.tip1}</span><span style={{color: 'var(--tx2)'}}>{dossier.tip2}</span></div>
              </div>
            </div>
            <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>
              {(dossier.axis as any[]).map((a: any, aI: number) => (<React.Fragment key={aI}><span>{a}</span></React.Fragment>))}
            </div>
          </div>

          <div style={{display: 'flex', gap: '12px', alignItems: 'stretch'}}>
            <div style={{flex: '1 1 auto', minWidth: '0', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', display: 'flex', flexDirection: 'column', overflow: 'hidden', maxHeight: '300px'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', borderBottom: '1px solid var(--bd2)'}}>
                <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.tableTitle}</span>
                <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>ORDENADO POR {dossier.sortBy} ▾</span>
              </div>
              <div style={{display: 'grid', gridTemplateColumns: '1.6fr .8fr .8fr .8fr .8fr', gap: '10px', padding: '7px 14px', borderBottom: '1px solid var(--bd2)', background: 'var(--bg2)', fontSize: '10px', letterSpacing: '.08em', color: 'var(--tx3)', textTransform: 'uppercase'}}>
                {(dossier.cols as any[]).map((c: any, cI: number) => (<React.Fragment key={cI}><span>{c}</span></React.Fragment>))}
              </div>
              <div style={{flex: '1 1 auto', overflow: 'auto'}}>
                {(dossier.rows as any[]).map((r: any, rI: number) => (<React.Fragment key={rI}>
                  <div style={{display: 'grid', gridTemplateColumns: '1.6fr .8fr .8fr .8fr .8fr', gap: '10px', padding: '6px 14px', borderBottom: '1px solid var(--bd3)', fontSize: '11.5px', alignItems: 'center'}}>
                    <span style={{color: 'var(--tx)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{r.a}</span>
                    <span style={{fontFamily: "'JetBrains Mono',monospace", color: 'var(--tx)'}}>{r.b}</span>
                    <span style={{fontFamily: "'JetBrains Mono',monospace", color: 'var(--tx2)'}}>{r.c}</span>
                    <span style={{fontFamily: "'JetBrains Mono',monospace", color: 'var(--tx2)'}}>{r.d}</span>
                    <span style={{fontFamily: "'JetBrains Mono',monospace", color: `${r.ec}`}}>{r.e}</span>
                  </div>
                </React.Fragment>))}
              </div>
            </div>

            <div style={{flex: '0 0 330px', display: 'flex', flexDirection: 'column', gap: '12px'}}>
              <div style={{flex: '1 1 auto', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', minHeight: '0'}}>
                <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.mapTitle}</span>
                <div style={{flex: '1 1 auto', minHeight: '120px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--bg2)', position: 'relative', overflow: 'hidden', backgroundImage: 'linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px)', backgroundSize: '18px 18px'}}>
                  {(dossier.mapDots as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
                    <span style={{position: 'absolute', left: `${p.x}%`, top: `${p.y}%`, width: '7px', height: '7px', borderRadius: '50%', background: `${p.c}`, border: '1px solid var(--bg)'}}></span>
                  </React.Fragment>))}
                  <span style={{position: 'absolute', left: '8px', bottom: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>MAPLIBRE · PLACEHOLDER</span>
                </div>
              </div>
              <div style={{flex: '0 0 auto', background: 'var(--hero-grad)', border: '1px solid var(--hero-bd)', borderRadius: '10px', padding: '12px 14px'}}>
                <div style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--live-tx)', textTransform: 'uppercase'}}>Contexto histórico</div>
                <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '16px', lineHeight: '1.35', color: 'var(--tx)', marginTop: '8px', textWrap: 'pretty'}}>{dossier.context}</div>
                <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px'}}>
                  <span onClick={copyQuote} style={{padding: '5px 9px', borderRadius: '6px', background: 'var(--brand)', border: '1px solid var(--brand2)', color: 'var(--on-brand)', fontSize: '11px', cursor: 'pointer'}}>⧉ {quoteLabel}</span>
                  <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>{dossier.seal}</span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
    </>)}
    </>
  )
}
