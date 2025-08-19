from typing import List, Dict, Any
from datetime import datetime
import logging
import os
from database.neo4j_integration import RelationshipType
from urllib.parse import urlparse
from inspect import iscoroutinefunction, isawaitable
from .advanced_verifier import AdvancedContentVerifier

from .yle_news_collector import YleNewsCollector
from .yle_web_scraper_collector import YleWebScraperCollector
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
                YleWebScraperCollector(),
                HelsingingSanomatCollector(),
                IltalehtCollector(),
                MTVUutisetCollector(),
                KauppalehtiCollector()
            ]
        self.collectors = collectors
        self.neo4j_writer = neo4j_writer  # Should be an instance of Neo4jWriter
        # Optional advanced hate-speech detector (feature-flag)
        self.advanced_verifier = None
        if str(os.getenv("ENABLE_HATE_SPEECH_DETECTOR", "")).strip().lower() in ("1", "true", "yes", "on"):
            try:
                self.advanced_verifier = AdvancedContentVerifier()
                self.logger.info("AdvancedContentVerifier enabled (hate-speech detection)")
            except Exception as e:
                self.logger.warning(f"Failed to initialize AdvancedContentVerifier: {e}")
        self.logger.info(f"Initialized with collectors: {[c.__class__.__name__ for c in self.collectors]}")

    async def enrich_and_store_politician_news(self, politician_id: str, politician_name: str, start_date: str = None, end_date: str = None, limit: int = 50) -> list:
        all_articles = []
        for collector in self.collectors:
            try:
                articles = await self._maybe_async_call(collector.get_politician_articles, politician_name, start_date, end_date, limit)
                all_articles.extend(articles)
            except Exception as e:
                self.logger.error(f"[{collector.__class__.__name__}] Error: {e}")
        deduped = self.deduplicate_articles(all_articles)
        # Lightweight verification/annotation before storage
        verified = []
        for art in deduped:
            try:
                annotations = self.verify_article(art)
                art.update(annotations)
            except Exception as ve:
                self.logger.warning(f"Verification failed for article {art.get('url','')}: {ve}")
            verified.append(art)
        # Store in Neo4j
        if self.neo4j_writer:
            await self._upsert_articles_and_relationships(politician_id, verified)
        return verified

    async def _upsert_articles_and_relationships(self, politician_id: str, articles: list):
        if not articles:
            return
            
        # Process articles in batches for better performance
        batch_size = 10
        total_articles = len(articles)
        self.logger.info(f"Processing {total_articles} articles in batches of {batch_size}")
        
        # First batch create all articles
        try:
            article_batch = []
            for article in articles:
                article_batch.append({
                    "url": article.get('url', ''),
                    "title": article.get('title', ''),
                    "content": article.get('content', ''),
                    "summary": article.get('summary', ''),
                    "published_date": article.get('published_date', ''),
                    "source": article.get('source', 'unknown'),
                    "is_fake_news": article.get('is_fake_news'),
                    "is_malicious_content": article.get('is_malicious_content'),
                    "contains_hate_speech": article.get('contains_hate_speech'),
                    "is_ai_generated": article.get('is_ai_generated'),
                })
                
                # Process in batches
                if len(article_batch) >= batch_size:
                    await self.neo4j_writer.batch_create_articles(article_batch)
                    article_batch = []
            
            # Process any remaining articles
            if article_batch:
                await self.neo4j_writer.batch_create_articles(article_batch)
                
            # Now create all relationships in a single batch
            relationships = []
            for article in articles:
                relationships.append({
                    "politician_id": politician_id,
                    "article_url": article.get('url', ''),
                    "relationship_type": RelationshipType.MENTIONS.value
                })
                
            if relationships:
                await self.neo4j_writer.batch_create_politician_article_relationships(relationships)
                
            self.logger.info(f"Successfully processed {total_articles} articles and created {len(relationships)} relationships")
                
        except Exception as e:
            self.logger.error(f"Error in batch processing articles or relationships: {e}")

    def verify_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform lightweight, conservative verification checks without external dependencies.
        This annotates the article with fields expected by the transformer/writer:
        - is_fake_news, is_malicious_content, contains_hate_speech, is_ai_generated
        - verification_confidence, verification_notes, verified_at, verification_source

        Heuristics:
        - Trust known mainstream Finnish sources lowers fake/malicious likelihood.
        - AI-generated: flag if author/source self-identifies as automated.
        - Hate speech: no in-code slur list; left as None to avoid false positives.
        """
        known_source_names = {
            'yle', 'helsingin sanomat', 'iltalehti', 'mtv uutiset', 'kauppalehti'
        }
        trusted_domains = {
            'yle.fi', 'hs.fi', 'iltalehti.fi', 'mtvuutiset.fi', 'kauppalehti.fi'
        }

        source = str(article.get('source', '')).strip()
        source_l = source.lower()
        author = str(article.get('author', '')).strip().lower()
        content = str(article.get('content', '')).strip().lower()
        url = str(article.get('url', '')).strip()
        hostname = urlparse(url).hostname or ''
        host_l = hostname.lower().lstrip('www.')

        # Fake/malicious conservative defaults based on domain trust + source name
        trusted_source = (
            any(name in source_l for name in known_source_names) or
            any(host_l == d or host_l.endswith('.' + d) for d in trusted_domains)
        )
        is_fake_news = False if trusted_source else None
        is_malicious_content = None

        # AI-generated heuristic (very conservative)
        ai_indicators = ['automated', 'generated by ai', 'ai-generated', 'gpt', 'chatgpt']
        is_ai_generated = True if any(tok in author or tok in content for tok in ai_indicators) else None

        # Hate speech detection (optional advanced verifier)
        contains_hate_speech = None
        hs_terms = []
        hs_score = 0.0
        if self.advanced_verifier:
            try:
                combined_text = f"{article.get('title','')}\n\n{article.get('content','')}"
                flag, score, matches = self.advanced_verifier.detect_hate_speech(combined_text)
                if flag:
                    contains_hate_speech = True
                    hs_score = float(score)
                    hs_terms = matches
            except Exception as ae:
                self.logger.warning(f"Advanced hate-speech detection failed: {ae}")

        notes = []
        if trusted_source:
            notes.append('trusted_source')
        if is_ai_generated:
            notes.append('ai_indicator_detected')
        if host_l:
            notes.append(f'domain:{host_l}')
        if contains_hate_speech:
            notes.append('hate_detected')
            if hs_terms:
                notes.append('hate_terms:' + '|'.join(hs_terms[:5]))

        # Confidence: raise slightly if hate detected
        base_conf = 0.2 if not trusted_source else 0.6
        if contains_hate_speech:
            base_conf = max(base_conf, min(0.95, 0.6 + hs_score * 0.3))

        return {
            'is_fake_news': is_fake_news,
            'is_malicious_content': is_malicious_content,
            'contains_hate_speech': contains_hate_speech,
            'is_ai_generated': is_ai_generated,
            'verification_confidence': base_conf,
            'verification_notes': ','.join(notes),
            'verified_at': datetime.now().isoformat(),
            'verification_source': 'heuristic_v1_domain_trust' + ('+hate_v1' if self.advanced_verifier else '')
        }

    @staticmethod
    async def _maybe_async_call(func, *args, **kwargs):
        # Support both async and sync collectors robustly
        try:
            if iscoroutinefunction(func):
                return await func(*args, **kwargs)
            result = func(*args, **kwargs)
            if isawaitable(result):
                return await result
            return result
        except Exception:
            # Re-raise to caller; verification loop handles per-collector errors
            raise

    @staticmethod
    def deduplicate_articles(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for article in articles:
            url = article.get('url', '').strip().lower()
            if url and url not in seen:
                seen.add(url)
                deduped.append(article)
        return deduped
