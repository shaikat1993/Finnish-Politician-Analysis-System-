from typing import List, Dict, Any
from datetime import datetime
import logging

from .yle_news_collector import YleNewsCollector
from .helsingin_sanomat_collector import HelsingingSanomatCollector
from .iltalehti_collector import IltalehtCollector
from .mtv_uutiset_collector import MTVUutisetCollector
from .kauppalehti_collector import KauppalehtiCollector

class UnifiedNewsEnricher:
    """
    Aggregates news from all collectors, deduplicates, and upserts to Neo4j.
    """
    def __init__(self, collectors=None, neo4j_writer=None):
        self.logger = logging.getLogger("unified_news_enricher")
        if collectors is None:
            collectors = [
                YleNewsCollector(),
                HelsingingSanomatCollector(),
                IltalehtCollector(),
                MTVUutisetCollector(),
                KauppalehtiCollector()
            ]
        self.collectors = collectors
        self.neo4j_writer = neo4j_writer  # Should be an instance of Neo4jWriter

    async def enrich_and_store_politician_news(self, politician_id: str, politician_name: str, start_date: str = None, end_date: str = None, limit: int = 50) -> list:
        all_articles = []
        for collector in self.collectors:
            try:
                articles = await self._maybe_async_call(collector.get_politician_articles, politician_name, start_date, end_date, limit)
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"[{collector.__class__.__name__}] Error: {e}")
        deduped = self.deduplicate_articles(all_articles)
        # Store in Neo4j
        if self.neo4j_writer:
            await self._upsert_articles_and_relationships(politician_id, deduped)
        return deduped

    async def _upsert_articles_and_relationships(self, politician_id: str, articles: list):
        for article in articles:
            try:
                article_id = await self.neo4j_writer.create_article(article, article.get('source', 'unknown'))
                if article_id:
                    # Relationship: (:Politician)-[:MENTIONS]->(:Article)
                    await self.neo4j_writer.create_relationship(
                        from_id=politician_id,
                        to_id=article_id,
                        relationship_type=getattr(self.neo4j_writer, 'RelationshipType', None) or 'MENTIONS',
                        properties={}
                    )
            except Exception as e:
                self.logger.error(f"Error upserting article or relationship: {e}")

    @staticmethod
    async def _maybe_async_call(func, *args, **kwargs):
        # Support both async and sync collectors
        if hasattr(func, "__await__") or hasattr(func, "__code__") and func.__code__.co_flags & 0x80:
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    @staticmethod
    def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for article in articles:
            key = (article.get('title', '').strip().lower(), article.get('url', '').strip())
            if key not in seen:
                seen.add(key)
                deduped.append(article)
        return deduped
