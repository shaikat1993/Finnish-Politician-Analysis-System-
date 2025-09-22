# Production Dockerfile for Streamlit frontend
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install specific version of streamlit_folium that has st_folium function
RUN pip install --no-cache-dir streamlit_folium==0.11.0

# Copy frontend source
COPY . /app

# Expose Streamlit default port
EXPOSE 8501

# Entrypoint: run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]