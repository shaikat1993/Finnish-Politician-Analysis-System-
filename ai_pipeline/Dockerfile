# Production Dockerfile for AI Pipeline
# Finnish Politician Analysis System - Multi-Agent Architecture
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai_pipeline ./ai_pipeline
COPY database ./database
COPY .env.example .env

# Create necessary directories
RUN mkdir -p \
    /app/cache \
    /app/security_metrics \
    /app/logs

# Set permissions
RUN chmod -R 755 /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from ai_pipeline import AgentOrchestrator; print('healthy')" || exit 1

# Expose no ports (service runs as worker/library)
# If you want to run as a service, expose appropriate port

# Default entrypoint - runs the orchestrator
CMD ["python", "-m", "ai_pipeline.run_orchestrator"]
