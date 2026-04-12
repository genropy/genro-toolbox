# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartRetry - Retry decorator with exponential backoff for sync and async functions.

Provides @smartretry for static config, retry_call for runtime config,
and RETRY_PRESETS with predefined policies (network, aggressive, gentle).
"""

import asyncio
import functools
import inspect
import random
import time
from collections.abc import Callable
from typing import Any

RETRY_PRESETS: dict[str, dict[str, Any]] = {
    "network": {
        "max_attempts": 3,
        "delay": 1.0,
        "backoff": 2.0,
        "jitter": True,
        "on": (ConnectionError, TimeoutError, OSError),
    },
    "aggressive": {
        "max_attempts": 5,
        "delay": 0.5,
        "backoff": 2.0,
        "jitter": True,
        "on": (Exception,),
    },
    "gentle": {
        "max_attempts": 2,
        "delay": 2.0,
        "backoff": 1.5,
        "jitter": False,
        "on": (ConnectionError, TimeoutError),
    },
}


def smartretry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    on: tuple[type[BaseException], ...] = (Exception,),
) -> Callable:
    """Retry decorator with exponential backoff. Detects sync/async at decoration time.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier applied to delay after each retry.
        jitter: Add random 0-10% variance to delay.
        on: Exception types to retry on.
    """
    if callable(max_attempts) and not isinstance(max_attempts, int):
        raise TypeError("smartretry requires arguments: use @smartretry() not @smartretry")

    def decorator(func: Callable) -> Callable:
        is_coro = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: BaseException | None = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except on as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        sleep_time = current_delay
                        if jitter:
                            sleep_time *= 1 + random.random() * 0.1
                        time.sleep(sleep_time)
                        current_delay *= backoff
            raise last_error  # type: ignore[misc]

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            last_error: BaseException | None = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except on as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        sleep_time = current_delay
                        if jitter:
                            sleep_time *= 1 + random.random() * 0.1
                        await asyncio.sleep(sleep_time)
                        current_delay *= backoff
            raise last_error  # type: ignore[misc]

        return async_wrapper if is_coro else sync_wrapper

    return decorator


def retry_call(
    func: Callable,
    args: tuple = (),
    kwargs: dict[str, Any] | None = None,
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    jitter: bool = True,
    on: tuple[type[BaseException], ...] = (Exception,),
    policy: dict[str, Any] | None = None,
) -> Any:
    """Call a function with retry logic. Returns coroutine for async callables.

    If policy is provided, its keys override the individual parameters.
    """
    if kwargs is None:
        kwargs = {}
    if policy is not None:
        max_attempts = policy.get("max_attempts", max_attempts)
        delay = policy.get("delay", delay)
        backoff = policy.get("backoff", backoff)
        jitter = policy.get("jitter", jitter)
        on = policy.get("on", on)

    decorated = smartretry(
        max_attempts=max_attempts,
        delay=delay,
        backoff=backoff,
        jitter=jitter,
        on=on,
    )(func)
    return decorated(*args, **kwargs)
