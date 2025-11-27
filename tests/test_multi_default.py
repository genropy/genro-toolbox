# Copyright 2025 Softwell S.r.l.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for multi_default module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from genro_toolbox.multi_default import (
    MultiDefault,
    auto_convert,
    flatten_dict,
    load_env,
    load_file,
    load_ini,
    load_json,
)

if TYPE_CHECKING:
    from collections.abc import Generator


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_ini_file(tmp_path: Path) -> Path:
    """Create a temporary .ini file for testing."""
    content = """\
[server]
host = localhost
port = 8000
debug = true

[logging]
level = INFO
file = /var/log/app.log
"""
    file_path = tmp_path / "config.ini"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """Create a temporary .json file for testing."""
    data = {
        "server": {"host": "localhost", "port": 8000, "debug": True},
        "logging": {"level": "INFO"},
    }
    file_path = tmp_path / "config.json"
    file_path.write_text(json.dumps(data))
    return file_path


@pytest.fixture
def env_vars() -> Generator[None, None, None]:
    """Set up and tear down environment variables for testing."""
    # Save original values
    original: dict[str, str | None] = {}
    test_vars = {
        "TESTAPP_SERVER_HOST": "envhost",
        "TESTAPP_SERVER_PORT": "9000",
        "TESTAPP_DEBUG": "true",
        "TESTAPP_TIMEOUT": "30.5",
        "TESTAPP_EMPTY": "",
        "OTHER_VAR": "ignored",
    }

    for key in test_vars:
        original[key] = os.environ.get(key)

    # Set test values
    for key, value in test_vars.items():
        os.environ[key] = value

    yield

    # Restore original values
    for key, orig_value in original.items():
        if orig_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = orig_value


# =============================================================================
# Tests: auto_convert
# =============================================================================


class TestAutoConvert:
    """Tests for auto_convert function."""

    def test_integer_positive(self) -> None:
        """Convert positive integer string."""
        assert auto_convert("123") == 123
        assert isinstance(auto_convert("123"), int)

    def test_integer_negative(self) -> None:
        """Convert negative integer string."""
        assert auto_convert("-456") == -456
        assert isinstance(auto_convert("-456"), int)

    def test_integer_zero(self) -> None:
        """Convert zero."""
        assert auto_convert("0") == 0
        assert isinstance(auto_convert("0"), int)

    def test_float_positive(self) -> None:
        """Convert positive float string."""
        assert auto_convert("12.5") == 12.5
        assert isinstance(auto_convert("12.5"), float)

    def test_float_negative(self) -> None:
        """Convert negative float string."""
        assert auto_convert("-3.14") == -3.14
        assert isinstance(auto_convert("-3.14"), float)

    def test_float_leading_dot(self) -> None:
        """Float with leading dot."""
        assert auto_convert(".5") == 0.5

    def test_float_trailing_dot(self) -> None:
        """Float with trailing dot."""
        assert auto_convert("5.") == 5.0

    def test_bool_true_variants(self) -> None:
        """Convert various true values to True."""
        for value in ["true", "True", "TRUE", "yes", "Yes", "on", "ON", "1"]:
            assert auto_convert(value) is True, f"Failed for {value!r}"

    def test_bool_false_variants(self) -> None:
        """Convert various false values to False."""
        for value in ["false", "False", "FALSE", "no", "No", "off", "OFF", "0"]:
            assert auto_convert(value) is False, f"Failed for {value!r}"

    def test_none_variants(self) -> None:
        """Convert none/null to None."""
        for value in ["none", "None", "NONE", "null", "Null", "NULL", ""]:
            assert auto_convert(value) is None, f"Failed for {value!r}"

    def test_string_unchanged(self) -> None:
        """Regular strings remain unchanged."""
        assert auto_convert("hello") == "hello"
        assert auto_convert("localhost") == "localhost"
        assert auto_convert("/path/to/file") == "/path/to/file"

    def test_whitespace_handling(self) -> None:
        """Whitespace is stripped before conversion."""
        assert auto_convert("  123  ") == 123
        assert auto_convert("  true  ") is True

    def test_non_string_passthrough(self) -> None:
        """Non-string values pass through unchanged."""
        assert auto_convert(123) == 123  # type: ignore[arg-type]
        assert auto_convert(True) is True  # type: ignore[arg-type]
        assert auto_convert(None) is None  # type: ignore[arg-type]


# =============================================================================
# Tests: flatten_dict
# =============================================================================


class TestFlattenDict:
    """Tests for flatten_dict function."""

    def test_already_flat(self) -> None:
        """Flat dict remains unchanged."""
        data = {"host": "localhost", "port": 8000}
        assert flatten_dict(data) == data

    def test_single_level_nesting(self) -> None:
        """Single level of nesting is flattened."""
        data = {"server": {"host": "localhost", "port": 8000}}
        expected = {"server_host": "localhost", "server_port": 8000}
        assert flatten_dict(data) == expected

    def test_multiple_sections(self) -> None:
        """Multiple sections are flattened correctly."""
        data = {
            "server": {"host": "localhost"},
            "logging": {"level": "INFO"},
        }
        expected = {"server_host": "localhost", "logging_level": "INFO"}
        assert flatten_dict(data) == expected

    def test_deep_nesting(self) -> None:
        """Deep nesting is flattened."""
        data = {"a": {"b": {"c": 1}}}
        expected = {"a_b_c": 1}
        assert flatten_dict(data) == expected

    def test_mixed_flat_and_nested(self) -> None:
        """Mix of flat and nested keys."""
        data = {"debug": True, "server": {"host": "localhost"}}
        expected = {"debug": True, "server_host": "localhost"}
        assert flatten_dict(data) == expected

    def test_custom_separator(self) -> None:
        """Custom separator is used."""
        data = {"server": {"host": "localhost"}}
        expected = {"server.host": "localhost"}
        assert flatten_dict(data, separator=".") == expected

    def test_empty_dict(self) -> None:
        """Empty dict returns empty dict."""
        assert flatten_dict({}) == {}

    def test_empty_nested_dict(self) -> None:
        """Empty nested dict produces no keys."""
        data = {"server": {}}
        assert flatten_dict(data) == {}


# =============================================================================
# Tests: load_ini
# =============================================================================


class TestLoadIni:
    """Tests for load_ini function."""

    def test_load_basic(self, temp_ini_file: Path) -> None:
        """Load basic .ini file."""
        result = load_ini(temp_ini_file)

        assert "server" in result
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 8000  # auto-converted to int
        assert result["server"]["debug"] is True  # auto-converted to bool

        assert "logging" in result
        assert result["logging"]["level"] == "INFO"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_ini(tmp_path / "nonexistent.ini")

    def test_accepts_string_path(self, temp_ini_file: Path) -> None:
        """Accept string path."""
        result = load_ini(str(temp_ini_file))
        assert "server" in result


# =============================================================================
# Tests: load_json
# =============================================================================


class TestLoadJson:
    """Tests for load_json function."""

    def test_load_basic(self, temp_json_file: Path) -> None:
        """Load basic .json file."""
        result = load_json(temp_json_file)

        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 8000
        assert result["server"]["debug"] is True
        assert result["logging"]["level"] == "INFO"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json")


# =============================================================================
# Tests: load_file (auto-detect)
# =============================================================================


class TestLoadFile:
    """Tests for load_file function."""

    def test_auto_detect_ini(self, temp_ini_file: Path) -> None:
        """Auto-detect .ini format."""
        result = load_file(temp_ini_file)
        assert "server" in result

    def test_auto_detect_json(self, temp_json_file: Path) -> None:
        """Auto-detect .json format."""
        result = load_file(temp_json_file)
        assert "server" in result

    def test_unsupported_format(self, tmp_path: Path) -> None:
        """Raise ValueError for unsupported format."""
        file_path = tmp_path / "config.xyz"
        file_path.write_text("content")

        with pytest.raises(ValueError, match="Unsupported config file format"):
            load_file(file_path)


# =============================================================================
# Tests: load_env
# =============================================================================


class TestLoadEnv:
    """Tests for load_env function."""

    def test_load_with_prefix(self, env_vars: None) -> None:
        """Load env vars with prefix."""
        result = load_env("TESTAPP")

        assert result["server_host"] == "envhost"
        assert result["server_port"] == 9000  # auto-converted
        assert result["debug"] is True  # auto-converted
        assert result["timeout"] == 30.5  # auto-converted
        assert result["empty"] is None  # empty string → None

    def test_prefix_not_matched(self, env_vars: None) -> None:
        """Vars without prefix are ignored."""
        result = load_env("TESTAPP")
        # OTHER_VAR should not be included
        assert "other_var" not in result
        assert "var" not in result

    def test_no_matching_vars(self) -> None:
        """No matching vars returns empty dict."""
        result = load_env("NONEXISTENT_PREFIX_XYZ")
        assert result == {}

    def test_keys_are_lowercase(self, env_vars: None) -> None:
        """Keys are lowercased."""
        result = load_env("TESTAPP")
        # All keys should be lowercase
        assert all(k == k.lower() for k in result.keys())


# =============================================================================
# Tests: MultiDefault
# =============================================================================


class TestMultiDefault:
    """Tests for MultiDefault class."""

    def test_single_dict_source(self) -> None:
        """Single dict source."""
        defaults = MultiDefault({"host": "localhost", "port": 8000})
        assert defaults["host"] == "localhost"
        assert defaults["port"] == 8000

    def test_single_dict_nested_is_flattened(self) -> None:
        """Nested dict is flattened."""
        defaults = MultiDefault({"server": {"host": "localhost"}})
        assert defaults["server_host"] == "localhost"
        assert "server" not in defaults

    def test_single_file_source(self, temp_ini_file: Path) -> None:
        """Single file source."""
        defaults = MultiDefault(str(temp_ini_file))
        assert defaults["server_host"] == "localhost"
        assert defaults["server_port"] == 8000

    def test_single_env_source(self, env_vars: None) -> None:
        """Single env source."""
        defaults = MultiDefault("ENV:TESTAPP")
        assert defaults["server_host"] == "envhost"
        assert defaults["server_port"] == 9000

    def test_priority_later_overrides_earlier(self, temp_ini_file: Path) -> None:
        """Later sources override earlier ones."""
        defaults = MultiDefault(
            {"server_host": "original", "server_port": 1111},
            str(temp_ini_file),  # has server.host=localhost, server.port=8000
        )
        assert defaults["server_host"] == "localhost"  # overridden by file
        assert defaults["server_port"] == 8000  # overridden by file

    def test_priority_env_overrides_file(
        self, temp_ini_file: Path, env_vars: None
    ) -> None:
        """Env vars override file values."""
        defaults = MultiDefault(
            str(temp_ini_file),  # server.host=localhost
            "ENV:TESTAPP",  # server_host=envhost
        )
        assert defaults["server_host"] == "envhost"  # env wins

    def test_multiple_sources_full_chain(
        self, temp_ini_file: Path, env_vars: None
    ) -> None:
        """Full chain: dict < file < env."""
        defaults = MultiDefault(
            {"server_host": "default", "custom_key": "from_dict"},
            str(temp_ini_file),
            "ENV:TESTAPP",
        )
        assert defaults["server_host"] == "envhost"  # from env
        assert defaults["logging_level"] == "INFO"  # from file (not in env)
        assert defaults["custom_key"] == "from_dict"  # only in dict

    def test_skip_missing_false_raises(self, tmp_path: Path) -> None:
        """Missing file raises error when skip_missing=False."""
        defaults = MultiDefault(
            str(tmp_path / "nonexistent.ini"),
            skip_missing=False,
        )
        with pytest.raises(FileNotFoundError):
            defaults.resolve()

    def test_skip_missing_true_skips(self, tmp_path: Path) -> None:
        """Missing file is skipped when skip_missing=True."""
        defaults = MultiDefault(
            {"host": "localhost"},
            str(tmp_path / "nonexistent.ini"),
            skip_missing=True,
        )
        # Should not raise, and dict values should be present
        assert defaults["host"] == "localhost"

    def test_lazy_resolution(self) -> None:
        """Resolution is lazy (only when accessed)."""
        defaults = MultiDefault({"host": "localhost"})
        # _resolved should be None before access
        assert defaults._resolved is None
        # Access triggers resolution
        _ = defaults["host"]
        assert defaults._resolved is not None

    def test_cached_resolution(self) -> None:
        """Resolution is cached."""
        defaults = MultiDefault({"host": "localhost"})
        result1 = defaults.resolve()
        result2 = defaults.resolve()
        assert result1 is result2  # Same object

    def test_mapping_protocol_iter(self) -> None:
        """Mapping protocol: __iter__."""
        defaults = MultiDefault({"a": 1, "b": 2})
        assert set(defaults) == {"a", "b"}

    def test_mapping_protocol_len(self) -> None:
        """Mapping protocol: __len__."""
        defaults = MultiDefault({"a": 1, "b": 2, "c": 3})
        assert len(defaults) == 3

    def test_mapping_protocol_keys(self) -> None:
        """Mapping protocol: keys()."""
        defaults = MultiDefault({"a": 1, "b": 2})
        assert set(defaults.keys()) == {"a", "b"}

    def test_mapping_protocol_values(self) -> None:
        """Mapping protocol: values()."""
        defaults = MultiDefault({"a": 1, "b": 2})
        assert set(defaults.values()) == {1, 2}

    def test_mapping_protocol_items(self) -> None:
        """Mapping protocol: items()."""
        defaults = MultiDefault({"a": 1, "b": 2})
        assert set(defaults.items()) == {("a", 1), ("b", 2)}

    def test_repr(self) -> None:
        """String representation."""
        defaults = MultiDefault({"a": 1}, "config.ini", skip_missing=True)
        repr_str = repr(defaults)
        assert "MultiDefault" in repr_str
        assert "{'a': 1}" in repr_str
        assert "'config.ini'" in repr_str
        assert "skip_missing=True" in repr_str

    def test_unsupported_source_type(self) -> None:
        """Raise ValueError for unsupported source type."""
        defaults = MultiDefault(12345)  # int is not a valid source
        with pytest.raises(ValueError, match="Unsupported source type"):
            defaults.resolve()

    def test_path_object_source(self, temp_ini_file: Path) -> None:
        """Path object is accepted as source."""
        defaults = MultiDefault(temp_ini_file)  # Path, not str
        assert defaults["server_host"] == "localhost"

    def test_properties(self) -> None:
        """Properties return correct values."""
        defaults = MultiDefault("a.ini", "b.json", skip_missing=True)
        assert defaults.sources == ("a.ini", "b.json")
        assert defaults.skip_missing is True


# =============================================================================
# Tests: Integration with SmartOptions
# =============================================================================


class TestMultiDefaultWithSmartOptions:
    """Tests for MultiDefault integration with SmartOptions."""

    def test_as_defaults_parameter(self) -> None:
        """MultiDefault works as SmartOptions defaults parameter."""
        from genro_toolbox import SmartOptions

        defaults = MultiDefault({"server_host": "localhost", "server_port": 8000})
        opts = SmartOptions(defaults=defaults)

        assert opts.server_host == "localhost"
        assert opts.server_port == 8000

    def test_incoming_overrides_multidefault(self) -> None:
        """SmartOptions incoming overrides MultiDefault values."""
        from genro_toolbox import SmartOptions

        defaults = MultiDefault({"server_host": "localhost", "server_port": 8000})
        opts = SmartOptions(
            incoming={"server_port": 9999},
            defaults=defaults,
        )

        assert opts.server_host == "localhost"  # from defaults
        assert opts.server_port == 9999  # from incoming

    def test_full_chain_with_smartoptions(
        self, temp_ini_file: Path, env_vars: None
    ) -> None:
        """Full priority chain: dict < file < env < incoming."""
        from genro_toolbox import SmartOptions

        defaults = MultiDefault(
            {"server_host": "default_host", "custom_key": "from_dict"},
            str(temp_ini_file),
            "ENV:TESTAPP",
        )

        opts = SmartOptions(
            incoming={"server_host": "incoming_host"},
            defaults=defaults,
        )

        assert opts.server_host == "incoming_host"  # incoming wins
        assert opts.server_port == 9000  # from env
        assert opts.logging_level == "INFO"  # from file
        assert opts.custom_key == "from_dict"  # from dict

    def test_with_ignore_none(self, env_vars: None) -> None:
        """SmartOptions ignore_none works with MultiDefault."""
        from genro_toolbox import SmartOptions

        defaults = MultiDefault({"empty": "default_value"}, "ENV:TESTAPP")
        # env has TESTAPP_EMPTY="" which becomes None

        opts = SmartOptions(
            incoming={"empty": None},
            defaults=defaults,
            ignore_none=True,
        )

        # incoming None is ignored, so env value (None) should be used
        # But env value is also None, so we get None
        assert opts.empty is None
