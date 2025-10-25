"""
Metrics and monitoring for NocoDB API usage.

Provides counters and stats for tracking API health and rate limiting.
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class APIMetrics:
    """Metrics for API requests"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rate_limited_requests: int = 0  # HTTP 429 responses
    total_retry_attempts: int = 0
    total_response_time: float = 0.0  # seconds

    # Breakdown by endpoint
    requests_by_endpoint: Dict[str, int] = field(default_factory=dict)

    # Rate limiting stats
    rate_limit_waits: int = 0  # Number of times we waited due to rate limiter
    total_rate_limit_wait_time: float = 0.0  # Total time spent waiting

    # Cache stats (will be populated from CacheManager)
    cache_hits: int = 0
    cache_misses: int = 0


class MetricsCollector:
    """
    Singleton metrics collector for tracking NocoDB API usage.

    Usage:
        collector = MetricsCollector.get_instance()

        # Record request
        start = time.time()
        try:
            response = await make_request(...)
            collector.record_request(endpoint, success=True, duration=time.time()-start)
        except Exception:
            collector.record_request(endpoint, success=False, duration=time.time()-start)

        # Get stats
        stats = collector.get_stats()
        print(f"Success rate: {stats['success_rate']}")
    """

    _instance: Optional['MetricsCollector'] = None

    def __init__(self):
        self.metrics = APIMetrics()
        self.start_time = time.time()

    @classmethod
    def get_instance(cls) -> 'MetricsCollector':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def record_request(
        self,
        endpoint: str,
        success: bool,
        duration: float,
        is_retry: bool = False,
        is_rate_limited: bool = False
    ) -> None:
        """
        Record API request metrics.

        Args:
            endpoint: API endpoint name (e.g., "get_records", "create_record")
            success: Whether request was successful
            duration: Request duration in seconds
            is_retry: Whether this was a retry attempt
            is_rate_limited: Whether this request got 429 response
        """
        self.metrics.total_requests += 1

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        if is_retry:
            self.metrics.total_retry_attempts += 1

        if is_rate_limited:
            self.metrics.rate_limited_requests += 1

        self.metrics.total_response_time += duration

        # Track per-endpoint
        if endpoint not in self.metrics.requests_by_endpoint:
            self.metrics.requests_by_endpoint[endpoint] = 0
        self.metrics.requests_by_endpoint[endpoint] += 1

    def record_rate_limit_wait(self, wait_time: float) -> None:
        """
        Record time spent waiting due to rate limiter.

        Args:
            wait_time: Time waited in seconds
        """
        self.metrics.rate_limit_waits += 1
        self.metrics.total_rate_limit_wait_time += wait_time

    def update_cache_stats(self, hits: int, misses: int) -> None:
        """
        Update cache statistics.

        Args:
            hits: Number of cache hits
            misses: Number of cache misses
        """
        self.metrics.cache_hits = hits
        self.metrics.cache_misses = misses

    def get_stats(self) -> dict:
        """
        Get comprehensive statistics.

        Returns:
            Dict with all metrics and calculated stats
        """
        total = self.metrics.total_requests
        success_rate = (self.metrics.successful_requests / total * 100) if total > 0 else 0
        avg_response_time = (self.metrics.total_response_time / total) if total > 0 else 0

        cache_total = self.metrics.cache_hits + self.metrics.cache_misses
        cache_hit_rate = (self.metrics.cache_hits / cache_total * 100) if cache_total > 0 else 0

        avg_rate_wait = (
            self.metrics.total_rate_limit_wait_time / self.metrics.rate_limit_waits
        ) if self.metrics.rate_limit_waits > 0 else 0

        uptime = time.time() - self.start_time
        requests_per_minute = (total / uptime * 60) if uptime > 0 else 0

        return {
            # Request stats
            'total_requests': total,
            'successful_requests': self.metrics.successful_requests,
            'failed_requests': self.metrics.failed_requests,
            'success_rate': f"{success_rate:.1f}%",

            # Rate limiting stats
            'rate_limited_requests': self.metrics.rate_limited_requests,
            'rate_limit_waits': self.metrics.rate_limit_waits,
            'total_rate_limit_wait_time': f"{self.metrics.total_rate_limit_wait_time:.1f}s",
            'avg_rate_limit_wait': f"{avg_rate_wait:.1f}s",

            # Performance stats
            'total_retry_attempts': self.metrics.total_retry_attempts,
            'avg_response_time': f"{avg_response_time:.3f}s",
            'requests_per_minute': f"{requests_per_minute:.1f}",

            # Cache stats
            'cache_hits': self.metrics.cache_hits,
            'cache_misses': self.metrics.cache_misses,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",

            # Breakdown
            'requests_by_endpoint': self.metrics.requests_by_endpoint,

            # System stats
            'uptime': f"{uptime:.0f}s"
        }

    def print_stats(self) -> None:
        """Print formatted statistics to console"""
        stats = self.get_stats()

        print("\n" + "="*60)
        print("📊 NocoDB API Metrics")
        print("="*60)

        print(f"\n📈 Requests:")
        print(f"   Total: {stats['total_requests']}")
        print(f"   Successful: {stats['successful_requests']}")
        print(f"   Failed: {stats['failed_requests']}")
        print(f"   Success Rate: {stats['success_rate']}")
        print(f"   RPS: {stats['requests_per_minute']} req/min")

        print(f"\n⏱️  Performance:")
        print(f"   Avg Response Time: {stats['avg_response_time']}")
        print(f"   Total Retries: {stats['total_retry_attempts']}")

        print(f"\n🚦 Rate Limiting:")
        print(f"   429 Responses: {stats['rate_limited_requests']}")
        print(f"   Rate Limit Waits: {stats['rate_limit_waits']}")
        print(f"   Total Wait Time: {stats['total_rate_limit_wait_time']}")
        print(f"   Avg Wait Time: {stats['avg_rate_limit_wait']}")

        print(f"\n💾 Cache:")
        print(f"   Hits: {stats['cache_hits']}")
        print(f"   Misses: {stats['cache_misses']}")
        print(f"   Hit Rate: {stats['cache_hit_rate']}")

        if stats['requests_by_endpoint']:
            print(f"\n🎯 Requests by Endpoint:")
            for endpoint, count in sorted(
                stats['requests_by_endpoint'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                print(f"   {endpoint}: {count}")

        print(f"\n⏰ Uptime: {stats['uptime']}")
        print("="*60 + "\n")

    def reset(self) -> None:
        """Reset all metrics"""
        self.metrics = APIMetrics()
        self.start_time = time.time()
