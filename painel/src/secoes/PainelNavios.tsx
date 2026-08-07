/* Gerado do handoff do Claude Design (seção navios) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function PainelNavios({ m }: { m: Modelo }) {
  const { lay, openNavios } = m
  return (
    <>
{/* NAVIOS · DEGRADADO */}
          <div onClick={openNavios} style={{background: 'var(--card)', border: '1px solid var(--warn-bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.navios.s}`, order: `${lay.navios.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span title="Sem leitura: não há dado para avaliar severidade. A fonte AIS não chegou a ser integrada." style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: '1px dashed var(--tx4)', color: 'var(--tx3)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', whiteSpace: 'nowrap'}}>s/ dado</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Navios (AIS)</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>BAÍA</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            {/* O card exibia "38 embarcações · 12 fundeadas", número que nunca saiu
                de fonte alguma: o AIS não chegou a ser integrado. Ausência declarada
                no lugar. [[DEC - Interface não afirma o que não mediu]] */}
            <div style={{display: 'flex', alignItems: 'flex-start', gap: '6px', padding: '6px 8px', borderRadius: '6px', background: 'var(--warn-bg)', border: '1px solid var(--warn-bd)', fontSize: '11px', color: 'var(--warn-tx)', lineHeight: '1.35'}}>
              <span>⚠</span><span>Fonte não integrada: o aisstream.io ficou mudo nos testes e a coleta nunca entrou no ar.</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'hidden', display: 'flex', flexDirection: 'column', gap: '4px'}}>
              <div style={{display: 'flex', alignItems: 'baseline', gap: '6px'}}>
                <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '24px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: 'var(--tx3)'}}>—</span>
                <span style={{fontSize: '11px', color: 'var(--tx3)'}}>embarcações na Baía</span>
              </div>
              <div style={{fontSize: '11px', color: 'var(--tx3)', lineHeight: '1.35'}}>Sem leitura nenhuma — nem antiga. Quando o AIS entrar, aparecem aqui as fundeadas, atracadas e em trânsito.</div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--s2)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s2)'}}></span>FONTE: AISSTREAM · SEM INTEGRAÇÃO
            </div>
          </div>
    </>
  )
}
