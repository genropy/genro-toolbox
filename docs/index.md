<div align="center">
  <img src="_static/logo.png" alt="Genro-Toolbox Logo" width="200"/>
</div>

# Genro-Toolbox

**Essential utilities for the Genro ecosystem (Genro Kyō)**

Genro-Toolbox is a lightweight, zero-dependency Python library providing core utilities for Genro Kyō (genro-asgi, genro-routes, genro-api, etc.). Think of it as the foundation from which Genro solutions are built.

## Features

- **`extract_kwargs`** - Decorator for extracting and grouping keyword arguments by prefix
- **`SmartOptions`** - Intelligent options merging with filtering and defaults
- **`TreeDict`** - Hierarchical dictionary with dot notation path access
- **`tags_match`** - Boolean expression matcher for tag-based filtering
- **`get_uuid`** - Sortable 22-char unique identifiers for distributed systems
- **`smartasync`** - Unified sync/async API decorator with automatic context detection
- **`safe_is_instance`** - Type checking without imports
- **`ascii_table`** - Beautiful ASCII and Markdown tables with formatting and hierarchies
- **Zero dependencies** - Pure Python standard library only (optional: tomli, pyyaml)
- **Full type hints** - Complete typing support
- **Python 3.10+** - Modern Python

## Quick Example

```python
from genro_toolbox import extract_kwargs

@extract_kwargs(logging=True, cache=True)
def setup_service(name, logging_kwargs=None, cache_kwargs=None, **kwargs):
    print(f"Logging config: {logging_kwargs}")
    print(f"Cache config: {cache_kwargs}")

# All these styles work:
setup_service(
    name="api",
    logging_level="INFO",      # → logging_kwargs={'level': 'INFO'}
    cache_ttl=300,             # → cache_kwargs={'ttl': 300}
)

setup_service(
    name="api",
    logging={'level': 'INFO'},  # Dict style
    cache=True                  # Boolean activation
)
```

```{toctree}
:maxdepth: 2
:caption: Contents
:hidden:

self
user-guide/installation
user-guide/quickstart
user-guide/extract-kwargs
user-guide/smart-options
user-guide/treedict
user-guide/tags-match
user-guide/safe-is-instance
user-guide/ascii-table
user-guide/best-practices
examples/index
api/reference
faq
appendix/architecture
appendix/contributing
```

## Part of Genro Kyō

Genro-Toolbox is part of [Genro Kyō](https://github.com/softwell/meta-genro-modules).

## License

Apache License 2.0 - Copyright © 2025 Softwell Srl
