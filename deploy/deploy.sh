#!/usr/bin/env bash
# Roda NO SERVIDOR, chamado pelo workflow de deploy depois que o código já
# chegou por rsync. Não aplica migrations por decisão do Luciano (2026-08-06):
# migration em hypertable do Timescale é dolorosa de desfazer, então fica manual.
# Aqui ele só AVISA quando há migration pendente.
#
# Uso: deploy/deploy.sh <sha-do-commit>
set -euo pipefail
cd /srv/riolive

SHA="${1:-desconhecido}"

echo "→ Subindo containers (build incremental)"
docker compose up -d --build

echo "→ Esperando a API responder"
for _ in $(seq 1 30); do
  if curl -fsS -m 5 http://127.0.0.1:8000/fontes >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

echo "→ Fumaça: API e painel pelo Caddy"
curl -fsS -m 10 http://127.0.0.1/api/fontes >/dev/null
curl -fsS -m 10 http://127.0.0.1/ >/dev/null

# Migrations: comparar o que o banco tem com o que o código traz. NUNCA aplicar.
# As revisões deste projeto são numeradas (0001..0004), não hashes — por isso
# pegar o primeiro campo da última linha não-vazia, e não um padrão de hex.
ATUAL=$(docker compose exec -T api alembic current 2>/dev/null | awk 'NF{l=$1} END{print l}' || true)
CABECA=$(docker compose exec -T api alembic heads 2>/dev/null | awk 'NF{l=$1} END{print l}' || true)
if [ -n "${CABECA}" ] && [ "${ATUAL}" != "${CABECA}" ]; then
  echo "MIGRACAO_PENDENTE banco=${ATUAL:-vazio} codigo=${CABECA}"
  echo "   Aplicar à mão: ssh root@169.58.140.118 'cd /srv/riolive && docker compose exec -T api alembic upgrade head'"
fi

echo "${SHA}" > /srv/riolive/VERSAO
date -Iseconds >> /srv/riolive/VERSAO
echo "→ Deploy concluído: ${SHA}"
