from functools import wraps
import logging
import time
from typing import Any, Callable, Optional



def timeit(logger: Optional[logging.Logger] = None):
    """
    Decorator to time async functions and log execution time.
    
    Usage:
        @timeit()                    # Uses root logger
        @timeit(my_logger)           # Uses custom logger
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            result = await func(*args, **kwargs)
            end_time = time.perf_counter()
            log = logger or logging.getLogger(func.__module__)
            log.info(f"Function {func.__name__} took {end_time - start_time:.2f}s")
            return result
        return wrapper
    return decorator