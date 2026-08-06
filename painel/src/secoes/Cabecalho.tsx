/* Gerado do handoff do Claude Design (seção cabecalho) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Cabecalho({ m }: { m: Modelo }) {
  const { clearZone, copyLabel, copyLink, goHome, goMapa, goStatus, headline, modeLabel, navA, navM, navS, sev, themeIcon, themeLabel, toggleMode, toggleTheme, toggleZonePicker, zoneChip, zoneLabel, zonePickerOpen, zones } = m
  return (
    <>
{/* ================= CABEÇALHO DE ESTADO ================= */}
    <div style={{display: 'flex', alignItems: 'center', gap: '16px', padding: '0 16px', height: '56px', flex: '0 0 56px', borderBottom: '1px solid var(--bd)', background: 'var(--bg)'}}>
      <div style={{width: '140px', height: '28px', border: '1px dashed var(--tx4)', borderRadius: '4px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--tx3)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', letterSpacing: '.08em', flex: '0 0 auto'}}>marca</div>

      <div style={{display: 'flex', gap: '2px', flex: '0 0 auto'}}>
        <div onClick={goHome} style={{padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', color: `${navA.c}`, background: `${navA.b}`}}>Agora</div>
        <div onClick={goMapa} style={{padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', color: `${navM.c}`, background: `${navM.b}`}}>Mapa</div>
        <div onClick={goStatus} style={{padding: '6px 12px', borderRadius: '6px', fontSize: '12px', fontWeight: '500', cursor: 'pointer', color: `${navS.c}`, background: `${navS.b}`}}>Status</div>
      </div>

      <div style={{width: '1px', height: '26px', background: 'var(--bd)'}}></div>

      <div style={{display: 'flex', alignItems: 'center', gap: '10px', minWidth: '0', flex: '1 1 auto'}}>
        <div style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '4px 10px', borderRadius: '6px', border: `1px solid ${sev.c}`, background: `${sev.bg}`, flex: '0 0 auto'}}>
          <span style={{fontSize: '11px', color: `${sev.c}`}}>{sev.i}</span>
          <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '16px', fontWeight: '600', color: `${sev.c}`, lineHeight: '1'}}>{sev.n}</span>
          <span style={{fontSize: '12px', fontWeight: '600', color: `${sev.c}`, letterSpacing: '.01em'}}>{sev.l}</span>
        </div>
        <div style={{minWidth: '0', overflow: 'hidden', paddingRight: '8px'}}>
          <div style={{fontSize: '13px', color: 'var(--tx)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>{headline}</div>
          <div style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', marginTop: '2px'}}>FONTE: COR · HÁ 3 MIN</div>
        </div>
      </div>

      <div style={{display: 'flex', alignItems: 'center', gap: '8px', flex: '0 0 auto', whiteSpace: 'nowrap'}}>
        {Boolean(zoneChip) && (<>
          <div style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '5px 8px 5px 10px', borderRadius: '999px', background: 'var(--brand)', border: '1px solid var(--brand2)', fontSize: '11px', fontWeight: '500', color: 'var(--on-brand)'}}>
            <span>{zoneChip}</span>
            <span onClick={clearZone} style={{cursor: 'pointer', color: 'var(--on-brand2)', fontSize: '11px'}}>✕</span>
          </div>
        </>)}
        <div onClick={toggleZonePicker} style={{display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '12px'}}>
          <span style={{color: 'var(--tx2)'}}>Território</span>
          <span style={{color: 'var(--tx)', fontWeight: '500'}}>{zoneLabel}</span>
          <span style={{color: 'var(--tx3)', fontSize: '9px'}}>▾</span>
        </div>
        <div onClick={copyLink} style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontSize: '11px', color: 'var(--live-tx)'}}>⧉ {copyLabel}</div>
        <div onClick={toggleMode} style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px dashed var(--tx4)', cursor: 'pointer', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)', whiteSpace: 'nowrap'}}>DEMO: {modeLabel}</div>
        <div onClick={toggleTheme} title="Alternar tema" style={{display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', cursor: 'pointer', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)', whiteSpace: 'nowrap'}}>{themeIcon} {themeLabel}</div>
        <div style={{display: 'flex', alignItems: 'center', gap: '6px', paddingLeft: '4px'}}>
          <span style={{width: '7px', height: '7px', borderRadius: '50%', background: 'var(--live)', animation: 'pulse 2s infinite'}}></span>
          <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx2)', letterSpacing: '.06em'}}>AO VIVO</span>
        </div>
      </div>
    </div>

    {/* seletor territorial aberto */}
    {Boolean(zonePickerOpen) && (<>
      <div style={{position: 'absolute', top: '58px', right: '16px', zIndex: '60', width: '280px', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '10px', boxShadow: 'var(--shadow)', animation: 'fadeIn .12s'}}>
        <input placeholder="Buscar zona ou bairro" style={{width: '100%', background: 'var(--bg)', border: '1px solid var(--bd)', borderRadius: '6px', padding: '7px 9px', color: 'var(--tx)', fontSize: '12px', fontFamily: 'Inter,sans-serif', outline: 'none'}} />
        <div style={{display: 'flex', flexDirection: 'column', gap: '1px', marginTop: '8px', maxHeight: '240px', overflow: 'auto'}}>
          {(zones as any[]).map((z: any, zI: number) => (<React.Fragment key={zI}>
            <div onClick={z.pick} style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '7px 8px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', color: 'var(--tx)'}}>
              <span>{z.label}</span>
              <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)'}}>{z.meta}</span>
            </div>
          </React.Fragment>))}
        </div>
      </div>
    </>)}
    </>
  )
}
