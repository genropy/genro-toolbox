# Claude Code Instructions - Genro-Toolbox

## Project Context

**genro-toolbox** is a lightweight, zero-dependency Python library providing essential utilities for the Genro ecosystem (Genro Kyō).

Part of **genro-modules** (Apache 2.0 license).

## Repository Structure

```
genro-toolbox/
├── src/genro_toolbox/
│   ├── __init__.py      # Public API exports
│   ├── ascii_table.py   # ASCII/Markdown table rendering
│   ├── decorators.py    # extract_kwargs decorator
│   ├── dict_utils.py    # SmartOptions, filtered_dict, make_opts
│   └── typeutils.py     # safe_is_instance
├── tests/
│   ├── test_ascii_table.py
│   ├── test_decorators.py
│   ├── test_dict_utils.py
│   └── test_typeutils.py
├── pyproject.toml
├── LICENSE              # Apache 2.0
└── README.md
```

## Public API

```python
from genro_toolbox import (
    extract_kwargs,      # Decorator for kwargs extraction by prefix
    SmartOptions,        # Namespace for option management
    safe_is_instance,    # Type check without importing
    render_ascii_table,  # ASCII table rendering
    render_markdown_table,  # Markdown table rendering
)
```

## Development

### Running Tests

```bash
pytest tests/
pytest tests/ --cov=src/genro_toolbox --cov-report=term-missing
```

### Code Style

- Python 3.10+
- Type hints required
- English for all code, comments, and commit messages

## Philosophy

> If you write a generic helper that could be useful elsewhere, put it in genro-toolbox.

This library is the **foundation** for utilities shared across:
- genro-asgi
- genro-routes
- genro-api
- Other Genro Kyō projects

## Key Design Principles

1. **Zero dependencies** - Only Python standard library
2. **Type-safe** - Full type hints
3. **Well-tested** - 100% test coverage goal
4. **Minimal** - Only essential utilities

## Git Commit Authorship

- **NEVER** include Claude as a co-author in commits
- **ALWAYS** remove the "Co-Authored-By: Claude" line

## Language Policy

- All code, comments, and commit messages in **English**
