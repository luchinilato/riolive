/* Gerado do handoff do Claude Design (seção rodape) — edite com cuidado:
   a fonte visual da verdade é docs/design/handoff/painel-rio.dc.html */
import React from 'react'
import type { Modelo } from '../modelo/tipos'

export function Rodape({ m }: { m: Modelo }) {
  const { goNerds, goStatus } = m
  return (
    <>
{/* ================= RODAPÉ ================= */}
    <div style={{flex: '0 0 30px', height: '30px', borderTop: '1px solid var(--bd)', background: 'var(--bg)', display: 'flex', alignItems: 'center', gap: '16px', padding: '0 16px', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', letterSpacing: '.04em'}}>
      <span onClick={goStatus} style={{cursor: 'pointer', color: 'var(--tx2)'}}><span style={{color: 'var(--s1)'}}>●</span> 11 DE 12 FONTES OPERANDO NORMALMENTE</span>
      <span style={{color: 'var(--tx4)'}}>/</span>
      <span onClick={goNerds} style={{cursor: 'pointer'}}>INFO PARA NERDS</span>
      <span style={{color: 'var(--tx4)'}}>/</span>
      <span style={{cursor: 'pointer'}}>METODOLOGIA</span>
      <span style={{color: 'var(--tx4)'}}>/</span>
      <span style={{cursor: 'pointer'}}>LICENÇA DOS DADOS · CC-BY 4.0</span>
      <span style={{marginLeft: 'auto'}}>ATUALIZADO 14:31:07 · FUSO AMERICA/SAO_PAULO</span>
    </div>
    </>
  )
}
