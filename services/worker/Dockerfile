FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

FROM base AS deps

COPY shared/pyproject.toml shared/pyproject.toml
COPY shared/shared/__init__.py shared/shared/__init__.py
COPY services/worker/pyproject.toml services/worker/pyproject.toml
COPY services/worker/worker/__init__.py services/worker/worker/__init__.py
COPY pyproject.toml uv.lock .python-version ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --package worker --no-dev --no-editable

FROM base AS runtime

COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY shared/shared/ /app/shared/shared/
COPY services/worker/worker/ /app/services/worker/worker/

EXPOSE 8000

CMD ["uvicorn", "worker.main:app", "--host", "0.0.0.0", "--port", "8000"]
