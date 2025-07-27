"""
Neo4j Database Connection Module
Provides async connection to Neo4j database
"""

import os
import asyncio
from typing import Optional, AsyncGenerator
from neo4j import AsyncGraphDatabase, AsyncSession

# Default connection parameters
DEFAULT_URI = "bolt://localhost:7687"
DEFAULT_USERNAME = "neo4j"
DEFAULT_PASSWORD = "password"

# Global connection instance
_driver = None


async def get_neo4j_connection():
    """
    Get or create a Neo4j driver instance
    
    Returns:
        Neo4j driver instance
    """
    global _driver
    
    if _driver is None:
        # Get connection parameters from environment variables or use defaults
        uri = os.getenv("NEO4J_URI", DEFAULT_URI)
        username = os.getenv("NEO4J_USERNAME", DEFAULT_USERNAME)
        password = os.getenv("NEO4J_PASSWORD", DEFAULT_PASSWORD)
        
        try:
            _driver = AsyncGraphDatabase.driver(uri, auth=(username, password))
            
            # Verify connection
            await _driver.verify_connectivity()
            
        except Exception as e:
            print(f"Failed to connect to Neo4j: {str(e)}")
            raise
            
    return _driver


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create and yield a Neo4j session
    
    Yields:
        AsyncSession: Neo4j session
    """
    driver = await get_neo4j_connection()
    session = driver.session()
    
    try:
        yield session
    finally:
        await session.close()


async def close_neo4j_connection():
    """
    Close Neo4j driver connection
    """
    global _driver
    
    if _driver is not None:
        await _driver.close()
        _driver = None
