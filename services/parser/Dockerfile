FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM base AS deps

COPY shared/pyproject.toml shared/pyproject.toml
COPY shared/shared/__init__.py shared/shared/__init__.py
COPY services/parser/pyproject.toml services/parser/pyproject.toml
COPY services/parser/parser/__init__.py services/parser/parser/__init__.py
COPY pyproject.toml uv.lock .python-version ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package parser --no-dev --no-editable

FROM base AS runtime

COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY shared/shared/ /app/shared/shared/
COPY services/parser/parser/ /app/services/parser/parser/

CMD ["python", "-m", "parser.main"]
