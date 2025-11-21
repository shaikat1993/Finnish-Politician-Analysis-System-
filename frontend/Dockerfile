# Production Dockerfile for Streamlit frontend
FROM python:3.11-slim as base

# Set environment variables for Python optimization
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

# Create non-root user for security
RUN useradd -m -u 1000 streamlit && \
    chown -R streamlit:streamlit /app

# Copy Streamlit config first
COPY --chown=streamlit:streamlit frontend/.streamlit /app/.streamlit

# Copy application code with proper ownership
COPY --chown=streamlit:streamlit . /app

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/logs \
    /app/cache && \
    chown -R streamlit:streamlit /app /app/.streamlit

# Switch to non-root user
USER streamlit

# Expose Streamlit default port
EXPOSE 8501

# Health check for container orchestration
HEALTHCHECK --interval=60s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Entrypoint: run Streamlit app with Docker-optimized settings
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=true", \
     "--server.enableXsrfProtection=true", \
     "--browser.gatherUsageStats=false"]
