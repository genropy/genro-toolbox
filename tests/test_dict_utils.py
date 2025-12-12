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
        # String lists become SmartOptions with True values
        assert isinstance(opts.tags, SmartOptions)
        assert opts.tags.default is True

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

    def test_contains_operator(self):
        """Test 'in' operator for key existence."""
        opts = SmartOptions({"a": 1, "b": 2})
        assert "a" in opts
        assert "b" in opts
        assert "c" not in opts

    def test_iter_over_keys(self):
        """Test iteration over keys."""
        opts = SmartOptions({"a": 1, "b": 2, "c": 3})
        keys = list(opts)
        assert set(keys) == {"a", "b", "c"}

    def test_getattr_returns_none_for_missing(self):
        """Test that missing keys return None instead of raising."""
        opts = SmartOptions({"a": 1})
        assert opts.a == 1
        assert opts.missing is None
        assert opts.another_missing is None

    def test_getitem_bracket_access(self):
        """Test bracket notation access."""
        opts = SmartOptions({"a": 1, "b": 2})
        assert opts["a"] == 1
        assert opts["b"] == 2
        assert opts["missing"] is None

    def test_nested_dict_becomes_smartoptions(self):
        """Test that nested dicts are wrapped in SmartOptions."""
        opts = SmartOptions({"server": {"host": "localhost", "port": 8080}})
        assert isinstance(opts.server, SmartOptions)
        assert opts.server.host == "localhost"
        assert opts.server.port == 8080

    def test_string_list_becomes_feature_flags(self):
        """Test that string lists become SmartOptions with True values."""
        opts = SmartOptions({"middleware": ["cors", "compression", "logging"]})
        assert isinstance(opts.middleware, SmartOptions)
        assert opts.middleware.cors is True
        assert opts.middleware.compression is True
        assert opts.middleware.logging is True
        assert opts.middleware.missing is None
        # Test iteration
        assert set(opts.middleware) == {"cors", "compression", "logging"}
        # Test 'in' operator
        assert "cors" in opts.middleware
        assert "unknown" not in opts.middleware

    def test_list_of_dicts_indexed_by_first_key(self):
        """Test that list of dicts is indexed by first key value."""
        opts = SmartOptions(
            {
                "apps": [
                    {"name": "shop", "module": "shop:ShopApp"},
                    {"name": "office", "module": "office:OfficeApp"},
                ]
            }
        )
        assert isinstance(opts.apps, SmartOptions)
        # Access by first key value
        assert opts.apps.shop.module == "shop:ShopApp"
        assert opts.apps.office.module == "office:OfficeApp"
        # Original name is preserved
        assert opts.apps.shop.name == "shop"
        # Iteration over keys
        assert set(opts.apps) == {"shop", "office"}
        # 'in' operator
        assert "shop" in opts.apps
        assert "unknown" not in opts.apps
        # Bracket access
        assert opts.apps["shop"].module == "shop:ShopApp"

    def test_mixed_list_unchanged(self):
        """Test that mixed lists are left unchanged."""
        opts = SmartOptions({"items": [1, "two", 3.0]})
        assert opts.items == [1, "two", 3.0]

    def test_empty_list_unchanged(self):
        """Test that empty lists are left unchanged."""
        opts = SmartOptions({"items": []})
        assert opts.items == []


class TestSmartOptionsFromCallable:
    """Tests for SmartOptions loading from callable signature."""

    def test_extracts_defaults_from_signature(self):
        """Test extraction of default values from function signature."""

        def my_func(name: str, port: int = 8000, debug: bool = False):
            pass

        opts = SmartOptions(my_func)
        assert opts.port == 8000
        assert opts.debug is False
        assert opts.name is None  # No default, not in argv

    def test_parses_argv_positional(self):
        """Test parsing positional arguments from argv."""

        def my_func(name: str, port: int = 8000):
            pass

        opts = SmartOptions(my_func, ["myapp"])
        assert opts.name == "myapp"
        assert opts.port == 8000

    def test_parses_argv_named(self):
        """Test parsing named arguments from argv."""

        def my_func(name: str, port: int = 8000, debug: bool = False):
            pass

        opts = SmartOptions(my_func, ["myapp", "--port", "9000"])
        assert opts.name == "myapp"
        assert opts.port == 9000
        assert opts.debug is False

    def test_parses_argv_boolean_flag(self):
        """Test parsing boolean flags from argv."""

        def my_func(name: str, debug: bool = False):
            pass

        opts = SmartOptions(my_func, ["myapp", "--debug"])
        assert opts.name == "myapp"
        assert opts.debug is True

    def test_handles_annotated_types(self):
        """Test handling of Annotated type hints."""
        from typing import Annotated

        def my_func(
            app_dir: Annotated[str, "Path to app"],
            port: Annotated[int, "Server port"] = 8000,
        ):
            pass

        opts = SmartOptions(my_func, ["/path/to/app", "--port", "9000"])
        assert opts.app_dir == "/path/to/app"
        assert opts.port == 9000


class TestSmartOptionsFromEnv:
    """Tests for SmartOptions loading from environment variables."""

    def test_loads_env_with_prefix(self, monkeypatch):
        """Test loading config from environment variables."""
        monkeypatch.setenv("MYAPP_HOST", "0.0.0.0")
        monkeypatch.setenv("MYAPP_PORT", "9000")
        monkeypatch.setenv("OTHER_VAR", "ignored")

        opts = SmartOptions("ENV:MYAPP")
        assert opts.host == "0.0.0.0"
        assert opts.port == "9000"  # Note: stays as string from env
        assert opts.other_var is None


class TestSmartOptionsAdd:
    """Tests for SmartOptions __add__ operator."""

    def test_add_two_smartoptions(self):
        """Test adding two SmartOptions together."""
        opts1 = SmartOptions({"a": 1, "b": 2})
        opts2 = SmartOptions({"b": 20, "c": 3})
        combined = opts1 + opts2
        assert combined.a == 1
        assert combined.b == 20  # Right side wins
        assert combined.c == 3

    def test_add_smartoptions_with_dict(self):
        """Test adding SmartOptions with a plain dict."""
        opts = SmartOptions({"a": 1})
        combined = opts + {"b": 2, "a": 10}
        assert combined.a == 10  # Dict overrides
        assert combined.b == 2

    def test_chain_multiple_adds(self):
        """Test chaining multiple additions."""
        base = SmartOptions({"host": "default", "port": 8000, "debug": False})
        from_file = SmartOptions({"host": "fromfile", "timeout": 30})
        from_env = {"port": 9000}
        from_argv = SmartOptions({"debug": True})

        final = base + from_file + from_env + from_argv
        assert final.host == "fromfile"  # from file
        assert final.port == 9000  # from env
        assert final.debug is True  # from argv
        assert final.timeout == 30  # from file

    def test_add_returns_new_instance(self):
        """Test that add returns a new SmartOptions instance."""
        opts1 = SmartOptions({"a": 1})
        opts2 = SmartOptions({"b": 2})
        combined = opts1 + opts2
        assert combined is not opts1
        assert combined is not opts2
        # Original unchanged
        assert "b" not in opts1
        assert "a" not in opts2


class TestSmartOptionsFromFile:
    """Tests for SmartOptions loading from config files."""

    def test_loads_yaml_file(self, tmp_path):
        """Test loading config from YAML file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("host: localhost\nport: 8080\n")

        opts = SmartOptions(str(config_file))
        assert opts.host == "localhost"
        assert opts.port == 8080

    def test_loads_json_file(self, tmp_path):
        """Test loading config from JSON file."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"host": "localhost", "port": 8080}')

        opts = SmartOptions(str(config_file))
        assert opts.host == "localhost"
        assert opts.port == 8080

    def test_loads_yaml_with_nested(self, tmp_path):
        """Test loading YAML with nested structures."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(
            """
server:
  host: localhost
  port: 8080
middleware:
  - cors
  - compression
apps:
  - name: shop
    module: shop:ShopApp
  - name: office
    module: office:OfficeApp
"""
        )

        opts = SmartOptions(str(config_file))
        assert opts.server.host == "localhost"
        assert opts.server.port == 8080
        assert opts.middleware.cors is True
        assert opts.apps.shop.module == "shop:ShopApp"

    def test_unsupported_format_raises(self, tmp_path):
        """Test that unsupported file format raises ValueError."""
        config_file = tmp_path / "config.xyz"
        config_file.write_text("some content")

        with pytest.raises(ValueError, match="Unsupported config file format"):
            SmartOptions(str(config_file))

    def test_loads_toml_file(self, tmp_path):
        """Test loading config from TOML file."""
        config_file = tmp_path / "config.toml"
        config_file.write_text('host = "localhost"\nport = 8080\n')

        opts = SmartOptions(str(config_file))
        assert opts.host == "localhost"
        assert opts.port == 8080

    def test_loads_ini_file(self, tmp_path):
        """Test loading config from INI file."""
        config_file = tmp_path / "config.ini"
        config_file.write_text("[server]\nhost = localhost\nport = 8080\n")

        opts = SmartOptions(str(config_file))
        assert opts.server_host == "localhost"
        assert opts.server_port == "8080"  # INI values are strings

    def test_missing_file_returns_empty(self, tmp_path):
        """Test that missing file returns empty SmartOptions."""
        config_file = tmp_path / "nonexistent.yaml"
        opts = SmartOptions(str(config_file))
        assert opts.as_dict() == {}

    def test_loads_from_path_object(self, tmp_path):
        """Test loading config from Path object."""
        from pathlib import Path

        config_file = tmp_path / "config.yaml"
        config_file.write_text("host: localhost\nport: 8080\n")

        opts = SmartOptions(Path(config_file))
        assert opts.host == "localhost"
        assert opts.port == 8080

    def test_empty_list_of_dicts(self):
        """Test handling of empty list of dicts."""
        opts = SmartOptions({"items": [{}]})
        # Empty dict has no keys, so nothing to index
        assert isinstance(opts.items, SmartOptions)


class TestSmartOptionsEdgeCases:
    """Tests for SmartOptions edge cases."""

    def test_getattr_underscore_raises(self):
        """Test that accessing _private raises AttributeError."""
        opts = SmartOptions({"a": 1})
        with pytest.raises(AttributeError):
            _ = opts._nonexistent

    def test_argv_value_after_flag(self):
        """Test parsing value that comes after a flag with value."""

        def my_func(name: str, count: int = 1, verbose: bool = False):
            pass

        # --count 5 followed by --verbose (bool flag)
        opts = SmartOptions(my_func, ["myname", "--count", "5", "--verbose"])
        assert opts.name == "myname"
        assert opts.count == 5
        assert opts.verbose is True

    def test_argv_dash_conversion(self):
        """Test that --my-option becomes my_option."""

        def my_func(my_option: str = "default"):
            pass

        opts = SmartOptions(my_func, ["--my-option", "value"])
        assert opts.my_option == "value"
