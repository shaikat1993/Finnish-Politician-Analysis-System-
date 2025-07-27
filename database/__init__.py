"""
Finnish Political Analysis System - Database Module
Senior-Level Database Architecture with Clean Separation of Concerns
"""

# Core database components (production-ready)
from .neo4j_integration import (
    Neo4jConnectionManager,
    Neo4jWriter, 
    Neo4jAnalytics,
    DataTransformer,
    EntityType,
    RelationshipType,
    get_neo4j_manager,
    get_neo4j_writer,
    get_neo4j_analytics,
    health_check
)

# Data collection bridge
from .collector_neo4j_bridge import (
    CollectorNeo4jBridge,
    run_full_data_ingestion,
    quick_politician_sync,
    quick_news_sync
)

# Schema management
from .setup_neo4j_schema import (
    Neo4jSchemaSetup,
    setup_neo4j_schema,
    verify_neo4j_schema
)

__version__ = "1.0.0"
__author__ = "Finnish Political Analysis System"

# Public API - what external modules should use
__all__ = [
    # Connection Management (Async, Production-Ready)
    "Neo4jConnectionManager",
    "get_neo4j_manager",
    "health_check",
    
    # Data Operations (CRUD, Analytics)
    "Neo4jWriter",
    "Neo4jAnalytics", 
    "get_neo4j_writer",
    "get_neo4j_analytics",
    
    # Data Transformation
    "DataTransformer",
    "EntityType",
    "RelationshipType",
    
    # Data Collection Integration
    "CollectorNeo4jBridge",
    "run_full_data_ingestion",
    "quick_politician_sync", 
    "quick_news_sync",
    
    # Schema Management
    "Neo4jSchemaSetup",
    "setup_neo4j_schema",
    "verify_neo4j_schema"
]

# Module-level configuration
DEFAULT_CONFIG = {
    "connection_pool_size": 10,
    "connection_timeout": 30,
    "query_timeout": 60,
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5
}

def get_database_info():
    """Get database module information"""
    return {
        "version": __version__,
        "components": len(__all__),
        "architecture": "Async Neo4j with Connection Pooling",
        "features": [
            "Production-grade connection management",
            "Circuit breaker pattern for resilience", 
            "Comprehensive error handling and retry logic",
            "Data transformation and validation pipeline",
            "Advanced analytics and network analysis",
            "Multi-source data collection integration",
            "Automated schema setup and verification"
        ]
    }
