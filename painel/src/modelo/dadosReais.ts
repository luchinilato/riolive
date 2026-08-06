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
  return { agora, fontes, eventos, previsao, chuva1h, ativo }
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
        up: '—', bars: Array(30).fill(deg ? 'var(--s2)' : 'var(--up-ok)'),
      }
    })
  }

  return saida
}
