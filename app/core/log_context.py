"""
Request-scoped logging context module.

Provides a mechanism to store and propagate a unique request ID across async
tasks for a single HTTP request. Ensures every log line emitted during the
request lifecycle carries the same identifier for easier tracing.
"""

import logging
from contextvars import ContextVar

# A ContextVar is like a global variable, but scoped per async task —
# each incoming request gets its own isolated value, safe under concurrency.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIDFilter(logging.Filter):
    """
    Logging filter that appends the current request ID to log records.

    This filter intercepts log records and dynamically injects the `request_id`
    attribute by retrieving it from the active `ContextVar`.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Inject the request ID into the log record.

        Args:
            record (logging.LogRecord): The log record being processed.

        Returns:
            bool: Always True to allow the log record to be emitted.
        """
        record.request_id = request_id_ctx.get()
        return True
