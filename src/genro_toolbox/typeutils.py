"""Import-free isinstance check using a fully-qualified class name string."""

from functools import cache
from typing import Any


@cache
def _mro_fullnames(cls: type) -> set[str]:
    """
    Return a set of fully qualified class names (module.ClassName)
    for all classes in the MRO of ``cls``.

    Cached for performance.
    """
    return {f"{c.__module__}.{c.__qualname__}" for c in cls.__mro__}


def safe_is_instance(obj: Any, class_full_name: str) -> bool:
    """Return True if obj is an instance of class_full_name (checked via MRO, no import)."""
    return class_full_name in _mro_fullnames(obj.__class__)


def is_awaitable(value: Any) -> bool:
    """Return True if *value* is awaitable (has an __await__ method)."""
    return hasattr(value, "__await__")
