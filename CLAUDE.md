# riolive — guia pra sessões de código

Painel público em tempo real da cidade do Rio. Backend Python (ingestão + API) e frontend React (`painel/`), monorepo privado. **Código, tabelas e identificadores em português** (decisão do Luciano). As decisões de produto/arquitetura vivem no vault Obsidian (`/mnt/c/Users/lucia/obsidian-cofre/Rio Live/` — comece pelo handoff mais recente e pelas notas `DEC - *`).

## Comandos

```bash
docker compose up -d              # Postgres(PostGIS+Timescale) + Redis + Dagster + API
uv run alembic upgrade head       # esquema (migrations 0001–0004)
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
- **`semente/`** — cargas re-executáveis: bairros, GTFS, fogo_cruzado (backfill; retomada ignora últimos 7 dias).
- **`blobs.py`** — R2 quando `RIOLIVE_R2_*` no ambiente, senão disco (`dados/blobs/`).
- **`painel/`** — view-model único (`modelo/base.ts` = porte literal do protótipo, com modos demo) + `modelo/dadosReais.ts` (overlay da API via TanStack Query). Seções em `secoes/` geradas do handoff (`docs/design/handoff/painel-rio.dc.html` é a fonte visual da verdade). Estilos inline por design. `maplibre-gl` fixado no v5 (v6 quebra pmtiles silenciosamente).

## Pegadinhas que já custaram tempo

- `.env` NUNCA entra na imagem Docker (o Dagster auto-carrega `.env` do cwd e sobrepõe o ambiente — ver `.dockerignore`). Chaves só no `.env`; `.env.example` é versionado e fica vazio.
- SPPO devolve HTTP 200 com dict de erro em timeout interno (classificar como rede). Fontes municipais caem com frequência — o produto é desenhado pra mostrar isso.
- `cd` relativo em comandos compostos falha quando o cwd do shell resetou — usar caminhos absolutos.
- `pkill -f` com o padrão no mesmo comando se mata — usar o truque `[p]adrão`.
- Cron do Dagster: minutos <60 → `*/N`; horas → `0 */H`; diária/semanal têm forma própria em `_cron()`.
- Fogo Cruzado: rate limit ~4 req/s (429); pino exato e sem atraso são exigência de DEC.

## Estado e fila

`fontes.xlsx` (raiz) = planilha viva das fontes com status real. O que falta está no handoff do vault (`2026-08-06 Handoff - backend e painel construídos...`): dossiê de Segurança + demais dossiês honestos, camadas reais no mapa, costuras de cards (mar/ar/queimadas), re-escopo por zona; deploy/monitoramento ficou deliberadamente pro final. Screenshots de referência em `docs/capturas/`.
