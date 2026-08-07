#!/usr/bin/env bash
# Backup diário do Postgres pro Cloudflare R2 (requisito da DEC de stack).
# pg_dump sai do container do banco e o upload usa o boto3 que já existe no
# container da API (mesmas credenciais R2 do .env) — nada instalado no host.
# Retenção: 14 diários no prefixo backups/pg/ do bucket.
set -euo pipefail
cd /srv/riolive

STAMP=$(date +%F)

docker compose exec -T db pg_dump -U riolive -d riolive -Fc \
  | docker compose exec -T api python -c '
import os, sys, datetime
import boto3
s3 = boto3.client(
    "s3",
    endpoint_url=os.environ["RIOLIVE_R2_ENDPOINT"],
    aws_access_key_id=os.environ["RIOLIVE_R2_ACCESS_KEY_ID"],
    aws_secret_access_key=os.environ["RIOLIVE_R2_SECRET_ACCESS_KEY"],
)
bucket = os.environ["RIOLIVE_R2_BUCKET"]
chave = f"backups/pg/riolive-{sys.argv[1]}.dump"
s3.upload_fileobj(sys.stdin.buffer, bucket, chave)
tam = s3.head_object(Bucket=bucket, Key=chave)["ContentLength"]
print(f"backup {chave}: {tam/1e6:.1f} MB")

limite = datetime.date.today() - datetime.timedelta(days=14)
antigos = [
    o["Key"]
    for o in s3.list_objects_v2(Bucket=bucket, Prefix="backups/pg/").get("Contents", [])
    if o["Key"] < f"backups/pg/riolive-{limite.isoformat()}"
]
for chave_antiga in antigos:
    s3.delete_object(Bucket=bucket, Key=chave_antiga)
    print(f"retenção: removido {chave_antiga}")
' "$STAMP"

# Dead-man's switch: pinga o healthchecks.io se a conta já existir (.env)
HC_URL=$(grep -E '^RIOLIVE_HEALTHCHECKS_URL=' .env | cut -d= -f2- || true)
if [ -n "${HC_URL}" ]; then
  curl -fsS -m 10 --retry 3 "${HC_URL}" >/dev/null || true
fi
