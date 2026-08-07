/* Dossiês temáticos montados com dado real da API.

   Cada função recebe o esqueleto vindo do base.ts (título, severidade, rota) e
   devolve o dossiê preenchido. Nenhuma delas inventa número: quando a leitura
   não existe, o campo sai como "—" com o motivo escrito, ou o dossiê inteiro
   declara ausência. [[DEC - Interface não afirma o que não mediu]].

   Chuva, mobilidade, trânsito e segurança continuam montados no dadosReais.ts —
   nasceram lá e não vale mexer neles nesta leva. */

import { SEV, poly } from './base'

/* A API pode responder com objeto de erro ({"detail": ...}) em vez de lista —
   404, 500, rota que ainda não subiu. Tratar isso como lista estoura `.filter` e
   derruba o painel inteiro, que é o pior desfecho possível num produto cujo tema
   é justamente fonte caindo. Aqui a resposta inesperada vira lista vazia. */
export const lista = (valor: unknown): any[] => (Array.isArray(valor) ? valor : [])

const hhmm = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
const ddmm = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getDate()).padStart(2, '0')}/${String(d.getMonth() + 1).padStart(2, '0')}`
}
const diaHora = (iso: string) => `${ddmm(iso)} ${hhmm(iso)}`

const nQuebrado = (v: number, casas = 1) => v.toFixed(casas).replace('.', ',')

const idadeEmMin = (iso: string) => Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000))
const idadeLegivel = (iso: string) => {
  const min = idadeEmMin(iso)
  if (min < 60) return `há ${min} min`
  const h = Math.round(min / 60)
  return h < 48 ? `há ${h} h` : `há ${Math.round(h / 24)} d`
}

/* Caixa do mapinha do dossiê: projeção linear simples, não é MapLibre. O bbox da
   região é maior que o do município porque avião e navio saem da cidade. */
const BBOX_MUNICIPIO = { latN: -22.74, latS: -23.11, lonW: -43.8, lonE: -43.09 }
const BBOX_REGIAO = { latN: -22.35, latS: -23.35, lonW: -44.05, lonE: -42.55 }

function projetar(lat: number, lon: number, bbox = BBOX_MUNICIPIO) {
  const limitar = (v: number) => Math.min(96, Math.max(2, v))
  return {
    x: limitar(((lon - bbox.lonW) / (bbox.lonE - bbox.lonW)) * 86 + 6).toFixed(0),
    y: limitar(((bbox.latN - lat) / (bbox.latN - bbox.latS)) * 78 + 10).toFixed(0),
  }
}

const ROSA = ['N', 'NE', 'L', 'SE', 'S', 'SO', 'O', 'NO']
const cardinal = (graus: number | null | undefined) =>
  graus == null ? '—' : ROSA[Math.round(graus / 45) % 8]

/* Eixo de até 8 rótulos cobrindo a série INTEIRA — do primeiro ao último ponto.
   Amostrar de N em N e cortar nos 8 primeiros (o que o protótipo fazia) rotula só
   o começo da série: o gráfico ia até 10:00 e o eixo parava nas 04:00. */
export function eixo(pontos: any[], rotulo: (ts: string) => string) {
  if (pontos.length <= 8) return pontos.map((p) => rotulo(p.ts))
  const indices = Array.from({ length: 8 }, (_, i) => Math.round((i * (pontos.length - 1)) / 7))
  return indices.map((i) => rotulo(pontos[i].ts))
}

/* Posição da caixinha de leitura sobre o gráfico. No protótipo ela era fixa em
   26%/34% e descrevia um ponto qualquer da série — apontava para o lugar errado.
   Aqui ela vai no x do ponto que descreve; passando de 60% ela alinha à direita
   pra não vazar do gráfico. */
export function posicaoTip(indice: number, total: number, valor: number, teto: number) {
  return {
    tipLeft: total > 1 ? (indice / (total - 1)) * 100 : 50,
    tipTop: Math.min(72, Math.max(6, (1 - valor / (teto || 1)) * 100)),
  }
}

// ---------------------------------------------------------------- PREVISÃO

export function dossiePrevisao(base: any, pontos: any[]) {
  const centro = pontos.find((p) => p.codigo === 'centro') ?? pontos[0]
  const met = centro?.metricas ?? {}
  const temps = lista(met.temp_c)
  if (!temps.length) {
    return {
      ...base,
      ausencia: {
        titulo: 'Sem rodada de previsão válida',
        texto: 'O Open-Meteo roda a cada 3 horas e a última rodada não trouxe valores pra frente deste instante. Guardamos todas as rodadas — assim que a próxima chegar, a curva volta sozinha.',
      },
    }
  }

  const prox24 = (arr: unknown) => lista(arr).slice(0, 24)
  const tempsProx = prox24(met.temp_c)
  const maxTemp = Math.max(...tempsProx.map((p) => p.valor))
  const minTemp = Math.min(...tempsProx.map((p) => p.valor))
  const horaMax = tempsProx.find((p) => p.valor === maxTemp)
  const chuva24 = prox24(met.precipitacao_mm).reduce((s, p) => s + p.valor, 0)
  const probMax = Math.max(0, ...prox24(met.prob_precipitacao_pct).map((p) => p.valor))
  const ventoMax = Math.max(0, ...prox24(met.vento_kmh).map((p) => p.valor))
  const umidade = lista(met.umidade_pct)[0]?.valor

  const oeste = pontos.find((p) => p.codigo === 'zona_oeste')
  const tempsOeste = lista(oeste?.metricas?.temp_c)
  const teto = Math.max(maxTemp, ...tempsOeste.map((p) => p.valor)) + 2

  const linhas = pontos
    .map((p) => {
      const t = lista(p.metricas?.temp_c)
      const chuva = lista(p.metricas?.precipitacao_mm).slice(0, 24).reduce((s, x) => s + x.valor, 0)
      return { nome: p.nome, lat: p.lat, lon: p.lon, agora: t[0]?.valor, max: t.length ? Math.max(...t.slice(0, 24).map((x) => x.valor)) : null, chuva }
    })
    .sort((a, b) => (b.agora ?? -99) - (a.agora ?? -99))

  return {
    ...base,
    ausencia: null,
    sev: chuva24 >= 20 ? SEV[3] : chuva24 >= 5 ? SEV[2] : SEV[1],
    kpis: [
      { l: 'Temperatura agora · Centro', v: `${Math.round(temps[0].valor)}`, u: '°C', c: 'var(--tx)', d: 'valor de modelo pra este instante, não termômetro na rua' },
      { l: 'Máxima nas próximas 24 h', v: `${Math.round(maxTemp)}`, u: horaMax ? `°C · ${hhmm(horaMax.ts)}` : '°C', c: maxTemp >= 35 ? 'var(--s3)' : 'var(--tx)', d: `mínima prevista de ${Math.round(minTemp)} °C` },
      { l: 'Chuva prevista · 24 h', v: nQuebrado(chuva24), u: 'mm acumulados', c: chuva24 >= 20 ? 'var(--s3)' : chuva24 >= 5 ? 'var(--s2)' : 'var(--tx)', d: `probabilidade máxima de ${Math.round(probMax)}%` },
      { l: 'Vento máximo', v: `${Math.round(ventoMax)}`, u: 'km/h', c: ventoMax >= 60 ? 'var(--s3)' : 'var(--tx)', d: umidade != null ? `umidade agora: ${Math.round(umidade)}%` : 'umidade sem leitura nesta rodada' },
    ],
    chartTitle: 'Temperatura prevista · próximas 48 h',
    s1: `${centro.nome} (°C)`,
    s2: tempsOeste.length ? `${oeste.nome} (°C)` : '',
    series1: poly(temps.map((p) => p.valor), 1000, 205, teto),
    series2: tempsOeste.length ? poly(tempsOeste.map((p) => p.valor), 1000, 205, teto) : '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: eixo(temps, hhmm),
    tipTime: `${hhmm(temps[0].ts)} · ${centro.nome.toUpperCase()}`,
    tip1: `${Math.round(temps[0].valor)} °C`,
    tip2: tempsOeste.length ? `${Math.round(tempsOeste[0].valor)} °C na Zona Oeste` : '',
    ...posicaoTip(0, temps.length, temps[0].valor, teto),
    cols: ['Ponto', 'Agora', 'Máx 24 h', 'Chuva 24 h', 'Situação'],
    rows: linhas.map((p) => ({
      a: p.nome,
      b: p.agora != null ? `${Math.round(p.agora)} °C` : '—',
      c: p.max != null ? `${Math.round(p.max)} °C` : '—',
      d: `${nQuebrado(p.chuva)} mm`,
      e: p.chuva >= 5 ? 'chuva prevista' : p.chuva > 0 ? 'garoa prevista' : 'sem chuva',
      ec: p.chuva >= 5 ? 'var(--s2)' : 'var(--tx2)',
    })),
    tableTitle: `${pontos.length} pontos de previsão na cidade`,
    sortBy: 'TEMPERATURA AGORA',
    mapTitle: 'Pontos de previsão',
    mapNota: 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO',
    mapDots: linhas
      .filter((p) => p.lat != null)
      .map((p) => ({ ...projetar(p.lat, p.lon), c: (p.agora ?? 0) >= 32 ? 'var(--s3)' : '#2c96c4', t: `${p.nome}: ${p.agora != null ? Math.round(p.agora) + ' °C' : 'sem valor'}` })),
    context: 'Previsão de modelo, não medição. O Open-Meteo roda a cada 3 h e guardamos todas as rodadas — dá pra confrontar depois o previsto com o que a cidade mediu.',
    seal: centro.emitida_em ? `OPEN-METEO · RODADA DE ${hhmm(centro.emitida_em)}` : 'OPEN-METEO',
  }
}

// ---------------------------------------------------------------- AR

const LIMITE_OMS_PM25 = 15  // média de 24 h recomendada pela OMS (2021)

export function dossieAr(base: any, estacoes: any[], serie: any[]) {
  const comLeitura = estacoes.filter((e) => e.leituras?.pm25 != null)
  const ordenadas = [...comLeitura].sort((a, b) => b.leituras.pm25 - a.leituras.pm25)
  const pior = ordenadas[0]
  /* Sem leitura ≠ sem resposta: a API respondeu com as estações, elas é que não
     publicaram. Culpar o nosso servidor aqui seria tão errado quanto inventar o
     número — o dossiê segue montado, com a tabela e os campos em "—". */
  if (!pior) {
    return {
      ...base,
      ausencia: {
        titulo: 'Estações sem leitura recente',
        texto: `As ${estacoes.length} estações estão listadas abaixo, mas nenhuma publicou PM2.5 nas últimas 6 horas. O OpenAQ reúne operadores diferentes e é comum uma rodada atrasar; enquanto não chega, não há número a exibir.`,
      },
      kpis: [],
      chartTitle: '', s1: '', s2: '', series1: '', series2: '', axis: [], tipTime: '',
      cols: ['Estação', 'PM2.5', 'PM10', 'O₃', 'Situação'],
      rows: estacoes.map((e) => ({
        a: e.bairro ?? e.nome, b: '—', c: '—', d: '—',
        e: 'sem leitura', ec: 'var(--tx3)',
      })),
      tableTitle: `${estacoes.length} estações agregadas pelo OpenAQ`,
      sortBy: '',
      mapTitle: '', mapDots: [], context: '', seal: 'OPENAQ · SEM LEITURA RECENTE',
    }
  }

  const media = comLeitura.reduce((s, e) => s + e.leituras.pm25, 0) / comLeitura.length
  const acima = comLeitura.filter((e) => e.leituras.pm25 >= LIMITE_OMS_PM25).length
  const faixa = (v: number) => (v >= 25 ? 'var(--s3)' : v >= LIMITE_OMS_PM25 ? 'var(--s2)' : 'var(--s1)')
  const rotulo = (v: number) => (v >= 25 ? 'Ruim' : v >= LIMITE_OMS_PM25 ? 'Moderada' : 'Boa')

  // a série vem por estação; o painel mostra a pior leitura de cada hora
  const porHora = new Map<string, number>()
  for (const p of serie) porHora.set(p.ts, Math.max(porHora.get(p.ts) ?? 0, p.maximo ?? p.media ?? 0))
  const horas = [...porHora.entries()].sort(([a], [b]) => (a < b ? -1 : 1))
  const valores = horas.map(([, v]) => v)
  const tetoSerie = Math.max(25, ...valores)

  const maisNova = comLeitura.map((e) => e.ts).filter(Boolean).sort().at(-1)

  return {
    ...base,
    ausencia: null,
    sev: pior.leituras.pm25 >= 25 ? SEV[3] : pior.leituras.pm25 >= LIMITE_OMS_PM25 ? SEV[2] : SEV[1],
    kpis: [
      { l: 'Pior PM2.5 agora', v: nQuebrado(pior.leituras.pm25), u: `µg/m³ · ${pior.bairro ?? pior.nome}`, c: faixa(pior.leituras.pm25), d: `qualidade ${rotulo(pior.leituras.pm25).toLowerCase()} pela referência da OMS` },
      { l: 'Média entre estações', v: nQuebrado(media), u: 'µg/m³ de PM2.5', c: faixa(media), d: 'média simples das estações que reportaram' },
      { l: 'Acima da recomendação', v: String(acima), u: `de ${comLeitura.length} estações`, c: acima ? 'var(--s2)' : 'var(--s1)', d: `limite da OMS (2021): ${LIMITE_OMS_PM25} µg/m³ em 24 h` },
      { l: 'Estações reportando', v: `${comLeitura.length}`, u: `de ${estacoes.length}`, c: comLeitura.length === estacoes.length ? 'var(--s1)' : 'var(--s2)', d: 'estação atrasada continua na lista, sem leitura' },
    ],
    chartTitle: 'PM2.5 · pior estação a cada hora',
    s1: 'máxima entre as estações (µg/m³)',
    s2: valores.length ? `recomendação da OMS (${LIMITE_OMS_PM25} µg/m³)` : '',
    series1: valores.length >= 2 ? poly(valores, 1000, 205, tetoSerie) : '',
    series2: valores.length >= 2 ? poly(valores.map(() => LIMITE_OMS_PM25), 1000, 205, tetoSerie) : '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: horas.length ? eixo(horas.map(([ts]) => ({ ts })), hhmm) : [],
    tipTime: horas.length ? `${hhmm(horas.at(-1)![0])} · MÁXIMA` : '',
    tip1: horas.length ? `${nQuebrado(horas.at(-1)![1])} µg/m³` : '',
    tip2: '',
    ...(horas.length ? posicaoTip(horas.length - 1, horas.length, horas.at(-1)![1], tetoSerie) : {}),
    notaGrafico: valores.length >= 2 ? '' : 'Sem série horária de PM2.5 no recorte — o agregado materializa ao longo do dia.',
    cols: ['Estação', 'PM2.5', 'PM10', 'O₃', 'Situação'],
    rows: [...estacoes]
      .sort((a, b) => (b.leituras?.pm25 ?? -1) - (a.leituras?.pm25 ?? -1))
      .map((e) => ({
        a: e.bairro ?? e.nome,
        b: e.leituras?.pm25 != null ? nQuebrado(e.leituras.pm25) : '—',
        c: e.leituras?.pm10 != null ? nQuebrado(e.leituras.pm10) : '—',
        d: e.leituras?.o3 != null ? nQuebrado(e.leituras.o3) : '—',
        e: e.leituras?.pm25 != null ? rotulo(e.leituras.pm25) : e.ts ? 'sem PM2.5' : 'sem leitura',
        ec: e.leituras?.pm25 != null ? faixa(e.leituras.pm25) : 'var(--tx3)',
      })),
    tableTitle: `${estacoes.length} estações agregadas pelo OpenAQ`,
    sortBy: 'PM2.5',
    mapTitle: 'Estações de qualidade do ar',
    mapNota: 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO',
    mapDots: estacoes
      .filter((e) => e.lat != null)
      .map((e) => ({
        ...projetar(e.lat, e.lon),
        c: e.leituras?.pm25 == null ? 'var(--tx4)' : faixa(e.leituras.pm25),
        t: `${e.nome}: ${e.leituras?.pm25 != null ? nQuebrado(e.leituras.pm25) + ' µg/m³' : 'sem leitura'}`,
      })),
    context: `PM2.5 é a partícula fina que entra no pulmão. A OMS recomenda até ${LIMITE_OMS_PM25} µg/m³ na média de 24 h; na tela está a leitura horária — comparável, não idêntica ao critério. Nem toda estação mede todos os poluentes.`,
    seal: maisNova ? `OPENAQ · ${comLeitura.length} ESTAÇÕES · ${idadeLegivel(maisNova).toUpperCase()}` : 'OPENAQ · SEM LEITURA RECENTE',
  }
}

// ---------------------------------------------------------------- MAR

export function dossieMar(base: any, pontos: any[]) {
  const copa = pontos.find((p) => p.codigo === 'mar_copacabana') ?? pontos[0]
  const barra = pontos.find((p) => p.codigo === 'mar_barra')
  const alturas = lista(copa?.metricas?.onda_altura_m)
  if (!alturas.length) {
    return {
      ...base,
      ausencia: {
        titulo: 'Sem rodada do modelo marinho',
        texto: 'A última rodada do Open-Meteo Marine não trouxe altura de onda pra frente deste instante. A balneabilidade do INEA segue não integrada (o boletim é PDF), então também não há contagem de praias.',
      },
    }
  }

  const periodos = lista(copa.metricas.onda_periodo_s)
  const direcoes = lista(copa.metricas.onda_direcao_graus)
  const alturasBarra = lista(barra?.metricas?.onda_altura_m)
  const porTsBarra = new Map(alturasBarra.map((p) => [p.ts, p.valor]))
  const porTsPeriodo = new Map(periodos.map((p) => [p.ts, p.valor]))
  const porTsDirecao = new Map(direcoes.map((p) => [p.ts, p.valor]))

  const prox24 = alturas.slice(0, 24)
  const maxAltura = Math.max(...prox24.map((p) => p.valor))
  const horaMax = prox24.find((p) => p.valor === maxAltura)
  const agora = alturas[0]
  const teto = Math.max(2, maxAltura, ...alturasBarra.map((p) => p.valor)) + 0.3
  const estado = (h: number) => (h >= 2.5 ? 'mar agitado' : h >= 1.5 ? 'mar moderado' : 'mar calmo')

  return {
    ...base,
    ausencia: null,
    sev: maxAltura >= 2.5 ? SEV[3] : maxAltura >= 1.5 ? SEV[2] : SEV[1],
    kpis: [
      { l: 'Onda agora · Copacabana', v: nQuebrado(agora.valor), u: `m · ${estado(agora.valor)}`, c: agora.valor >= 2.5 ? 'var(--s3)' : 'var(--tx)', d: `período de ${Math.round(porTsPeriodo.get(agora.ts) ?? 0)} s, direção ${cardinal(porTsDirecao.get(agora.ts))}` },
      { l: 'Máxima em Copacabana · 24 h', v: nQuebrado(maxAltura), u: horaMax ? `m · ${hhmm(horaMax.ts)}` : 'm', c: maxAltura >= 2.5 ? 'var(--s3)' : 'var(--tx)', d: maxAltura >= 2.5 ? 'faixa de ressaca pra orla exposta' : 'sem ressaca prevista no período' },
      { l: 'Onda agora · Barra', v: alturasBarra.length ? nQuebrado(alturasBarra[0].valor) : '—', u: alturasBarra.length ? 'm' : 'sem ponto ativo', c: 'var(--tx)', d: 'o segundo ponto marinho que coletamos' },
      { l: 'Balneabilidade', v: '—', u: 'praias próprias', c: 'var(--tx3)', d: 'boletim do INEA é PDF; o parsing está pendente e não estimamos' },
    ],
    chartTitle: 'Altura de onda prevista · próximas 48 h',
    s1: 'Copacabana (m)',
    s2: alturasBarra.length ? 'Barra da Tijuca (m)' : '',
    series1: poly(alturas.map((p) => p.valor), 1000, 205, teto),
    series2: alturasBarra.length ? poly(alturasBarra.map((p) => p.valor), 1000, 205, teto) : '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: eixo(alturas, hhmm),
    tipTime: `${hhmm(agora.ts)} · COPACABANA`,
    tip1: `${nQuebrado(agora.valor)} m`,
    tip2: alturasBarra.length ? `${nQuebrado(alturasBarra[0].valor)} m na Barra` : '',
    ...posicaoTip(0, alturas.length, agora.valor, teto),
    cols: ['Hora', 'Copacabana', 'Barra', 'Período', 'Direção'],
    rows: prox24.map((p) => ({
      a: hhmm(p.ts),
      b: `${nQuebrado(p.valor)} m`,
      c: porTsBarra.has(p.ts) ? `${nQuebrado(porTsBarra.get(p.ts)!)} m` : '—',
      d: `${Math.round(porTsPeriodo.get(p.ts) ?? 0)} s`,
      e: cardinal(porTsDirecao.get(p.ts)),
      ec: p.valor >= 2.5 ? 'var(--s3)' : 'var(--tx2)',
    })),
    tableTitle: 'Previsão hora a hora · próximas 24 h',
    sortBy: 'HORA',
    mapTitle: 'Pontos marinhos',
    mapNota: 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO',
    mapDots: pontos
      .filter((p) => p.lat != null)
      .map((p) => ({ ...projetar(p.lat, p.lon), c: '#2c96c4', t: p.nome })),
    context: 'Onda é previsão do modelo marinho do Open-Meteo, não boia medindo no mar. A balneabilidade vem do boletim do INEA em PDF, que ainda não lemos — por isso não há contagem de praias aqui.',
    seal: copa.emitida_em ? `OPEN-METEO MARINE · RODADA DE ${hhmm(copa.emitida_em)}` : 'OPEN-METEO MARINE',
  }
}

// ---------------------------------------------------------------- CÉU

export function dossieCeu(base: any, ceu: any) {
  const aeronaves = lista(ceu.aeronaves)
  const serie = lista(ceu.serie_15min)
  const comAltitude = aeronaves.filter((a) => a.altitude_pes != null)
  const pico = serie.length ? Math.max(...serie.map((p) => p.aeronaves)) : null
  const picoQuando = serie.find((p) => p.aeronaves === pico)
  const limite = ceu.limite_altitude_baixa_pes ?? 5000

  const ordenadas = [...aeronaves].sort(
    (a, b) => (a.altitude_pes ?? 1e9) - (b.altitude_pes ?? 1e9),
  )

  return {
    ...base,
    ausencia: null,
    sev: SEV[1],
    kpis: [
      { l: 'Aeronaves agora', v: String(ceu.total ?? aeronaves.length), u: 'no raio de 40 MN', c: 'var(--tx)', d: `posição transmitida nos últimos ${ceu.minutos ?? 10} min` },
      { l: 'Em altitude baixa', v: String(ceu.em_altitude_baixa ?? 0), u: `abaixo de ${limite.toLocaleString('pt-BR')} pés`, c: 'var(--tx)', d: 'aproximação ou subida — a aeronave não diz qual' },
      { l: 'Pico nas últimas 24 h', v: pico != null ? String(pico) : '—', u: picoQuando ? `aeronaves · ${hhmm(picoQuando.ts)}` : 'sem série', c: 'var(--tx)', d: 'contagem por janela de 15 min' },
      { l: 'Pousos por hora', v: '—', u: 'SDU e GIG', c: 'var(--tx3)', d: 'sem plano de voo não dá pra afirmar pouso; não estimamos' },
    ],
    chartTitle: 'Aeronaves sobre a região · últimas 24 h',
    s1: 'aeronaves por janela de 15 min',
    s2: '',
    series1: serie.length >= 2 ? poly(serie.map((p) => p.aeronaves), 1000, 205, Math.max(...serie.map((p) => p.aeronaves))) : '',
    series2: '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: serie.length ? eixo(serie, hhmm) : [],
    tipTime: serie.length ? `${hhmm(serie.at(-1).ts)} · CÉU` : '',
    tip1: serie.length ? `${serie.at(-1).aeronaves} aeronaves` : '',
    tip2: '',
    ...(serie.length ? posicaoTip(serie.length - 1, serie.length, serie.at(-1).aeronaves, Math.max(...serie.map((p) => p.aeronaves))) : {}),
    notaGrafico: serie.length >= 2 ? '' : 'Série de 15 min ainda materializando — o agregado contínuo cobre as últimas horas.',
    cols: ['Voo', 'Altitude', 'Velocidade', 'Última msg', 'Situação'],
    rows: ordenadas.map((a) => ({
      a: a.voo || a.veiculo,
      b: a.altitude_pes != null ? `${a.altitude_pes.toLocaleString('pt-BR')} pés` : a.no_solo ? 'no solo' : '—',
      c: a.velocidade_kmh != null ? `${a.velocidade_kmh} km/h` : '—',
      d: hhmm(a.ts),
      e: a.no_solo ? 'no solo' : a.altitude_pes == null ? 'sem altitude' : a.altitude_pes < limite ? 'baixa altitude' : 'em rota',
      ec: a.altitude_pes != null && a.altitude_pes < limite ? 'var(--s2)' : 'var(--tx2)',
    })),
    tableTitle: `${aeronaves.length} aeronaves transmitindo agora`,
    sortBy: 'MENOR ALTITUDE',
    mapTitle: 'Aeronaves na região',
    mapNota: 'PROJEÇÃO SIMPLES · RAIO DE 40 MN',
    mapDots: aeronaves
      .filter((a) => a.lat != null)
      .map((a) => ({
        ...projetar(a.lat, a.lon, BBOX_REGIAO),
        c: a.altitude_pes != null && a.altitude_pes < limite ? 'var(--s2)' : '#2c96c4',
        t: `${a.voo || a.veiculo}${a.altitude_pes != null ? ` · ${a.altitude_pes} pés` : ''}`,
      })),
    context: aeronaves.length
      ? `ADS-B da rede comunitária adsb.lol, raio de 40 milhas náuticas do centro — ${comAltitude.length} de ${aeronaves.length} aeronaves transmitindo altitude agora. Sem plano de voo, não afirmamos pouso, decolagem nem destino.`
      : 'ADS-B da rede comunitária adsb.lol, raio de 40 milhas náuticas do centro. Nenhuma aeronave transmitindo neste instante — céu vazio de madrugada é normal, e a curva acima mostra o movimento do dia.',
    seal: 'ADSB.LOL · AO VIVO · LICENÇA ODBL',
  }
}

// ---------------------------------------------------------------- QUEIMADAS

export function dossieQueimadas(base: any, q: any, periodo: string) {
  const serie = lista(q.serie)
  const focos = lista(q.lista)
  const bairros = lista(q.por_bairro)
  const rotuloJanela = periodo === '24h' ? 'últimas 24 h' : periodo === '7d' ? 'últimos 7 dias' : 'últimos 30 dias'
  const porHora = q.passo === 'hour'

  return {
    ...base,
    ausencia: null,
    sev: q.focos > 10 ? SEV[3] : q.focos > 0 ? SEV[2] : SEV[1],
    kpis: [
      { l: `Focos · ${rotuloJanela}`, v: String(q.focos ?? 0), u: 'detecções de satélite', c: q.focos ? 'var(--s2)' : 'var(--s1)', d: 'foco não é incêndio confirmado' },
      { l: 'Bairros atingidos', v: String(q.bairros_atingidos ?? 0), u: 'com ao menos 1 foco', c: 'var(--tx)', d: bairros.length ? `mais atingido: ${bairros[0].nome} (${bairros[0].focos})` : 'nenhum foco no recorte' },
      { l: 'Detecção mais recente', v: q.ultimo ? hhmm(q.ultimo) : '—', u: q.ultimo ? ddmm(q.ultimo) : 'sem foco na janela', c: 'var(--tx)', d: q.ultimo ? idadeLegivel(q.ultimo) : 'o INPE publica a cada 10 min' },
      { l: 'Nossa série começa em', v: q.desde ? ddmm(q.desde) : '—', u: q.desde ? String(new Date(q.desde).getFullYear()) : 'sem histórico', c: 'var(--tx3)', d: 'memória curta: comparação com anos anteriores ainda não existe' },
    ],
    chartTitle: `Focos de calor · ${rotuloJanela}`,
    s1: porHora ? 'focos por hora' : 'focos por dia',
    s2: '',
    series1: serie.length >= 2 ? poly(serie.map((p) => p.focos), 1000, 205, Math.max(1, ...serie.map((p) => p.focos))) : '',
    series2: '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: serie.length ? eixo(serie, porHora ? hhmm : ddmm) : [],
    tipTime: serie.length ? `${porHora ? hhmm(serie.at(-1).ts) : ddmm(serie.at(-1).ts)} · FOCOS` : '',
    tip1: serie.length ? `${serie.at(-1).focos} focos` : '',
    tip2: '',
    ...(serie.length ? posicaoTip(serie.length - 1, serie.length, serie.at(-1).focos, Math.max(1, ...serie.map((p) => p.focos))) : {}),
    notaGrafico: serie.length >= 2 ? '' : q.focos ? 'Poucos focos no recorte pra desenhar uma curva — a tabela abaixo lista cada detecção.' : 'Nenhum foco detectado no recorte, então não há curva. A ausência aqui é o dado.',
    cols: ['Bairro', 'Quando', 'Satélite', 'Região administrativa', 'Idade'],
    rows: focos.map((f) => ({
      a: f.bairro ?? 'fora dos bairros mapeados',
      b: diaHora(f.inicio),
      c: f.satelite ?? '—',
      d: f.ra ?? '—',
      e: idadeLegivel(f.inicio),
      ec: 'var(--tx2)',
    })),
    tableTitle: focos.length ? `${focos.length} focos no recorte — mais recentes primeiro` : '',
    sortBy: focos.length ? 'MAIS RECENTE' : '',
    mapTitle: focos.length ? 'Focos no mapa' : '',
    mapNota: 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO',
    mapDots: focos
      .filter((f) => f.lat != null)
      .map((f) => ({ ...projetar(f.lat, f.lon), c: 'var(--s3)', t: `${f.bairro ?? 'sem bairro'} · ${diaHora(f.inicio)}` })),
    context: `Foco de calor é anomalia térmica vista por satélite, não incêndio confirmado. Guardamos só o que cai dentro dos bairros do município${q.desde ? `, desde ${ddmm(q.desde)}` : ''} — série curta demais pra comparar com anos anteriores.`,
    seal: 'INPE · CSV DE 10 EM 10 MIN',
  }
}

// ---------------------------------------------------------------- CIDADE VIVA

const TIPOS_AGENDA: Record<string, string> = { jogo: 'Jogo', agua: 'Águas do Rio' }

export function dossieCidade(base: any, eventos: any[]) {
  const agenda = eventos
    .filter((e) => e.tipo in TIPOS_AGENDA)
    .sort((a, b) => (a.inicio < b.inicio ? 1 : -1))
  const agora = Date.now()
  const futuros = agenda.filter((e) => new Date(e.inicio).getTime() > agora)
  const proximo = [...futuros].sort((a, b) => (a.inicio < b.inicio ? -1 : 1))[0]
  const jogos = futuros.filter((e) => e.tipo === 'jogo')
  const aguas = agenda.filter((e) => e.tipo === 'agua')
  const vigentes = agenda.filter((e) => !e.fim || new Date(e.fim).getTime() > agora)

  const situacao = (e: any) => {
    const inicio = new Date(e.inicio).getTime()
    const fim = e.fim ? new Date(e.fim).getTime() : null
    if (inicio > agora) return 'programado'
    if (fim == null || fim > agora) return 'acontecendo'
    return 'encerrado'
  }

  return {
    ...base,
    ausencia: null,
    sev: SEV[1],
    kpis: [
      { l: 'Na agenda', v: String(agenda.length), u: 'eventos no período', c: 'var(--tx)', d: 'jogos e comunicados de água — o que muda a rotina sem ser emergência' },
      { l: 'Jogos por vir', v: String(jogos.length), u: 'com estádio pinado', c: 'var(--tx)', d: proximo?.tipo === 'jogo' ? `próximo: ${diaHora(proximo.inicio)}` : 'pino do estádio resolvido na ingestão' },
      { l: 'Comunicados de água', v: String(aguas.length), u: 'da concessionária', c: aguas.length ? 'var(--s2)' : 'var(--tx)', d: 'manutenção e desabastecimento publicados pela Águas do Rio' },
      { l: 'Acontecendo agora', v: String(vigentes.filter((e) => new Date(e.inicio).getTime() <= agora).length), u: 'em curso', c: 'var(--tx)', d: 'evento sem hora de fim conta como em curso' },
    ],
    chartTitle: 'Agenda da cidade',
    s1: '', s2: '', series1: '', series2: '',
    annX: -10, annW: 0, annLeft: -20, annLabel: '',
    axis: [], tipTime: '', tip1: '', tip2: '',
    notaGrafico: 'Agenda não é série temporal: contar eventos por dia aqui não diria nada, porque as duas fontes publicam em ritmos completamente diferentes. A linha do tempo desta seção é a própria tabela.',
    cols: ['Evento', 'Quando', 'Bairro', 'Fonte', 'Situação'],
    rows: agenda.map((e) => ({
      a: e.titulo,
      b: diaHora(e.inicio),
      c: e.bairro ?? '—',
      d: TIPOS_AGENDA[e.tipo],
      e: situacao(e),
      ec: situacao(e) === 'acontecendo' ? 'var(--live-tx)' : 'var(--tx2)',
    })),
    tableTitle: agenda.length ? `${agenda.length} eventos — mais recentes primeiro` : '',
    sortBy: agenda.length ? 'DATA' : '',
    mapTitle: 'Onde acontece',
    mapNota: 'PROJEÇÃO SIMPLES · BBOX DO MUNICÍPIO',
    mapDots: agenda
      .filter((e) => e.lat != null)
      .map((e) => ({ ...projetar(e.lat, e.lon), c: e.tipo === 'jogo' ? 'var(--live-tx)' : 'var(--s2)', t: `${e.titulo} · ${diaHora(e.inicio)}` })),
    context: 'O que muda a rotina sem ser emergência: jogos (com o estádio pinado) e comunicados da Águas do Rio. Agenda cultural e obras não entram — não achamos fonte aberta viva pra elas, e a lacuna fica declarada.',
    seal: 'THESPORTSDB + ÁGUAS DO RIO',
  }
}

// ---------------------------------------------------------------- NAVIOS

export function dossieNavios(base: any) {
  return {
    ...base,
    sev: SEV[2],
    kpis: [],
    chartTitle: '', s1: '', s2: '', series1: '', series2: '', notaGrafico: '',
    axis: [], rows: [], cols: [], tableTitle: '', mapDots: [], mapTitle: '',
    ausencia: {
      titulo: 'Navios: nenhuma leitura — a fonte não está integrada',
      texto:
        'O AIS (posição de embarcação) depende do aisstream.io, que exige chave e ficou mudo nos testes de 5 e 6 de agosto. A integração não foi concluída, então não existe leitura nenhuma — nem antiga, nem parcial. Preferimos dizer isso a exibir uma contagem de navios que não medimos. Quando o AIS entrar, aparecem aqui as embarcações fundeadas, atracadas e em trânsito na Baía de Guanabara, com tipo e horário da última mensagem.',
    },
    context: '',
    seal: 'AISSTREAM · SEM INTEGRAÇÃO',
  }
}
