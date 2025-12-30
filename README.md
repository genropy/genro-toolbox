<p align="center">
  <img src="docs/assets/logo.png" alt="Genro-Toolbox Logo" width="200">
</p>

<p align="center">
  <a href="https://badge.fury.io/py/genro-toolbox"><img src="https://badge.fury.io/py/genro-toolbox.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/genro-toolbox/"><img src="https://img.shields.io/badge/python-3.10%2B-blue.svg" alt="Python 3.10+"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://github.com/genropy/genro-toolbox/actions/workflows/test.yml"><img src="https://github.com/genropy/genro-toolbox/actions/workflows/test.yml/badge.svg" alt="Tests"></a>
  <a href="https://codecov.io/gh/genropy/genro-toolbox"><img src="https://codecov.io/gh/genropy/genro-toolbox/graph/badge.svg" alt="codecov"></a>
  <a href="https://genro-toolbox.readthedocs.io/"><img src="https://readthedocs.org/projects/genro-toolbox/badge/?version=latest" alt="Documentation"></a>
  <a href="llm-docs/"><img src="https://img.shields.io/badge/LLM%20Docs-available-brightgreen" alt="LLM Docs"></a>
</p>

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

- **SmartOptions** - Multi-source config with merge via `+` operator
- **TreeDict** - Hierarchical dict with dot notation and path access
- **extract_kwargs** - Decorator to group kwargs by prefix
- **get_uuid** - Sortable 22-char unique identifiers for distributed systems
- **smartasync** - Unified sync/async API with automatic context detection
- **safe_is_instance** - isinstance() without importing the class
- **render_ascii_table** - ASCII table rendering with formatting
- **render_markdown_table** - Markdown table rendering
- **tags_match** - Boolean expression matcher for tag-based filtering

## Examples

### SmartOptions

Load config from multiple sources with type conversion:

```python
from genro_toolbox import SmartOptions
import sys

def serve(host: str = '127.0.0.1', port: int = 8000, debug: bool = False):
    pass

# Load from env and argv with automatic type conversion
# Priority: defaults < env < argv
config = SmartOptions(serve, env='MYAPP', argv=sys.argv[1:])

config["host"]   # from env (MYAPP_HOST) or default
config["port"]   # int from env (MYAPP_PORT) or argv
config["debug"]  # True if --debug passed
```

Compose with `+` for file configs:

```python
config = (
    SmartOptions('config.yaml') +      # file config
    SmartOptions(serve, env='MYAPP', argv=sys.argv[1:])  # defaults < env < argv
)
```

Load from files (YAML, JSON, TOML, INI):

```python
opts = SmartOptions('config.yaml')
opts["server.host"]  # nested dicts become SmartOptions
opts["middleware.cors"]  # string lists become feature flags (True)
opts["apps.shop.module"]  # list of dicts indexed by first key
```

Basic merge with filtering:

```python
opts = SmartOptions(
    {"timeout": 30},                    # runtime values
    {"timeout": 10, "retries": 3},      # defaults
    ignore_none=True,
    ignore_empty=True,
)

opts["timeout"]   # 30 (runtime wins)
opts["retries"]   # 3 (from defaults)
```

### TreeDict

Hierarchical dictionary with path access:

```python
from genro_toolbox import TreeDict

# Create from nested dict
td = TreeDict({"user": {"name": "Alice", "prefs": {"theme": "dark"}}})

# Or from JSON string
td = TreeDict('{"user": {"name": "Alice"}}')

# Or from config file (JSON, YAML, TOML, INI)
td = TreeDict.from_file("config.yaml")

# Path string access
td["user.name"]        # "Alice"
td["user.prefs.theme"] # "dark"
td["missing"]          # None (no KeyError)

# Auto-create intermediate dicts on write
td["settings.db.host"] = "localhost"
td["settings.db.host"] # "localhost"

# List access with #N syntax
td = TreeDict({"users": [{"name": "Alice"}, {"name": "Bob"}]})
td["users.#0.name"]    # "Alice"
td["users.#1.name"]    # "Bob"

# Walk all paths
for path, value in td.walk():
    print(f"{path} = {value}")
# users.#0.name = Alice
# users.#1.name = Bob

# Thread-safe access (sync)
with td:
    td["counter"] = td["counter"] + 1

# Async-safe access
async with td:
    td["counter"] = td["counter"] + 1

# Convert back to dict
td.as_dict()  # {"user": {"name": "Alice", ...}}
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

### tags_match

```python
from genro_toolbox import tags_match

# Simple tag check
tags_match("admin", {"admin", "user"})  # True

# OR (comma, pipe, or keyword)
tags_match("admin,public", {"public"})  # True
tags_match("admin or public", {"admin"})  # True

# AND (ampersand or keyword)
tags_match("admin&internal", {"admin", "internal"})  # True
tags_match("admin and internal", {"admin"})  # False

# NOT (exclamation or keyword)
tags_match("!admin", {"public"})  # True
tags_match("not admin", {"admin"})  # False

# Complex expressions
tags_match("(admin|public)&!internal", {"admin"})  # True
tags_match("(admin or public) and not internal", {"admin", "internal"})  # False
```

### get_uuid

```python
from genro_toolbox import get_uuid

# Generate sortable unique identifiers
uid = get_uuid()  # e.g., "Z00005KmLxHj7F9aGbCd3e"

len(uid)      # 22 characters
uid[0]        # 'Z' (version marker, sorts after legacy UUIDs)
uid.isalnum() # True (URL-safe)

# IDs are lexicographically sortable by creation time
ids = [get_uuid() for _ in range(3)]
sorted(ids) == ids  # True (already sorted)
```

### smartasync

```python
from genro_toolbox import smartasync

class DataManager:
    @smartasync
    async def fetch_data(self, url: str):
        async with httpx.AsyncClient() as client:
            return await client.get(url).json()

manager = DataManager()

# Sync context - no await needed!
data = manager.fetch_data("https://api.example.com")

# Async context - use await
async def main():
    data = await manager.fetch_data("https://api.example.com")

# Also works with sync methods in async context (offloaded to thread)
class LegacyProcessor:
    @smartasync
    def cpu_intensive(self, data):
        return process(data)  # Blocking operation

async def main():
    proc = LegacyProcessor()
    result = await proc.cpu_intensive(data)  # Won't block event loop
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
