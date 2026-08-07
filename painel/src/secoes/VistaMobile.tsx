/* Vista mobile (≤640px): pilha rolável — extraída da seção MOBILE do handoff
   (sem a moldura de celular do preview). Mesmo view-model do desktop. */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { LARGURA_MIN_HORIZONTAL, Logo } from '../componentes/Logo'

export function VistaMobile({ m }: { m: Modelo }) {
  const { zoneLabel, toggleTheme, themeIcon, sev, headlineShort, tickerLoop, mt, mTabCards, mTabFeed, mobileCards, mobileFeed, mobileList, feed } = m
  return (
    <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--bg)', color: 'var(--tx)', fontFamily: 'Inter,system-ui,sans-serif', overflow: 'hidden' }}>
<div style={{flex: '0 0 auto', padding: '10px 14px 8px', borderBottom: '1px solid var(--bd)'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
            {/* o slot do handoff tinha 96px; horizontal não desce de 120px, então é essa a largura */}
            <Logo variante="horizontal" style={{width: `${LARGURA_MIN_HORIZONTAL}px`, flex: '0 0 auto'}} />
            <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '5px', padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--bd)', fontSize: '11px', color: 'var(--tx)', whiteSpace: 'nowrap'}}>{zoneLabel} <span style={{color: 'var(--tx3)', fontSize: '9px'}}>▾</span></div>
            <div onClick={toggleTheme} style={{padding: '4px 7px', borderRadius: '6px', border: '1px solid var(--bd)', fontSize: '11px', color: 'var(--tx2)', cursor: 'pointer'}}>{themeIcon}</div>
            <span style={{width: '7px', height: '7px', borderRadius: '50%', background: 'var(--live)', animation: 'pulse 2s infinite'}}></span>
          </div>
          <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '9px'}}>
            <span title={sev.d} style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '3px 8px', borderRadius: '6px', border: `1px solid ${sev.c}`, background: `${sev.bg}`, color: `${sev.c}`, fontSize: '12px', fontWeight: '600'}}>{sev.i} {sev.n} {sev.l}</span>
          </div>
          <div style={{fontSize: '12px', color: 'var(--tx2)', marginTop: '7px', lineHeight: '1.4'}}>{headlineShort}</div>
        </div>
        <div style={{flex: '0 0 26px', borderBottom: '1px solid var(--bd)', background: 'var(--bg2)', overflow: 'hidden', display: 'flex', alignItems: 'center'}}>
          <div style={{display: 'flex', width: 'max-content', animation: 'tick 52s linear infinite'}}>
            {(tickerLoop as any[]).map((t: any, tI: number) => (<React.Fragment key={tI}>
              <div style={{display: 'flex', gap: '6px', padding: '0 11px', borderRight: '1px solid var(--bd2)', whiteSpace: 'nowrap', fontFamily: "'JetBrains Mono',monospace", fontSize: '9.5px'}}>
                <span style={{color: 'var(--tx3)'}}>{t.k}</span><span style={{color: 'var(--tx)'}}>{t.v}</span><span style={{color: `${t.dc}`}}>{t.d}</span>
              </div>
            </React.Fragment>))}
          </div>
        </div>
        <div style={{flex: '0 0 auto', display: 'flex', borderBottom: '1px solid var(--bd)'}}>
          <div onClick={mTabCards} style={{flex: '1', textAlign: 'center', padding: '9px 0', fontSize: '12px', fontWeight: '500', color: `${mt.a.c}`, borderBottom: `2px solid ${mt.a.b}`, cursor: 'pointer'}}>Cartões</div>
          <div onClick={mTabFeed} style={{flex: '1', textAlign: 'center', padding: '9px 0', fontSize: '12px', fontWeight: '500', color: `${mt.f.c}`, borderBottom: `2px solid ${mt.f.b}`, cursor: 'pointer'}}>Feed</div>
        </div>
        <div style={{flex: '1 1 auto', minHeight: '0', overflowY: 'auto', overflowX: 'hidden', padding: '10px', display: 'flex', flexDirection: 'column', gap: '10px'}}>
          {Boolean(mobileCards) && (<>
            {(mobileList as any[]).map((c: any, cI: number) => (<React.Fragment key={cI}>
              <div style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px'}}>
                <div style={{display: 'flex', alignItems: 'center', gap: '7px'}}>
                  <span style={{padding: '1px 5px', borderRadius: '4px', border: `1px solid ${c.sev.c}`, color: `${c.sev.c}`, fontFamily: "'JetBrains Mono',monospace", fontSize: '9.5px'}}>{c.sev.i} {c.sev.n}</span>
                  <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.09em', color: 'var(--tx2)', textTransform: 'uppercase'}}>{c.t}</span>
                  <span style={{marginLeft: 'auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
                </div>
                <div style={{display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '8px'}}>
                  <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '28px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: `${c.hc}`}}>{c.v}</span>
                  <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{c.u}</span>
                </div>
                <div style={{fontSize: '11.5px', color: 'var(--tx2)', marginTop: '6px', lineHeight: '1.4'}}>{c.sub}</div>
                <div style={{display: 'flex', alignItems: 'center', gap: '6px', marginTop: '9px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>
                  <span style={{width: '5px', height: '5px', borderRadius: '50%', background: `${c.dot}`}}></span>{c.seal}
                </div>
              </div>
            </React.Fragment>))}
          </>)}
          {Boolean(mobileFeed) && (<>
            {(feed as any[]).map((f: any, fI: number) => (<React.Fragment key={fI}>
              <div style={{display: 'flex', gap: '9px', paddingBottom: '9px', borderBottom: '1px solid var(--bd3)'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', flex: '0 0 34px', paddingTop: '1px'}}>{f.h}</span>
                <span style={{flex: '0 0 auto', paddingTop: '1px', fontSize: '9px', color: `${f.sev.c}`}}>{f.sev.i}</span>
                <span style={{flex: '1 1 auto', minWidth: '0', fontSize: '12px', color: 'var(--tx)', lineHeight: '1.4'}}>{f.txt}</span>
              </div>
            </React.Fragment>))}
          </>)}
        </div>
        <div style={{flex: '0 0 auto', display: 'flex', borderTop: '1px solid var(--bd)', background: 'var(--bg2)', padding: '8px 0 14px'}}>
          <div style={{flex: '1', textAlign: 'center', fontSize: '11px', color: 'var(--live-tx)'}}>Agora</div>
          <div style={{flex: '1', textAlign: 'center', fontSize: '11px', color: 'var(--tx3)'}}>Mapa</div>
          <div style={{flex: '1', textAlign: 'center', fontSize: '11px', color: 'var(--tx3)'}}>Status</div>

      </div>
    </div>
  )
}
