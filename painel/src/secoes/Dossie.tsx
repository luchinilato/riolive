/* Gerado do handoff do Claude Design (seção dossie) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html

   Alterado em 2026-08-07: cada bloco (KPIs, gráfico, tabela, mapa, contexto) só
   aparece se houver dado pra ele, e o dossiê sem dado abre um bloco de ausência
   com o motivo. Antes, todo tema herdava o dossiê de chuva do protótipo — /ar
   abria 33 pluviômetros com o título trocado. [[DEC - Interface não afirma o que
   não mediu]]. */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Dossie({ m }: { m: Modelo }) {
  const { closeDossier, copyLabel, copyLink, copyQuote, dossier, gridY, periods, quoteLabel } = m
  if (!dossier) return null

  const kpis = (dossier.kpis ?? []) as any[]
  const rows = (dossier.rows ?? []) as any[]
  const mapDots = (dossier.mapDots ?? []) as any[]
  const temGrafico = Boolean(dossier.series1)
  const temTabela = rows.length > 0
  const temMapa = mapDots.length > 0
  const ausencia = dossier.ausencia as { titulo: string; texto: string } | null | undefined

  return (
    <>
{/* ================= CARTÃO EXPANDIDO (DOSSIÊ) ================= */}
      <div style={{position: 'fixed', inset: '0', zIndex: '80', background: 'var(--bg)', display: 'flex', flexDirection: 'column', animation: 'expandIn .26s cubic-bezier(.2,.7,.3,1)'}}>
        <div style={{flex: '0 0 auto', display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderBottom: '1px solid var(--bd)'}}>
          <span onClick={closeDossier} style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '6px 10px', border: '1px solid var(--bd)', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: 'var(--tx2)', whiteSpace: 'nowrap'}}>← Voltar</span>
          <span title={dossier.sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '2px 6px', borderRadius: '4px', border: `1px solid ${dossier.sev.c}`, color: `${dossier.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>{dossier.sev.i} {dossier.sev.n}</span>
          <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '20px', fontWeight: '600'}}>{dossier.title}</span>
          <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', padding: '3px 7px', border: '1px solid var(--bd)', borderRadius: '4px'}}>{dossier.route}</span>
          <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px'}}>
            {/* sem dado, escolher janela não muda nada — o seletor sai de cena */}
            {!ausencia && (periods as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
              <span onClick={p.pick} style={{padding: '5px 11px', borderRadius: '6px', border: `1px solid ${p.bd}`, background: `${p.bg}`, color: `${p.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', cursor: 'pointer'}}>{p.label}</span>
            </React.Fragment>))}
            <span onClick={copyLink} style={{padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '11px', color: 'var(--live-tx)'}}>⧉ {copyLabel}</span>
          </div>
        </div>

        <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'auto', padding: '14px 16px', display: 'flex', flexDirection: 'column', gap: '12px'}}>
          {/* Ausência declarada: o que falta e por quê. Nunca um número no lugar. */}
          {ausencia && (
            <div style={{background: 'var(--card)', border: '1px dashed var(--bd-strong)', borderRadius: '10px', padding: '16px 18px'}}>
              <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '17px', fontWeight: '600', color: 'var(--tx)'}}>{ausencia.titulo}</div>
              <div style={{fontSize: '12.5px', color: 'var(--tx2)', marginTop: '8px', lineHeight: '1.55', maxWidth: '78ch', textWrap: 'pretty'}}>{ausencia.texto}</div>
            </div>
          )}

          {kpis.length > 0 && (
            <div style={{display: 'flex', gap: '12px'}}>
              {kpis.map((k: any, kI: number) => (<React.Fragment key={kI}>
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
          )}

          {(temGrafico || dossier.notaGrafico) && (
            <div style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '10px'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.chartTitle}</span>
                <span style={{display: 'flex', alignItems: 'center', gap: '12px', marginLeft: 'auto', fontSize: '11px', color: 'var(--tx2)'}}>
                  {/* legenda de série sem série desenhada é enfeite: some junto */}
                  {Boolean(dossier.series1) && Boolean(dossier.s1) && <span style={{display: 'flex', alignItems: 'center', gap: '5px'}}><span style={{width: '12px', height: '2px', background: '#149cc6'}}></span>{dossier.s1}</span>}
                  {Boolean(dossier.series2) && Boolean(dossier.s2) && <span style={{display: 'flex', alignItems: 'center', gap: '5px'}}><span style={{width: '12px', height: '2px', background: '#c08428'}}></span>{dossier.s2}</span>}
                </span>
              </div>
              {temGrafico ? (
                <>
                  <div style={{position: 'relative', height: '210px'}}>
                    <svg viewBox="0 0 1000 210" preserveAspectRatio="none" style={{width: '100%', height: '210px', display: 'block'}}>
                      {(gridY as any[]).map((g: any, gI: number) => (<React.Fragment key={gI}>
                        <line x1="0" y1={g} x2="1000" y2={g} stroke="var(--bd2)" strokeWidth="1"></line>
                      </React.Fragment>))}
                      {dossier.annW > 0 && <rect x={dossier.annX} y="0" width={dossier.annW} height="210" fill="rgba(205,64,72,.13)"></rect>}
                      {Boolean(dossier.series2) && <polyline points={dossier.series2} fill="none" stroke="#c08428" strokeWidth="2" strokeDasharray="4 4"></polyline>}
                      <polyline points={dossier.series1} fill="none" stroke="#149cc6" strokeWidth="2" strokeLinejoin="round"></polyline>
                    </svg>
                    {Boolean(dossier.annLabel) && <div style={{position: 'absolute', left: `${dossier.annLeft}%`, top: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--s4)', letterSpacing: '.05em'}}>{dossier.annLabel}</div>}
                    {Boolean(dossier.tipTime) && (
                      <div style={{position: 'absolute', left: `${dossier.tipLeft ?? 26}%`, top: `${dossier.tipTop ?? 34}%`, transform: (dossier.tipLeft ?? 26) > 60 ? 'translateX(-100%)' : 'none', background: 'var(--card2)', border: '1px solid var(--bd-strong)', borderRadius: '6px', padding: '7px 9px', fontSize: '11px', boxShadow: 'var(--shadow)', whiteSpace: 'nowrap'}}>
                        <div style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)'}}>{dossier.tipTime}</div>
                        <div style={{display: 'flex', gap: '10px', marginTop: '4px'}}><span style={{color: 'var(--tx)'}}>{dossier.tip1}</span><span style={{color: 'var(--tx2)'}}>{dossier.tip2}</span></div>
                      </div>
                    )}
                  </div>
                  <div style={{display: 'flex', justifyContent: 'space-between', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>
                    {(dossier.axis as any[]).map((a: any, aI: number) => (<React.Fragment key={aI}><span>{a}</span></React.Fragment>))}
                  </div>
                </>
              ) : (
                <div style={{fontSize: '12px', color: 'var(--tx2)', lineHeight: '1.5', padding: '6px 0 2px', maxWidth: '78ch', textWrap: 'pretty'}}>{dossier.notaGrafico}</div>
              )}
            </div>
          )}

          {(temTabela || temMapa || dossier.context) && (
            <div style={{display: 'flex', gap: '12px', alignItems: 'stretch'}}>
              {temTabela && (
                <div style={{flex: '1 1 auto', minWidth: '0', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', display: 'flex', flexDirection: 'column', overflow: 'hidden', maxHeight: '300px'}}>
                  <div style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 14px', borderBottom: '1px solid var(--bd2)'}}>
                    <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.tableTitle}</span>
                    {Boolean(dossier.sortBy) && <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>ORDENADO POR {dossier.sortBy} ▾</span>}
                  </div>
                  <div style={{display: 'grid', gridTemplateColumns: '1.6fr .8fr .8fr .8fr .8fr', gap: '10px', padding: '7px 14px', borderBottom: '1px solid var(--bd2)', background: 'var(--bg2)', fontSize: '10px', letterSpacing: '.08em', color: 'var(--tx3)', textTransform: 'uppercase'}}>
                    {(dossier.cols as any[]).map((c: any, cI: number) => (<React.Fragment key={cI}><span>{c}</span></React.Fragment>))}
                  </div>
                  <div style={{flex: '1 1 auto', overflow: 'auto'}}>
                    {rows.map((r: any, rI: number) => (<React.Fragment key={rI}>
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
              )}

              <div style={{flex: temTabela ? '0 0 330px' : '1 1 auto', display: 'flex', flexDirection: 'column', gap: '12px'}}>
                {temMapa && (
                  <div style={{flex: '1 1 auto', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', minHeight: '0'}}>
                    <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{dossier.mapTitle}</span>
                    <div style={{flex: '1 1 auto', minHeight: '120px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--bg2)', position: 'relative', overflow: 'hidden', backgroundImage: 'linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px)', backgroundSize: '18px 18px'}}>
                      {mapDots.map((p: any, pI: number) => (<React.Fragment key={pI}>
                        <span title={p.t} style={{position: 'absolute', left: `${p.x}%`, top: `${p.y}%`, width: '7px', height: '7px', borderRadius: '50%', background: `${p.c}`, border: '1px solid var(--bg)'}}></span>
                      </React.Fragment>))}
                      <span style={{position: 'absolute', left: '8px', bottom: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>{dossier.mapNota || 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO'}</span>
                    </div>
                  </div>
                )}
                {Boolean(dossier.context) && (
                  <div style={{flex: '0 0 auto', background: 'var(--hero-grad)', border: '1px solid var(--hero-bd)', borderRadius: '10px', padding: '12px 14px'}}>
                    <div style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--live-tx)', textTransform: 'uppercase'}}>Contexto histórico</div>
                    <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '16px', lineHeight: '1.35', color: 'var(--tx)', marginTop: '8px', textWrap: 'pretty'}}>{dossier.context}</div>
                    <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px'}}>
                      <span onClick={copyQuote} style={{padding: '5px 9px', borderRadius: '6px', background: 'var(--brand)', border: '1px solid var(--brand2)', color: 'var(--on-brand)', fontSize: '11px', cursor: 'pointer'}}>⧉ {quoteLabel}</span>
                      <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>{dossier.seal}</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

        </div>
      </div>
    </>
  )
}
