# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartAsync - Unified sync/async API decorator.

Automatic context detection for methods that work in both sync and async contexts.

This module is also available as a standalone package: pip install smartasync

Design Context:
    This module is optimized for environments with pre-assigned thread workers
    (e.g., Gunicorn with sync workers, Django, Flask). In these contexts, threads
    are long-lived and reused across requests, so the per-thread loop pool provides
    efficient event loop reuse without creation overhead.

Caveats - Nested Mixed Calls:
    When async code offloads sync code to a thread (via to_thread), and that sync
    code calls async functions, those async functions MUST be decorated with
    @smartasync to work correctly. Without the decorator, the sync code receives
    a raw coroutine object it cannot use.

    Problematic chain:
        async A() -> sync B() [in thread] -> async C() [NO decorator] = BROKEN

    Safe chain:
        async A() -> sync B() [in thread] -> async C() [@smartasync] = WORKS

    Best practice: Apply @smartasync only at the "leaf" level - the outermost
    boundary where sync code calls async code. Avoid deep nesting of mixed calls.

Inline Usage:
    smartasync can be used inline without the decorator syntax, useful for
    wrapping third-party async functions or one-off calls:

        # Wrap and call in one line
        result = smartasync(some_async_func)(arg1, arg2)

        # Or wrap once, call multiple times
        wrapped = smartasync(third_party_async_func)
        result1 = wrapped(args1)
        result2 = wrapped(args2)
"""

import asyncio
import contextvars
import functools
import threading

from .typeutils import is_awaitable

_async_mode: contextvars.ContextVar[bool | None] = contextvars.ContextVar(
    "genro_async_mode", default=None
)


def set_sync(active: bool = True) -> None:
    """Force sync mode. Overrides auto-detection of async context.

    Call set_sync(False) to cancel override and return to auto-detect.
    """
    _async_mode.set(False if active else None)


def set_async(active: bool = True) -> None:
    """Force async mode. Overrides auto-detection of async context.

    Call set_async(False) to cancel override and return to auto-detect.
    """
    _async_mode.set(True if active else None)


class AsyncHandler:
    """Manages per-thread event loops for sync context execution.

    Provides a single point of access to determine async/sync context
    and manage event loops for each thread.

    The current_thread_loop property returns:
    - None: if running in async context (external loop exists)
    - EventLoop: if running in sync context (creates/reuses per-thread loop)
    """

    def __init__(self):
        self._thread_loops: dict[int, asyncio.AbstractEventLoop] = {}
        self._reset_lock = threading.Lock()

    @property
    def current_thread_loop(self) -> asyncio.AbstractEventLoop | None:
        """Get event loop for current thread, or None if in async context."""
        if is_async_context():
            return None

        tid = threading.get_ident()
        loop = self._thread_loops.get(tid)
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._thread_loops[tid] = loop
        return loop

    @current_thread_loop.setter
    def current_thread_loop(self, value):
        """Set or remove the event loop for current thread (None to remove)."""
        tid = threading.get_ident()
        if value is None:
            self._thread_loops.pop(tid, None)
        else:
            self._thread_loops[tid] = value

    def reset(self):
        """Clear all cached event loops. Thread-safe.

        Closes all loops before clearing. Use only in tests when no
        other threads are actively using smartasync.
        """
        with self._reset_lock:
            for loop in self._thread_loops.values():
                if not loop.is_closed():
                    loop.close()
            self._thread_loops.clear()


# Module-level singleton
_async_handler = AsyncHandler()


def is_async_context() -> bool:
    """Return True if running in async context. Respects set_sync/set_async override."""
    mode = _async_mode.get()
    if mode is not None:
        return mode
    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def reset_smartasync_cache():
    """Clear all cached event loops. Call in tests to ensure clean state."""
    _async_handler.reset()


def smartasync(method):
    """Decorator that adapts sync/async functions to work in both contexts.

    Dispatches based on (async_context, is_coroutine):
    sync+async→run_until_complete, sync+sync→passthrough,
    async+async→return coroutine, async+sync→to_thread.
    """
    # Import time: Detect if method is async
    is_coro = asyncio.iscoroutinefunction(method)

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        # Get loop for current thread (None if async context)
        loop = _async_handler.current_thread_loop
        async_context = loop is None

        # Dispatch based on (async_context, is_coro) using pattern matching
        match (async_context, is_coro):
            case (False, True):
                # Sync context + Async method -> Run with per-thread loop
                coro = method(*args, **kwargs)
                return loop.run_until_complete(coro)

            case (False, False):
                # Sync context + Sync method -> Direct call (pass-through)
                return method(*args, **kwargs)

            case (True, True):
                # Async context + Async method -> Return coroutine to be awaited
                return method(*args, **kwargs)

            case (True, False):
                # Async context + Sync method -> Offload to thread (don't block event loop)
                return asyncio.to_thread(method, *args, **kwargs)

    return wrapper


async def smartawait(value):
    """Await a value recursively until it is no longer awaitable."""
    while is_awaitable(value):
        value = await value
    return value


def smartcontinuation(value, on_resolved, *args, **kwargs):
    """Apply on_resolved to value, wrapping in a continuation if value is awaitable."""
    if is_awaitable(value):

        async def cont():
            resolved = await value
            return on_resolved(resolved, *args, **kwargs)

        return cont()
    return on_resolved(value, *args, **kwargs)


class SmartLock:
    """Async lock with lazy creation and Future sharing for concurrent callers."""

    __slots__ = ("_lock", "_future")

    def __init__(self):
        """Initialize with no lock or future (created on-demand)."""
        self._lock = None
        self._future = None

    async def run_once(self, coro_func, *args, **kwargs):
        """Execute coro_func once, sharing the result with concurrent callers via a Future."""
        # Fast path: if Future exists, another call is in progress
        if self._future is not None:
            return await self._future

        # Create lock on first use
        if self._lock is None:
            self._lock = asyncio.Lock()

        async with self._lock:
            # Double-check after acquiring lock
            if self._future is not None:
                return await self._future

            # Create Future for other callers to await
            loop = asyncio.get_running_loop()
            self._future = loop.create_future()

            try:
                result = await coro_func(*args, **kwargs)
                self._future.set_result(result)
                return result
            except Exception as e:
                self._future.set_exception(e)
                raise
            finally:
                self._future = None

    def reset(self):
        """Reset the lock state.

        Cancels any pending future, causing waiters to receive CancelledError.
        """
        if self._future is not None and not self._future.done():
            self._future.cancel()
        self._future = None
