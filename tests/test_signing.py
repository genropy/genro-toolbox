# Copyright 2025 Softwell S.r.l. - Genropy Team
# SPDX-License-Identifier: Apache-2.0

"""Tests for signing module."""

import json
import time

import pytest

from genro_toolbox.signing import (
    SignatureError,
    SignatureExpired,
    sign,
    verify,
)

KEY = "server-side-secret"
OTHER_KEY = "a-different-secret"


class TestRoundTrip:
    """A signed payload comes back unchanged."""

    def test_payload_survives(self):
        assert verify(sign("hello", KEY), KEY) == "hello"

    def test_empty_payload(self):
        assert verify(sign("", KEY), KEY) == ""

    def test_payload_containing_the_separator(self):
        """Separator inside the payload must not truncate it."""
        payload = json.dumps({"exclude": "*.tmp.*.bak", "path": "/srv"})
        assert verify(sign(payload, KEY), KEY) == payload

    def test_payload_with_many_separators(self):
        payload = "." * 50
        assert verify(sign(payload, KEY), KEY) == payload

    def test_unicode_payload(self):
        payload = "città — naïve 日本語 🎉"
        assert verify(sign(payload, KEY), KEY) == payload

    def test_json_resolver_payload(self):
        """The genro-bag use case: a serialized resolver."""
        payload = json.dumps(
            {
                "resolver_module": "genro_bag.resolvers.directory_resolver",
                "resolver_class": "DirectoryResolver",
                "args": ["/srv/data"],
                "kwargs": {"exclude": "*.tmp.*.bak"},
            }
        )
        assert verify(sign(payload, KEY), KEY) == payload


class TestTampering:
    """Any change to the token is rejected."""

    def test_wrong_key(self):
        token = sign("hello", KEY)
        with pytest.raises(SignatureError):
            verify(token, OTHER_KEY)

    def test_altered_payload(self):
        """Re-encoding a different payload keeps the original signature."""
        from genro_toolbox.signing import _b64_encode

        token = sign("/srv/data", KEY)
        _, expiry, signature = token.split(".")
        forged = f"{_b64_encode(b'/etc')}.{expiry}.{signature}"
        with pytest.raises(SignatureError):
            verify(forged, KEY)

    def test_altered_signature(self):
        token = sign("hello", KEY)
        with pytest.raises(SignatureError):
            verify(token[:-1] + ("A" if token[-1] != "A" else "B"), KEY)

    def test_stripped_expiry(self):
        """Dropping the expiry to make a token permanent must fail."""
        token = sign("hello", KEY, expires_in=60)
        payload, _, signature = token.split(".")
        with pytest.raises(SignatureError):
            verify(f"{payload}..{signature}", KEY)

    def test_no_separator(self):
        with pytest.raises(SignatureError):
            verify("garbage", KEY)

    def test_only_one_separator(self):
        with pytest.raises(SignatureError):
            verify("garbage.more", KEY)


class TestExpiry:
    """Expiry lives inside the signed area and is always enforced."""

    def test_valid_before_expiry(self):
        assert verify(sign("hello", KEY, expires_in=60), KEY) == "hello"

    def test_rejected_after_expiry(self):
        token = sign("hello", KEY, expires_in=1)
        time.sleep(1.1)
        with pytest.raises(SignatureExpired):
            verify(token, KEY)

    def test_expired_is_a_signature_error(self):
        """SignatureExpired subclasses SignatureError, so one except catches both."""
        token = sign("hello", KEY, expires_in=1)
        time.sleep(1.1)
        with pytest.raises(SignatureError):
            verify(token, KEY)

    def test_no_expiry_never_expires(self):
        assert verify(sign("hello", KEY), KEY) == "hello"

    def test_non_numeric_expiry_is_refused(self):
        """A non-numeric expiry must fail, not silently skip the check."""
        from genro_toolbox.signing import _b64_encode, _signature

        payload = _b64_encode(b"hello")
        expiry = _b64_encode(b"2020-01-01")
        signed_part = f"{payload}.{expiry}"
        token = f"{signed_part}.{_signature(signed_part, KEY)}"
        with pytest.raises(SignatureError):
            verify(token, KEY)

    def test_zero_expires_in_refused(self):
        with pytest.raises(ValueError):
            sign("hello", KEY, expires_in=0)

    def test_negative_expires_in_refused(self):
        with pytest.raises(ValueError):
            sign("hello", KEY, expires_in=-60)


class TestKeyRequired:
    """An empty key would make the signature meaningless."""

    def test_sign_without_key(self):
        with pytest.raises(ValueError):
            sign("hello", "")

    def test_verify_without_key(self):
        with pytest.raises(ValueError):
            verify(sign("hello", KEY), "")


class TestTokenShape:
    """The wire format is three base64url fields."""

    def test_three_fields(self):
        assert len(sign("hello", KEY).split(".")) == 3

    def test_three_fields_with_expiry(self):
        assert len(sign("hello", KEY, expires_in=60).split(".")) == 3

    def test_url_safe(self):
        """No character needing escaping in a URL or an XML attribute."""
        token = sign("città — naïve 日本語 🎉 <>&\"'", KEY, expires_in=60)
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.")
        assert set(token) <= allowed

    def test_expiry_field_empty_when_no_expiry(self):
        assert sign("hello", KEY).split(".")[1] == ""
