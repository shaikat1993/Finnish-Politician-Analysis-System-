"""
Embeddings module for AI Pipeline
Handles embedding generation and vector store management.
"""

from .embedding_manager import EmbeddingManager
from .vector_store_manager import VectorStoreManager

__all__ = [
    'EmbeddingManager',
    'VectorStoreManager'
]
