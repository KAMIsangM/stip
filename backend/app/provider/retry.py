"""Retry and fallback helpers for external providers."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.core.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int | None = None,
    backoff_seconds: list[float] | None = None,
    label: str = "provider",
) -> T:
    """Run an async operation with configurable retries."""
    cfg = get_settings()
    attempts = max_attempts or cfg["llm"]["retry"]["max_attempts"]
    delays = backoff_seconds or cfg["llm"]["retry"]["backoff_seconds"]
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            logger.warning(
                "%s attempt %s/%s failed: %s", label, attempt, attempts, exc
            )
            if attempt < attempts:
                delay = delays[min(attempt - 1, len(delays) - 1)]
                await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error


async def with_retry_and_fallback(
    primary: Callable[[], Awaitable[T]],
    fallback: Callable[[], Awaitable[T]] | None,
    *,
    label: str = "provider",
) -> T:
    """Try primary with retries; on total failure invoke fallback with retries."""
    try:
        return await with_retry(primary, label=f"{label}:primary")
    except Exception as primary_error:
        if fallback is None:
            raise
        logger.warning(
            "%s primary exhausted, trying fallback: %s", label, primary_error
        )
        try:
            return await with_retry(fallback, label=f"{label}:fallback")
        except Exception as fallback_error:
            raise RuntimeError(
                f"{label} primary and fallback both failed"
            ) from fallback_error
