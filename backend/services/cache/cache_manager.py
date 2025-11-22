"""
Redis-based cache manager for NovaIntel.
"""
import json
import hashlib
from typing import Optional, Any, Dict
from utils.config import settings

class CacheManager:
    """Manages Redis cache connections and operations."""
    
    def __init__(self):
        self.redis_client = None
        self._enabled = settings.REDIS_ENABLED
        self._initialize()
    
    def _initialize(self):
        """Initialize Redis connection."""
        if not self._enabled:
            print("[INFO] Redis caching is disabled")
            return
        
        try:
            import redis
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                db=settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            print(f"[OK] Redis cache connected: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        except ImportError:
            print("[WARNING] Redis not installed. Run: pip install redis hiredis")
            self.redis_client = None
            self._enabled = False
        except Exception as e:
            print(f"[WARNING] Redis connection failed: {e}")
            print("   Caching will be disabled. Continuing without cache...")
            self.redis_client = None
            self._enabled = False
    
    def is_available(self) -> bool:
        """Check if cache is available."""
        return self._enabled and self.redis_client is not None
    
    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """Create a cache key from prefix and arguments."""
        # Create a hash of the arguments
        key_parts = [prefix]
        if args:
            key_parts.extend(str(arg) for arg in args)
        if kwargs:
            # Sort kwargs for consistent keys
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend(f"{k}:{v}" for k, v in sorted_kwargs)
        
        key_string = ":".join(key_parts)
        # Hash if too long (Redis key limit is 512MB, but we'll limit to 250 chars)
        if len(key_string) > 250:
            key_hash = hashlib.md5(key_string.encode()).hexdigest()
            return f"{prefix}:hash:{key_hash}"
        return key_string
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as e:
            print(f"[WARNING] Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.is_available():
            return False
        
        try:
            ttl = ttl or settings.CACHE_TTL
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            print(f"[WARNING] Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            print(f"[WARNING] Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            print(f"[WARNING] Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            print(f"[WARNING] Cache exists error for key {key}: {e}")
            return False
    
    def get_or_set(self, key: str, func, ttl: Optional[int] = None, *args, **kwargs) -> Any:
        """Get from cache or compute and set if not exists."""
        # Try to get from cache
        cached = self.get(key)
        if cached is not None:
            return cached
        
        # Compute value
        value = func(*args, **kwargs)
        
        # Store in cache
        if value is not None:
            self.set(key, value, ttl)
        
        return value
    
    def invalidate_project(self, project_id: int):
        """Invalidate all cache entries for a project."""
        patterns = [
            f"rag:query:*:project:{project_id}",
            f"rag:embedding:*:project:{project_id}",
            f"rag:context:*:project:{project_id}",
            f"workflow:*:project:{project_id}",
        ]
        for pattern in patterns:
            self.delete_pattern(pattern)

# Global instance
cache_manager = CacheManager()

