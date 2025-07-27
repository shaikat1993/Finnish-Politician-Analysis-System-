"""
Analytics Service Layer for FPAS API
Provides political data analysis functionality
"""

import sys
import os
from typing import List, Dict, Any, Optional
from neo4j import AsyncSession

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class AnalyticsService:
    """Service layer for political data analytics"""
    
    def __init__(self, session: AsyncSession):
        """
        Initialize analytics service with a database session
        
        Args:
            session: Neo4j database session
        """
        self.session = session
    
    async def analyze_politician_network(self, 
                                      politician_ids: List[str],
                                      depth: int = 1,
                                      include_evidence: bool = False) -> Dict[str, Any]:
        """
        Analyze network of relationships between politicians
        
        Args:
            politician_ids: List of politician IDs
            depth: Relationship depth (1-3)
            include_evidence: Include evidence for relationships
            
        Returns:
            Dict containing network analysis
        """
        # Build query with variable depth paths
        depth_str = '1..' + str(min(3, max(1, depth)))
        evidence_return = ", r.evidence as evidence" if include_evidence else ""
        
        query = f"""
        MATCH path = (p1:Politician)-[r*{depth_str}]-(p2:Politician)
        WHERE p1.id IN $politician_ids AND p2.id IN $politician_ids
        UNWIND relationships(path) as rel
        RETURN DISTINCT 
            startNode(rel).id as source_id,
            startNode(rel).name as source_name,
            endNode(rel).id as target_id, 
            endNode(rel).name as target_name,
            type(rel) as relationship_type,
            rel.strength as strength
            {evidence_return}
        """
        
        result = await self.session.run(query, {"politician_ids": politician_ids})
        records = await result.fetch_all()
        
        # Format network data
        nodes = {}
        edges = []
        
        for record in records:
            # Add source node if not exists
            source_id = record["source_id"]
            if source_id not in nodes:
                nodes[source_id] = {
                    "id": source_id,
                    "name": record["source_name"],
                    "type": "politician"
                }
                
            # Add target node if not exists
            target_id = record["target_id"]
            if target_id not in nodes:
                nodes[target_id] = {
                    "id": target_id,
                    "name": record["target_name"],
                    "type": "politician"
                }
                
            # Add relationship
            edge = {
                "source": source_id,
                "target": target_id,
                "type": record["relationship_type"],
                "strength": record["strength"]
            }
            
            # Add evidence if requested
            if include_evidence and "evidence" in record:
                edge["evidence"] = record["evidence"]
                
            edges.append(edge)
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges
        }
    
    async def analyze_coalition_potential(self,
                                       party_ids: List[str],
                                       include_historical: bool = True) -> Dict[str, Any]:
        """
        Analyze potential coalition formation between parties
        
        Args:
            party_ids: List of party IDs
            include_historical: Include historical coalition data
            
        Returns:
            Dict containing coalition analysis
        """
        # Get party compatibility based on voting patterns
        compatibility_query = """
        MATCH (p1:Party)-[r:VOTING_COMPATIBILITY]-(p2:Party)
        WHERE p1.id IN $party_ids AND p2.id IN $party_ids AND p1.id <> p2.id
        RETURN 
            p1.id as party1_id,
            p1.name as party1_name,
            p2.id as party2_id,
            p2.name as party2_name,
            r.compatibility_score as score,
            r.key_agreements as agreements,
            r.key_disagreements as disagreements
        """
        
        compatibility_result = await self.session.run(compatibility_query, {"party_ids": party_ids})
        compatibility_records = await compatibility_result.fetch_all()
        
        # Format compatibility matrix
        compatibility_matrix = {}
        key_issues = set()
        
        for record in compatibility_records:
            party1 = record["party1_id"]
            party2 = record["party2_id"]
            
            if party1 not in compatibility_matrix:
                compatibility_matrix[party1] = {}
                
            compatibility_matrix[party1][party2] = {
                "score": record["score"],
                "agreements": record["agreements"],
                "disagreements": record["disagreements"]
            }
            
            # Collect all key issues
            if record["agreements"]:
                key_issues.update(record["agreements"])
            if record["disagreements"]:
                key_issues.update(record["disagreements"])
        
        # Get historical coalition data if requested
        historical_data = []
        if include_historical:
            historical_query = """
            MATCH (c:Coalition)
            WHERE all(p IN c.parties WHERE p IN $party_ids)
            RETURN 
                c.id as coalition_id,
                c.name as coalition_name,
                c.start_date as start_date,
                c.end_date as end_date,
                c.success_rating as success_rating,
                c.key_achievements as key_achievements
            ORDER BY c.start_date DESC
            LIMIT 5
            """
            
            historical_result = await self.session.run(historical_query, {"party_ids": party_ids})
            historical_records = await historical_result.fetch_all()
            
            for record in historical_records:
                historical_data.append({
                    "coalition_id": record["coalition_id"],
                    "name": record["coalition_name"],
                    "start_date": record["start_date"],
                    "end_date": record["end_date"],
                    "success_rating": record["success_rating"],
                    "key_achievements": record["key_achievements"]
                })
        
        return {
            "compatibility_matrix": compatibility_matrix,
            "key_issues": list(key_issues),
            "historical_coalitions": historical_data
        }
    
    async def calculate_politician_sentiment(self, limit: int = 10) -> Dict[str, Any]:
        """
        Calculate sentiment for politicians based on news coverage
        
        Args:
            limit: Maximum number of politicians to include
            
        Returns:
            Dict containing sentiment analysis
        """
        query = """
        MATCH (p:Politician)-[r:MENTIONED_IN]->(n:News)
        WITH p, avg(n.sentiment_score) as avg_sentiment, count(n) as mention_count
        ORDER BY mention_count DESC, avg_sentiment DESC
        LIMIT $limit
        RETURN 
            p.id as politician_id,
            p.name as politician_name,
            p.party as party,
            avg_sentiment,
            mention_count
        """
        
        result = await self.session.run(query, {"limit": limit})
        records = await result.fetch_all()
        
        sentiment_data = []
        for record in records:
            sentiment_data.append({
                "politician_id": record["politician_id"],
                "name": record["politician_name"],
                "party": record["party"],
                "average_sentiment": record["avg_sentiment"],
                "mention_count": record["mention_count"]
            })
            
        return sentiment_data
    
    async def identify_trending_topics(self, days: int = 30, limit: int = 10) -> Dict[str, Any]:
        """
        Identify trending political topics from news
        
        Args:
            days: Number of past days to analyze
            limit: Maximum number of topics to return
            
        Returns:
            Dict containing trending topics
        """
        query = """
        MATCH (t:Topic)<-[r:HAS_TOPIC]-(n:News)
        WHERE datetime(n.published_date) > datetime() - duration({days: $days})
        WITH t, count(n) as article_count
        ORDER BY article_count DESC
        LIMIT $limit
        RETURN 
            t.id as topic_id,
            t.name as topic_name,
            t.category as category,
            article_count
        """
        
        result = await self.session.run(query, {"days": days, "limit": limit})
        records = await result.fetch_all()
        
        topics = []
        for record in records:
            topics.append({
                "topic_id": record["topic_id"],
                "name": record["topic_name"],
                "category": record["category"],
                "article_count": record["article_count"]
            })
            
        return topics
