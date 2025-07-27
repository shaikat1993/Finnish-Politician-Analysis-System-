"""
Embedding Manager
Handles embedding generation for documents using various embedding models.
"""

import logging
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
import asyncio

# LangChain imports
from langchain_community.embeddings import OpenAIEmbeddings
# HuggingFace embeddings temporarily disabled due to Python 3.13 compatibility
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

class EmbeddingManager:
    """
    Manages embedding generation for documents with support for multiple
    embedding providers (OpenAI, HuggingFace, etc.)
    """
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.logger = logging.getLogger(__name__)
        self.embeddings_model = self._initialize_embeddings_model()
        
    def _initialize_embeddings_model(self):
        """Initialize the embeddings model based on provider"""
        try:
            if self.provider == "openai":
                # Requires OPENAI_API_KEY environment variable
                return OpenAIEmbeddings(
                    model="text-embedding-ada-002",
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
            elif self.provider == "huggingface":
                # HuggingFace embeddings temporarily disabled due to Python 3.13 compatibility
                self.logger.warning("HuggingFace embeddings not available with Python 3.13. Falling back to OpenAI.")
                if os.getenv("OPENAI_API_KEY"):
                    self.provider = "openai"
                    return OpenAIEmbeddings(
                        model="text-embedding-ada-002",
                        openai_api_key=os.getenv("OPENAI_API_KEY")
                    )
                else:
                    raise ValueError("HuggingFace embeddings unavailable and no OpenAI API key found")
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings model: {str(e)}")
            # No fallback available - HuggingFace embeddings disabled for Python 3.13
            self.logger.error("No fallback embedding provider available")
            raise
    
    async def generate_embeddings(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of documents
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            List of dictionaries containing document metadata and embeddings
        """
        self.logger.info(f"Generating embeddings for {len(documents)} documents using {self.provider}")
        
        embedded_documents = []
        
        # Process documents in batches to avoid memory issues
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_embeddings = await self._process_batch(batch)
            embedded_documents.extend(batch_embeddings)
            
            self.logger.info(f"Processed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
        
        self.logger.info(f"Successfully generated embeddings for {len(embedded_documents)} documents")
        return embedded_documents
    
    async def _process_batch(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Process a batch of documents for embedding generation"""
        embedded_docs = []
        
        try:
            # Extract text content from documents
            texts = [doc.page_content for doc in documents]
            
            # Generate embeddings
            if self.provider == "openai":
                # OpenAI embeddings are async-friendly
                embeddings = await self._generate_openai_embeddings(texts)
            else:
                # HuggingFace embeddings (synchronous)
                embeddings = self.embeddings_model.embed_documents(texts)
            
            # Combine documents with their embeddings
            for doc, embedding in zip(documents, embeddings):
                embedded_doc = {
                    'document_id': self._generate_document_id(doc),
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'embedding': embedding,
                    'embedding_model': self.provider,
                    'embedding_dimension': len(embedding),
                    'generated_at': datetime.now().isoformat()
                }
                embedded_docs.append(embedded_doc)
                
        except Exception as e:
            self.logger.error(f"Error processing batch: {str(e)}")
            # Return documents without embeddings as fallback
            for doc in documents:
                embedded_docs.append({
                    'document_id': self._generate_document_id(doc),
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'embedding': None,
                    'embedding_model': None,
                    'error': str(e),
                    'generated_at': datetime.now().isoformat()
                })
        
        return embedded_docs
    
    async def _generate_openai_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate OpenAI embeddings with proper async handling"""
        try:
            # OpenAI embeddings with rate limiting
            embeddings = []
            for text in texts:
                embedding = await asyncio.to_thread(
                    self.embeddings_model.embed_query, text
                )
                embeddings.append(embedding)
                # Small delay to respect rate limits
                await asyncio.sleep(0.1)
            return embeddings
        except Exception as e:
            self.logger.error(f"OpenAI embedding generation failed: {str(e)}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a single query string
        
        Args:
            query: Query string to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            return self.embeddings_model.embed_query(query)
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {str(e)}")
            return []
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            import numpy as np
            
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate similarity: {str(e)}")
            return 0.0
    
    def find_similar_documents(self, query_embedding: List[float], 
                             document_embeddings: List[Dict], 
                             top_k: int = 10) -> List[Dict]:
        """
        Find most similar documents to a query embedding
        
        Args:
            query_embedding: Query embedding vector
            document_embeddings: List of document embedding dictionaries
            top_k: Number of top results to return
            
        Returns:
            List of most similar documents with similarity scores
        """
        similarities = []
        
        for doc_data in document_embeddings:
            if doc_data.get('embedding'):
                similarity = self.calculate_similarity(
                    query_embedding, 
                    doc_data['embedding']
                )
                similarities.append({
                    'document': doc_data,
                    'similarity': similarity
                })
        
        # Sort by similarity (descending) and return top k
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_k]
    
    def _generate_document_id(self, document: Document) -> str:
        """Generate a unique ID for a document"""
        metadata = document.metadata
        
        # Try to use existing IDs from metadata
        if metadata.get('politician_id'):
            return f"politician_{metadata['politician_id']}"
        elif metadata.get('article_id'):
            return f"article_{metadata['article_id']}"
        else:
            # Generate ID from content hash
            import hashlib
            content_hash = hashlib.md5(document.page_content.encode()).hexdigest()[:12]
            doc_type = metadata.get('type', 'unknown')
            return f"{doc_type}_{content_hash}"
    
    def get_embedding_stats(self, embedded_documents: List[Dict]) -> Dict[str, Any]:
        """Get statistics about generated embeddings"""
        if not embedded_documents:
            return {}
        
        successful_embeddings = [doc for doc in embedded_documents if doc.get('embedding')]
        failed_embeddings = [doc for doc in embedded_documents if not doc.get('embedding')]
        
        stats = {
            'total_documents': len(embedded_documents),
            'successful_embeddings': len(successful_embeddings),
            'failed_embeddings': len(failed_embeddings),
            'success_rate': len(successful_embeddings) / len(embedded_documents) if embedded_documents else 0,
            'embedding_provider': self.provider,
            'embedding_dimension': successful_embeddings[0].get('embedding_dimension') if successful_embeddings else None,
            'document_types': {}
        }
        
        # Count document types
        for doc in embedded_documents:
            doc_type = doc.get('metadata', {}).get('type', 'unknown')
            stats['document_types'][doc_type] = stats['document_types'].get(doc_type, 0) + 1
        
        return stats
