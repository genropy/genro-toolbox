# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""TreeDict - A hierarchical dictionary with dot notation access."""

from __future__ import annotations

import asyncio
import configparser
import json
from collections.abc import Iterator
from pathlib import Path
from threading import RLock
from typing import Any

try:
    import tomllib
except ImportError:
    tomllib = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class _TraversalError(Exception):
    """Internal signal for failed path traversal (not part of public API)."""


class TreeDict:
    """Hierarchical dictionary with dot-path access, list indexing (#N), and thread/async safety."""

    __slots__ = ("_data", "_lock", "_async_lock")

    def __init__(self, data: dict[str, Any] | str | None = None) -> None:
        """Initialize TreeDict with optional data.

        Args:
            data: Initial data. Can be:
                - dict: Used directly
                - str: Parsed as JSON
                - None: Empty TreeDict

        Raises:
            json.JSONDecodeError: If string is not valid JSON.
            TypeError: If data is not dict, str, or None.
        """
        object.__setattr__(self, "_data", {})
        object.__setattr__(self, "_lock", RLock())
        object.__setattr__(self, "_async_lock", None)  # Lazy init

        if data is None:
            return

        if isinstance(data, str):
            data = json.loads(data)

        if not isinstance(data, dict):
            raise TypeError(f"Expected dict or JSON string, got {type(data).__name__}")

        for key, value in data.items():
            self._data[key] = self._wrap(value)

    def __enter__(self) -> TreeDict:
        """Acquire lock for thread-safe access."""
        self._lock.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        """Release lock."""
        self._lock.release()

    async def __aenter__(self) -> TreeDict:
        """Acquire async lock for async-safe access."""
        if self._async_lock is None:
            object.__setattr__(self, "_async_lock", asyncio.Lock())
        await self._async_lock.acquire()
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Release async lock."""
        self._async_lock.release()

    def _wrap(self, value: Any) -> Any:
        """Wrap nested dicts as TreeDict, leave other values unchanged.

        If value is a TreeDict, creates a new TreeDict sharing the same _data.
        """
        if isinstance(value, TreeDict):
            # Share the same _data reference
            new_td = TreeDict.__new__(TreeDict)
            object.__setattr__(new_td, "_data", value._data)
            object.__setattr__(new_td, "_lock", RLock())
            object.__setattr__(new_td, "_async_lock", None)
            return new_td
        if isinstance(value, dict):
            return TreeDict(value)
        return value

    def _unwrap(self, value: Any) -> Any:
        """Unwrap TreeDict to plain dict recursively."""
        if isinstance(value, TreeDict):
            return {k: self._unwrap(v) for k, v in value._data.items()}
        if isinstance(value, list):
            return [self._unwrap(item) for item in value]
        return value

    def _parse_key(self, key: str) -> tuple[bool, int | str]:
        """Parse a path segment, detecting list index (#N) syntax.

        Returns:
            Tuple of (is_list_index, index_or_key)
        """
        if key.startswith("#") and key[1:].isdigit():
            return True, int(key[1:])
        return False, key

    def _traverse_to_parent(
        self, parts: list[str], *, create: bool = False
    ) -> Any:
        """Walk all path segments except the last, returning the parent container.

        Args:
            parts: All path segments (the full split path).
            create: If True, create intermediate TreeDict/list nodes as needed.

        Raises:
            _TraversalError: When navigation fails (missing key, wrong type, None).
        """
        current: Any = self

        for i, part in enumerate(parts[:-1]):
            if current is None:
                raise _TraversalError

            is_list_idx, key = self._parse_key(part)

            if is_list_idx:
                assert isinstance(key, int)
                if not isinstance(current, list):
                    if create:
                        raise TypeError(f"Cannot index non-list with {part}")
                    raise _TraversalError
                if create:
                    while len(current) <= key:
                        current.append(None)
                    if current[key] is None:
                        next_is_list, _ = self._parse_key(parts[i + 1])
                        current[key] = [] if next_is_list else TreeDict()
                elif key < 0 or key >= len(current):
                    raise _TraversalError
                current = current[key]
                if not create and isinstance(current, dict) and not isinstance(current, TreeDict):
                    current = TreeDict(current)
            elif isinstance(current, TreeDict):
                if create:
                    assert isinstance(key, str)
                    if key not in current._data or current._data[key] is None:
                        next_is_list, _ = self._parse_key(parts[i + 1])
                        current._data[key] = [] if next_is_list else TreeDict()
                    current = current._data[key]
                else:
                    current = current._data.get(key)
            elif not create and isinstance(current, dict):
                current = current.get(key)
            else:
                if create:
                    raise TypeError(f"Cannot set attribute on {type(current)}")
                raise _TraversalError

        return current

    def _get_by_path(self, path: str) -> Any:
        """Get value by dot-separated path string."""
        parts = path.split(".")
        try:
            current = self._traverse_to_parent(parts, create=False)
        except _TraversalError:
            return None
        if current is None:
            return None
        last_part = parts[-1]
        is_list_idx, key = self._parse_key(last_part)
        if is_list_idx:
            if not isinstance(current, list):
                return None
            assert isinstance(key, int)
            if key < 0 or key >= len(current):
                return None
            result = current[key]
            if isinstance(result, dict) and not isinstance(result, TreeDict):
                return TreeDict(result)
            return result
        if isinstance(current, TreeDict):
            return current._data.get(key)
        if isinstance(current, dict):
            return current.get(key)
        return None

    def _set_by_path(self, path: str, value: Any) -> None:
        """Set value by dot-separated path string, creating intermediate nodes."""
        parts = path.split(".")
        current = self._traverse_to_parent(parts, create=True)

        last_part = parts[-1]
        is_list_idx, key = self._parse_key(last_part)

        if is_list_idx:
            assert isinstance(key, int)
            if not isinstance(current, list):
                raise TypeError(f"Cannot index non-list with {last_part}")
            while len(current) <= key:
                current.append(None)
            current[key] = self._wrap(value)
        elif isinstance(current, TreeDict):
            assert isinstance(key, str)
            current._data[key] = self._wrap(value)
        else:
            raise TypeError(f"Cannot set attribute on {type(current)}")

    def _del_by_path(self, path: str) -> None:
        """Delete value by dot-separated path string."""
        parts = path.split(".")
        try:
            current = self._traverse_to_parent(parts, create=False)
        except _TraversalError:
            raise KeyError(path) from None

        if current is None:
            raise KeyError(path)

        last_part = parts[-1]
        is_list_idx, key = self._parse_key(last_part)

        if is_list_idx:
            if not isinstance(current, list):
                raise KeyError(path)
            assert isinstance(key, int)
            if key < 0 or key >= len(current):
                raise KeyError(path)
            del current[key]
        elif isinstance(current, TreeDict):
            assert isinstance(key, str)
            if key not in current._data:
                raise KeyError(path)
            del current._data[key]
        else:
            raise KeyError(path)

    def __getitem__(self, path: str) -> Any:
        """Get value by dot-separated path string."""
        return self._get_by_path(path)

    def __setitem__(self, path: str, value: Any) -> None:
        """Set value by dot-separated path string."""
        self._set_by_path(path, value)

    def __delitem__(self, path: str) -> None:
        """Delete value by dot-separated path string."""
        self._del_by_path(path)

    def __contains__(self, key: str) -> bool:
        """Check if key exists (top-level only)."""
        return key in self._data

    def __len__(self) -> int:
        """Return number of top-level keys."""
        return len(self._data)

    def __iter__(self) -> Iterator[str]:
        """Iterate over top-level keys."""
        return iter(self._data)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"TreeDict({self._unwrap(self)})"

    def __eq__(self, other: object) -> bool:
        """Check equality with another TreeDict or dict."""
        if isinstance(other, TreeDict):
            return self._data == other._data
        if isinstance(other, dict):
            return self._unwrap(self) == other
        return NotImplemented

    def keys(self) -> Any:
        """Return top-level keys."""
        return self._data.keys()

    def values(self) -> Any:
        """Return top-level values."""
        return self._data.values()

    def items(self) -> Any:
        """Return top-level items."""
        return self._data.items()

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by key or path, with default."""
        if "." in key or key.startswith("#"):
            result = self._get_by_path(key)
            return default if result is None else result
        return self._data.get(key, default)

    def as_dict(self) -> dict[str, Any]:
        """Return plain dict representation (recursive unwrap)."""
        return self._unwrap(self)

    @classmethod
    def from_file(cls, path: str | Path) -> TreeDict:
        """Load TreeDict from a config file.

        Supports JSON, YAML, TOML, and INI formats (auto-detected by extension).

        Args:
            path: Path to the config file.

        Returns:
            TreeDict with loaded data.

        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If file format is not supported.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        suffix = path.suffix.lower()

        if suffix == ".json":
            with open(path) as f:
                data = json.load(f)
        elif suffix in (".yaml", ".yml"):
            if yaml is None:
                raise ImportError("PyYAML is required to load YAML files: pip install pyyaml")
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        elif suffix == ".toml":
            if tomllib is None:
                raise ImportError(
                    "tomli is required to load TOML files on Python < 3.11: pip install tomli"
                )
            with open(path, "rb") as f:
                data = tomllib.load(f)
        elif suffix == ".ini":
            parser = configparser.ConfigParser()
            parser.read(path)
            data = {section: dict(parser.items(section)) for section in parser.sections()}
        else:
            raise ValueError(f"Unsupported config file format: {suffix}")

        return cls(data)

    def walk(self, expand_lists: bool = False, _prefix: str = "") -> Iterator[tuple[str, Any]]:
        """Iterate over all paths and leaf values.

        Args:
            expand_lists: If True, traverse into lists using #N paths.
                         If False, lists are treated as leaf values.

        Yields:
            Tuples of (path, value) for each leaf node.

        Example:
            >>> td = TreeDict({"a": 1, "b": {"c": 2}})
            >>> list(td.walk())
            [('a', 1), ('b.c', 2)]
        """
        for key, value in self._data.items():
            path = f"{_prefix}.{key}" if _prefix else key

            if isinstance(value, TreeDict):
                yield from value.walk(expand_lists=expand_lists, _prefix=path)
            elif expand_lists and isinstance(value, list):
                yield from self._walk_list(value, path, expand_lists)
            else:
                yield path, value

    def _walk_list(
        self, lst: list[Any], prefix: str, expand_lists: bool
    ) -> Iterator[tuple[str, Any]]:
        """Walk through a list, yielding paths with #N notation."""
        for i, item in enumerate(lst):
            path = f"{prefix}.#{i}"
            if isinstance(item, dict):
                wrapped = TreeDict(item) if not isinstance(item, TreeDict) else item
                yield from wrapped.walk(expand_lists=expand_lists, _prefix=path)
            elif expand_lists and isinstance(item, list):
                yield from self._walk_list(item, path, expand_lists)
            else:
                yield path, item
