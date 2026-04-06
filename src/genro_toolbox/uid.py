# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Unique identifier generation utilities for Genro.

Provides sortable, URL-safe unique identifiers suitable for database
primary keys, session IDs, and other uses across distributed systems.
"""

import os
import time

# Base62 alphabet (sortable: 0-9, A-Z, a-z)
_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_BASE = len(_ALPHABET)

# Epoch: 2025-01-01 00:00:00 UTC in microseconds
_EPOCH_US = 1735689600_000_000

_TIMESTAMP_LENGTH = 9
_RANDOM_LENGTH = 12
_RANDOM_BYTES = 9  # 72 bits entropy for 12 base62 chars


def _encode_base62(value: int, length: int) -> str:
    """Encode an integer as a fixed-width base62 string (big-endian)."""
    result = ""
    for _ in range(length):
        result = _ALPHABET[value % _BASE] + result
        value //= _BASE
    return result


def get_uuid() -> str:
    """Generate a 22-char sortable unique ID (Z + 9-char base62 timestamp + 12-char base62 random)."""
    ts = int(time.time() * 1_000_000) - _EPOCH_US
    ts_part = _encode_base62(ts, _TIMESTAMP_LENGTH)
    rand_val = int.from_bytes(os.urandom(_RANDOM_BYTES), "big")
    rand_part = _encode_base62(rand_val, _RANDOM_LENGTH)
    return "Z" + ts_part + rand_part
