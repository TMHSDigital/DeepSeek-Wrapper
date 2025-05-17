# Utils package for DeepSeek Wrapper 
import functools
import time
import logging
import asyncio
from typing import Callable, Optional, Any, TypeVar
from .realtime import get_realtime_info

T = TypeVar('T')
logger = logging.getLogger(__name__)

def retry(max_attempts: int = 3, base_delay: float = 1.0, backoff_factor: float = 2.0):
    """
    Decorator for retrying a function if it raises an exception.
    
    Args:
        max_attempts: Maximum number of attempts to try the function
        base_delay: Initial delay between retries in seconds
        backoff_factor: Multiplicative factor to increase delay between retries
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempts = 0
            delay = base_delay
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            attempts = 0
            delay = base_delay
            
            while attempts < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {str(e)}")
                        raise
                    
                    logger.warning(f"Attempt {attempts} failed: {str(e)}. Retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    delay *= backoff_factor
            
            # This should never be reached, but just in case
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.__name__ in func.__module__ or 'async' in func.__name__:
            return async_wrapper
        else:
            return wrapper
    
    return decorator

# Export the functions
__all__ = ['retry', 'get_realtime_info'] 