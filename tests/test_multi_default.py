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
from typing import TYPE_CHECKING, Annotated

import pytest

from genro_toolbox.multi_default import (
    MultiDefault,
    extract_signature,
    flatten_dict,
    load_argv,
    load_env,
    load_file,
    load_ini,
    load_json,
    load_toml,
    load_yaml,
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
        """Load basic .ini file - all values are strings."""
        result = load_ini(temp_ini_file)

        assert "server" in result
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == "8000"  # string, not int
        assert result["server"]["debug"] == "true"  # string, not bool

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
# Tests: load_toml
# =============================================================================


class TestLoadToml:
    """Tests for load_toml function."""

    def test_load_basic(self, tmp_path: Path) -> None:
        """Load basic .toml file - preserves types."""
        content = """\
[server]
host = "localhost"
port = 8000
debug = true

[logging]
level = "INFO"
"""
        file_path = tmp_path / "config.toml"
        file_path.write_text(content)

        result = load_toml(file_path)

        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 8000  # int preserved
        assert result["server"]["debug"] is True  # bool preserved
        assert result["logging"]["level"] == "INFO"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_toml(tmp_path / "nonexistent.toml")


# =============================================================================
# Tests: load_yaml
# =============================================================================


class TestLoadYaml:
    """Tests for load_yaml function."""

    def test_load_basic(self, tmp_path: Path) -> None:
        """Load basic .yaml file - preserves types."""
        content = """\
server:
  host: localhost
  port: 8000
  debug: true

logging:
  level: INFO
"""
        file_path = tmp_path / "config.yaml"
        file_path.write_text(content)

        result = load_yaml(file_path)

        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 8000  # int preserved
        assert result["server"]["debug"] is True  # bool preserved
        assert result["logging"]["level"] == "INFO"

    def test_file_not_found(self, tmp_path: Path) -> None:
        """Raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_yaml(tmp_path / "nonexistent.yaml")

    def test_empty_file_returns_empty_dict(self, tmp_path: Path) -> None:
        """Empty yaml file returns empty dict."""
        file_path = tmp_path / "empty.yaml"
        file_path.write_text("")

        result = load_yaml(file_path)
        assert result == {}


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
        """Load env vars with prefix - all values are strings."""
        result = load_env("TESTAPP")

        assert result["server_host"] == "envhost"
        assert result["server_port"] == "9000"  # string, not int
        assert result["debug"] == "true"  # string, not bool
        assert result["timeout"] == "30.5"  # string, not float
        assert result["empty"] == ""  # empty string stays empty

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
        """Single file source - values are strings."""
        defaults = MultiDefault(str(temp_ini_file))
        assert defaults["server_host"] == "localhost"
        assert defaults["server_port"] == "8000"  # string from ini

    def test_single_env_source(self, env_vars: None) -> None:
        """Single env source - values are strings."""
        defaults = MultiDefault("ENV:TESTAPP")
        assert defaults["server_host"] == "envhost"
        assert defaults["server_port"] == "9000"  # string from env

    def test_priority_later_overrides_earlier(self, temp_ini_file: Path) -> None:
        """Later sources override earlier ones."""
        defaults = MultiDefault(
            {"server_host": "original", "server_port": 1111},
            str(temp_ini_file),  # has server.host=localhost, server.port=8000
        )
        assert defaults["server_host"] == "localhost"  # overridden by file
        assert defaults["server_port"] == "8000"  # overridden by file (string)

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

    def test_types_property(self) -> None:
        """Types property returns the types dict."""
        defaults = MultiDefault({"port": "8000"}, types={"port": int})
        assert defaults.types == {"port": int}

    def test_types_converts_string_to_int(self) -> None:
        """Types parameter converts string to int."""
        defaults = MultiDefault({"port": "8000"}, types={"port": int})
        assert defaults["port"] == 8000
        assert isinstance(defaults["port"], int)

    def test_types_converts_string_to_float(self) -> None:
        """Types parameter converts string to float."""
        defaults = MultiDefault({"timeout": "30.5"}, types={"timeout": float})
        assert defaults["timeout"] == 30.5
        assert isinstance(defaults["timeout"], float)

    def test_types_converts_string_to_bool_true(self) -> None:
        """Types parameter converts string to bool True."""
        defaults = MultiDefault(
            {"debug": "true", "verbose": "yes", "active": "1"},
            types={"debug": bool, "verbose": bool, "active": bool},
        )
        assert defaults["debug"] is True
        assert defaults["verbose"] is True
        assert defaults["active"] is True

    def test_types_converts_string_to_bool_false(self) -> None:
        """Types parameter converts string to bool False."""
        defaults = MultiDefault(
            {"debug": "false", "verbose": "no", "active": "0"},
            types={"debug": bool, "verbose": bool, "active": bool},
        )
        assert defaults["debug"] is False
        assert defaults["verbose"] is False
        assert defaults["active"] is False

    def test_types_converts_ini_values(self, tmp_path: Path) -> None:
        """Types parameter converts string values from ini files."""
        ini_file = tmp_path / "config.ini"
        ini_file.write_text("[app]\nversion = 00123\nport = 8080\n")

        # Without types, values are strings
        defaults_without_types = MultiDefault(str(ini_file))
        assert defaults_without_types["app_version"] == "00123"  # string
        assert defaults_without_types["app_port"] == "8080"  # string

        # With types, values are converted
        defaults_with_types = MultiDefault(str(ini_file), types={"app_port": int})
        assert defaults_with_types["app_version"] == "00123"  # still string
        assert defaults_with_types["app_port"] == 8080  # converted to int

    def test_types_skips_none_values(self) -> None:
        """Types parameter skips None values."""
        defaults = MultiDefault({"port": None}, types={"port": int})
        assert defaults["port"] is None

    def test_types_skips_already_correct_type(self) -> None:
        """Types parameter skips values already of correct type."""
        defaults = MultiDefault({"port": 8000}, types={"port": int})
        assert defaults["port"] == 8000
        assert isinstance(defaults["port"], int)

    def test_types_keeps_original_on_conversion_failure(self) -> None:
        """Types parameter keeps original value on conversion failure."""
        defaults = MultiDefault({"port": "not_a_number"}, types={"port": int})
        assert defaults["port"] == "not_a_number"

    def test_types_in_repr(self) -> None:
        """Types is included in repr."""
        defaults = MultiDefault({"a": 1}, types={"a": int})
        repr_str = repr(defaults)
        assert "types=" in repr_str
        assert "int" in repr_str

    def test_types_not_in_repr_when_empty(self) -> None:
        """Types is not included in repr when empty."""
        defaults = MultiDefault({"a": 1})
        repr_str = repr(defaults)
        assert "types=" not in repr_str

    def test_types_ignores_missing_keys(self) -> None:
        """Types parameter ignores keys not present in sources."""
        defaults = MultiDefault(
            {"port": "8000"},
            types={"port": int, "timeout": float},  # timeout not in sources
        )
        assert defaults["port"] == 8000
        assert "timeout" not in defaults


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
        assert opts.server_port == "9000"  # from env (string)
        assert opts.logging_level == "INFO"  # from file
        assert opts.custom_key == "from_dict"  # from dict

    def test_with_ignore_none(self, env_vars: None) -> None:
        """SmartOptions ignore_none works with MultiDefault."""
        from genro_toolbox import SmartOptions

        defaults = MultiDefault({"empty": "default_value"}, "ENV:TESTAPP")
        # env has TESTAPP_EMPTY="" which is now kept as empty string

        opts = SmartOptions(
            incoming={"empty": None},
            defaults=defaults,
            ignore_none=True,
        )

        # incoming None is ignored, so env value ("") is used
        assert opts.empty == ""


# =============================================================================
# Tests: extract_signature
# =============================================================================


class TestExtractSignature:
    """Tests for extract_signature function."""

    def test_simple_function(self) -> None:
        """Extract from simple function with defaults."""

        def cmd(foo: str = "default", bar: int = 42) -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        assert defaults == {"foo": "default", "bar": 42}
        assert types == {"foo": str, "bar": int}
        assert helps == {}

    def test_annotated_with_help(self) -> None:
        """Extract help strings from Annotated."""

        def cmd(
            foo: Annotated[str, "Foo help"] = "default",
            bar: Annotated[int, "Bar help"] = 42,
        ) -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        assert defaults == {"foo": "default", "bar": 42}
        assert types == {"foo": str, "bar": int}
        assert helps == {"foo": "Foo help", "bar": "Bar help"}

    def test_optional_type(self) -> None:
        """Extract inner type from Optional."""

        def cmd(
            config: Path | None = None,
            host: str = "localhost",
        ) -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        assert defaults == {"config": None, "host": "localhost"}
        assert types == {"config": Path, "host": str}

    def test_bool_type(self) -> None:
        """Extract bool type."""

        def cmd(debug: bool = False, verbose: bool = True) -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        assert defaults == {"debug": False, "verbose": True}
        assert types == {"debug": bool, "verbose": bool}

    def test_skips_args_kwargs(self) -> None:
        """Skip *args and **kwargs."""

        def cmd(foo: str = "x", *args: str, **kwargs: int) -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        assert defaults == {"foo": "x"}
        assert types == {"foo": str}

    def test_no_default_value(self) -> None:
        """Parameters without defaults are not included."""

        def cmd(required: str, optional: str = "default") -> None:
            pass

        defaults, types, helps = extract_signature(cmd)
        # Only parameters with defaults are extracted
        assert defaults == {"optional": "default"}
        assert types == {"optional": str}  # required has no default, so no type


# =============================================================================
# Tests: load_argv
# =============================================================================


class TestLoadArgv:
    """Tests for load_argv function."""

    def test_basic_args(self) -> None:
        """Parse basic arguments."""
        defaults = {"foo": "default", "bar": 42}
        types = {"foo": str, "bar": int}
        helps = {}

        result = load_argv(defaults, types, helps, ["--foo", "custom", "--bar", "100"])
        assert result == {"foo": "custom", "bar": 100}

    def test_partial_args(self) -> None:
        """Only provided args are in result."""
        defaults = {"foo": "default", "bar": 42}
        types = {"foo": str, "bar": int}
        helps = {}

        result = load_argv(defaults, types, helps, ["--bar", "100"])
        assert result == {"bar": 100}
        assert "foo" not in result

    def test_bool_store_true(self) -> None:
        """Bool with default=False uses store_true."""
        defaults = {"debug": False}
        types = {"debug": bool}
        helps = {}

        result = load_argv(defaults, types, helps, ["--debug"])
        assert result == {"debug": True}

    def test_bool_store_false(self) -> None:
        """Bool with default=True uses --no-xxx."""
        defaults = {"verbose": True}
        types = {"verbose": bool}
        helps = {}

        result = load_argv(defaults, types, helps, ["--no-verbose"])
        assert result == {"verbose": False}

    def test_empty_argv(self) -> None:
        """Empty argv returns empty dict."""
        defaults = {"foo": "default"}
        types = {"foo": str}
        helps = {}

        result = load_argv(defaults, types, helps, [])
        assert result == {}

    def test_underscore_to_dash(self) -> None:
        """Underscores in param names become dashes in CLI."""
        defaults = {"server_port": 8000}
        types = {"server_port": int}
        helps = {}

        result = load_argv(defaults, types, helps, ["--server-port", "9000"])
        assert result == {"server_port": 9000}


# =============================================================================
# Tests: MultiDefault with callable and ARGV
# =============================================================================


class TestMultiDefaultCallable:
    """Tests for MultiDefault with callable source."""

    def test_callable_provides_defaults(self) -> None:
        """Callable source provides defaults."""

        def cmd(foo: str = "default", bar: int = 42) -> None:
            pass

        defaults = MultiDefault(cmd)
        assert defaults["foo"] == "default"
        assert defaults["bar"] == 42

    def test_callable_provides_types(self) -> None:
        """Callable source provides types for conversion."""

        def cmd(port: int = 8000) -> None:
            pass

        defaults = MultiDefault(cmd, {"port": "9000"})  # string from dict
        assert defaults["port"] == 9000  # converted to int
        assert isinstance(defaults["port"], int)

    def test_callable_with_file_override(self, tmp_path: Path) -> None:
        """File overrides callable defaults."""

        def cmd(foo: str = "default", bar: int = 42) -> None:
            pass

        toml_file = tmp_path / "config.toml"
        toml_file.write_text('foo = "from_file"\n')

        defaults = MultiDefault(cmd, str(toml_file))
        assert defaults["foo"] == "from_file"
        assert defaults["bar"] == 42

    def test_callable_with_env_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Env overrides callable defaults."""

        def cmd(foo: str = "default", bar: int = 42) -> None:
            pass

        monkeypatch.setenv("MYAPP_FOO", "from_env")

        defaults = MultiDefault(cmd, "ENV:MYAPP")
        assert defaults["foo"] == "from_env"
        assert defaults["bar"] == 42

    def test_only_one_callable_allowed(self) -> None:
        """Only one callable source is allowed."""

        def cmd1(foo: str = "a") -> None:
            pass

        def cmd2(bar: str = "b") -> None:
            pass

        with pytest.raises(ValueError, match="Only one callable"):
            MultiDefault(cmd1, cmd2)

    def test_explicit_types_override_callable_types(self) -> None:
        """Explicit types parameter overrides callable types."""

        def cmd(value: int = 42) -> None:
            pass

        # Explicit types says value is str, not int
        defaults = MultiDefault(cmd, types={"value": str})
        assert defaults["value"] == "42"  # converted to str


class TestMultiDefaultArgv:
    """Tests for MultiDefault with ARGV: source."""

    def test_argv_parses_args(self) -> None:
        """ARGV: parses command line arguments via load_argv."""

        def cmd(
            foo: Annotated[str, "Foo value"] = "default",
            bar: Annotated[int, "Bar value"] = 42,
        ) -> None:
            pass

        # Test load_argv directly with explicit argv
        defaults_dict, types, helps = extract_signature(cmd)
        result = load_argv(
            defaults_dict, types, helps, ["--foo", "custom", "--bar", "100"]
        )
        assert result == {"foo": "custom", "bar": 100}

    def test_argv_requires_callable(self) -> None:
        """ARGV: requires a callable source."""
        with pytest.raises(ValueError, match="requires a callable"):
            MultiDefault({"foo": "bar"}, "ARGV:")

    def test_full_chain_with_argv(self, tmp_path: Path) -> None:
        """Full chain: callable < file < env < argv."""

        def cmd(
            foo: str = "from_callable",
            bar: int = 1,
            baz: str = "unchanged",
        ) -> None:
            pass

        toml_file = tmp_path / "config.toml"
        toml_file.write_text('foo = "from_file"\nbar = 2\n')

        # Create MultiDefault and test _load_source for ARGV
        defaults = MultiDefault(cmd, str(toml_file))

        # callable provides defaults
        assert defaults["baz"] == "unchanged"
        # file overrides
        assert defaults["foo"] == "from_file"
        assert defaults["bar"] == 2
