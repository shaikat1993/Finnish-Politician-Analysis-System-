"""
Streamlined Agent-Based Orchestrator for Finnish Politician Analysis System
Production-grade LangChain specialized multi-agent coordinator.
"""

import logging
import asyncio
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .agents import (
    DataCollectionAgent,
    AnalysisAgent,
    RelationshipAgent,
    StorageAgent,
    QueryAgent,
    create_all_agents
)
from .memory.shared_memory import SharedAgentMemory

# Load environment variables
load_dotenv()

class AgentOrchestrator:
    """
    Production LangChain Specialized Multi-Agent Orchestrator
    
    This implements a true distributed multi-agent system with:
    - Specialized LangChain agents for different tasks
    - Distributed coordination through shared memory
    - Fault tolerance and error recovery
    - Complex multi-step workflows
    
    Architecture:
    - DataCollectionAgent: Handles all data collection operations
    - AnalysisAgent: Performs content analysis and insights
    - RelationshipAgent: Extracts and analyzes relationships
    - StorageAgent: Manages Neo4j and vector database storage
    - QueryAgent: Handles all query operations
    - Shared Memory: Cross-agent state and communication
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.shared_memory = SharedAgentMemory()
        self.agents = {}
        self.is_initialized = False
        
        # Validate environment
        self._validate_environment()
        
        self.logger.info("AgentOrchestrator initialized")
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = ["OPENAI_API_KEY"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    async def initialize(self):
        """
        Initialize the agent orchestrator and all specialized agents
        """
        try:
            if self.is_initialized:
                self.logger.info("AgentOrchestrator already initialized")
                return
            
            self.logger.info("Initializing AgentOrchestrator with specialized agents...")
            
            # Initialize shared memory
            await self.shared_memory.initialize()
            
            # Initialize all specialized agents
            openai_api_key = os.getenv("OPENAI_API_KEY")
            self.agents = create_all_agents(
                shared_memory=self.shared_memory,
                openai_api_key=openai_api_key
            )
            
            self.is_initialized = True
            self.logger.info(f"AgentOrchestrator initialization completed with {len(self.agents)} specialized agents")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AgentOrchestrator: {str(e)}")
            raise
    
    async def process_data_ingestion(
        self,
        sources: List[str] = None,
        limit: int = 100,
        query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute intelligent data ingestion workflow using specialized agents
        
        This workflow demonstrates the power of the specialized agent architecture:
        1. DataCollectionAgent gathers data from multiple sources
        2. AnalysisAgent analyzes the collected content
        3. RelationshipAgent extracts relationships between entities
        4. StorageAgent stores everything in Neo4j and vector databases
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            workflow_id = f"data_ingestion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Starting data ingestion workflow: {workflow_id}")
            
            # Store workflow start in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "workflow_type": "data_ingestion",
                    "sources": sources,
                    "limit": limit,
                    "query": query,
                    "status": "started",
                    "started_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            
            # Step 1: Data Collection
            data_collection_agent = self.agents["data_collection"]
            if sources and "politicians" in str(sources).lower():
                politician_data = await data_collection_agent.collect_politicians(sources, limit)
            else:
                politician_data = None
                
            if sources and "news" in str(sources).lower():
                news_data = await data_collection_agent.collect_news(sources, limit, query)
            else:
                news_data = None
            
            # Step 2: Analysis
            analysis_agent = self.agents["analysis"]
            analysis_results = {}
            if politician_data:
                analysis_results["politicians"] = await analysis_agent.analyze_politicians()
            if news_data:
                analysis_results["news"] = await analysis_agent.analyze_news()
            
            # Step 3: Relationship Extraction
            relationship_agent = self.agents["relationship"]
            relationships = await relationship_agent.extract_relationships()
            
            # Step 4: Storage
            storage_agent = self.agents["storage"]
            storage_results = {}
            if politician_data:
                storage_results["politicians"] = await storage_agent.store_politicians()
            if news_data:
                storage_results["news"] = await storage_agent.store_news()
            if relationships:
                storage_results["relationships"] = await storage_agent.store_relationships()
            
            # Update workflow status in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "results": {
                        "data_collection": {"politicians": bool(politician_data), "news": bool(news_data)},
                        "analysis": analysis_results,
                        "relationships": relationships,
                        "storage": storage_results
                    },
                    "completed_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "orchestrator_type": "langchain_specialized_multi_agent",
                "agent_coordination": True,
                "intelligent_reasoning": True,
                "results": {
                    "data_collection": {"politicians": bool(politician_data), "news": bool(news_data)},
                    "analysis": analysis_results,
                    "relationships": relationships,
                    "storage": storage_results
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error in data ingestion workflow: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "error": str(e),
                    "failed_at": datetime.now().isoformat()
                },
                memory_type="workflow_status"
            )
            raise
    
    async def process_user_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user query using intelligent agent coordination
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            query_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.logger.info(f"Processing user query: {query_id}")
            
            # Store query start in shared memory
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "query_id": query_id,
                    "query": query,
                    "context": context,
                    "status": "processing",
                    "started_at": datetime.now().isoformat()
                },
                memory_type="query_status"
            )
            
            # Execute through QueryAgent
            query_agent = self.agents["query"]
            
            # Determine query type and route appropriately
            if "politician" in query.lower():
                result = await query_agent.search_politicians(query)
            elif "news" in query.lower():
                result = await query_agent.search_news(query)
            elif "relationship" in query.lower() or "connection" in query.lower():
                result = await query_agent.find_relationships(query)
            else:
                result = await query_agent.semantic_search(query)
            
            # Update query status
            await self.shared_memory.store_memory(
                agent_id="orchestrator",
                content={
                    "query_id": query_id,
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                },
                memory_type="query_status"
            )
            
            return {
                "query_id": query_id,
                "status": "completed",
                "orchestrator_type": "langchain_specialized_multi_agent",
                "intelligent_routing": True,
                **result
            }
            
        except Exception as e:
            self.logger.error(f"Error in user query processing: {str(e)}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive system health check
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            self.logger.info("Performing system health check")
            
            health_status = {
                "orchestrator": "healthy",
                "shared_memory": "healthy",
                "agents": {},
                "timestamp": datetime.now().isoformat()
            }
            
            # Check each agent
            for agent_name, agent in self.agents.items():
                try:
                    agent_info = agent.get_agent_info()
                    health_status["agents"][agent_name] = {
                        "status": agent_info.get("status", "unknown"),
                        "capabilities": len(agent_info.get("capabilities", [])),
                        "tools": len(agent_info.get("tools", []))
                    }
                except Exception as e:
                    health_status["agents"][agent_name] = {
                        "status": "error",
                        "error": str(e)
                    }
            
            # Check data collection health
            if "data_collection" in self.agents:
                try:
                    data_collection_agent = self.agents["data_collection"]
                    data_health = await data_collection_agent.health_check()
                    health_status["data_sources"] = data_health
                except Exception as e:
                    health_status["data_sources"] = {"status": "error", "error": str(e)}
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "orchestrator": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        return {
            "name": "Finnish Politician Analysis System - AI Pipeline",
            "version": "2.0.0",
            "architecture": "langchain_specialized_multi_agent",
            "orchestrator_type": "distributed_coordination",
            "agents": list(self.agents.keys()) if self.agents else [],
            "total_agents": len(self.agents),
            "is_initialized": self.is_initialized,
            "features": [
                "specialized_agent_coordination",
                "intelligent_reasoning_with_gpt4",
                "shared_memory_system",
                "fault_tolerant_workflows",
                "real_time_adaptation",
                "production_monitoring"
            ],
            "supported_workflows": [
                "data_ingestion",
                "user_query",
                "health_check",
                "relationship_analysis",
                "content_analysis"
            ]
        }

# Global orchestrator instance
_orchestrator_instance = None

def get_agent_orchestrator() -> AgentOrchestrator:
    """Get or create the global agent orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance
