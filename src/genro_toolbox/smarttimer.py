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
from typing import Any, Callable

from .uid import get_uuid

_timers: dict[str, Any] = {}
_timers_lock = threading.Lock()


def _is_async_context() -> bool:
    """Return True if a running event loop exists."""
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


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


def _sync_timeout(timer_id: str, delay: float, callback: Callable,
                  args: tuple, kwargs: dict) -> None:
    """Execute a one-shot timer in sync context using threading.Timer."""

    def _run():
        _cleanup(timer_id)
        _invoke_sync(callback, *args, **kwargs)

    t = threading.Timer(delay, _run)
    t.daemon = True
    with _timers_lock:
        _timers[timer_id] = t
    t.start()


def _sync_interval(timer_id: str, delay: float, callback: Callable,
                   args: tuple, kwargs: dict) -> None:
    """Execute a repeating timer in sync context using threading.Timer."""
    stop_event = threading.Event()

    def _run():
        while not stop_event.is_set():
            stop_event.wait(delay)
            if stop_event.is_set():
                break
            _invoke_sync(callback, *args, **kwargs)
        _cleanup(timer_id)

    with _timers_lock:
        _timers[timer_id] = stop_event
    t = threading.Thread(target=_run, daemon=True)
    t.start()


async def _async_timeout(timer_id: str, delay: float, callback: Callable,
                         args: tuple, kwargs: dict) -> None:
    """Execute a one-shot timer in async context."""
    try:
        await asyncio.sleep(delay)
        await _invoke_async(callback, *args, **kwargs)
    except asyncio.CancelledError:
        pass
    finally:
        _cleanup(timer_id)


async def _async_interval(timer_id: str, delay: float, callback: Callable,
                          args: tuple, kwargs: dict) -> None:
    """Execute a repeating timer in async context."""
    try:
        while True:
            await asyncio.sleep(delay)
            await _invoke_async(callback, *args, **kwargs)
    except asyncio.CancelledError:
        pass
    finally:
        _cleanup(timer_id)


def set_timeout(delay: float, callback: Callable,
                *args: Any, **kwargs: Any) -> str:
    """Schedule a one-shot callback after delay seconds.

    Args:
        delay: Seconds to wait before executing callback.
        callback: Function to call (sync or async).
        *args: Positional arguments for callback.
        **kwargs: Keyword arguments for callback.

    Returns:
        Timer ID string for cancellation.
    """
    timer_id = get_uuid()

    if _is_async_context():
        loop = asyncio.get_running_loop()
        task = loop.create_task(_async_timeout(timer_id, delay, callback,
                                               args, kwargs))
        with _timers_lock:
            _timers[timer_id] = task
    else:
        _sync_timeout(timer_id, delay, callback, args, kwargs)

    return timer_id


def set_interval(delay: float, callback: Callable,
                 *args: Any, **kwargs: Any) -> str:
    """Schedule a repeating callback every delay seconds.

    Args:
        delay: Seconds between each callback execution.
        callback: Function to call (sync or async).
        *args: Positional arguments for callback.
        **kwargs: Keyword arguments for callback.

    Returns:
        Timer ID string for cancellation.
    """
    timer_id = get_uuid()

    if _is_async_context():
        loop = asyncio.get_running_loop()
        task = loop.create_task(_async_interval(timer_id, delay, callback,
                                                args, kwargs))
        with _timers_lock:
            _timers[timer_id] = task
    else:
        _sync_interval(timer_id, delay, callback, args, kwargs)

    return timer_id


def cancel_timer(timer_id: str) -> bool:
    """Cancel a timer by its ID.

    Args:
        timer_id: The ID returned by set_timeout or set_interval.

    Returns:
        True if the timer was found and cancelled, False otherwise.
    """
    with _timers_lock:
        handle = _timers.pop(timer_id, None)

    if handle is None:
        return False

    if isinstance(handle, asyncio.Task):
        handle.cancel()
    elif isinstance(handle, threading.Timer):
        handle.cancel()
    elif isinstance(handle, threading.Event):
        handle.set()

    return True
