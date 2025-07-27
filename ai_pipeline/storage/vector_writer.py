"""
Vector Writer
Handles writing embedded documents to vector database for semantic search.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

# Import vector store manager
from ..embeddings.vector_store_manager import VectorStoreManager

class VectorWriter:
    """
    Writes embedded documents to vector database for semantic search
    in the Finnish Politician Analysis System.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.logger = logging.getLogger(__name__)
        self.vector_store_manager = VectorStoreManager(persist_directory)
        self.initialized = False
        
    def initialize(self, embedding_function):
        """
        Initialize the vector writer with embedding function
        
        Args:
            embedding_function: Embedding function from EmbeddingManager
        """
        try:
            self.vector_store_manager.initialize_vector_store(embedding_function)
            self.initialized = True
            self.logger.info("Vector writer initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector writer: {str(e)}")
            raise
    
    def write_embedded_documents(self, embedded_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Write embedded documents to vector database
        
        Args:
            embedded_documents: List of documents with embeddings
            
        Returns:
            Dictionary with operation results
        """
        if not self.initialized:
            raise ValueError("Vector writer not initialized. Call initialize() first.")
        
        self.logger.info(f"Writing {len(embedded_documents)} embedded documents to vector store")
        
        # Separate documents by type for better organization
        politicians = [doc for doc in embedded_documents 
                      if doc.get('metadata', {}).get('type') == 'politician']
        news_articles = [doc for doc in embedded_documents 
                        if doc.get('metadata', {}).get('type') == 'news_article']
        other_docs = [doc for doc in embedded_documents 
                     if doc.get('metadata', {}).get('type') not in ['politician', 'news_article']]
        
        results = {
            'politicians': self._write_politician_embeddings(politicians),
            'news_articles': self._write_news_embeddings(news_articles),
            'other_documents': self._write_other_embeddings(other_docs),
            'total_processed': len(embedded_documents)
        }
        
        # Calculate overall success
        total_added = sum(result.get('documents_added', 0) for result in results.values() if isinstance(result, dict))
        total_errors = sum(len(result.get('errors', [])) for result in results.values() if isinstance(result, dict))
        
        results['summary'] = {
            'success': total_errors == 0,
            'total_documents_added': total_added,
            'total_errors': total_errors,
            'success_rate': total_added / len(embedded_documents) if embedded_documents else 0
        }
        
        self.logger.info(f"Vector writing completed: {total_added} documents added, {total_errors} errors")
        
        return results
    
    def _write_politician_embeddings(self, politician_docs: List[Dict]) -> Dict[str, Any]:
        """Write politician embeddings to vector store"""
        if not politician_docs:
            return {'documents_added': 0, 'documents_skipped': 0, 'errors': []}
        
        try:
            result = self.vector_store_manager.add_documents(politician_docs)
            self.logger.info(f"Added {result.get('documents_added', 0)} politician embeddings")
            return result
            
        except Exception as e:
            error_msg = f"Failed to write politician embeddings: {str(e)}"
            self.logger.error(error_msg)
            return {
                'documents_added': 0,
                'documents_skipped': len(politician_docs),
                'errors': [error_msg]
            }
    
    def _write_news_embeddings(self, news_docs: List[Dict]) -> Dict[str, Any]:
        """Write news article embeddings to vector store"""
        if not news_docs:
            return {'documents_added': 0, 'documents_skipped': 0, 'errors': []}
        
        try:
            result = self.vector_store_manager.add_documents(news_docs)
            self.logger.info(f"Added {result.get('documents_added', 0)} news article embeddings")
            return result
            
        except Exception as e:
            error_msg = f"Failed to write news embeddings: {str(e)}"
            self.logger.error(error_msg)
            return {
                'documents_added': 0,
                'documents_skipped': len(news_docs),
                'errors': [error_msg]
            }
    
    def _write_other_embeddings(self, other_docs: List[Dict]) -> Dict[str, Any]:
        """Write other document embeddings to vector store"""
        if not other_docs:
            return {'documents_added': 0, 'documents_skipped': 0, 'errors': []}
        
        try:
            result = self.vector_store_manager.add_documents(other_docs)
            self.logger.info(f"Added {result.get('documents_added', 0)} other document embeddings")
            return result
            
        except Exception as e:
            error_msg = f"Failed to write other embeddings: {str(e)}"
            self.logger.error(error_msg)
            return {
                'documents_added': 0,
                'documents_skipped': len(other_docs),
                'errors': [error_msg]
            }
    
    def search_similar_documents(self, query: str, k: int = 10, 
                                filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents in vector store
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of similar documents
        """
        if not self.initialized:
            raise ValueError("Vector writer not initialized")
        
        return self.vector_store_manager.similarity_search(query, k, filter_dict)
    
    def search_politicians(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for politicians based on query
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant politicians
        """
        return self.vector_store_manager.similarity_search(
            query=query,
            k=k,
            filter_dict={'type': 'politician'}
        )
    
    def search_news_articles(self, query: str, k: int = 10) -> List[Dict]:
        """
        Search for news articles based on query
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant news articles
        """
        return self.vector_store_manager.similarity_search(
            query=query,
            k=k,
            filter_dict={'type': 'news_article'}
        )
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        if not self.initialized:
            return {'error': 'Vector writer not initialized'}
        
        return self.vector_store_manager.get_collection_stats()
    
    def backup_vector_store(self, backup_path: str) -> Dict[str, Any]:
        """
        Create a backup of the vector store
        
        Args:
            backup_path: Path to save backup
            
        Returns:
            Dictionary with backup results
        """
        if not self.initialized:
            raise ValueError("Vector writer not initialized")
        
        return self.vector_store_manager.backup_collection(backup_path)
    
    def clear_vector_store(self) -> Dict[str, Any]:
        """Clear all documents from vector store"""
        if not self.initialized:
            raise ValueError("Vector writer not initialized")
        
        return self.vector_store_manager.clear_collection()
