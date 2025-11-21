"""
QueryAgent - Specialized LangChain Agent for Data Querying
Handles all query operations against Neo4j graph database and vector databases.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Set up module-level logger
logger = logging.getLogger(__name__)

# QueryTool: Stub implementation for security research demonstration
#
# DESIGN DECISION (Design Science Research):
# This stub tool demonstrates OWASP LLM06 permission control mechanisms without
# requiring Neo4j/vector database infrastructure. Security mechanisms (permission
# checking, rate limiting, audit logging) operate independently of database
# implementation, allowing isolated evaluation of security controls.
#
# In production deployment, this would contain real database query logic such as:
# - Cypher queries against Neo4j graph database
# - Vector similarity search for semantic retrieval
# - Hybrid search combining graph traversal and embeddings
# - Complex relationship queries across politician networks
#
# The security architecture supports full database integration without modification.
try:
    from langchain.tools import BaseTool
except ImportError:
    BaseTool = object

class QueryTool(BaseTool):
    """
    Stub implementation of QueryTool for OWASP LLM security research.

    This simplified tool is used to demonstrate and evaluate security mechanisms
    (OWASP LLM06 permission control) in isolation from database complexity.
    Security overhead measurements and attack prevention validation remain valid
    regardless of database implementation details.
    """
    name: str = "QueryTool"
    description: str = "Performs basic query (stub for demonstration purposes)"

    def _run(self, input: str) -> str:
        """Execute query operation (stub implementation for security testing)"""
        return f"[QueryTool] Query complete: {input}"

    async def _arun(self, input: str) -> str:
        """Async execution wrapper"""
        return self._run(input)

class NewsSearchTool(BaseTool):
    """Tool for searching news about Finnish politicians using internal collectors."""
    
    name: str = "news_search"
    description: str = "Search for news about Finnish politicians from multiple Finnish news sources"
    
    def _run(self, query: str) -> str:
        """Run the Finnish news search using internal collectors."""
        try:
            import sys
            import os
            import json
            import logging
            import re
            from datetime import datetime, timedelta
            
            # Add data_collection to path
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data_collection'))
            
            # Import collectors
            from data_collection.news.yle_news_collector import YleNewsCollector
            from data_collection.news.iltalehti_collector import IltalehtCollector
            
            # Calculate date range (last 3 months)
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            
            logger.info(f"Searching for news about '{query}' from {start_date} to {end_date}")
            results = []
            
            # Try YLE collector first
            try:
                # YLE collector requires API credentials
                try:
                    yle_collector = YleNewsCollector()
                    yle_articles = yle_collector.get_politician_articles(
                        politician_name=query,
                        start_date=start_date,
                        end_date=end_date,
                        limit=10
                    )
                    if yle_articles:
                        results.extend(yle_articles)
                        logger.info(f"Found {len(yle_articles)} YLE articles about {query}")
                except ValueError as ve:
                    # This happens if YLE API credentials are missing
                    logger.warning(f"YLE collector not available: {str(ve)}")
            except Exception as e:
                logger.error(f"Error with YLE collector: {str(e)}")
            
            # Try Iltalehti collector
            try:
                il_collector = IltalehtCollector()
                il_articles = il_collector.get_politician_articles(
                    politician_name=query,
                    start_date=start_date,
                    end_date=end_date,
                    limit=10
                )
                if il_articles:
                    results.extend(il_articles)
                    logger.info(f"Found {len(il_articles)} Iltalehti articles about {query}")
            except Exception as e:
                logger.error(f"Error with Iltalehti collector: {str(e)}")
            
            # Filter results to ensure they're relevant
            filtered_results = []
            seen_urls = set()
            
            # Split query into words for better matching
            query_words = query.lower().split()
            
            for article in results:
                # Handle both dict and object formats
                if isinstance(article, dict):
                    title = article.get('title', '')
                    url = article.get('url', '')
                    date = article.get('published_date', '')
                    source = article.get('source', '')
                    content = article.get('content', '')
                else:
                    title = getattr(article, 'title', '')
                    url = getattr(article, 'url', '')
                    date = getattr(article, 'published_date', '')
                    source = getattr(article, 'source', 'unknown')
                    content = getattr(article, 'content', '')
                
                # Skip if URL is empty or a navigation link or already seen
                if not url or url.startswith('mailto:') or not title or url in seen_urls:
                    continue
                    
                # Check if the article is actually about the politician
                # Look for the politician's name in the title or content
                title_lower = title.lower()
                content_lower = content.lower() if content else ''
                
                # Check if all words in the query appear in title or content
                is_relevant = all(word in title_lower or word in content_lower for word in query_words)
                
                if is_relevant:
                    filtered_results.append({
                        'title': title,
                        'url': url,
                        'date': date,
                        'source': source
                    })
                    seen_urls.add(url)
            
            # Format results
            if filtered_results:
                formatted_results = []
                for article in filtered_results:
                    formatted_results.append(f"- [{article['title']}]({article['url']}) - {article['source']} ({article['date']})")
                
                logger.info(f"Returning {len(formatted_results)} relevant news articles")
                return "Found the following news articles about the politician:\n\n" + "\n\n".join(formatted_results)
            else:
                logger.warning(f"No relevant news articles found about {query}")
                return f"No relevant news articles found about {query} in Finnish news sources."
            
        except Exception as e:
            logger.error(f"Error searching Finnish news: {str(e)}")
            return f"Error searching Finnish news: {str(e)}"
    
    async def _arun(self, query: str) -> str:
        """Run the Finnish news search asynchronously."""
        return self._run(query)

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun

from ..memory.shared_memory import SharedAgentMemory
from ..security import secure_prompt, secure_output, verify_response, track_metrics
from ..security import AgentPermissionManager
from ..security import SecureAgentExecutor

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
    
    def __init__(self, shared_memory: SharedAgentMemory, openai_api_key: str = None) -> None:
        self.agent_id = "query_agent"
        self.shared_memory = shared_memory

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
            DuckDuckGoSearchRun(),
            NewsSearchTool()
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

        # Initialize OWASP LLM06 Permission Manager
        self.permission_manager = AgentPermissionManager(enable_metrics=True)

        # Create SECURED executor with LLM06 protection
        self.executor = SecureAgentExecutor(
            agent=self.agent,
            tools=self.tools,
            agent_id=self.agent_id,
            permission_manager=self.permission_manager,
            memory=ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            ),
            verbose=True,
            max_iterations=15,  # Increased from 5 to allow complex multi-tool queries
            max_execution_time=30  # 30 second timeout for safety
        )

        logger.info(f"QueryAgent initialized with {len(self.tools)} tools and LLM06 protection")
    
    def _get_system_prompt(self) -> str:
        return """
You are a superhuman Query Agent for the Finnish Politician Analysis System.

Your mission is to answer ANY question about a selected Finnish politician with the highest possible accuracy, using all available data and tools.

**Answering Strategy:**
1. ALWAYS first use Neo4j (the graph database) and the vector database (via QueryTool) to answer the question.
2. If you cannot fully answer from Neo4j/vector DB, use specialized news search and Wikipedia tools to supplement your answer.
3. Combine and synthesize information from multiple sources for the most complete answer.
4. Always cite your sources or explain how you arrived at the answer.

You have access to:
- QueryTool: for database queries
- WikipediaQueryRun: for Wikipedia lookups
- DuckDuckGoSearchRun: for general web search
- NewsSearchTool: for searching Finnish news sources about politicians (PREFERRED for news queries)

When processing queries:
- Use the QueryTool for all database operations
- Use NewsSearchTool for any news-related queries about Finnish politicians
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
            logger.info(f"Searching politicians with query: {query}")
            
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
            
            logger.info("Politician search completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in politician search: {str(e)}")
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
            logger.info(f"Searching news with query: {query}")
            
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
            
            logger.info("News search completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in news search: {str(e)}")
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
            logger.info(f"Finding relationships for entity: {entity1}")
            
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
            
            logger.info("Relationship query completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in relationship query: {str(e)}")
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
            logger.info(f"Performing semantic search with query: {query}")
            
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
            
            logger.info("Semantic search completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
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
            "status": "active",
            "security": {
                "prompt_injection_protection": True,
                "output_sanitization": True,
                "response_verification": True,
                "metrics_collection": True,
                "excessive_agency_protection": True  # LLM06
            }
        }

    def get_security_metrics(self) -> Dict[str, Any]:
        """
        Get OWASP LLM06 security metrics for this agent

        Returns:
            Dictionary with permission enforcement metrics
        """
        return self.permission_manager.get_metrics()

    def get_audit_log(self, result_filter: Optional[str] = None) -> List:
        """
        Get OWASP LLM06 audit log for this agent

        Args:
            result_filter: Filter by "allowed" or "denied" (optional)

        Returns:
            List of audit entries
        """
        return self.permission_manager.get_audit_log(
            agent_id=self.agent_id,
            result_filter=result_filter
        )
