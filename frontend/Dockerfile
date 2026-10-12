#----------------------------------------------------------------------------------
# build stage (same setup as the backend Dockerfile)
#----------------------------------------------------------------------------------
FROM python:3.12.7-slim-bookworm AS builder
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-dev

COPY . .
RUN uv sync --locked --no-dev

#----------------------------------------------------------------------------------
# production stage
#----------------------------------------------------------------------------------
FROM python:3.12.7-slim-bookworm
WORKDIR /app

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

COPY --from=builder --chown=appuser:appuser /app /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

CMD ["/bin/sh", "-c", "exec fastapi run main.py --host 0.0.0.0 --port \"$PORT\""]
