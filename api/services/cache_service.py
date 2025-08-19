#!/usr/bin/env python3
"""
Cache Service for Finnish Political Analysis System
Provides a fast in-memory caching layer with TTL support
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """
    Memory-based caching service with TTL support
    Provides fast access to frequently requested data
    """
    
    def __init__(self, cleanup_interval: int = 300):
        """
        Initialize the cache service
        
        Args:
            cleanup_interval: Interval in seconds between cache cleanup runs
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_timestamp)
        self._lock = threading.RLock()
        self._cleanup_interval = cleanup_interval
        
        # Start cleanup thread
        self._start_cleanup_thread()
        
        logger.info("Cache service initialized")
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set a value in the cache with a TTL
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default: 1 hour)
        """
        expiry = time.time() + ttl
        
        with self._lock:
            self._cache[key] = (value, expiry)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache
        
        Args:
            key: Cache key
            
        Returns:
            The cached value or None if not found or expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            value, expiry = self._cache[key]
            
            # Check if expired
            if time.time() > expiry:
                # Remove expired item
                del self._cache[key]
                return None
            
            return value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all items from the cache"""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dict with cache statistics
        """
        with self._lock:
            total_items = len(self._cache)
            
            # Count expired items
            now = time.time()
            expired_items = sum(1 for _, expiry in self._cache.values() if now > expiry)
            
            # Calculate memory usage (approximate)
            import sys
            memory_usage = sum(
                sys.getsizeof(key) + sys.getsizeof(value) + sys.getsizeof(expiry)
                for key, (value, expiry) in self._cache.items()
            )
            
            return {
                "total_items": total_items,
                "expired_items": expired_items,
                "active_items": total_items - expired_items,
                "memory_usage_bytes": memory_usage,
                "memory_usage_mb": memory_usage / (1024 * 1024)
            }
    
    def _cleanup_expired(self) -> int:
        """
        Remove expired items from cache
        
        Returns:
            Number of items removed
        """
        now = time.time()
        removed = 0
        
        with self._lock:
            expired_keys = [
                key for key, (_, expiry) in self._cache.items()
                if now > expiry
            ]
            
            for key in expired_keys:
                del self._cache[key]
                removed += 1
        
        if removed > 0:
            logger.debug(f"Removed {removed} expired items from cache")
        
        return removed
    
    def _start_cleanup_thread(self) -> None:
        """Start the background thread that cleans up expired cache entries"""
        def cleanup_task():
            while True:
                time.sleep(self._cleanup_interval)
                try:
                    self._cleanup_expired()
                except Exception as e:
                    logger.error(f"Error in cache cleanup: {e}")
        
        thread = threading.Thread(target=cleanup_task, daemon=True)
        thread.start()
        logger.debug("Cache cleanup thread started")


# Create a singleton instance
_cache_instance = None

def get_cache() -> CacheService:
    """
    Get the global cache service instance
    
    Returns:
        CacheService instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance
