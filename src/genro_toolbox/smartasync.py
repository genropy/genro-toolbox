# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartAsync - Unified sync/async API decorator.

Automatic context detection for methods that work in both sync and async contexts.

This module is also available as a standalone package: pip install smartasync
"""

import asyncio
import functools
import inspect
import threading


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
        """Get event loop for current thread, or None if in async context.

        Returns:
            None if an external event loop is running (async context),
            otherwise returns (creating if needed) a loop for this thread.
        """
        try:
            asyncio.get_running_loop()
            return None
        except RuntimeError:
            pass

        tid = threading.get_ident()
        loop = self._thread_loops.get(tid)
        if loop is None or loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._thread_loops[tid] = loop
        return loop

    @current_thread_loop.setter
    def current_thread_loop(self, value):
        """Set or remove the event loop for current thread.

        Args:
            value: EventLoop to set, or None to remove current thread's loop.
        """
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


def reset_smartasync_cache():
    """Clear all cached event loops.

    Call this in tests to ensure clean state.

    Example:
        from genro_toolbox import reset_smartasync_cache

        def test_something():
            reset_smartasync_cache()
            # test code...
    """
    _async_handler.reset()


def smartasync(method):
    """Bidirectional decorator for methods and functions that work in both sync and async contexts.

    Automatically detects whether the code is running in an async or sync
    context and adapts accordingly. Works in BOTH directions:
    - Async methods/functions called from sync context (uses asyncio.run)
    - Sync methods/functions called from async context (uses asyncio.to_thread)

    Features:
    - Auto-detection of sync/async context using asyncio.get_running_loop()
    - Asymmetric caching: caches True (async), always checks False (sync)
    - Enhanced error handling with clear messages
    - Works with both async and sync methods and standalone functions
    - No configuration needed - just apply the decorator
    - Prevents blocking event loop when calling sync methods from async context

    How it works:
    - At import time: Checks if method is async using asyncio.iscoroutinefunction()
    - At runtime: Detects if running in async context (checks for event loop)
    - Asymmetric cache: Once async context is detected (True), it's cached forever
    - Sync context (False) is never cached, always re-checked
    - This allows transitioning from sync -> async, but not async -> sync (which is correct)
    - Uses pattern matching to dispatch based on (has_loop, is_coroutine)

    Execution scenarios (async_context, async_method):
    - (False, True):  Sync context + Async method -> Execute with asyncio.run()
    - (False, False): Sync context + Sync method -> Direct call (pass-through)
    - (True, True):   Async context + Async method -> Return coroutine (for await)
    - (True, False):  Async context + Sync method -> Offload to thread (asyncio.to_thread)

    Args:
        method: Method or function to decorate (async or sync)

    Returns:
        Wrapped function that works in both sync and async contexts

    Example with class methods:
        class Manager:
            @smartasync
            async def async_configure(self, config: dict) -> None:
                # Async implementation uses await
                await self._async_setup(config)

            @smartasync
            def sync_process(self, data: str) -> str:
                # Sync implementation (e.g., CPU-bound or legacy code)
                return process_legacy(data)

        # Sync context usage
        manager = Manager()
        manager.async_configure({...})  # No await needed! Uses asyncio.run()
        result = manager.sync_process("data")  # Direct call

        # Async context usage
        async def main():
            manager = Manager()
            await manager.async_configure({...})  # Normal await
            result = await manager.sync_process("data")  # Offloaded to thread!

    Example with standalone functions:
        @smartasync
        async def fetch_data(url: str) -> dict:
            # Async function
            return await http_client.get(url)

        @smartasync
        def process_cpu_intensive(data: list) -> list:
            # Sync function (CPU-bound)
            return [expensive_computation(x) for x in data]

        # Sync context
        data = fetch_data("https://api.example.com")  # No await needed!
        result = process_cpu_intensive(data)

        # Async context
        async def main():
            data = await fetch_data("https://api.example.com")  # Normal await
            result = await process_cpu_intensive(data)  # Offloaded to thread!
    """
    # Import time: Detect if method is async
    is_coro = asyncio.iscoroutinefunction(method)

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        # Get loop for current thread (None if async context)
        loop = _async_handler.current_thread_loop
        async_context = loop is None
        async_method = is_coro

        # Dispatch based on (async_context, async_method) using pattern matching
        match (async_context, async_method):
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
    """Resolve nested awaitables recursively.

    Useful when calling methods that may be sync or async, or when
    awaitables return other awaitables (e.g., coroutine returning coroutine).

    Args:
        value: Either a value or an awaitable that returns a value

    Returns:
        The final resolved value (all awaitables unwrapped)

    Example:
        async def _do_load(self) -> Any:
            # self.load() might be sync or async depending on subclass
            result = await smartawait(self.load())
            return result

        # Also handles nested awaitables:
        async def get_loader():
            return load_data()  # returns another coroutine

        result = await smartawait(get_loader())  # resolves both levels
    """
    while inspect.isawaitable(value):
        value = await value
    return value


def smartcontinuation(value, on_resolved, *args, **kwargs):
    """Apply a callback to a value, handling both sync and async cases.

    If value is a coroutine, wraps it in a continuation that awaits the value
    and then calls on_resolved. Otherwise calls on_resolved directly.

    Args:
        value: Either a value or a coroutine
        on_resolved: Callback to apply to the resolved value
        *args: Additional positional arguments for on_resolved
        **kwargs: Additional keyword arguments for on_resolved

    Returns:
        If value is coroutine: a new coroutine that awaits and transforms
        If value is not coroutine: the direct result of on_resolved(value, ...)

    Example:
        def extract_key(data, key):
            return data[key]

        # Works with sync values
        result = smartcontinuation({"a": 1}, extract_key, "a")  # returns 1

        # Works with async values
        result = smartcontinuation(async_load(), extract_key, "a")  # returns coroutine
        value = await result  # returns the extracted key
    """
    if inspect.isawaitable(value):

        async def cont():
            resolved = await value
            return on_resolved(resolved, *args, **kwargs)

        return cont()
    return on_resolved(value, *args, **kwargs)


class SmartLock:
    """Async lock with Future sharing, created on-demand.

    Useful for classes that may or may not be used in async context.
    The lock and futures are only created when actually needed.

    Features:
        - Lock created lazily on first use
        - Future sharing: concurrent callers wait for same result
        - Automatic cleanup after completion

    Example:
        class CachedLoader:
            def __init__(self):
                self._lock = SmartLock()
                self._value = None
                self._loaded = False

            async def get_value(self):
                if self._loaded:
                    return self._value

                result = await self._lock.run_once(self._do_load)
                if result is not None:  # First caller returns value
                    self._value = result
                    self._loaded = True
                return self._value

            async def _do_load(self):
                # Expensive async operation
                return await fetch_data()
    """

    __slots__ = ("_lock", "_future")

    def __init__(self):
        """Initialize with no lock or future (created on-demand)."""
        self._lock = None
        self._future = None

    async def run_once(self, coro_func, *args, **kwargs):
        """Execute coroutine once, sharing result with concurrent callers.

        If another caller is already executing, waits for their result
        instead of running the coroutine again.

        Args:
            coro_func: Async function to execute
            *args: Positional arguments for coro_func
            **kwargs: Keyword arguments for coro_func

        Returns:
            Result from coro_func (either from this call or shared)

        Raises:
            Any exception raised by coro_func (propagated to all waiters)
        """
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
            loop = asyncio.get_event_loop()
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

        Clears any pending future. Use with caution - concurrent
        callers waiting on a future will receive an error.
        """
        self._future = None
