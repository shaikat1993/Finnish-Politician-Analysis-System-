"""
AI Service Layer for FPAS API
Provides abstraction over AI pipeline operations
"""

import sys
import os
from typing import List, Dict, Any, Optional
import asyncio
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from existing AI pipeline module
from ai_pipeline.agents.supervisor_agent import SupervisorAgent
from ai_pipeline.memory.shared_memory import SharedMemory
from ai_pipeline.tools.coordination_tools import (
    DataCollectionTool,
    AnalysisTool,
    RelationshipTool,
    StorageTool,
    QueryTool
)

logger = logging.getLogger("fpas_api.ai_service")

class AIPipelineService:
    """Service layer for AI pipeline operations"""
    
    def __init__(self):
        """Initialize AI pipeline service"""
        self._supervisor_agent = None
        self._shared_memory = None
        self._tools = {}
    
    async def _ensure_initialized(self):
        """Ensure AI pipeline components are initialized"""
        if not self._supervisor_agent:
            try:
                self._shared_memory = SharedMemory()
                
                # Initialize all tools
                self._tools = {
                    "data_collection": DataCollectionTool(self._shared_memory),
                    "analysis": AnalysisTool(self._shared_memory),
                    "relationship": RelationshipTool(self._shared_memory),
                    "storage": StorageTool(self._shared_memory),
                    "query": QueryTool(self._shared_memory)
                }
                
                # Initialize supervisor agent with all tools
                self._supervisor_agent = SupervisorAgent(
                    tools=list(self._tools.values()),
                    shared_memory=self._shared_memory
                )
                
                logger.info("AI pipeline service initialized successfully")
                
            except Exception as e:
                logger.error(f"Failed to initialize AI pipeline service: {str(e)}")
                raise
    
    async def analyze_politician(self, politician_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        Analyze a politician using the AI pipeline
        
        Args:
            politician_id: ID of the politician to analyze
            depth: Analysis depth (1-3)
            
        Returns:
            Dict containing analysis results
        """
        await self._ensure_initialized()
        
        try:
            # Create analysis request
            request = {
                "entity_type": "politician",
                "entity_id": politician_id,
                "depth": depth,
                "include_relationships": True,
                "include_sentiment": True,
            }
            
            # Use the relationship tool directly
            result = await self._tools["relationship"].analyze_entity_relationships(request)
            
            # Enhance with sentiment analysis
            sentiment = await self._tools["analysis"].analyze_sentiment({
                "entity_type": "politician",
                "entity_id": politician_id
            })
            
            return {
                "politician_id": politician_id,
                "relationships": result.get("relationships", []),
                "key_findings": result.get("key_findings", []),
                "sentiment": sentiment.get("sentiment", {}),
                "analysis_depth": depth
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze politician {politician_id}: {str(e)}")
            raise
    
    async def analyze_news_sentiment(self, news_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze sentiment of news articles
        
        Args:
            news_ids: List of news article IDs to analyze
            
        Returns:
            Dict containing sentiment analysis results
        """
        await self._ensure_initialized()
        
        try:
            # Batch sentiment analysis
            results = []
            for news_id in news_ids:
                result = await self._tools["analysis"].analyze_sentiment({
                    "entity_type": "news",
                    "entity_id": news_id
                })
                results.append({
                    "news_id": news_id,
                    "sentiment": result.get("sentiment", {})
                })
            
            return {
                "results": results,
                "count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze news sentiment: {str(e)}")
            raise
    
    async def analyze_query(self, query_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform custom analysis using natural language query
        
        Args:
            query_request: Query request with structure:
                {
                    "query": "Natural language query",
                    "context_ids": Optional[List[str]],
                    "detailed": bool
                }
            
        Returns:
            Dict containing analysis results
        """
        await self._ensure_initialized()
        
        try:
            # Prepare the request for the supervisor agent
            request = {
                "query": query_request["query"],
                "context": {
                    "entity_ids": query_request.get("context_ids", []),
                    "detailed": query_request.get("detailed", False)
                }
            }
            
            # Use the supervisor agent for complex queries
            response = await self._supervisor_agent.run(request["query"], request["context"])
            
            # Process and structure the response
            result = {
                "query": query_request["query"],
                "answer": response,
                "sources": self._shared_memory.get_sources()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to analyze query: {str(e)}")
            raise
    
    async def analyze_coalition_potential(self, party_ids: List[str]) -> Dict[str, Any]:
        """
        Analyze coalition potential between political parties
        
        Args:
            party_ids: List of party IDs to analyze
            
        Returns:
            Dict containing coalition analysis results
        """
        await self._ensure_initialized()
        
        try:
            # Use relationship tool for coalition analysis
            request = {
                "entity_type": "party",
                "entity_ids": party_ids,
                "analysis_type": "coalition_potential"
            }
            
            result = await self._tools["relationship"].analyze_relationship_network(request)
            
            return {
                "party_ids": party_ids,
                "coalition_potential": result.get("network_analysis", {}),
                "compatibility_matrix": result.get("compatibility_matrix", {}),
                "key_issues": result.get("key_issues", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze coalition potential: {str(e)}")
            raise
    
    async def get_trending_topics(self, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """
        Get trending topics from news analysis
        
        Args:
            days: Number of past days to analyze
            limit: Maximum number of topics to return
            
        Returns:
            Dict containing trending topics
        """
        await self._ensure_initialized()
        
        try:
            # Use analysis tool for trending topics
            request = {
                "analysis_type": "trending_topics",
                "timeframe_days": days,
                "limit": limit
            }
            
            result = await self._tools["analysis"].analyze_content(request)
            
            return {
                "trending_topics": result.get("topics", []),
                "timeframe_days": days,
                "topic_count": len(result.get("topics", []))
            }
            
        except Exception as e:
            logger.error(f"Failed to get trending topics: {str(e)}")
            raise
