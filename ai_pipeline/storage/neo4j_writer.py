"""
Neo4j Writer
Handles writing documents and relationships to Neo4j graph database.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
import os

# Add database path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'database'))
from database import get_neo4j_manager

class Neo4jWriter:
    """
    Writes processed documents and relationships to Neo4j graph database
    for the Finnish Politician Analysis System.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.neo4j = get_neo4j_manager()
        
    def write_politicians(self, politician_documents: List[Dict]) -> Dict[str, Any]:
        """
        Write politician documents to Neo4j
        
        Args:
            politician_documents: List of politician document dictionaries
            
        Returns:
            Dictionary with operation results
        """
        self.logger.info(f"Writing {len(politician_documents)} politicians to Neo4j")
        
        created_count = 0
        updated_count = 0
        errors = []
        
        with self.neo4j.session() as session:
            for doc in politician_documents:
                try:
                    metadata = doc.get('metadata', {})
                    
                    # Create politician node
                    result = session.run("""
                        MERGE (p:Politician {id: $politician_id})
                        SET p.name = $name,
                            p.party = $party,
                            p.position = $position,
                            p.constituency = $constituency,
                            p.region = $region,
                            p.email = $email,
                            p.website = $website,
                            p.bio = $bio,
                            p.source = $source,
                            p.data_completeness = $data_completeness,
                            p.updated_at = $updated_at,
                            p.content = $content
                        RETURN p.id as id, 
                               CASE WHEN p.created_at IS NULL THEN 'created' ELSE 'updated' END as action
                    """, {
                        'politician_id': metadata.get('politician_id'),
                        'name': metadata.get('name'),
                        'party': metadata.get('party'),
                        'position': metadata.get('position'),
                        'constituency': metadata.get('constituency'),
                        'region': metadata.get('region'),
                        'email': metadata.get('email'),
                        'website': metadata.get('website'),
                        'bio': doc.get('content', ''),
                        'source': metadata.get('source'),
                        'data_completeness': metadata.get('data_completeness', 0.0),
                        'updated_at': datetime.now().isoformat(),
                        'content': doc.get('content', '')
                    })
                    
                    record = result.single()
                    if record and record['action'] == 'created':
                        created_count += 1
                    else:
                        updated_count += 1
                        
                    # Create party node and relationship if party exists
                    if metadata.get('party'):
                        session.run("""
                            MERGE (party:Party {name: $party_name})
                            SET party.updated_at = $updated_at
                            WITH party
                            MATCH (p:Politician {id: $politician_id})
                            MERGE (p)-[:MEMBER_OF]->(party)
                        """, {
                            'party_name': metadata.get('party'),
                            'politician_id': metadata.get('politician_id'),
                            'updated_at': datetime.now().isoformat()
                        })
                    
                    # Create constituency node and relationship if constituency exists
                    if metadata.get('constituency'):
                        session.run("""
                            MERGE (c:Constituency {name: $constituency_name})
                            SET c.region = $region,
                                c.updated_at = $updated_at
                            WITH c
                            MATCH (p:Politician {id: $politician_id})
                            MERGE (p)-[:REPRESENTS]->(c)
                        """, {
                            'constituency_name': metadata.get('constituency'),
                            'region': metadata.get('region'),
                            'politician_id': metadata.get('politician_id'),
                            'updated_at': datetime.now().isoformat()
                        })
                        
                except Exception as e:
                    error_msg = f"Error writing politician {metadata.get('name', 'Unknown')}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
        
        self.logger.info(f"Politicians written: {created_count} created, {updated_count} updated, {len(errors)} errors")
        
        return {
            'success': len(errors) == 0,
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
            'total_processed': len(politician_documents)
        }
    
    def write_news_articles(self, news_documents: List[Dict]) -> Dict[str, Any]:
        """
        Write news article documents to Neo4j
        
        Args:
            news_documents: List of news article document dictionaries
            
        Returns:
            Dictionary with operation results
        """
        self.logger.info(f"Writing {len(news_documents)} news articles to Neo4j")
        
        created_count = 0
        updated_count = 0
        errors = []
        
        with self.neo4j.session() as session:
            for doc in news_documents:
                try:
                    metadata = doc.get('metadata', {})
                    
                    # Skip chunks, only process main articles
                    if metadata.get('type') == 'news_article_chunk':
                        continue
                    
                    # Create article node
                    result = session.run("""
                        MERGE (a:Article {id: $article_id})
                        SET a.title = $title,
                            a.author = $author,
                            a.published_date = $published_date,
                            a.url = $url,
                            a.source = $source,
                            a.category = $category,
                            a.tags = $tags,
                            a.word_count = $word_count,
                            a.political_relevance = $political_relevance,
                            a.sentiment = $sentiment,
                            a.content = $content,
                            a.updated_at = $updated_at
                        RETURN a.id as id,
                               CASE WHEN a.created_at IS NULL THEN 'created' ELSE 'updated' END as action
                    """, {
                        'article_id': metadata.get('article_id'),
                        'title': metadata.get('title'),
                        'author': metadata.get('author'),
                        'published_date': metadata.get('published_date'),
                        'url': metadata.get('url'),
                        'source': metadata.get('source'),
                        'category': metadata.get('category'),
                        'tags': metadata.get('tags', []),
                        'word_count': metadata.get('word_count', 0),
                        'political_relevance': metadata.get('political_relevance', 0.0),
                        'sentiment': metadata.get('sentiment', 'neutral'),
                        'content': doc.get('content', ''),
                        'updated_at': datetime.now().isoformat()
                    })
                    
                    record = result.single()
                    if record and record['action'] == 'created':
                        created_count += 1
                    else:
                        updated_count += 1
                    
                    # Create source node and relationship
                    if metadata.get('source'):
                        session.run("""
                            MERGE (s:NewsSource {name: $source_name})
                            SET s.updated_at = $updated_at
                            WITH s
                            MATCH (a:Article {id: $article_id})
                            MERGE (a)-[:PUBLISHED_BY]->(s)
                        """, {
                            'source_name': metadata.get('source'),
                            'article_id': metadata.get('article_id'),
                            'updated_at': datetime.now().isoformat()
                        })
                    
                    # Create topic nodes and relationships for tags
                    tags = metadata.get('tags', [])
                    if isinstance(tags, list):
                        for tag in tags[:5]:  # Limit to 5 tags
                            session.run("""
                                MERGE (t:Topic {name: $tag_name})
                                SET t.updated_at = $updated_at
                                WITH t
                                MATCH (a:Article {id: $article_id})
                                MERGE (a)-[:TAGGED_WITH]->(t)
                            """, {
                                'tag_name': str(tag),
                                'article_id': metadata.get('article_id'),
                                'updated_at': datetime.now().isoformat()
                            })
                        
                except Exception as e:
                    error_msg = f"Error writing article {metadata.get('title', 'Unknown')}: {str(e)}"
                    self.logger.error(error_msg)
                    errors.append(error_msg)
        
        self.logger.info(f"Articles written: {created_count} created, {updated_count} updated, {len(errors)} errors")
        
        return {
            'success': len(errors) == 0,
            'created': created_count,
            'updated': updated_count,
            'errors': errors,
            'total_processed': len([doc for doc in news_documents if doc.get('metadata', {}).get('type') != 'news_article_chunk'])
        }
    
    def write_relationships(self, relationships: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Write extracted relationships to Neo4j
        
        Args:
            relationships: Dictionary of relationship types and their data
            
        Returns:
            Dictionary with operation results
        """
        self.logger.info(f"Writing relationships to Neo4j: {sum(len(rels) for rels in relationships.values())} total")
        
        results = {}
        
        with self.neo4j.session() as session:
            # Write politician mentions in articles
            mentions = relationships.get('politician_mentions', [])
            results['politician_mentions'] = self._write_politician_mentions(session, mentions)
            
            # Write article-politician discussion links
            article_links = relationships.get('article_politician_links', [])
            results['article_politician_links'] = self._write_article_politician_links(session, article_links)
            
            # Write politician collaborations
            collaborations = relationships.get('politician_collaborations', [])
            results['politician_collaborations'] = self._write_politician_collaborations(session, collaborations)
            
            # Write topic associations
            topic_associations = relationships.get('topic_associations', [])
            results['topic_associations'] = self._write_topic_associations(session, topic_associations)
            
            # Write geographic connections
            geographic_connections = relationships.get('geographic_connections', [])
            results['geographic_connections'] = self._write_geographic_connections(session, geographic_connections)
        
        total_created = sum(result.get('created', 0) for result in results.values())
        total_errors = sum(len(result.get('errors', [])) for result in results.values())
        
        self.logger.info(f"Relationships written: {total_created} created, {total_errors} errors")
        
        return {
            'success': total_errors == 0,
            'total_created': total_created,
            'total_errors': total_errors,
            'details': results
        }
    
    def _write_politician_mentions(self, session, mentions: List[Dict]) -> Dict[str, Any]:
        """Write politician mention relationships"""
        created_count = 0
        errors = []
        
        for mention in mentions:
            try:
                session.run("""
                    MATCH (p:Politician {id: $politician_id})
                    MATCH (a:Article {id: $article_id})
                    MERGE (p)-[r:MENTIONED_IN]->(a)
                    SET r.context = $context,
                        r.confidence = $confidence,
                        r.created_at = $created_at
                """, {
                    'politician_id': mention.get('source_id'),
                    'article_id': mention.get('target_id'),
                    'context': mention.get('context', ''),
                    'confidence': mention.get('confidence', 0.5),
                    'created_at': mention.get('extracted_at')
                })
                created_count += 1
                
            except Exception as e:
                errors.append(f"Politician mention error: {str(e)}")
        
        return {'created': created_count, 'errors': errors}
    
    def _write_article_politician_links(self, session, links: List[Dict]) -> Dict[str, Any]:
        """Write article-politician discussion relationships"""
        created_count = 0
        errors = []
        
        for link in links:
            try:
                session.run("""
                    MATCH (a:Article {id: $article_id})
                    MATCH (p:Politician {id: $politician_id})
                    MERGE (a)-[r:DISCUSSES]->(p)
                    SET r.relevance_score = $relevance_score,
                        r.sentiment = $sentiment,
                        r.created_at = $created_at
                """, {
                    'article_id': link.get('source_id'),
                    'politician_id': link.get('target_id'),
                    'relevance_score': link.get('relevance_score', 0.0),
                    'sentiment': link.get('sentiment', 'neutral'),
                    'created_at': link.get('extracted_at')
                })
                created_count += 1
                
            except Exception as e:
                errors.append(f"Article-politician link error: {str(e)}")
        
        return {'created': created_count, 'errors': errors}
    
    def _write_politician_collaborations(self, session, collaborations: List[Dict]) -> Dict[str, Any]:
        """Write politician collaboration relationships"""
        created_count = 0
        errors = []
        
        for collab in collaborations:
            try:
                session.run("""
                    MATCH (p1:Politician {id: $politician1_id})
                    MATCH (p2:Politician {id: $politician2_id})
                    MERGE (p1)-[r:COLLABORATES_WITH]-(p2)
                    SET r.strength = $strength,
                        r.evidence_articles = $evidence_articles,
                        r.created_at = $created_at
                """, {
                    'politician1_id': collab.get('source_id'),
                    'politician2_id': collab.get('target_id'),
                    'strength': collab.get('strength', 1),
                    'evidence_articles': collab.get('evidence_articles', []),
                    'created_at': collab.get('extracted_at')
                })
                created_count += 1
                
            except Exception as e:
                errors.append(f"Politician collaboration error: {str(e)}")
        
        return {'created': created_count, 'errors': errors}
    
    def _write_topic_associations(self, session, associations: List[Dict]) -> Dict[str, Any]:
        """Write topic association relationships"""
        created_count = 0
        errors = []
        
        for assoc in associations:
            try:
                # Create topic node first
                session.run("""
                    MERGE (t:Topic {name: $topic_name})
                    SET t.updated_at = $updated_at
                """, {
                    'topic_name': assoc.get('target_id'),
                    'updated_at': datetime.now().isoformat()
                })
                
                # Create relationship based on source type
                if assoc.get('source_type') == 'politician':
                    session.run("""
                        MATCH (p:Politician {id: $entity_id})
                        MATCH (t:Topic {name: $topic_name})
                        MERGE (p)-[r:ASSOCIATED_WITH]->(t)
                        SET r.relevance_score = $relevance_score,
                            r.keywords_found = $keywords_found,
                            r.created_at = $created_at
                    """, {
                        'entity_id': assoc.get('source_id'),
                        'topic_name': assoc.get('target_id'),
                        'relevance_score': assoc.get('relevance_score', 0.0),
                        'keywords_found': assoc.get('keywords_found', []),
                        'created_at': assoc.get('extracted_at')
                    })
                elif assoc.get('source_type') == 'news_article':
                    session.run("""
                        MATCH (a:Article {id: $entity_id})
                        MATCH (t:Topic {name: $topic_name})
                        MERGE (a)-[r:COVERS_TOPIC]->(t)
                        SET r.relevance_score = $relevance_score,
                            r.keywords_found = $keywords_found,
                            r.created_at = $created_at
                    """, {
                        'entity_id': assoc.get('source_id'),
                        'topic_name': assoc.get('target_id'),
                        'relevance_score': assoc.get('relevance_score', 0.0),
                        'keywords_found': assoc.get('keywords_found', []),
                        'created_at': assoc.get('extracted_at')
                    })
                
                created_count += 1
                
            except Exception as e:
                errors.append(f"Topic association error: {str(e)}")
        
        return {'created': created_count, 'errors': errors}
    
    def _write_geographic_connections(self, session, connections: List[Dict]) -> Dict[str, Any]:
        """Write geographic connection relationships"""
        created_count = 0
        errors = []
        
        for conn in connections:
            try:
                session.run("""
                    MATCH (p1:Politician {id: $politician1_id})
                    MATCH (p2:Politician {id: $politician2_id})
                    MERGE (p1)-[r:SAME_CONSTITUENCY]-(p2)
                    SET r.location = $location,
                        r.created_at = $created_at
                """, {
                    'politician1_id': conn.get('source_id'),
                    'politician2_id': conn.get('target_id'),
                    'location': conn.get('location'),
                    'created_at': conn.get('extracted_at')
                })
                created_count += 1
                
            except Exception as e:
                errors.append(f"Geographic connection error: {str(e)}")
        
        return {'created': created_count, 'errors': errors}
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the Neo4j database"""
        try:
            with self.neo4j.session() as session:
                # Count nodes by type
                node_counts = {}
                node_types = ['Politician', 'Article', 'Party', 'Constituency', 'Topic', 'NewsSource']
                
                for node_type in node_types:
                    result = session.run(f"MATCH (n:{node_type}) RETURN count(n) as count")
                    node_counts[node_type] = result.single()['count']
                
                # Count relationships by type
                relationship_result = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                """)
                
                relationship_counts = {}
                for record in relationship_result:
                    relationship_counts[record['rel_type']] = record['count']
                
                return {
                    'node_counts': node_counts,
                    'relationship_counts': relationship_counts,
                    'total_nodes': sum(node_counts.values()),
                    'total_relationships': sum(relationship_counts.values()),
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database stats: {str(e)}")
            return {'error': str(e)}
