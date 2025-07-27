"""
LangChain Multi-Agent System for Finnish Politician Analysis System (FPAS)

This module implements a production-grade multi-agent architecture using LangChain's
agent framework, featuring:

- Specialized agents for data collection, analysis, relationships, storage, and queries
- Inter-agent communication through shared memory and coordination tools
- LangChain-native agent patterns with proper tool integration
- Production monitoring and error handling
- Distributed agent coordination without central supervisor

Architecture follows LangChain best practices for enterprise AI systems.
"""

from .data_collection_agent import DataCollectionAgent
from .analysis_agent import AnalysisAgent
from .relationship_agent import RelationshipAgent
from .storage_agent import StorageAgent
from .query_agent import QueryAgent

__all__ = [
    'DataCollectionAgent',
    'AnalysisAgent', 
    'RelationshipAgent',
    'StorageAgent',
    'QueryAgent'
]

# Agent system metadata
AGENT_SYSTEM_VERSION = "2.0.0"
SUPPORTED_WORKFLOWS = [
    "data_collection",
    "content_analysis",
    "relationship_extraction",
    "data_storage",
    "semantic_search",
    "graph_queries",
    "multi_agent_coordination"
]

# Agent registry for dynamic loading
AGENT_REGISTRY = {
    'data_collection': DataCollectionAgent,
    'analysis': AnalysisAgent,
    'relationship': RelationshipAgent,
    'storage': StorageAgent,
    'query': QueryAgent
}

def get_agent_system_info():
    """Get information about the agent system"""
    return {
        "version": AGENT_SYSTEM_VERSION,
        "architecture": "LangChain Specialized Multi-Agent",
        "supported_workflows": SUPPORTED_WORKFLOWS,
        "agent_types": [
            "DataCollectionAgent", 
            "AnalysisAgent",
            "RelationshipAgent",
            "StorageAgent",
            "QueryAgent"
        ],
        "coordination_model": "distributed_with_shared_memory",
        "total_agents": len(AGENT_REGISTRY)
    }

def create_agent(agent_type: str, shared_memory, openai_api_key: str = None):
    """Create an agent instance by type"""
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(f"Unknown agent type: {agent_type}. Available: {list(AGENT_REGISTRY.keys())}")
    
    agent_class = AGENT_REGISTRY[agent_type]
    return agent_class(shared_memory=shared_memory, openai_api_key=openai_api_key)

def create_all_agents(shared_memory, openai_api_key: str = None):
    """Create all agent instances"""
    agents = {}
    for agent_type, agent_class in AGENT_REGISTRY.items():
        agents[agent_type] = agent_class(shared_memory=shared_memory, openai_api_key=openai_api_key)
    return agents
