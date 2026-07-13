"""Tests for the metadata decorator."""

from genro_toolbox import metadata


class TestMetadataFunction:
    """metadata applied to functions."""

    def test_single_attribute(self):
        """A single kwarg is stamped as an attribute on the function."""

        @metadata(public=True)
        def handler():
            return "ok"

        assert handler.public is True

    def test_multiple_attributes(self):
        """Multiple kwargs are all stamped as attributes."""

        @metadata(public=True, order=5, label="handler")
        def handler():
            pass

        assert handler.public is True
        assert handler.order == 5
        assert handler.label == "handler"

    def test_prefix(self):
        """With prefix, attribute names become <prefix>_<key>."""

        @metadata(prefix="rpc", public=True)
        def handler():
            pass

        assert handler.rpc_public is True
        assert not hasattr(handler, "public")

    def test_prefix_multiple_keys(self):
        """Prefix is applied to every key."""

        @metadata(prefix="rpc", public=True, tags="admin")
        def handler():
            pass

        assert handler.rpc_public is True
        assert handler.rpc_tags == "admin"

    def test_returns_same_object(self):
        """The decorated function is returned unchanged (identity)."""

        def handler():
            return 42

        decorated = metadata(public=True)(handler)

        assert decorated is handler
        assert decorated() == 42

    def test_no_attributes(self):
        """No kwargs leaves the target untouched but still returns it."""

        @metadata()
        def handler():
            return "ok"

        assert handler() == "ok"


class TestMetadataClass:
    """metadata applied to classes."""

    def test_single_attribute(self):
        """A single kwarg is stamped as a class attribute."""

        @metadata(mixin_order=10)
        class Core:
            pass

        assert Core.mixin_order == 10

    def test_multiple_attributes(self):
        """Multiple kwargs are all stamped as class attributes."""

        @metadata(mixin_order=10, category="core", enabled=False)
        class Core:
            pass

        assert Core.mixin_order == 10
        assert Core.category == "core"
        assert Core.enabled is False

    def test_prefix(self):
        """With prefix, class attribute names become <prefix>_<key>."""

        @metadata(prefix="meta", version=2)
        class Core:
            pass

        assert Core.meta_version == 2
        assert not hasattr(Core, "version")

    def test_returns_same_class(self):
        """The decorated class is returned unchanged (identity)."""

        class Core:
            pass

        decorated = metadata(mixin_order=10)(Core)

        assert decorated is Core

    def test_class_remains_instantiable(self):
        """A decorated class stays instantiable with attributes on instances."""

        @metadata(mixin_order=10)
        class Core:
            def __init__(self, name):
                self.name = name

        instance = Core("alpha")

        assert instance.name == "alpha"
        assert instance.mixin_order == 10

    def test_prefix_visible_on_instances(self):
        """Prefixed class attributes are visible on instances too."""

        @metadata(prefix="meta", version=2)
        class Core:
            pass

        instance = Core()

        assert instance.meta_version == 2
