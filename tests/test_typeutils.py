"""Tests for the typeutils module."""

from genro_toolbox import safe_is_instance


class TestSafeIsInstance:
    """Tests for safe_is_instance function."""

    def test_basic_instance_check(self):
        """Test basic instance checking with full class name."""

        class MyClass:
            pass

        obj = MyClass()
        assert safe_is_instance(obj, f"{MyClass.__module__}.{MyClass.__qualname__}")

    def test_subclass_recognition(self):
        """Test that subclasses are recognized correctly."""

        class Base:
            pass

        class Derived(Base):
            pass

        obj = Derived()
        # Should recognize both Derived and Base
        assert safe_is_instance(obj, f"{Derived.__module__}.{Derived.__qualname__}")
        assert safe_is_instance(obj, f"{Base.__module__}.{Base.__qualname__}")

    def test_negative_case(self):
        """Test that unrelated classes return False."""

        class ClassA:
            pass

        class ClassB:
            pass

        obj = ClassA()
        assert not safe_is_instance(obj, f"{ClassB.__module__}.{ClassB.__qualname__}")

    def test_multiple_inheritance(self):
        """Test with multiple inheritance."""

        class MixinA:
            pass

        class MixinB:
            pass

        class Derived(MixinA, MixinB):
            pass

        obj = Derived()
        # Should recognize all classes in MRO
        assert safe_is_instance(obj, f"{Derived.__module__}.{Derived.__qualname__}")
        assert safe_is_instance(obj, f"{MixinA.__module__}.{MixinA.__qualname__}")
        assert safe_is_instance(obj, f"{MixinB.__module__}.{MixinB.__qualname__}")

    def test_builtin_types(self):
        """Test with built-in Python types."""
        assert safe_is_instance(42, "builtins.int")
        assert safe_is_instance("hello", "builtins.str")
        assert safe_is_instance([1, 2, 3], "builtins.list")
        assert safe_is_instance({"a": 1}, "builtins.dict")

    def test_builtin_type_inheritance(self):
        """Test subclass recognition with built-in types."""

        class MyList(list):
            pass

        obj = MyList()
        assert safe_is_instance(obj, f"{MyList.__module__}.{MyList.__qualname__}")
        assert safe_is_instance(obj, "builtins.list")  # Parent class
        assert safe_is_instance(obj, "builtins.object")  # Ultimate base

    def test_nonexistent_class(self):
        """Test that checking for non-existent class returns False."""

        class MyClass:
            pass

        obj = MyClass()
        assert not safe_is_instance(obj, "fake.module.NonExistentClass")

    def test_object_base_class(self):
        """Test that all objects are instances of object."""

        class MyClass:
            pass

        obj = MyClass()
        assert safe_is_instance(obj, "builtins.object")

    def test_multilevel_inheritance(self):
        """Test with multiple levels of inheritance."""

        class GrandParent:
            pass

        class Parent(GrandParent):
            pass

        class Child(Parent):
            pass

        obj = Child()
        # Should recognize entire inheritance chain
        assert safe_is_instance(obj, f"{Child.__module__}.{Child.__qualname__}")
        assert safe_is_instance(obj, f"{Parent.__module__}.{Parent.__qualname__}")
        assert safe_is_instance(
            obj, f"{GrandParent.__module__}.{GrandParent.__qualname__}"
        )

    def test_caching_behavior(self):
        """Test that caching works correctly."""

        class MyClass:
            pass

        obj1 = MyClass()
        obj2 = MyClass()

        # First call populates cache
        result1 = safe_is_instance(obj1, f"{MyClass.__module__}.{MyClass.__qualname__}")
        # Second call should use cached result
        result2 = safe_is_instance(obj2, f"{MyClass.__module__}.{MyClass.__qualname__}")

        assert result1 is True and result2 is True


class TestSafeIsInstanceEdgeCases:
    """Edge cases for safe_is_instance."""

    def test_empty_string_class_name(self):
        """Test with empty class name."""

        class MyClass:
            pass

        obj = MyClass()
        assert not safe_is_instance(obj, "")

    def test_partial_class_name(self):
        """Test with partial class name (no module)."""

        class MyClass:
            pass

        obj = MyClass()
        # Should not match just class name without module
        assert not safe_is_instance(obj, "MyClass")

    def test_with_nested_class(self):
        """Test with nested class definition."""

        class Outer:
            class Inner:
                pass

        obj = Outer.Inner()
        # Nested classes have qualified names with dots
        assert safe_is_instance(
            obj, f"{Outer.Inner.__module__}.{Outer.Inner.__qualname__}"
        )
