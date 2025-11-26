[![PyPI version](https://badge.fury.io/py/genro-toolbox.svg)](https://badge.fury.io/py/genro-toolbox)
[![Python](https://img.shields.io/pypi/pyversions/genro-toolbox.svg)](https://pypi.org/project/genro-toolbox/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://github.com/genropy/genro-toolbox/actions/workflows/test.yml/badge.svg)](https://github.com/genropy/genro-toolbox/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/genropy/genro-toolbox/graph/badge.svg)](https://codecov.io/gh/genropy/genro-toolbox)
[![Documentation](https://readthedocs.org/projects/genro-toolbox/badge/?version=latest)](https://genro-toolbox.readthedocs.io/)
[![LLM Docs](https://img.shields.io/badge/LLM%20Docs-available-brightgreen)](llm-docs/)

# Genro-Toolbox

> Essential utilities for the Genro ecosystem

Part of [Genro Kyō](https://github.com/genropy) ecosystem.

A lightweight, zero-dependency Python library providing core utilities that can be used across all Genro projects.

📚 **[Full Documentation](https://genro-toolbox.readthedocs.io/)**

## Installation

```bash
pip install genro-toolbox
```

## Features

- **SmartOptions** - Merge runtime kwargs with defaults
- **extract_kwargs** - Decorator to group kwargs by prefix
- **safe_is_instance** - isinstance() without importing the class
- **render_ascii_table** - ASCII table rendering with formatting
- **render_markdown_table** - Markdown table rendering

## Examples

### SmartOptions

```python
from genro_toolbox import SmartOptions

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

### extract_kwargs Decorator

```python
from genro_toolbox import extract_kwargs

@extract_kwargs(logging=True, cache=True)
def my_function(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    print(f"logging: {logging_kwargs}")
    print(f"cache: {cache_kwargs}")

my_function(
    "test",
    logging_level="INFO",
    logging_format="json",
    cache_ttl=300,
)
# logging: {'level': 'INFO', 'format': 'json'}
# cache: {'ttl': 300}
```

### safe_is_instance

```python
from genro_toolbox import safe_is_instance

# Check type without importing
safe_is_instance(42, "builtins.int")              # True
safe_is_instance(my_obj, "mypackage.BaseClass")   # True (includes subclasses)
```

### ASCII & Markdown Tables

```python
from genro_toolbox import render_ascii_table, render_markdown_table

data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Active", "type": "bool"},
    ],
    "rows": [
        ["Alice", "yes"],
        ["Bob", "no"],
    ],
}

print(render_ascii_table(data))
# +-------+--------+
# |Name   |Active  |
# +-------+--------+
# |Alice  |true    |
# +-------+--------+
# |Bob    |false   |
# +-------+--------+
```

## Philosophy

> If you write a generic helper that could be useful elsewhere, put it in genro-toolbox.

This library serves as the foundation for utilities shared across:
- genro-asgi
- genro-routes
- genro-api
- Other Genro Kyō projects

## License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

Copyright 2025 Softwell S.r.l.
