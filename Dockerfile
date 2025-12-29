# Use a multi-arch base image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    pkg-config \
    libcairo2-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (including libcairo2) and set timezone
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -fs /usr/share/zoneinfo/Europe/Paris /etc/localtime \
    && echo "Europe/Paris" > /etc/timezone

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app .

# Create a non-root user
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "index.py"] 
