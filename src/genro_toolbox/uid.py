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

# Epoch: 2025-01-01 00:00:00 UTC in microseconds
_EPOCH_US = 1735689600_000_000


def get_uuid() -> str:
    """Generate a 22-char sortable unique ID (Z + 9-char base62 timestamp + 12-char base62 random)."""
    # Timestamp part: 9 chars in base62 (µs since 2025-01-01 UTC)
    ts = int(time.time() * 1_000_000) - _EPOCH_US
    ts_part = ""
    for _ in range(9):
        ts_part = _ALPHABET[ts % 62] + ts_part
        ts //= 62

    # Random part: 12 chars in base62 (~71 bits entropy)
    rand_bytes = os.urandom(9)  # 72 bits
    val = int.from_bytes(rand_bytes, "big")
    rand_part = ""
    for _ in range(12):
        rand_part += _ALPHABET[val % 62]
        val //= 62

    return "Z" + ts_part + rand_part
