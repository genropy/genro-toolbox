# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartAsync - Unified sync/async API decorator.

Automatic context detection for methods that work in both sync and async contexts.

This module is also available as a standalone package: pip install smartasync
"""

import asyncio
import functools


def reset_smartasync_cache(func):
    """Reset cache for a @smartasync decorated function.

    Call this in tests to ensure clean state for async context detection.

    Args:
        func: A function decorated with @smartasync

    Example:
        from genro_toolbox import reset_smartasync_cache

        def test_something():
            obj = MyClass()
            reset_smartasync_cache(obj.async_method)
            # test code...
    """
    if hasattr(func, "_smartasync_reset_cache"):
        func._smartasync_reset_cache()


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

    # Asymmetric cache: only cache True (async context found)
    _cached_has_loop = False

    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        nonlocal _cached_has_loop

        # Context detection with asymmetric caching
        if _cached_has_loop:
            async_context = True
        else:
            try:
                asyncio.get_running_loop()
                # Found event loop! Cache it forever
                async_context = True
                _cached_has_loop = True
            except RuntimeError:
                # No event loop - sync context
                # Don't cache False, always re-check next time
                async_context = False

        async_method = is_coro

        # Dispatch based on (async_context, async_method) using pattern matching
        match (async_context, async_method):
            case (False, True):
                # Sync context + Async method -> Run with asyncio.run()
                coro = method(*args, **kwargs)
                try:
                    return asyncio.run(coro)
                except RuntimeError as e:
                    if "cannot be called from a running event loop" in str(e):
                        raise RuntimeError(
                            f"Cannot call {method.__name__}() synchronously from within "
                            f"an async context. Use 'await {method.__name__}()' instead."
                        ) from e
                    raise

            case (False, False):
                # Sync context + Sync method -> Direct call (pass-through)
                return method(*args, **kwargs)

            case (True, True):
                # Async context + Async method -> Return coroutine to be awaited
                return method(*args, **kwargs)

            case (True, False):
                # Async context + Sync method -> Offload to thread (don't block event loop)
                return asyncio.to_thread(method, *args, **kwargs)

    # Add cache reset method for testing
    def reset_cache():
        nonlocal _cached_has_loop
        _cached_has_loop = False

    wrapper._smartasync_reset_cache = reset_cache

    return wrapper


async def smartawait(result):
    """Await result if it's a coroutine, otherwise return as-is.

    Useful when calling methods that may be sync or async (e.g., overridden
    methods in subclasses where the base class doesn't know if the override
    is async or not).

    Args:
        result: Either a value or a coroutine that returns a value

    Returns:
        The value (awaited if coroutine, direct otherwise)

    Example:
        async def _do_load(self) -> Any:
            # self.load() might be sync or async depending on subclass
            result = await smartawait(self.load())
            return result
    """
    if asyncio.iscoroutine(result):
        return await result
    return result


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
