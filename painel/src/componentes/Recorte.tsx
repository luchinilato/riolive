/* Carimbo de recorte territorial, no cabeçalho do cartão.

   Existe porque o seletor de zona é global e o recorte não: chuva, ar,
   segurança, queimadas, cidade viva e a memória sabem filtrar por zona; frota,
   trânsito, previsão, mar e céu medem a cidade e vão continuar medindo — não é
   pendência, é o que o dado é (linha de ônibus cruza a cidade, boia de mar fica
   fora do município).

   Sem zona escolhida nada aparece: o padrão é a cidade e carimbar "CIDADE
   INTEIRA" em tudo, o tempo todo, viraria ruído que ninguém lê — e carimbo que
   ninguém lê não protege de nada. */

import type { Modelo } from '../modelo/tipos'

export function Recorte({ marca }: { marca?: Modelo | null }) {
  if (!marca) return null
  const daZona = Boolean(marca.zona)
  return (
    <span
      title={daZona ? 'Este cartão mostra só o recorte escolhido.' : `Sem recorte por zona: ${marca.motivo}.`}
      style={{
        flex: '0 0 auto',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '1px 5px',
        borderRadius: '4px',
        border: `1px solid ${daZona ? 'var(--brand2)' : 'var(--bd)'}`,
        color: daZona ? 'var(--tx2)' : 'var(--tx3)',
        background: daZona ? 'var(--card2)' : 'transparent',
        fontFamily: "'JetBrains Mono',monospace",
        fontSize: '9px',
        letterSpacing: '.06em',
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
      }}
    >
      {daZona ? '◧' : '◻'} {marca.texto}
    </span>
  )
}
