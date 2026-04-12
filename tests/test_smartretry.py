# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Tests for smartretry module."""

from unittest.mock import AsyncMock, patch

import pytest

from genro_toolbox.smartretry import RETRY_PRESETS, retry_call, smartretry

# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


class TestSmartretrySync:
    @patch("genro_toolbox.smartretry.time.sleep")
    def test_succeeds_without_retry(self, mock_sleep):
        @smartretry(max_attempts=3, on=(ValueError,))
        def ok():
            return 42

        assert ok() == 42
        mock_sleep.assert_not_called()

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_retries_on_matching_exception(self, mock_sleep):
        call_count = 0

        @smartretry(max_attempts=3, delay=1.0, on=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_raises_after_max_attempts(self, mock_sleep):
        @smartretry(max_attempts=3, delay=0.1, on=(ValueError,))
        def always_fail():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            always_fail()
        assert mock_sleep.call_count == 2

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_no_retry_on_non_matching_exception(self, mock_sleep):
        @smartretry(max_attempts=3, on=(ValueError,))
        def wrong_error():
            raise TypeError("wrong")

        with pytest.raises(TypeError, match="wrong"):
            wrong_error()
        mock_sleep.assert_not_called()

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_exponential_backoff_delays(self, mock_sleep):
        @smartretry(max_attempts=4, delay=1.0, backoff=2.0, jitter=False, on=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_jitter_adds_variance(self, mock_sleep):
        @smartretry(max_attempts=2, delay=1.0, jitter=True, on=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()

        actual_delay = mock_sleep.call_args_list[0].args[0]
        assert 1.0 <= actual_delay <= 1.1

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_no_jitter_when_disabled(self, mock_sleep):
        @smartretry(max_attempts=2, delay=1.0, jitter=False, on=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()

        assert mock_sleep.call_args_list[0].args[0] == 1.0

    def test_preserves_function_metadata(self):
        @smartretry(max_attempts=2, on=(ValueError,))
        def my_func():
            """My docstring."""

        assert my_func.__name__ == "my_func"
        assert my_func.__doc__ == "My docstring."


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


class TestSmartretryAsync:
    @pytest.mark.asyncio
    @patch("genro_toolbox.smartretry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_succeeds_without_retry(self, mock_sleep):
        @smartretry(max_attempts=3, on=(ValueError,))
        async def ok():
            return 42

        assert await ok() == 42
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    @patch("genro_toolbox.smartretry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_retries_on_matching_exception(self, mock_sleep):
        call_count = 0

        @smartretry(max_attempts=3, delay=1.0, on=(ValueError,))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        assert await flaky() == "ok"
        assert call_count == 3
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("genro_toolbox.smartretry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_raises_after_max_attempts(self, mock_sleep):
        @smartretry(max_attempts=3, delay=0.1, on=(ValueError,))
        async def always_fail():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await always_fail()
        assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    @patch("genro_toolbox.smartretry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_exponential_backoff(self, mock_sleep):
        @smartretry(max_attempts=4, delay=1.0, backoff=2.0, jitter=False, on=(ValueError,))
        async def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            await always_fail()

        delays = [call.args[0] for call in mock_sleep.call_args_list]
        assert delays == [1.0, 2.0, 4.0]


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------


class TestRetryPresets:
    def test_network_preset_values(self):
        p = RETRY_PRESETS["network"]
        assert p["max_attempts"] == 3
        assert p["delay"] == 1.0
        assert p["backoff"] == 2.0
        assert p["jitter"] is True
        assert p["on"] == (ConnectionError, TimeoutError, OSError)

    def test_aggressive_preset_values(self):
        p = RETRY_PRESETS["aggressive"]
        assert p["max_attempts"] == 5
        assert p["delay"] == 0.5
        assert p["on"] == (Exception,)

    def test_gentle_preset_values(self):
        p = RETRY_PRESETS["gentle"]
        assert p["max_attempts"] == 2
        assert p["delay"] == 2.0
        assert p["backoff"] == 1.5
        assert p["jitter"] is False

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_preset_with_decorator(self, mock_sleep):
        call_count = 0

        @smartretry(**RETRY_PRESETS["gentle"])
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("fail")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 2


# ---------------------------------------------------------------------------
# retry_call
# ---------------------------------------------------------------------------


class TestRetryCall:
    @patch("genro_toolbox.smartretry.time.sleep")
    def test_sync_call(self, mock_sleep):
        def add(a, b):
            return a + b

        result = retry_call(add, args=(2, 3))
        assert result == 5
        mock_sleep.assert_not_called()

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_sync_call_with_retries(self, mock_sleep):
        call_count = 0

        def flaky(x):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("fail")
            return x * 2

        result = retry_call(flaky, args=(5,), max_attempts=3, on=(ValueError,))
        assert result == 10
        assert call_count == 2

    @pytest.mark.asyncio
    @patch("genro_toolbox.smartretry.asyncio.sleep", new_callable=AsyncMock)
    async def test_async_call(self, mock_sleep):
        async def add(a, b):
            return a + b

        result = await retry_call(add, args=(2, 3))
        assert result == 5

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_policy_dict_overrides(self, mock_sleep):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"

        result = retry_call(
            flaky,
            policy={"max_attempts": 3, "delay": 0.5, "on": (ValueError,)},
        )
        assert result == "ok"
        assert call_count == 3

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_args_and_kwargs_passing(self, mock_sleep):
        def greet(name, greeting="hello"):
            return f"{greeting} {name}"

        result = retry_call(greet, args=("world",), kwargs={"greeting": "hi"})
        assert result == "hi world"


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    @patch("genro_toolbox.smartretry.time.sleep")
    def test_max_attempts_one(self, mock_sleep):
        @smartretry(max_attempts=1, on=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()
        mock_sleep.assert_not_called()

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_zero_delay(self, mock_sleep):
        @smartretry(max_attempts=2, delay=0.0, on=(ValueError,))
        def always_fail():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            always_fail()
        assert mock_sleep.call_count == 1
        assert mock_sleep.call_args_list[0].args[0] == 0.0

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_exception_subclass_matching(self, mock_sleep):
        call_count = 0

        @smartretry(max_attempts=3, on=(OSError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("subclass of OSError")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 2

    @patch("genro_toolbox.smartretry.time.sleep")
    def test_multiple_exception_types(self, mock_sleep):
        call_count = 0

        @smartretry(max_attempts=3, on=(ValueError, TypeError))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("v")
            if call_count == 2:
                raise TypeError("t")
            return "ok"

        assert flaky() == "ok"
        assert call_count == 3

    def test_decorator_without_parentheses_raises_type_error(self):
        with pytest.raises(TypeError, match="smartretry requires arguments"):

            @smartretry  # type: ignore[arg-type]
            def bad():
                pass
