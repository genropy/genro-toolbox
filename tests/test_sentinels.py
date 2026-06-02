"""Tests for the sentinels module."""

from genro_toolbox import MANDATORY
from genro_toolbox.sentinels import _Mandatory


class TestMandatory:
    """Tests for the MANDATORY sentinel."""

    def test_singleton_identity(self):
        """Every _Mandatory() returns the same instance as MANDATORY."""
        assert _Mandatory() is MANDATORY
        assert _Mandatory() is _Mandatory()

    def test_repr(self):
        """repr is the bare name MANDATORY."""
        assert repr(MANDATORY) == "MANDATORY"

    def test_falsy(self):
        """MANDATORY is falsy."""
        assert bool(MANDATORY) is False
        assert not MANDATORY

    def test_distinct_from_none(self):
        """MANDATORY is not None and not equal to None."""
        assert MANDATORY is not None
        assert MANDATORY != None  # noqa: E711

    def test_usable_as_default_marker(self):
        """A parameter left as MANDATORY can be detected by identity."""

        def f(value=MANDATORY):
            if value is MANDATORY:
                raise ValueError("value is required")
            return value

        try:
            f()
        except ValueError as exc:
            assert str(exc) == "value is required"
        else:
            raise AssertionError("expected ValueError")

        assert f(0) == 0
        assert f(None) is None
