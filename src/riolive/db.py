"""Engine e sessões SQLAlchemy."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from riolive.config import config


@lru_cache
def engine() -> Engine:
    return create_engine(config().database_url, pool_pre_ping=True)


@lru_cache
def _fabrica_sessao() -> sessionmaker[Session]:
    return sessionmaker(bind=engine(), expire_on_commit=False)


@contextmanager
def sessao() -> Iterator[Session]:
    """Sessão com commit no sucesso e rollback em exceção."""
    s = _fabrica_sessao()()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
