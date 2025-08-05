"""
Production-Grade Neo4j Integration Layer
Senior-Level Implementation with Async Connection Pooling, Error Handling, and Analytics
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from datetime import datetime, date
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
import json
import time
from enum import Enum
import hashlib

from neo4j import AsyncGraphDatabase, AsyncSession, AsyncTransaction
from neo4j.exceptions import ServiceUnavailable, TransientError, ClientError
import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CONFIGURATION & ENUMS
# =============================================================================

class EntityType(Enum):
    POLITICIAN = "Politician"
    PARTY = "Party"
    ARTICLE = "Article"
    POSITION = "Position"
    CONSTITUENCY = "Constituency"
    POLICY_TOPIC = "PolicyTopic"
    EVENT = "Event"

class RelationshipType(Enum):
    MEMBER_OF = "MEMBER_OF"
    REPRESENTS = "REPRESENTS"
    HOLDS_POSITION = "HOLDS_POSITION"
    MENTIONS = "MENTIONS"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    OPPOSES = "OPPOSES"
    SUPPORTS_POLICY = "SUPPORTS_POLICY"
    COALITION_WITH = "COALITION_WITH"

@dataclass
class Neo4jConfig:
    """Neo4j connection configuration"""
    uri: str = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    user: str = os.getenv('NEO4J_USER', 'neo4j')
    password: str = os.getenv('NEO4J_PASSWORD', 'neo4j')
    database: str = os.getenv('NEO4J_DATABASE', 'neo4j')
    max_connection_lifetime: int = 3600  # 1 hour
    max_connection_pool_size: int = 100
    connection_acquisition_timeout: int = 60
    encrypted: bool = False
    trust: str = "TRUST_ALL_CERTIFICATES"

# =============================================================================
# PRODUCTION-GRADE NEO4J CONNECTION MANAGER
# =============================================================================

class Neo4jConnectionManager:
    """
    Production-grade Neo4j connection manager with:
    - Async connection pooling
    - Circuit breaker pattern
    - Comprehensive error handling
    - Performance monitoring
    - Automatic retry logic
    """
    
    def __init__(self, config: Neo4jConfig = None):
        self.config = config or Neo4jConfig()
        self.driver = None
        self.logger = self._setup_logging()
        self._connection_attempts = 0
        self._max_retries = 3
        self._retry_delay = 1.0
        self._circuit_breaker_failures = 0
        self._circuit_breaker_threshold = 5
        self._circuit_breaker_timeout = 60
        self._last_failure_time = None
        self._performance_metrics = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'avg_query_time': 0.0,
            'total_query_time': 0.0
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup comprehensive logging"""
        logger = logging.getLogger('neo4j_integration')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Load schema from file
            schema_path = os.path.join(os.path.dirname(__file__), 'neo4j_schema.cypher')
            # File handler
            file_handler = logging.FileHandler('neo4j_integration.log')
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    async def initialize(self) -> bool:
        """Initialize connection with retry logic and circuit breaker"""
        if self._is_circuit_breaker_open():
            self.logger.warning("Circuit breaker is open, skipping connection attempt")
            return False
        
        for attempt in range(self._max_retries):
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.config.uri,
                    auth=(self.config.user, self.config.password),
                    max_connection_lifetime=self.config.max_connection_lifetime,
                    max_connection_pool_size=self.config.max_connection_pool_size,
                    connection_acquisition_timeout=self.config.connection_acquisition_timeout,
                    encrypted=self.config.encrypted,
                    trust=self.config.trust
                )
                
                # Test connection
                await self.driver.verify_connectivity()
                
                self.logger.info(f"Neo4j connection established successfully on attempt {attempt + 1}")
                self._connection_attempts = 0
                self._circuit_breaker_failures = 0
                return True
                
            except (ServiceUnavailable, ClientError) as e:
                self._connection_attempts += 1
                self._circuit_breaker_failures += 1
                self._last_failure_time = time.time()
                
                self.logger.error(f"Connection attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))  # Exponential backoff
        
        self.logger.error("All connection attempts failed")
        return False
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self._circuit_breaker_failures < self._circuit_breaker_threshold:
            return False
        
        if self._last_failure_time is None:
            return False
        
        return (time.time() - self._last_failure_time) < self._circuit_breaker_timeout
    
    async def close(self):
        """Close connection gracefully"""
        if self.driver:
            await self.driver.close()
            self.logger.info("Neo4j connection closed")
    
    @asynccontextmanager
    async def session(self, database: str = None) -> AsyncSession:
        """Get async session with error handling"""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized")
        
        session = None
        try:
            session = self.driver.session(database=database or self.config.database)
            yield session
        except Exception as e:
            self.logger.error(f"Session error: {str(e)}")
            raise
        finally:
            if session:
                await session.close()
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute query with performance monitoring and error handling"""
        start_time = time.time()
        parameters = parameters or {}
        
        # Assert all parameter keys are strings for Neo4j compatibility
        if parameters is not None:
            for k in parameters.keys():
                if not isinstance(k, str):
                    self.logger.error(f"Neo4j query parameters contain non-string key: {k} (type: {type(k)}), parameters: {parameters}")
                    raise TypeError(f"Neo4j query parameters must have string keys, got key: {k} (type: {type(k)})")
        try:
            async with self.session() as session:
                result = await session.run(query, parameters)
                records = await result.data()
                
                # Update performance metrics
                query_time = time.time() - start_time
                self._update_performance_metrics(query_time, success=True)
                
                self.logger.info(f"Query executed successfully in {query_time:.3f}s, returned {len(records)} records")
                return records
                
        except (ServiceUnavailable, TransientError) as e:
            self._update_performance_metrics(time.time() - start_time, success=False)
            self.logger.error(f"Transient error executing query: {str(e)}")
            
            # Retry logic for transient errors
            await asyncio.sleep(self._retry_delay)
            return await self.execute_query(query, parameters)
            
        except Exception as e:
            self._update_performance_metrics(time.time() - start_time, success=False)
            self.logger.error(f"Error executing query: {str(e)}")
            raise
    
    def _update_performance_metrics(self, query_time: float, success: bool):
        """Update performance metrics"""
        self._performance_metrics['total_queries'] += 1
        self._performance_metrics['total_query_time'] += query_time
        
        if success:
            self._performance_metrics['successful_queries'] += 1
        else:
            self._performance_metrics['failed_queries'] += 1
        
        # Update average
        if self._performance_metrics['total_queries'] > 0:
            self._performance_metrics['avg_query_time'] = (
                self._performance_metrics['total_query_time'] / 
                self._performance_metrics['total_queries']
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self._performance_metrics.copy()

# =============================================================================
# DATA TRANSFORMATION LAYER
# =============================================================================

class DataTransformer:
    """Transform data from collectors to Neo4j-optimized format"""
    
    @staticmethod
    def transform_politician_data(politician_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Transform politician data for Neo4j storage (canonical numeric ID only)"""
        # Always use the official numeric ID from Eduskunta or raise an error
        final_id = str(politician_data.get('id', '')).strip()
        if not final_id.isdigit():
            raise ValueError(f"Invalid or missing numeric ID for politician: {politician_data}")
        return {
            'politician_id': final_id,
            'name': politician_data.get('name', ''),
            'first_name': politician_data.get('first_name', ''),
            'last_name': politician_data.get('last_name', ''),
            'current_party': politician_data.get('party', ''),
            'current_position': politician_data.get('position', ''),
            'constituency': politician_data.get('constituency', ''),
            'image_url': str(politician_data.get('image_url', '') or '').strip(),
            'is_active': politician_data.get('active', True),
            'contact_info': json.dumps(politician_data.get('contact', {})),
            'biography': politician_data.get('bio', ''),
            'wikipedia_url': politician_data.get('wikipedia_url', ''),
            'wikipedia_summary': politician_data.get('wikipedia_summary', ''),
            'wikipedia_image_url': politician_data.get('wikipedia_image_url', ''),
            'data_sources': [source],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def transform_article_data(article_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Transform news article data for Neo4j storage"""
        return {
            'article_id': article_data.get('id') or (hashlib.sha256(article_data.get('url', '').strip().lower().encode('utf-8')).hexdigest() if article_data.get('url') else None),
            'title': article_data.get('title', ''),
            'content': article_data.get('content', ''),
            'summary': article_data.get('summary', ''),
            'author': article_data.get('author', ''),
            'source': source,
            'published_date': article_data.get('published_date', datetime.now().isoformat()),
            'url': article_data.get('url', ''),
            'language': article_data.get('language', 'fi'),
            'word_count': len(article_data.get('content', '').split()),
            'sentiment_score': article_data.get('sentiment', 0.0),
            'political_relevance': article_data.get('political_relevance', 0.5),
            'mentioned_politicians': json.dumps(article_data.get('mentioned_politicians', [])),
            'mentioned_parties': json.dumps(article_data.get('mentioned_parties', [])),
            'tags': json.dumps(article_data.get('tags', [])),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def transform_party_data(party_data: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Transform political party data for Neo4j storage"""
        return {
            'party_id': party_data.get('id') or f"{source}_{party_data.get('name', '').replace(' ', '_')}",
            'name': party_data.get('name', ''),
            'short_name': party_data.get('short_name', ''),
            'ideology_score': party_data.get('ideology_score', 0.0),
            'coalition_status': party_data.get('coalition_status', 'independent'),
            'current_leader': party_data.get('leader', ''),
            'member_count': party_data.get('member_count', 0),
            'parliamentary_seats': party_data.get('seats', 0),
            'website': party_data.get('website', ''),
            'is_active': party_data.get('active', True),
            'data_sources': [source],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

# =============================================================================
# NEO4J WRITER - OPTIMIZED CRUD OPERATIONS
# =============================================================================

class Neo4jWriter:
    """High-performance Neo4j writer with batch operations and validation"""
    
    def __init__(self, connection_manager: Neo4jConnectionManager = None):
        self.connection_manager = connection_manager or Neo4jConnectionManager()
        self.transformer = DataTransformer()
        self.logger = logging.getLogger('neo4j_writer')
    
    async def initialize(self):
        """Initialize the writer"""
        return await self.connection_manager.initialize()
    
    async def create_politician(self, politician_data: Dict[str, Any], source: str) -> str:
        """Create or update politician node"""
        transformed_data = self.transformer.transform_politician_data(politician_data, source)
        
        # Use proper parameterized query with robust politician_id
        query = """
        MERGE (p:Politician {politician_id: $politician_id})
        SET p.name = $name,
            p.current_party = $current_party,
            p.constituency = $constituency,
            p.current_position = $current_position,
            p.image_url = $image_url,
            p.is_active = $is_active,
            p.first_name = $first_name,
            p.last_name = $last_name,
            p.contact_info = $contact_info,
            p.biography = $biography,
            p.data_sources = $data_sources,
            p.created_at = $created_at,
            p.updated_at = $updated_at
        RETURN p.politician_id as politician_id, p.image_url as image_url
        """
        
        result = await self.connection_manager.execute_query(
            query,
            transformed_data
        )
        
        return result[0]['politician_id'] if result else None
    
    async def create_article(self, article_data: Dict[str, Any], source: str) -> str:
        """Create or update article node"""
        transformed_data = self.transformer.transform_article_data(article_data, source)
        
        query = """
        MERGE (a:Article {url: $url})
        SET a += $properties
        RETURN a.article_id as article_id
        """
        
        result = await self.connection_manager.execute_query(
            query,
            {
                'url': transformed_data['url'],
                'properties': transformed_data
            }
        )
        
        return result[0]['article_id'] if result else None
    
    async def create_relationship(
        self,
        politician_id: str,
        article_url: str,
        relationship_type: RelationshipType,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Create relationship between Politician and Article"""
        properties = properties or {}
        properties['created_at'] = datetime.now().isoformat()

        self.logger.info(
            f"Creating relationship {relationship_type.value} between Politician(id={politician_id}) and Article(url={article_url})"
        )

        query = f"""
        MATCH (p:Politician {{id: $politician_id}}), (a:Article {{url: $article_url}})
        MERGE (p)-[r:{relationship_type.value}]->(a)
        SET r += $properties
        RETURN r
        """
        result = await self.connection_manager.execute_query(
            query,
            {
                'politician_id': politician_id,
                'article_url': article_url,
                'properties': properties
            }
        )
        return len(result) > 0
    
    async def batch_create_politicians(self, politicians_data: List[Dict[str, Any]], source: str) -> List[str]:
        """Batch create politicians for high performance (guaranteed unique IDs, robust error handling, and image/province correctness)"""
        batch_size = 100
        created_ids = []
        logger = self.logger
        logger.info(f"[BATCH IMPORT] Received {len(politicians_data)} politicians for import from source: {source}")

        # Log incoming politician IDs for debugging
        logger.info(f"[DEBUG] Received {len(politicians_data)} politicians. Sample IDs: {[p.get('politician_id') for p in politicians_data[:10]]}")
        # Deduplicate input by politician_id only (guaranteed unique, robust to int/str)
        deduped_dict = {}
        for p in politicians_data:
            pid = p.get('politician_id', '')
            if pid is None:
                continue
            pid_str = str(pid).strip()
            if not pid_str or pid_str.lower() in ('none', 'null', 'nan'):
                logger.warning(f"[SKIP] Invalid politician_id: {pid} in {p}")
                continue
            deduped_dict[pid_str] = p
        deduped = list(deduped_dict.values())
        logger.info(f"[BATCH IMPORT] Deduplicated to {len(deduped)} unique politicians by politician_id. Sample: {[p.get('politician_id') for p in deduped[:10]]}")

        for i in range(0, len(deduped), batch_size):
            batch = deduped[i:i + batch_size]
            transformed_batch = []
            for p in batch:
                t = self.transformer.transform_politician_data(p, source)
                # Guarantee unique, non-empty ID
                if not t['politician_id'] or not t['name']:
                    logger.warning(f"[SKIP] Empty ID or name: {t}")
                    continue
                transformed_batch.append(t)
            if not transformed_batch:
                logger.warning(f"[BATCH {i//batch_size+1}] No valid politicians in batch, skipping.")
                continue
            logger.info(f"[BATCH {i//batch_size+1}] Inserting {len(transformed_batch)} politicians. Sample: {[t['politician_id'] for t in transformed_batch[:3]]}")

            query = """
            UNWIND $politicians as politician
            MERGE (p:Politician {politician_id: politician.politician_id})
            SET p.name = politician.name,
                p.current_party = politician.current_party,
                p.constituency = politician.constituency,
                p.current_position = politician.current_position,
                p.image_url = CASE 
                    WHEN politician.image_url IS NOT NULL AND politician.image_url <> '' 
                    THEN politician.image_url 
                    ELSE p.image_url 
                END,
                p.is_active = politician.is_active,
                p.first_name = politician.first_name,
                p.last_name = politician.last_name,
                p.contact_info = politician.contact_info,
                p.biography = politician.biography,
                p.data_sources = politician.data_sources,
                p.created_at = politician.created_at,
                p.updated_at = politician.updated_at
            RETURN p.politician_id as politician_id, p.image_url as image_url, p.constituency as constituency
            """
            try:
                result = await self.connection_manager.execute_query(
                    query,
                    {'politicians': transformed_batch}
                )
                logger.info(f"[BATCH {i//batch_size+1}] Created {len(result)} politicians. Sample: {[r['politician_id'] for r in result[:3]]}")
                created_ids.extend([r['politician_id'] for r in result])
            except Exception as e:
                logger.error(f"[BATCH {i//batch_size+1}] ERROR: {str(e)}")
        logger.info(f"[BATCH IMPORT] Total politicians created: {len(created_ids)}")
        return created_ids

    
    async def close(self):
        """Close the writer"""
        await self.connection_manager.close()

# =============================================================================
# ANALYTICS QUERY ENGINE
# =============================================================================

class Neo4jAnalytics:
    """Advanced analytics queries for Finnish political analysis"""
    
    def __init__(self, connection_manager: Neo4jConnectionManager = None):
        self.connection_manager = connection_manager or Neo4jConnectionManager()
        self.logger = logging.getLogger('neo4j_analytics')
    
    async def get_coalition_analysis(self) -> List[Dict[str, Any]]:
        """Analyze cross-party collaborations for coalition detection"""
        query = """
        MATCH (p1:Politician)-[c:COLLABORATES_WITH]-(p2:Politician)
        WHERE p1.current_party <> p2.current_party
        WITH p1.current_party as party1, p2.current_party as party2, 
             count(c) as collaborations, avg(c.strength) as avg_strength
        WHERE collaborations >= 3
        RETURN party1, party2, collaborations, avg_strength
        ORDER BY collaborations DESC, avg_strength DESC
        """
        
        return await self.connection_manager.execute_query(query)
    
    async def get_influence_network(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get political influence network analysis"""
        query = """
        MATCH (p:Politician)-[r:COLLABORATES_WITH|INFLUENCES]-(other:Politician)
        WITH p, count(r) as connections, avg(r.strength) as avg_influence
        WHERE connections >= 5
        RETURN p.name as politician, p.current_party as party, 
               connections, avg_influence,
               p.current_position as position
        ORDER BY connections DESC, avg_influence DESC
        LIMIT $limit
        """
        
        return await self.connection_manager.execute_query(query, {'limit': limit})
    
    async def get_media_coverage_analysis(self, days: int = 30) -> List[Dict[str, Any]]:
        """Analyze media coverage patterns"""
        query = """
        MATCH (a:Article)-[m:MENTIONS]-(p:Politician)
        WHERE date(a.published_date) >= date() - duration({days: $days})
        WITH p, count(a) as mentions, avg(m.sentiment) as avg_sentiment,
             avg(a.political_relevance) as avg_relevance
        WHERE mentions >= 5
        RETURN p.name as politician, p.current_party as party,
               mentions, avg_sentiment, avg_relevance
        ORDER BY mentions DESC
        """
        
        return await self.connection_manager.execute_query(query, {'days': days})
    
    async def get_policy_alignment_clusters(self) -> List[Dict[str, Any]]:
        """Analyze policy alignment patterns"""
        query = """
        MATCH (p:Politician)-[s:SUPPORTS_POLICY]-(pt:PolicyTopic)
        WITH pt, collect({
            politician: p.name, 
            party: p.current_party, 
            strength: s.strength
        }) as supporters
        WHERE size(supporters) >= 3
        RETURN pt.name as policy_topic, pt.category as category,
               supporters, size(supporters) as supporter_count
        ORDER BY supporter_count DESC
        """
        
        return await self.connection_manager.execute_query(query)

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

# Global instances for easy access
_neo4j_manager = None
_neo4j_writer = None
_neo4j_analytics = None

async def get_neo4j_manager() -> Neo4jConnectionManager:
    """Get singleton Neo4j connection manager"""
    global _neo4j_manager
    if _neo4j_manager is None:
        _neo4j_manager = Neo4jConnectionManager()
        await _neo4j_manager.initialize()
    return _neo4j_manager

async def get_neo4j_writer() -> Neo4jWriter:
    """Get singleton Neo4j writer"""
    global _neo4j_writer
    if _neo4j_writer is None:
        manager = await get_neo4j_manager()
        _neo4j_writer = Neo4jWriter(manager)
        await _neo4j_writer.initialize()
    return _neo4j_writer

async def get_neo4j_analytics() -> Neo4jAnalytics:
    """Get singleton Neo4j analytics engine"""
    global _neo4j_analytics
    if _neo4j_analytics is None:
        manager = await get_neo4j_manager()
        _neo4j_analytics = Neo4jAnalytics(manager)
    return _neo4j_analytics

# =============================================================================
# HEALTH CHECK & MONITORING
# =============================================================================

async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for Neo4j integration"""
    try:
        manager = await get_neo4j_manager()
        
        # Test basic connectivity
        test_query = "RETURN 'Neo4j is healthy' as status, datetime() as timestamp"
        result = await manager.execute_query(test_query)
        
        # Get performance metrics
        metrics = manager.get_performance_metrics()
        
        return {
            'status': 'healthy',
            'neo4j_response': result[0] if result else None,
            'performance_metrics': metrics,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
