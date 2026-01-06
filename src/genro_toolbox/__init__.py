"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.4.0"

from .ascii_table import render_ascii_table, render_markdown_table
from .decorators import extract_kwargs
from .dict_utils import SmartOptions, dictExtract
from .smartasync import SmartLock, smartasync, smartawait
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
    "smartsplit",
]
