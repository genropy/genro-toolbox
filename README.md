# Genro-Toolbox

Essential utilities for the Genro ecosystem (Genro Kyō).

A lightweight, zero-dependency library providing core utilities that can be used across all Genro projects.

## Installation

```bash
pip install genro-toolbox
```

## Features

### SmartOptions

A convenience namespace for merging runtime kwargs with defaults:

```python
from genro_toolbox import SmartOptions

opts = SmartOptions(
    {"timeout": 30},  # runtime values
    {"timeout": 10, "retries": 3},  # defaults
    ignore_none=True,
    ignore_empty=True,
)

print(opts.timeout)  # 30 (from runtime)
print(opts.retries)  # 3 (from defaults)
print(opts.as_dict())  # {"timeout": 30, "retries": 3}
```

### extract_kwargs Decorator

Extract prefixed kwargs into grouped dictionaries:

```python
from genro_toolbox import extract_kwargs

@extract_kwargs(logging=True, cache=True)
def my_function(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    print(f"logging: {logging_kwargs}")
    print(f"cache: {cache_kwargs}")
    print(f"other: {kwargs}")

my_function(
    "test",
    logging_level="INFO",
    logging_format="json",
    cache_ttl=300,
    timeout=30,
)
# Output:
# logging: {'level': 'INFO', 'format': 'json'}
# cache: {'ttl': 300}
# other: {'timeout': 30}
```

### safe_is_instance

Check if an object is an instance of a class by its fully qualified name, without importing:

```python
from genro_toolbox import safe_is_instance

# Works with any object
safe_is_instance(42, "builtins.int")  # True
safe_is_instance("hello", "builtins.str")  # True

# Works with custom classes (includes subclass recognition)
safe_is_instance(my_obj, "mypackage.models.BaseNode")
```

### ASCII & Markdown Tables

Render data as formatted tables:

```python
from genro_toolbox import render_ascii_table, render_markdown_table

data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Age", "type": "int"},
        {"name": "Active", "type": "bool"},
    ],
    "rows": [
        ["Alice", "25", "yes"],
        ["Bob", "30", "no"],
    ],
}

print(render_ascii_table(data))
# +-------+-----+--------+
# |Name   |Age  |Active  |
# +-------+-----+--------+
# |Alice  |25   |true    |
# +-------+-----+--------+
# |Bob    |30   |false   |
# +-------+-----+--------+

print(render_markdown_table(data))
# | Name | Age | Active |
# | --- | --- | --- |
# | Alice | 25 | true |
# | Bob | 30 | false |
```

## Philosophy

> If you write a generic helper that could be useful elsewhere, put it in genro-toolbox.

This library serves as the foundation for utilities shared across:
- genro-asgi
- genro-routes
- genro-api
- Other Genro ecosystem projects

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

## Contributing

Part of Genro Kyō. Contributions welcome via GitHub.
