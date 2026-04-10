# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartTimer - Async-only non-blocking timers.

Provides setTimeout/setInterval semantics (like JavaScript) for async contexts.
Raises RuntimeError if called outside a running event loop.

API:
    set_timeout(delay, callback, *args, **kwargs) -> timer_id
    set_interval(delay, callback, *args, **kwargs) -> timer_id
    cancel_timer(timer_id) -> bool

Callback handling:
    - Async callback: awaited directly
    - Sync callback: offloaded to thread via asyncio.to_thread
"""

import asyncio
import inspect
from collections.abc import Callable
from typing import Any

from .smartasync import is_async_context as _is_async_context
from .uid import get_uuid

_timers: dict[str, asyncio.Task] = {}


def _require_async_context() -> None:
    """Raise RuntimeError if called outside an async context."""
    if not _is_async_context():
        raise RuntimeError(
            "set_timeout/set_interval require a running async event loop. "
            "Call them from within an async function or an active asyncio.run() context."
        )


async def _invoke_async(callback: Callable, *args: Any, **kwargs: Any) -> None:
    """Invoke callback, handling both sync and async callables."""
    if inspect.iscoroutinefunction(callback):
        await callback(*args, **kwargs)
    else:
        await asyncio.to_thread(callback, *args, **kwargs)


def _cleanup(timer_id: str) -> None:
    """Remove timer from registry."""
    _timers.pop(timer_id, None)


async def _async_timeout(
    timer_id: str, delay: float, callback: Callable, args: tuple, kwargs: dict
) -> None:
    """Execute a one-shot timer."""
    try:
        await asyncio.sleep(delay)
        await _invoke_async(callback, *args, **kwargs)
    finally:
        _cleanup(timer_id)


async def _async_interval(
    timer_id: str,
    delay: float,
    callback: Callable,
    args: tuple,
    kwargs: dict,
    first_delay: float,
) -> None:
    """Execute a repeating timer."""
    try:
        await asyncio.sleep(first_delay)
        await _invoke_async(callback, *args, **kwargs)
        while True:
            await asyncio.sleep(delay)
            await _invoke_async(callback, *args, **kwargs)
    finally:
        _cleanup(timer_id)


def set_timeout(delay: float, callback: Callable, *args: Any, **kwargs: Any) -> str:
    """Schedule a one-shot callback after delay seconds. Returns timer ID.

    Raises RuntimeError if called outside an async context.
    """
    _require_async_context()
    timer_id = get_uuid()
    loop = asyncio.get_running_loop()
    task = loop.create_task(_async_timeout(timer_id, delay, callback, args, kwargs))
    _timers[timer_id] = task
    return timer_id


def set_interval(
    delay: float,
    callback: Callable,
    *args: Any,
    initial_delay: float | None = None,
    **kwargs: Any,
) -> str:
    """Schedule a repeating callback every delay seconds. Returns timer ID.

    Raises RuntimeError if called outside an async context.
    """
    _require_async_context()
    timer_id = get_uuid()
    first_delay = initial_delay if initial_delay is not None else delay
    loop = asyncio.get_running_loop()
    task = loop.create_task(
        _async_interval(timer_id, delay, callback, args, kwargs, first_delay)
    )
    _timers[timer_id] = task
    return timer_id


def cancel_timer(timer_id: str) -> bool:
    """Cancel a timer by its ID. Returns True if found and cancelled."""
    task = _timers.pop(timer_id, None)
    if task is None:
        return False
    task.cancel()
    return True
