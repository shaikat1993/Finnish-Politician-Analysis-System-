"""
DataCollectionAgent - Specialized LangChain Agent for Data Collection
Handles all data collection operations from multiple Finnish political sources.
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

from ..tools.coordination_tools import DataCollectionTool
from ..memory.shared_memory import SharedAgentMemory

class DataCollectionAgent:
    """
    Specialized LangChain agent for data collection operations.
    
    Responsibilities:
    - Collect politician data from Eduskunta, Wikipedia, and other sources
    - Collect news articles from YLE, Helsingin Sanomat, and other media
    - Validate and clean collected data
    - Store raw data in shared memory for processing
    - Monitor data source health and availability
    """
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None):
        self.agent_id = "data_collection_agent"
        self.shared_memory = shared_memory
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,
            openai_api_key=openai_api_key
        )
        
        # Initialize tools
        self.tools = [DataCollectionTool()]
        
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
        
        self.logger.info(f"DataCollectionAgent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the data collection agent"""
        return """You are a specialized Data Collection Agent for the Finnish Politician Analysis System.

Your primary responsibilities:
1. Collect politician data from multiple sources (Eduskunta, Wikipedia, party websites)
2. Collect news articles from Finnish media (YLE, Helsingin Sanomat, Iltalehti, etc.)
3. Validate data quality and completeness
4. Handle API rate limits and errors gracefully
5. Store collected data in shared memory for other agents

Key principles:
- Always validate data before storing
- Handle errors gracefully and retry when appropriate
- Respect API rate limits and terms of service
- Provide detailed status updates on collection progress
- Prioritize data quality over quantity

When collecting data:
- Use the DataCollectionTool for all collection operations
- Specify appropriate limits to avoid overwhelming sources
- Include relevant search queries when needed
- Log all collection activities for monitoring

You work as part of a multi-agent system. Store your results in shared memory so other agents can process them."""

    async def collect_politicians(self, sources: List[str] = None, limit: int = 50) -> Dict[str, Any]:
        """
        Collect politician data from specified sources
        
        Args:
            sources: List of sources to collect from (default: all available)
            limit: Maximum number of politicians per source
            
        Returns:
            Collection results with status and data
        """
        try:
            if not sources:
                sources = ["eduskunta", "wikipedia"]
            
            self.logger.info(f"Starting politician collection from sources: {sources}")
            
            # Execute collection using agent
            result = await self.executor.ainvoke({
                "input": f"Collect politician data from sources: {sources} with limit: {limit}"
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_collection",
                    "sources": sources,
                    "limit": limit,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="collection_result"
            )
            
            self.logger.info("Politician collection completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in politician collection: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_collection",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def collect_news(self, sources: List[str] = None, limit: int = 100, query: str = None) -> Dict[str, Any]:
        """
        Collect news articles from specified sources
        
        Args:
            sources: List of news sources to collect from
            limit: Maximum number of articles per source
            query: Optional search query
            
        Returns:
            Collection results with status and data
        """
        try:
            if not sources:
                sources = ["yle", "helsingin_sanomat"]
            
            self.logger.info(f"Starting news collection from sources: {sources}")
            
            # Execute collection using agent
            result = await self.executor.ainvoke({
                "input": f"Collect news articles from sources: {sources} with limit: {limit} and query: {query}"
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_collection",
                    "sources": sources,
                    "limit": limit,
                    "query": query,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="collection_result"
            )
            
            self.logger.info("News collection completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in news collection: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_collection",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all data sources
        
        Returns:
            Health status of all data sources
        """
        try:
            self.logger.info("Starting data source health check")
            
            # Execute health check using agent
            result = await self.executor.ainvoke({
                "input": "Perform health check on all data sources"
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "health_check",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="health_status"
            )
            
            self.logger.info("Health check completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "DataCollectionAgent",
            "capabilities": [
                "politician_data_collection",
                "news_article_collection", 
                "data_source_health_monitoring",
                "data_validation",
                "rate_limit_handling"
            ],
            "tools": [tool.name for tool in self.tools],
            "status": "active"
        }
