"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.5.1"

from .ascii_table import render_ascii_table, render_markdown_table
from .decorators import extract_kwargs
from .dict_utils import SmartOptions, dictExtract
from .smartasync import SmartLock, reset_smartasync_cache, smartasync, smartawait
from .string_utils import smartsplit
from .tags_match import RuleError, tags_match
from .treedict import TreeDict
from .typeutils import safe_is_instance
from .uid import get_uuid

__all__ = [
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
    "SmartLock",
    "reset_smartasync_cache",
    "smartsplit",
]
