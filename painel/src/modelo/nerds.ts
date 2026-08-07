/* Dados da página "Info para Nerds" — a vitrine de engenharia do Sinal Carioca.
 *
 * Os volumes são ESTIMATIVAS MENSAIS, não leitura ao vivo (decisão de 2026-08-07):
 * a página mostra ordem de grandeza e stack, não telemetria em tempo real. Cada
 * número abaixo traz a medição real de onde saiu — ao reestimar, refaça a conta,
 * não chute. Medições de 2026-08-07 contra a produção no Contabo.
 */

export interface Metrica {
  rotulo: string
  valor: string
  unidade: string
  detalhe: string
}

/* Ônibus: 409.658 posições gravadas numa hora de operação (backfill de 2026-08-07,
 * fatia do início da noite). Modelo do dia: ~400 mil/h em 18 h ativas + ~150 mil/h
 * nas 6 h de madrugada ≈ 8,1 M/dia. BRT: 7,3 a 13,6 mil/h medidos de madrugada,
 * ~20 mil/h de média no dia. Aviões (ADS-B): 15 a 31/h de madrugada, muito mais de dia. */
export const VOLUME_MENSAL: Metrica[] = [
  {
    rotulo: 'Posições de veículos',
    valor: '255',
    unidade: 'milhões/mês',
    detalhe: 'GPS de ~4 mil ônibus e do BRT, uma leitura a cada 36 s por veículo',
  },
  {
    rotulo: 'Medições',
    valor: '2,2',
    unidade: 'milhões/mês',
    detalhe: 'chuva, nível de rios, qualidade do ar, velocidade de corredores',
  },
  {
    rotulo: 'Varreduras de radar',
    valor: '8,6',
    unidade: 'mil/mês',
    detalhe: 'imagem do radar do Sumaré de 5 em 5 minutos, guardada por 1 ano',
  },
  {
    rotulo: 'Em regime, na retenção',
    valor: '750',
    unidade: 'milhões de linhas',
    detalhe: 'posições ficam 90 dias; medições e eventos ficam pra sempre',
  },
]

/* Histórico já carregado — o que dá profundidade ao painel, além do tempo real. */
export const HISTORICO: Metrica[] = [
  {
    rotulo: 'Fogo Cruzado',
    valor: '28,6',
    unidade: 'mil ocorrências',
    detalhe: 'toda a violência armada mapeada na capital desde 2016',
  },
  {
    rotulo: 'ISP-RJ',
    valor: '282',
    unidade: 'meses',
    detalhe: 'estatística criminal oficial de 2003 a 2026, seis métricas',
  },
  {
    rotulo: 'GTFS',
    valor: '1,03',
    unidade: 'milhão de horários',
    detalhe: '492 rotas planejadas, o "planejado" do planejado × realizado',
  },
]

export interface BlocoStack {
  titulo: string
  linhas: { chave: string; valor: string }[]
}

export const STACK: BlocoStack[] = [
  {
    titulo: 'Dados',
    linhas: [
      { chave: 'Banco', valor: 'Postgres com PostGIS e TimescaleDB' },
      { chave: 'Séries', valor: 'hypertables, compressão nativa, retenção por política' },
      { chave: 'Pré-agregação', valor: 'continuous aggregates atualizados pelo próprio banco' },
      { chave: 'Espacial', valor: 'índice GiST, junção por bairro e RA, células H3' },
      { chave: 'Migrations', valor: 'Alembic, aplicadas à mão em produção por decisão' },
    ],
  },
  {
    titulo: 'Ingestão',
    linhas: [
      { chave: 'Orquestração', valor: 'Dagster, um job por fonte com cadência própria' },
      { chave: 'Fontes', valor: '18 módulos config-driven, cada um com fixture real e teste' },
      { chave: 'Rede', valor: 'httpx com retry e backoff exponencial (tenacity)' },
      { chave: 'Validação', valor: 'Pydantic v2 — formato que muda vira falha explícita' },
      { chave: 'Deduplicação', valor: 'chave natural no banco; janelas se sobrepõem de propósito' },
    ],
  },
  {
    titulo: 'Saúde das fontes',
    linhas: [
      { chave: 'Estados', valor: 'online, degradada, fora, congelada' },
      { chave: 'Classes de falha', valor: 'rede (passa), schema (não passa), frescor (dado parado)' },
      { chave: 'Contadores', valor: 'Redis, com cooldown pra não repetir alarme' },
      { chave: 'Salvaguarda', valor: 'detector de linha parada só roda com GPS comprovadamente são' },
    ],
  },
  {
    titulo: 'Entrega',
    linhas: [
      { chave: 'API', valor: 'FastAPI, só leitura, Cache-Control pensado pra CDN' },
      { chave: 'Painel', valor: 'React com Vite, view-model único, TanStack Query' },
      { chave: 'Mapa', valor: 'MapLibre com tiles Protomaps servidos do próprio object storage' },
      { chave: 'Blobs', valor: 'Cloudflare R2, URLs pré-assinadas' },
    ],
  },
  {
    titulo: 'Infraestrutura',
    linhas: [
      { chave: 'Servidor', valor: 'VPS próprio, Docker Compose, base endurecida' },
      { chave: 'Exposição', valor: 'só o Caddy na rua; banco e orquestrador por túnel SSH' },
      { chave: 'Entrega', valor: 'push na main deploya sozinho, atrás de um gate de qualidade' },
      { chave: 'Gate', valor: 'ruff, mypy e a suíte de testes — vermelho não sobe' },
      { chave: 'Backup', valor: 'dump diário do Postgres pro object storage, com retenção' },
    ],
  },
]

/* Por que a página existe, em uma frase que não seja auto-elogio. */
export const ABERTURA =
  'O painel mostra a cidade. Esta página mostra a máquina que sustenta o painel: ' +
  'de onde o dado vem, quanto dele passa por aqui, e o que acontece quando uma fonte cai.'

export const NOTA_RODAPE =
  'Volumes são estimativas mensais derivadas de medição real na produção em 2026-08-07, ' +
  'não leitura ao vivo. O estado atual de cada fonte, esse sim, está na página de Status.'
