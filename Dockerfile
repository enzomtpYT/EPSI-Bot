# Multi-stage Dockerfile powered by uv
FROM python:3.12-slim-bookworm AS builder

# Copy uv binary from official Astral distroless image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Use the system Python across both stages
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PYTHON_DOWNLOADS=0
ENV UV_PYTHON=/usr/local/bin/python

WORKDIR /app

# Install dependencies using system Python in /app/.venv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy source code and install project
COPY . .
RUN uv sync --frozen --no-dev

# Final runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Configure timezone to Europe/Paris and install curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && ln -fs /usr/share/zoneinfo/Europe/Paris /etc/localtime \
    && echo "Europe/Paris" > /etc/timezone

# Setup non-root botuser and data directory
RUN useradd -m botuser && mkdir -p /app/data && chown -R botuser:botuser /app

# Copy virtual environment and app code from builder
COPY --from=builder --chown=botuser:botuser /app /app

RUN mkdir -p /app/data && chown -R botuser:botuser /app/data

USER botuser

ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app/src"

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["/app/.venv/bin/python", "src/main.py"]
