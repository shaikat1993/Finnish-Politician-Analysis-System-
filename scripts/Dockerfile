# Minimal Python image for running utility scripts
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy scripts source
COPY . /app

# Default entrypoint (can be overridden)
CMD ["python", "scripts/init_province_data.py"]
