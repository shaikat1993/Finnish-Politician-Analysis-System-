# Production Dockerfile for ai_pipeline
FROM python:3.11-slim as base

# Set workdir
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy ai_pipeline source
COPY . /app

# Expose no ports (service/worker pattern)

# Entrypoint
CMD ["python", "-m", "ai_pipeline.run_orchestrator"]
