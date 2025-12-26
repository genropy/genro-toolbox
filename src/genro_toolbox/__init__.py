"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.3.0"

from .decorators import extract_kwargs
from .dict_utils import SmartOptions, dictExtract
from .typeutils import safe_is_instance
from .ascii_table import render_ascii_table, render_markdown_table
from .tags_match import tags_match, RuleError
from .treedict import TreeDict

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
]
