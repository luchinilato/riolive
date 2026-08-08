/* Cliente da API de leitura do riolive (FastAPI). */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function obter<T>(caminho: string): Promise<T> {
  const resposta = await fetch(`${BASE}${caminho}`)
  if (!resposta.ok) throw new Error(`${caminho}: HTTP ${resposta.status}`)
  return resposta.json() as Promise<T>
}

/* `?zona=` só entra quando há zona escolhida: a API entende a ausência como "a
   cidade inteira", e mandar `zona=` vazio seria pedir um recorte que não existe
   — 422, não cidade inteira. */
const comZona = (caminho: string, zona?: string | null) =>
  zona ? `${caminho}${caminho.includes('?') ? '&' : '?'}zona=${zona}` : caminho

export const api = {
  agora: () => obter<any>('/agora'),
  fontes: () => obter<any[]>('/fontes'),
  eventos: (horas = 24, limite = 40, zona?: string | null) =>
    obter<any[]>(comZona(`/eventos?horas=${horas}&limite=${limite}`, zona)),
  eventosDoTipo: (tipo: string, horas = 24, limite = 200, zona?: string | null) =>
    obter<any[]>(comZona(`/eventos?tipo=${tipo}&horas=${horas}&limite=${limite}`, zona)),
  previsao: (local = 'centro', horas = 12) =>
    obter<any>(`/previsao?local=${local}&horas=${horas}`),
  serie: (metrica: string, passo = '1h', horas = 24) =>
    obter<any>(`/series/${metrica}?passo=${passo}&horas=${horas}`),
  locais: (consulta: string) => obter<any>(`/locais?${consulta}`),
  estacoesChuva: (zona?: string | null) => obter<any[]>(comZona('/chuva/estacoes', zona)),
  estacoesAr: (zona?: string | null) => obter<any[]>(comZona('/ar/estacoes', zona)),
  radar: (quadros = 12) => obter<any>(`/radar?quadros=${quadros}`),
  corredores: () => obter<any>('/transito/corredores'),
  mobilidade: () => obter<any>('/mobilidade/linhas'),
  seguranca: (horas = 24, zona?: string | null) =>
    obter<any>(comZona(`/seguranca/resumo?horas=${horas}`, zona)),
  aeronaves: (minutos = 10, horas = 24) =>
    obter<any>(`/ceu/aeronaves?minutos=${minutos}&horas=${horas}`),
  queimadas: (horas = 24) => obter<any>(`/queimadas/resumo?horas=${horas}`),
  climatologia: (zona?: string | null) => obter<any>(comZona('/chuva/climatologia', zona)),
  pipeline: () => obter<any>('/fontes/pipeline'),
}
