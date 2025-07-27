"""
Configuration management for FPAS API
Handles environment variables and application settings
"""

import os
from pydantic import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Finnish Politician Analysis System"
    
    # Neo4j settings - using the same environment vars as the core project
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # OpenAI settings for AI pipeline
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # API Security
    CORS_ORIGINS: list = ["*"]  # For production, specify specific origins
    
    # Caching settings
    CACHE_EXPIRY_SECONDS: int = 300  # 5 minutes
    
    # Pagination defaults
    DEFAULT_LIMIT: int = 100
    MAX_LIMIT: int = 500
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
