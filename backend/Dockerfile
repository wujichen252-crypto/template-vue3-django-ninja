FROM ghcr.io/astral-sh/uv:0.5-python3.11-bookworm-slim AS deps

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=deps /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

COPY backend/ /app/

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

# 使用 gunicorn.conf.py 配置文件
COPY backend/gunicorn.conf.py /app/gunicorn.conf.py

CMD ["gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]
