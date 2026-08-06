/* Gerado do handoff do Claude Design (seção cidade_viva) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function PainelCidadeViva({ m }: { m: Modelo }) {
  const { lay, openCidade } = m
  return (
    <>
{/* CIDADE VIVA */}
          <div onClick={openCidade} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: '8px', overflow: 'hidden', cursor: 'pointer', gridColumn: `span ${lay.cidade.s}`, order: `${lay.cidade.o}`}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
              <span style={{display: 'flex', alignItems: 'center', gap: '5px', padding: '1px 5px', borderRadius: '4px', border: '1px solid var(--s2)', color: 'var(--s2)', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px'}}>◆ 2</span>
              <span style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', flex: '1 1 auto', minWidth: '0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>Cidade viva</span>
              <span style={{flex: '0 0 auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', whiteSpace: 'nowrap'}}>4</span>
              <span style={{flex: '0 0 auto', color: 'var(--tx3)', fontSize: '11px'}}>⤢</span>
            </div>
            <div style={{flex: '1 1 auto', minHeight: '0', overflowY: 'auto', overflowX: 'hidden', display: 'flex', flexDirection: 'column', gap: '7px'}}>
              <div style={{display: 'flex', flexDirection: 'column', gap: '3px', minWidth: '0'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--live-tx)'}}>SÁB 19:30</span>
                <span style={{minWidth: '0', fontSize: '11px', color: 'var(--tx)', lineHeight: '1.35'}}>Flamengo × Vitória, Maracanã <span style={{color: 'var(--tx2)'}}>— esquema especial de trânsito</span></span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: '3px', minWidth: '0', borderTop: '1px solid var(--bd3)', paddingTop: '7px'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--s2)'}}>QUI 22H</span>
                <span style={{minWidth: '0', fontSize: '11px', color: 'var(--tx)', lineHeight: '1.35'}}>Águas do Rio: manutenção programada em Irajá <span style={{color: 'var(--tx2)'}}>até 5h</span></span>
              </div>
              <div style={{display: 'flex', flexDirection: 'column', gap: '3px', minWidth: '0', borderTop: '1px solid var(--bd3)', paddingTop: '7px'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)'}}>DOM 07:00</span>
                <span style={{minWidth: '0', fontSize: '11px', color: 'var(--tx2)', lineHeight: '1.35'}}>Aterro do Flamengo fechado para lazer</span>
              </div>
            </div>
            <div style={{display: 'flex', alignItems: 'center', gap: '6px', borderTop: '1px solid var(--bd2)', paddingTop: '7px', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx3)', letterSpacing: '.05em'}}>
              <span style={{width: '5px', height: '5px', borderRadius: '50%', background: 'var(--s1)'}}></span>THESPORTSDB + ÁGUAS DO RIO · HÁ 30 MIN
            </div>
          </div>
    </>
  )
}
