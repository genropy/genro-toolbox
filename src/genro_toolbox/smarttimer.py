# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartTimer - Non-blocking timers with automatic sync/async detection.

Provides setTimeout/setInterval semantics (like JavaScript) that work
transparently in both sync and async Python contexts.

API:
    set_timeout(delay, callback, *args, **kwargs) -> timer_id
    set_interval(delay, callback, *args, **kwargs) -> timer_id
    cancel_timer(timer_id) -> bool

Context detection:
    - Sync context: uses threading.Timer (non-blocking)
    - Async context: uses asyncio tasks with asyncio.sleep

Callback handling:
    - Sync callback in sync context: called directly in timer thread
    - Async callback in sync context: run on a per-thread event loop
    - Sync callback in async context: offloaded to thread via to_thread
    - Async callback in async context: awaited directly
"""

import asyncio
import functools
import inspect
import threading
from collections.abc import Callable
from typing import Any

from .smartasync import is_async_context as _is_async_context
from .uid import get_uuid

_timers: dict[str, Any] = {}
_timers_lock = threading.Lock()


async def _invoke_async(callback: Callable, *args: Any, **kwargs: Any) -> None:
    """Invoke callback, handling both sync and async callables."""
    if inspect.iscoroutinefunction(callback):
        await callback(*args, **kwargs)
    else:
        await asyncio.to_thread(functools.partial(callback, *args, **kwargs))


def _invoke_sync(callback: Callable, *args: Any, **kwargs: Any) -> None:
    """Invoke callback from a sync thread, handling async callables."""
    if inspect.iscoroutinefunction(callback):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(callback(*args, **kwargs))
        finally:
            loop.close()
    else:
        callback(*args, **kwargs)


def _cleanup(timer_id: str) -> None:
    """Remove timer from registry."""
    with _timers_lock:
        _timers.pop(timer_id, None)


def _sync_timeout(
    timer_id: str, delay: float, callback: Callable, args: tuple, kwargs: dict
) -> None:
    """Execute a one-shot timer in sync context using threading.Timer."""

    def _run():
        _cleanup(timer_id)
        _invoke_sync(callback, *args, **kwargs)

    timer_thread = threading.Timer(delay, _run)
    timer_thread.daemon = True
    with _timers_lock:
        _timers[timer_id] = timer_thread
    timer_thread.start()


def _schedule_async_task(timer_id: str, coro: Any) -> None:
    """Create an async task for the coroutine and register it in _timers."""
    loop = asyncio.get_running_loop()
    task = loop.create_task(coro)
    with _timers_lock:
        _timers[timer_id] = task


def _sync_interval(
    timer_id: str,
    delay: float,
    callback: Callable,
    args: tuple,
    kwargs: dict,
    first_delay: float,
) -> None:
    """Execute a repeating timer in sync context using threading.Timer."""
    stop_event = threading.Event()

    def _run():
        stop_event.wait(first_delay)
        if not stop_event.is_set():
            _invoke_sync(callback, *args, **kwargs)
        while not stop_event.is_set():
            stop_event.wait(delay)
            if stop_event.is_set():
                break
            _invoke_sync(callback, *args, **kwargs)
        _cleanup(timer_id)

    with _timers_lock:
        _timers[timer_id] = stop_event
    interval_thread = threading.Thread(target=_run, daemon=True)
    interval_thread.start()


async def _async_timeout(
    timer_id: str, delay: float, callback: Callable, args: tuple, kwargs: dict
) -> None:
    """Execute a one-shot timer in async context."""
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
    """Execute a repeating timer in async context."""
    try:
        await asyncio.sleep(first_delay)
        await _invoke_async(callback, *args, **kwargs)
        while True:
            await asyncio.sleep(delay)
            await _invoke_async(callback, *args, **kwargs)
    finally:
        _cleanup(timer_id)


def set_timeout(delay: float, callback: Callable, *args: Any, **kwargs: Any) -> str:
    """Schedule a one-shot callback after delay seconds. Returns timer ID."""
    timer_id = get_uuid()

    if _is_async_context():
        _schedule_async_task(timer_id, _async_timeout(timer_id, delay, callback, args, kwargs))
    else:
        _sync_timeout(timer_id, delay, callback, args, kwargs)

    return timer_id


def set_interval(
    delay: float,
    callback: Callable,
    *args: Any,
    initial_delay: float | None = None,
    **kwargs: Any,
) -> str:
    """Schedule a repeating callback every delay seconds. Returns timer ID."""
    timer_id = get_uuid()
    first_delay = initial_delay if initial_delay is not None else delay

    if _is_async_context():
        _schedule_async_task(
            timer_id,
            _async_interval(timer_id, delay, callback, args, kwargs, first_delay),
        )
    else:
        _sync_interval(timer_id, delay, callback, args, kwargs, first_delay)

    return timer_id


def cancel_timer(timer_id: str) -> bool:
    """Cancel a timer by its ID. Returns True if found and cancelled."""
    with _timers_lock:
        handle = _timers.pop(timer_id, None)

    if handle is None:
        return False

    if isinstance(handle, (asyncio.Task, threading.Timer)):
        handle.cancel()
    elif isinstance(handle, threading.Event):
        handle.set()

    return True
