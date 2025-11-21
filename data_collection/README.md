# FPAS Data Collection Service

Production data collection service for the Finnish Politician Analysis System.

## Overview

Autonomous service that collects data from multiple sources and stores it in Neo4j:

### Data Sources

**Politicians:**
- Eduskunta (Parliament) - Official politician data, voting records
- Vaalikone (YLE Election Compass) - Political positions
- Kuntaliitto (Municipal League) - Local government data

**News:**
- YLE (Finnish Broadcasting Company)
- Helsingin Sanomat
- Iltalehti
- MTV Uutiset
- Kauppalehti

**Secondary:**
- Wikipedia - Biographical enrichment
- Statistics Finland - Administrative data

## Quick Start

### Run with Docker (Recommended)

```bash
# From project root
docker build -t fpas-data-collection -f data_collection/Dockerfile .

# Run with environment variables from root .env
docker run -d \
  --name fpas-collector \
  --env-file .env \
  fpas-data-collection
```

### Run Locally

```bash
# From project root
python -m data_collection.news.run_news_enrichment_for_all
```

## Configuration

All configuration is managed via the project root `.env` file:

```bash
# Neo4j Connection (required)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Optional: Limit politicians for testing
ENRICH_LIMIT=10

# Optional: Content verification
ENABLE_HATE_SPEECH_DETECTOR=false
```

## Architecture

```
BaseCollector (abstract base class)
├── NewsCollector
│   ├── YleNewsCollector
│   ├── YleWebScraperCollector
│   ├── HelsingingSanomatCollector
│   ├── IltalehtCollector
│   ├── MTVUutisetCollector
│   └── KauppalehtiCollector
│
└── PoliticianCollector
    ├── EduskuntaCollector
    ├── VaalikoneCollector
    └── KuntaliittoCollector
```

### Key Components

**[base_collector.py](base_collector.py)** - Base classes with:
- Automatic rate limiting per service
- Retry logic with exponential backoff
- Session management
- Error handling

**[config/api_endpoints.py](config/api_endpoints.py)** - Centralized configuration:
- All API endpoints
- Rate limits per service
- Headers and authentication
- RSS feed URLs

**[news/unified_news_enricher.py](news/unified_news_enricher.py)** - Orchestration:
- Aggregates from all news sources
- Deduplication
- Batch Neo4j storage
- Content verification

**[news/run_news_enrichment_for_all.py](news/run_news_enrichment_for_all.py)** - Entry point:
- Fetches all politicians from Neo4j
- Enriches news for each politician
- Error handling per politician

## Features

✅ **Automatic rate limiting** - Respects each service's limits
✅ **Retry with exponential backoff** - Handles transient failures
✅ **Centralized API configuration** - Easy to maintain
✅ **Content verification** - Optional hate speech detection
✅ **Batch processing** - Efficient Neo4j writes
✅ **RSS + API support** - Multiple collection methods
✅ **Async/await** - Non-blocking operations

## Production Deployment

### Docker Compose (Recommended)

```yaml
services:
  data-collection:
    build:
      context: .
      dockerfile: data_collection/Dockerfile
    env_file: .env
    depends_on:
      - neo4j
    restart: unless-stopped
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: fpas-data-collection
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: collector
            image: fpas-data-collection:latest
            envFrom:
            - secretRef:
                name: fpas-secrets
```

## Monitoring

Logs are written to stdout/stderr in JSON format for easy aggregation.

**Key metrics to monitor:**
- Collection success/failure rate
- Articles collected per politician
- API rate limit hits
- Processing time per politician

## Development

### Project Structure

```
data_collection/
├── base_collector.py           # Base classes
├── config/
│   └── api_endpoints.py        # API configuration
├── politicians/                # Politician collectors
├── news/                       # News collectors
├── secondary/                  # Wikipedia, etc.
├── administrative/             # Statistics Finland
└── Dockerfile                  # Production container
```

### Adding a New Collector

1. Inherit from `BaseCollector`, `NewsCollector`, or `PoliticianCollector`
2. Add configuration to `config/api_endpoints.py`
3. Implement required abstract methods
4. Add to `UnifiedNewsEnricher` if news source

## Troubleshooting

**Neo4j connection errors:**
- Verify `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` in `.env`
- Ensure Neo4j is running and accessible

**Rate limit errors:**
- Adjust rate limits in `config/api_endpoints.py`
- Check service-specific rate limit policies

**Missing data:**
- Check logs for specific collector errors
- Verify API endpoints are still valid
- Some services may require API keys

## License

Academic research project - CC BY 4.0
