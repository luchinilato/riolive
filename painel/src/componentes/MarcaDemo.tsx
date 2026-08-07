/* Página de prova da marca (só dev: /marca.html, fora do build de produção).
   Serve pra checar as três coisas que quebram na mão: o arquivo único servindo
   os dois temas, o contraste do acento no claro, e os clipPath não colidindo
   quando a marca aparece mais de uma vez na mesma página. */

import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { LARGURA_MIN_HORIZONTAL, Logo } from './Logo'

export function Bloco({ titulo, nota, children }: { titulo: string; nota?: string; children: ReactNode }) {
  return (
    <section style={{ border: '1px solid var(--bd)', borderRadius: '10px', background: 'var(--card)', padding: '18px 20px 20px' }}>
      <h2 style={{ margin: '0 0 4px', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px', letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--tx3)', fontWeight: 500 }}>{titulo}</h2>
      {nota && <p style={{ margin: '0 0 16px', fontSize: '12px', color: 'var(--tx2)', lineHeight: 1.5, maxWidth: '62ch' }}>{nota}</p>}
      {children}
    </section>
  )
}

export function Amostra({ rotulo, children }: { rotulo: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-start' }}>
      {children}
      <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9.5px', color: 'var(--tx3)', letterSpacing: '.04em' }}>{rotulo}</span>
    </div>
  )
}

export function MarcaDemo() {
  const [tema, setTema] = useState<'escuro' | 'claro'>('escuro')

  // mesmo mecanismo do App.tsx: data-tema no <html>, tokens resolvem o resto
  useEffect(() => {
    document.documentElement.dataset.tema = tema
  }, [tema])

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--tx)', fontFamily: 'Inter,system-ui,sans-serif', padding: '28px 32px 64px' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontFamily: "'Space Grotesk',sans-serif", fontSize: '18px', fontWeight: 600 }}>Sinal Carioca — prova da marca</h1>
        <button
          onClick={() => setTema((t) => (t === 'escuro' ? 'claro' : 'escuro'))}
          style={{ marginLeft: 'auto', padding: '7px 12px', borderRadius: '6px', border: '1px solid var(--bd)', background: 'var(--card)', color: 'var(--tx2)', cursor: 'pointer', fontFamily: "'JetBrains Mono',monospace", fontSize: '10px' }}
        >
          {tema === 'escuro' ? '☾ ESCURO' : '☀ CLARO'} — alternar
        </button>
      </header>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <Bloco
          titulo="Duas instâncias na mesma página"
          nota="O teste que importa: ids de clipPath repetidos fazem o recorte da segunda marca casar com o clipPath da primeira e o acento sumir. Com useId() sufixando id e url(#…), as quatro abaixo recortam igual."
        >
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Amostra rotulo="instância 1 · horizontal"><Logo style={{ height: '44px' }} /></Amostra>
            <Amostra rotulo="instância 2 · horizontal"><Logo style={{ height: '44px' }} /></Amostra>
            <Amostra rotulo="instância 3 · empilhado"><Logo variante="empilhado" style={{ height: '84px' }} /></Amostra>
            <Amostra rotulo="instância 4 · empilhado"><Logo variante="empilhado" style={{ height: '84px' }} /></Amostra>
          </div>
        </Bloco>

        <Bloco
          titulo="Horizontal — cabeçalho e alturas limitadas"
          nota={`Piso de ${LARGURA_MIN_HORIZONTAL}px de largura: abaixo disso "Sinal Carioca" deixa de ler e ainda não existe símbolo isolado pra cair.`}
        >
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Amostra rotulo="h=26px (~147px) · cabeçalho desktop"><Logo style={{ height: '26px' }} /></Amostra>
            <Amostra rotulo={`w=${LARGURA_MIN_HORIZONTAL}px · piso, cabeçalho mobile`}><Logo style={{ width: `${LARGURA_MIN_HORIZONTAL}px` }} /></Amostra>
            <Amostra rotulo="h=64px · uso ampliado"><Logo style={{ height: '64px' }} /></Amostra>
          </div>
        </Bloco>

        <Bloco
          titulo="Empilhado — onde sobra espaço vertical"
          nota="Login, estado vazio, splash. Hoje o painel não tem nenhuma dessas telas, então esta variante ainda não tem uso em produção — mas está pronta."
        >
          <div style={{ display: 'flex', gap: '40px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Amostra rotulo="h=72px"><Logo variante="empilhado" style={{ height: '72px' }} /></Amostra>
            <Amostra rotulo="h=120px"><Logo variante="empilhado" style={{ height: '120px' }} /></Amostra>
            <Amostra rotulo="h=180px"><Logo variante="empilhado" style={{ height: '180px' }} /></Amostra>
          </div>
        </Bloco>

        <Bloco
          titulo="Herança de cor"
          nota="As letras são currentColor, então a marca segue a cor do texto do pai — é assim que um arquivo único atende os dois temas. O acento fica no token --sc-acento e não herda."
        >
          <div style={{ display: 'flex', gap: '32px', flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <Amostra rotulo="padrão (--sc-marca)"><Logo style={{ height: '38px' }} /></Amostra>
            <div style={{ color: 'var(--tx3)' }}>
              <Amostra rotulo="pai em var(--tx3)"><Logo style={{ height: '38px', color: 'inherit' }} /></Amostra>
            </div>
            <div style={{ color: 'var(--s4)' }}>
              <Amostra rotulo="pai em var(--s4)"><Logo style={{ height: '38px', color: 'inherit' }} /></Amostra>
            </div>
          </div>
        </Bloco>

        <Bloco
          titulo="Sobre fundos do tema"
          nota="Checagem rápida de leitura nas superfícies que o painel realmente usa."
        >
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            {[
              { nome: '--bg', cor: 'var(--bg)' },
              { nome: '--card', cor: 'var(--card)' },
              { nome: '--card2', cor: 'var(--card2)' },
              { nome: '--bg3', cor: 'var(--bg3)' },
            ].map((f) => (
              <div key={f.nome} style={{ background: f.cor, border: '1px solid var(--bd)', borderRadius: '8px', padding: '18px 20px', display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'flex-start' }}>
                <Logo style={{ height: '30px' }} />
                <span style={{ fontFamily: "'JetBrains Mono',monospace", fontSize: '9.5px', color: 'var(--tx3)' }}>{f.nome}</span>
              </div>
            ))}
          </div>
        </Bloco>
      </div>
    </div>
  )
}
