"""
Utility functions for NocoDB API requests with retry logic.
"""
import asyncio
import httpx


async def nocodb_request_with_retry(
    method: str,
    url: str,
    headers: dict,
    max_retries: int = 3,
    base_delay: float = 2.0,
    **kwargs
) -> httpx.Response:
    """
    Make HTTP request to NocoDB with exponential backoff for 429 errors.

    Args:
        method: HTTP method (GET, POST, PATCH, etc.)
        url: Request URL
        headers: Request headers
        max_retries: Maximum number of retries for 429 errors
        base_delay: Base delay in seconds (exponential: 2s, 4s, 8s)
        **kwargs: Additional arguments for httpx request (json, params, timeout, etc.)

    Returns:
        httpx.Response object

    Raises:
        httpx.HTTPStatusError: For non-429 HTTP errors
        Exception: For other errors after all retries exhausted
    """
    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, headers=headers, **kwargs)

                # Check for 429 - too many requests
                if response.status_code == 429:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)  # Exponential: 2s, 4s, 8s
                        print(f"⚠️  Rate limit (429) from NocoDB, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
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
                delay = base_delay * (2 ** attempt)
                print(f"⚠️  Request error: {e}, retrying in {delay}s (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                continue
            else:
                # Re-raise after max retries
                raise

    # Should not reach here
    raise Exception("Unexpected error in nocodb_request_with_retry")
