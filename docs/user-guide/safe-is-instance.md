# safe_is_instance Guide

Check if an object is an instance of a class by its fully qualified name, without importing the class.

## Overview

`safe_is_instance` allows you to check if an object is an instance of a class identified only by its full class path (e.g., `"mypackage.models.BaseNode"`), without importing the target class.

**Key Benefits**:
- Avoids circular imports
- Works with classes that may not be installed
- Recognizes subclasses (full MRO support)
- Cached for performance

## Basic Usage

```python
from genro_toolbox import safe_is_instance

# Check built-in types
safe_is_instance(42, "builtins.int")  # True
safe_is_instance("hello", "builtins.str")  # True
safe_is_instance([1, 2, 3], "builtins.list")  # True
safe_is_instance({"a": 1}, "builtins.dict")  # True
```

## Custom Classes

```python
from genro_toolbox import safe_is_instance

class MyClass:
    pass

obj = MyClass()

# Use full qualified name: module.ClassName
safe_is_instance(obj, f"{MyClass.__module__}.{MyClass.__qualname__}")  # True
```

## Subclass Recognition

`safe_is_instance` recognizes the entire inheritance chain:

```python
class GrandParent:
    pass

class Parent(GrandParent):
    pass

class Child(Parent):
    pass

obj = Child()

# All return True
safe_is_instance(obj, f"{Child.__module__}.{Child.__qualname__}")
safe_is_instance(obj, f"{Parent.__module__}.{Parent.__qualname__}")
safe_is_instance(obj, f"{GrandParent.__module__}.{GrandParent.__qualname__}")
safe_is_instance(obj, "builtins.object")  # Ultimate base class
```

## Multiple Inheritance

Works correctly with multiple inheritance:

```python
class MixinA:
    pass

class MixinB:
    pass

class Derived(MixinA, MixinB):
    pass

obj = Derived()

# Recognizes all classes in MRO
safe_is_instance(obj, f"{Derived.__module__}.{Derived.__qualname__}")  # True
safe_is_instance(obj, f"{MixinA.__module__}.{MixinA.__qualname__}")    # True
safe_is_instance(obj, f"{MixinB.__module__}.{MixinB.__qualname__}")    # True
```

## Use Cases

### Avoiding Circular Imports

```python
# In module_a.py
from genro_toolbox import safe_is_instance

def process_node(obj):
    # Avoid importing module_b which imports module_a
    if safe_is_instance(obj, "module_b.Node"):
        return handle_node(obj)
    return handle_other(obj)
```

### Plugin System

```python
from genro_toolbox import safe_is_instance

def load_plugin(obj):
    """Load plugin without requiring plugin base class import."""
    if safe_is_instance(obj, "myapp.plugins.BasePlugin"):
        obj.initialize()
        return obj
    raise TypeError("Not a valid plugin")
```

### Optional Dependencies

```python
from genro_toolbox import safe_is_instance

def serialize(obj):
    """Serialize object, handling optional pandas DataFrames."""
    if safe_is_instance(obj, "pandas.core.frame.DataFrame"):
        return obj.to_dict()
    if safe_is_instance(obj, "numpy.ndarray"):
        return obj.tolist()
    return str(obj)
```

## Edge Cases

### Non-existent Classes

Returns `False` for non-existent class names:

```python
class MyClass:
    pass

obj = MyClass()
safe_is_instance(obj, "fake.module.NonExistentClass")  # False
```

### Partial Class Names

Requires fully qualified name (module + class):

```python
class MyClass:
    pass

obj = MyClass()
safe_is_instance(obj, "MyClass")  # False (no module)
```

### Nested Classes

Nested classes have qualified names with dots:

```python
class Outer:
    class Inner:
        pass

obj = Outer.Inner()
# Use qualname which includes the nesting
safe_is_instance(obj, f"{Outer.Inner.__module__}.{Outer.Inner.__qualname__}")  # True
```

## Performance

`safe_is_instance` uses LRU caching for optimal performance:

```python
# First call populates cache
result1 = safe_is_instance(obj1, "mymodule.MyClass")

# Subsequent calls use cached MRO lookup
result2 = safe_is_instance(obj2, "mymodule.MyClass")  # Fast!
```

The MRO (Method Resolution Order) fullnames are cached per class, so repeated checks on objects of the same class are very efficient.

## API Reference

```python
def safe_is_instance(obj: Any, class_full_name: str) -> bool:
    """
    Return True if obj is an instance of the class identified by
    class_full_name or any of its subclasses — without importing
    the class.

    Args:
        obj: The object to check.
        class_full_name: The fully qualified class name,
            e.g. "mypkg.models.BaseNode".

    Returns:
        True if obj is an instance of the class, False otherwise.
    """
```

## See Also

- [SmartOptions Guide](smart-options.md) - Option merging and filtering
- [extract_kwargs Guide](extract-kwargs.md) - Kwargs extraction decorator
- [API Reference](../api/reference.md) - Complete API documentation
