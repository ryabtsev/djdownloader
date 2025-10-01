import asyncio
import logging
from functools import wraps
import aiohttp

logging.basicConfig(level=logging.INFO)


def async_backoff(tries: int, delay: int, backoff: int = 2):
    """
    Async backoff decorator.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries > 1:
                try:
                    return await func(*args, **kwargs)
                except aiohttp.ClientError as e:
                    await asyncio.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            return await func(*args, **kwargs)
        return wrapper
    return decorator
