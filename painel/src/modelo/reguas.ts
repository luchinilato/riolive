/* Réguas: onde o número cai numa escala que o leitor entende.

   "45 mm/h" não diz nada a quem não é meteorologista. A régua responde "isso é
   muito?" — e a resposta certa depende da grandeza:

   - classificação da própria fonte (chuva, ar): não precisa de histórico, é
     critério oficial e público;
   - razão realizado ÷ referência (mobilidade, trânsito): o denominador é o
     planejado, que já temos;
   - memória (percentil da série): só existe onde há histórico — hoje, segurança.

   A régua NUNCA é inventada: cada uma diz de onde vem, e a fonte aparece no
   tooltip. Onde não há critério publicado, o campo `fonte` diz que a divisão é
   nossa. [[DEC - Interface não afirma o que não mediu]] */

export interface Regua {
  rotulo: string       // onde caiu: "chuva forte"
  indice: number       // faixa atual (0-based)
  faixas: string[]     // nomes das faixas, em ordem
  cores: string[]      // cor de cada faixa
  dica: string         // tooltip: escala completa + fonte
  valor?: string       // valor formatado, quando ajuda a ler a barra
}

const monta = (
  valor: number,
  cortes: number[],
  faixas: string[],
  cores: string[],
  escala: string,
  fonte: string,
): Regua => {
  let indice = 0
  while (indice < cortes.length && valor >= cortes[indice]) indice += 1
  return {
    rotulo: faixas[indice],
    indice,
    faixas,
    cores,
    dica: `${escala}\nFonte da classificação: ${fonte}.`,
  }
}

/* Classificação do Alerta Rio / COR, publicada por eles:
   fraca < 5 mm/h · moderada 5 a 25 · forte 25 a 50 · muito forte > 50. */
export const reguaChuva = (mmPorHora: number): Regua =>
  monta(
    mmPorHora,
    [5, 25, 50],
    ['fraca', 'moderada', 'forte', 'muito forte'],
    ['var(--s1)', '#149cc6', 'var(--s3)', 'var(--s4)'],
    'Intensidade de chuva: fraca abaixo de 5 mm/h · moderada de 5 a 25 · forte de 25 a 50 · muito forte acima de 50.',
    'Alerta Rio / COR',
  )

/* Diretriz da OMS (2021) pra PM2.5: 15 µg/m³ na média de 24 h. O corte de 25
   marca o dobro do recomendado — nossa divisão, declarada como tal. */
export const reguaAr = (pm25: number): Regua =>
  monta(
    pm25,
    [15, 25],
    ['dentro do limite', 'acima do limite', 'muito acima'],
    ['var(--s1)', 'var(--s2)', 'var(--s3)'],
    'PM2.5: a OMS recomenda até 15 µg/m³ na média de 24 h. Acima de 25 é mais que o dobro do recomendado.',
    'OMS (2021); o corte de 25 é divisão nossa',
  )

/* Altura de onda: a divisão é nossa, calibrada pelo uso comum da orla. */
export const reguaMar = (metros: number): Regua =>
  monta(
    metros,
    [1.5, 2.5],
    ['calmo', 'moderado', 'agitado'],
    ['var(--s1)', 'var(--s2)', 'var(--s3)'],
    'Altura de onda: calmo abaixo de 1,5 m · moderado de 1,5 a 2,5 · agitado acima de 2,5.',
    'divisão nossa, não há classificação oficial pra orla do Rio',
  )

/* Aqui a régua não é escala: é a razão entre o que a cidade prometeu e o que
   ela está entregando. O denominador é o GTFS. */
export const reguaFrota = (pctAtivas: number): Regua =>
  monta(
    pctAtivas,
    [70, 90],
    ['bem abaixo do planejado', 'abaixo do planejado', 'em linha com o planejado'],
    ['var(--s3)', 'var(--s2)', 'var(--s1)'],
    'Percentual das linhas com frequência planejada no GTFS que têm veículo transmitindo agora. Os cortes de 70% e 90% são divisão nossa.',
    'GTFS da SMTR ÷ GPS da frota',
  )

/* Fluidez = velocidade atual ÷ fluxo livre do trecho, como o TomTom define. */
export const reguaTransito = (fluidezPct: number): Regua =>
  monta(
    fluidezPct,
    [60, 85],
    ['congestionado', 'moderado', 'fluindo'],
    ['var(--s3)', 'var(--s2)', 'var(--s1)'],
    'Fluidez é a velocidade atual dividida pela velocidade de fluxo livre do trecho. Abaixo de 60% conta como congestionado; acima de 85%, fluindo.',
    'TomTom (fluxo livre); os cortes são divisão nossa',
  )
