"""
Dictionary utilities for Genro-Toolbox.

Provides utilities for dict manipulation used across the library.
"""

from collections.abc import Callable, Mapping
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


class SmartOptions(SimpleNamespace):
    """
    Convenience namespace for option management.

    Args:
        incoming: Mapping with runtime kwargs.
        defaults: Mapping with baseline options.
        ignore_none: Skip incoming entries where the value is ``None``.
        ignore_empty: Skip empty strings/collections from incoming entries.
    """

    def __init__(
        self,
        incoming: Mapping[str, Any] | None = None,
        defaults: Mapping[str, Any] | None = None,
        *,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Callable[[str, Any], bool] | None = None,
    ):
        merged = _merge_kwargs(
            incoming,
            defaults,
            filter_fn=filter_fn,
            ignore_none=ignore_none,
            ignore_empty=ignore_empty,
        )
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
            (k[lprefix:] if k[lprefix:] not in reserved_names else f"_{k[lprefix:]}", cb(k))
            for k in list(mydict.keys())
            if k.startswith(prefix)
        ]
    )
