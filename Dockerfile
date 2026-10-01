# Multi-stage Dockerfile powered by uv
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies using uv sync without dev packages
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install project
COPY . .
RUN uv sync --frozen --no-dev

# Final runtime image
FROM python:3.11-slim-bookworm

WORKDIR /app

# Configure timezone to Europe/Paris
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -fs /usr/share/zoneinfo/Europe/Paris /etc/localtime \
    && echo "Europe/Paris" > /etc/timezone

# Setup non-root botuser
RUN useradd -m botuser && chown -R botuser:botuser /app

# Copy virtual environment and app code from builder
COPY --from=builder --chown=botuser:botuser /app /app

USER botuser

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/src"

EXPOSE 8080

CMD ["python", "src/main.py"]
