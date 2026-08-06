"""Base declarativa e tipos comuns dos modelos."""

from datetime import datetime
from typing import Annotated, Any

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, mapped_column

# Todo timestamp do projeto é timezone-aware (timestamptz)
ts_tz = Annotated[datetime, mapped_column(DateTime(timezone=True))]


class Base(DeclarativeBase):
    type_annotation_map = {  # noqa: RUF012 — config de classe do SQLAlchemy, não estado mutável
        dict[str, Any]: JSONB,
        datetime: DateTime(timezone=True),
    }
