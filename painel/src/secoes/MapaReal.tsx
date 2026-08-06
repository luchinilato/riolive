/* Mapa real: MapLibre + basemap Protomaps (PMTiles no R2; cópia local em dev)
   com camadas vivas da API — frota (/posicoes) e radar (/radar). */

import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { Protocol } from 'pmtiles'
import { layers as camadasBase, namedFlavor } from '@protomaps/basemaps'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api'

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

export function MapaReal({ preset }: { preset: string }) {
  const alvo = useRef<HTMLDivElement>(null)
  const mapa = useRef<maplibregl.Map | null>(null)
  const pronto = useRef(false)

  const posicoes = useQuery({
    queryKey: ['posicoes-mapa'],
    queryFn: () => fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/posicoes?minutos=5`).then((r) => r.json()),
    refetchInterval: 30_000,
    retry: 1,
  })
  const radar = useQuery({ queryKey: ['radar-mapa'], queryFn: () => fetch(`${import.meta.env.VITE_API_URL ?? 'http://localhost:8000'}/radar?quadros=1`).then((r) => r.json()), refetchInterval: 120_000, retry: 1 })

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
      m.addSource('frota', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } })
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

  // radar: quadro mais novo como overlay, só no recorte de chuva
  useEffect(() => {
    const m = mapa.current
    if (!m || !pronto.current) return
    const mostrar = preset === 'chuva'
    const quadro = radar.data?.quadros?.at(-1)
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
  }, [preset, radar.data, radar.dataUpdatedAt])

  const nFrota = posicoes.data?.features?.length ?? 0

  return (
    <>
      <div ref={alvo} style={{ position: 'absolute', inset: 0 }} />
      <div style={{ position: 'absolute', left: '12px', bottom: '12px', display: 'flex', alignItems: 'center', gap: '10px', padding: '6px 10px', borderRadius: '6px', background: 'var(--scrim)', border: '1px solid var(--bd)', fontFamily: "'JetBrains Mono',monospace", fontSize: '9px', color: 'var(--tx2)', pointerEvents: 'none' }}>
        <span><span style={{ color: '#149cc6' }}>●</span> FROTA AO VIVO {nFrota.toLocaleString('pt-BR')}</span>
        {preset === 'chuva' && <span><span style={{ color: '#57b7dc' }}>▦</span> RADAR · QUADRO MAIS NOVO</span>}
        <span style={{ color: 'var(--tx3)' }}>BASEMAP PROTOMAPS · R2</span>
      </div>
    </>
  )
}
