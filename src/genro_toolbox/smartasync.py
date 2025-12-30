# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""SmartAsync - Unified sync/async API decorator.

Automatic context detection for methods that work in both sync and async contexts.

This module is also available as a standalone package: pip install smartasync
"""

import asyncio
import functools


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
