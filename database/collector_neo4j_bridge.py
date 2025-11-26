"""
Data Collection Bridge to Neo4j
Connects all 11 collectors to the optimized Neo4j integration layer
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'data_collection'))

from database.neo4j_integration import (
    Neo4jWriter, DataTransformer, RelationshipType,
    get_neo4j_writer, get_neo4j_manager
)

# Import all 9 collectors (removed broken Kuntaliitto and Vaalikone)
from politicians.eduskunta_collector import EduskuntaCollector

from news.yle_news_collector import YleNewsCollector
from news.helsingin_sanomat_collector import HelsingingSanomatCollector
from news.iltalehti_collector import IltalehtCollector
from news.kauppalehti_collector import KauppalehtiCollector
from news.mtv_uutiset_collector import MTVUutisetCollector

from secondary.wikipedia_person_collector import WikipediaPersonCollector

class CollectorNeo4jBridge:
    """
    Bridge between data collectors and Neo4j integration
    Handles data validation, transformation, and batch processing
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j_writer = None
        self.transformer = DataTransformer()
        
        # Initialize all 9 collectors (removed broken Kuntaliitto and Vaalikone)
        self.collectors = {
            # Politicians (1 collector - primary source)
            'eduskunta': EduskuntaCollector(),
            
            # News (5 collectors)
            'yle': YleNewsCollector(),
            'helsingin_sanomat': HelsingingSanomatCollector(),
            'iltalehti': IltalehtCollector(),
            'kauppalehti': KauppalehtiCollector(),
            'mtv_uutiset': MTVUutisetCollector(),
            
            # Secondary (1 collector)
            'wikipedia': WikipediaPersonCollector()
        }
        
        self.processing_stats = {
            'total_politicians_processed': 0,
            'total_articles_processed': 0,
            'total_relationships_created': 0,
            'processing_errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def initialize(self):
        """Initialize the bridge with Neo4j connection"""
        try:
            self.neo4j_writer = await get_neo4j_writer()
            self.logger.info("CollectorNeo4jBridge initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize bridge: {str(e)}")
            return False
    
    async def collect_and_store_politicians(self, 
                                          sources: List[str] = None, 
                                          limit: int = 100) -> Dict[str, Any]:
        """
        Collect politician data from specified sources and store in Neo4j
        
        Args:
            sources: List of collector names to use (default: all politician collectors)
            limit: Maximum number of politicians per source
            
        Returns:
            Dictionary with processing results
        """
        if sources is None:
            sources = ['eduskunta']  # Only working politician collector
        
        self.processing_stats['start_time'] = datetime.now()
        results = {
            'success': True,
            'sources_processed': [],
            'politicians_created': [],
            'errors': []
        }
        
        for source in sources:
            if source not in self.collectors:
                self.logger.warning(f"Unknown collector source: {source}")
                continue
            
            try:
                self.logger.info(f"Collecting politicians from {source}...")
                collector = self.collectors[source]
                
                # Collect data from source
                if hasattr(collector, 'get_politicians'):
                    raw_politicians = await self._safe_collect(
                        collector.get_politicians
                    )
                    # Apply limit after collection
                    if raw_politicians and limit:
                        raw_politicians = raw_politicians[:limit]
                elif hasattr(collector, 'collect_data'):
                    raw_data = await self._safe_collect(
                        collector.collect_data
                    )
                    raw_politicians = raw_data.get('politicians', []) if raw_data else []
                    # Apply limit after collection
                    if raw_politicians and limit:
                        raw_politicians = raw_politicians[:limit]
                else:
                    self.logger.warning(f"Collector {source} has no suitable collection method")
                    continue
                
                if not raw_politicians:
                    self.logger.warning(f"No politicians collected from {source}")
                    continue
                
                # Transform and validate data
                validated_politicians = []
                for politician in raw_politicians:
                    try:
                        validated_politician = self._validate_politician_data(politician)
                        if validated_politician:
                            validated_politicians.append(validated_politician)
                    except Exception as e:
                        self.logger.error(f"Validation error for politician from {source}: {str(e)}")
                        self.processing_stats['processing_errors'] += 1
                
                # Batch store in Neo4j
                if validated_politicians:
                    created_ids = await self.neo4j_writer.batch_create_politicians(
                        validated_politicians, source
                    )
                    
                    results['politicians_created'].extend(created_ids)
                    self.processing_stats['total_politicians_processed'] += len(created_ids)
                    
                    self.logger.info(f"Successfully stored {len(created_ids)} politicians from {source}")
                
                results['sources_processed'].append(source)
                
            except Exception as e:
                error_msg = f"Error processing {source}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                self.processing_stats['processing_errors'] += 1
        
        self.processing_stats['end_time'] = datetime.now()
        return results
    
    async def collect_and_store_articles(self, 
                                       sources: List[str] = None, 
                                       limit: int = 50) -> Dict[str, Any]:
        """
        Collect news articles from specified sources and store in Neo4j
        
        Args:
            sources: List of collector names to use (default: all news collectors)
            limit: Maximum number of articles per source
            
        Returns:
            Dictionary with processing results
        """
        if sources is None:
            sources = ['yle', 'helsingin_sanomat', 'iltalehti', 'kauppalehti', 'mtv_uutiset']
        
        results = {
            'success': True,
            'sources_processed': [],
            'articles_created': [],
            'errors': []
        }
        
        for source in sources:
            if source not in self.collectors:
                self.logger.warning(f"Unknown collector source: {source}")
                continue
            
            try:
                self.logger.info(f"Collecting articles from {source}...")
                collector = self.collectors[source]
                
                # Always use get_politician_articles for news collectors
                politician_name = "Sanna Marin"  # For pipeline runs, this can be parameterized
                if hasattr(collector, 'get_politician_articles'):
                    raw_articles = await self._safe_collect(
                        collector.get_politician_articles,
                        politician_name=politician_name,
                        limit=limit
                    )
                else:
                    self.logger.warning(f"Collector {source} has no get_politician_articles method")
                    continue

                if not raw_articles:
                    self.logger.warning(f"No articles collected from {source}")
                    continue
                
                # Transform and validate data
                validated_articles = []
                for article in raw_articles:
                    try:
                        validated_article = self._validate_article_data(article)
                        if validated_article:
                            validated_articles.append(validated_article)
                    except Exception as e:
                        self.logger.error(f"Validation error for article from {source}: {str(e)}")
                        self.processing_stats['processing_errors'] += 1
                
                # Store articles in Neo4j
                created_ids = []
                for article in validated_articles:
                    try:
                        article_id = await self.neo4j_writer.create_article(article, source)
                        if article_id:
                            created_ids.append(article_id)
                    except Exception as e:
                        self.logger.error(f"Error storing article: {str(e)}")
                        self.processing_stats['processing_errors'] += 1
                
                results['articles_created'].extend(created_ids)
                self.processing_stats['total_articles_processed'] += len(created_ids)
                
                self.logger.info(f"Successfully stored {len(created_ids)} articles from {source}")
                results['sources_processed'].append(source)
                
            except Exception as e:
                error_msg = f"Error processing {source}: {str(e)}"
                self.logger.error(error_msg)
                results['errors'].append(error_msg)
                self.processing_stats['processing_errors'] += 1
        
        return results
    
    async def create_politician_article_relationships(self, 
                                                    politician_ids: List[str], 
                                                    article_ids: List[str]) -> int:
        """
        Create MENTIONS relationships between politicians and articles
        
        Args:
            politician_ids: List of politician IDs
            article_ids: List of article IDs
            
        Returns:
            Number of relationships created
        """
        relationships_created = 0
        
        try:
            # Get Neo4j manager for complex queries
            manager = await get_neo4j_manager()
            
            # Query to find politician mentions in articles
            query = """
            MATCH (p:Politician), (a:Article)
            WHERE p.politician_id IN $politician_ids 
            AND a.article_id IN $article_ids
            AND (
                toLower(a.title) CONTAINS toLower(p.name) OR
                toLower(a.content) CONTAINS toLower(p.name) OR
                p.name IN apoc.convert.fromJsonList(a.mentioned_politicians)
            )
            MERGE (a)-[r:MENTIONS]->(p)
            SET r.created_at = datetime(),
                r.detection_method = 'content_analysis'
            RETURN count(r) as relationships_created
            """
            
            result = await manager.execute_query(query, {
                'politician_ids': politician_ids,
                'article_ids': article_ids
            })
            
            if result:
                relationships_created = result[0]['relationships_created']
                self.processing_stats['total_relationships_created'] += relationships_created
                self.logger.info(f"Created {relationships_created} politician-article relationships")
            
        except Exception as e:
            self.logger.error(f"Error creating relationships: {str(e)}")
            self.processing_stats['processing_errors'] += 1
        
        return relationships_created
    
    async def run_complete_data_ingestion(self, 
                                        politician_limit: int = 100,
                                        article_limit: int = 50) -> Dict[str, Any]:
        """
        Run complete data ingestion from all 11 collectors
        
        Args:
            politician_limit: Maximum politicians per source
            article_limit: Maximum articles per source
            
        Returns:
            Comprehensive processing results
        """
        self.logger.info("Starting complete data ingestion from all 11 collectors...")
        self.processing_stats['start_time'] = datetime.now()
        
        # Step 1: Collect and store politicians
        self.logger.info("Phase 1: Collecting politicians from 3 sources...")
        politician_results = await self.collect_and_store_politicians(limit=politician_limit)
        
        # Step 2: Collect and store articles
        self.logger.info("Phase 2: Collecting articles from 5 news sources...")
        article_results = await self.collect_and_store_articles(limit=article_limit)
        
        # Step 3: Create relationships
        self.logger.info("Phase 3: Creating politician-article relationships...")
        relationships_created = 0
        if politician_results['politicians_created'] and article_results['articles_created']:
            relationships_created = await self.create_politician_article_relationships(
                politician_results['politicians_created'],
                article_results['articles_created']
            )
        
        # Step 4: Collect Wikipedia data for enrichment
        self.logger.info("Phase 4: Enriching with Wikipedia data...")
        wikipedia_results = await self._collect_wikipedia_enrichment()
        
        self.processing_stats['end_time'] = datetime.now()
        duration = (self.processing_stats['end_time'] - self.processing_stats['start_time']).total_seconds()
        
        # Compile comprehensive results
        results = {
            'success': True,
            'processing_duration_seconds': duration,
            'statistics': self.processing_stats.copy(),
            'politician_results': politician_results,
            'article_results': article_results,
            'relationships_created': relationships_created,
            'wikipedia_enrichment': wikipedia_results,
            'summary': {
                'total_politicians': len(politician_results['politicians_created']),
                'total_articles': len(article_results['articles_created']),
                'total_relationships': relationships_created,
                'sources_processed': {
                    'politician_sources': politician_results['sources_processed'],
                    'news_sources': article_results['sources_processed'],
                    'secondary_sources': ['wikipedia'] if wikipedia_results['success'] else []
                },
                'error_count': self.processing_stats['processing_errors']
            }
        }
        
        self.logger.info(f"Complete data ingestion finished in {duration:.2f} seconds")
        self.logger.info(f"Processed: {results['summary']['total_politicians']} politicians, "
                        f"{results['summary']['total_articles']} articles, "
                        f"{results['summary']['total_relationships']} relationships")
        
        return results
    
    async def _collect_wikipedia_enrichment(self) -> Dict[str, Any]:
        """Collect Wikipedia data for politician enrichment (force update all)"""
        import json
        try:
            wikipedia_collector = self.collectors['wikipedia']
            manager = await get_neo4j_manager()
            existing_politicians = await manager.execute_query(
                "MATCH (p:Politician) RETURN p.name as name, p.politician_id as id"
            )
            self.logger.info(f"[ENRICHMENT] Found {len(existing_politicians)} politicians to enrich.")
            enriched_count = 0
            for politician in existing_politicians:
                self.logger.info(f"[ENRICHMENT] Attempting: {politician['name']} ({politician['id']})")
                try:
                    info = wikipedia_collector.get_info(politician['name'])
                    if info and not info.get('error'):
                        update_query = """
                        MATCH (p:Politician {politician_id: $politician_id})
                        SET p.wikipedia_url = $wikipedia_url,
                            p.wikipedia_summary = $wikipedia_summary,
                            p.wikipedia_image_url = $wikipedia_image_url,
                            p.updated_at = datetime()
                        RETURN p.politician_id
                        """
                        await manager.execute_query(update_query, {
                            'politician_id': politician['id'],
                            'wikipedia_url': info.get('wikipedia_url', ''),
                            'wikipedia_summary': info.get('wikipedia_summary', ''),
                            'wikipedia_image_url': info.get('wikipedia_image_url', ''),
                        })
                        enriched_count += 1
                    else:
                        self.logger.warning(f"No Wikipedia data for {politician['name']}")
                except Exception as e:
                    self.logger.error(f"Error enriching politician {politician['name']}: {str(e)}")
            return {
                'success': True,
                'politicians_enriched': enriched_count
            }
        except Exception as e:
            self.logger.error(f"Wikipedia enrichment failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_politician_data(self, politician_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and clean politician data"""
        if not politician_data.get('name'):
            return None
        
        # Ensure required fields
        validated = {
            'name': politician_data.get('name', '').strip(),
            'party': politician_data.get('party', '').strip(),
            'position': politician_data.get('position', '').strip(),
            'constituency': politician_data.get('constituency', '').strip(),
            'bio': politician_data.get('bio', '').strip(),
            'active': politician_data.get('active', True),
        }
        
        # Handle image_url with special care
        original_image_url = politician_data.get('image_url', '')
        validated_image_url = str(original_image_url or '').strip()
        validated['image_url'] = validated_image_url
        
        # Log image URL validation for debugging
        if original_image_url != validated_image_url:
            self.logger.warning(f"[IMAGE_URL_VALIDATION] Image URL modified during validation for {politician_data.get('name')}: '{original_image_url}' -> '{validated_image_url}'")
        else:
            self.logger.debug(f"[IMAGE_URL_VALIDATION] Image URL preserved for {politician_data.get('name')}: '{validated_image_url}'")

        # Preserve and validate politician_id
        pid = politician_data.get('politician_id')
        if pid is not None:
            pid_str = str(pid).strip()
            if pid_str and pid_str.lower() not in ('none', 'null', 'nan'):
                validated['politician_id'] = pid_str
            else:
                self.logger.warning(f"[VALIDATION] Skipping invalid politician_id: {pid} for {politician_data.get('name')}")
        else:
            self.logger.warning(f"[VALIDATION] Missing politician_id for {politician_data.get('name')}")

        # Add optional fields if present
        for field in ['first_name', 'last_name', 'contact', 'id']:
            if field in politician_data:
                validated[field] = politician_data[field]

        # Log validated data for debugging
        self.logger.debug(f"[VALIDATION] Validated politician: name={validated.get('name')}, politician_id={validated.get('politician_id')}, image_url={validated.get('image_url')}")
        return validated
    
    def _validate_article_data(self, article_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Validate and clean article data"""
        if not article_data.get('title') or not article_data.get('url'):
            return None
        
        # Ensure required fields
        validated = {
            'title': article_data.get('title', '').strip(),
            'content': article_data.get('content', '').strip(),
            'url': article_data.get('url', '').strip(),
            'author': article_data.get('author', '').strip(),
            'published_date': article_data.get('published_date', datetime.now().isoformat())
        }
        
        # Add optional fields if present
        for field in ['summary', 'sentiment', 'political_relevance', 'tags', 'id']:
            if field in article_data:
                validated[field] = article_data[field]
        
        return validated
    
    async def _safe_collect(self, collect_method, **kwargs):
        """Safely execute collector method with error handling"""
        try:
            if asyncio.iscoroutinefunction(collect_method):
                return await collect_method(**kwargs)
            else:
                return collect_method(**kwargs)
        except Exception as e:
            self.logger.error(f"Collection method failed: {str(e)}")
            return None
    
    async def close(self):
        """Close the bridge and cleanup resources"""
        if self.neo4j_writer:
            await self.neo4j_writer.close()
        self.logger.info("CollectorNeo4jBridge closed")

# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

async def run_full_data_ingestion(politician_limit: int = 200, 
                                 article_limit: int = 50) -> Dict[str, Any]:
    """
    Convenience function to run complete data ingestion
    
    Args:
        politician_limit: Maximum politicians per source
        article_limit: Maximum articles per source
        
    Returns:
        Comprehensive processing results
    """
    bridge = CollectorNeo4jBridge()
    
    try:
        await bridge.initialize()
        results = await bridge.run_complete_data_ingestion(
            politician_limit=politician_limit,
            article_limit=article_limit
        )
        return results
    finally:
        await bridge.close()

async def quick_politician_sync(sources: List[str] = None, limit: int = 50) -> Dict[str, Any]:
    """
    Quick sync of politician data from specified sources
    
    Args:
        sources: List of collector names (default: all politician collectors)
        limit: Maximum politicians per source
        
    Returns:
        Processing results
    """
    bridge = CollectorNeo4jBridge()
    
    try:
        await bridge.initialize()
        results = await bridge.collect_and_store_politicians(sources=sources, limit=limit)
        return results
    finally:
        await bridge.close()

async def quick_news_sync(sources: List[str] = None, limit: int = 30) -> Dict[str, Any]:
    """
    Quick sync of news articles from specified sources
    
    Args:
        sources: List of collector names (default: all news collectors)
        limit: Maximum articles per source
        
    Returns:
        Processing results
    """
    bridge = CollectorNeo4jBridge()
    
    try:
        await bridge.initialize()
        results = await bridge.collect_and_store_articles(sources=sources, limit=limit)
        return results
    finally:
        await bridge.close()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Main execution for testing the bridge"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 Testing Collector-Neo4j Bridge")
    print("=" * 50)
    
    # Run full data ingestion
    results = await run_full_data_ingestion(politician_limit=200, article_limit=10)
    
    print("\n📊 INGESTION RESULTS:")
    print(f"   Politicians: {results['summary']['total_politicians']}")
    print(f"   Articles: {results['summary']['total_articles']}")
    print(f"   Relationships: {results['summary']['total_relationships']}")
    print(f"   Duration: {results['processing_duration_seconds']:.2f} seconds")
    print(f"   Errors: {results['summary']['error_count']}")
    
    print("\n✅ Bridge testing completed!")

if __name__ == "__main__":
    asyncio.run(main())
