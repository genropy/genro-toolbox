# FAQ

## General

### What is genro-toolbox?

Genro-toolbox is a lightweight, zero-dependency Python library providing essential utilities for the Genro Kyō ecosystem. It serves as the foundation for common patterns used across genro-asgi, genro-routes, genro-api, and other Genro projects.

### Why use genro-toolbox instead of writing my own utilities?

1. **Tested** - 88 tests covering all functionality
2. **Zero dependencies** - Only Python standard library
3. **Type-safe** - Full type hints
4. **Consistent** - Same patterns across all Genro projects

### What Python versions are supported?

Python 3.10 and later. We use modern type hints (`|` union syntax, `dict[str, Any]`).

## SmartOptions

### Why use SmartOptions instead of a plain dict?

SmartOptions provides:
- Path notation access (`opts["server.host"]` for nested values)
- Automatic merging of defaults with runtime values
- Filtering of `None` and empty values
- Loading from files (YAML, JSON, TOML, INI)
- Loading from environment variables and CLI args
- Immutable copy via `as_dict()`

### What counts as "empty" when using ignore_empty=True?

Empty strings `""`, empty lists `[]`, empty dicts `{}`, empty tuples `()`, empty sets `set()`, empty bytes `b""`, and empty frozensets. Note that `None` is NOT considered empty - use `ignore_none=True` for that.

### Can I modify SmartOptions after creation?

Yes. SmartOptions is mutable:

```python
opts = SmartOptions({"timeout": 10}, {})
opts["timeout"] = 20       # Set
opts["new_key"] = "value"  # Add
del opts["timeout"]        # Delete
```

## extract_kwargs

### Why does extract_kwargs always return a dict, never None?

This is by design for consistency. Even when no kwargs match the prefix, you get an empty dict `{}`. This means you can always safely do `logging_kwargs.get("level")` without checking for None first.

### What happens to the reserved word "class"?

Python's `class` keyword is automatically renamed to `_class`:

```python
@extract_kwargs(html=True)
def func(html_kwargs=None, **kwargs):
    return html_kwargs

func(html_class="container")  # Returns {"_class": "container"}
```

### Can I use extract_kwargs on functions (not just methods)?

Yes. The decorator detects whether the first argument is `self` (a method) or not (a function). Both work correctly.

### What's the difference between pop=True and pop=False?

- `pop=True` (default): Extracted kwargs are removed from the original kwargs
- `pop=False`: Extracted kwargs remain in the original kwargs too

```python
@extract_kwargs(logging={'pop': False})
def func(logging_kwargs=None, **kwargs):
    # logging_kwargs = {"level": "INFO"}
    # kwargs = {"logging_level": "INFO", "other": "value"}  # Still contains logging_level
```

## safe_is_instance

### Why not just use isinstance()?

`isinstance()` requires importing the class. `safe_is_instance()` works with the fully qualified class name as a string, avoiding import cycles and allowing type checks without runtime dependencies.

### Does safe_is_instance work with subclasses?

Yes. It checks the entire MRO (Method Resolution Order), so:

```python
class Parent: pass
class Child(Parent): pass

obj = Child()
safe_is_instance(obj, "module.Parent")  # True
safe_is_instance(obj, "module.Child")   # True
```

### Is safe_is_instance cached?

Yes. The MRO lookup is cached using `@lru_cache` for performance. Multiple calls with the same class are fast.

## Tables

### What's the difference between render_ascii_table and render_markdown_table?

- `render_ascii_table`: Box-drawing characters, word wrapping, max_width support
- `render_markdown_table`: GitHub-compatible markdown format

### How do I format dates?

Use the `format` field with a simplified date format:

```python
{"name": "Date", "type": "date", "format": "dd/mm/yyyy"}
# Input: "2025-11-24" → Output: "24/11/2025"
```

Supported: `yyyy`, `yy`, `mm`, `dd`, `HH`, `MM`, `SS`

### How does boolean formatting work?

Values `"true"`, `"yes"`, `"1"` (case-insensitive) → `"true"`
Values `"false"`, `"no"`, `"0"` (case-insensitive) → `"false"`

## Troubleshooting

### I get "ModuleNotFoundError: No module named 'genro_toolbox'"

Make sure you've installed the package:

```bash
pip install genro-toolbox
```

### Type hints aren't working in my IDE

Ensure you're using Python 3.10+ and your IDE supports modern type hints. The library uses `dict[str, Any]` syntax (not `Dict[str, Any]`).
