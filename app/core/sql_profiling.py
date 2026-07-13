"""
SQL query profiling module.

Provides functionality to attach SQLAlchemy event listeners to the engine, logging
every executed SQL statement along with its execution time. This aids in identifying
slow queries and performance bottlenecks during development.
"""

import logging
import time

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("app.sql_profiling")

SLOW_QUERY_THRESHOLD_MS = 100


def enable_sql_profiling(engine: Engine) -> None:
    """
    Enable SQL execution profiling on a given SQLAlchemy engine.

    Attaches `before_cursor_execute` and `after_cursor_execute` event listeners
    to calculate query durations and log them. Slow queries are logged as warnings.

    Args:
        engine (Engine): The SQLAlchemy sync engine to profile.
    """

    @event.listens_for(engine, "before_cursor_execute")
    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        start = conn.info["query_start_time"].pop(-1)
        duration_ms = (time.perf_counter() - start) * 1000
        clean_statement = " ".join(statement.split())

        if duration_ms >= SLOW_QUERY_THRESHOLD_MS:
            logger.warning(
                "[SQL]   SLOW (%.1fms): %s | params=%s",
                duration_ms,
                clean_statement,
                parameters,
            )
        else:
            logger.debug("[SQL]   (%.1fms): %s", duration_ms, clean_statement)
