"""Armazenamento de blobs (radar PNG, PDFs): banco não guarda imagem.

Decisão de 2026-08-06: object storage é o Cloudflare R2 (egress zero, API S3,
mesma conta da CDN). Com RIOLIVE_R2_* configurado no ambiente, o armazém é o R2;
sem, cai pro disco local (dev). O banco guarda só o manifesto (blob_manifesto) —
o `path` registrado é o mesmo nos dois backends, então migrar é copiar arquivos.
"""

from functools import lru_cache
from pathlib import Path
from typing import Protocol

import boto3
from botocore.exceptions import ClientError

from riolive.config import config


class Armazem(Protocol):
    def salvar(self, caminho: str, conteudo: bytes) -> str: ...
    def existe(self, caminho: str) -> bool: ...


class ArmazemLocal:
    """Blobs em disco (dev). Caminho relativo vira o `path` do manifesto."""

    def __init__(self, raiz: str | None = None) -> None:
        self._raiz = Path(raiz if raiz is not None else config().blobs_dir)

    def salvar(self, caminho: str, conteudo: bytes) -> str:
        destino = self._raiz / caminho
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_bytes(conteudo)
        return caminho

    def existe(self, caminho: str) -> bool:
        return (self._raiz / caminho).exists()


class ArmazemR2:
    """Blobs no Cloudflare R2 via API S3."""

    def __init__(self) -> None:
        cfg = config()
        self._bucket = cfg.r2_bucket
        self._s3 = boto3.client(
            "s3",
            endpoint_url=cfg.r2_endpoint,
            aws_access_key_id=cfg.r2_access_key_id.get_secret_value(),
            aws_secret_access_key=cfg.r2_secret_access_key.get_secret_value(),
        )

    def salvar(self, caminho: str, conteudo: bytes) -> str:
        self._s3.put_object(Bucket=self._bucket, Key=caminho, Body=conteudo)
        return caminho

    def existe(self, caminho: str) -> bool:
        try:
            self._s3.head_object(Bucket=self._bucket, Key=caminho)
            return True
        except ClientError:
            return False


@lru_cache
def armazem() -> Armazem:
    if config().r2_configurado:
        return ArmazemR2()
    return ArmazemLocal()
