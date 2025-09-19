from functools import wraps
import logging
import time
from typing import Any, Callable, Optional
import inspect



def timeit(logger: Optional[logging.Logger] = None):
    """
    Decorator to time async functions and log execution time. Work for both async function and sync function
    
    Usage:
        @timeit()                    # Uses root logger
        @timeit(my_logger)           # Uses custom logger
    """
    def decorator(func: Callable) -> Callable:
        log = logger or logging.getLogger(func.__module__)
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> Any:
                start_time = time.perf_counter()
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                log.info(f"Function {func.__name__} took {end_time - start_time:.2f}s")
                return result
        else:
            @wraps(func)
            def wrapper(*args,**kwargs) -> Any:
                start_time = time.perf_counter()
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                log.info(f"Function {func.__name__} took {end_time - start_time:.2f}s")
                return result
    
        return wrapper
    return decorator