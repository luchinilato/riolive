/* Barreira de erro do painel.

   Em 2026-08-07 um endpoint respondeu 404, o corpo do erro chegou onde o código
   esperava uma lista, e o `.filter` estourou. Sem barreira, o React desmontou a
   árvore inteira e a tela ficou preta — um painel público sumindo por causa de
   um card. Num produto cujo tema é fonte de dado caindo, isso é inaceitável.

   Aqui a falha vira uma tela legível com o erro, em vez de nada. */

import React from 'react'

interface Estado {
  erro: Error | null
}

export class Barreira extends React.Component<{ children: React.ReactNode }, Estado> {
  state: Estado = { erro: null }

  static getDerivedStateFromError(erro: Error): Estado {
    return { erro }
  }

  componentDidCatch(erro: Error, info: React.ErrorInfo) {
    console.error('[painel] erro não tratado', erro, info.componentStack)
  }

  render() {
    if (!this.state.erro) return this.props.children
    return (
      <div style={{minHeight: '100vh', background: 'var(--bg)', color: 'var(--tx)', fontFamily: 'Inter,system-ui,sans-serif', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '32px'}}>
        <div style={{maxWidth: '560px', background: 'var(--card)', border: '1px solid var(--bd)', borderRadius: '10px', padding: '20px 22px'}}>
          <div style={{fontFamily: "'Space Grotesk',sans-serif", fontSize: '20px', fontWeight: 600}}>O painel falhou ao montar</div>
          <div style={{fontSize: '12px', color: 'var(--tx2)', marginTop: '8px', lineHeight: 1.5}}>
            Isto é defeito nosso, não uma fonte fora do ar — quando uma fonte cai, o painel mostra
            a queda em vez de sumir. O erro está abaixo e no console.
          </div>
          <pre style={{marginTop: '14px', padding: '10px 12px', background: 'var(--bg2)', border: '1px solid var(--bd2)', borderRadius: '6px', fontFamily: "'JetBrains Mono',monospace", fontSize: '11px', color: 'var(--s4)', whiteSpace: 'pre-wrap', overflowX: 'auto'}}>
            {this.state.erro.message}
          </pre>
          <div onClick={() => window.location.reload()} style={{marginTop: '14px', display: 'inline-block', padding: '7px 14px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--bg2)', cursor: 'pointer', fontSize: '12px'}}>
            Recarregar
          </div>
        </div>
      </div>
    )
  }
}
