/* Gerado do handoff do Claude Design (seção mapa) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import type { Modelo } from '../modelo/tipos'
import React, { Suspense } from 'react'
const MapaReal = React.lazy(() => import('./MapaReal').then((m) => ({ default: m.MapaReal })))

export function VistaMapa({ m }: { m: Modelo }) {
  const { camadasAtivas, contagemCamadas, copyLabel, copyLink, frames, isMapa, layers, mapPresets, recortes } = m
  /* O mapa não recorta por zona: as camadas saem de `/locais`, que ainda não
     tem o filtro, e a geografia já está na tela. Com uma zona escolhida no
     cabeçalho, dizer isso aqui é o mínimo — senão o carimbo do cabeçalho vale
     para uma tela que mostra a cidade inteira. */
  const semRecorte = recortes && Object.keys(recortes).length > 0
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
            {Boolean(semRecorte) && (<div title="As camadas do mapa saem de /locais, que ainda não filtra por zona." style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'transparent', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', letterSpacing: '.06em', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>◻ MAPA: CIDADE INTEIRA</div>)}
            <div onClick={copyLink} style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '11px', color: 'var(--live-tx)', whiteSpace: 'nowrap'}}>⧉ {copyLabel}</div>
          </div>
        </div>

        <div style={{flex: '1 1 auto', minHeight: '0', display: 'flex', gap: '12px'}}>
          <div style={{flex: '1 1 auto', minWidth: '0', position: 'relative', border: '1px solid var(--bd)', borderRadius: '10px', overflow: 'hidden', background: 'var(--bg2)', backgroundImage: 'linear-gradient(var(--map-grid) 1px,transparent 1px),linear-gradient(90deg,var(--map-grid) 1px,transparent 1px),linear-gradient(115deg,var(--map-grid2) 1px,transparent 1px)', backgroundSize: '46px 46px,46px 46px,90px 90px'}}>
            <Suspense fallback={<div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--tx3)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', letterSpacing: '.08em' }}>CARREGANDO MAPA…</div>}><MapaReal camadas={camadasAtivas} /></Suspense>
          </div>

          <div style={{flex: '0 0 268px', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', display: 'flex', flexDirection: 'column', overflow: 'hidden'}}>
            <div style={{padding: '10px 12px', borderBottom: '1px solid var(--bd2)', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase'}}>Camadas</span>
              <span style={{flex: '0 0 auto', marginLeft: 'auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>{contagemCamadas}</span>
            </div>
            <div style={{flex: '1 1 auto', overflow: 'auto'}}>
              {(layers as any[]).map((l: any, lI: number) => (<React.Fragment key={lI}>
                <div onClick={l.toggle} style={{display: 'flex', gap: '9px', alignItems: 'flex-start', padding: '9px 12px', borderBottom: '1px solid var(--bd3)', cursor: l.pronta ? 'pointer' : 'not-allowed', opacity: l.pronta ? 1 : 0.55}}>
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
