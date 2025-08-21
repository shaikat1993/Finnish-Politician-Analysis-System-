"""
QueryAgent - Specialized LangChain Agent for Data Querying
Handles all query operations against Neo4j graph database and vector databases.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Minimal QueryTool implementation (DB tool)
try:
    from langchain.tools import BaseTool
except ImportError:
    BaseTool = object

class QueryTool(BaseTool):
    name: str = "QueryTool"
    description: str = "Performs basic query (echoes input for test purposes)"

    def _run(self, input: str) -> str:
        return f"[QueryTool] Echo: {input}"

    async def _arun(self, input: str) -> str:
        return self._run(input)

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain.tools.wikipedia.tool import WikipediaQueryRun

from ..memory.shared_memory import SharedAgentMemory
from ..security.security_decorators import secure_prompt, secure_output, verify_response, track_metrics

class QueryAgent:
    """
    Specialized LangChain agent for data querying operations.
    
    Responsibilities:
    - Execute complex queries against Neo4j graph database
    - Perform semantic search using vector databases
    - Handle user queries and convert them to appropriate database queries
    - Provide intelligent query optimization and result formatting
    - Support both structured and natural language queries
    """
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None):
        self.agent_id = "query_agent"
        self.shared_memory = shared_memory
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.2,  # Low temperature for consistent query generation
            openai_api_key=openai_api_key
        )
        
        # Initialize tools
        wikipedia_api = WikipediaAPIWrapper()
        self.tools = [
            QueryTool(),  # Neo4j/vector DB tool
            WikipediaQueryRun(api_wrapper=wikipedia_api),
            DuckDuckGoSearchRun()
        ]
        
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
        
        self.logger.info(f"QueryAgent initialized with {len(self.tools)} tools")
    
    def _get_system_prompt(self) -> str:
        return """
You are a superhuman Query Agent for the Finnish Politician Analysis System.

Your mission is to answer ANY question about a selected Finnish politician with the highest possible accuracy, using all available data and tools.

**Answering Strategy:**
1. ALWAYS first use Neo4j (the graph database) and the vector database (via QueryTool) to answer the question.
2. If you cannot fully answer from Neo4j/vector DB, use Wikipedia and web search tools to supplement your answer.
3. Combine and synthesize information from multiple sources for the most complete answer.
4. Always cite your sources or explain how you arrived at the answer.

You have access to:
- QueryTool: for database queries
- WikipediaQueryRun: for Wikipedia lookups
- DuckDuckGoSearchRun: for live web search
    - DuckDuckGoSearchRun: for live web search
    - Aggregation and statistical queries
    - Temporal queries for trend analysis

    When processing queries:
    - Use the QueryTool for all database operations
    - Analyze user intent to determine optimal query strategy
    - Combine graph and vector search when appropriate
    - Format results for maximum clarity and usefulness
    - Store query results in shared memory for caching

You work as part of a multi-agent system. Your query results help users discover insights and other agents perform their analysis tasks."""

    @track_metrics()
    @secure_prompt(strict_mode=True)
    @secure_output(strict_mode=False)
    @verify_response(verification_type="consistency")
    async def search_politicians(self, query: str, search_type: str = "hybrid") -> Dict[str, Any]:
        """
        Search for politicians using various search strategies
        
        Args:
            query: Search query (name, party, position, etc.)
            search_type: Type of search (exact, semantic, hybrid)
            
        Returns:
            Search results with politician data
        """
        try:
            self.logger.info(f"Searching politicians with query: {query}")
            
            # Execute search using agent
            result = await self.executor.ainvoke({
                "input": f"Search for politicians using query: '{query}' with search type: {search_type}. Provide comprehensive results with politician profiles and relationships."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_search",
                    "query": query,
                    "search_type": search_type,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="query_result"
            )
            
            self.logger.info("Politician search completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in politician search: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "politician_search",
                    "query": query,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    @track_metrics()
    @secure_prompt(strict_mode=True)
    @secure_output(strict_mode=False)
    @verify_response(verification_type="consistency")
    async def search_news(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search news articles with optional filters
        
        Args:
            query: Search query for news content
            filters: Optional filters (date range, source, politician mentions)
            
        Returns:
            News search results with articles and metadata
        """
        try:
            self.logger.info(f"Searching news with query: {query}")
            
            # Execute search using agent
            result = await self.executor.ainvoke({
                "input": f"Search news articles with query: '{query}' and filters: {filters}. Include related politician mentions and article metadata."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "news_search",
                    "query": query,
                    "filters": filters,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="query_result"
            )
            
            self.logger.info("News search completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in news search: {str(e)}")
            raise
    
    @track_metrics()
    @secure_prompt(strict_mode=True)
    @secure_output(strict_mode=False)
    @verify_response(verification_type="consistency")
    async def find_relationships(self, entity1: str, entity2: str = None, relationship_type: str = None) -> Dict[str, Any]:
        """
        Find relationships between political entities
        
        Args:
            entity1: First entity (politician, party, etc.)
            entity2: Optional second entity for direct relationship queries
            relationship_type: Optional filter for relationship type
            
        Returns:
            Relationship query results with connection details
        """
        try:
            self.logger.info(f"Finding relationships for entity: {entity1}")
            
            # Execute relationship query using agent
            result = await self.executor.ainvoke({
                "input": f"Find relationships for entity: '{entity1}' with entity2: '{entity2}' and relationship type: '{relationship_type}'. Include relationship strength and context."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "relationship_query",
                    "entity1": entity1,
                    "entity2": entity2,
                    "relationship_type": relationship_type,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="query_result"
            )
            
            self.logger.info("Relationship query completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in relationship query: {str(e)}")
            raise
    
    @track_metrics()
    @secure_prompt(strict_mode=True)
    @secure_output(strict_mode=False)
    @verify_response(verification_type="consistency")
    async def semantic_search(self, query: str, limit: int = 10, similarity_threshold: float = 0.7) -> Dict[str, Any]:
        """
        Perform semantic search across all content
        
        Args:
            query: Natural language search query
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results
            
        Returns:
            Semantic search results with similarity scores
        """
        try:
            self.logger.info(f"Performing semantic search with query: {query}")
            
            # Execute semantic search using agent
            result = await self.executor.ainvoke({
                "input": f"Semantic search for: '{query}'. Limit: {limit}. Similarity threshold: {similarity_threshold}."
            })
            
            # Store results in shared memory
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "semantic_search",
                    "query": query,
                    "limit": limit,
                    "similarity_threshold": similarity_threshold,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="query_result"
            )
            
            self.logger.info("Semantic search completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in semantic search: {str(e)}")
            await self.shared_memory.store_memory(
                agent_id=self.agent_id,
                content={
                    "operation": "semantic_search",
                    "query": query,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                },
                memory_type="error"
            )
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "QueryAgent",
            "capabilities": [
                "neo4j_graph_queries",
                "vector_semantic_search",
                "natural_language_query_processing",
                "query_optimization",
                "result_formatting",
                "relationship_traversal",
                "aggregation_queries",
                "temporal_queries"
            ],
            "tools": [tool.name for tool in self.tools],
            "status": "active"
        }
