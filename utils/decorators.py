"""Generic route decorators. Moved verbatim from app.py."""

import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def timeout_decorator(seconds=120):
    """Decorator to add timeout to routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if elapsed > seconds:
                    logger.warning(f"Request took {elapsed:.2f}s (exceeded {seconds}s timeout)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Request failed after {elapsed:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator
