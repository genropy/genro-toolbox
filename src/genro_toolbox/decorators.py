"""
Decorators for Genro-Toolbox.

Provides utilities for extracting and grouping keyword arguments.
"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from .dict_utils import dictExtract

F = TypeVar("F", bound=Callable[..., Any])

# Constants to avoid recreating dicts
_DEFAULT_EXTRACT_OPTIONS = {"slice_prefix": True, "pop": False, "is_list": False}
_POP_EXTRACT_OPTIONS = {"slice_prefix": True, "pop": True, "is_list": False}


def extract_kwargs(
    _adapter: str | None = None,
    _dictkwargs: dict[str, Any] | None = None,
    **extraction_specs: Any,
) -> Callable[[F], F]:
    """A decorator that extracts ``**kwargs`` into sub-families by prefix.

    This decorator allows methods to accept kwargs with prefixes (e.g., `logging_level`,
    `cache_ttl`) and automatically groups them into separate kwargs dictionaries
    (e.g., `logging_kwargs`, `cache_kwargs`).

    Args:
        _adapter: Optional name of a method on self that will pre-process kwargs.
                 The adapter method receives kwargs dict and can modify it in-place.
        _dictkwargs: Optional dict to use instead of ``**extraction_specs``.
                    Useful for dynamic extraction specifications.
        **extraction_specs: Extraction specifications where keys are prefix names.
                          Values can be:
                          - True: Extract and remove (pop=True)
                          - dict: Custom options (slice_prefix, pop, is_list)

    Returns:
        Decorated function that extracts kwargs by prefix.

    Example:
        >>> @extract_kwargs(palette=True, dialog=True, default=True)
        ... def my_method(self, pane, table=None,
        ...              palette_kwargs=None, dialog_kwargs=None, default_kwargs=None,
        ...              **kwargs):
        ...     pass
        ...
        >>> # Call with prefixed parameters
        >>> obj.my_method(palette_height='200px', palette_width='300px',
        ...              dialog_height='250px')
        >>> # palette_kwargs={'height': '200px', 'width': '300px'}
        >>> # dialog_kwargs={'height': '250px'}

    Notes:
        - The decorated function MUST have `{prefix}_kwargs` parameters for each prefix
        - Reserved keyword 'class' is automatically renamed to '_class'
        - Works with both class methods (with self) and standalone functions
        - Maintains 100% compatibility with original Genropy implementation
    """
    # Use _dictkwargs if provided, otherwise use extraction_specs
    # Note: We use a different variable name to avoid shadowing the parameter
    specs_to_use = _dictkwargs if _dictkwargs is not None else extraction_specs

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Check if this is a method (has self) or function
            # For methods: self is args[0]
            # For functions: no self
            has_self = len(args) > 0 and hasattr(args[0].__class__, func.__name__)
            self_arg = args[0] if has_self else None

            # Call adapter if specified and this is a method
            if _adapter and self_arg is not None:
                adapter_method = getattr(self_arg, _adapter, None)
                if adapter_method is not None:
                    adapter_method(kwargs)

            # Process each extraction specification
            for extract_key, extract_value in specs_to_use.items():
                grp_key = f"{extract_key}_kwargs"

                # Get existing grouped kwargs (if explicitly passed)
                current = kwargs.pop(grp_key, None)
                if current is None:
                    current = {}
                elif not isinstance(current, dict):
                    # Edge case: someone passed non-dict, convert to dict
                    current = {}

                # Determine extraction options based on extract_value
                if extract_value is True:
                    # True means: extract and remove from source
                    extract_options = _POP_EXTRACT_OPTIONS
                elif isinstance(extract_value, dict):
                    # Dict means: custom options
                    extract_options = {**_DEFAULT_EXTRACT_OPTIONS, **extract_value}
                else:
                    # Default: extract but don't remove from source
                    extract_options = _DEFAULT_EXTRACT_OPTIONS

                # Extract prefixed kwargs
                prefix = f"{extract_key}_"
                extracted = dictExtract(kwargs, prefix, **extract_options)

                # Merge extracted kwargs with current
                current.update(extracted)

                # Set the grouped kwargs back
                # Always set as dict (never None), matching original behavior
                kwargs[grp_key] = current

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
