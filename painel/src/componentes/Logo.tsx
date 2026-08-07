/* Marca Sinal Carioca — SVG inline no DOM (nunca <img> nem background-image:
   só inline faz `currentColor` e `var(--sc-acento)` valerem, que é o que permite
   um arquivo único servir os dois temas). Geometria vem intacta dos .svg. */

import { useId, useMemo } from 'react'
import type { CSSProperties } from 'react'
import bruteHorizontal from '../assets/sinal-carioca-horizontal.svg?raw'
import bruteEmpilhado from '../assets/sinal-carioca-empilhado.svg?raw'

export type VarianteMarca = 'horizontal' | 'empilhado'

const ARQUIVOS: Record<VarianteMarca, string> = {
  horizontal: bruteHorizontal,
  empilhado: bruteEmpilhado,
}

/* ids fixos do contrato dos arquivos; precisam virar únicos por instância */
const IDS_INTERNOS = ['scSinal', 'scCarioca'] as const

/* Largura mínima legível do horizontal: abaixo disso "Sinal Carioca" deixa de
   ler e ainda não existe símbolo isolado pra cair. */
export const LARGURA_MIN_HORIZONTAL = 120

type Arquivo = { viewBox: string; miolo: string }

/* O <svg> raiz é reescrito em JSX (pra receber className/style/aria); o miolo
   — defs + paths — entra sem tocar. */
function lerArquivo(bruto: string): Arquivo {
  const viewBox = /<svg[^>]*\sviewBox="([^"]+)"/.exec(bruto)?.[1] ?? ''
  const miolo = bruto.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '')
  return { viewBox, miolo }
}

const ARQUIVOS_LIDOS: Record<VarianteMarca, Arquivo> = {
  horizontal: lerArquivo(ARQUIVOS.horizontal),
  empilhado: lerArquivo(ARQUIVOS.empilhado),
}

/* Duas marcas na mesma página com o mesmo id de clipPath: o segundo recorte
   casa com o primeiro clipPath e o acento some. Sufixar id e url(#…) resolve. */
function comIdsUnicos(miolo: string, sufixo: string): string {
  let saida = miolo
  for (const id of IDS_INTERNOS) {
    saida = saida
      .replaceAll(`id="${id}"`, `id="${id}-${sufixo}"`)
      .replaceAll(`url(#${id})`, `url(#${id}-${sufixo})`)
  }
  return saida
}

export function Logo({
  variante = 'horizontal',
  className,
  style,
}: {
  variante?: VarianteMarca
  className?: string
  style?: CSSProperties
}) {
  /* useId pode trazer caracteres não-alfanuméricos (React 19: «r0»); limpo
     porque o valor vira id de SVG e alvo de url(#…). */
  const sufixo = useId().replace(/[^a-zA-Z0-9]/g, '')
  const { viewBox, miolo } = ARQUIVOS_LIDOS[variante]
  const html = useMemo(() => comIdsUnicos(miolo, sufixo), [miolo, sufixo])

  return (
    <svg
      viewBox={viewBox}
      role="img"
      aria-label="Sinal Carioca"
      className={className}
      /* sem width/height: o tamanho vem de fora; o viewBox dá a proporção
         intrínseca, então definir só a altura já acerta a largura.
         `color` alimenta o currentColor das letras. */
      style={{ display: 'block', color: 'var(--sc-marca)', ...style }}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
