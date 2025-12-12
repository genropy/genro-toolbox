"""
Dictionary utilities for Genro-Toolbox.

Provides utilities for dict manipulation used across the library.
"""

from collections.abc import Callable, Mapping
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def filtered_dict(
    data: Mapping[str, Any] | None,
    filter_fn: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any]:
    """
    Return a dict filtered through ``filter_fn``.

    Args:
        data: Mapping with the original values (can be None).
        filter_fn: Optional callable receiving ``(key, value)`` and returning
            True if the pair should be kept. When None, the mapping is copied.
    """
    if not data:
        return {}
    if filter_fn is None:
        return dict(data)
    return {k: v for k, v in data.items() if filter_fn(k, v)}


def make_opts(
    incoming: Mapping[str, Any] | None,
    defaults: Mapping[str, Any] | None = None,
    *,
    filter_fn: Callable[[str, Any], bool] | None = None,
    ignore_none: bool = False,
    ignore_empty: bool = False,
) -> SimpleNamespace:
    """
    Merge ``incoming`` kwargs with ``defaults`` and return a SimpleNamespace.

    ``incoming`` values override defaults after optional filtering steps.
    """
    merged_dict = _merge_kwargs(
        incoming,
        defaults,
        filter_fn=filter_fn,
        ignore_none=ignore_none,
        ignore_empty=ignore_empty,
    )
    return SimpleNamespace(**merged_dict)


def _merge_kwargs(
    incoming: Mapping[str, Any] | None,
    defaults: Mapping[str, Any] | None,
    *,
    filter_fn: Callable[[str, Any], bool] | None = None,
    ignore_none: bool = False,
    ignore_empty: bool = False,
) -> dict[str, Any]:
    combined_filter = _compose_filter(filter_fn, ignore_none, ignore_empty)
    merged_defaults = dict(defaults or {})
    filtered_incoming = filtered_dict(incoming, combined_filter)
    return merged_defaults | filtered_incoming


def _compose_filter(
    filter_fn: Callable[[str, Any], bool] | None,
    ignore_none: bool,
    ignore_empty: bool,
) -> Callable[[str, Any], bool] | None:
    if not (filter_fn or ignore_none or ignore_empty):
        return None

    def predicate(key: str, value: Any) -> bool:
        if ignore_none and value is None:
            return False
        if ignore_empty and _is_empty_value(value):
            return False
        if filter_fn and not filter_fn(key, value):
            return False
        return True

    return predicate


def _is_empty_value(value: Any) -> bool:
    """Return True for values considered 'empty'."""
    empty_sequences = (str, bytes, list, tuple, dict, set, frozenset)
    if isinstance(value, empty_sequences):
        return len(value) == 0
    return False


def _load_from_callable(
    func: Callable[..., Any], argv: list[str] | None = None
) -> dict[str, Any]:
    """Extract defaults from callable signature and parse argv."""
    import inspect

    sig = inspect.signature(func)
    result = {}
    types = {}
    positional_params = []

    # Extract defaults and types from signature
    for name, param in sig.parameters.items():
        if param.default is not inspect.Parameter.empty:
            result[name] = param.default
        else:
            positional_params.append(name)

        # Extract type from annotation
        if param.annotation is not inspect.Parameter.empty:
            ann = param.annotation
            # Handle Annotated types
            if hasattr(ann, "__origin__") and ann.__origin__ is type(None):
                continue
            if hasattr(ann, "__metadata__"):  # Annotated type
                ann = ann.__args__[0]
            if ann in (str, int, float, bool):
                types[name] = ann

    # Parse argv if provided
    if argv is not None:
        result = _parse_argv(argv, result, types, positional_params)

    return result


def _parse_argv(
    argv: list[str],
    defaults: dict[str, Any],
    types: dict[str, type],
    positional_params: list[str],
) -> dict[str, Any]:
    """Parse argv into a dict using defaults and types."""
    result = dict(defaults)
    positional_index = 0
    i = 0

    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            # Check if it's a boolean flag
            if key in types and types[key] is bool:
                result[key] = True
            elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                value = argv[i + 1]
                if key in types:
                    value = types[key](value)
                result[key] = value
                i += 1
        else:
            # Positional argument
            if positional_index < len(positional_params):
                key = positional_params[positional_index]
                value = arg
                if key in types:
                    value = types[key](value)
                result[key] = value
                positional_index += 1
        i += 1

    return result


def _load_env(prefix: str) -> dict[str, Any]:
    """Load config from environment variables with given prefix."""
    import os

    prefix_upper = prefix.upper() + "_"
    result = {}
    for key, value in os.environ.items():
        if key.startswith(prefix_upper):
            # Remove prefix and convert to lowercase
            clean_key = key[len(prefix_upper) :].lower()
            result[clean_key] = value
    return result


def _load_config_file(path: str | Path) -> dict[str, Any]:
    """Load config from file based on extension. Returns {} if file doesn't exist."""
    path = Path(path)
    if not path.exists():
        return {}
    suffix = path.suffix.lower()

    if suffix == ".yaml" or suffix == ".yml":
        import yaml

        with open(path) as f:
            return yaml.safe_load(f) or {}
    elif suffix == ".json":
        import json

        with open(path) as f:
            return json.load(f)
    elif suffix == ".toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[import-not-found]
        with open(path, "rb") as f:
            return tomllib.load(f)
    elif suffix == ".ini":
        import configparser

        parser = configparser.ConfigParser()
        parser.read(path)
        return {
            f"{section}_{key}": value
            for section in parser.sections()
            for key, value in parser.items(section)
        }
    else:
        raise ValueError(f"Unsupported config file format: {suffix}")


def _wrap_nested_dicts(data: dict[str, Any]) -> dict[str, Any]:
    """Wrap nested dicts and string lists in SmartOptions recursively.

    - Nested dicts become SmartOptions
    - String lists become SmartOptions with boolean values (feature flags)
    - Lists of dicts are indexed by first key of first element
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = SmartOptions(value)
        elif isinstance(value, list) and value:
            if all(isinstance(x, str) for x in value):
                # String list -> feature flags
                result[key] = SmartOptions({x: True for x in value})
            elif all(isinstance(x, dict) for x in value):
                # List of dicts -> index by first key of first element
                result[key] = _index_list_of_dicts(value)
            else:
                result[key] = value
        else:
            result[key] = value
    return result


def _index_list_of_dicts(items: list[dict[str, Any]]) -> "SmartOptions":
    """Convert list of dicts to SmartOptions indexed by first key value."""
    if not items or not items[0]:
        return SmartOptions({})

    # Get the first key from first element as index key
    index_key = next(iter(items[0].keys()))

    indexed = {}
    for item in items:
        if index_key in item:
            key_value = item[index_key]
            indexed[key_value] = SmartOptions(item)

    return SmartOptions(indexed)


class SmartOptions(SimpleNamespace):
    """
    Convenience namespace for option management.

    Args:
        incoming: Mapping with runtime kwargs, or a file path (str/Path) to load.
        defaults: Mapping with baseline options.
        ignore_none: Skip incoming entries where the value is ``None``.
        ignore_empty: Skip empty strings/collections from incoming entries.
        filter_fn: Optional callable receiving ``(key, value)`` and returning
            True if the pair should be kept.

    If incoming is a string or Path and defaults is None, loads config from file.
    Nested dicts are recursively wrapped in SmartOptions.
    """

    def __init__(
        self,
        incoming: Mapping[str, Any] | str | Path | Callable[..., Any] | None = None,
        defaults: Mapping[str, Any] | list[str] | None = None,
        *,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Callable[[str, Any], bool] | None = None,
    ):
        # If incoming is callable, defaults is argv (list)
        if callable(incoming) and not isinstance(incoming, type):
            argv = defaults if isinstance(defaults, list) else None
            incoming = _load_from_callable(incoming, argv)
            defaults = None
        # If incoming is a string, detect source type
        elif isinstance(incoming, str) and defaults is None:
            if incoming.startswith("ENV:"):
                incoming = _load_env(incoming[4:])
            else:
                incoming = _load_config_file(incoming)
        elif isinstance(incoming, Path) and defaults is None:
            incoming = _load_config_file(incoming)

        merged = _merge_kwargs(
            incoming,
            defaults,
            filter_fn=filter_fn,
            ignore_none=ignore_none,
            ignore_empty=ignore_empty,
        )

        # Wrap nested dicts recursively
        merged = _wrap_nested_dicts(merged)

        object.__setattr__(self, "_data", dict(merged))
        super().__init__(**merged)

    def as_dict(self) -> dict[str, Any]:
        """Return a copy of current options."""
        return dict(self._data)

    def __setattr__(self, key: str, value: Any):
        if key == "_data":
            object.__setattr__(self, key, value)
            return
        self._data[key] = value
        super().__setattr__(key, value)

    def __delattr__(self, key: str):
        if key == "_data":
            raise AttributeError("_data attribute cannot be removed")
        self._data.pop(key, None)
        super().__delattr__(key)

    def __add__(self, other: "SmartOptions | Mapping[str, Any]") -> "SmartOptions":
        """Merge two SmartOptions. Right side overrides left side."""
        if isinstance(other, SmartOptions):
            other_data = other._data
        else:
            other_data = dict(other)
        merged = self._data | other_data
        return SmartOptions(merged)

    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self._data

    def __iter__(self):
        """Iterate over keys."""
        return iter(self._data)

    def __getattr__(self, key: str) -> Any:
        """Return None for missing keys instead of raising AttributeError."""
        if key.startswith("_"):
            raise AttributeError(key)
        return self._data.get(key)

    def __getitem__(self, key: str) -> Any:
        """Access by key with bracket notation."""
        return self._data.get(key)


def dictExtract(mydict, prefix, pop=False, slice_prefix=True, is_list=False):
    """Return a dict of the items with keys starting with prefix.

    :param mydict: sourcedict
    :param prefix: the prefix of the items you need to extract
    :param pop: removes the items from the sourcedict
    :param slice_prefix: shortens the keys of the output dict removing the prefix
    :param is_list: reserved for future use (currently not used)
    :returns: a dict of the items with keys starting with prefix"""

    # FIXME: the is_list parameter is never used.

    lprefix = len(prefix) if slice_prefix else 0

    cb = mydict.pop if pop else mydict.get
    reserved_names = ["class"]
    return dict(
        [
            (
                k[lprefix:] if k[lprefix:] not in reserved_names else f"_{k[lprefix:]}",
                cb(k),
            )
            for k in list(mydict.keys())
            if k.startswith(prefix)
        ]
    )
