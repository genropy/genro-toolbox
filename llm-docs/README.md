# genro-toolbox - LLM Quick Reference

Zero-dependency Python utilities for the Genro Kyō ecosystem.

## Installation

```bash
pip install genro-toolbox
```

## Core API

```python
from genro_toolbox import (
    SmartOptions,           # Merge kwargs with defaults
    extract_kwargs,         # Decorator: group kwargs by prefix
    safe_is_instance,       # isinstance() without import
    render_ascii_table,     # ASCII table rendering
    render_markdown_table,  # Markdown table rendering
)
```

## Quick Examples

### SmartOptions

```python
opts = SmartOptions(
    {"timeout": 30},                    # runtime values
    {"timeout": 10, "retries": 3},      # defaults
    ignore_none=True,
    ignore_empty=True,
)
opts.timeout   # 30 (runtime wins)
opts.retries   # 3 (from defaults)
opts.as_dict() # {"timeout": 30, "retries": 3}
```

### extract_kwargs

```python
@extract_kwargs(logging=True, cache=True)
def func(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    return logging_kwargs, cache_kwargs

func("x", logging_level="INFO", cache_ttl=300, other=1)
# logging_kwargs = {"level": "INFO"}
# cache_kwargs = {"ttl": 300}
# kwargs = {"other": 1}
```

### safe_is_instance

```python
safe_is_instance(42, "builtins.int")           # True
safe_is_instance(obj, "mymodule.MyClass")      # True (includes subclasses)
```

### Tables

```python
data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Active", "type": "bool"},
    ],
    "rows": [["Alice", "yes"], ["Bob", "no"]],
}
render_ascii_table(data)   # ASCII box table
render_markdown_table(data) # | Name | Active | ...
```
