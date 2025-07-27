"""
Relationship Extractor
Extracts and creates relationships between politicians, news articles, and other entities.
"""

import logging
from typing import List, Dict, Any, Tuple, Set
from datetime import datetime
import re

class RelationshipExtractor:
    """
    Extracts relationships between entities (politicians, news articles, parties, etc.)
    for Neo4j graph database storage.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.politician_patterns = self._build_politician_patterns()
        self.party_patterns = self._build_party_patterns()
        
    def extract_relationships(self, documents: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Extract all relationships from processed documents
        
        Args:
            documents: List of processed document dictionaries
            
        Returns:
            Dictionary containing different relationship types
        """
        relationships = {
            'politician_mentions': [],
            'party_affiliations': [],
            'article_politician_links': [],
            'politician_collaborations': [],
            'topic_associations': [],
            'geographic_connections': []
        }
        
        # Group documents by type for efficient processing
        politicians = [doc for doc in documents if doc.get('metadata', {}).get('type') == 'politician']
        news_articles = [doc for doc in documents if doc.get('metadata', {}).get('type') == 'news_article']
        
        # Extract different types of relationships
        relationships['politician_mentions'] = self._extract_politician_mentions(news_articles, politicians)
        relationships['party_affiliations'] = self._extract_party_affiliations(politicians)
        relationships['article_politician_links'] = self._extract_article_politician_links(news_articles, politicians)
        relationships['politician_collaborations'] = self._extract_politician_collaborations(politicians, news_articles)
        relationships['topic_associations'] = self._extract_topic_associations(documents)
        relationships['geographic_connections'] = self._extract_geographic_connections(politicians)
        
        total_relationships = sum(len(rel_list) for rel_list in relationships.values())
        self.logger.info(f"Extracted {total_relationships} relationships across {len(relationships)} types")
        
        return relationships
    
    def _extract_politician_mentions(self, news_articles: List[Dict], politicians: List[Dict]) -> List[Dict]:
        """Extract mentions of politicians in news articles"""
        mentions = []
        
        # Create politician name lookup
        politician_lookup = {}
        for politician in politicians:
            metadata = politician.get('metadata', {})
            name = metadata.get('name', '').lower()
            if name:
                politician_lookup[name] = metadata.get('politician_id')
        
        for article in news_articles:
            article_metadata = article.get('metadata', {})
            article_content = article.get('page_content', '').lower()
            
            for politician_name, politician_id in politician_lookup.items():
                if politician_name in article_content:
                    mentions.append({
                        'type': 'MENTIONED_IN',
                        'source_id': politician_id,
                        'source_type': 'politician',
                        'target_id': article_metadata.get('article_id'),
                        'target_type': 'news_article',
                        'context': self._extract_mention_context(article_content, politician_name),
                        'confidence': self._calculate_mention_confidence(article_content, politician_name),
                        'extracted_at': datetime.now().isoformat()
                    })
        
        return mentions
    
    def _extract_party_affiliations(self, politicians: List[Dict]) -> List[Dict]:
        """Extract party affiliation relationships"""
        affiliations = []
        
        for politician in politicians:
            metadata = politician.get('metadata', {})
            politician_id = metadata.get('politician_id')
            party = metadata.get('party')
            
            if politician_id and party:
                affiliations.append({
                    'type': 'MEMBER_OF',
                    'source_id': politician_id,
                    'source_type': 'politician',
                    'target_id': self._normalize_party_id(party),
                    'target_type': 'party',
                    'party_name': party,
                    'extracted_at': datetime.now().isoformat()
                })
        
        return affiliations
    
    def _extract_article_politician_links(self, news_articles: List[Dict], politicians: List[Dict]) -> List[Dict]:
        """Extract direct links between articles and politicians they discuss"""
        links = []
        
        for article in news_articles:
            article_metadata = article.get('metadata', {})
            mentioned_politicians = article_metadata.get('mentioned_politicians', [])
            
            for politician_mention in mentioned_politicians:
                # Find matching politician
                matching_politician = self._find_politician_by_name(politicians, politician_mention)
                if matching_politician:
                    links.append({
                        'type': 'DISCUSSES',
                        'source_id': article_metadata.get('article_id'),
                        'source_type': 'news_article',
                        'target_id': matching_politician.get('metadata', {}).get('politician_id'),
                        'target_type': 'politician',
                        'relevance_score': article_metadata.get('political_relevance', 0.0),
                        'sentiment': article_metadata.get('sentiment', 'neutral'),
                        'extracted_at': datetime.now().isoformat()
                    })
        
        return links
    
    def _extract_politician_collaborations(self, politicians: List[Dict], news_articles: List[Dict]) -> List[Dict]:
        """Extract collaboration relationships between politicians"""
        collaborations = []
        
        # Find politicians mentioned together in articles
        politician_cooccurrences = {}
        
        for article in news_articles:
            mentioned = article.get('metadata', {}).get('mentioned_politicians', [])
            if len(mentioned) > 1:
                # Create pairs of co-mentioned politicians
                for i, pol1 in enumerate(mentioned):
                    for pol2 in mentioned[i+1:]:
                        pair = tuple(sorted([pol1, pol2]))
                        if pair not in politician_cooccurrences:
                            politician_cooccurrences[pair] = []
                        politician_cooccurrences[pair].append(article.get('metadata', {}).get('article_id'))
        
        # Convert co-occurrences to collaboration relationships
        for (pol1, pol2), article_ids in politician_cooccurrences.items():
            if len(article_ids) >= 2:  # Require multiple co-mentions
                collaborations.append({
                    'type': 'COLLABORATES_WITH',
                    'source_id': self._find_politician_id_by_name(politicians, pol1),
                    'source_type': 'politician',
                    'target_id': self._find_politician_id_by_name(politicians, pol2),
                    'target_type': 'politician',
                    'strength': len(article_ids),
                    'evidence_articles': article_ids,
                    'extracted_at': datetime.now().isoformat()
                })
        
        return collaborations
    
    def _extract_topic_associations(self, documents: List[Dict]) -> List[Dict]:
        """Extract topic associations for entities"""
        associations = []
        
        # Define key political topics
        topics = {
            'climate': ['ilmasto', 'ympäristö', 'hiili', 'energia'],
            'economy': ['talous', 'budjetti', 'vero', 'työllisyys'],
            'healthcare': ['terveys', 'sairaala', 'lääkäri', 'hoito'],
            'education': ['koulutus', 'opetus', 'yliopisto', 'koulu'],
            'immigration': ['maahanmuutto', 'turvapaikka', 'pakolainen'],
            'defense': ['puolustus', 'nato', 'turvallisuus', 'sota']
        }
        
        for document in documents:
            content = document.get('page_content', '').lower()
            metadata = document.get('metadata', {})
            entity_id = metadata.get('politician_id') or metadata.get('article_id')
            entity_type = metadata.get('type')
            
            if entity_id and entity_type:
                for topic, keywords in topics.items():
                    relevance_score = sum(1 for keyword in keywords if keyword in content)
                    if relevance_score > 0:
                        associations.append({
                            'type': 'ASSOCIATED_WITH_TOPIC',
                            'source_id': entity_id,
                            'source_type': entity_type,
                            'target_id': topic,
                            'target_type': 'topic',
                            'relevance_score': relevance_score / len(keywords),
                            'keywords_found': [kw for kw in keywords if kw in content],
                            'extracted_at': datetime.now().isoformat()
                        })
        
        return associations
    
    def _extract_geographic_connections(self, politicians: List[Dict]) -> List[Dict]:
        """Extract geographic connections between politicians"""
        connections = []
        
        # Group politicians by constituency/region
        geographic_groups = {}
        
        for politician in politicians:
            metadata = politician.get('metadata', {})
            constituency = metadata.get('constituency')
            region = metadata.get('region')
            politician_id = metadata.get('politician_id')
            
            if politician_id:
                if constituency:
                    if constituency not in geographic_groups:
                        geographic_groups[constituency] = []
                    geographic_groups[constituency].append(politician_id)
                
                if region and region != constituency:
                    if region not in geographic_groups:
                        geographic_groups[region] = []
                    geographic_groups[region].append(politician_id)
        
        # Create connections between politicians in same geographic areas
        for location, politician_ids in geographic_groups.items():
            if len(politician_ids) > 1:
                for i, pol1 in enumerate(politician_ids):
                    for pol2 in politician_ids[i+1:]:
                        connections.append({
                            'type': 'SAME_CONSTITUENCY',
                            'source_id': pol1,
                            'source_type': 'politician',
                            'target_id': pol2,
                            'target_type': 'politician',
                            'location': location,
                            'extracted_at': datetime.now().isoformat()
                        })
        
        return connections
    
    def _build_politician_patterns(self) -> List[str]:
        """Build patterns for politician name recognition"""
        return [
            r'kansanedustaja\s+(\w+\s+\w+)',
            r'ministeri\s+(\w+\s+\w+)',
            r'pääministeri\s+(\w+\s+\w+)',
            r'puheenjohtaja\s+(\w+\s+\w+)'
        ]
    
    def _build_party_patterns(self) -> Dict[str, str]:
        """Build party name patterns and normalizations"""
        return {
            'sdp': 'Suomen Sosialidemokraattinen Puolue',
            'kokoomus': 'Kansallinen Kokoomus',
            'keskusta': 'Suomen Keskusta',
            'perussuomalaiset': 'Perussuomalaiset',
            'vihreät': 'Vihreä liitto',
            'vasemmistoliitto': 'Vasemmistoliitto',
            'rkp': 'Ruotsalainen kansanpuolue',
            'kristillisdemokraatit': 'Kristillisdemokraatit'
        }
    
    def _extract_mention_context(self, content: str, politician_name: str) -> str:
        """Extract context around politician mention"""
        # Find the mention and extract surrounding text
        pattern = re.compile(f'.{{0,100}}{re.escape(politician_name)}.{{0,100}}', re.IGNORECASE)
        match = pattern.search(content)
        return match.group(0) if match else ""
    
    def _calculate_mention_confidence(self, content: str, politician_name: str) -> float:
        """Calculate confidence score for politician mention"""
        # Simple confidence based on context
        context = self._extract_mention_context(content, politician_name)
        confidence = 0.5  # Base confidence
        
        # Increase confidence if mentioned with title
        if any(title in context.lower() for title in ['ministeri', 'kansanedustaja', 'pääministeri']):
            confidence += 0.3
        
        # Increase confidence if mentioned with party
        if any(party in context.lower() for party in self.party_patterns.keys()):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _normalize_party_id(self, party_name: str) -> str:
        """Normalize party name to consistent ID"""
        party_lower = party_name.lower()
        for abbrev, full_name in self.party_patterns.items():
            if abbrev in party_lower or full_name.lower() in party_lower:
                return abbrev
        return party_name.lower().replace(' ', '_')
    
    def _find_politician_by_name(self, politicians: List[Dict], name: str) -> Dict:
        """Find politician document by name"""
        name_lower = name.lower()
        for politician in politicians:
            politician_name = politician.get('metadata', {}).get('name', '').lower()
            if name_lower in politician_name or politician_name in name_lower:
                return politician
        return None
    
    def _find_politician_id_by_name(self, politicians: List[Dict], name: str) -> str:
        """Find politician ID by name"""
        politician = self._find_politician_by_name(politicians, name)
        if politician:
            return politician.get('metadata', {}).get('politician_id')
        return None
