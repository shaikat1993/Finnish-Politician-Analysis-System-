"""
AI Pipeline for Finnish Politician Analysis System
Production-grade LangChain Multi-Agent System for intelligent political data analysis.

This module implements a sophisticated multi-agent architecture using LangChain's
agent framework, featuring:

- SupervisorAgent: Master agent with GPT-4 reasoning for workflow coordination
- Specialized Tools: LangChain BaseTool implementations for data collection, 
  analysis, relationship extraction, storage, and querying
- Shared Memory: Inter-agent communication and state management
- Agent Orchestrator: Production-grade workflow coordinator
- Fault Tolerance: Error recovery and graceful degradation
- Performance Monitoring: Agent statistics and system health tracking

Architecture follows LangChain best practices for enterprise AI systems.
"""

# Core Agent System
from .agents import (
    DataCollectionAgent,
    AnalysisAgent,
    RelationshipAgent,
    StorageAgent,
    QueryAgent,
    create_all_agents,
    create_agent
)
from .agent_orchestrator import AgentOrchestrator, get_agent_orchestrator

# LangChain Tools for Agent Coordination
from .tools import (
    DataCollectionTool,
    AnalysisTool,
    RelationshipTool,
    StorageTool,
    QueryTool
)

# Shared Memory System
from .memory import SharedAgentMemory, MemoryEntry

# Legacy Components (maintained for backward compatibility)
from .document_processors import PoliticianProcessor, NewsProcessor, RelationshipExtractor
from .embeddings import EmbeddingManager, VectorStoreManager
from .storage import Neo4jWriter, VectorWriter

# Agent System Metadata
__version__ = "2.0.0"
__architecture__ = "langchain_multi_agent"
__agent_types__ = [
    "SupervisorAgent",
    "DataCollectionAgent", 
    "AnalysisAgent",
    "RelationshipAgent",
    "StorageAgent",
    "QueryAgent"
]

# Primary Exports (New LangChain Specialized Multi-Agent System)
__all__ = [
    # Core Agent System
    'DataCollectionAgent',
    'AnalysisAgent',
    'RelationshipAgent',
    'StorageAgent',
    'QueryAgent',
    'create_all_agents',
    'create_agent',
    'AgentOrchestrator',
    'get_agent_orchestrator',
    
    # LangChain Tools
    'DataCollectionTool',
    'AnalysisTool',
    'RelationshipTool',
    'StorageTool',
    'QueryTool',
    
    # Memory System
    'SharedAgentMemory',
    'MemoryEntry',
    
    # Legacy Components (backward compatibility)
    'PoliticianProcessor',
    'NewsProcessor',
    'RelationshipExtractor',
    'EmbeddingManager',
    'VectorStoreManager',
    'Neo4jWriter',
    'VectorWriter',
    
    # Metadata
    '__version__',
    '__architecture__',
    '__agent_types__'
]

# Convenience Functions
def get_system_info():
    """
    Get comprehensive information about the AI Pipeline system
    
    Returns:
        Dict containing system architecture, version, and capabilities
    """
    return {
        "name": "Finnish Politician Analysis System - AI Pipeline",
        "version": __version__,
        "architecture": __architecture__,
        "agent_types": __agent_types__,
        "features": [
            "langchain_multi_agent_coordination",
            "intelligent_reasoning_with_gpt4",
            "shared_memory_system",
            "fault_tolerant_workflows",
            "real_time_adaptation",
            "production_monitoring",
            "backward_compatibility"
        ],
        "supported_workflows": [
            "data_ingestion",
            "user_query",
            "health_check",
            "relationship_analysis",
            "content_analysis"
        ]
    }

def create_agent_system(openai_api_key: str = None):
    """
    Create and initialize the complete specialized agent system
    
    Args:
        openai_api_key: OpenAI API key (optional, will use env var if not provided)
    
    Returns:
        Initialized AgentOrchestrator instance with all specialized agents
    """
    if openai_api_key:
        import os
        os.environ["OPENAI_API_KEY"] = openai_api_key
    
    orchestrator = get_agent_orchestrator()
    return orchestrator

def get_available_agents():
    """
    Get list of all available specialized agents
    
    Returns:
        List of agent types and their capabilities
    """
    return {
        "data_collection": {
            "class": "DataCollectionAgent",
            "capabilities": [
                "politician_data_collection",
                "news_article_collection",
                "data_source_health_monitoring",
                "data_validation",
                "rate_limit_handling"
            ]
        },
        "analysis": {
            "class": "AnalysisAgent",
            "capabilities": [
                "politician_profile_analysis",
                "voting_pattern_analysis",
                "news_sentiment_analysis",
                "topic_modeling",
                "trend_identification",
                "comparative_analysis",
                "insight_generation"
            ]
        },
        "relationship": {
            "class": "RelationshipAgent",
            "capabilities": [
                "relationship_extraction",
                "political_network_analysis",
                "coalition_detection",
                "alliance_identification",
                "relationship_change_tracking",
                "graph_data_preparation"
            ]
        },
        "storage": {
            "class": "StorageAgent",
            "capabilities": [
                "neo4j_graph_storage",
                "vector_database_storage",
                "relationship_graph_creation",
                "data_integrity_management",
                "storage_error_handling",
                "duplicate_data_management"
            ]
        },
        "query": {
            "class": "QueryAgent",
            "capabilities": [
                "neo4j_graph_queries",
                "vector_semantic_search",
                "natural_language_query_processing",
                "query_optimization",
                "result_formatting",
                "relationship_traversal"
            ]
        }
    }
