FROM python:3.12-slim

# uv via PyPI: o registry ghcr.io resolve de forma instável neste WSL
RUN pip install --no-cache-dir "uv>=0.9,<0.10"

WORKDIR /app

# Dependências primeiro (camada cacheável)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"
ENV DAGSTER_HOME=/app/.dagster_home
RUN mkdir -p /app/.dagster_home
