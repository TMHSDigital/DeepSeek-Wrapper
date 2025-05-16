import time
from functools import wraps
from typing import Callable

def retry(max_retries: int = 3, backoff: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    from .errors import DeepSeekAuthError
                    if isinstance(e, DeepSeekAuthError):
                        raise
                    retries += 1
                    if retries > max_retries:
                        raise
                    time.sleep(backoff * (2 ** (retries - 1)))
        return wrapper
    return decorator 