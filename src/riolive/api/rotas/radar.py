"""GET /radar — manifesto dos últimos quadros pro overlay animado do mapa.

Enquanto o bucket não tem domínio público (Cloudflare custom domain, pendência
de deploy), as URLs saem pré-assinadas com validade curta — funcionam hoje e o
contrato não muda quando o domínio chegar (só o formato da URL).
"""

from typing import Annotated, Any

from fastapi import APIRouter, Query
from sqlalchemy import text

from riolive.blobs import ArmazemR2, armazem
from riolive.db import sessao

rota = APIRouter(tags=["radar"])
VALIDADE_URL_S = 900


@rota.get("/radar")
def quadros_radar(quadros: Annotated[int, Query(ge=1, le=40)] = 8) -> dict[str, Any]:
    with sessao() as s:
        linhas = s.execute(
            text(
                "SELECT b.ts, b.path, b.meta FROM blob_manifesto b "
                "JOIN fonte f ON f.id = b.fonte_id WHERE f.slug = 'radar_sumare' "
                "ORDER BY b.ts DESC LIMIT :lim"
            ),
            {"lim": quadros},
        ).all()
    deposito = armazem()
    resultado = []
    for linha in reversed(linhas):  # do mais antigo pro mais novo (ordem de animação)
        url = None
        if isinstance(deposito, ArmazemR2):
            url = deposito._s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": deposito._bucket, "Key": linha.path},
                ExpiresIn=VALIDADE_URL_S,
            )
        resultado.append({"ts": linha.ts.isoformat(), "path": linha.path, "url": url})
    bounds = linhas[0].meta.get("bounds") if linhas and linhas[0].meta else None
    return {"bounds": bounds, "quadros": resultado}
