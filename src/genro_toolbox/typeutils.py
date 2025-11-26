"""
Utilities for checking whether an object is an instance of a class
identified only by its full class path (module.ClassName),
without importing the target class.

This avoids circular imports and still behaves like ``isinstance``,
including subclass recognition.

Example:
    safe_is_instance(obj, "mypackage.models.BaseNode")
"""

from functools import lru_cache
from typing import Any


@lru_cache(maxsize=None)
def _mro_fullnames(cls: type) -> set[str]:
    """
    Return a set of fully qualified class names (module.ClassName)
    for all classes in the MRO of ``cls``.

    Cached for performance.
    """
    return {f"{c.__module__}.{c.__qualname__}" for c in cls.__mro__}


def safe_is_instance(obj: Any, class_full_name: str) -> bool:
    """
    Return True if ``obj`` is an instance of the class identified by
    ``class_full_name`` or any of its subclasses — without importing
    the class.

    Args:
        obj: The object to check.
        class_full_name: The fully qualified class name,
            e.g. ``"mypkg.models.BaseNode"``.
    """
    return class_full_name in _mro_fullnames(obj.__class__)
