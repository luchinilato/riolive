"""Armazenamento de blobs (radar PNG, PDFs): banco não guarda imagem.

Decisão de 2026-08-06: object storage é o Cloudflare R2 em produção (egress zero,
API S3, mesma conta da CDN); em dev, disco local com a mesma interface. O banco
guarda só o manifesto (tabela blob_manifesto). O backend R2 entra quando o bucket
e as credenciais existirem — a interface não muda.
"""

from pathlib import Path

from riolive.config import config


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


def armazem() -> ArmazemLocal:
    # Quando RIOLIVE_R2_* existir no ambiente, este factory passa a devolver o
    # backend R2 (S3) sem mudar nenhum chamador.
    return ArmazemLocal()
