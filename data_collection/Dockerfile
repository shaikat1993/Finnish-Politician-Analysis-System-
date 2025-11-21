# Production Dockerfile for data_collection service
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 collector && \
    chown -R collector:collector /app

# Copy application code
COPY --chown=collector:collector . /app

# Create necessary directories
RUN mkdir -p \
    /app/cache \
    /app/logs \
    /app/data && \
    chown -R collector:collector /app

# Switch to non-root user
USER collector

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Entrypoint: by default, run news enrichment for all politicians
CMD ["python", "-m", "data_collection.news.run_news_enrichment_for_all"]
