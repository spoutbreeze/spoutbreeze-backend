import redis.asyncio as redis
from redis.asyncio import Redis
from app.config.settings import get_settings
from app.config.logger_config import get_logger
from typing import Optional
import pickle
from functools import wraps
import hashlib
import asyncio

settings = get_settings()
logger = get_logger("Redis")

class RedisCache:
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        
    async def connect(self):
        """Initialize Redis connection with retry logic"""
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Parse Redis URL or use default connection
                if settings.redis_url.startswith('redis://'):
                    self.redis_client = redis.from_url(
                        settings.redis_url,
                        encoding="utf-8",
                        decode_responses=False,
                        max_connections=20,
                        retry_on_timeout=True,
                        socket_timeout=5,
                        socket_connect_timeout=5
                    )
                else:
                    # Fallback to direct connection
                    self.redis_client = redis.Redis(
                        host='localhost',
                        port=6379,
                        db=0,
                        encoding="utf-8",
                        decode_responses=False,
                        max_connections=20,
                        retry_on_timeout=True,
                        socket_timeout=5,
                        socket_connect_timeout=5
                    )
                
                # Test connection
                await self.redis_client.ping()
                logger.info(f"Redis connection established successfully on attempt {attempt + 1}")
                return
                
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("Failed to connect to Redis after all retries. Caching will be disabled.")
                    self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
    
    async def get(self, key: str):
        """Get value from cache"""
        if not self.redis_client:
            return None
        try:
            value = await self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value, ttl: int = 300):
        """Set value in cache with TTL in seconds"""
        if not self.redis_client:
            return False
        try:
            serialized_value = pickle.dumps(value)
            await self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return False
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE_PATTERN error for pattern {pattern}: {e}")
            return False

    async def health_check(self) -> bool:
        """Check if Redis is healthy"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

# Global cache instance
cache = RedisCache()

def generate_cache_key(*args, **kwargs) -> str:
    """Generate a consistent cache key from arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(ttl: int = 300, key_prefix: str = ""):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            logger.debug(f"Cache SET for key: {cache_key}")
            return result
        return wrapper
    return decorator