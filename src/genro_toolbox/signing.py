# Copyright 2025 Softwell S.r.l. - Genro Team
# SPDX-License-Identifier: Apache-2.0

"""HMAC-signed payloads with optional expiry.

Authenticates data that leaves the server and comes back — a payload handed
to a client, stored in a URL or a cookie, then returned to be acted upon.
The key never leaves the server: sign on the way out, verify on the way in.

Token layout, three base64url fields joined by ``.``::

    <payload>.<expiry>.<signature>

Fields are base64url-encoded (alphabet ``A-Za-z0-9-_``), so the separator
can never occur inside a field and the payload round-trips byte for byte
whatever it contains. ``expiry`` is a Unix timestamp, empty when the token
does not expire; it sits inside the signed area, so it cannot be altered.

The signature is HMAC-SHA256 over the encoded ``<payload>.<expiry>`` prefix,
compared with :func:`hmac.compare_digest`.

Example:
    token = sign("hello", key="secret", expires_in=300)
    verify(token, key="secret")   # -> "hello"
"""

import base64
import hashlib
import hmac
import time

SEPARATOR = "."


class SignatureError(Exception):
    """The token is malformed or its signature does not match."""


class SignatureExpired(SignatureError):
    """The signature is valid but the token's expiry has passed."""


def _b64_encode(raw: bytes) -> str:
    """Encode bytes as unpadded base64url."""
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64_decode(text: str) -> bytes:
    """Decode unpadded base64url back to bytes."""
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _signature(signed_part: str, key: str) -> str:
    """Return the HMAC-SHA256 of the signed prefix, as base64url."""
    mac = hmac.new(key.encode("utf-8"), signed_part.encode("ascii"), hashlib.sha256)
    return _b64_encode(mac.digest())


def sign(payload: str, key: str, expires_in: int | None = None) -> str:
    """Sign a payload, optionally giving it a lifetime.

    Args:
        payload: The string to protect. Any content is allowed.
        key: Secret key. Keep it server-side.
        expires_in: Lifetime in seconds. ``None`` means no expiry.

    Returns:
        The signed token.

    Raises:
        ValueError: If the key is empty, or expires_in is not positive.
    """
    if not key:
        raise ValueError("A non-empty key is required to sign a payload.")
    if expires_in is not None and expires_in <= 0:
        raise ValueError(f"expires_in must be a positive number of seconds, got {expires_in!r}.")

    expiry = "" if expires_in is None else _b64_encode(str(int(time.time()) + expires_in).encode())
    signed_part = f"{_b64_encode(payload.encode('utf-8'))}{SEPARATOR}{expiry}"
    return f"{signed_part}{SEPARATOR}{_signature(signed_part, key)}"


def verify(token: str, key: str) -> str:
    """Verify a token and return its payload.

    Args:
        token: A token produced by :func:`sign`.
        key: The same secret key used to sign.

    Returns:
        The original payload, byte for byte.

    Raises:
        ValueError: If the key is empty.
        SignatureExpired: Signature valid, but the token has expired.
        SignatureError: Malformed token, or signature mismatch.
    """
    if not key:
        raise ValueError("A non-empty key is required to verify a token.")

    signed_part, separator, signature = token.rpartition(SEPARATOR)
    if not separator:
        raise SignatureError("Malformed token: expected three '.'-separated fields.")

    if not hmac.compare_digest(_signature(signed_part, key), signature):
        raise SignatureError("Signature does not match: the token was not produced with this key.")

    encoded_payload, separator, encoded_expiry = signed_part.partition(SEPARATOR)
    if not separator:
        raise SignatureError("Malformed token: expected three '.'-separated fields.")

    if encoded_expiry:
        # Signed, so a non-numeric expiry means the token was built wrong,
        # never that someone tampered with it. Refuse it either way.
        expiry = _b64_decode(encoded_expiry).decode("ascii")
        if not expiry.isdigit():
            raise SignatureError(f"Malformed token: expiry {expiry!r} is not a timestamp.")
        # Compare against the untruncated clock: flooring both sides would
        # keep a token alive for up to a second past its expiry.
        if int(expiry) < time.time():
            raise SignatureExpired("Token has expired.")

    return _b64_decode(encoded_payload).decode("utf-8")
