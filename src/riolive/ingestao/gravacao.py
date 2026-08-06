"""Gravação dos registros tipados no banco, com enriquecimento espacial na entrada.

Enriquecimento (bairro/RA/H3) acontece uma vez, aqui — nunca em query. Dedup de
janelas sobrepostas (SPPO) é ON CONFLICT DO NOTHING sobre as PKs naturais.
"""

from datetime import UTC, datetime
from typing import Any

import h3
from geoalchemy2.elements import WKTElement
from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from riolive.blobs import armazem
from riolive.ingestao.contrato import (
    BlobNovo,
    EventoNovo,
    FonteConfig,
    LocalNovo,
    MedicaoNova,
    PosicaoNova,
    PrevisaoNova,
)
from riolive.modelos import BlobManifesto, Evento, Fonte, Local, Medicao, Posicao, Previsao

TAMANHO_LOTE = 5000


def _ponto(lat: float, lon: float) -> WKTElement:
    return WKTElement(f"POINT({lon} {lat})", srid=4326)


def _bairro_do_ponto(sessao: Session, lat: float, lon: float) -> tuple[int | None, int | None]:
    """Point-in-polygon contra a dimensão bairro. (None, None) se a dimensão não foi carregada."""
    linha = sessao.execute(
        text(
            "SELECT id, ra_id FROM bairro "
            "WHERE ST_Contains(geom, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)) LIMIT 1"
        ),
        {"lat": lat, "lon": lon},
    ).first()
    return (linha[0], linha[1]) if linha else (None, None)


def garantir_fonte(sessao: Session, cfg: FonteConfig) -> int:
    """Upsert da dimensão fonte a partir da FonteConfig; retorna o id."""
    stmt = (
        insert(Fonte)
        .values(
            slug=cfg.slug,
            nome=cfg.nome,
            orgao=cfg.orgao,
            url=cfg.url,
            licenca=cfg.licenca,
            bloco=cfg.bloco,
            criticidade=cfg.criticidade,
            cadencia_segundos=int(cfg.cadencia.total_seconds()),
        )
        .on_conflict_do_update(
            index_elements=["slug"],
            set_={
                "nome": cfg.nome,
                "orgao": cfg.orgao,
                "url": cfg.url,
                "licenca": cfg.licenca,
                "bloco": cfg.bloco,
                "criticidade": cfg.criticidade,
                "cadencia_segundos": int(cfg.cadencia.total_seconds()),
            },
        )
        .returning(Fonte.id)
    )
    return sessao.execute(stmt).scalar_one()


def upsert_locais(sessao: Session, fonte_id: int, locais: list[LocalNovo]) -> dict[str, int]:
    """Garante os pontos fixos da fonte e retorna codigo_externo → local.id."""
    for novo in locais:
        existe = sessao.execute(
            select(Local.id).where(
                Local.fonte_id == fonte_id, Local.codigo_externo == novo.codigo_externo
            )
        ).scalar_one_or_none()
        if existe is not None:
            continue
        bairro_id, ra_id = _bairro_do_ponto(sessao, novo.lat, novo.lon)
        sessao.add(
            Local(
                fonte_id=fonte_id,
                codigo_externo=novo.codigo_externo,
                nome=novo.nome,
                tipo=novo.tipo,
                geom=_ponto(novo.lat, novo.lon),
                bairro_id=bairro_id,
                ra_id=ra_id,
                h3_r8=h3.latlng_to_cell(novo.lat, novo.lon, 8),
                extra=novo.extra,
            )
        )
    sessao.flush()
    linhas = sessao.execute(
        select(Local.codigo_externo, Local.id).where(Local.fonte_id == fonte_id)
    ).all()
    return {codigo: id_ for codigo, id_ in linhas}


def inserir_medicoes(
    sessao: Session,
    fonte_id: int,
    medicoes: list[MedicaoNova],
    mapa_locais: dict[str, int],
    coletado_em: datetime,
) -> int:
    """Insere medições; releitura da mesma (local, métrica, ts) é ignorada. Retorna inseridos."""
    valores: list[dict[str, Any]] = [
        {
            "ts": m.ts,
            "local_id": mapa_locais[m.codigo_local],
            "fonte_id": fonte_id,
            "metrica": m.metrica,
            "valor": m.valor,
            "coletado_em": coletado_em,
            "payload": m.payload,
        }
        for m in medicoes
    ]
    inseridos = 0
    for i in range(0, len(valores), TAMANHO_LOTE):
        lote = valores[i : i + TAMANHO_LOTE]
        # RETURNING devolve só as linhas de fato inseridas (rowcount não é
        # confiável em insert multi-valores com ON CONFLICT)
        resultado = sessao.execute(
            insert(Medicao)
            .values(lote)
            .on_conflict_do_nothing(index_elements=["local_id", "metrica", "ts"])
            .returning(Medicao.ts)
        )
        inseridos += len(resultado.all())
    return inseridos


def inserir_posicoes(sessao: Session, posicoes: list[PosicaoNova], coletado_em: datetime) -> int:
    """Insere posições; janelas sobrepostas deduplicam na PK (modal, veiculo_id, ts)."""
    valores: list[dict[str, Any]] = [
        {
            "ts": p.ts,
            "modal": p.modal,
            "veiculo_id": p.veiculo_id,
            "linha": p.linha,
            "geom": _ponto(p.lat, p.lon),
            "velocidade": p.velocidade,
            "extra": p.extra,
            "coletado_em": coletado_em,
        }
        for p in posicoes
    ]
    inseridos = 0
    for i in range(0, len(valores), TAMANHO_LOTE):
        lote = valores[i : i + TAMANHO_LOTE]
        resultado = sessao.execute(
            insert(Posicao)
            .values(lote)
            .on_conflict_do_nothing(index_elements=["modal", "veiculo_id", "ts"])
            .returning(Posicao.ts)
        )
        inseridos += len(resultado.all())
    return inseridos


def gravar_eventos(
    sessao: Session, fonte_id: int, eventos: list[EventoNovo], coletado_em: datetime
) -> int:
    """Grava eventos. Pra tipo `vigente` (ex. estágio da cidade) só existe um evento
    aberto por tipo: releitura igual é no-op; mudança fecha o anterior e abre o novo.
    Evento pontual (não vigente) deduplica pela chave natural (tipo, inicio, h3_r8):
    fontes como o INPE re-servem a mesma janela em arquivos sucessivos.
    Retorna eventos novos inseridos.
    """
    inseridos = 0
    for novo in eventos:
        if novo.encerrar:
            sessao.execute(
                update(Evento)
                .where(Evento.tipo == novo.tipo, Evento.fim.is_(None))
                .values(fim=novo.inicio)
            )
            continue
        bairro_id, ra_id = (
            _bairro_do_ponto(sessao, novo.lat, novo.lon)
            if novo.lat is not None and novo.lon is not None
            else (None, None)
        )
        if novo.exigir_bairro and bairro_id is None:
            continue  # fora do município (ou dimensão bairro não carregada)
        h3_r8 = (
            h3.latlng_to_cell(novo.lat, novo.lon, 8)
            if novo.lat is not None and novo.lon is not None
            else None
        )
        if novo.vigente:
            aberto = sessao.execute(
                select(Evento)
                .where(Evento.tipo == novo.tipo, Evento.fim.is_(None))
                .order_by(Evento.inicio.desc())
                .limit(1)
            ).scalar_one_or_none()
            if aberto is not None:
                # mesmo estado vigente (severidade e título) = releitura; nada a fazer.
                # inicio não entra: fontes sem timestamp próprio mandam inicio=agora
                if aberto.severidade == novo.severidade and aberto.titulo == novo.titulo:
                    continue
                sessao.execute(
                    update(Evento)
                    .where(Evento.inicio == aberto.inicio, Evento.id == aberto.id)
                    .values(fim=novo.inicio)
                )
        else:
            repetido = sessao.execute(
                select(Evento.id)
                .where(
                    Evento.tipo == novo.tipo,
                    Evento.inicio == novo.inicio,
                    Evento.h3_r8.is_(None) if h3_r8 is None else Evento.h3_r8 == h3_r8,
                )
                .limit(1)
            ).scalar_one_or_none()
            if repetido is not None:
                continue
        sessao.add(
            Evento(
                tipo=novo.tipo,
                fonte_id=fonte_id,
                severidade=novo.severidade,
                inicio=novo.inicio,
                fim=novo.fim,
                titulo=novo.titulo,
                descricao=novo.descricao,
                geom=(
                    _ponto(novo.lat, novo.lon)
                    if novo.lat is not None and novo.lon is not None
                    else None
                ),
                bairro_id=bairro_id,
                ra_id=ra_id,
                h3_r8=h3_r8,
                visivel_apos=novo.visivel_apos,
                payload=novo.payload,
                coletado_em=coletado_em,
            )
        )
        inseridos += 1
    sessao.flush()
    return inseridos


def inserir_previsoes(
    sessao: Session,
    previsoes: list[PrevisaoNova],
    mapa_locais: dict[str, int],
    emitida_em: datetime,
) -> int:
    """Insere uma rodada de previsão; todas as rodadas são preservadas (decisão A)."""
    valores: list[dict[str, Any]] = [
        {
            "emitida_em": emitida_em,
            "local_id": mapa_locais[p.codigo_local],
            "metrica": p.metrica,
            "ts_alvo": p.ts_alvo,
            "valor": p.valor,
        }
        for p in previsoes
    ]
    inseridos = 0
    for i in range(0, len(valores), TAMANHO_LOTE):
        lote = valores[i : i + TAMANHO_LOTE]
        resultado = sessao.execute(
            insert(Previsao)
            .values(lote)
            .on_conflict_do_nothing(index_elements=["local_id", "metrica", "ts_alvo", "emitida_em"])
            .returning(Previsao.ts_alvo)
        )
        inseridos += len(resultado.all())
    return inseridos


def gravar_blobs(sessao: Session, fonte_id: int, blobs: list[BlobNovo]) -> int:
    """Salva blobs no armazém e registra no manifesto; caminho repetido é no-op."""
    deposito = armazem()
    inseridos = 0
    for blob in blobs:
        existe = sessao.execute(
            select(BlobManifesto.id)
            .where(BlobManifesto.fonte_id == fonte_id, BlobManifesto.path == blob.caminho)
            .limit(1)
        ).scalar_one_or_none()
        if existe is not None:
            continue
        deposito.salvar(blob.caminho, blob.conteudo)
        sessao.add(BlobManifesto(fonte_id=fonte_id, ts=blob.ts, path=blob.caminho, meta=blob.meta))
        inseridos += 1
    sessao.flush()
    return inseridos


def agora_utc() -> datetime:
    return datetime.now(tz=UTC)
