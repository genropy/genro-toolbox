# Copyright 2025 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""String utilities for Genro framework."""

from __future__ import annotations


def smartsplit(path: str, separator: str) -> list[str]:
    """Split a string by separator, ignoring escaped occurrences."""
    escape = "\\" + separator
    has_escape = escape in path
    if has_escape:
        path = path.replace(escape, chr(1))
    path_list = [x.strip() for x in path.split(separator)]
    if has_escape:
        path_list = [x.replace(chr(1), escape) for x in path_list]
    return path_list
