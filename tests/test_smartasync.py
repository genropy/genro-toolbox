# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Test @smartasync decorator."""

import asyncio

import pytest

from genro_toolbox.smartasync import smartasync


class SimpleManager:
    """Simple test class with smartasync methods."""

    def __init__(self):
        self.call_count = 0

    @smartasync
    async def async_method(self, value: str) -> str:
        """Async method decorated with @smartasync."""
        await asyncio.sleep(0.01)
        self.call_count += 1
        return f"Result: {value}"

    @smartasync
    def sync_method(self, value: str) -> str:
        """Sync method decorated with @smartasync (pass-through)."""
        self.call_count += 1
        return f"Sync: {value}"


class ManagerWithSlots:
    """Test class with __slots__."""

    __slots__ = ("data",)

    def __init__(self):
        self.data = []

    @smartasync
    async def add_item(self, item: str) -> None:
        """Add item to data."""
        await asyncio.sleep(0.01)
        self.data.append(item)

    @smartasync
    async def get_count(self) -> int:
        """Get data count."""
        await asyncio.sleep(0.01)
        return len(self.data)


class TestSmartasyncSyncContext:
    """Tests for smartasync in sync context."""

    def test_async_method_without_await(self):
        """Async method can be called without await in sync context."""
        obj = SimpleManager()
        result = obj.async_method("test")
        assert result == "Result: test"
        assert obj.call_count == 1

    def test_sync_method_direct_call(self):
        """Sync method works directly in sync context."""
        obj = SimpleManager()
        result = obj.sync_method("sync")
        assert result == "Sync: sync"
        assert obj.call_count == 1

    def test_slots_class_sync(self):
        """Works with __slots__ classes in sync context."""
        obj = ManagerWithSlots()
        obj.add_item("item1")
        obj.add_item("item2")
        count = obj.get_count()
        assert count == 2


class TestSmartasyncAsyncContext:
    """Tests for smartasync in async context."""

    @pytest.mark.asyncio
    async def test_async_method_with_await(self):
        """Async method works with await in async context."""
        obj = SimpleManager()
        result = await obj.async_method("async")
        assert result == "Result: async"
        assert obj.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_method_offloaded(self):
        """Sync method is offloaded to thread in async context."""
        obj = SimpleManager()
        result = await obj.sync_method("sync")
        assert result == "Sync: sync"
        assert obj.call_count == 1

    @pytest.mark.asyncio
    async def test_slots_class_async(self):
        """Works with __slots__ classes in async context."""
        obj = ManagerWithSlots()
        await obj.add_item("async1")
        await obj.add_item("async2")
        count = await obj.get_count()
        assert count == 2


class TestCacheReset:
    """Tests for cache reset functionality."""

    def test_cache_reset(self):
        """Cache can be reset for testing."""
        obj = SimpleManager()
        obj.async_method._smartasync_reset_cache()

        result = obj.async_method("test1")
        assert result == "Result: test1"

        obj.async_method._smartasync_reset_cache()

        result = obj.async_method("test2")
        assert result == "Result: test2"


class TestErrorPropagation:
    """Tests for error propagation."""

    def test_error_in_sync_context(self):
        """RuntimeError from user code propagates in sync context."""

        class BuggyManager:
            @smartasync
            async def buggy_method(self):
                await asyncio.sleep(0.01)
                raise RuntimeError("User error in async code")

        obj = BuggyManager()
        with pytest.raises(RuntimeError, match="User error in async code"):
            obj.buggy_method()

    @pytest.mark.asyncio
    async def test_error_in_async_context(self):
        """Error propagates in async context."""

        class BuggyManager:
            @smartasync
            async def buggy_method(self):
                await asyncio.sleep(0.01)
                raise ValueError("Async error")

        obj = BuggyManager()
        with pytest.raises(ValueError, match="Async error"):
            await obj.buggy_method()


class TestHelpfulErrorMessage:
    """Tests for helpful error messages."""

    def test_sync_call_from_async_context_error(self, monkeypatch):
        """Helpful error when asyncio.run() called from running loop."""
        obj = SimpleManager()
        obj.async_method._smartasync_reset_cache()

        def fake_asyncio_run(coro):
            try:
                coro.close()
            finally:
                raise RuntimeError(
                    "asyncio.run() cannot be called from a running event loop"
                )

        monkeypatch.setattr(asyncio, "run", fake_asyncio_run)

        with pytest.raises(RuntimeError) as excinfo:
            obj.async_method("boom")

        message = str(excinfo.value)
        assert "Cannot call async_method() synchronously" in message
        assert "Use 'await async_method()' instead" in message


class TestStandaloneFunctions:
    """Tests for standalone functions (not class methods)."""

    def test_standalone_async_function_sync(self):
        """Standalone async function works in sync context."""

        @smartasync
        async def process_data(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        result = process_data(5, 3)
        assert result == 8

    @pytest.mark.asyncio
    async def test_standalone_async_function_async(self):
        """Standalone async function works in async context."""

        @smartasync
        async def fetch_data(value: str) -> str:
            await asyncio.sleep(0.01)
            return f"fetched-{value}"

        result = await fetch_data("test")
        assert result == "fetched-test"

    @pytest.mark.asyncio
    async def test_standalone_sync_function_in_async(self):
        """Standalone sync function offloaded to thread in async context."""
        import time

        @smartasync
        def cpu_intensive(n: int) -> int:
            time.sleep(0.01)
            return n * n

        result = await cpu_intensive(7)
        assert result == 49

        # Multiple concurrent calls
        results = await asyncio.gather(
            cpu_intensive(2), cpu_intensive(3), cpu_intensive(4)
        )
        assert results == [4, 9, 16]


class TestBidirectional:
    """Tests for bidirectional sync/async scenarios."""

    @pytest.mark.asyncio
    async def test_async_app_calling_sync_library(self):
        """Async app can call sync legacy library (offloaded to thread)."""
        import time

        class LegacyLibrary:
            def __init__(self):
                self.processed = []

            @smartasync
            def blocking_operation(self, data: str) -> str:
                time.sleep(0.01)
                result = data.upper()
                self.processed.append(result)
                return result

        lib = LegacyLibrary()

        result = await lib.blocking_operation("legacy")
        assert result == "LEGACY"
        assert "LEGACY" in lib.processed

        # Multiple concurrent calls
        results = await asyncio.gather(
            lib.blocking_operation("item1"),
            lib.blocking_operation("item2"),
            lib.blocking_operation("item3"),
        )
        assert results == ["ITEM1", "ITEM2", "ITEM3"]
