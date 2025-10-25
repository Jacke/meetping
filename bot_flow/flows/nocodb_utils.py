"""
Utility functions for NocoDB API requests with retry logic.
"""
import asyncio
import random
import httpx
from typing import Optional
from bot_flow.flows.rate_limiter import RateLimiter


# Global connection pool (singleton pattern)
_client_pool: Optional[httpx.AsyncClient] = None

# Global request counter for tracking RPS
_request_counter = {
    'total': 0,
    'success': 0,
    'failed': 0,
    'rate_limited': 0
}


def get_request_stats() -> dict:
    """Get current request statistics"""
    return _request_counter.copy()


async def get_client_pool() -> httpx.AsyncClient:
    """
    Get or create global httpx AsyncClient with connection pooling.

    Returns:
        Shared httpx.AsyncClient instance
    """
    global _client_pool
    if _client_pool is None:
        _client_pool = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=20,  # Max concurrent connections
                max_keepalive_connections=10  # Keep 10 connections alive
            ),
            timeout=httpx.Timeout(30.0)  # Global timeout
        )
    return _client_pool


async def close_client_pool() -> None:
    """Close global client pool (call on shutdown)"""
    global _client_pool
    if _client_pool is not None:
        await _client_pool.aclose()
        _client_pool = None


async def nocodb_request_with_retry(
    method: str,
    url: str,
    headers: dict,
    max_retries: int = 5,
    base_delay: float = 3.0,
    **kwargs
) -> httpx.Response:
    """
    Make HTTP request to NocoDB with exponential backoff + jitter for 429 errors.

    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        url: Request URL
        headers: Request headers
        max_retries: Maximum number of retries for 429 errors (default: 5, increased from 3)
        base_delay: Base delay in seconds (default: 3s, increased from 2s)
        **kwargs: Additional arguments for httpx request (json, params, timeout, etc.)

    Returns:
        httpx.Response object

    Raises:
        httpx.HTTPStatusError: For non-429 HTTP errors
        Exception: For other errors after all retries exhausted
    """
    import time
    from datetime import datetime

    # Get rate limiter singleton
    rate_limiter = RateLimiter.get_instance()

    # Get shared client pool
    client = await get_client_pool()

    # Extract endpoint name for logging (clean URL)
    endpoint = url.replace('https://app.nocodb.com', '').replace('/api/v2/tables/', 'tables/')
    if len(endpoint) > 60:
        endpoint = endpoint[:57] + '...'

    # Extract params/body for logging
    params = kwargs.get('params', {})
    json_data = kwargs.get('json', {})

    for attempt in range(max_retries + 1):
        try:
            # Apply rate limiting before request
            start_time = time.time()
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            # Log outgoing request
            print(f"\n📤 [{timestamp}] NocoDB Request:")
            print(f"   Method: {method}")
            print(f"   Endpoint: {endpoint}")
            if params:
                # Format params nicely
                params_str = ", ".join(f"{k}={v}" for k, v in params.items())
                if len(params_str) > 100:
                    params_str = params_str[:97] + '...'
                print(f"   Params: {params_str}")
            if json_data:
                # Show json body (truncated)
                json_str = str(json_data)
                if len(json_str) > 150:
                    json_str = json_str[:147] + '...'
                print(f"   Body: {json_str}")

            async with rate_limiter:
                response = await client.request(method, url, headers=headers, **kwargs)

                # Update counters
                _request_counter['total'] += 1

                # Log response
                duration = time.time() - start_time
                timestamp_end = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                # Choose emoji based on status
                if response.status_code < 300:
                    status_emoji = "✅"
                    _request_counter['success'] += 1
                elif response.status_code == 429:
                    status_emoji = "🚫"
                    _request_counter['rate_limited'] += 1
                elif response.status_code < 500:
                    status_emoji = "⚠️"
                    _request_counter['failed'] += 1
                else:
                    status_emoji = "❌"
                    _request_counter['failed'] += 1

                print(f"{status_emoji} [{timestamp_end}] NocoDB Response: {response.status_code} in {duration:.3f}s")

                # Show response size
                content_length = response.headers.get('content-length', 'unknown')
                print(f"   Size: {content_length} bytes")

                # For list responses, show count
                if response.status_code < 300:
                    try:
                        data = response.json()
                        if 'list' in data:
                            print(f"   Records: {len(data['list'])}")
                        elif 'id' in data or 'Id' in data:
                            print(f"   Record ID: {data.get('id') or data.get('Id')}")
                    except:
                        pass

                # Show cumulative stats
                print(f"   📊 Total requests: {_request_counter['total']} " +
                      f"(✅ {_request_counter['success']}, " +
                      f"❌ {_request_counter['failed']}, " +
                      f"🚫 {_request_counter['rate_limited']})")

                # Check for 429 - too many requests
                if response.status_code == 429:
                    if attempt < max_retries:
                        # Calculate delay with exponential backoff + jitter
                        exponential_delay = base_delay * (2 ** attempt)  # 3s, 6s, 12s, 24s, 48s
                        jitter = random.uniform(0, exponential_delay * 0.3)  # Add 0-30% jitter
                        delay = exponential_delay + jitter

                        # Check for Retry-After header
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                # Retry-After can be seconds or HTTP date
                                retry_delay = float(retry_after)
                                delay = max(delay, retry_delay)  # Use larger of the two
                                print(f"⚠️  Rate limit (429), Retry-After: {retry_delay}s")
                            except ValueError:
                                pass  # Ignore if not a number

                        print(f"⚠️  Rate limit (429) from NocoDB, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(delay)
                        continue  # Retry
                    else:
                        print(f"❌ Rate limit (429) exceeded max retries")
                        response.raise_for_status()  # This will raise HTTPStatusError

                return response

        except httpx.HTTPStatusError:
            # Re-raise HTTP errors (including 429 after max retries)
            raise
        except Exception as e:
            if attempt < max_retries:
                # Apply exponential backoff + jitter for other errors
                exponential_delay = base_delay * (2 ** attempt)
                jitter = random.uniform(0, exponential_delay * 0.3)
                delay = exponential_delay + jitter

                print(f"⚠️  Request error: {e}, retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
            else:
                # Re-raise after max retries
                raise

    # Should not reach here
    raise Exception("Unexpected error in nocodb_request_with_retry")
