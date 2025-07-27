"""
Neo4j Service Layer for FPAS API
Provides abstraction over Neo4j database operations
"""

import sys
import os
from typing import List, Dict, Any, Optional
from neo4j import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import from existing database module
from database import get_neo4j_analytics, get_neo4j_writer

class Neo4jService:
    """Service layer for Neo4j database operations"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize Neo4j service with a database session
        
        Args:
            session: Neo4j database session
        """
        self.session = session
        self._analytics = None
        self._writer = None
    
    @property
    async def analytics(self):
        """Get Neo4j analytics instance"""
        if not self._analytics:
            self._analytics = get_neo4j_analytics()
        return self._analytics
    
    @property
    async def writer(self):
        """Get Neo4j writer instance"""
        if not self._writer:
            self._writer = get_neo4j_writer()
        return self._writer
    
    async def get_politicians(self, 
                             skip: int = 0, 
                             limit: int = 100, 
                             party: Optional[str] = None,
                             active_only: bool = False) -> Dict[str, Any]:
        """
        Get paginated list of politicians with optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            party: Filter by political party
            active_only: Filter only active politicians
            
        Returns:
            Dict containing politicians and total count
        """
        # Build query with parameters
        query = """
        MATCH (p:Politician)
        WHERE 
            ($party IS NULL OR p.party = $party)
            AND ($active_only = False OR p.active = True)
        RETURN p
        ORDER BY p.name
        SKIP $skip
        LIMIT $limit
        """
        
        # Count query
        count_query = """
        MATCH (p:Politician)
        WHERE 
            ($party IS NULL OR p.party = $party)
            AND ($active_only = False OR p.active = True)
        RETURN count(p) AS total
        """
        
        # Run queries
        result = await self.session.run(query, {
            "party": party,
            "active_only": active_only,
            "skip": skip,
            "limit": limit
        })
        
        politicians = [record["p"] for record in await result.fetch_all()]
        
        count_result = await self.session.run(count_query, {
            "party": party,
            "active_only": active_only
        })
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        return {
            "politicians": politicians,
            "total": total
        }
    
    async def get_politician_by_id(self, 
                                  politician_id: str,
                                  include_news: bool = True,
                                  include_relationships: bool = False) -> Dict[str, Any]:
        """
        Get detailed information about a specific politician
        
        Args:
            politician_id: Politician ID
            include_news: Include latest news about the politician
            include_relationships: Include politician's relationships
            
        Returns:
            Dict containing politician details and related data
        """
        # Base query for politician data
        query = """
        MATCH (p:Politician {id: $id})
        RETURN p
        """
        
        result = await self.session.run(query, {"id": politician_id})
        record = await result.single()
        
        if not record:
            return None
            
        politician = dict(record["p"])
        
        # Get latest news if requested
        if include_news:
            news_query = """
            MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
            RETURN n
            ORDER BY n.published_date DESC
            LIMIT 5
            """
            
            news_result = await self.session.run(news_query, {"id": politician_id})
            news_records = await news_result.fetch_all()
            latest_news = [dict(record["n"]) for record in news_records]
            politician["latest_news"] = latest_news
            
        # Get relationships if requested
        if include_relationships:
            relations_query = """
            MATCH (p:Politician {id: $id})-[r]-(other:Politician)
            RETURN type(r) as type, other, r.strength as strength, r.evidence as evidence
            LIMIT 10
            """
            
            relations_result = await self.session.run(relations_query, {"id": politician_id})
            relations_records = await relations_result.fetch_all()
            
            relationships = []
            for record in relations_records:
                relationships.append({
                    "type": record["type"],
                    "politician": dict(record["other"]),
                    "strength": record["strength"],
                    "evidence": record["evidence"]
                })
                
            politician["relationships"] = relationships
            
        return politician
    
    async def search_politicians(self, 
                               query: str,
                               skip: int = 0,
                               limit: int = 100) -> Dict[str, Any]:
        """
        Search for politicians by name or other attributes
        
        Args:
            query: Search query string
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dict containing matching politicians and total count
        """
        # Build case-insensitive search query
        search_query = """
        MATCH (p:Politician)
        WHERE toLower(p.name) CONTAINS toLower($query)
           OR toLower(p.party) CONTAINS toLower($query)
           OR toLower(p.title) CONTAINS toLower($query)
        RETURN p
        ORDER BY p.name
        SKIP $skip
        LIMIT $limit
        """
        
        # Count query
        count_query = """
        MATCH (p:Politician)
        WHERE toLower(p.name) CONTAINS toLower($query)
           OR toLower(p.party) CONTAINS toLower($query)
           OR toLower(p.title) CONTAINS toLower($query)
        RETURN count(p) AS total
        """
        
        # Run queries
        result = await self.session.run(search_query, {
            "query": query,
            "skip": skip,
            "limit": limit
        })
        
        politicians = [dict(record["p"]) for record in await result.fetch_all()]
        
        count_result = await self.session.run(count_query, {"query": query})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        return {
            "politicians": politicians,
            "total": total
        }
    
    async def get_news_articles(self,
                              skip: int = 0,
                              limit: int = 100,
                              source: Optional[str] = None) -> Dict[str, Any]:
        """
        Get paginated list of news articles with optional filtering
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            source: Filter by news source
            
        Returns:
            Dict containing news articles and total count
        """
        # Build query with parameters
        query = """
        MATCH (n:News)
        WHERE $source IS NULL OR n.source = $source
        RETURN n
        ORDER BY n.published_date DESC
        SKIP $skip
        LIMIT $limit
        """
        
        # Count query
        count_query = """
        MATCH (n:News)
        WHERE $source IS NULL OR n.source = $source
        RETURN count(n) AS total
        """
        
        # Run queries
        result = await self.session.run(query, {
            "source": source,
            "skip": skip,
            "limit": limit
        })
        
        news_articles = [dict(record["n"]) for record in await result.fetch_all()]
        
        count_result = await self.session.run(count_query, {"source": source})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        return {
            "news_articles": news_articles,
            "total": total
        }
        
    async def get_news_by_politician(self,
                                    politician_id: str,
                                    skip: int = 0,
                                    limit: int = 20) -> Dict[str, Any]:
        """
        Get news articles mentioning a specific politician
        
        Args:
            politician_id: Politician ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            Dict containing news articles and total count
        """
        # Check if politician exists
        check_query = "MATCH (p:Politician {id: $id}) RETURN p"
        check_result = await self.session.run(check_query, {"id": politician_id})
        check_record = await check_result.single()
        
        if not check_record:
            return None
        
        # Get news articles
        news_query = """
        MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
        RETURN n
        ORDER BY n.published_date DESC
        SKIP $skip
        LIMIT $limit
        """
        
        # Count query
        count_query = """
        MATCH (p:Politician {id: $id})-[:MENTIONED_IN]->(n:News)
        RETURN count(n) AS total
        """
        
        # Execute queries
        result = await self.session.run(news_query, {
            "id": politician_id,
            "skip": skip,
            "limit": limit
        })
        
        news_articles = [dict(record["n"]) for record in await result.fetch_all()]
        
        count_result = await self.session.run(count_query, {"id": politician_id})
        count_record = await count_result.single()
        total = count_record["total"] if count_record else 0
        
        return {
            "news_articles": news_articles,
            "total": total
        }
