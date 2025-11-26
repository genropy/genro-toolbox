"""Tests for dict utility helpers."""

import pytest
from genro_toolbox import SmartOptions
from genro_toolbox.dict_utils import filtered_dict, make_opts


class TestFilteredDict:
    """Tests for filtered_dict helper."""

    def test_returns_copy_when_no_filter(self):
        source = {"a": 1, "b": 2}
        result = filtered_dict(source)
        assert result == source
        assert result is not source

    def test_filters_none_values(self):
        source = {"a": 1, "b": None, "c": 3}
        result = filtered_dict(source, lambda key, value: value is not None)
        assert result == {"a": 1, "c": 3}

    def test_handles_none_source(self):
        assert filtered_dict(None) == {}


class TestMakeOpts:
    """Tests for make_opts helper."""

    def test_merges_defaults_and_incoming(self):
        opts = make_opts({"timeout": 10}, {"timeout": 5, "retries": 3})
        assert opts.timeout == 10
        assert opts.retries == 3

    def test_respects_filter_function(self):
        opts = make_opts(
            {"timeout": None, "retries": 5},
            {"timeout": 2, "retries": 1},
            filter_fn=lambda _, value: value is not None,
        )
        assert opts.timeout == 2  # None filtered, default preserved
        assert opts.retries == 5

    def test_ignore_none_flag(self):
        opts = make_opts(
            {"timeout": None},
            {"timeout": 15},
            ignore_none=True,
        )
        assert opts.timeout == 15

    def test_ignore_empty_flag(self):
        opts = make_opts(
            {"tag": "", "labels": []},
            {"tag": "default", "labels": ["x"]},
            ignore_empty=True,
        )
        assert opts.tag == "default"
        assert opts.labels == ["x"]

    def test_accepts_missing_mappings(self):
        opts = make_opts(None, None)
        assert vars(opts) == {}


class TestSmartOptions:
    """Tests for SmartOptions helper class."""

    def test_basic_merge(self):
        opts = SmartOptions({"timeout": 5}, {"timeout": 1, "retries": 3})
        assert opts.timeout == 5
        assert opts.retries == 3

    def test_ignore_flags(self):
        opts = SmartOptions(
            {"timeout": None, "tags": []},
            {"timeout": 10, "tags": ["default"]},
            ignore_none=True,
            ignore_empty=True,
        )
        assert opts.timeout == 10
        assert opts.tags == ["default"]

    def test_as_dict_returns_copy(self):
        opts = SmartOptions({"timeout": 2}, {})
        result = opts.as_dict()
        assert result == {"timeout": 2}
        result["timeout"] = 99
        assert opts.timeout == 2  # original not mutated

    def test_attribute_updates_are_tracked(self):
        opts = SmartOptions({"timeout": 2}, {})
        opts.timeout = 7
        assert opts.as_dict()["timeout"] == 7
        opts.new_flag = True
        assert opts.as_dict()["new_flag"] is True
        del opts.timeout
        assert "timeout" not in opts.as_dict()

    def test_setting_data_attribute(self):
        """Test that setting _data attribute works correctly."""
        opts = SmartOptions({"x": 1}, {})

        # This should work without issues
        opts._data = {"y": 2}

        # Verify it was set
        assert hasattr(opts, "_data")
        assert opts._data == {"y": 2}

    def test_deleting_data_attribute_raises_error(self):
        """Test that deleting _data attribute raises AttributeError."""
        opts = SmartOptions({"x": 1}, {})

        # Attempting to delete _data should raise AttributeError
        with pytest.raises(AttributeError, match="_data attribute cannot be removed"):
            del opts._data

    def test_is_empty_with_non_sequence(self):
        """Test _is_empty helper with non-sequence values."""
        # Test with None value (should not be filtered as empty)
        opts = make_opts({"x": None}, {}, ignore_empty=True)
        assert hasattr(opts, "x")  # None is not considered empty
        assert opts.x is None

        # Test with numeric value (should not be filtered)
        opts = make_opts({"x": 0}, {}, ignore_empty=True)
        assert hasattr(opts, "x")  # 0 is not considered empty
        assert opts.x == 0
