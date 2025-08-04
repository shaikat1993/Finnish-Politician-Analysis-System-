"""
Configuration management for FPAS API
Handles environment variables and application settings
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finnish Politician Analysis System"

    # Neo4j settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")

    # OpenAI and AI pipeline
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_PROVIDER: str = ""
    EMBEDDING_MODEL: str = ""
    MAX_CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # YLE and LangSmith
    YLE_APP_ID: str = ""
    YLE_APP_KEY: str = ""
    YLE_API_KEY: str = ""
    LANGSMITH_TRACING: str = ""
    LANGSMITH_ENDPOINT: str = ""
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = ""

    # Chroma/Vector DB
    CHROMA_PERSIST_DIRECTORY: str = ""

    # API Security
    CORS_ORIGINS: list[str] = ["*"]  # For production, specify specific origins

    # Caching and pagination
    CACHE_EXPIRY_SECONDS: int = 300  # 5 minutes
    DEFAULT_LIMIT: int = 100
    MAX_LIMIT: int = 500

    model_config = {
        "extra": "allow",
        "env_file": ".env",
        "case_sensitive": True
    }

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()