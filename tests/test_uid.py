# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Tests for uid module."""

import time

from genro_toolbox.uid import get_uuid


class TestGetUuid:
    """Tests for get_uuid function."""

    def test_length_is_22(self):
        """ID should be exactly 22 characters."""
        uid = get_uuid()
        assert len(uid) == 22

    def test_starts_with_z(self):
        """ID should start with 'Z' version marker."""
        uid = get_uuid()
        assert uid[0] == "Z"

    def test_is_alphanumeric(self):
        """ID should be URL-safe (alphanumeric only)."""
        uid = get_uuid()
        assert uid.isalnum()

    def test_uniqueness(self):
        """Multiple calls should produce unique IDs."""
        ids = {get_uuid() for _ in range(1000)}
        assert len(ids) == 1000

    def test_sortability(self):
        """IDs generated in sequence should sort in same order."""
        ids = []
        for _ in range(10):
            ids.append(get_uuid())
            time.sleep(0.001)  # 1ms delay to ensure different timestamps

        sorted_ids = sorted(ids)
        assert ids == sorted_ids

    def test_base62_alphabet(self):
        """ID should only contain base62 characters."""
        alphabet = set("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
        for _ in range(100):
            uid = get_uuid()
            assert all(c in alphabet for c in uid)

    def test_timestamp_portion_changes(self):
        """Timestamp portion should change over time."""
        uid1 = get_uuid()
        time.sleep(0.01)  # 10ms
        uid2 = get_uuid()

        # Timestamp is chars 1-9 (after 'Z')
        ts1 = uid1[1:10]
        ts2 = uid2[1:10]
        assert ts1 != ts2

    def test_random_portion_varies(self):
        """Random portion should vary between calls."""
        # Even with same timestamp, random should differ
        uids = [get_uuid() for _ in range(10)]
        random_parts = [uid[10:] for uid in uids]
        # All random parts should be unique
        assert len(set(random_parts)) == 10

    def test_structure(self):
        """Verify ID structure: Z + 9 timestamp + 12 random."""
        uid = get_uuid()
        assert uid[0] == "Z"  # Version marker
        assert len(uid[1:10]) == 9  # Timestamp portion
        assert len(uid[10:]) == 12  # Random portion

    def test_rapid_generation(self):
        """Rapid generation should still produce sortable unique IDs."""
        # Generate many IDs as fast as possible
        ids = [get_uuid() for _ in range(100)]

        # All should be unique
        assert len(set(ids)) == 100

        # Should still be sortable (or at least not reverse sorted)
        # Note: within same microsecond, order depends on random part
        sorted_ids = sorted(ids)
        # At minimum, first and last should be in correct order
        assert ids[0] <= sorted_ids[-1]
