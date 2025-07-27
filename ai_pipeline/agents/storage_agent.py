"""
StorageAgent - Specialized LangChain Agent for Data Storage
Handles all storage operations to Neo4j graph database and vector databases.
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

from ..tools.coordination_tools import StorageTool
from ..memory.shared_memory import SharedAgentMemory

class StorageAgent:
    """
    Specialized LangChain agent for data storage operations.
    
    Responsibilities:
    - Store processed politician data in Neo4j graph database
    - Store news articles in Neo4j with proper relationships
    - Store relationship data as graph connections
    - Manage vector database storage for semantic search
    - Ensure data consistency and integrity
    - Handle storage errors and retries
    """
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None):
        self.agent_id = "storage_agent"
        self.shared_memory = shared_memory
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.1,  # Low temperature for consistent storage operations
            openai_api_key=openai_api_key
        )
        
        # Initialize tools
        self.tools = [StorageTool()]
        
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
        
        self.logger.info(f"StorageAgent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the storage agent"""
        return """You are a specialized Storage Agent for the Finnish Politician Analysis System.

Your primary responsibilities:
1. Store processed politician data in Neo4j graph database with proper node structure
2. Store news articles in Neo4j with relationships to mentioned politicians
3. Store relationship data as graph connections between entities
4. Manage vector database storage for semantic search capabilities
5. Ensure data consistency, integrity, and proper indexing
6. Handle storage errors gracefully with retry mechanisms

Key principles:
- Maintain data integrity and consistency across all storage operations
- Use proper Neo4j node labels and relationship types
- Ensure vector embeddings are properly stored for semantic search
- Handle duplicate data appropriately (update vs. create new)
- Provide detailed logging of all storage operations
- Implement proper error handling and recovery

Storage operations:
- Politician nodes with properties (name, party, position, bio, etc.)
- News article nodes with content and metadata
- Relationship edges between politicians, parties, and news
- Vector embeddings for semantic similarity search
- Temporal data for tracking changes over time

When storing data:
- Use the StorageTool for all storage operations
- Validate data structure before storage
- Handle conflicts and duplicates appropriately
- Maintain referential integrity in the graph
- Store results and status in shared memory

You work as part of a multi-agent system. Your storage operations enable other agents to query and analyze the data effectively."""

    async def store_politicians(self, politician_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Store politician data in Neo4j graph database
        
        Args:
            politician_data: List of processed politician data to store
            
        Returns:
            Storage results with status and statistics
        """
        try:
            self.logger.info("Starting politician data storage")
            
            # Get processed data from shared memory if not provided
            if not politician_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="collection_result",
                    agent_id="data_collection_agent"
                )
                politician_data = [m.content for m in memories if "politician" in m.content.get("operation", "")]
            
            # Execute storage using agent
            result = await self.executor.ainvoke({
                "input": f"Store {len(politician_data)} politician records in Neo4j graph database with proper node structure and relationships."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_storage",
                    "data_count": len(politician_data) if politician_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="storage_result"
            )
            
            self.logger.info("Politician storage completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in politician storage: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_storage",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def store_news(self, news_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Store news articles in Neo4j with relationships to politicians
        
        Args:
            news_data: List of processed news articles to store
            
        Returns:
            Storage results with status and statistics
        """
        try:
            self.logger.info("Starting news data storage")
            
            # Get processed data from shared memory if not provided
            if not news_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="collection_result",
                    agent_id="data_collection_agent"
                )
                news_data = [m.content for m in memories if "news" in m.content.get("operation", "")]
            
            # Execute storage using agent
            result = await self.executor.ainvoke({
                "input": f"Store {len(news_data)} news articles in Neo4j with proper relationships to mentioned politicians and parties."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_storage",
                    "data_count": len(news_data) if news_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="storage_result"
            )
            
            self.logger.info("News storage completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in news storage: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_storage",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    async def store_relationships(self, relationship_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Store relationship data as graph connections in Neo4j
        
        Args:
            relationship_data: List of extracted relationships to store
            
        Returns:
            Storage results with status and statistics
        """
        try:
            self.logger.info("Starting relationship data storage")
            
            # Get relationship data from shared memory if not provided
            if not relationship_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="relationship_result",
                    agent_id="relationship_agent"
                )
                relationship_data = [m.content for m in memories]
            
            # Execute storage using agent
            result = await self.executor.ainvoke({
                "input": f"Store {len(relationship_data)} relationship records as graph connections in Neo4j with proper relationship types and properties."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "relationship_storage",
                    "data_count": len(relationship_data) if relationship_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="storage_result"
            )
            
            self.logger.info("Relationship storage completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in relationship storage: {str(e)}")
            raise
    
    async def store_vectors(self, document_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Store document embeddings in vector database for semantic search
        
        Args:
            document_data: List of processed documents with embeddings
            
        Returns:
            Vector storage results with status
        """
        try:
            self.logger.info("Starting vector data storage")
            
            # Get processed documents from shared memory if not provided
            if not document_data:
                memories = await self.shared_memory.get_memories(
                    memory_type="collection_result"
                )
                document_data = [m.content for m in memories]
            
            # Execute vector storage using agent
            result = await self.executor.ainvoke({
                "input": f"Store {len(document_data)} document embeddings in vector database for semantic search capabilities."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "vector_storage",
                    "data_count": len(document_data) if document_data else 0,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="storage_result"
            )
            
            self.logger.info("Vector storage completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in vector storage: {str(e)}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "StorageAgent",
            "capabilities": [
                "neo4j_graph_storage",
                "vector_database_storage",
                "relationship_graph_creation",
                "data_integrity_management",
                "storage_error_handling",
                "duplicate_data_management",
                "indexing_optimization"
            ],
            "tools": [tool.name for tool in self.tools],
            "status": "active"
        }
