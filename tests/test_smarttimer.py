# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

import asyncio

import pytest

from genro_toolbox import cancel_timer, set_interval, set_timeout

# --- Sync context tests: must raise RuntimeError ---


class TestSyncRaises:
    def test_set_timeout_raises_outside_async(self):
        with pytest.raises(RuntimeError, match="require a running async event loop"):
            set_timeout(0.05, lambda: None)

    def test_set_interval_raises_outside_async(self):
        with pytest.raises(RuntimeError, match="require a running async event loop"):
            set_interval(0.05, lambda: None)

    def test_cancel_nonexistent(self):
        assert cancel_timer("nonexistent_id") is False


# --- Async context tests ---


class TestAsyncTimeout:
    @pytest.mark.asyncio
    async def test_callback_fires(self):
        result = []

        async def cb(val):
            result.append(val)

        set_timeout(0.05, cb, "done")
        await asyncio.sleep(0.15)
        assert result == ["done"]

    @pytest.mark.asyncio
    async def test_sync_callback_in_async(self):
        result = []
        set_timeout(0.05, result.append, "sync_in_async")
        await asyncio.sleep(0.15)
        assert result == ["sync_in_async"]

    @pytest.mark.asyncio
    async def test_cancel_before_fire(self):
        result = []

        async def cb(val):
            result.append(val)

        tid = set_timeout(0.2, cb, "nope")
        cancelled = cancel_timer(tid)
        await asyncio.sleep(0.35)
        assert cancelled is True
        assert result == []

    @pytest.mark.asyncio
    async def test_callback_with_kwargs(self):
        result = {}

        async def store(key, value=None):
            result[key] = value

        set_timeout(0.05, store, "k", value=42)
        await asyncio.sleep(0.15)
        assert result == {"k": 42}

    @pytest.mark.asyncio
    async def test_returns_string_id(self):
        tid = set_timeout(10.0, lambda: None)
        assert isinstance(tid, str)
        assert len(tid) == 22
        cancel_timer(tid)


class TestAsyncInterval:
    @pytest.mark.asyncio
    async def test_fires_multiple_times(self):
        result = []

        async def cb(val):
            result.append(val)

        tid = set_interval(0.05, cb, "tick")
        await asyncio.sleep(0.3)
        cancel_timer(tid)
        assert len(result) >= 3

    @pytest.mark.asyncio
    async def test_cancel_stops_firing(self):
        result = []

        async def cb(val):
            result.append(val)

        tid = set_interval(0.05, cb, "tick")
        await asyncio.sleep(0.15)
        cancel_timer(tid)
        count_at_cancel = len(result)
        await asyncio.sleep(0.15)
        assert len(result) == count_at_cancel

    @pytest.mark.asyncio
    async def test_sync_callback_in_async_interval(self):
        result = []
        tid = set_interval(0.05, result.append, "tick")
        await asyncio.sleep(0.2)
        cancel_timer(tid)
        assert len(result) >= 2


class TestInitialDelay:
    @pytest.mark.asyncio
    async def test_initial_delay_shorter(self):
        result = []

        async def cb(val):
            result.append(val)

        tid = set_interval(0.2, cb, "tick", initial_delay=0.05)
        await asyncio.sleep(0.15)
        cancel_timer(tid)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_initial_delay_default(self):
        result = []

        async def cb(val):
            result.append(val)

        tid = set_interval(0.1, cb, "tick")
        await asyncio.sleep(0.05)
        assert len(result) == 0
        await asyncio.sleep(0.15)
        cancel_timer(tid)
        assert len(result) >= 1


class TestTimerIsolation:
    @pytest.mark.asyncio
    async def test_multiple_async_timers_independent(self):
        r1, r2 = [], []

        async def cb(lst, val):
            lst.append(val)

        t1 = set_timeout(0.05, cb, r1, "a")
        set_timeout(0.05, cb, r2, "b")
        cancel_timer(t1)
        await asyncio.sleep(0.15)
        assert r1 == []
        assert r2 == ["b"]
