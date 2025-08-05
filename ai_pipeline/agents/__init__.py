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

from .analysis_agent import AnalysisAgent
from .query_agent import QueryAgent

__all__ = [
    'AnalysisAgent',
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

def get_agent_system_info():
    """Get information about the agent system"""
    return {
        "version": AGENT_SYSTEM_VERSION,
        "architecture": "LangChain Specialized Multi-Agent",
        "supported_workflows": SUPPORTED_WORKFLOWS,
        "agent_types": [
            "AnalysisAgent",
            "QueryAgent"
        ],
        "coordination_model": "distributed_with_shared_memory",
        "total_agents": 2
    }




