/* Sobrepõe dados reais da API ao modelo demo do handoff.

   Regra: só sobrepõe no modo calmo sem recorte de zona (os modos crise/zona são
   demonstrações visuais do protótipo). Painéis cuja fonte ainda não existe
   (segurança, trânsito, céu, mar, cidade viva) permanecem com o mock do design. */

import { useQuery } from '@tanstack/react-query'
import type { EstadoUi, Modelo } from './tipos'
import { SEV, poly } from './base'

const A_CADA_30S = { refetchInterval: 30_000, staleTime: 15_000, retry: 1 }

import { api } from '../api'

export function useDadosReais(ui: EstadoUi) {
  const ativo = ui.mode === 'calmo' && !ui.zone
  const agora = useQuery({ queryKey: ['agora'], queryFn: api.agora, enabled: ativo, ...A_CADA_30S })
  const fontes = useQuery({ queryKey: ['fontes'], queryFn: api.fontes, enabled: ativo, ...A_CADA_30S })
  const eventos = useQuery({ queryKey: ['eventos'], queryFn: () => api.eventos(24), enabled: ativo, ...A_CADA_30S })
  const previsao = useQuery({ queryKey: ['previsao'], queryFn: () => api.previsao('centro'), enabled: ativo, refetchInterval: 300_000, retry: 1 })
  const chuva1h = useQuery({ queryKey: ['chuva1h'], queryFn: () => api.serie('chuva_15min', '1h', 12), enabled: ativo, refetchInterval: 300_000, retry: 1 })

  // dossiê de chuva: série do período + tabela das 33 estações
  const noDossieChuva = ativo && ui.dossier === 'chuva'
  const passo = ui.period === '30d' ? '1d' : '1h'
  const horas = ui.period === '24h' ? 24 : ui.period === '7d' ? 168 : 720
  const serieDossie = useQuery({
    queryKey: ['serie-dossie-chuva', ui.period],
    queryFn: () => api.serie('chuva_1h', passo, horas),
    enabled: noDossieChuva, refetchInterval: 300_000, retry: 1,
  })
  const estacoesChuva = useQuery({
    queryKey: ['estacoes-chuva'],
    queryFn: () => fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/chuva/estacoes`).then((r) => r.json()),
    enabled: noDossieChuva, refetchInterval: 60_000, retry: 1,
  })

  const radarMapa = useQuery({
    queryKey: ['radar-mapa'],
    queryFn: () => fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/radar?quadros=12`).then((r) => r.json()),
    enabled: ativo && ui.route === 'mapa', refetchInterval: 120_000, retry: 1,
  })

  const mobilidade = useQuery({
    queryKey: ['mobilidade-linhas'],
    queryFn: () => fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/mobilidade/linhas`).then((r) => r.json()),
    enabled: ativo, refetchInterval: 60_000, retry: 1,
  })

  return { agora, fontes, eventos, previsao, chuva1h, serieDossie, estacoesChuva, mobilidade, radarMapa, ui, ativo }
}

const hhmm = (iso: string) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

export function aplicarDadosReais(m: Modelo, d: ReturnType<typeof useDadosReais>): Modelo {
  if (!d.ativo) return m
  const saida: Modelo = { ...m, aoVivo: false }

  const ag = d.agora.data
  if (ag) {
    saida.aoVivo = true
    if (ag.estagio) {
      saida.sev = SEV[ag.estagio.severidade] ?? m.sev
      if (ag.estagio.severidade === 1)
        saida.headline = 'A cidade opera normalmente. Sem chuva na última hora.'
      else saida.headline = `${ag.estagio.titulo} em vigor desde ${hhmm(ag.estagio.inicio)}.`
    }
    const va = ag.veiculos_ativos ?? {}
    const onibus = va.onibus ?? 0
    const brt = va.brt ?? 0
    if (onibus + brt > 0) {
      saida.mob = {
        ...m.mob,
        hero: (onibus + brt).toLocaleString('pt-BR'),
        sub: `${onibus.toLocaleString('pt-BR')} ônibus + ${brt.toLocaleString('pt-BR')} BRT · ao vivo`,
      }
    }
    const cont = ag.snapshot?.contadores ?? {}
    if (cont.chuva) {
      const max15 = cont.chuva.max_15min ?? 0
      saida.chuva = {
        ...m.chuva,
        hero: String(max15).replace('.', ','),
        sub: max15 > 0 ? 'máxima entre as 33 estações · últimos 15 min' : 'na última hora · todas as estações reportando',
      }
      if (cont.nivel_rios_max_cm != null)
        saida.chuva.rios = `Rios: máx ${cont.nivel_rios_max_cm} cm — monitorando 4 estações`
    }
    if (cont.pm25_max != null)
      saida.ar = { ...m.ar, heroSub: `PM2.5 máx ${String(cont.pm25_max).replace('.', ',')} µg/m³` }
    if (cont.eventos_abertos?.foco_calor != null)
      saida.queimadasHero = String(cont.eventos_abertos.foco_calor)
  }

  if (d.chuva1h.data?.pontos?.length) {
    const porHora = new Map<string, number>()
    for (const p of d.chuva1h.data.pontos) {
      const chave = p.ts
      porHora.set(chave, Math.max(porHora.get(chave) ?? 0, p.maximo ?? 0))
    }
    const valores = [...porHora.values()].slice(-12)
    if (valores.length >= 2)
      saida.chuva = { ...saida.chuva, spark: poly(valores, 220, 34, Math.max(10, ...valores)) }
  }

  if (d.previsao.data?.metricas?.temp_c?.length) {
    const met = d.previsao.data.metricas
    const horas = (met.temp_c as any[]).slice(0, 12).map((p, i) => {
      const t = new Date(p.ts)
      const temp = Math.round(p.valor)
      const chuvaMm = met.precipitacao_mm?.[i]?.valor ?? 0
      return {
        t: String(t.getHours()).padStart(2, '0'),
        h: `${temp}°`,
        bar: Math.round((temp - 14) * 2.2),
        rain: Math.max(2, Math.round(chuvaMm * 6)),
      }
    })
    const agoraTemp = Math.round(met.temp_c[0].valor)
    saida.previsao = { ...m.previsao, hours: horas, hero: `${agoraTemp} °C` }
  }

  if (d.eventos.data?.length && d.fontes.data) {
    const nomesFonte = new Map<number, string>()
    // /eventos traz fonte_id? não — mapeia por tipo conhecido
    const rotulo: Record<string, string> = {
      estagio_cor: 'COR', foco_calor: 'INPE', linha_parada: 'SMTR',
    }
    saida.feedReal = true
    const feed = d.eventos.data.slice(0, 12).map((e: any) => ({
      h: hhmm(e.inicio),
      sev: SEV[Math.min(5, Math.max(1, e.severidade))],
      txt: e.titulo + (e.fim ? '' : ' — vigente'),
      src: rotulo[e.tipo] ?? e.tipo,
    }))
    if (feed.length) saida.feed = m.dossier ? saida.feed : feed
    saida.feedCount = `${d.eventos.data.length} EVENTOS · 24H`
    void nomesFonte
  }

  if (d.fontes.data?.length) {
    const porEstado: Record<string, number> = {}
    for (const f of d.fontes.data) porEstado[f.estado] = (porEstado[f.estado] ?? 0) + 1
    const online = porEstado.online ?? 0
    const total = d.fontes.data.length
    saida.rodapeFontes = `${online} DE ${total} FONTES OPERANDO NORMALMENTE`
    saida.sources = d.fontes.data.map((f: any) => {
      const deg = f.estado !== 'online'
      return {
        n: f.nome, org: f.orgao,
        state: f.estado === 'online' ? 'Online' : f.estado.charAt(0).toUpperCase() + f.estado.slice(1),
        i: deg ? '◆' : '●', c: deg ? 'var(--s2)' : 'var(--s1)',
        age: f.desde ? `desde ${hhmm(f.desde)}` : '—',
        agec: deg ? 'var(--s2)' : 'var(--tx2)',
        up: f.uptime_pct != null ? `${String(f.uptime_pct).replace('.', ',')}%` : '—',
        bars: (f.dias ?? Array(30).fill(null)).map((dia: string | null) =>
          dia === 'online' ? 'var(--up-ok)'
          : dia === 'degradada' ? 'var(--s2)'
          : dia === 'congelada' ? 'var(--s3)'
          : dia === 'fora' ? 'var(--s4)'
          : 'var(--bd2)'),  // sem dado: neutro, não verde
      }
    })
  }

  // cartão Mobilidade: planejado × realizado real
  const mo = d.mobilidade.data
  if (mo) {
    const paradas: any[] = mo.linhas_paradas ?? []
    const warn = !mo.gps_saudavel
      ? 'GPS da frota fora do ar — detector de linha parada em espera'
      : paradas.length
        ? `${paradas.length} linha${paradas.length > 1 ? 's' : ''} sem circular há 40+ min: ${paradas.slice(0, 3).map((p) => p.linha).join(', ')}${paradas.length > 3 ? '…' : ''}`
        : 'Nenhuma linha planejada sem circular agora'
    saida.mob = {
      ...saida.mob,
      warn,
      warnBg: !mo.gps_saudavel ? 'var(--s2-bg)' : paradas.length ? 'var(--s3-bg)' : 'var(--ok-bg)',
      warnBd: !mo.gps_saudavel ? 'var(--warn-bd)' : paradas.length ? 'var(--s3-bd)' : 'var(--ok-bd)',
      warnC: !mo.gps_saudavel ? 'var(--warn-tx)' : paradas.length ? 'var(--s3-tx)' : 'var(--s1)',
      count: `${mo.linhas_planejadas_agora} LINHAS`,
    }
    if (mo.pct_ativas != null && saida.mob.sub?.includes('ao vivo'))
      saida.mob.sub = `${saida.mob.sub} · ${mo.pct_ativas}% das linhas planejadas ativas`
  }

  // dossiê de Mobilidade real
  if (d.ui.dossier === 'mobilidade' && saida.dossier && mo) {
    const paradas: any[] = mo.linhas_paradas ?? []
    const linhas: any[] = mo.linhas ?? []
    const serie: any[] = mo.serie_veiculos_15min ?? []
    const dossie: any = { ...saida.dossier, title: 'Mobilidade', route: '/mobilidade' }
    dossie.sev = !mo.gps_saudavel ? SEV[2] : paradas.length > 5 ? SEV[3] : SEV[1]
    dossie.kpis = [
      { l: 'Linhas planejadas agora', v: String(mo.linhas_planejadas_agora ?? '—'), u: 'com frequência no GTFS', c: 'var(--tx)', d: 'calendário e janelas vigentes neste instante' },
      { l: 'Linhas ativas', v: String(mo.linhas_ativas ?? '—'), u: mo.pct_ativas != null ? `${mo.pct_ativas}% do planejado` : '', c: mo.pct_ativas >= 80 ? 'var(--s1)' : 'var(--s2)', d: 'com veículo transmitindo nos últimos 15 min' },
      { l: 'Linhas paradas (40+ min)', v: mo.gps_saudavel ? String(paradas.length) : '—', u: mo.gps_saudavel ? 'detector ativo' : 'detector em espera', c: paradas.length ? 'var(--s3)' : 'var(--s1)', d: mo.gps_saudavel ? 'planejadas agora, sem nenhum GPS' : 'GPS da frota fora do ar' },
      { l: 'Veículos no último bucket', v: serie.length ? String(serie.at(-1).veiculos) : '—', u: 'janela de 15 min', c: 'var(--tx)', d: 'agregado contínuo frota_veiculo_15min' },
    ]
    if (serie.length >= 2) {
      const valores = serie.map((p) => p.veiculos)
      dossie.series1 = poly(valores, 1000, 205, Math.max(...valores))
      dossie.series2 = ''
      dossie.s1 = 'veículos ativos por 15 min (ônibus + BRT)'
      dossie.s2 = 'planejado por faixa horária · em breve'
      dossie.annW = 0; dossie.annX = -10; dossie.annLabel = ''
      dossie.chartTitle = 'Frota ativa · últimas 24 h'
      const passoN = Math.max(1, Math.floor(serie.length / 8))
      dossie.axis = serie.filter((_: any, i: number) => i % passoN === 0).slice(0, 8).map((p) => hhmm(p.ts))
      const ult = serie.at(-1)
      dossie.tipTime = `${hhmm(ult.ts)} · FROTA`
      dossie.tip1 = `${ult.veiculos} veículos`
      dossie.tip2 = ''
    }
    const piores = [...linhas].slice(0, 40)
    dossie.rows = piores.map((li) => ({
      a: `${li.linha}`,
      b: `${li.headway_min} min`,
      c: String(li.veiculos),
      d: li.minutos_sem_gps == null ? 'sem GPS hoje' : li.minutos_sem_gps <= 15 ? 'agora' : `há ${li.minutos_sem_gps} min`,
      e: li.veiculos > 0 ? 'circulando' : mo.gps_saudavel && li.minutos_sem_gps != null && li.minutos_sem_gps >= 40 ? 'PARADA' : 'sem sinal',
      ec: li.veiculos > 0 ? 'var(--tx2)' : 'var(--s3)',
    }))
    dossie.cols = ['Linha', 'Freq. plan.', 'Veículos', 'Último GPS', 'Situação']
    dossie.tableTitle = `${linhas.length} linhas planejadas pra agora — piores primeiro`
    dossie.sortBy = 'MENOS VEÍCULOS'
    dossie.mapTitle = 'Frota no mapa'
    dossie.mapDots = []
    dossie.context = mo.gps_saudavel
      ? `${mo.linhas_ativas} de ${mo.linhas_planejadas_agora} linhas planejadas estão circulando (${mo.pct_ativas}%). O detector abre um evento por linha sem GPS há 40+ min e fecha quando ela volta.`
      : 'O GPS da frota está fora do ar — sem leitura confiável, o detector fica em espera pra não gerar falsos positivos em massa. O planejado (GTFS) segue exibido.'
    dossie.seal = 'SMTR (GPS) + GTFS · DETECTOR A CADA 5 MIN'
    saida.dossier = dossie
  }

  // ticker composto de leituras reais (substitui o mock quando a API responde)
  if (ag) {
    const cont = ag.snapshot?.contadores ?? {}
    const va = ag.veiculos_ativos ?? {}
    const tempAgora = d.previsao.data?.metricas?.temp_c?.[0]?.valor
    const itens: any[] = []
    const põe = (k: string, v: string, d_ = '▬', dc = 'var(--tx2)') => itens.push({ k, v, d: d_, dc })
    if (ag.estagio) põe('ESTÁGIO', String(ag.estagio.severidade), '▬', 'var(--s1)')
    if (va.onibus || va.brt) põe('VEÍCULOS', ((va.onibus ?? 0) + (va.brt ?? 0)).toLocaleString('pt-BR'), '▲', 'var(--s1)')
    if (cont.chuva) põe('CHUVA MÁX 15MIN', `${String(cont.chuva.max_15min ?? 0).replace('.', ',')}mm`)
    if (cont.nivel_rios_max_cm != null) põe('RIO MÁX', `${cont.nivel_rios_max_cm}cm`)
    if (cont.pm25_max != null) põe('PM2.5 MÁX', String(cont.pm25_max).replace('.', ','))
    if (tempAgora != null) põe('TEMP CENTRO', `${String(Math.round(tempAgora * 10) / 10).replace('.', ',')}°C`)
    if (cont.eventos_abertos) põe('EVENTOS ABERTOS', String(Object.values(cont.eventos_abertos as Record<string, number>).reduce((a, b) => a + b, 0)))
    if (cont.fontes) põe('FONTES ONLINE', `${cont.fontes.online ?? 0}/${Object.values(cont.fontes as Record<string, number>).reduce((a, b) => a + b, 0)}`)
    if (itens.length >= 5) saida.tickerLoop = itens.concat(itens)
  }

  // painel queimadas real (contagem de focos abertos dentro do município)
  const focosAbertos = ag?.snapshot?.contadores?.eventos_abertos?.foco_calor
  if (focosAbertos != null) {
    saida.queimadasHero = String(focosAbertos)
    saida.queimadasSub = focosAbertos > 0 ? 'focos ativos no município agora' : 'focos no município · 3 h'
  }

  // dossiê de chuva com dados reais
  if (d.ui.dossier === 'chuva' && saida.dossier && (d.serieDossie.data || d.estacoesChuva.data)) {
    const dossie = { ...saida.dossier }
    const pontos: any[] = d.serieDossie.data?.pontos ?? []
    if (pontos.length >= 2) {
      const porBucket = new Map<string, number>()
      for (const p of pontos) porBucket.set(p.ts, Math.max(porBucket.get(p.ts) ?? 0, p.maximo ?? p.media ?? 0))
      const ordenado = [...porBucket.entries()].sort(([a], [b]) => (a < b ? -1 : 1))
      const valores = ordenado.map(([, v]) => v)
      const maxV = Math.max(5, ...valores)
      dossie.series1 = poly(valores, 1000, 205, maxV)
      dossie.series2 = ''  // média histórica entra com o backfill (série 1997–2025)
      dossie.s1 = 'chuva observada — máx entre as 33 estações (mm/h)'
      dossie.s2 = 'média histórica · disponível após o backfill'
      dossie.annW = 0; dossie.annX = -10; dossie.annLabel = ''
      const passoN = Math.max(1, Math.floor(ordenado.length / 8))
      dossie.axis = ordenado.filter((_, i) => i % passoN === 0).slice(0, 8).map(([ts]) => hhmm(ts))
      const ultimo = ordenado.at(-1)!
      dossie.tipTime = `${hhmm(ultimo[0])} · MÁX DAS 33`
      dossie.tip1 = `${String(Math.round(ultimo[1] * 10) / 10).replace('.', ',')} mm`
      dossie.tip2 = 'histórico após o backfill'
      const soma = valores.reduce((a, b) => a + b, 0)
      dossie.chartTitle = `Chuva por hora · ${d.ui.period === '24h' ? 'últimas 24 h' : d.ui.period === '7d' ? 'últimos 7 dias' : 'últimos 30 dias'}`
      dossie.context = `Acumulado do período (máx horária somada): ${String(Math.round(soma * 10) / 10).replace('.', ',')} mm. Comparação com a média histórica 1997–2025 entra com o backfill.`
    }
    const estacoes: any[] = d.estacoesChuva.data ?? []
    if (estacoes.length) {
      dossie.rows = estacoes.map((e) => ({
        a: e.nome,
        b: String(e.leituras?.chuva_1h ?? '—').replace('.', ','),
        c: String(e.leituras?.chuva_24h ?? '—').replace('.', ','),
        d: e.bairro ?? '—',
        e: (e.leituras?.chuva_15min ?? 0) > 0 ? 'chovendo' : 'normal',
        ec: (e.leituras?.chuva_15min ?? 0) > 0 ? 'var(--s3)' : 'var(--tx2)',
      }))
      dossie.cols = ['Estação', 'mm 1 h', 'mm 24 h', 'Bairro', 'Situação']
      dossie.tableTitle = `${estacoes.length} estações pluviométricas`
      // mapa: projeção linear das estações no box (bbox do município)
      const latN = -22.74, latS = -23.11, lonW = -43.80, lonE = -43.09
      dossie.mapDots = estacoes.map((e) => ({
        x: (((e.lon - lonW) / (lonE - lonW)) * 86 + 6).toFixed(0),
        y: (((latN - e.lat) / (latN - latS)) * 78 + 10).toFixed(0),
        c: (e.leituras?.chuva_15min ?? 0) > 0 ? '#1d7cab' : '#2c96c4',
      }))
      const maisNovo = estacoes.map((e) => e.ts).filter(Boolean).sort().at(-1)
      if (maisNovo) {
        const idadeMin = Math.max(0, Math.round((Date.now() - new Date(maisNovo).getTime()) / 60000))
        dossie.seal = `ALERTA RIO · 33 ESTAÇÕES · HÁ ${idadeMin} MIN`
      }
      const kpiUltimaHora = Math.max(...estacoes.map((e) => e.leituras?.chuva_1h ?? 0))
      const reportando = estacoes.filter((e) => e.ts).length
      dossie.kpis = [
        { l: 'Máx na última hora', v: String(kpiUltimaHora).replace('.', ','), u: 'mm (entre as 33)', c: 'var(--tx)', d: kpiUltimaHora > 0 ? 'chuva em curso' : 'nenhuma estação com registro' },
        { l: 'Estações reportando', v: `${reportando}`, u: 'de 33', c: reportando === 33 ? 'var(--s1)' : 'var(--s2)', d: 'última leitura em até 3 h' },
        { l: 'Rio mais alto agora', v: String(ag?.snapshot?.contadores?.nivel_rios_max_cm ?? '—'), u: 'cm', c: 'var(--tx)', d: '4 estações fluviométricas (ANA)' },
        { l: 'Memória histórica', v: '1997+', u: 'após o backfill', c: 'var(--tx3)', d: 'percentis e comparações entram com a série do datario' },
      ]
    }
    saida.dossier = dossie
  }

  // timeline do mapa: quadros reais do radar (o mais novo em ciano)
  const quadros: any[] = d.radarMapa.data?.quadros ?? []
  if (quadros.length >= 2) {
    saida.frames = quadros.map((q, i) => ({
      h: 8 + Math.round((i / (quadros.length - 1)) * 8),
      c: i === quadros.length - 1 ? 'var(--live-tx)' : 'var(--bd4)',
    }))
  }

  // mobileList é derivada dos painéis no modelo base — re-deriva com os valores reais
  if (Array.isArray(saida.mobileList)) {
    saida.mobileList = saida.mobileList.map((cartao: any) => {
      if (cartao.t === 'Chuva e água' && saida.chuva)
        return { ...cartao, v: saida.chuva.hero, sub: saida.chuva.sub }
      if (cartao.t === 'Mobilidade' && saida.mob)
        return { ...cartao, v: saida.mob.hero, sub: saida.mob.sub }
      if (cartao.t === 'Previsão' && saida.previsao)
        return { ...cartao, v: saida.previsao.hero }
      if (cartao.t === 'Qualidade do ar' && saida.ar)
        return { ...cartao, u: saida.ar.heroSub }
      return cartao
    })
  }

  return saida
}
