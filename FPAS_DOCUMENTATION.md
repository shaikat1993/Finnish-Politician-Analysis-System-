# Finnish Politician Analysis System (FPAS) - Technical Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Module Reference](#module-reference)
   - [Data Collection](#data-collection)
   - [Database](#database)
   - [AI Pipeline](#ai-pipeline)
   - [API](#api)
   - [Frontend](#frontend)
   - [Security](#security)
   - [Testing](#testing)
4. [Key Workflows](#key-workflows)
5. [Configuration](#configuration)
6. [Development Guide](#development-guide)

## Project Overview

The Finnish Politician Analysis System (FPAS) is an enterprise-grade AI-powered political analysis system that provides real-time monitoring and analysis of Finnish politicians. The system collects data from official sources, news outlets, and public records, processes it through an advanced AI pipeline, and presents insights through an interactive dashboard.

## System Architecture

FPAS follows a modular, layered architecture:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   Data Collection   │────▶│    AI Pipeline      │────▶│      Frontend       │
│                     │     │                     │     │                     │
│ - Politicians       │     │ - Agent Orchestrator│     │ - Streamlit UI      │
│ - News Articles     │     │ - Analysis Agent    │     │ - Interactive Map   │
│ - Administrative    │     │ - Query Agent       │     │ - Politician Grid   │
└─────────┬───────────┘     └─────────┬───────────┘     └─────────────────────┘
          │                           │                           ▲
          │                           │                           │
          ▼                           ▼                           │
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│      Database       │◀───▶│        API          │────▶│     Security        │
│                     │     │                     │     │                     │
│ - Neo4j Graph DB    │     │ - FastAPI Endpoints │     │ - Prompt Injection  │
│ - Vector Storage    │     │ - Data Models       │     │ - Output Sanitizing │
│ - Analytics Queries │     │ - Response Handling │     │ - Verification      │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

## Module Reference

### Data Collection

#### `/data_collection/base_collector.py`
- **Purpose**: Provides abstract base classes for all data collectors
- **Key Components**: 
  - `BaseCollector`: Abstract class with HTTP request functionality, rate limiting, and retry logic
  - `NewsCollector`: Base class for news source collectors with RSS feed support
  - `PoliticianCollector`: Base class for politician data collectors

#### `/data_collection/politicians/eduskunta_collector.py`
- **Purpose**: Collects Finnish Parliament (Eduskunta) politician data
- **Key Components**:
  - `EduskuntaCollector`: Fetches politician data from official API and JSON files
  - Includes fallback web scraping when API is unavailable
  - Handles image retrieval with multiple fallback strategies

#### `/data_collection/politicians/kuntaliitto_collector.py`
- **Purpose**: Collects municipal politician data
- **Key Components**:
  - `KuntalittoCollector`: Fetches local government politician data

#### `/data_collection/news/helsingin_sanomat_collector.py`
- **Purpose**: Collects news from Helsingin Sanomat
- **Key Components**:
  - `HSCollector`: Fetches and parses news articles with politician mentions

#### `/data_collection/administrative/statistics_finland_collector.py`
- **Purpose**: Collects official statistics and administrative data
- **Key Components**:
  - `StatisticsFinlandCollector`: Fetches province/region data from official PxWeb API
  - Handles population, area, and demographic data

### Database

#### `/database/neo4j_integration.py`
- **Purpose**: Core database integration layer
- **Key Components**:
  - `Neo4jConnectionManager`: Manages async connection pooling with circuit breaker
  - `DataTransformer`: Transforms collected data for database storage
  - `Neo4jWriter`: Handles batch creation of entities and relationships
  - `Neo4jAnalytics`: Provides advanced political analysis queries

#### `/database/collector_neo4j_bridge.py`
- **Purpose**: Bridges data collectors with Neo4j storage
- **Key Components**:
  - `CollectorNeo4jBridge`: Orchestrates data collection and storage
  - Handles error recovery and partial data persistence

#### `/database/unified_news_enricher.py`
- **Purpose**: Enriches politician data with news articles
- **Key Components**:
  - `UnifiedNewsEnricher`: Aggregates news from all sources for a politician
  - Handles deduplication and relationship creation

### AI Pipeline

#### `/ai_pipeline/agent_orchestrator.py`
- **Purpose**: Coordinates AI agents and workflows
- **Key Components**:
  - `AgentOrchestrator`: Central coordinator for specialized agents
  - Manages shared memory for cross-agent communication
  - Handles fault tolerance and environment validation

#### `/ai_pipeline/agents/analysis_agent.py`
- **Purpose**: Performs AI-powered content analysis
- **Key Components**:
  - `AnalysisAgent`: Analyzes politician profiles, voting patterns, and news
  - Generates insights, summaries, and comparative analyses
  - Uses security decorators for safe operation

#### `/ai_pipeline/agents/query_agent.py`
- **Purpose**: Handles natural language queries about politicians
- **Key Components**:
  - `QueryAgent`: Translates natural language to database queries
  - Provides conversational responses to user questions

#### `/ai_pipeline/memory/shared_memory.py`
- **Purpose**: Provides shared state between agents
- **Key Components**:
  - `SharedMemory`: Manages agent communication and context
  - Persists important information across agent runs

### API

#### `/api/main.py`
- **Purpose**: FastAPI application entry point
- **Key Components**:
  - Application configuration and middleware setup
  - Router registration and OpenAPI documentation

#### `/api/routers/politicians.py`
- **Purpose**: Endpoints for politician data
- **Key Components**:
  - List, search, and detail endpoints for politicians
  - Province-based politician filtering
  - Unified details endpoint with news integration

#### `/api/routers/news.py`
- **Purpose**: Endpoints for news articles
- **Key Components**:
  - News search and filtering endpoints
  - Politician-specific news retrieval

#### `/api/routers/analysis.py`
- **Purpose**: Endpoints for AI analysis
- **Key Components**:
  - Custom analysis endpoint with async processing
  - Status checking for long-running analyses

#### `/api/routers/provinces.py`
- **Purpose**: Endpoints for province/region data
- **Key Components**:
  - Province listing and detail endpoints
  - Province statistics and politician counts

### Frontend

#### `/frontend/app.py`
- **Purpose**: Streamlit application entry point
- **Key Components**:
  - Page routing and configuration
  - Session state initialization

#### `/frontend/dashboard/main_dashboard.py`
- **Purpose**: Main dashboard interface
- **Key Components**:
  - `MainDashboard`: Integrates all UI components
  - Tab-based navigation between views
  - Politician grid display with pagination

#### `/frontend/components/map/finland_map.py`
- **Purpose**: Interactive map visualization
- **Key Components**:
  - `FinlandMap`: Folium-based map of Finnish provinces
  - Province selection and highlighting
  - Population and politician density visualization

#### `/frontend/components/chat/enhanced_politician_chat.py`
- **Purpose**: AI assistant chat interface
- **Key Components**:
  - `EnhancedPoliticianChat`: Chat UI with AI integration
  - Research mode with visualization tools
  - Direct API integration with polling for async responses

#### `/frontend/components/analysis/analysis_dashboard.py`
- **Purpose**: Detailed politician analysis view
- **Key Components**:
  - `AnalysisDashboard`: Displays comprehensive politician details
  - News article visualization
  - Wikipedia integration

### Security

#### `/ai_pipeline/security/security_decorators.py`
- **Purpose**: Security controls for AI components
- **Key Components**:
  - `secure_prompt`: Decorator for prompt injection prevention
  - `secure_output`: Decorator for output sanitization
  - `verify_response`: Decorator for response verification

#### `/ai_pipeline/security/prompt_guard.py`
- **Purpose**: Prevents prompt injection attacks
- **Key Components**:
  - `PromptGuard`: Detects and mitigates prompt injection attempts
  - Pattern-based detection for common attack vectors

#### `/ai_pipeline/security/output_sanitizer.py`
- **Purpose**: Sanitizes AI outputs for safety
- **Key Components**:
  - `OutputSanitizer`: Detects and redacts sensitive information
  - Prevents unintended data disclosure

#### `/ai_pipeline/security/verification_system.py`
- **Purpose**: Verifies AI responses for accuracy
- **Key Components**:
  - `VerificationSystem`: Checks responses for factual accuracy
  - Prevents hallucinations and misinformation

### Testing

#### `/tests/api/test_api_endpoints.py`
- **Purpose**: Tests API endpoints
- **Key Components**: Unit tests for API functionality

#### `/tests/features/test_e2e_workflows.py`
- **Purpose**: End-to-end feature tests
- **Key Components**: Complete workflow testing from data collection to frontend

#### `/tests/integration/test_system_integration.py`
- **Purpose**: Tests component integration
- **Key Components**: Verifies proper interaction between system components

## Key Workflows

### Politician Data Collection Workflow
1. `CollectorNeo4jBridge` initiates collection from multiple sources
2. Each collector (Eduskunta, Kuntaliitto) fetches data
3. `DataTransformer` standardizes the collected data
4. `Neo4jWriter` stores politicians in the database
5. API endpoints make data available to frontend

### News Analysis Workflow
1. News collectors fetch articles from Finnish news sources
2. `UnifiedNewsEnricher` aggregates news for specific politicians
3. `AnalysisAgent` performs sentiment and topic analysis
4. Results are stored in Neo4j with relationships to politicians
5. Frontend displays news with analysis in politician details

### User Query Workflow
1. User submits question via `EnhancedPoliticianChat`
2. Request is sent to `/analysis/custom` API endpoint
3. `AgentOrchestrator` routes query to appropriate agent
4. `QueryAgent` processes query and generates response
5. Response is returned to frontend with optional visualization

## Configuration

### Environment Variables
- `NEO4J_URI`: Neo4j database connection URI
- `NEO4J_USER`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `NEO4J_DATABASE`: Neo4j database name
- `OPENAI_API_KEY`: OpenAI API key for AI pipeline
- `API_BASE_URL`: Base URL for API (default: http://localhost:8000/api/v1)

### API Configuration
- API is configured in `/api/core/config.py`
- Default API prefix is `/api/v1`
- CORS is enabled for all origins in development

## Development Guide

### Running the System
1. Start Neo4j database:
   ```
   docker-compose up -d neo4j
   ```

2. Start the API:
   ```
   uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Start the frontend:
   ```
   streamlit run frontend/app.py
   ```

### Common Development Tasks

#### Adding a New Data Collector
1. Create a new collector class extending `BaseCollector`, `NewsCollector`, or `PoliticianCollector`
2. Implement required abstract methods
3. Register in `CollectorNeo4jBridge` for automatic integration

#### Adding a New API Endpoint
1. Create or modify a router file in `/api/routers/`
2. Define endpoint function with appropriate path and method
3. Register router in `/api/main.py`

#### Adding a New Frontend Component
1. Create component class in appropriate `/frontend/components/` subdirectory
2. Implement `render()` method for Streamlit integration
3. Add to relevant dashboard in `/frontend/dashboard/`

## Known Issues and Solutions

### Issue: Web Scraping Reliability
- **Problem**: EduskuntaCollector CSS selectors need updating for current website structure
- **Solution**: Inspect current Eduskunta website HTML and update selectors in `_scrape_current_mps()` method

### Issue: Relationship Type Inconsistency
- **Problem**: Mismatch between Neo4j Enum (MENTIONS) and usage (MENTIONED_IN)
- **Solution**: Standardize by either adding MENTIONED_IN to RelationshipType Enum or using MENTIONS consistently

### Issue: Frontend State Management
- **Problem**: Session state initialization issues in some components
- **Solution**: Ensure all components initialize their session state variables in `__init__` methods

### Issue: API URL Construction
- **Problem**: Inconsistent API URL formatting in frontend components
- **Solution**: Use consistent API base URL with proper prefix handling

### Issue: Province Data Sourcing
- **Problem**: Currently using hardcoded province metadata
- **Solution**: Implement dynamic fetching from Statistics Finland API

## Completion Status

The Finnish Politician Analysis System is approximately **85% complete** with most core functionality working well. The remaining work is primarily focused on reliability improvements and optimization rather than new feature development.
