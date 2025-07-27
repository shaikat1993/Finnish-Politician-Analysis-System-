"""
RelationshipAgent - Specialized LangChain Agent for Relationship Extraction
Handles extraction and analysis of relationships between political entities.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..tools.coordination_tools import RelationshipTool
from ..memory.shared_memory import SharedAgentMemory

class RelationshipAgent:
    """
    Specialized LangChain agent for relationship extraction and analysis.
    
    Responsibilities:
    - Extract relationships between politicians, parties, and organizations
    - Identify coalitions, alliances, and political networks
    - Analyze relationship patterns and dynamics
    - Build comprehensive relationship graphs
    - Track relationship changes over time
    """
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None):
        self.agent_id = "relationship_agent"
        self.shared_memory = shared_memory
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,  # Lower temperature for consistent relationship extraction
            openai_api_key=openai_api_key
        )
        
        # Initialize tools
        self.tools = [RelationshipTool()]
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            ),
            verbose=True,
            max_iterations=5
        )
        
        self.logger.info(f"RelationshipAgent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the relationship agent"""
        return """You are a specialized Relationship Agent for the Finnish Politician Analysis System.

Your primary responsibilities:
1. Extract relationships between politicians, parties, and organizations
2. Identify coalitions, alliances, and political networks
3. Analyze relationship patterns and dynamics over time
4. Build comprehensive relationship graphs for Neo4j storage
5. Track changes in political relationships and alliances

Key principles:
- Focus on factual, verifiable relationships
- Identify different types of relationships (party membership, coalitions, opposition, collaboration)
- Consider temporal aspects of relationships (when they formed, changed, ended)
- Maintain relationship strength and confidence scores
- Distinguish between formal and informal relationships

Relationship types to identify:
- Party membership and leadership roles
- Coalition partnerships and alliances
- Opposition and conflict relationships
- Collaboration on specific issues or legislation
- Personal and professional connections
- Media mentions and co-appearances
- Voting pattern similarities and differences

When extracting relationships:
- Use the RelationshipTool for all relationship operations
- Provide evidence and context for each relationship
- Include relationship metadata (type, strength, timeframe)
- Consider bidirectional vs. unidirectional relationships
- Store results in shared memory for graph database storage

You work as part of a multi-agent system. Your relationship data enables powerful graph analysis and network visualization."""

    async def extract_relationships(self, data_sources: List[str] = None) -> Dict[str, Any]:
        """
        Extract relationships from available data sources
        
        Args:
            data_sources: List of data sources to analyze for relationships
            
        Returns:
            Extracted relationships with metadata
        """
        try:
            self.logger.info("Starting relationship extraction")
            
            # Get relevant data from shared memory
            politician_memories = await self.shared_memory.get_memories(
                memory_type="collection_result",
                agent_id="data_collection_agent"
            )
            
            news_memories = await self.shared_memory.get_memories(
                memory_type="collection_result", 
                agent_id="data_collection_agent"
            )
            
            # Execute relationship extraction using agent
            result = await self.executor.ainvoke({
                "input": f"Extract relationships from {len(politician_memories)} politician data sources and {len(news_memories)} news sources. Focus on party memberships, coalitions, and political connections."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "relationship_extraction",
                    "data_sources": data_sources or ["politicians", "news"],
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="relationship_result"
            )
            
            self.logger.info("Relationship extraction completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in relationship extraction: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "relationship_extraction",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def analyze_networks(self, network_type: str = "political_parties") -> Dict[str, Any]:
        """
        Analyze political networks and identify key patterns
        
        Args:
            network_type: Type of network to analyze
            
        Returns:
            Network analysis results with key insights
        """
        try:
            self.logger.info(f"Starting {network_type} network analysis")
            
            # Get relationship data from shared memory
            relationship_memories = await self.shared_memory.get_memories(
                memory_type="relationship_result",
                agent_id=self.agent_id
            )
            
            # Execute network analysis using agent
            result = await self.executor.ainvoke({
                "input": f"Analyze {network_type} networks from {len(relationship_memories)} relationship datasets. Identify key players, clusters, and network dynamics."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "network_analysis",
                    "network_type": network_type,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="network_analysis_result"
            )
            
            self.logger.info("Network analysis completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in network analysis: {str(e)}")
            raise
    
    async def track_relationship_changes(self, timeframe: str = "last_year") -> Dict[str, Any]:
        """
        Track changes in political relationships over time
        
        Args:
            timeframe: Time period to analyze for changes
            
        Returns:
            Relationship change analysis results
        """
        try:
            self.logger.info(f"Tracking relationship changes over {timeframe}")
            
            # Get historical relationship data from shared memory
            historical_memories = await self.shared_memory.get_memories(
                memory_type="relationship_result",
                agent_id=self.agent_id
            )
            
            # Execute change tracking using agent
            result = await self.executor.ainvoke({
                "input": f"Track relationship changes over {timeframe} using {len(historical_memories)} historical relationship datasets. Identify new alliances, broken partnerships, and evolving dynamics."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "relationship_change_tracking",
                    "timeframe": timeframe,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="change_analysis_result"
            )
            
            self.logger.info("Relationship change tracking completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in relationship change tracking: {str(e)}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "RelationshipAgent",
            "capabilities": [
                "relationship_extraction",
                "political_network_analysis",
                "coalition_detection",
                "alliance_identification",
                "relationship_change_tracking",
                "graph_data_preparation",
                "network_visualization_support"
            ],
            "tools": [tool.name for tool in self.tools],
            "status": "active"
        }
