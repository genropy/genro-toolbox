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

    MultiDefault(*sources, types={...})
        ↓ resolve() + flatten + convert
    dict (flat: {'section_key': value, ...})
        ↓
    SmartOptions(incoming, defaults)
        ↓
    opts.section_key

Sources are processed in order, with later sources overriding earlier ones.
Nested structures are flattened using underscore as separator.

Type Conversion
---------------

By default, all values from files and environment variables are kept as strings.
Use the ``types`` parameter for explicit type conversion::

    defaults = MultiDefault(
        'config.ini',
        'ENV:MYAPP',
        types={
            'server_port': int,
            'server_debug': bool,
            'timeout': float,
        }
    )

Supported Sources
-----------------

dict
    Python dictionary, used directly. Can be flat or nested (will be flattened).
    Example: ``{'server': {'host': 'localhost'}}`` → ``{'server_host': 'localhost'}``

str (file path)
    File path with extension determining the format. Supported formats:
    - ``.ini`` - ConfigParser format (stdlib) - values are strings
    - ``.json`` - JSON format (stdlib) - preserves JSON types
    - ``.toml`` - TOML format (tomllib Python 3.11+ or tomli package) - preserves TOML types
    - ``.yaml``, ``.yml`` - YAML format (pyyaml package required) - preserves YAML types

str (ENV:PREFIX)
    Environment variables with the given prefix. The prefix is stripped and
    the remaining key is lowercased. Values are strings.
    Example: ``MYAPP_SERVER_HOST=x`` with ``'ENV:MYAPP'`` → ``{'server_host': 'x'}``

pathlib.Path
    Same as str file path, but as Path object.

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
        types={'server_port': int, 'server_debug': bool},   # explicit conversions
    )

    # Use with SmartOptions
    opts = SmartOptions(
        incoming={'server_port': 9999},  # runtime overrides (highest priority)
        defaults=defaults,
    )

    opts.server_host    # from file or env (string)
    opts.server_port    # 9999 (from incoming, int)

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

flatten_dict(data, separator)
    Flatten nested dict using separator.

load_ini(path)
    Load configuration from .ini file (values are strings).

load_json(path)
    Load configuration from .json file.

load_toml(path)
    Load configuration from .toml file.

load_yaml(path)
    Load configuration from .yaml file.

load_env(prefix)
    Load configuration from environment variables with prefix (values are strings).

load_file(path)
    Load configuration from file (auto-detect format from extension).
"""

from __future__ import annotations

import argparse
import inspect
import json
import os
import sys
from collections.abc import Callable, ItemsView, Iterator, KeysView, Mapping, ValuesView
from configparser import ConfigParser
from pathlib import Path
from typing import Annotated, Any, Union, get_args, get_origin

__all__ = [
    "MultiDefault",
    "flatten_dict",
    "load_ini",
    "load_json",
    "load_toml",
    "load_yaml",
    "load_env",
    "load_file",
    "load_argv",
    "extract_signature",
]

# -----------------------------------------------------------------------------
# Type Conversion Constants (used by MultiDefault._convert_value)
# -----------------------------------------------------------------------------

_BOOL_TRUE = frozenset({"true", "yes", "on", "1"})


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
    All values are returned as strings (use ``types`` parameter in
    ``MultiDefault`` for explicit type conversion).

    Args:
        path: Path to .ini file.

    Returns:
        Nested dictionary with sections as top-level keys. All values are strings.

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
        {'server': {'host': 'localhost', 'port': '8000'}, 'logging': {'level': 'INFO'}}
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
            result[section][key] = value

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
    else:  # pragma: no cover
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
    except ImportError:  # pragma: no cover
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
    3. Value is kept as string (use ``types`` in ``MultiDefault`` for conversion)

    Args:
        prefix: Environment variable prefix (without trailing underscore).

    Returns:
        Flat dictionary with lowercase keys. All values are strings.

    Examples:
        Given environment::

            MYAPP_SERVER_HOST=localhost
            MYAPP_SERVER_PORT=8000
            MYAPP_DEBUG=true
            OTHER_VAR=ignored

        >>> load_env('MYAPP')
        {'server_host': 'localhost', 'server_port': '8000', 'debug': 'true'}
    """
    prefix_with_underscore = f"{prefix}_"
    prefix_len = len(prefix_with_underscore)

    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if key.startswith(prefix_with_underscore):
            clean_key = key[prefix_len:].lower()
            result[clean_key] = value

    return result


# -----------------------------------------------------------------------------
# Signature Extraction and ARGV Loading
# -----------------------------------------------------------------------------


def _unwrap_annotated(annotation: Any) -> tuple[Any, str | None]:
    """
    Extract the actual type and help string from an Annotated type.

    Args:
        annotation: Type annotation, possibly Annotated[T, "help"].

    Returns:
        Tuple of (actual_type, help_string or None).

    Examples:
        >>> _unwrap_annotated(Annotated[int, "Port number"])
        (int, "Port number")
        >>> _unwrap_annotated(str)
        (str, None)
    """
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        actual_type = args[0]
        help_str = args[1] if len(args) > 1 and isinstance(args[1], str) else None
        return actual_type, help_str
    return annotation, None


def _is_optional(type_hint: Any) -> tuple[bool, Any]:
    """
    Check if a type hint is Optional (Union with None).

    Args:
        type_hint: Type annotation to check.

    Returns:
        Tuple of (is_optional, inner_type).

    Examples:
        >>> _is_optional(Union[str, None])
        (True, str)
        >>> _is_optional(str | None)
        (True, str)
        >>> _is_optional(str)
        (False, str)
    """
    import types

    origin = get_origin(type_hint)
    # Handle both typing.Union and types.UnionType (Python 3.10+ `X | Y` syntax)
    if origin is Union or isinstance(type_hint, types.UnionType):
        args = get_args(type_hint)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return True, non_none[0]
    return False, type_hint


def extract_signature(
    func: Callable[..., Any],
) -> tuple[dict[str, Any], dict[str, type], dict[str, str]]:
    """
    Extract defaults, types, and help strings from a callable's signature.

    Analyzes function parameters to extract:
    - Default values for each parameter
    - Type annotations (unwrapping Annotated if present)
    - Help strings from Annotated metadata

    Args:
        func: Callable with type annotations and default values.

    Returns:
        Tuple of (defaults_dict, types_dict, help_dict).

    Examples:
        >>> def cmd(host: Annotated[str, "Server host"] = "localhost",
        ...         port: Annotated[int, "Port"] = 8000):
        ...     pass
        >>> defaults, types, helps = extract_signature(cmd)
        >>> defaults
        {'host': 'localhost', 'port': 8000}
        >>> types
        {'host': str, 'port': int}
        >>> helps
        {'host': 'Server host', 'port': 'Port'}
    """
    from typing import get_type_hints

    sig = inspect.signature(func)
    defaults: dict[str, Any] = {}
    types: dict[str, type] = {}
    helps: dict[str, str] = {}

    # Get resolved type hints (handles "from __future__ import annotations")
    try:
        type_hints = get_type_hints(func, include_extras=True)
    except Exception:
        type_hints = {}

    for name, param in sig.parameters.items():
        # Skip *args and **kwargs
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        # Extract default value
        if param.default is not param.empty:
            defaults[name] = param.default

            # Extract type and help from resolved type hint
            if name in type_hints:
                annotation = type_hints[name]
                actual_type, help_str = _unwrap_annotated(annotation)

                # Handle Optional types
                is_opt, inner_type = _is_optional(actual_type)
                if is_opt:
                    actual_type = inner_type

                # Store type if it's a concrete type
                if isinstance(actual_type, type):
                    types[name] = actual_type

                # Store help string if present
                if help_str:
                    helps[name] = help_str

    return defaults, types, helps


def load_argv(
    defaults: dict[str, Any],
    types: dict[str, type],
    helps: dict[str, str],
    argv: list[str] | None = None,
) -> dict[str, Any]:
    """
    Parse command-line arguments based on extracted signature info.

    Creates an argparse.ArgumentParser based on the provided defaults,
    types, and help strings, then parses the given argv.

    Args:
        defaults: Default values for each argument.
        types: Type for each argument.
        helps: Help string for each argument.
        argv: Command-line arguments to parse (default: empty list).

    Returns:
        Dictionary with parsed argument values (only non-None values).

    Examples:
        >>> defaults = {'host': 'localhost', 'port': 8000}
        >>> types = {'host': str, 'port': int}
        >>> helps = {'host': 'Server host', 'port': 'Port number'}
        >>> load_argv(defaults, types, helps, ['--port', '9000'])
        {'port': 9000}
    """
    parser = argparse.ArgumentParser()

    # Track which names use --no-xxx form
    bool_inverted: set[str] = set()

    for name in defaults:
        arg_name = f"--{name.replace('_', '-')}"
        kwargs: dict[str, Any] = {}

        # Help string
        if name in helps:
            kwargs["help"] = helps[name]

        # Default value
        default = defaults.get(name)

        # Type handling
        type_cls = types.get(name)
        if type_cls is bool:
            # Boolean: use store_true or store_false based on default
            if default is True:
                kwargs["action"] = "store_false"
                kwargs["dest"] = name
                arg_name = f"--no-{name.replace('_', '-')}"
                bool_inverted.add(name)
            else:
                kwargs["action"] = "store_true"
        else:
            kwargs["default"] = None  # We use None to detect "not provided"
            if type_cls is not None:
                kwargs["type"] = type_cls

        parser.add_argument(arg_name, **kwargs)

    if argv is None:
        argv = []

    args = parser.parse_args(argv)

    # Return only values that were actually provided
    result: dict[str, Any] = {}
    for name in defaults:
        type_cls = types.get(name)
        value = getattr(args, name, None)

        if type_cls is bool:
            default = defaults.get(name)
            # For bools, check if the value differs from default
            if value != default:
                result[name] = value
        elif value is not None:
            result[name] = value

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
            - callable: Extract defaults and types from function signature
            - dict: Used directly (flattened if nested)
            - str (file path): Load from file (.ini, .json, .toml, .yaml)
            - str "ENV:PREFIX": Load from environment variables with prefix
            - str "ARGV:": Parse sys.argv using signature from callable source
            - pathlib.Path: Load from file

        skip_missing: If True, silently skip missing files instead of raising
            FileNotFoundError. Default: False.

        types: Optional dict mapping keys to types for explicit conversion.
            When specified, values for these keys are converted to the given
            type instead of using auto_convert heuristics. This is useful for
            values that should remain strings (e.g., "00123") or for explicit
            type control. Note: if a callable source is provided, its types
            are automatically merged with this parameter.

    Attributes:
        sources: Tuple of original source specifications.
        skip_missing: Whether missing files are skipped.
        types: Type conversion map.

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

        With explicit types::

            defaults = MultiDefault(
                'config.ini',
                'ENV:MYAPP',
                types={
                    'server_port': int,
                    'server_debug': bool,
                    'version': str,  # Keep "1.0.0" as string
                }
            )

        With callable and ARGV::

            def cmd_serve(
                host: Annotated[str, "Server host"] = "127.0.0.1",
                port: Annotated[int, "Server port"] = 8000,
                debug: Annotated[bool, "Enable debug"] = False,
            ) -> int:
                ...

            defaults = MultiDefault(
                cmd_serve,        # defaults + types from signature
                'config.toml',    # file overrides
                'ENV:MYAPP',      # env overrides
                'ARGV:',          # CLI overrides (uses signature for argparse)
            )
    """

    def __init__(
        self,
        *sources: Any,
        skip_missing: bool = False,
        types: dict[str, type] | None = None,
    ):
        self._sources = sources
        self._skip_missing = skip_missing
        self._types = dict(types) if types else {}
        self._resolved: dict[str, Any] | None = None

        # Extract signature info from callable source (if any)
        self._sig_defaults: dict[str, Any] = {}
        self._sig_types: dict[str, type] = {}
        self._sig_helps: dict[str, str] = {}
        self._has_callable = False

        for source in sources:
            if callable(source) and not isinstance(source, type):
                if self._has_callable:
                    raise ValueError("Only one callable source is allowed")
                self._has_callable = True
                self._sig_defaults, self._sig_types, self._sig_helps = (
                    extract_signature(source)
                )
                # Merge callable types with explicit types (explicit wins)
                merged_types = dict(self._sig_types)
                merged_types.update(self._types)
                self._types = merged_types

        # Validate ARGV: requires a callable
        for source in sources:
            if isinstance(source, str) and source.startswith("ARGV:"):
                if not self._has_callable:
                    raise ValueError(
                        "ARGV: source requires a callable source for signature"
                    )

    @property
    def sources(self) -> tuple[Any, ...]:
        """Original source specifications."""
        return self._sources

    @property
    def skip_missing(self) -> bool:
        """Whether missing files are skipped."""
        return self._skip_missing

    @property
    def types(self) -> dict[str, type]:
        """Type conversion map."""
        return self._types

    def resolve(self) -> dict[str, Any]:
        """
        Resolve all sources and return merged flat dictionary.

        Sources are processed in order, with later sources overriding
        earlier ones. Nested dictionaries are flattened with "_" separator.

        If ``types`` was provided, values for those keys are converted
        to the specified type instead of using auto_convert heuristics.

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

        # Apply explicit type conversions
        if self._types:
            for key, type_cls in self._types.items():
                if key in result:
                    result[key] = self._convert_value(result[key], type_cls)

        self._resolved = result
        return result

    def _convert_value(self, value: Any, type_cls: type) -> Any:
        """
        Convert a value to the specified type.

        Args:
            value: Value to convert.
            type_cls: Target type (int, float, bool, str, etc.).

        Returns:
            Converted value, or original value if conversion fails.
        """
        # Already correct type or None
        if value is None or isinstance(value, type_cls):
            return value

        try:
            # Special handling for bool from string
            if type_cls is bool and isinstance(value, str):
                return value.lower() in _BOOL_TRUE
            return type_cls(value)
        except (ValueError, TypeError):
            # Keep original value if conversion fails
            return value

    def _load_source(self, source: Any) -> dict[str, Any]:
        """
        Load configuration from a single source.

        Args:
            source: Source specification (callable, dict, str, Path).

        Returns:
            Dictionary loaded from source.

        Raises:
            FileNotFoundError: If file source doesn't exist.
            ValueError: If source type is not recognized.
        """
        # Callable: return extracted defaults
        if callable(source) and not isinstance(source, type):
            return self._sig_defaults

        # Dict: use directly
        if isinstance(source, dict):
            return source

        # Path: load from file
        if isinstance(source, Path):
            return load_file(source)

        # String: could be file path, ENV:PREFIX, or ARGV:
        if isinstance(source, str):
            if source.startswith("ENV:"):
                prefix = source[4:]  # Remove "ENV:" prefix
                return load_env(prefix)
            elif source.startswith("ARGV:"):
                return load_argv(
                    self._sig_defaults,
                    self._sig_types,
                    self._sig_helps,
                )
            else:
                return load_file(source)

        raise ValueError(
            f"Unsupported source type: {type(source).__name__}. "
            f"Expected callable, dict, str, or Path."
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
        parts = [sources_repr, f"skip_missing={self._skip_missing}"]
        if self._types:
            parts.append(f"types={self._types!r}")
        return f"MultiDefault({', '.join(parts)})"
