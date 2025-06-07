import time
import asyncio
from functools import wraps

def cached_async(expire=60):
    cache_storage = {}

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = (func.__name__, args, frozenset(kwargs.items()))
            now = time.time()

            if key in cache_storage:
                result, timestamp = cache_storage[key]
                if now - timestamp < expire:
                    return result

            result = await func(*args, **kwargs)
            cache_storage[key] = (result, now)
            return result
        return wrapper
    return decorator
