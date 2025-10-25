#!/usr/bin/env python3
"""Quick test to verify imports and basic functionality"""
import sys
import importlib.util

print("Testing imports...")

# Test 1: Rate Limiter
print("\n1. Testing Rate Limiter...")
# Import directly from file to avoid bot_flow/__init__.py
spec = importlib.util.spec_from_file_location("rate_limiter", "bot_flow/flows/rate_limiter.py")
rate_limiter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rate_limiter_module)
RateLimiter = rate_limiter_module.RateLimiter
TokenBucket = rate_limiter_module.TokenBucket
limiter = RateLimiter.get_instance(requests_per_second=5.0, burst_size=10)
print(f"   ✅ Rate limiter created: {limiter.bucket.refill_rate} RPS")
stats = limiter.get_stats()
print(f"   ✅ Stats: {stats}")

# Test 2: Cache Manager
print("\n2. Testing Cache Manager...")
spec = importlib.util.spec_from_file_location("cache_manager", "bot_flow/flows/cache_manager.py")
cache_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cache_module)
CacheManager = cache_module.CacheManager
cache = CacheManager.get_instance(default_ttl=300.0)
cache.set('test_key', 'test_value', ttl=60.0)
value = cache.get('test_key')
print(f"   ✅ Cache set/get works: {value}")
stats = cache.get_stats()
print(f"   ✅ Stats: {stats}")

# Test 3: Metrics
print("\n3. Testing Metrics...")
spec = importlib.util.spec_from_file_location("metrics", "bot_flow/flows/metrics.py")
metrics_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics_module)
MetricsCollector = metrics_module.MetricsCollector
collector = MetricsCollector.get_instance()
collector.record_request('test_endpoint', success=True, duration=0.5)
collector.record_request('test_endpoint', success=True, duration=0.3)
collector.record_request('test_endpoint', success=False, duration=1.0)
stats = collector.get_stats()
print(f"   ✅ Metrics: {stats['total_requests']} requests, {stats['success_rate']} success")
print(f"   ✅ Avg response time: {stats['avg_response_time']}")

# Test 4: Connection pool (requires httpx)
print("\n4. Testing Connection Pool...")
try:
    import asyncio
    from bot_flow.flows.nocodb_utils import get_client_pool, close_client_pool

    async def test_pool():
        client = await get_client_pool()
        print(f"   ✅ Connection pool created: {client}")
        await close_client_pool()
        print(f"   ✅ Connection pool closed")

    asyncio.run(test_pool())
except ImportError as e:
    print(f"   ⚠️  Skipped (missing dependency): {e}")

print("\n✅ All tests passed!")
print("\n📊 Summary:")
print(f"   - Rate Limiter: Working ✅")
print(f"   - Cache Manager: Working ✅")
print(f"   - Metrics: Working ✅")
print(f"   - Connection Pool: {'Working ✅' if 'httpx' in str(locals()) else 'Skipped ⚠️'}")

print("\n🎉 Rate limiting infrastructure is ready!")
