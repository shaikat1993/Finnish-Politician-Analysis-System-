"""
LangChain Tools for Multi-Agent Coordination

This module provides LangChain-native tools that enable the SupervisorAgent
to coordinate with specialized agents and execute complex workflows.

Tools follow LangChain BaseTool patterns and provide:
- Structured input/output schemas
- Async execution capabilities
- Error handling and logging
- Integration with existing FPAS components
"""

from .coordination_tools import (
    DataCollectionTool,
    AnalysisTool,
    RelationshipTool,
    StorageTool,
    QueryTool
)

__all__ = [
    'DataCollectionTool',
    'AnalysisTool', 
    'RelationshipTool',
    'StorageTool',
    'QueryTool'
]

# Tool registry for dynamic loading
TOOL_REGISTRY = {
    'data_collection': DataCollectionTool,
    'analysis': AnalysisTool,
    'relationship': RelationshipTool,
    'storage': StorageTool,
    'query': QueryTool
}

def get_all_tools():
    """Get instances of all available tools"""
    return [tool_class() for tool_class in TOOL_REGISTRY.values()]

def get_tool_by_name(tool_name: str):
    """Get a specific tool by name"""
    if tool_name in TOOL_REGISTRY:
        return TOOL_REGISTRY[tool_name]()
    raise ValueError(f"Unknown tool: {tool_name}")
