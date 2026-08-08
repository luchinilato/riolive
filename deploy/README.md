# Operação do servidor (Contabo VPS 6 — 169.58.140.118)

Deploy feito em 2026-08-06. Ubuntu 24.04 LTS, Docker CE + Compose, stack em
`/srv/riolive` (mesmo compose do dev + override `docker-compose.prod.yml`).
Painel público: **http://169.58.140.118** (Caddy: SPA + `/api` → FastAPI).
O produto se chama **Sinal Carioca** e o domínio é **`sinalcarioca.rio`** (ver
`[[DEC - Nome do produto - Sinal Carioca]]`). O Caddy ainda serve por IP puro:
apontar o DNS e ligar o TLS é passo pendente.

## Acesso

```bash
ssh root@169.58.140.118                          # só por chave (senha desabilitada)
ssh -L 3300:127.0.0.1:3300 root@169.58.140.118   # túnel: Dagster UI em localhost:3300
ssh -L 5433:127.0.0.1:5432 root@169.58.140.118   # túnel: Postgres em localhost:5433
```

Console de emergência (se o SSH quebrar): painel da Contabo → VNC.

## Layout e princípios

- `/srv/riolive` — código (rsync do repo, ver "Atualizar") + `.env` de produção
  (chmod 600; contém a senha do Postgres em `POSTGRES_PASSWORD` e
  `COMPOSE_FILE=docker-compose.yml:docker-compose.prod.yml`, então
  `docker compose` já resolve os dois arquivos sozinho).
- **Nenhum serviço além do Caddy publica porta externa.** O Docker fura o UFW,
  então tudo interno é `127.0.0.1` (db 5432, api 8000, dagster 3300).
- Firewall UFW: só 22/80/443. fail2ban no sshd. unattended-upgrades ativo.
- Apps futuros: compose próprio em `/srv/<app>`, bloco novo no Caddyfile.

## Deploy automático (push na `main`)

`.github/workflows/deploy.yml` roda a cada push na `main` (ou à mão, pelo
"Run workflow"). Três etapas: **gate** (`ruff format --check`, `ruff check`,
`mypy`, `pytest` — os testes de API pulam sozinhos por não haver Postgres no
runner), **build do painel** (`VITE_API_URL=/api`) e **entrega** (rsync do
código + do `dist/`, depois `deploy/deploy.sh` no servidor). Se o gate falhar,
nada chega em produção.

**Migrations não são aplicadas automaticamente** (decisão de 2026-08-06:
migration em hypertable do Timescale é dolorosa de desfazer). O `deploy.sh`
compara `alembic current` com `alembic heads` e, havendo diferença, o workflow
marca um aviso amarelo na execução. Aplicar à mão:

```bash
ssh root@169.58.140.118 'cd /srv/riolive && docker compose exec -T api alembic upgrade head'
```

Como o deploy reinicia a stack, cada push custa ~30–60 s sem coleta. Com GPS
sem backfill, isso é um micro-buraco na série — motivo pra agrupar pushes.

Segredo necessário no repo (Settings → Secrets → Actions): **`SSH_DEPLOY_KEY`**,
a chave privada dedicada (`github-actions-deploy-riolive`) cuja pública está no
`authorized_keys` do root com a opção `restrict`. O host key do servidor está
fixado no workflow — se a máquina for reinstalada, atualizar aquela linha.
O `.env` nunca passa pelo CI. Última entrega fica registrada em `/srv/riolive/VERSAO`.

## Rota nova na API exige rebuild

O serviço `api` é `build: .` sem volume de código, então o container roda a
imagem antiga até ser reconstruído. Rota que existe no código e responde 404 em
produção é quase sempre isto:

```bash
ssh root@169.58.140.118 'cd /srv/riolive && docker compose up -d --build api'
```

Ordem importa quando a rota depende de esquema novo: **migration primeiro**,
rebuild depois. Ao contrário, a API sobe consultando tabela que ainda não
existe e devolve 500 no lugar de 404.

## Cargas históricas (seeds que escrevem passado)

O container `api` **não monta `dados/`**, então credencial que vive ali (a
service account do GCP, por exemplo) não existe dentro dele. Para uma carga que
roda uma vez, subir um container avulso com o volume é melhor do que alterar o
compose de forma permanente:

```bash
ssh root@169.58.140.118 'cd /srv/riolive &&   docker compose run -d --name riolive-backfill-chuva   -v /srv/riolive/dados:/app/dados:ro   api python -m riolive.semente.chuva_datario'

docker logs -f riolive-backfill-chuva     # acompanhar
docker rm riolive-backfill-chuva          # limpar quando terminar
```

**`-d` não é opcional em carga longa.** `docker compose exec -T` sobrevive à
morte do cliente SSH, o que soa bom e não é: o processo continua no servidor
sem ninguém lendo o log, e conferir órfão com `ps aux` dentro da imagem devolve
vazio porque `ps` não existe ali. Lançado com `run -d`, o log fica no container.

**Custo medido do backfill de chuva (2026-08-07):** 330 meses, ~69 s por mês em
produção contra ~20 s em máquina local — 6 h no total, limitado por CPU do
Python (container em 105%, Postgres em 2,7%). Enquanto roda, `/mobilidade/linhas`
sai de 411 ms para ~1 s com cache quente; as demais rotas não mudam. É
retomável: relançar pula os meses já carregados sem gastar consulta.

**Agregado contínuo não enxerga passado inserido depois.** A política de refresh
só olha os últimos dias, então um backfill de 1997 enche a `medicao` e o
agregado continua vazio — com a API respondendo "sem histórico" e nada logando
erro. Os seeds que escrevem passado chamam `refresh_continuous_aggregate` no
fim; se rodar carga por fora, chamar à mão:

```sql
-- Dois agregados, nesta ordem: o diário é agregado do de 15 min (ver 0008).
-- Materializar só o de cima devolve dia vazio, sem erro nenhum.
CALL refresh_continuous_aggregate('chuva_15min_estacao', NULL, NULL);
CALL refresh_continuous_aggregate('chuva_dia_estacao', NULL, NULL);
```

## Atualizar o código à mão (fallback)

```bash
# do WSL, na raiz do worktree com o código desejado:
rsync -az --delete \
  --exclude '.git' --exclude '.venv' --exclude '__pycache__' --exclude '.pytest_cache' \
  --exclude '.mypy_cache' --exclude '.ruff_cache' --exclude '.dagster_home' \
  --exclude 'painel/node_modules' --exclude 'dados' --exclude '.env' \
  ./ root@169.58.140.118:/srv/riolive/

# painel (build local, VITE_API_URL=/api é obrigatório):
cd painel && VITE_API_URL=/api npm run build
rsync -az --delete painel/dist/ root@169.58.140.118:/srv/riolive/painel/dist/

# no servidor:
ssh root@169.58.140.118 'cd /srv/riolive && docker compose up -d --build'
```

O `.env` NUNCA entra no rsync — vive só no servidor. Migrations:
`docker compose exec -T api alembic upgrade head`.

## Backup e restore

- Cron diário 03:20 (`/etc/cron.d/riolive-backup`) roda `deploy/backup_r2.sh`:
  `pg_dump -Fc` → R2 `riolive-blobs/backups/pg/`, retenção 14 dias, log em
  `/var/log/riolive-backup.log`. Pinga healthchecks.io quando
  `RIOLIVE_HEALTHCHECKS_URL` for preenchida no `.env`.
- **Restore** (banco Timescale exige pré/pós):
  ```sql
  SELECT timescaledb_pre_restore();
  -- pg_restore -U riolive -d riolive caminho.dump
  SELECT timescaledb_post_restore();
  ```
- O banco `dagster` (runs/schedules) não é backupado de propósito — operacional
  e recriável.

## Limitações conhecidas do ambiente (2026-08-06)

- **metro_rio**: a API `ondeestameutrem.metrorio.app` responde **403 pro IP do
  datacenter** (local funciona). Fica `fora` até termos saída por outro IP
  (ex. Cloudflare Worker como proxy) ou o bloqueio mudar.
- GPS não tem backfill: servidor desligado = buraco na série (motivo de o
  deploy ter saído do WSL).
- O daemon do Dagster **local (WSL) foi parado** pra não consumir as APIs em
  dobro (TomTom free tier, rate limit do Fogo Cruzado). Religar só pra testar:
  `docker compose start dagster-daemon` — e desligar depois.

## Pendências pra quando as contas existirem

- SMTP (alertas por e-mail), healthchecks.io (dead-man's switch), Sentry —
  preencher as variáveis já existentes no `.env` e `docker compose up -d`.
- Domínio (nome ainda em aberto): trocar `:80` pelo hostname no `deploy/Caddyfile`
  (TLS automático) e rebuildar o painel se a API mudar de origem; Cloudflare
  na frente conforme a `[[DEC - Stack de backend e infraestrutura]]`.
