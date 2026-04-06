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


def get_uuid() -> str:
    """Generate a 22-char sortable unique ID (Z + 9-char base62 timestamp + 12-char base62 random)."""
    # Timestamp part
    ts = int(time.time() * 1_000_000) - _EPOCH_US
    ts_part = ""
    for _ in range(_TIMESTAMP_LENGTH):
        ts_part = _ALPHABET[ts % _BASE] + ts_part
        ts //= _BASE

    # Random part
    rand_bytes = os.urandom(_RANDOM_BYTES)
    val = int.from_bytes(rand_bytes, "big")
    rand_part = ""
    for _ in range(_RANDOM_LENGTH):
        rand_part += _ALPHABET[val % _BASE]
        val //= _BASE

    return "Z" + ts_part + rand_part
