/* Página "Info para Nerds" — a engenharia por trás do painel.
   Não veio do handoff do Claude Design: escrita aqui, reusando os tokens do
   cockpit (mesmas variáveis de cor, mesmas famílias, mesmo raio de borda). */
import React from 'react'
import type { Modelo } from '../modelo/tipos'
import { ABERTURA, HISTORICO, NOTA_RODAPE, STACK, VOLUME_MENSAL } from '../modelo/nerds'
import type { Metrica } from '../modelo/nerds'

function Cartao({ m, destaque }: { m: Metrica; destaque?: boolean }) {
  return (
    <div style={{flex: '1', minWidth: '0', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '12px 14px'}}>
      <div style={{fontSize: '10px', letterSpacing: '.1em', color: 'var(--tx3)', textTransform: 'uppercase', fontWeight: '600'}}>{m.rotulo}</div>
      <div style={{display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '6px'}}>
        <span style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: destaque ? '30px' : '26px', fontWeight: '600', letterSpacing: '-.02em', lineHeight: '1', color: destaque ? 'var(--brand)' : 'var(--tx)'}}>{m.valor}</span>
        <span style={{fontSize: '11px', color: 'var(--tx2)'}}>{m.unidade}</span>
      </div>
      <div style={{fontSize: '11px', color: 'var(--tx2)', marginTop: '7px', lineHeight: '1.45'}}>{m.detalhe}</div>
    </div>
  )
}

function Titulo({ children }: { children: React.ReactNode }) {
  return (
    <div style={{fontSize: '11px', fontWeight: '600', letterSpacing: '.1em', color: 'var(--tx2)', textTransform: 'uppercase', marginBottom: '10px'}}>{children}</div>
  )
}

export function VistaNerds({ m }: { m: Modelo }) {
  const { isNerds } = m
  if (!isNerds) return null
  return (
    <div style={{flex: '1 1 auto', minHeight: '0', overflow: 'auto', padding: '16px'}}>

      <div style={{display: 'flex', alignItems: 'flex-end', gap: '16px', marginBottom: '16px'}}>
        <div style={{maxWidth: '760px'}}>
          <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '22px', fontWeight: '600'}}>Info para Nerds</div>
          <div style={{fontSize: '12px', color: 'var(--tx2)', marginTop: '5px', lineHeight: '1.5'}}>{ABERTURA}</div>
        </div>
        <div style={{marginLeft: 'auto', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', letterSpacing: '.05em', textAlign: 'right', whiteSpace: 'nowrap'}}>
          18 FONTES · 4 NATUREZAS DE DADO<br />INGESTÃO CONTÍNUA DESDE 2026-08-06
        </div>
      </div>

      <Titulo>Volume que passa pela máquina</Titulo>
      <div style={{display: 'flex', gap: '12px', marginBottom: '18px'}}>
        {VOLUME_MENSAL.map((metrica, i) => (
          <Cartao key={i} m={metrica} destaque={i === 0} />
        ))}
      </div>

      <Titulo>Histórico já carregado</Titulo>
      <div style={{display: 'flex', gap: '12px', marginBottom: '18px'}}>
        {HISTORICO.map((metrica, i) => (
          <Cartao key={i} m={metrica} />
        ))}
      </div>

      <Titulo>Como isso é construído</Titulo>
      <div style={{display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px', marginBottom: '16px'}}>
        {STACK.map((bloco, bI) => (
          <div key={bI} style={{background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', overflow: 'hidden'}}>
            <div style={{padding: '9px 14px', borderBottom: '1px solid var(--bd)', background: 'var(--bg2)', fontSize: '10px', letterSpacing: '.1em', color: 'var(--tx3)', textTransform: 'uppercase', fontWeight: '600'}}>{bloco.titulo}</div>
            {bloco.linhas.map((linha, lI) => (
              <div key={lI} style={{display: 'grid', gridTemplateColumns: '.75fr 1.25fr', gap: '10px', padding: '8px 14px', borderBottom: lI === bloco.linhas.length - 1 ? 'none' : '1px solid var(--bd3)', alignItems: 'baseline'}}>
                <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', color: 'var(--tx3)', letterSpacing: '.03em'}}>{linha.chave}</span>
                <span style={{fontSize: '11.5px', color: 'var(--tx)', lineHeight: '1.45'}}>{linha.valor}</span>
              </div>
            ))}
          </div>
        ))}
      </div>

      <div style={{fontSize: '11px', color: 'var(--tx3)', lineHeight: '1.5'}}>{NOTA_RODAPE}</div>
    </div>
  )
}
