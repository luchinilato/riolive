/* Mapa real: MapLibre + basemap Protomaps (PMTiles no R2; cópia local em dev)
   com camadas vivas da API. Cada camada da lateral liga uma consulta e uma layer
   do MapLibre — e só busca quando ligada, pra não puxar 500 eventos à toa. */

import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Protocol } from 'pmtiles'
import { layers as camadasBase, namedFlavor } from '@protomaps/basemaps'
import { useQuery } from '@tanstack/react-query'
import type { FeatureCollection, Point } from 'geojson'

const URL_PMTILES = new URL(
  import.meta.env.VITE_PMTILES_URL ?? '/rio.pmtiles',
  window.location.origin,
).href  // o protocolo pmtiles exige URL absoluta

let protocoloRegistrado = false
function garantirProtocolo() {
  if (!protocoloRegistrado) {
    const protocolo = new Protocol()
    maplibregl.addProtocol('pmtiles', protocolo.tile)
    protocoloRegistrado = true
  }
}

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
const buscar = (caminho: string) => fetch(`${BASE}${caminho}`).then((r) => r.json())

/* Cada camada de ponto: cor, raio e como o popover se lê. Ter isso numa tabela
   evita repetir addLayer cinco vezes com detalhes divergindo em silêncio. */
const PONTOS = [
  { k: 'tiroteios', cor: '#cd4048', raio: [9, 3, 14, 7] },
  { k: 'focos', cor: '#e07b39', raio: [9, 2.5, 14, 6] },
  { k: 'chuva_estacoes', cor: '#149cc6', raio: [9, 3, 14, 6] },
  { k: 'rios', cor: '#57b7dc', raio: [9, 3.5, 14, 7] },
  { k: 'ar', cor: '#8e7cc3', raio: [9, 3, 14, 6] },
] as const

const VAZIO: FeatureCollection = { type: 'FeatureCollection', features: [] }

const quando = (iso: string) => {
  const minutos = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (minutos < 1) return 'agora'
  if (minutos < 60) return `há ${minutos} min`
  const horas = Math.round(minutos / 60)
  return horas < 24 ? `há ${horas} h` : `há ${Math.round(horas / 24)} d`
}

/* /eventos devolve lista com lat/lon soltos; o mapa quer GeoJSON. Evento sem
   pino é descartado: ponto em (0,0) cairia no Atlântico. */
function eventosParaGeoJson(eventos: any[]): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: (eventos ?? [])
      .filter((e) => e.lat != null && e.lon != null)
      .map((e) => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [e.lon, e.lat] },
        properties: {
          titulo: e.titulo,
          detalhe: e.descricao ?? '',
          quando: `${e.tipo.toUpperCase()} · ${quando(e.inicio)}`,
        },
      })),
  }
}

/* /locais já vem GeoJSON — só reescreve as propriedades pro formato do popover. */
function locaisParaGeoJson(colecao: any): FeatureCollection {
  return {
    type: 'FeatureCollection',
    features: (colecao?.features ?? []).map((f: any) => ({
      ...f,
      properties: {
        titulo: f.properties?.nome ?? 'Estação',
        detalhe: f.properties?.bairro ? `Bairro: ${f.properties.bairro}` : '',
        quando: f.properties?.tipo ? String(f.properties.tipo).toUpperCase() : '',
      },
    })),
  }
}

export function MapaReal({ camadas }: { camadas: string[] }) {
  const alvo = useRef<HTMLDivElement>(null)
  const mapa = useRef<maplibregl.Map | null>(null)
  const pronto = useRef(false)
  const ligada = (k: string) => camadas?.includes(k) ?? false

  const posicoes = useQuery({
    queryKey: ['posicoes-mapa'],
    queryFn: () => buscar('/posicoes?minutos=5'),
    refetchInterval: 30_000,
    retry: 1,
    enabled: ligada('frota'),
  })
  const aeronaves = useQuery({
    queryKey: ['aeronaves-mapa'],
    queryFn: () => buscar('/posicoes?modal=aviao&minutos=15'),
    refetchInterval: 30_000, retry: 1, enabled: ligada('aeronaves'),
  })
  const tiroteios = useQuery({
    queryKey: ['tiroteios-mapa'],
    queryFn: () => buscar('/eventos?tipo=tiroteio&horas=24&limite=500'),
    refetchInterval: 120_000, retry: 1, enabled: ligada('tiroteios'),
  })
  const focos = useQuery({
    queryKey: ['focos-mapa'],
    queryFn: () => buscar('/eventos?tipo=foco_calor&horas=24&limite=500'),
    refetchInterval: 300_000, retry: 1, enabled: ligada('focos'),
  })
  const estacoesChuva = useQuery({
    queryKey: ['locais-chuva-mapa'],
    queryFn: () => buscar('/locais?fonte=alerta_rio'),
    refetchInterval: 600_000, retry: 1, enabled: ligada('chuva_estacoes'),
  })
  const estacoesRios = useQuery({
    queryKey: ['locais-rios-mapa'],
    queryFn: () => buscar('/locais?fonte=rios_ana'),
    refetchInterval: 600_000, retry: 1, enabled: ligada('rios'),
  })
  const estacoesAr = useQuery({
    queryKey: ['locais-ar-mapa'],
    queryFn: () => buscar('/locais?fonte=openaq'),
    refetchInterval: 600_000, retry: 1, enabled: ligada('ar'),
  })
  const radar = useQuery({ queryKey: ['radar-mapa'], queryFn: () => buscar('/radar?quadros=12'), refetchInterval: 120_000, retry: 1, enabled: ligada('radar') })

  useEffect(() => {
    if (!alvo.current || mapa.current) return
    garantirProtocolo()
    const estilo: maplibregl.StyleSpecification = {
      version: 8,
      glyphs: 'https://protomaps.github.io/basemaps-assets/fonts/{fontstack}/{range}.pbf',
      sprite: 'https://protomaps.github.io/basemaps-assets/sprites/v4/dark',
      sources: {
        protomaps: {
          type: 'vector',
          url: `pmtiles://${URL_PMTILES}`,
          attribution: '© OpenStreetMap · Protomaps',
        },
      },
      layers: camadasBase('protomaps', namedFlavor('dark'), { lang: 'pt' }),
    }
    const m = new maplibregl.Map({
      container: alvo.current,
      style: estilo,
      center: [-43.28, -22.91],
      zoom: 10.6,
      minZoom: 8.5,
      maxZoom: 16,
      attributionControl: { compact: true },
    })
    m.on('error', (e: any) => console.log('[maplibre]', e?.error?.message ?? e))
    m.on('load', () => {
      m.addSource('frota', { type: 'geojson', data: VAZIO })
      m.addLayer({
        id: 'frota',
        type: 'circle',
        source: 'frota',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 1.6, 13, 4],
          'circle-color': ['match', ['get', 'modal'], 'brt', '#00C0F3', '#149cc6'],
          'circle-opacity': 0.85,
        },
      })
      m.addSource('aeronaves', { type: 'geojson', data: VAZIO })
      m.addLayer({
        id: 'aeronaves',
        type: 'circle',
        source: 'aeronaves',
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['zoom'], 9, 2.2, 14, 5],
          'circle-color': '#b9c4cc',
          'circle-opacity': 0.9,
        },
      })
      for (const p of PONTOS) {
        m.addSource(p.k, { type: 'geojson', data: VAZIO })
        m.addLayer({
          id: p.k,
          type: 'circle',
          source: p.k,
          paint: {
            'circle-radius': [
              'interpolate', ['linear'], ['zoom'],
              p.raio[0], p.raio[1], p.raio[2], p.raio[3],
            ],
            'circle-color': p.cor,
            'circle-opacity': 0.85,
            'circle-stroke-width': 1,
            'circle-stroke-color': 'rgba(0,0,0,.45)',
          },
        })
        // popover: o pino sozinho não conta a história, e o produto é sobre a história
        m.on('click', p.k, (evento) => {
          const f = evento.features?.[0]
          if (!f) return
          const props = f.properties ?? {}
          const geo = f.geometry as Point
          new maplibregl.Popup({ closeButton: true, maxWidth: '280px' })
            .setLngLat(geo.coordinates as [number, number])
            .setHTML(
              `<div style="font:12px Inter,system-ui,sans-serif;color:#111">
                 <strong>${props.titulo ?? p.k}</strong>
                 ${props.detalhe ? `<div style="margin-top:4px;color:#444">${props.detalhe}</div>` : ''}
                 ${props.quando ? `<div style="margin-top:6px;font:10px 'JetBrains Mono',monospace;color:#666">${props.quando}</div>` : ''}
               </div>`,
            )
            .addTo(m)
        })
        m.on('mouseenter', p.k, () => { m.getCanvas().style.cursor = 'pointer' })
        m.on('mouseleave', p.k, () => { m.getCanvas().style.cursor = '' })
      }
      pronto.current = true
    })
    mapa.current = m
    ;(window as any).__mapa = m
    return () => {
      m.remove()
      mapa.current = null
      pronto.current = false
    }
  }, [])

  // frota ao vivo
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current || !posicoes.data) return
    const fonte = m.getSource('frota') as maplibregl.GeoJSONSource | undefined
    fonte?.setData(posicoes.data)
  }, [posicoes.data, posicoes.dataUpdatedAt])

  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current || !aeronaves.data) return
    ;(m.getSource('aeronaves') as maplibregl.GeoJSONSource | undefined)?.setData(aeronaves.data)
  }, [aeronaves.data, aeronaves.dataUpdatedAt])

  // eventos e estações viram os pontos temáticos
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current) return
    const definir = (k: string, dados: FeatureCollection) =>
      (m.getSource(k) as maplibregl.GeoJSONSource | undefined)?.setData(dados)
    if (tiroteios.data) definir('tiroteios', eventosParaGeoJson(tiroteios.data))
    if (focos.data) definir('focos', eventosParaGeoJson(focos.data))
    if (estacoesChuva.data) definir('chuva_estacoes', locaisParaGeoJson(estacoesChuva.data))
    if (estacoesRios.data) definir('rios', locaisParaGeoJson(estacoesRios.data))
    if (estacoesAr.data) definir('ar', locaisParaGeoJson(estacoesAr.data))
  }, [
    tiroteios.dataUpdatedAt, focos.dataUpdatedAt, estacoesChuva.dataUpdatedAt,
    estacoesRios.dataUpdatedAt, estacoesAr.dataUpdatedAt,
  ])

  // liga/desliga: o checkbox da lateral tem que mexer no mapa, senão é enfeite
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current) return
    for (const id of ['frota', 'aeronaves', ...PONTOS.map((p) => p.k)]) {
      if (m.getLayer(id)) {
        m.setLayoutProperty(id, 'visibility', ligada(id) ? 'visible' : 'none')
      }
    }
  }, [camadas, posicoes.dataUpdatedAt])

  const [quadroIdx, setQuadroIdx] = useState(0)
  useEffect(() => {
    const quadros = radar.data?.quadros ?? []
    if (!ligada('radar') || quadros.length < 2) return
    const id = setInterval(() => setQuadroIdx((i) => (i + 1) % quadros.length), 700)
    return () => clearInterval(id)
  }, [camadas, radar.data])

  // radar: animação dos últimos quadros, só no recorte de chuva
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current) return
    const mostrar = ligada('radar')
    const quadros = radar.data?.quadros ?? []
    const quadro = quadros[quadroIdx % Math.max(1, quadros.length)] ?? quadros.at(-1)
    const bounds = radar.data?.bounds
    const existente = m.getSource('radar') as maplibregl.ImageSource | undefined
    if (!mostrar || !quadro?.url || !bounds) {
      if (m.getLayer('radar')) m.removeLayer('radar')
      if (existente) m.removeSource('radar')
      return
    }
    const [latS, lonW] = bounds.sw
    const [latN, lonE] = bounds.ne
    const cantos: [[number, number], [number, number], [number, number], [number, number]] = [
      [lonW, latN], [lonE, latN], [lonE, latS], [lonW, latS],
    ]
    if (existente) {
      existente.updateImage({ url: quadro.url, coordinates: cantos })
    } else {
      m.addSource('radar', { type: 'image', url: quadro.url, coordinates: cantos })
      m.addLayer({ id: 'radar', type: 'raster', source: 'radar', paint: { 'raster-opacity': 0.75 } })
    }
  }, [camadas, radar.data, radar.dataUpdatedAt, quadroIdx])

  const nFrota = posicoes.data?.features?.length ?? 0
  const nTiros = (tiroteios.data ?? []).filter((e: any) => e.lat != null).length
  const nFocos = (focos.data ?? []).filter((e: any) => e.lat != null).length

  return (
    <>
      <div ref={alvo} style={{ position: 'absolute', inset: 0 }} />
      <div style={{ position: 'absolute', left: '12px', bottom: '12px', display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 10px', borderRadius: '6px', background: 'var(--scrim)', border: '1px solid var(--bd)', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx2)', pointerEvents: 'none' }}>
        {ligada('frota') && <span><span style={{ color: '#149cc6' }}>●</span> FROTA AO VIVO {nFrota.toLocaleString('pt-BR')}</span>}
        {ligada('tiroteios') && <span><span style={{ color: '#cd4048' }}>●</span> TIROS 24H {nTiros}</span>}
        {ligada('focos') && <span><span style={{ color: '#e07b39' }}>●</span> FOCOS {nFocos}</span>}
        {ligada('radar') && <span><span style={{ color: '#57b7dc' }}>▦</span> RADAR · ANIMANDO {String((radar.data?.quadros ?? []).length)} QUADROS</span>}
        <span style={{ color: 'var(--tx3)' }}>BASEMAP PROTOMAPS · R2</span>
      </div>
    </>
  )
}
