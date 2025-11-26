# extract_kwargs Decorator

Complete guide to the `extract_kwargs` decorator.

## Overview

The `extract_kwargs` decorator extracts and groups keyword arguments by prefix, solving the problem of passing nested configuration in a clean and flexible way.

## Basic Usage

The simplest use case: extract parameters with a specific prefix.

```python
from genro_toolbox import extract_kwargs

class MyClass:
    @extract_kwargs(logging=True)
    def my_method(self, name, logging_kwargs=None, **kwargs):
        print(f"Logging config: {logging_kwargs}")
        print(f"Other params: {kwargs}")

obj = MyClass()
obj.my_method(
    name="test",
    logging_level="INFO",
    logging_format="json",
    timeout=30
)
# Output:
# Logging config: {'level': 'INFO', 'format': 'json'}
# Other params: {'name': 'test', 'timeout': 30}
```

**How it works:**
1. Parameters starting with `logging_` are extracted
2. The prefix is removed: `logging_level` → `level`
3. They're grouped into `logging_kwargs` dictionary
4. Other parameters remain in `**kwargs`

## Multiple Prefix Families

Extract multiple groups of parameters simultaneously:

```python
@extract_kwargs(logging=True, cache=True)
def setup(self, name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    return {
        "logging": logging_kwargs,
        "cache": cache_kwargs,
        "other": kwargs
    }

result = obj.setup(
    name="api",
    logging_level="INFO",
    cache_ttl=300,
    cache_backend="redis",
    timeout=30
)
# Result:
# {
#     "logging": {"level": "INFO"},
#     "cache": {"ttl": 300, "backend": "redis"},
#     "other": {"timeout": 30}
# }
```

## Calling Styles

### Style 1: Prefix Style (Most Explicit)

Pass parameters with prefixes - most explicit and IDE-friendly:

```python
setup(
    name="api",
    logging_level="INFO",      # Clear what this configures
    logging_format="json",
    cache_ttl=300
)
```

### Style 2: Dict Style (Compact)

Pass a dictionary directly - useful when config comes from files:

```python
config = {
    "level": "INFO",
    "format": "json"
}

setup(
    name="api",
    logging=config,  # Pass entire dict
    cache={'ttl': 300}
)
```

### Style 3: Boolean Activation

Pass `True` to activate with defaults:

```python
setup(
    name="api",
    logging=True  # logging_kwargs = {}
)
```

This is useful when the decorated function has sensible defaults.

## Advanced Options

### Custom Extraction Options

Pass a dict to customize extraction behavior:

```python
@extract_kwargs(logging={'pop': False, 'slice_prefix': True})
def my_method(self, logging_kwargs=None, **kwargs):
    return {"logging": logging_kwargs, "other": kwargs}

result = obj.my_method(logging_level="INFO", timeout=30)
# With pop=False, params stay in kwargs too:
# {
#     "logging": {"level": "INFO"},
#     "other": {"timeout": 30, "logging_level": "INFO"}  ← Still here!
# }
```

**Options:**
- `pop`: If `True`, remove extracted params from source (default for `param=True`)
- `slice_prefix`: If `True`, remove prefix from keys (default: `True`)
- `is_list`: Reserved for future use

### Keep Prefix in Keys

Sometimes you want to keep the full key name:

```python
@extract_kwargs(logging={'slice_prefix': False, 'pop': True})
def my_method(self, logging_kwargs=None, **kwargs):
    return {"logging": logging_kwargs, "other": kwargs}

result = obj.my_method(logging_level="INFO", timeout=30)
# {
#     "logging": {"logging_level": "INFO"},  ← Prefix kept!
#     "other": {"timeout": 30}
# }
```

## Reserved Keywords

Python reserved keywords are automatically handled. The keyword `class` is renamed to `_class`:

```python
@extract_kwargs(logging=True)
def my_method(self, logging_kwargs=None):
    return {"logging": logging_kwargs}

result = obj.my_method(logging_class="MyLogger")
# {
#     "logging": {"_class": "MyLogger"}  ← 'class' → '_class'
# }
```

## Merging with Existing kwargs

You can pass both `prefix_kwargs` explicitly AND prefixed parameters - they merge:

```python
@extract_kwargs(logging=True)
def my_method(self, logging_kwargs=None, **kwargs):
    return {"logging": logging_kwargs, "other": kwargs}

result = obj.my_method(
    logging_kwargs={"existing": "value"},  # Explicit dict
    logging_level="INFO",                  # Prefixed param
    timeout=30
)
# {
#     "logging": {"existing": "value", "level": "INFO"},  ← Merged!
#     "other": {"timeout": 30}
# }
```

## Advanced Features

### Dynamic Extraction Specs (_dictkwargs)

Use `_dictkwargs` to provide extraction specs dynamically:

```python
# Define specs separately
extract_spec = {"logging": True, "cache": True}

@extract_kwargs(_dictkwargs=extract_spec)
def my_method(self, logging_kwargs=None, cache_kwargs=None):
    return {"logging": logging_kwargs, "cache": cache_kwargs}

result = obj.my_method(
    logging_level="INFO",
    cache_ttl=300
)
# Both extracted using dynamic spec
```

This is useful when extraction specs come from configuration or are computed at runtime.

### Adapter Hook (_adapter)

Use `_adapter` to pre-process kwargs before extraction:

```python
class ClassWithAdapter:
    def my_adapter(self, kwargs):
        # Pre-process kwargs before extraction
        self.adapter_called = True
        kwargs['modified_by_adapter'] = True

    @extract_kwargs(_adapter='my_adapter', logging=True)
    def my_method(self, logging_kwargs=None, **kwargs):
        return {"logging": logging_kwargs, "other": kwargs}

obj = ClassWithAdapter()
result = obj.my_method(logging_level="INFO", timeout=30)
# Adapter was called before extraction
# result["other"]["modified_by_adapter"] == True
```

**Use cases for adapters:**
- Normalize parameter names
- Add computed parameters
- Validate parameters before extraction
- Apply transformations

## Signature

```python
def extract_kwargs(
    _adapter: Optional[str] = None,
    _dictkwargs: Optional[Dict[str, Any]] = None,
    **extraction_specs: Any
) -> Callable[[F], F]:
    """
    Args:
        _adapter: Optional method name on self for pre-processing kwargs
        _dictkwargs: Optional dict of extraction specs (alternative to **extraction_specs)
        **extraction_specs: Prefix names with values:
                           - True: Extract and pop
                           - dict: Custom options (pop, slice_prefix, is_list)

    Returns:
        Decorated function
    """
```

## Requirements

The decorated function **MUST** have `{prefix}_kwargs` parameters for each prefix specified:

```python
# Correct
@extract_kwargs(logging=True, cache=True)
def func(self, logging_kwargs=None, cache_kwargs=None, **kwargs):
    pass

# Wrong - missing cache_kwargs parameter
@extract_kwargs(logging=True, cache=True)
def func(self, logging_kwargs=None, **kwargs):  # Will fail!
    pass
```

## Works with Functions Too

While originally designed for class methods, `extract_kwargs` also works with standalone functions:

```python
@extract_kwargs(logging=True)
def standalone_func(name, logging_kwargs=None, **kwargs):
    print(f"Name: {name}")
    print(f"Logging: {logging_kwargs}")
    print(f"Other: {kwargs}")

# Works without self!
standalone_func(name="test", logging_level="INFO", timeout=30)
```

## See Also

- [Best Practices](best-practices.md) - Production usage patterns
- [Examples](../examples/index.md) - Real-world examples
- [API Reference](../api/reference.md) - Full API documentation
