/* Barra de faixas: mostra em qual segmento da escala o valor caiu.

   Ocupa uma linha do cartão (14 px) e substitui a pergunta que o cockpit não
   respondia: "45 mm/h é muito?". A faixa ativa fica acesa, as outras ficam como
   contorno — dá pra ler a posição sem ler o texto. */

import type { Regua } from '../modelo/reguas'

export function BarraRegua({ regua }: { regua: Regua | null | undefined }) {
  if (!regua) return null
  return (
    <div title={regua.dica} style={{display: 'flex', alignItems: 'center', gap: '7px', cursor: 'help'}}>
      <div style={{display: 'flex', gap: '2px', flex: '0 0 auto'}}>
        {regua.faixas.map((_, i) => (
          <span
            key={i}
            style={{
              width: '13px', height: '4px', borderRadius: '2px',
              background: i === regua.indice ? regua.cores[i] : 'transparent',
              border: `1px solid ${i === regua.indice ? regua.cores[i] : 'var(--tx4)'}`,
            }}
          />
        ))}
      </div>
      <span style={{fontSize: '10.5px', color: regua.cores[regua.indice], whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}>
        {regua.rotulo}
      </span>
      <span style={{fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx4)', flex: '0 0 auto'}}>
        {regua.indice + 1}/{regua.faixas.length}
      </span>
    </div>
  )
}
