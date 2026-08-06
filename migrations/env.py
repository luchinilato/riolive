from alembic import context
from sqlalchemy import create_engine

from riolive.config import config
from riolive.modelos import Base

target_metadata = Base.metadata


def include_object(obj, name, type_, reflected, compare_to):  # type: ignore[no-untyped-def]
    # Tabelas internas do Timescale/PostGIS não são nossas
    if type_ == "table" and getattr(obj, "schema", None) in {
        "_timescaledb_internal",
        "_timescaledb_catalog",
        "tiger",
        "topology",
    }:
        return False
    if type_ == "table" and name == "spatial_ref_sys":
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(config().database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
