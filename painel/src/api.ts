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
  eventos: (horas = 24) => obter<any[]>(`/eventos?horas=${horas}&limite=40`),
  previsao: (local = 'centro') => obter<any>(`/previsao?local=${local}&horas=12`),
  serie: (metrica: string, passo = '1h', horas = 24) =>
    obter<any>(`/series/${metrica}?passo=${passo}&horas=${horas}`),
}
