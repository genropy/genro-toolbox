# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Tests for TreeDict class."""

import json
import tempfile
from pathlib import Path

import pytest

from genro_toolbox.treedict import TreeDict


class TestTreeDictInit:
    """Tests for TreeDict initialization."""

    def test_empty_init(self) -> None:
        """Empty TreeDict should have no data."""
        td = TreeDict()
        assert len(td) == 0
        assert td.as_dict() == {}

    def test_init_with_flat_dict(self) -> None:
        """TreeDict should accept flat dict."""
        td = TreeDict({"a": 1, "b": 2})
        assert td["a"] == 1
        assert td["b"] == 2

    def test_init_with_nested_dict(self) -> None:
        """TreeDict should wrap nested dicts."""
        td = TreeDict({"a": {"b": {"c": 1}}})
        assert isinstance(td["a"], TreeDict)
        assert isinstance(td["a.b"], TreeDict)
        assert td["a.b.c"] == 1

    def test_init_with_list(self) -> None:
        """TreeDict should keep lists as lists."""
        td = TreeDict({"data": [1, 2, 3]})
        assert td["data"] == [1, 2, 3]
        assert isinstance(td["data"], list)

    def test_init_with_json_string(self) -> None:
        """TreeDict should parse JSON string."""
        td = TreeDict('{"a": 1, "b": {"c": 2}}')
        assert td["a"] == 1
        assert td["b.c"] == 2

    def test_init_with_invalid_json_raises(self) -> None:
        """TreeDict should raise on invalid JSON string."""
        with pytest.raises(json.JSONDecodeError):
            TreeDict("not valid json")

    def test_init_with_invalid_type_raises(self) -> None:
        """TreeDict should raise on invalid type."""
        with pytest.raises(TypeError):
            TreeDict(123)  # type: ignore[arg-type]


class TestTreeDictPathAccess:
    """Tests for path string access."""

    def test_get_simple_path(self) -> None:
        """Getting by simple path works."""
        td = TreeDict({"a": 1})
        assert td["a"] == 1

    def test_get_nested_path(self) -> None:
        """Getting by nested path works."""
        td = TreeDict({"a": {"b": {"c": 1}}})
        assert td["a.b.c"] == 1

    def test_get_missing_path(self) -> None:
        """Getting missing path returns None."""
        td = TreeDict()
        assert td["a.b.c"] is None

    def test_set_simple_path(self) -> None:
        """Setting by simple path works."""
        td = TreeDict()
        td["a"] = 1
        assert td["a"] == 1

    def test_set_creates_intermediate(self) -> None:
        """Setting nested path creates intermediate dicts."""
        td = TreeDict()
        td["a.b.c"] = 1
        assert td["a.b.c"] == 1
        assert isinstance(td["a"], TreeDict)
        assert isinstance(td["a.b"], TreeDict)

    def test_del_simple_path(self) -> None:
        """Deleting by simple path works."""
        td = TreeDict({"a": 1})
        del td["a"]
        assert td["a"] is None

    def test_del_nested_path(self) -> None:
        """Deleting by nested path works."""
        td = TreeDict({"a": {"b": 1, "c": 2}})
        del td["a.b"]
        assert td["a.b"] is None
        assert td["a.c"] == 2

    def test_del_missing_path_raises(self) -> None:
        """Deleting missing path raises KeyError."""
        td = TreeDict()
        with pytest.raises(KeyError):
            del td["a.b.c"]


class TestTreeDictListAccess:
    """Tests for list access with #N syntax."""

    def test_get_list_item(self) -> None:
        """Getting list item by #N works."""
        td = TreeDict({"items": [1, 2, 3]})
        assert td["items.#0"] == 1
        assert td["items.#1"] == 2
        assert td["items.#2"] == 3

    def test_get_nested_in_list(self) -> None:
        """Getting nested value in list item works."""
        td = TreeDict({"users": [{"name": "Alice"}, {"name": "Bob"}]})
        assert td["users.#0.name"] == "Alice"
        assert td["users.#1.name"] == "Bob"

    def test_get_list_out_of_bounds(self) -> None:
        """Getting out of bounds list index returns None."""
        td = TreeDict({"items": [1, 2]})
        assert td["items.#5"] is None

    def test_get_list_on_non_list(self) -> None:
        """Getting #N on non-list returns None."""
        td = TreeDict({"a": 1})
        assert td["a.#0"] is None

    def test_set_list_item(self) -> None:
        """Setting list item creates list with padding."""
        td = TreeDict()
        td["data.#0.id"] = 1
        assert td["data.#0.id"] == 1
        assert isinstance(td["data"], list)

    def test_set_list_with_gap(self) -> None:
        """Setting list item beyond length pads with None."""
        td = TreeDict()
        td["data.#0"] = "a"
        td["data.#2"] = "c"
        assert td["data"] == ["a", None, "c"]

    def test_del_list_item(self) -> None:
        """Deleting list item works."""
        td = TreeDict({"data": [1, 2, 3]})
        del td["data.#1"]
        assert td["data"] == [1, 3]


class TestTreeDictDictInterface:
    """Tests for dict-like interface."""

    def test_contains(self) -> None:
        """'in' operator works for top-level keys."""
        td = TreeDict({"a": 1})
        assert "a" in td
        assert "b" not in td

    def test_len(self) -> None:
        """len() returns number of top-level keys."""
        td = TreeDict({"a": 1, "b": 2, "c": 3})
        assert len(td) == 3

    def test_iter(self) -> None:
        """Iteration yields top-level keys."""
        td = TreeDict({"a": 1, "b": 2})
        assert set(td) == {"a", "b"}

    def test_keys(self) -> None:
        """keys() returns top-level keys."""
        td = TreeDict({"a": 1, "b": 2})
        assert set(td.keys()) == {"a", "b"}

    def test_values(self) -> None:
        """values() returns top-level values."""
        td = TreeDict({"a": 1, "b": 2})
        assert set(td.values()) == {1, 2}

    def test_items(self) -> None:
        """items() returns top-level items."""
        td = TreeDict({"a": 1, "b": 2})
        assert set(td.items()) == {("a", 1), ("b", 2)}

    def test_get_with_default(self) -> None:
        """get() returns default for missing keys."""
        td = TreeDict({"a": 1})
        assert td.get("a") == 1
        assert td.get("b") is None
        assert td.get("b", 42) == 42

    def test_get_path_with_default(self) -> None:
        """get() works with path strings."""
        td = TreeDict({"a": {"b": 1}})
        assert td.get("a.b") == 1
        assert td.get("a.c", 42) == 42


class TestTreeDictAsDict:
    """Tests for as_dict() method."""

    def test_as_dict_flat(self) -> None:
        """as_dict() returns plain dict for flat data."""
        td = TreeDict({"a": 1, "b": 2})
        assert td.as_dict() == {"a": 1, "b": 2}

    def test_as_dict_nested(self) -> None:
        """as_dict() unwraps nested TreeDicts."""
        td = TreeDict({"a": {"b": {"c": 1}}})
        result = td.as_dict()
        assert result == {"a": {"b": {"c": 1}}}
        assert not isinstance(result["a"], TreeDict)

    def test_as_dict_with_lists(self) -> None:
        """as_dict() handles lists correctly."""
        td = TreeDict({"items": [{"id": 1}, {"id": 2}]})
        result = td.as_dict()
        assert result == {"items": [{"id": 1}, {"id": 2}]}


class TestTreeDictWalk:
    """Tests for walk() method."""

    def test_walk_flat(self) -> None:
        """walk() yields flat paths."""
        td = TreeDict({"a": 1, "b": 2})
        result = dict(td.walk())
        assert result == {"a": 1, "b": 2}

    def test_walk_nested(self) -> None:
        """walk() yields nested paths."""
        td = TreeDict({"a": {"b": {"c": 1}}})
        result = dict(td.walk())
        assert result == {"a.b.c": 1}

    def test_walk_mixed(self) -> None:
        """walk() handles mixed structure."""
        td = TreeDict({"name": "test", "config": {"debug": True}})
        result = dict(td.walk())
        assert result == {"name": "test", "config.debug": True}

    def test_walk_list_as_leaf(self) -> None:
        """walk() treats lists as leaf values by default."""
        td = TreeDict({"items": [1, 2, 3]})
        result = dict(td.walk())
        assert result == {"items": [1, 2, 3]}

    def test_walk_expand_lists(self) -> None:
        """walk(expand_lists=True) traverses lists."""
        td = TreeDict({"items": [{"id": 1}, {"id": 2}]})
        result = dict(td.walk(expand_lists=True))
        assert result == {"items.#0.id": 1, "items.#1.id": 2}

    def test_walk_expand_simple_list(self) -> None:
        """walk(expand_lists=True) handles simple lists."""
        td = TreeDict({"items": [1, 2, 3]})
        result = dict(td.walk(expand_lists=True))
        assert result == {"items.#0": 1, "items.#1": 2, "items.#2": 3}


class TestTreeDictEquality:
    """Tests for equality comparison."""

    def test_equal_treedicts(self) -> None:
        """Equal TreeDicts compare equal."""
        td1 = TreeDict({"a": 1, "b": {"c": 2}})
        td2 = TreeDict({"a": 1, "b": {"c": 2}})
        assert td1 == td2

    def test_equal_to_dict(self) -> None:
        """TreeDict equals equivalent dict."""
        td = TreeDict({"a": 1, "b": {"c": 2}})
        assert td == {"a": 1, "b": {"c": 2}}

    def test_not_equal_different_values(self) -> None:
        """Different values compare not equal."""
        td1 = TreeDict({"a": 1})
        td2 = TreeDict({"a": 2})
        assert td1 != td2


class TestTreeDictRepr:
    """Tests for string representation."""

    def test_repr_empty(self) -> None:
        """Empty TreeDict repr."""
        td = TreeDict()
        assert repr(td) == "TreeDict({})"

    def test_repr_with_data(self) -> None:
        """TreeDict repr shows data."""
        td = TreeDict({"a": 1})
        assert repr(td) == "TreeDict({'a': 1})"


class TestTreeDictContextManager:
    """Tests for context manager (thread-safe access)."""

    def test_context_manager_basic(self) -> None:
        """Context manager acquires and releases lock."""
        td = TreeDict({"a": 1})
        with td:
            td["b"] = 2
        assert td["b"] == 2

    def test_context_manager_returns_self(self) -> None:
        """Context manager returns TreeDict instance."""
        td = TreeDict({"a": 1})
        with td as ctx:
            assert ctx is td

    def test_context_manager_nested(self) -> None:
        """Nested context managers work (RLock is reentrant)."""
        td = TreeDict({"a": 1})
        with td:
            with td:
                td["b"] = 2
        assert td["b"] == 2

    def test_context_manager_with_exception(self) -> None:
        """Lock is released even if exception occurs."""
        td = TreeDict({"a": 1})
        try:
            with td:
                td["b"] = 2
                raise ValueError("test error")
        except ValueError:
            pass
        # Lock should be released, we can acquire it again
        with td:
            td["c"] = 3
        assert td["c"] == 3


class TestTreeDictAsyncContextManager:
    """Tests for async context manager (async-safe access)."""

    @pytest.mark.asyncio
    async def test_async_context_manager_basic(self) -> None:
        """Async context manager acquires and releases lock."""
        td = TreeDict({"a": 1})
        async with td:
            td["b"] = 2
        assert td["b"] == 2

    @pytest.mark.asyncio
    async def test_async_context_manager_returns_self(self) -> None:
        """Async context manager returns TreeDict instance."""
        td = TreeDict({"a": 1})
        async with td as ctx:
            assert ctx is td

    @pytest.mark.asyncio
    async def test_async_context_manager_with_exception(self) -> None:
        """Async lock is released even if exception occurs."""
        td = TreeDict({"a": 1})
        try:
            async with td:
                td["b"] = 2
                raise ValueError("test error")
        except ValueError:
            pass
        # Lock should be released, we can acquire it again
        async with td:
            td["c"] = 3
        assert td["c"] == 3

    @pytest.mark.asyncio
    async def test_async_lock_lazy_init(self) -> None:
        """Async lock is lazily initialized."""
        td = TreeDict({"a": 1})
        assert td._async_lock is None
        async with td:
            assert td._async_lock is not None


class TestTreeDictNestedTreeDict:
    """Tests for nested TreeDict handling."""

    def test_assign_treedict_shares_data(self) -> None:
        """Assigning TreeDict shares the underlying data."""
        td1 = TreeDict({"x": 1})
        td2 = TreeDict()
        td2["child"] = td1

        # Modifying td1 affects td2["child"] (same _data reference)
        td1["x"] = 999
        assert td2["child.x"] == 999

    def test_assign_treedict_is_treedict(self) -> None:
        """Assigned TreeDict remains a TreeDict."""
        td1 = TreeDict({"x": 1})
        td2 = TreeDict()
        td2["child"] = td1

        assert isinstance(td2["child"], TreeDict)

    def test_nested_treedict_in_init(self) -> None:
        """TreeDict in init data is handled."""
        inner = TreeDict({"x": 1})
        outer = TreeDict({"child": inner.as_dict()})

        assert outer["child.x"] == 1


class TestTreeDictFromFile:
    """Tests for from_file classmethod."""

    def test_from_json_file(self) -> None:
        """Load TreeDict from JSON file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"server": {"host": "localhost", "port": 8080}}, f)
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td["server.host"] == "localhost"
        assert td["server.port"] == 8080
        Path(f.name).unlink()

    def test_from_file_not_found(self) -> None:
        """from_file raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            TreeDict.from_file("/nonexistent/path/config.json")

    def test_from_file_unsupported_format(self) -> None:
        """from_file raises ValueError for unsupported format."""
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.write(b"data")
            f.flush()
            with pytest.raises(ValueError, match="Unsupported"):
                TreeDict.from_file(f.name)
            Path(f.name).unlink()

    def test_from_file_with_path_object(self) -> None:
        """from_file accepts Path object."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            td = TreeDict.from_file(Path(f.name))

        assert td["key"] == "value"
        Path(f.name).unlink()

    def test_from_yaml_file(self) -> None:
        """Load TreeDict from YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("server:\n  host: localhost\n  port: 8080\n")
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td["server.host"] == "localhost"
        assert td["server.port"] == 8080
        Path(f.name).unlink()

    def test_from_yml_file(self) -> None:
        """Load TreeDict from .yml file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
            f.write("key: value\n")
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td["key"] == "value"
        Path(f.name).unlink()

    def test_from_toml_file(self) -> None:
        """Load TreeDict from TOML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[server]\nhost = "localhost"\nport = 8080\n')
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td["server.host"] == "localhost"
        assert td["server.port"] == 8080
        Path(f.name).unlink()

    def test_from_ini_file(self) -> None:
        """Load TreeDict from INI file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ini", delete=False) as f:
            f.write("[server]\nhost = localhost\nport = 8080\n")
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td["server.host"] == "localhost"
        assert td["server.port"] == "8080"  # INI values are strings
        Path(f.name).unlink()

    def test_from_empty_yaml_file(self) -> None:
        """Load TreeDict from empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            f.flush()
            td = TreeDict.from_file(f.name)

        assert td.as_dict() == {}
        Path(f.name).unlink()


class TestTreeDictDeleteEdgeCases:
    """Tests for delete edge cases."""

    def test_delete_nested_key(self) -> None:
        """Delete a nested key."""
        td = TreeDict({"a": {"b": {"c": 1, "d": 2}}})
        del td["a.b.c"]
        assert td["a.b.c"] is None
        assert td["a.b.d"] == 2

    def test_delete_nonexistent_key_raises(self) -> None:
        """Delete nonexistent key raises KeyError."""
        td = TreeDict({"a": 1})
        with pytest.raises(KeyError):
            del td["nonexistent"]

    def test_delete_nonexistent_nested_key_raises(self) -> None:
        """Delete nonexistent nested key raises KeyError."""
        td = TreeDict({"a": {"b": 1}})
        with pytest.raises(KeyError):
            del td["a.nonexistent"]

    def test_delete_through_non_dict_raises(self) -> None:
        """Delete through non-dict value raises KeyError."""
        td = TreeDict({"a": 1})
        with pytest.raises(KeyError):
            del td["a.b"]

    def test_delete_from_list(self) -> None:
        """Delete from list removes the element."""
        td = TreeDict({"items": [1, 2, 3]})
        del td["items.#0"]
        assert td["items"] == [2, 3]


class TestTreeDictWalkEdgeCases:
    """Tests for walk edge cases."""

    def test_walk_with_nested_lists(self) -> None:
        """Walk with expand_lists through nested lists."""
        td = TreeDict({"data": [[1, 2], [3, 4]]})
        paths = list(td.walk(expand_lists=True))
        assert ("data.#0.#0", 1) in paths
        assert ("data.#0.#1", 2) in paths
        assert ("data.#1.#0", 3) in paths
        assert ("data.#1.#1", 4) in paths

    def test_walk_list_of_dicts_with_expand(self) -> None:
        """Walk list of dicts with expand_lists."""
        td = TreeDict({"users": [{"name": "Alice"}, {"name": "Bob"}]})
        paths = list(td.walk(expand_lists=True))
        assert ("users.#0.name", "Alice") in paths
        assert ("users.#1.name", "Bob") in paths


class TestTreeDictSetEdgeCases:
    """Tests for set edge cases."""

    def test_set_through_list_raises(self) -> None:
        """Set through list index raises TypeError."""
        td = TreeDict({"items": [1, 2, 3]})
        with pytest.raises(TypeError):
            td["items.#0.value"] = "x"

    def test_set_creates_intermediate_dicts(self) -> None:
        """Set creates intermediate dicts."""
        td = TreeDict({})
        td["a.b.c.d"] = 1
        assert td["a.b.c.d"] == 1
        assert isinstance(td["a"], TreeDict)
        assert isinstance(td["a.b"], TreeDict)
        assert isinstance(td["a.b.c"], TreeDict)


class TestTreeDictGetEdgeCases:
    """Tests for get edge cases."""

    def test_get_with_default(self) -> None:
        """Get with default value."""
        td = TreeDict({"a": 1})
        assert td.get("a", 99) == 1
        assert td.get("missing", 99) == 99

    def test_get_nested_with_default(self) -> None:
        """Get nested path with default."""
        td = TreeDict({"a": {"b": 1}})
        assert td.get("a.b", 99) == 1
        assert td.get("a.missing", 99) == 99

    def test_get_through_non_dict_returns_default(self) -> None:
        """Get through non-dict returns default."""
        td = TreeDict({"a": 1})
        assert td.get("a.b", 99) == 99
