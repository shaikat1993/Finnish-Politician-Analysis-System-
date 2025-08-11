# Production Dockerfile for data_collection service
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy data_collection source
COPY . /app

# Entrypoint: by default, run news enrichment for all politicians
CMD ["python", "-m", "data_collection.news.run_news_enrichment_for_all"]
