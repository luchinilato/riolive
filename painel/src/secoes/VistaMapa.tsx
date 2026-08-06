/* Gerado do handoff do Claude Design (seção mapa) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function VistaMapa({ m }: { m: Modelo }) {
  const { copyLabel, copyLink, frames, isMapa, layers, mapFleet, mapIncidents, mapPresets } = m
  return (
    <>
{/* ================= MAPA ================= */}
    {Boolean(isMapa) && (<>
      <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', flexDirection: 'column', padding: '12px 16px', gap: '10px'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap'}}>
          {(mapPresets as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
            <div onClick={p.pick} style={{display: 'flex', alignItems: 'center', gap: '7px', padding: '7px 12px', borderRadius: '999px', border: `1px solid ${p.bd}`, background: `${p.bg}`, color: `${p.c}`, fontSize: '12px', fontWeight: '500', cursor: 'pointer', whiteSpace: 'nowrap'}}>
              <span style={{fontSize: '10px', color: `${p.dot}`}}>{p.icon}</span>{p.label}
              <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>{p.n}</span>
            </div>
          </React.Fragment>))}
          <div style={{marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', fontSize: '11px', color: 'var(--tx2)', whiteSpace: 'nowrap'}}>Janela <span style={{color: 'var(--tx)', fontFamily: "'JetBrains Mono',monospace"}}>3h</span> <span style={{color: 'var(--tx3)'}}>/ 24h</span></div>
            <div onClick={copyLink} style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '11px', color: 'var(--live-tx)', whiteSpace: 'nowrap'}}>⧉ {copyLabel}</div>
          </div>
        </div>

        <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', gap: '12px'}}>
          <div style={{flex: '1 1 auto', minWidth: '0', position: 'relative', border: '1px solid var(--bd)', borderRadius: '10px', overflow: 'hidden', background: 'var(--bg2)', backgroundImage: 'linear-gradient(var(--map-grid) 1px,transparent 1px),linear-gradient(90deg,var(--map-grid) 1px,transparent 1px),linear-gradient(115deg,var(--map-grid2) 1px,transparent 1px)', backgroundSize: '46px 46px,46px 46px,90px 90px'}}>
            <div style={{position: 'absolute', left: '12px', top: '12px', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', letterSpacing: '.06em', padding: '3px 7px', border: '1px solid var(--bd)', borderRadius: '4px', background: 'var(--scrim)'}}>BASEMAP PLACEHOLDER · MAPLIBRE</div>
            {(mapFleet as any[]).map((p: any, pI: number) => (<React.Fragment key={pI}>
              <span style={{position: 'absolute', left: `${p.x}%`, top: `${p.y}%`, width: '3px', height: '3px', borderRadius: '50%', background: '#149cc6', opacity: '.85'}}></span>
            </React.Fragment>))}
            {(mapIncidents as any[]).map((i: any, iI: number) => (<React.Fragment key={iI}>
              <span style={{position: 'absolute', left: `${i.x}%`, top: `${i.y}%`, width: '16px', height: '16px', background: `${i.c}`, opacity: '.55', clipPath: 'polygon(25% 5%,75% 5%,100% 50%,75% 95%,25% 95%,0% 50%)'}}></span>
            </React.Fragment>))}
            <div style={{position: 'absolute', left: '41%', top: '37%', transform: 'translate(-50%,-100%)', width: '250px', background: 'var(--card)', border: '1px solid var(--bd-strong)', borderRadius: '8px', padding: '10px', boxShadow: 'var(--shadow)'}}>
              <div style={{display: 'flex', alignItems: 'center', gap: '7px'}}>
                <span style={{padding: '1px 5px', borderRadius: '4px', border: '1px solid var(--s3)', color: 'var(--s3)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>▲ 3</span>
                <span style={{fontSize: '12px', fontWeight: '600', color: 'var(--tx)'}}>Linha 232 parada</span>
              </div>
              <div style={{fontSize: '11px', color: 'var(--tx2)', marginTop: '6px', lineHeight: '1.4'}}>Sem GPS ativo há 47 min no trecho Penha → Central. Ocorrência de tiro a 380 m às 13:52.</div>
              <div style={{display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px', borderTop: '1px solid var(--bd2)', paddingTop: '7px'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)'}}>SMTR + FOGO CRUZADO · 14:04</span>
                <span style={{marginLeft: 'auto', fontSize: '11px', color: 'var(--live-tx)', cursor: 'pointer'}}>⧉ copiar link</span>
              </div>
              <span style={{position: 'absolute', left: '50%', bottom: '-6px', marginLeft: '-6px', width: '10px', height: '10px', background: 'var(--card)', borderRight: '1px solid var(--bd-strong)', borderBottom: '1px solid var(--bd-strong)', transform: 'rotate(45deg)'}}></span>
            </div>
            <div style={{position: 'absolute', left: '12px', bottom: '12px', display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 10px', borderRadius: '6px', background: 'var(--scrim)', border: '1px solid var(--bd)', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx2)'}}>
              <span><span style={{color: '#149cc6'}}>●</span> FROTA ATIVA 4.212</span>
              <span><span style={{color: 'var(--s4)'}}>⬢</span> OCORRÊNCIAS 24H</span>
              <span><span style={{color: 'var(--s3)'}}>▲</span> LINHAS PARADAS 3</span>
            </div>
          </div>

          <div style={{flex: '0 0 268px', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
            <div style={{padding: '10px 12px', borderBottom: '1px solid var(--bd2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>Camadas</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>4/11 ATIVAS</span>
            </div>
            <div style={{flex: '1 1 auto', overflow: 'auto'}}>
              {(layers as any[]).map((l: any, lI: number) => (<React.Fragment key={lI}>
                <div onClick={l.toggle} style={{display: 'flex', gap: '9px', alignItems: 'flex-start', padding: '9px 12px', borderBottom: '1px solid var(--bd3)', cursor: 'pointer'}}>
                  <span style={{flex: '0 0 auto', marginTop: '1px', width: '13px', height: '13px', borderRadius: '3px', border: `1px solid ${l.bd}`, background: `${l.bg}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '9px', color: 'var(--bg)'}}>{l.mark}</span>
                  <span style={{flex: '1 1 auto', minWidth: '0'}}>
                    <span style={{display: 'block', fontSize: '11.5px', color: `${l.tc}`}}>{l.n}</span>
                    <span style={{display: 'block', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: `${l.sc}`, marginTop: '2px'}}>{l.src}</span>
                  </span>
                </div>
              </React.Fragment>))}
            </div>
          </div>
        </div>

        <div style={{flex: '0 0 auto', display: 'flex', alignItems: 'center', gap: '12px', padding: '8px 12px', border: '1px solid var(--bd)', borderRadius: '10px', background: 'var(--card)'}}>
          <span style={{width: '26px', height: '26px', borderRadius: '50%', background: 'var(--brand)', border: '1px solid var(--brand2)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--on-brand)', fontSize: '10px', cursor: 'pointer'}}>▶</span>
          <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)'}}>RADAR · ÚLTIMOS 40 MIN</span>
          <div style={{flex: '1 1 auto', display: 'flex', gap: '2px', alignItems: 'center'}}>
            {(frames as any[]).map((f: any, fI: number) => (<React.Fragment key={fI}>
              <span style={{flex: '1', height: `${f.h}px`, background: `${f.c}`, borderRadius: '1px'}}></span>
            </React.Fragment>))}
          </div>
          <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx)'}}>14:31</span>
        </div>
      </div>
    </>)}
    </>
  )
}
