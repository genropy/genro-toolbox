# Copyright 2025 Softwell S.r.l. - SPDX-License-Identifier: Apache-2.0
"""String utilities for Genro framework."""

from __future__ import annotations

_ESCAPE_PLACEHOLDER = chr(1)


def smartsplit(path: str, separator: str) -> list[str]:
    """Split a string by separator, ignoring escaped occurrences."""
    escape = "\\" + separator
    has_escape = escape in path
    if has_escape:
        path = path.replace(escape, _ESCAPE_PLACEHOLDER)
    path_list = [x.strip() for x in path.split(separator)]
    if has_escape:
        path_list = [x.replace(_ESCAPE_PLACEHOLDER, escape) for x in path_list]
    return path_list
