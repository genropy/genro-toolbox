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

"""
Multi-source configuration loader with flattening support.

This module provides ``MultiDefault``, a class that loads configuration from
multiple sources (dict, files, environment variables) and merges them into
a single flat dictionary. It implements the Mapping protocol, making it
directly usable as the ``defaults`` parameter of ``SmartOptions``.

Architecture
------------

::

    MultiDefault(*sources)
        ↓ resolve() + flatten
    dict (flat: {'section_key': value, ...})
        ↓
    SmartOptions(incoming, defaults)
        ↓
    opts.section_key

Sources are processed in order, with later sources overriding earlier ones.
Nested structures are flattened using underscore as separator.

Supported Sources
-----------------

dict
    Python dictionary, used directly. Can be flat or nested (will be flattened).
    Example: ``{'server': {'host': 'localhost'}}`` → ``{'server_host': 'localhost'}``

str (file path)
    File path with extension determining the format. Supported formats:
    - ``.ini`` - ConfigParser format (stdlib)
    - ``.json`` - JSON format (stdlib)
    - ``.toml`` - TOML format (tomllib Python 3.11+ or tomli package)
    - ``.yaml``, ``.yml`` - YAML format (pyyaml package required)

str (ENV:PREFIX)
    Environment variables with the given prefix. The prefix is stripped and
    the remaining key is lowercased.
    Example: ``MYAPP_SERVER_HOST=x`` with ``'ENV:MYAPP'`` → ``{'server_host': 'x'}``

pathlib.Path
    Same as str file path, but as Path object.

Auto Type Conversion
--------------------

String values from .ini files and environment variables are automatically
converted to Python types:

- ``"123"`` → ``int(123)``
- ``"12.5"`` → ``float(12.5)``
- ``"true"``, ``"false"``, ``"yes"``, ``"no"``, ``"on"``, ``"off"`` → ``bool``
- ``"none"``, ``"null"`` → ``None``
- Everything else → ``str``

Example Usage
-------------

Basic usage with multiple sources::

    from genro_toolbox import SmartOptions, MultiDefault

    defaults = MultiDefault(
        {'server_host': '0.0.0.0', 'server_port': 8000},  # hardcoded base
        'config/base.ini',                                  # file config
        'config/local.ini',                                 # local overrides
        'ENV:MYAPP',                                        # env var overrides
        skip_missing=True,                                  # ignore missing files
    )

    # Use with SmartOptions
    opts = SmartOptions(
        incoming={'server_port': 9999},  # runtime overrides (highest priority)
        defaults=defaults,
    )

    opts.server_host    # from file or env
    opts.server_port    # 9999 (from incoming)

Priority order (lowest to highest)::

    hardcoded dict < config file < local file < env vars < incoming

Extracting grouped config::

    from genro_toolbox import dictExtract

    server_config = dictExtract(opts.as_dict(), 'server_')
    # {'host': '...', 'port': 9999}

Classes
-------

MultiDefault
    Main class for loading and merging configuration from multiple sources.

Functions
---------

auto_convert(value)
    Convert string to appropriate Python type.

flatten_dict(data, separator)
    Flatten nested dict using separator.

load_ini(path)
    Load configuration from .ini file.

load_json(path)
    Load configuration from .json file.

load_toml(path)
    Load configuration from .toml file.

load_yaml(path)
    Load configuration from .yaml file.

load_env(prefix)
    Load configuration from environment variables with prefix.

load_file(path)
    Load configuration from file (auto-detect format from extension).
"""

from __future__ import annotations

import json
import os
import sys
from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from configparser import ConfigParser
from pathlib import Path
from typing import Any

__all__ = [
    "MultiDefault",
    "auto_convert",
    "flatten_dict",
    "load_ini",
    "load_json",
    "load_toml",
    "load_yaml",
    "load_env",
    "load_file",
]

# -----------------------------------------------------------------------------
# Type Conversion
# -----------------------------------------------------------------------------

_BOOL_TRUE = frozenset({"true", "yes", "on", "1"})
_BOOL_FALSE = frozenset({"false", "no", "off", "0"})
_NONE_VALUES = frozenset({"none", "null", ""})


def auto_convert(value: str) -> int | float | bool | None | str:
    """
    Convert string value to appropriate Python type.

    Conversion rules (in order):
    1. If value looks like int (digits only, optional leading minus) → int
    2. If value looks like float (digits with single dot) → float
    3. If value is true/yes/on/1 (case insensitive) → True
    4. If value is false/no/off/0 (case insensitive) → False
    5. If value is none/null/empty (case insensitive) → None
    6. Otherwise → str (unchanged)

    Args:
        value: String value to convert.

    Returns:
        Converted value with appropriate Python type.

    Examples:
        >>> auto_convert("123")
        123
        >>> auto_convert("12.5")
        12.5
        >>> auto_convert("true")
        True
        >>> auto_convert("none")
        None
        >>> auto_convert("hello")
        'hello'
    """
    if not isinstance(value, str):
        return value

    stripped = value.strip()
    lower = stripped.lower()

    # Check for None values
    if lower in _NONE_VALUES:
        return None

    # Check for boolean
    if lower in _BOOL_TRUE:
        return True
    if lower in _BOOL_FALSE:
        return False

    # Check for int
    if stripped.lstrip("-").isdigit() and stripped.count("-") <= 1:
        if stripped.startswith("-") or stripped[0].isdigit():
            try:
                return int(stripped)
            except ValueError:
                pass

    # Check for float
    if stripped.count(".") == 1:
        parts = stripped.lstrip("-").split(".")
        if all(p.isdigit() for p in parts if p):
            try:
                return float(stripped)
            except ValueError:
                pass

    return value


# -----------------------------------------------------------------------------
# Flattening
# -----------------------------------------------------------------------------


def flatten_dict(
    data: Mapping[str, Any],
    separator: str = "_",
    parent_key: str = "",
) -> dict[str, Any]:
    """
    Flatten nested dictionary using separator between keys.

    Args:
        data: Dictionary to flatten (can be nested).
        separator: String to join nested keys (default: "_").
        parent_key: Prefix for keys (used in recursion).

    Returns:
        Flat dictionary with joined keys.

    Examples:
        >>> flatten_dict({'server': {'host': 'localhost', 'port': 8000}})
        {'server_host': 'localhost', 'server_port': 8000}

        >>> flatten_dict({'a': {'b': {'c': 1}}})
        {'a_b_c': 1}

        >>> flatten_dict({'debug': True, 'server': {'host': 'x'}})
        {'debug': True, 'server_host': 'x'}
    """
    items: list[tuple[str, Any]] = []

    for key, value in data.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, Mapping):
            items.extend(flatten_dict(value, separator, new_key).items())
        else:
            items.append((new_key, value))

    return dict(items)


# -----------------------------------------------------------------------------
# File Loaders
# -----------------------------------------------------------------------------


def load_ini(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from .ini file.

    Sections become top-level keys, options become nested keys.
    Values are auto-converted to appropriate Python types.

    Args:
        path: Path to .ini file.

    Returns:
        Nested dictionary with sections as top-level keys.

    Raises:
        FileNotFoundError: If file does not exist.

    Examples:
        Given config.ini::

            [server]
            host = localhost
            port = 8000

            [logging]
            level = INFO

        >>> load_ini('config.ini')
        {'server': {'host': 'localhost', 'port': 8000}, 'logging': {'level': 'INFO'}}
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    parser = ConfigParser()
    parser.read(path)

    result: dict[str, Any] = {}
    for section in parser.sections():
        result[section] = {}
        for key, value in parser.items(section):
            result[section][key] = auto_convert(value)

    return result


def load_json(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from .json file.

    Args:
        path: Path to .json file.

    Returns:
        Dictionary loaded from JSON (can be nested).

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open() as f:
        return json.load(f)


def load_toml(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from .toml file.

    Requires tomllib (Python 3.11+) or tomli package.

    Args:
        path: Path to .toml file.

    Returns:
        Dictionary loaded from TOML.

    Raises:
        FileNotFoundError: If file does not exist.
        ImportError: If tomllib/tomli not available.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    # Try tomllib (Python 3.11+) first, then tomli
    if sys.version_info >= (3, 11):
        import tomllib

        with path.open("rb") as f:
            return tomllib.load(f)
    else:
        try:
            import tomli

            with path.open("rb") as f:
                return tomli.load(f)
        except ImportError:
            raise ImportError(
                "TOML support requires Python 3.11+ or 'tomli' package. "
                "Install with: pip install tomli"
            ) from None


def load_yaml(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from .yaml/.yml file.

    Requires pyyaml package.

    Args:
        path: Path to .yaml file.

    Returns:
        Dictionary loaded from YAML.

    Raises:
        FileNotFoundError: If file does not exist.
        ImportError: If pyyaml not available.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError(
            "YAML support requires 'pyyaml' package. "
            "Install with: pip install pyyaml"
        ) from None

    with path.open() as f:
        return yaml.safe_load(f) or {}


def load_file(path: str | Path) -> dict[str, Any]:
    """
    Load configuration from file, auto-detecting format from extension.

    Supported extensions: .ini, .json, .toml, .yaml, .yml

    Args:
        path: Path to configuration file.

    Returns:
        Dictionary loaded from file.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file extension is not supported.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    loaders = {
        ".ini": load_ini,
        ".json": load_json,
        ".toml": load_toml,
        ".yaml": load_yaml,
        ".yml": load_yaml,
    }

    loader = loaders.get(suffix)
    if loader is None:
        raise ValueError(
            f"Unsupported config file format: {suffix}. "
            f"Supported: {', '.join(loaders.keys())}"
        )

    return loader(path)


# -----------------------------------------------------------------------------
# Environment Loader
# -----------------------------------------------------------------------------


def load_env(prefix: str) -> dict[str, Any]:
    """
    Load configuration from environment variables with given prefix.

    Variables are matched by prefix, then:
    1. Prefix is stripped
    2. Key is lowercased
    3. Value is auto-converted to appropriate type

    Args:
        prefix: Environment variable prefix (without trailing underscore).

    Returns:
        Flat dictionary with lowercase keys.

    Examples:
        Given environment::

            MYAPP_SERVER_HOST=localhost
            MYAPP_SERVER_PORT=8000
            MYAPP_DEBUG=true
            OTHER_VAR=ignored

        >>> load_env('MYAPP')
        {'server_host': 'localhost', 'server_port': 8000, 'debug': True}
    """
    prefix_with_underscore = f"{prefix}_"
    prefix_len = len(prefix_with_underscore)

    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if key.startswith(prefix_with_underscore):
            clean_key = key[prefix_len:].lower()
            result[clean_key] = auto_convert(value)

    return result


# -----------------------------------------------------------------------------
# MultiDefault Class
# -----------------------------------------------------------------------------


class MultiDefault(Mapping[str, Any]):
    """
    Load and merge configuration from multiple sources into a flat dictionary.

    Sources are processed in order, with later sources overriding earlier ones.
    The result is a flat dictionary (nested structures are flattened with "_").

    Implements the Mapping protocol, so it can be used directly as the
    ``defaults`` parameter of ``SmartOptions``.

    Args:
        *sources: Configuration sources in priority order (lowest first).
            - dict: Used directly (flattened if nested)
            - str (file path): Load from file (.ini, .json, .toml, .yaml)
            - str "ENV:PREFIX": Load from environment variables with prefix
            - pathlib.Path: Load from file

        skip_missing: If True, silently skip missing files instead of raising
            FileNotFoundError. Default: False.

    Attributes:
        sources: Tuple of original source specifications.
        skip_missing: Whether to skip missing files.

    Examples:
        Basic usage::

            defaults = MultiDefault(
                {'server_host': '0.0.0.0'},
                'config.ini',
                'ENV:MYAPP',
            )

        With SmartOptions::

            from genro_toolbox import SmartOptions

            opts = SmartOptions(
                incoming={'debug': True},
                defaults=MultiDefault('config.ini', 'ENV:MYAPP'),
            )

        Skip missing files::

            defaults = MultiDefault(
                'base.ini',
                'local.ini',  # may not exist
                skip_missing=True,
            )
    """

    def __init__(self, *sources: Any, skip_missing: bool = False):
        self._sources = sources
        self._skip_missing = skip_missing
        self._resolved: dict[str, Any] | None = None

    @property
    def sources(self) -> tuple[Any, ...]:
        """Original source specifications."""
        return self._sources

    @property
    def skip_missing(self) -> bool:
        """Whether missing files are skipped."""
        return self._skip_missing

    def resolve(self) -> dict[str, Any]:
        """
        Resolve all sources and return merged flat dictionary.

        Sources are processed in order, with later sources overriding
        earlier ones. Nested dictionaries are flattened with "_" separator.

        Returns:
            Flat dictionary with all configuration merged.

        Raises:
            FileNotFoundError: If a file source doesn't exist and
                skip_missing is False.
            ValueError: If a source type is not recognized.
        """
        if self._resolved is not None:
            return self._resolved

        result: dict[str, Any] = {}

        for source in self._sources:
            try:
                data = self._load_source(source)
            except FileNotFoundError:
                if self._skip_missing:
                    continue
                raise

            # Flatten if nested, then merge
            flat_data = flatten_dict(data) if data else {}
            result.update(flat_data)

        self._resolved = result
        return result

    def _load_source(self, source: Any) -> dict[str, Any]:
        """
        Load configuration from a single source.

        Args:
            source: Source specification (dict, str, Path).

        Returns:
            Dictionary loaded from source.

        Raises:
            FileNotFoundError: If file source doesn't exist.
            ValueError: If source type is not recognized.
        """
        # Dict: use directly
        if isinstance(source, dict):
            return source

        # Path: load from file
        if isinstance(source, Path):
            return load_file(source)

        # String: could be file path or ENV:PREFIX
        if isinstance(source, str):
            if source.startswith("ENV:"):
                prefix = source[4:]  # Remove "ENV:" prefix
                return load_env(prefix)
            else:
                return load_file(source)

        raise ValueError(
            f"Unsupported source type: {type(source).__name__}. "
            f"Expected dict, str, or Path."
        )

    # -------------------------------------------------------------------------
    # Mapping Protocol
    # -------------------------------------------------------------------------

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys."""
        return iter(self.resolve())

    def __getitem__(self, key: str) -> Any:
        """Get value by key."""
        return self.resolve()[key]

    def __len__(self) -> int:
        """Return number of keys."""
        return len(self.resolve())

    def keys(self) -> KeysView[str]:
        """Return keys view."""
        return self.resolve().keys()

    def values(self) -> ValuesView[Any]:
        """Return values view."""
        return self.resolve().values()

    def items(self) -> ItemsView[str, Any]:
        """Return items view."""
        return self.resolve().items()

    def __repr__(self) -> str:
        """Return string representation."""
        sources_repr = ", ".join(repr(s) for s in self._sources)
        return f"MultiDefault({sources_repr}, skip_missing={self._skip_missing})"


# -----------------------------------------------------------------------------
# Module Entry Point
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    # Example usage
    defaults = MultiDefault(
        {"server_host": "0.0.0.0", "server_port": 8000},
        "ENV:GENRO_TEST",
    )
    print("Resolved config:")
    for key, value in defaults.items():
        print(f"  {key}: {value!r}")
