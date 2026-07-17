"""
Execution profiling utilities module.

Provides decorators and utilities for measuring and logging the execution time
of asynchronous functions, primarily for performance monitoring.
"""

import functools
import logging
import time
from typing import Callable, TypeVar, Awaitable

logger = logging.getLogger("app.profiling")

F = TypeVar("F", bound=Callable[..., Awaitable])

SLOW_THRESHOLD_MS = 200


def log_timing(func: F) -> F:
    """
    Measure and log the execution time of an asynchronous function.

    Wraps an async function and logs its duration in milliseconds. Execution times
    exceeding the `SLOW_THRESHOLD_MS` are logged as warnings to highlight potential
    performance bottlenecks.

    Args:
        func (F): The asynchronous function to wrap and measure.

    Returns:
        F: The wrapped asynchronous function that includes timing logic.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        """
        Execute the wrapped function and record its execution time.

        Args:
            *args: Positional arguments for the wrapped function.
            **kwargs: Keyword arguments for the wrapped function.

        Returns:
            The result of the wrapped function.
        """
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            qualified_name = f"{func.__module__}.{func.__qualname__}"

            if duration_ms >= SLOW_THRESHOLD_MS:
                logger.warning("[FUNC]  SLOW %-55s %.1fms", qualified_name, duration_ms)
            else:
                logger.debug("[FUNC]  %-60s %.1fms", qualified_name, duration_ms)

    return wrapper  # type: ignore[return-value]
