"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.8.1"

from .ascii_table import render_ascii_table, render_markdown_table
from .decorators import extract_kwargs
from .dict_utils import DictObj, SmartOptions, dictExtract
from .smartasync import (
    SmartLock,
    is_async_context,
    reset_smartasync_cache,
    smartasync,
    smartawait,
    smartcontinuation,
)
from .pantry import Pantry
from .smarttimer import cancel_timer, set_interval, set_timeout
from .string_utils import smartsplit
from .tags_match import RuleError, tags_match
from .treedict import TreeDict
from .typeutils import safe_is_instance
from .uid import get_uuid

__all__ = [
    "DictObj",
    "extract_kwargs",
    "SmartOptions",
    "dictExtract",
    "safe_is_instance",
    "render_ascii_table",
    "render_markdown_table",
    "tags_match",
    "RuleError",
    "TreeDict",
    "get_uuid",
    "smartasync",
    "smartawait",
    "smartcontinuation",
    "SmartLock",
    "reset_smartasync_cache",
    "is_async_context",
    "smartsplit",
    "set_timeout",
    "set_interval",
    "cancel_timer",
    "pantry",
    "Pantry",
]

pantry = Pantry()
