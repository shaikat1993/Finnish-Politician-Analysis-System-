"""
Vector Store Manager
Manages vector database operations for semantic search and retrieval.
"""

import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import json

# LangChain imports
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

class VectorStoreManager:
    """
    Manages vector database operations using Chroma for semantic search
    and document retrieval in the Finnish Politician Analysis System.
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        self.logger = logging.getLogger(__name__)
        self.vector_store = None
        self.collection_name = "fpas_documents"
        
    def initialize_vector_store(self, embedding_function):
        """
        Initialize the Chroma vector store
        
        Args:
            embedding_function: Embedding function from EmbeddingManager
        """
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # Initialize Chroma vector store
            self.vector_store = Chroma(
                collection_name=self.collection_name,
                embedding_function=embedding_function,
                persist_directory=self.persist_directory
            )
            
            self.logger.info(f"Vector store initialized at {self.persist_directory}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize vector store: {str(e)}")
            raise
    
    def add_documents(self, embedded_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Add embedded documents to the vector store
        
        Args:
            embedded_documents: List of documents with embeddings
            
        Returns:
            Dictionary with operation results
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized. Call initialize_vector_store first.")
        
        self.logger.info(f"Adding {len(embedded_documents)} documents to vector store")
        
        # Convert embedded documents to LangChain Documents
        documents = []
        metadatas = []
        ids = []
        
        for embedded_doc in embedded_documents:
            if embedded_doc.get('embedding'):  # Only add documents with valid embeddings
                # Create LangChain Document
                doc = Document(
                    page_content=embedded_doc['content'],
                    metadata=embedded_doc['metadata']
                )
                documents.append(doc)
                
                # Prepare metadata (Chroma doesn't store embeddings in metadata)
                metadata = embedded_doc['metadata'].copy()
                metadata.update({
                    'embedding_model': embedded_doc.get('embedding_model'),
                    'embedding_dimension': embedded_doc.get('embedding_dimension'),
                    'generated_at': embedded_doc.get('generated_at'),
                    'added_to_vector_store': datetime.now().isoformat()
                })
                metadatas.append(metadata)
                
                # Use document ID
                ids.append(embedded_doc['document_id'])
        
        try:
            # Add documents to vector store
            if documents:
                self.vector_store.add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # Persist the vector store
                self.vector_store.persist()
                
                self.logger.info(f"Successfully added {len(documents)} documents to vector store")
                
                return {
                    'success': True,
                    'documents_added': len(documents),
                    'documents_skipped': len(embedded_documents) - len(documents),
                    'collection_name': self.collection_name
                }
            else:
                self.logger.warning("No valid documents with embeddings to add")
                return {
                    'success': False,
                    'documents_added': 0,
                    'documents_skipped': len(embedded_documents),
                    'error': 'No valid embeddings found'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {str(e)}")
            return {
                'success': False,
                'documents_added': 0,
                'error': str(e)
            }
    
    def similarity_search(self, query: str, k: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        Perform similarity search in the vector store
        
        Args:
            query: Search query string
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of similar documents with metadata
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        try:
            # Perform similarity search
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            # Format results
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'similarity_score': float(score),
                    'document_type': doc.metadata.get('type', 'unknown')
                })
            
            self.logger.info(f"Similarity search returned {len(formatted_results)} results for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Similarity search failed: {str(e)}")
            return []
    
    def search_by_politician(self, politician_name: str, k: int = 5) -> List[Dict]:
        """
        Search for documents related to a specific politician
        
        Args:
            politician_name: Name of the politician
            k: Number of results to return
            
        Returns:
            List of related documents
        """
        # Search with politician name as query
        query_results = self.similarity_search(
            query=f"politician {politician_name}",
            k=k
        )
        
        # Also search with metadata filter
        filter_results = self.similarity_search(
            query=politician_name,
            k=k,
            filter_dict={'name': politician_name}
        )
        
        # Combine and deduplicate results
        all_results = query_results + filter_results
        seen_ids = set()
        unique_results = []
        
        for result in all_results:
            doc_id = result['metadata'].get('politician_id') or result['metadata'].get('article_id')
            if doc_id and doc_id not in seen_ids:
                seen_ids.add(doc_id)
                unique_results.append(result)
        
        return unique_results[:k]
    
    def search_by_topic(self, topic: str, k: int = 10) -> List[Dict]:
        """
        Search for documents related to a specific topic
        
        Args:
            topic: Topic to search for
            k: Number of results to return
            
        Returns:
            List of topic-related documents
        """
        return self.similarity_search(
            query=f"topic {topic} politics Finnish",
            k=k
        )
    
    def search_by_party(self, party_name: str, k: int = 10) -> List[Dict]:
        """
        Search for documents related to a specific political party
        
        Args:
            party_name: Name of the political party
            k: Number of results to return
            
        Returns:
            List of party-related documents
        """
        return self.similarity_search(
            query=f"party {party_name} politics",
            k=k,
            filter_dict={'party': party_name}
        )
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection
        
        Returns:
            Dictionary with collection statistics
        """
        if not self.vector_store:
            return {'error': 'Vector store not initialized'}
        
        try:
            # Get collection info
            collection = self.vector_store._collection
            
            stats = {
                'collection_name': self.collection_name,
                'total_documents': collection.count(),
                'persist_directory': self.persist_directory,
                'last_updated': datetime.now().isoformat()
            }
            
            # Try to get document type breakdown
            try:
                # Sample some documents to analyze types
                sample_results = self.vector_store.similarity_search("", k=100)
                type_counts = {}
                
                for doc in sample_results:
                    doc_type = doc.metadata.get('type', 'unknown')
                    type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
                
                stats['document_types'] = type_counts
                
            except Exception:
                stats['document_types'] = 'Unable to analyze'
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {str(e)}")
            return {'error': str(e)}
    
    def delete_documents(self, document_ids: List[str]) -> Dict[str, Any]:
        """
        Delete documents from the vector store
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Dictionary with deletion results
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        try:
            # Delete documents
            self.vector_store.delete(ids=document_ids)
            self.vector_store.persist()
            
            self.logger.info(f"Deleted {len(document_ids)} documents from vector store")
            
            return {
                'success': True,
                'documents_deleted': len(document_ids)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete documents: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def clear_collection(self) -> Dict[str, Any]:
        """
        Clear all documents from the collection
        
        Returns:
            Dictionary with operation results
        """
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        try:
            # Get all document IDs and delete them
            collection = self.vector_store._collection
            all_ids = collection.get()['ids']
            
            if all_ids:
                self.vector_store.delete(ids=all_ids)
                self.vector_store.persist()
                
                self.logger.info(f"Cleared {len(all_ids)} documents from collection")
                
                return {
                    'success': True,
                    'documents_deleted': len(all_ids)
                }
            else:
                return {
                    'success': True,
                    'documents_deleted': 0,
                    'message': 'Collection was already empty'
                }
                
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def backup_collection(self, backup_path: str) -> Dict[str, Any]:
        """
        Create a backup of the vector store collection
        
        Args:
            backup_path: Path to save the backup
            
        Returns:
            Dictionary with backup results
        """
        try:
            import shutil
            
            # Create backup directory
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Copy the entire persist directory
            shutil.copytree(self.persist_directory, backup_path, dirs_exist_ok=True)
            
            self.logger.info(f"Vector store backed up to {backup_path}")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'backup_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to backup collection: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
