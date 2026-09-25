import json
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.config import settings

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheInterface(ABC):
    """Abstract interface for cache implementations"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Dict[str, Any], expire_hours: int = None) -> bool:
        """Set value in cache with expiration"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass


class RedisCache(CacheInterface):
    """Redis-based cache implementation"""
    
    def __init__(self, redis_url: str):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis package not available")
        
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from Redis cache"""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception:
            return None
    
    async def set(self, key: str, value: Dict[str, Any], expire_hours: int = None) -> bool:
        """Set value in Redis cache with expiration"""
        try:
            expire_seconds = None
            if expire_hours:
                expire_seconds = expire_hours * 3600
            
            return self.redis_client.set(
                key, 
                json.dumps(value, default=str), 
                ex=expire_seconds
            )
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return False


class InMemoryCache(CacheInterface):
    """In-memory cache implementation"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._expiry: Dict[str, float] = {}
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry is expired"""
        if key not in self._expiry:
            return False
        return time.time() > self._expiry[key]
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, expiry_time in self._expiry.items() 
            if current_time > expiry_time
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from in-memory cache"""
        self._cleanup_expired()
        
        if key in self._cache and not self._is_expired(key):
            return self._cache[key].copy()
        return None
    
    async def set(self, key: str, value: Dict[str, Any], expire_hours: int = None) -> bool:
        """Set value in in-memory cache with expiration"""
        try:
            self._cache[key] = value.copy()
            
            if expire_hours:
                self._expiry[key] = time.time() + (expire_hours * 3600)
            
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from in-memory cache"""
        try:
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return True
        except Exception:
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in in-memory cache"""
        self._cleanup_expired()
        return key in self._cache and not self._is_expired(key)


class CacheService:
    """Main cache service that manages cache operations"""
    
    def __init__(self):
        self.cache_impl = self._initialize_cache()
        self.default_expire_hours = settings.cache_expiration_hours
    
    def _initialize_cache(self) -> CacheInterface:
        """Initialize appropriate cache implementation"""
        if settings.redis_url and REDIS_AVAILABLE:
            try:
                return RedisCache(settings.redis_url)
            except Exception:
                # Fall back to in-memory cache if Redis fails
                pass
        
        return InMemoryCache()
    
    async def get_cached_image(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached image data
        
        Args:
            cache_key: Cache key for the image
            
        Returns:
            Cached image data or None if not found
        """
        return await self.cache_impl.get(cache_key)
    
    async def cache_image(
        self, 
        cache_key: str, 
        image_url: str, 
        created_at: datetime,
        expire_hours: int = None
    ) -> bool:
        """
        Cache image data
        
        Args:
            cache_key: Cache key for the image
            image_url: URL of the generated image
            created_at: When the image was created
            expire_hours: Cache expiration in hours (optional)
            
        Returns:
            True if successful, False otherwise
        """
        cache_data = {
            "image_url": image_url,
            "created_at": created_at.isoformat(),
            "cached_at": datetime.now().isoformat()
        }
        
        expire_hours = expire_hours or self.default_expire_hours
        return await self.cache_impl.set(cache_key, cache_data, expire_hours)
    
    async def invalidate_cache(self, cache_key: str) -> bool:
        """
        Invalidate cached image
        
        Args:
            cache_key: Cache key to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        return await self.cache_impl.delete(cache_key)
    
    async def is_cached(self, cache_key: str) -> bool:
        """
        Check if image is cached
        
        Args:
            cache_key: Cache key to check
            
        Returns:
            True if cached, False otherwise
        """
        return await self.cache_impl.exists(cache_key)

