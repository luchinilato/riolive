/* Cliente da API de leitura do riolive (FastAPI). */

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

async function obter<T>(caminho: string): Promise<T> {
  const resposta = await fetch(`${BASE}${caminho}`)
  if (!resposta.ok) throw new Error(`${caminho}: HTTP ${resposta.status}`)
  return resposta.json() as Promise<T>
}

export const api = {
  agora: () => obter<any>('/agora'),
  fontes: () => obter<any[]>('/fontes'),
  eventos: (horas = 24, limite = 40) => obter<any[]>(`/eventos?horas=${horas}&limite=${limite}`),
  eventosDoTipo: (tipo: string, horas = 24, limite = 200) =>
    obter<any[]>(`/eventos?tipo=${tipo}&horas=${horas}&limite=${limite}`),
  previsao: (local = 'centro', horas = 12) =>
    obter<any>(`/previsao?local=${local}&horas=${horas}`),
  serie: (metrica: string, passo = '1h', horas = 24) =>
    obter<any>(`/series/${metrica}?passo=${passo}&horas=${horas}`),
  locais: (consulta: string) => obter<any>(`/locais?${consulta}`),
  estacoesChuva: () => obter<any[]>('/chuva/estacoes'),
  estacoesAr: () => obter<any[]>('/ar/estacoes'),
  radar: (quadros = 12) => obter<any>(`/radar?quadros=${quadros}`),
  corredores: () => obter<any>('/transito/corredores'),
  mobilidade: () => obter<any>('/mobilidade/linhas'),
  seguranca: (horas = 24) => obter<any>(`/seguranca/resumo?horas=${horas}`),
  aeronaves: (minutos = 10, horas = 24) =>
    obter<any>(`/ceu/aeronaves?minutos=${minutos}&horas=${horas}`),
  queimadas: (horas = 24) => obter<any>(`/queimadas/resumo?horas=${horas}`),
  climatologia: () => obter<any>('/chuva/climatologia'),
  pipeline: () => obter<any>('/fontes/pipeline'),
}
