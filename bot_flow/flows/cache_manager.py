"""
Cache manager for NocoDB data (texts, config).

Provides in-memory caching with TTL to reduce API calls.
"""
import time
import asyncio
from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass


@dataclass
class CacheEntry:
    """Cache entry with data and expiration time"""
    data: Any
    expires_at: float


class CacheManager:
    """
    In-memory cache with TTL (Time To Live).

    Usage:
        cache = CacheManager.get_instance()

        # Try to get from cache
        texts = cache.get('texts')
        if texts is None:
            # Cache miss, load from NocoDB
            texts = await load_texts_from_nocodb()
            cache.set('texts', texts, ttl=300)  # Cache for 5 minutes
    """

    _instance: Optional['CacheManager'] = None

    def __init__(self, default_ttl: float = 300.0):
        """
        Initialize cache manager.

        Args:
            default_ttl: Default TTL in seconds (default: 300s = 5 minutes)
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = asyncio.Lock()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }

    @classmethod
    def get_instance(cls, default_ttl: float = 300.0) -> 'CacheManager':
        """
        Get singleton instance of cache manager.

        Args:
            default_ttl: Default TTL (only used on first call)

        Returns:
            CacheManager instance
        """
        if cls._instance is None:
            cls._instance = cls(default_ttl)
        return cls._instance

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self.cache.get(key)

        if entry is None:
            self.stats['misses'] += 1
            return None

        # Check if expired
        if time.monotonic() >= entry.expires_at:
            # Expired, remove from cache
            del self.cache[key]
            self.stats['misses'] += 1
            return None

        self.stats['hits'] += 1
        return entry.data

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use default)
        """
        if ttl is None:
            ttl = self.default_ttl

        expires_at = time.monotonic() + ttl
        self.cache[key] = CacheEntry(data=value, expires_at=expires_at)
        self.stats['sets'] += 1

    def invalidate(self, key: str) -> None:
        """
        Manually invalidate (remove) cache entry.

        Args:
            key: Cache key to remove
        """
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear entire cache"""
        self.cache.clear()

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: Callable,
        ttl: Optional[float] = None
    ) -> Any:
        """
        Get value from cache or fetch if not available.

        Thread-safe with async lock to prevent thundering herd.

        Args:
            key: Cache key
            fetch_fn: Async function to fetch data if cache miss
            ttl: TTL in seconds (None = use default)

        Returns:
            Cached or fetched value
        """
        # Try without lock first (fast path)
        value = self.get(key)
        if value is not None:
            return value

        # Cache miss, acquire lock to prevent multiple fetches
        async with self.lock:
            # Double-check after acquiring lock
            value = self.get(key)
            if value is not None:
                return value

            # Fetch data
            value = await fetch_fn()
            self.set(key, value, ttl)
            return value

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, hit_rate, total_entries
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.1f}%",
            'total_sets': self.stats['sets'],
            'total_entries': len(self.cache)
        }

    def cleanup_expired(self) -> int:
        """
        Manually cleanup expired entries.

        Returns:
            Number of entries removed
        """
        now = time.monotonic()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry.expires_at
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)
