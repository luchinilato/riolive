# riolive — guia pra sessões de código

**Sinal Carioca** (`sinalcarioca.rio`) — painel público em tempo real da cidade do Rio. `riolive` é o nome do repo/código; o produto é Sinal Carioca. Backend Python (ingestão + API) e frontend React (`painel/`), monorepo privado. **Código, tabelas e identificadores em português** (decisão do Luciano). As decisões de produto/arquitetura vivem no vault Obsidian (`/mnt/c/Users/lucia/obsidian-cofre/Rio Live/` — comece pelo handoff mais recente e pelas notas `DEC - *`).

## Comandos

```bash
docker compose up -d              # Postgres(PostGIS+Timescale) + Redis + Dagster + API
uv run alembic upgrade head       # esquema (migrations 0001–0005)
uv run pytest                     # ~80 testes; os de API/BD pulam se o compose estiver fora
uv run ruff format . && uv run ruff check . && uv run mypy   # gate obrigatório antes de commit
cd painel && npm run dev          # cockpit em :5173 (API precisa estar de pé em :8000)
```

Dagster UI: `localhost:3300` (a 3000 do host está ocupada por outro app). API/Swagger: `localhost:8000/docs`.

## Arquitetura (o essencial)

- **`src/riolive/fontes/`** — um módulo por fonte exportando `FONTE: FonteConfig` (slug, cadência, criticidade, `coletar`). Registro em `fontes/__init__.py`. Toda fonte tem fixture real em `tests/fixtures/` e testes. Erros: `ErroRede` (transitório) / `ErroSchema` (formato mudou) — classes da máquina de saúde; credencial ausente = `RuntimeError` (defeito nosso, estoura no Dagster).
- **`ingestao/`** — `fetcher.py` (httpx+tenacity), `contrato.py` (MedicaoNova/PosicaoNova/EventoNovo/PrevisaoNova/BlobNovo), `gravacao.py` (dedup por PK natural + enriquecimento bairro/RA/H3 na entrada), `execucao.py` (coleta→grava→saúde→alerta).
- **`saude/`** — máquina de estados (online/degradada/fora/congelada), contadores e cooldown no Redis. **`detectores/linha_parada.py`** — planejado×realizado; NUNCA roda sem `gps_confiavel()` (online 20+ min contínuos + 1.500 ônibus transmitindo — aprendido com 111 falsos positivos).
- **`api/rotas/`** — read-only; eventos saem SÓ pela `vw_evento_publico`. Cache-Control pra CDN.
- **`semente/`** — cargas re-executáveis: bairros, GTFS, fogo_cruzado (backfill; retomada ignora últimos 7 dias), gps_sppo (backfill de posições; retoma da fronteira do banco, fatias de 10 min), chuva_datario (1997→2024-06 do BigQuery público; ~1 GB de consulta para 27 anos, e **materializa `chuva_dia_estacao` no fim** — agregado contínuo não enxerga passado inserido depois).
- **`blobs.py`** — R2 quando `RIOLIVE_R2_*` no ambiente, senão disco (`dados/blobs/`).
- **`painel/`** — view-model único (`modelo/base.ts` = porte literal do protótipo, com modos demo) + `modelo/dadosReais.ts` (overlay da API via TanStack Query). Seções em `secoes/` geradas do handoff (`docs/design/handoff/painel-rio.dc.html` é a fonte visual da verdade). Estilos inline por design. `maplibre-gl` fixado no v5 (v6 quebra pmtiles silenciosamente).

## Pegadinhas que já custaram tempo

- `.env` NUNCA entra na imagem Docker (o Dagster auto-carrega `.env` do cwd e sobrepõe o ambiente — ver `.dockerignore`). Chaves só no `.env`; `.env.example` é versionado e fica vazio.
- SPPO devolve HTTP 200 com dict de erro em timeout interno (classificar como rede). Fontes municipais caem com frequência — o produto é desenhado pra mostrar isso.
- **SPPO: o sufixo `Z` do campo `datetime` é mentira** — o valor é hora local do Rio. Parseado ao pé da letra, toda posição entra 3 h no passado, em silêncio. Quem pegou foi a checagem de frescor (fonte virou `congelada`), não teste nenhum. Achado em 2026-08-07, junto com a troca de schema da SMTR (o payload virou GTFS: `id_veiculo`, `servico`, `trip_id`, `shape_id`). Ao mexer em fonte com timestamp, desconfie do fuso antes de confiar no rótulo.
- Posição de ônibus **tem** backfill: a API do SPPO serve janelas passadas (testado até 30 h). Buraco na série é recuperável com `python -m riolive.semente.gps_sppo`.
- `cd` relativo em comandos compostos falha quando o cwd do shell resetou — usar caminhos absolutos.
- `pkill -f` com o padrão no mesmo comando se mata — usar o truque `[p]adrão`.
- Cron do Dagster: minutos <60 → `*/N`; horas → `0 */H`; diária/semanal têm forma própria em `_cron()`.
- Fogo Cruzado: rate limit ~4 req/s (429); pino exato e sem atraso são exigência de DEC.
- **Chuva histórica: `chuva_1h` é janela móvel.** Somar todas as leituras dá 4× a chuva real (leitura de 15 em 15 min). A base somável é `chuva_15min` — é a única que o backfill importa como acumulável.
- **Climatologia compara o mesmo recorte de dias** (1 a D contra 1 a D), nunca mês em curso contra mês fechado: o segundo anuncia seca histórica todo dia 5 só por ler o calendário.

## Estado e fila

`fontes.xlsx` (raiz) = planilha viva das fontes com status real. O que falta está no handoff do vault (`2026-08-06 Handoff - backend e painel construídos...`): dossiê de Segurança + demais dossiês honestos, camadas reais no mapa, costuras de cards (mar/ar/queimadas), re-escopo por zona. Screenshots de referência em `docs/capturas/`.

## Produção (desde 2026-08-06)

No ar em **http://169.58.140.118** (Contabo VPS, `/srv/riolive`). **`deploy/README.md` é a doc de operação** — acesso, túneis, backup, restore. Push na `main` deploya sozinho depois do gate (`.github/workflows/deploy.yml`); **migrations não são automáticas** por decisão — o deploy avisa e você aplica à mão. O daemon do Dagster **local está parado de propósito** (duas instâncias gastariam as cotas das APIs em dobro); produção é a fonte da série. Decisões no vault: `DEC - Topologia de produção no VPS` e `DEC - Deploy automático com gate, migrations manuais`.
