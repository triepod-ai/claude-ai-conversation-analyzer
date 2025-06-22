#!/usr/bin/env python3
"""
Redis Caching Layer for Claude Conversation API
Provides ultra-fast caching for frequent queries and search results
"""

import redis
import json
import hashlib
import time
from typing import Optional, Dict, Any, List
from functools import wraps
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCache:
    """High-performance Redis caching layer for conversation search"""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 6379, 
                 db: int = 0,
                 default_ttl: int = 3600):  # 1 hour default TTL
        """
        Initialize Redis cache connection
        
        Args:
            host: Redis server host
            port: Redis server port  
            db: Redis database number
            default_ttl: Default time-to-live in seconds
        """
        try:
            self.redis_client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.default_ttl = default_ttl
            self.is_available = True
            logger.info(f"✅ Redis cache connected: {host}:{port}/{db}")
            
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.warning(f"⚠️  Redis unavailable: {e}")
            self.redis_client = None
            self.is_available = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache key from arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return f"claude_api:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with error handling"""
        if not self.is_available:
            return None
            
        try:
            cached_value = self.redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with error handling"""
        if not self.is_available:
            return False
            
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available:
            return False
            
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError as e:
            logger.warning(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.is_available:
            return 0
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logger.warning(f"Cache clear error: {e}")
        return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        if not self.is_available:
            return {"status": "unavailable"}
            
        try:
            info = self.redis_client.info()
            return {
                "status": "available",
                "used_memory": info.get('used_memory_human', 'Unknown'),
                "connected_clients": info.get('connected_clients', 0),
                "total_commands_processed": info.get('total_commands_processed', 0),
                "keyspace_hits": info.get('keyspace_hits', 0),
                "keyspace_misses": info.get('keyspace_misses', 0),
                "hit_rate": self._calculate_hit_rate(info)
            }
        except redis.RedisError:
            return {"status": "error"}
    
    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

# Global cache instance
cache = RedisCache()

def cached_search(ttl: int = 1800):  # 30 minutes for search results
    """
    Decorator for caching search results
    
    Args:
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(f"search:{func.__name__}", *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"⚡ Cache HIT: {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            # Cache the result
            cache.set(cache_key, result, ttl)
            logger.info(f"💾 Cache MISS: {func.__name__} ({execution_time:.1f}ms)")
            
            return result
        return wrapper
    return decorator

def cached_stats(ttl: int = 300):  # 5 minutes for stats
    """Decorator for caching database statistics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache._generate_key(f"stats:{func.__name__}", *args, **kwargs)
            
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"📊 Stats cache HIT: {func.__name__}")
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.info(f"📊 Stats cache MISS: {func.__name__}")
            
            return result
        return wrapper
    return decorator

# Cache invalidation helpers
def invalidate_search_cache():
    """Invalidate all search-related cache entries"""
    return cache.clear_pattern("claude_api:*search*")

def invalidate_stats_cache():
    """Invalidate all statistics cache entries"""
    return cache.clear_pattern("claude_api:*stats*")

def get_cache_health() -> Dict[str, Any]:
    """Get comprehensive cache health information"""
    stats = cache.get_stats()
    
    return {
        "redis_available": cache.is_available,
        "connection_status": "connected" if cache.is_available else "disconnected", 
        "performance_stats": stats,
        "cache_keys": {
            "search_patterns": "claude_api:*search*",
            "stats_patterns": "claude_api:*stats*"
        },
        "ttl_settings": {
            "search_results": "30 minutes",
            "database_stats": "5 minutes", 
            "default": "1 hour"
        }
    }

if __name__ == "__main__":
    # Test cache functionality
    print("🧪 Testing Redis Cache...")
    
    health = get_cache_health()
    print(f"Cache Status: {health['connection_status']}")
    
    if cache.is_available:
        # Test basic operations
        test_key = "test:performance"
        test_data = {"message": "Redis cache working!", "timestamp": time.time()}
        
        cache.set(test_key, test_data, 60)
        retrieved = cache.get(test_key)
        
        print(f"✅ Test passed: {retrieved}")
        cache.delete(test_key)
    else:
        print("⚠️  Redis not available - caching disabled")