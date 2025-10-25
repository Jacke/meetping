"""
Rate limiter for NocoDB API requests using token bucket algorithm.

This module provides global rate limiting to prevent HTTP 429 errors from NocoDB.
Uses token bucket algorithm with configurable RPS and burst size.
"""
import asyncio
import time
from typing import Optional


class TokenBucket:
    """
    Token bucket rate limiter for async operations.

    Algorithm:
    - Tokens are added to bucket at a constant rate (refill_rate)
    - Each request consumes 1 token
    - Bucket has maximum capacity (burst_size)
    - If no tokens available, request waits until tokens are available

    This prevents burst traffic from overwhelming NocoDB API.
    """

    def __init__(self, requests_per_second: float = 5.0, burst_size: int = 10):
        """
        Initialize token bucket rate limiter.

        Args:
            requests_per_second: Rate at which tokens are added (RPS limit)
            burst_size: Maximum number of tokens (allows bursts up to this limit)
        """
        self.refill_rate = requests_per_second  # tokens per second
        self.capacity = burst_size  # max tokens
        self.tokens = float(burst_size)  # current tokens (start full)
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens from bucket. Waits if not enough tokens available.

        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        async with self.lock:
            while True:
                # Refill tokens based on time elapsed
                now = time.monotonic()
                elapsed = now - self.last_refill
                self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
                self.last_refill = now

                # Check if we have enough tokens
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Not enough tokens, calculate wait time
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.refill_rate

        # Wait outside of lock to allow other coroutines to check
        await asyncio.sleep(wait_time)


class RateLimiter:
    """
    Global rate limiter for NocoDB API requests.

    Usage:
        limiter = RateLimiter.get_instance()
        async with limiter:
            # Make NocoDB request
            response = await client.get(...)
    """

    _instance: Optional['RateLimiter'] = None

    def __init__(self, requests_per_second: float = 5.0, burst_size: int = 10):
        """
        Initialize rate limiter with token bucket.

        Args:
            requests_per_second: Maximum RPS for NocoDB API (default: 5)
            burst_size: Maximum burst size (default: 10)
        """
        self.bucket = TokenBucket(requests_per_second, burst_size)
        self.stats = {
            'total_requests': 0,
            'total_wait_time': 0.0
        }

    @classmethod
    def get_instance(cls, requests_per_second: float = 5.0, burst_size: int = 10) -> 'RateLimiter':
        """
        Get singleton instance of rate limiter.

        Args:
            requests_per_second: Maximum RPS (only used on first call)
            burst_size: Maximum burst size (only used on first call)

        Returns:
            RateLimiter instance
        """
        if cls._instance is None:
            cls._instance = cls(requests_per_second, burst_size)
        return cls._instance

    async def __aenter__(self):
        """Context manager entry - acquire token before request"""
        start = time.monotonic()
        await self.bucket.acquire(1)
        wait_time = time.monotonic() - start

        self.stats['total_requests'] += 1
        self.stats['total_wait_time'] += wait_time

        if wait_time > 0.01:  # Log only if we actually waited
            print(f"⏱️  Rate limiter: waited {wait_time:.2f}s before NocoDB request")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        return False

    def get_stats(self) -> dict:
        """
        Get rate limiter statistics.

        Returns:
            Dict with total_requests and average_wait_time
        """
        total = self.stats['total_requests']
        avg_wait = self.stats['total_wait_time'] / total if total > 0 else 0
        return {
            'total_requests': total,
            'total_wait_time': self.stats['total_wait_time'],
            'average_wait_time': avg_wait
        }
