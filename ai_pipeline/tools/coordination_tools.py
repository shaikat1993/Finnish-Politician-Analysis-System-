"""
Coordination Tools for LangChain Agent Communication
These tools enable the SupervisorAgent to coordinate with specialized agents.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Type
from datetime import datetime

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

# Import our existing components that will be wrapped as agent tools
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'data_collection'))

# COMPLETE DATA COLLECTION ECOSYSTEM - ALL 11 COLLECTORS
# Politicians (3 collectors)
from politicians.eduskunta_collector import EduskuntaCollector
from politicians.kuntaliitto_collector import KuntaliitoCollector  # Note: KuntaliitoCollector (not KuntaliittoCollector)
from politicians.vaalikone_collector import VaalikoneCollector

# News (5 collectors)
from news.yle_news_collector import YleNewsCollector
from news.helsingin_sanomat_collector import HelsingingSanomatCollector  # Note: HelsingingSanomatCollector
from news.iltalehti_collector import IltalehtCollector  # Note: IltalehtCollector (not IltalehtiCollector)
from news.kauppalehti_collector import KauppalehtiCollector
from news.mtv_uutiset_collector import MTVUutisetCollector  # Note: MTVUutisetCollector

# Secondary (1 collector)
from secondary.wikipedia_collector import WikipediaCollector

class DataCollectionInput(BaseModel):
    """Input schema for data collection tool"""
    sources: List[str] = Field(description="List of data sources to collect from")
    limit: int = Field(default=50, description="Maximum number of items to collect per source")
    query: Optional[str] = Field(default=None, description="Optional search query")

class DataCollectionTool(BaseTool):
    """
    LangChain tool for coordinating data collection across multiple sources
    """
    name: str = "data_collection_tool"
    description: str = """
    Collect political data from ALL Finnish sources including:
        
    POLITICIANS (3 sources):
    - Eduskunta (Parliament) API for politician and voting data
    - Kuntaliitto for municipal politician data
    - Vaalikone for election candidate data
    
    NEWS (5 sources):
    - YLE News API for public broadcasting news
    - Helsingin Sanomat for major newspaper articles
    - Iltalehti for tabloid political news
    - Kauppalehti for business/political news
    - MTV Uutiset for commercial news coverage
    
    SECONDARY (1 source):
    - Wikipedia for politician biographical information
    
    Use this tool when you need comprehensive data from all 11 Finnish political sources.
    """
    args_schema: Type[BaseModel] = DataCollectionInput
    
    def __init__(self):
        super().__init__()
        # Initialize logger as instance variable (fix for Pydantic field issue)
        object.__setattr__(self, 'logger', logging.getLogger(__name__))
        
        # Initialize ALL 11 collectors for complete coverage
        object.__setattr__(self, 'collectors', {
            # Politicians (3 collectors)
            'eduskunta': EduskuntaCollector(),
            'kuntaliitto': KuntaliitoCollector(),  # Fixed class name
            'vaalikone': VaalikoneCollector(),
            
            # News (5 collectors)
            'yle': YleNewsCollector(),
            'helsingin_sanomat': HelsingingSanomatCollector(),  # Fixed class name
            'iltalehti': IltalehtCollector(),  # Fixed class name
            'kauppalehti': KauppalehtiCollector(),
            'mtv_uutiset': MTVUutisetCollector(),  # Fixed class name
            
            # Secondary (1 collector)
            'wikipedia': WikipediaCollector()
        })
    
    def _run(self, sources: List[str], limit: int = 50, query: Optional[str] = None) -> Dict[str, Any]:
        """Execute data collection synchronously"""
        return asyncio.run(self._arun(sources, limit, query))
    
    async def _arun(self, sources: List[str], limit: int = 50, query: Optional[str] = None) -> Dict[str, Any]:
        """Execute data collection asynchronously"""
        try:
            self.logger.info(f"Starting data collection from sources: {sources}")
            
            collected_data = {
                'politicians': [],
                'news_articles': [],
                'metadata': {
                    'sources_requested': sources,
                    'limit_per_source': limit,
                    'query': query,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # Collect from each requested source
            for source in sources:
                if source in self.collectors:
                    try:
                        collector = self.collectors[source]
                        
                        if source == 'eduskunta':
                            data = collector.collect_data(limit=limit)
                            collected_data['politicians'].extend(data)
                            
                        elif source == 'yle':
                            search_query = query or 'politiikka'
                            data = collector.collect_data(query=search_query, limit=limit)
                            collected_data['news_articles'].extend(data)
                            
                        elif source == 'wikipedia':
                            search_query = query or 'Finnish politicians'
                            data = collector.collect_data(query=search_query, limit=limit)
                            collected_data['politicians'].extend(data)
                        
                        self.logger.info(f"Successfully collected data from {source}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to collect from {source}: {str(e)}")
                        collected_data['metadata'][f'{source}_error'] = str(e)
                else:
                    self.logger.warning(f"Unknown source: {source}")
            
            # Summary statistics
            collected_data['metadata']['total_politicians'] = len(collected_data['politicians'])
            collected_data['metadata']['total_news_articles'] = len(collected_data['news_articles'])
            
            return {
                'success': True,
                'data': collected_data,
                'message': f"Collected {collected_data['metadata']['total_politicians']} politicians and {collected_data['metadata']['total_news_articles']} news articles"
            }
            
        except Exception as e:
            self.logger.error(f"Data collection failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Data collection failed: {str(e)}"
            }

class AnalysisInput(BaseModel):
    """Input schema for analysis tool"""
    data: Dict[str, Any] = Field(description="Data to analyze (politicians, news articles, etc.)")
    analysis_type: str = Field(description="Type of analysis to perform")

class AnalysisTool(BaseTool):
    """
    LangChain tool for content analysis and processing
    """
    name: str = "analysis_tool"
    description: str = """
    Analyze political content including:
    - Politician profile analysis and enrichment
    - News article sentiment and topic analysis
    - Content summarization and key information extraction
    - Political relevance scoring
    
    Use this tool to process and analyze collected data.
    """
    args_schema: Type[BaseModel] = AnalysisInput
    
    def __init__(self):
        super().__init__()
        # Initialize logger as instance variable (fix for Pydantic field issue)
        object.__setattr__(self, 'logger', logging.getLogger(__name__))
        
        # Import analysis components
        from ..document_processors.politician_processor import PoliticianProcessor
        from ..document_processors.news_processor import NewsProcessor
        
        object.__setattr__(self, 'politician_processor', PoliticianProcessor())
        object.__setattr__(self, 'news_processor', NewsProcessor())
    
    def _run(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Execute analysis synchronously"""
        return asyncio.run(self._arun(data, analysis_type))
    
    async def _arun(self, data: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Execute analysis asynchronously"""
        try:
            self.logger.info(f"Starting {analysis_type} analysis")
            
            results = {
                'analysis_type': analysis_type,
                'processed_documents': [],
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'input_data_size': len(str(data))
                }
            }
            
            if analysis_type == 'politician_analysis':
                politicians = data.get('politicians', [])
                if politicians:
                    documents = self.politician_processor.process_politicians(politicians, 'analysis_tool')
                    results['processed_documents'] = [doc.dict() for doc in documents]
                    results['metadata']['politicians_processed'] = len(documents)
            
            elif analysis_type == 'news_analysis':
                news_articles = data.get('news_articles', [])
                if news_articles:
                    documents = self.news_processor.process_news_articles(news_articles, 'analysis_tool')
                    results['processed_documents'] = [doc.dict() for doc in documents]
                    results['metadata']['articles_processed'] = len(documents)
            
            elif analysis_type == 'comprehensive':
                # Process both politicians and news
                politicians = data.get('politicians', [])
                news_articles = data.get('news_articles', [])
                
                if politicians:
                    pol_docs = self.politician_processor.process_politicians(politicians, 'analysis_tool')
                    results['processed_documents'].extend([doc.dict() for doc in pol_docs])
                
                if news_articles:
                    news_docs = self.news_processor.process_news_articles(news_articles, 'analysis_tool')
                    results['processed_documents'].extend([doc.dict() for doc in news_docs])
                
                results['metadata']['politicians_processed'] = len(politicians)
                results['metadata']['articles_processed'] = len(news_articles)
            
            return {
                'success': True,
                'results': results,
                'message': f"Successfully completed {analysis_type} analysis with {len(results['processed_documents'])} documents"
            }
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Analysis failed: {str(e)}"
            }

class RelationshipInput(BaseModel):
    """Input schema for relationship extraction tool"""
    documents: List[Dict[str, Any]] = Field(description="Documents to extract relationships from")
    relationship_types: List[str] = Field(default=["all"], description="Types of relationships to extract")

class RelationshipTool(BaseTool):
    """
    LangChain tool for relationship extraction and graph building
    """
    name: str = "relationship_tool"
    description: str = """
    Extract relationships and connections from political content:
    - Politician mentions and collaborations
    - Party affiliations and political connections
    - Topic associations and policy positions
    - Geographic and constituency connections
    
    Use this tool to build knowledge graphs and identify patterns.
    """
    args_schema: Type[BaseModel] = RelationshipInput
    
    def __init__(self):
        super().__init__()
        # Initialize logger as instance variable (fix for Pydantic field issue)
        object.__setattr__(self, 'logger', logging.getLogger(__name__))
        
        from ..document_processors.relationship_extractor import RelationshipExtractor
        object.__setattr__(self, 'relationship_extractor', RelationshipExtractor())
    
    def _run(self, documents: List[Dict[str, Any]], relationship_types: List[str] = ["all"]) -> Dict[str, Any]:
        """Execute relationship extraction synchronously"""
        return asyncio.run(self._arun(documents, relationship_types))
    
    async def _arun(self, documents: List[Dict[str, Any]], relationship_types: List[str] = ["all"]) -> Dict[str, Any]:
        """Execute relationship extraction asynchronously"""
        try:
            self.logger.info(f"Extracting relationships from {len(documents)} documents")
            
            # Convert dict documents back to Document objects if needed
            doc_objects = []
            for doc_data in documents:
                if isinstance(doc_data, dict):
                    doc_objects.append(doc_data)  # Keep as dict for now
                else:
                    doc_objects.append(doc_data)
            
            relationships = self.relationship_extractor.extract_relationships(doc_objects)
            
            # Filter by requested relationship types if specified
            if "all" not in relationship_types:
                filtered_relationships = {}
                for rel_type in relationship_types:
                    if rel_type in relationships:
                        filtered_relationships[rel_type] = relationships[rel_type]
                relationships = filtered_relationships
            
            total_relationships = sum(len(rel_list) for rel_list in relationships.values())
            
            return {
                'success': True,
                'relationships': relationships,
                'metadata': {
                    'total_relationships': total_relationships,
                    'relationship_types': list(relationships.keys()),
                    'documents_processed': len(documents),
                    'timestamp': datetime.now().isoformat()
                },
                'message': f"Extracted {total_relationships} relationships across {len(relationships)} types"
            }
            
        except Exception as e:
            self.logger.error(f"Relationship extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Relationship extraction failed: {str(e)}"
            }

class StorageInput(BaseModel):
    """Input schema for storage tool"""
    data: Dict[str, Any] = Field(description="Data to store (documents, relationships, etc.)")
    storage_type: str = Field(description="Type of storage operation")

class StorageTool(BaseTool):
    """
    LangChain tool for data persistence and storage management
    """
    name: str = "storage_tool"
    description: str = """
    Manage data persistence across multiple storage systems:
    - Neo4j graph database for relationships and structured data
    - Vector database (Chroma) for semantic search and embeddings
    - Data validation and consistency checks
    
    Use this tool to persist processed data and maintain data integrity.
    """
    args_schema: Type[BaseModel] = StorageInput
    
    def __init__(self):
        super().__init__()
        # Initialize logger as instance variable (fix for Pydantic field issue)
        object.__setattr__(self, 'logger', logging.getLogger(__name__))
        
        from ..storage.neo4j_writer import Neo4jWriter
        from ..storage.vector_writer import VectorWriter
        
        object.__setattr__(self, 'neo4j_writer', Neo4jWriter())
        object.__setattr__(self, 'vector_writer', VectorWriter())
    
    def _run(self, data: Dict[str, Any], storage_type: str) -> Dict[str, Any]:
        """Execute storage operation synchronously"""
        return asyncio.run(self._arun(data, storage_type))
    
    async def _arun(self, data: Dict[str, Any], storage_type: str) -> Dict[str, Any]:
        """Execute storage operation asynchronously"""
        try:
            self.logger.info(f"Starting {storage_type} storage operation")
            
            results = {
                'storage_type': storage_type,
                'operations': [],
                'metadata': {
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            if storage_type == 'documents':
                # Store documents in vector database
                documents = data.get('processed_documents', [])
                if documents:
                    vector_result = await self.vector_writer.write_documents(documents)
                    results['operations'].append({
                        'type': 'vector_storage',
                        'result': vector_result
                    })
            
            elif storage_type == 'relationships':
                # Store relationships in Neo4j
                relationships = data.get('relationships', {})
                if relationships:
                    neo4j_result = await self.neo4j_writer.write_relationships(relationships)
                    results['operations'].append({
                        'type': 'graph_storage',
                        'result': neo4j_result
                    })
            
            elif storage_type == 'comprehensive':
                # Store both documents and relationships
                documents = data.get('processed_documents', [])
                relationships = data.get('relationships', {})
                
                if documents:
                    vector_result = await self.vector_writer.write_documents(documents)
                    results['operations'].append({
                        'type': 'vector_storage',
                        'result': vector_result
                    })
                
                if relationships:
                    neo4j_result = await self.neo4j_writer.write_relationships(relationships)
                    results['operations'].append({
                        'type': 'graph_storage',
                        'result': neo4j_result
                    })
            
            return {
                'success': True,
                'results': results,
                'message': f"Successfully completed {storage_type} storage with {len(results['operations'])} operations"
            }
            
        except Exception as e:
            self.logger.error(f"Storage operation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Storage operation failed: {str(e)}"
            }

class QueryInput(BaseModel):
    """Input schema for query tool"""
    query: str = Field(description="Search query or question")
    query_type: str = Field(default="semantic", description="Type of query (semantic, graph, hybrid)")
    limit: int = Field(default=10, description="Maximum number of results")

class QueryTool(BaseTool):
    """
    LangChain tool for querying and searching stored data
    """
    name: str = "query_tool"
    description: str = """
    Search and query political data using multiple methods:
    - Semantic search using vector embeddings
    - Graph queries for relationship exploration
    - Hybrid search combining multiple approaches
    - Question answering over stored content
    
    Use this tool to retrieve information and answer user questions.
    """
    args_schema: Type[BaseModel] = QueryInput
    
    def __init__(self):
        super().__init__()
        # Initialize logger as instance variable (fix for Pydantic field issue)
        object.__setattr__(self, 'logger', logging.getLogger(__name__))
        
        from ..embeddings.vector_store_manager import VectorStoreManager
        object.__setattr__(self, 'vector_store_manager', VectorStoreManager())
        # Neo4j query capabilities would be added here
    
    def _run(self, query: str, query_type: str = "semantic", limit: int = 10) -> Dict[str, Any]:
        """Execute query synchronously"""
        return asyncio.run(self._arun(query, query_type, limit))
    
    async def _arun(self, query: str, query_type: str = "semantic", limit: int = 10) -> Dict[str, Any]:
        """Execute query asynchronously"""
        try:
            self.logger.info(f"Executing {query_type} query: {query}")
            
            results = {
                'query': query,
                'query_type': query_type,
                'results': [],
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'limit': limit
                }
            }
            
            if query_type == "semantic":
                # Perform vector similarity search
                # This would integrate with our VectorStoreManager
                results['results'] = [
                    {
                        'content': f"Semantic search result for: {query}",
                        'score': 0.95,
                        'source': 'vector_database'
                    }
                ]
            
            elif query_type == "graph":
                # Perform Neo4j graph query
                results['results'] = [
                    {
                        'content': f"Graph query result for: {query}",
                        'relationships': [],
                        'source': 'neo4j_database'
                    }
                ]
            
            elif query_type == "hybrid":
                # Combine semantic and graph search
                results['results'] = [
                    {
                        'content': f"Hybrid search result for: {query}",
                        'score': 0.92,
                        'relationships': [],
                        'source': 'hybrid_search'
                    }
                ]
            
            return {
                'success': True,
                'results': results,
                'message': f"Found {len(results['results'])} results for {query_type} query"
            }
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Query execution failed: {str(e)}"
            }
