# riolive — Sinal Carioca

Backend do **Sinal Carioca** (`sinalcarioca.rio`), painel público em tempo real da cidade do Rio de Janeiro: ingestão de dezenas de fontes de dados abertos, persistência espacial/temporal (PostGIS + TimescaleDB) e API. `riolive` é o nome do repositório e do código; o produto é Sinal Carioca.

**Código fechado.** O produto é o painel hospedado; este repositório é privado.

## Stack

- Python 3.12, gerenciado com [uv](https://docs.astral.sh/uv/)
- Ingestão: httpx + tenacity, um módulo por fonte (config-driven), schemas Pydantic v2
- Orquestração: Dagster
- Banco: Postgres com PostGIS + TimescaleDB (hypertables, compressão, retenção, agregados contínuos), migrations via Alembic
- Infra local: Docker Compose (Postgres, Redis, Dagster)
- Monitoramento de fontes: máquina de estados (3 classes de falha), alertas por e-mail com cooldown, dead-man's switch (healthchecks.io), Sentry

## Subir o ambiente

```bash
cp .env.example .env        # preencher chaves; NUNCA commitar o .env
uv sync                     # dependências
docker compose up -d        # Postgres + Redis + Dagster
uv run alembic upgrade head # esquema do banco
uv run python -m riolive.semente.bairros  # dimensões bairro/RA (data.rio)
uv run pytest               # testes
```

Dagster UI: http://localhost:3300

## Estrutura

```
src/riolive/
├── config.py        # configurações (pydantic-settings, prefixo RIOLIVE_)
├── db.py            # engine/sessão SQLAlchemy
├── modelos/         # dimensões (fonte, local, bairro, ra) e fatos (medicao, posicao, evento, ...)
├── ingestao/        # fetcher genérico, contrato de fonte, gravação
├── fontes/          # um módulo por fonte: fetcher + schema + parser + cadência + criticidade
├── saude/           # máquina de estados de saúde, alertas, heartbeat
└── orquestracao/    # jobs, schedules e sensors do Dagster
migrations/          # Alembic
tests/fixtures/      # payloads reais capturados das fontes
```

## Documentação de projeto

As decisões de produto e arquitetura vivem no cofre Obsidian (`Rio Live/`), fora deste repo. Documentos canônicos: catálogo de fontes, DEC do modelo de dados, DEC de stack, DEC de monitoramento.
