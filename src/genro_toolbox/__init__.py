"""
Genro-Toolbox - Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities.
"""

__version__ = "0.1.0"

from .decorators import extract_kwargs
from .dict_utils import SmartOptions, dictExtract
from .multi_default import MultiDefault
from .typeutils import safe_is_instance
from .ascii_table import render_ascii_table, render_markdown_table
from .xml_utils import dict_to_xml, xml_to_dict
from . import types

__all__ = [
    "extract_kwargs",
    "SmartOptions",
    "dictExtract",
    "MultiDefault",
    "safe_is_instance",
    "render_ascii_table",
    "render_markdown_table",
    "types",
    "dict_to_xml",
    "xml_to_dict",
]
