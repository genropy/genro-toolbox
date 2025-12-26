# SmartOptions Guide

Complete guide to using `SmartOptions` for intelligent option merging and configuration loading.

## Overview

`SmartOptions` is a versatile namespace class for managing configuration with intelligent merging, multi-source loading, and hierarchical data support. Built on `TreeDict`, it uses path notation for accessing nested values.

**Key Features**:

- Load config from files (YAML, JSON, TOML, INI)
- Load config from environment variables
- Extract defaults from function signatures
- Merge multiple sources with `+` operator
- Nested dicts become SmartOptions recursively
- String lists become feature flags
- List of dicts indexed by first key value
- Path notation access: `opts["server.host"]`

## Basic Usage

```python
from genro_toolbox import SmartOptions

# Incoming options override defaults
opts = SmartOptions(
    incoming={'timeout': 5},
    defaults={'timeout': 1, 'retries': 3}
)

print(opts["timeout"])  # 5 (from incoming)
print(opts["retries"])  # 3 (from defaults)
```

## Loading from Files

SmartOptions can load configuration directly from files:

```python
# From YAML
opts = SmartOptions('config.yaml')

# From JSON
opts = SmartOptions('config.json')

# From TOML
opts = SmartOptions('config.toml')

# From INI (keys become section_key format)
opts = SmartOptions('config.ini')

# From Path object
from pathlib import Path
opts = SmartOptions(Path('config.yaml'))
```

Missing files return an empty SmartOptions (no error).

## Loading from Environment Variables

Use the `ENV:PREFIX` syntax to load from environment variables:

```python
# Given: MYAPP_HOST=localhost MYAPP_PORT=9000
opts = SmartOptions('ENV:MYAPP')

print(opts["host"])  # 'localhost'
print(opts["port"])  # '9000' (string from env)
```

The prefix is stripped and keys are lowercased.

## Loading from Function Signatures

Extract defaults and parse argv from a callable:

```python
def serve(host: str = '127.0.0.1', port: int = 8000, debug: bool = False):
    pass

# Just extract defaults
opts = SmartOptions(serve)
print(opts["host"])   # '127.0.0.1'
print(opts["port"])   # 8000
print(opts["debug"])  # False
```

### Using env and argv Parameters

Load from environment and CLI with automatic type conversion:

```python
def serve(host: str = '127.0.0.1', port: int = 8000, debug: bool = False):
    pass

# Given: MYAPP_HOST=0.0.0.0 MYAPP_PORT=9000
opts = SmartOptions(serve, env='MYAPP', argv=['--debug'])

print(opts["host"])   # '0.0.0.0' (from env)
print(opts["port"])   # 9000 (int, converted from env)
print(opts["debug"])  # True (from argv)
```

**Priority**: defaults < env < argv (rightmost wins)

Types are extracted from the function signature and applied to both env and argv values.

Boolean conversion from environment supports: `true`, `1`, `yes`, `on` (case-insensitive) → `True`

### Legacy argv Syntax

You can also pass argv as second positional argument:

```python
import sys
opts = SmartOptions(serve, sys.argv[1:])
# ./app.py --port 9000 --debug
# opts["port"] = 9000, opts["debug"] = True
```

### Annotated Types

Supports `Annotated` types for help strings:

```python
from typing import Annotated

def serve(
    app_dir: Annotated[str, 'Path to application'],
    port: Annotated[int, 'Server port'] = 8000,
):
    pass

opts = SmartOptions(serve, argv=['/path/to/app', '--port', '9000'])
print(opts["app_dir"])  # '/path/to/app'
print(opts["port"])     # 9000
```

## Composing with `+` Operator

The most powerful feature: compose multiple sources with priority:

```python
def serve(host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
    pass

# Priority: base < file < env < argv (rightmost wins)
opts = (
    SmartOptions(serve) +                    # defaults from signature
    SmartOptions('config.yaml') +            # file overrides
    SmartOptions('ENV:MYAPP') +              # env overrides
    SmartOptions(serve, sys.argv[1:])        # argv overrides (highest)
)
```

You can also add plain dicts:

```python
opts = SmartOptions({'a': 1}) + {'b': 2, 'a': 10}
print(opts["a"])  # 10 (dict overrides)
print(opts["b"])  # 2
```

## Nested Structures

### Nested Dicts Become SmartOptions

```python
opts = SmartOptions({
    'server': {
        'host': 'localhost',
        'port': 8080
    }
})

print(opts["server.host"])  # 'localhost'
print(opts["server.port"])  # 8080
```

### String Lists Become Feature Flags

```python
opts = SmartOptions({
    'middleware': ['cors', 'compression', 'logging']
})

print(opts["middleware.cors"])         # True
print(opts["middleware.compression"])  # True
print('cors' in opts["middleware"])    # True
```

### List of Dicts Indexed by First Key

```python
opts = SmartOptions({
    'apps': [
        {'name': 'shop', 'module': 'shop:ShopApp'},
        {'name': 'office', 'module': 'office:OfficeApp'},
    ]
})

print(opts["apps.shop.module"])    # 'shop:ShopApp'
print(opts["apps.office.module"])  # 'office:OfficeApp'
print('shop' in opts["apps"])      # True
```

## Filtering Options

### Ignore None Values

```python
opts = SmartOptions(
    incoming={'timeout': None},
    defaults={'timeout': 10},
    ignore_none=True
)

print(opts["timeout"])  # 10 (default kept)
```

### Ignore Empty Collections

```python
opts = SmartOptions(
    incoming={'tags': [], 'name': ''},
    defaults={'tags': ['prod'], 'name': 'default'},
    ignore_empty=True
)

print(opts["tags.prod"])  # True (feature flag)
print(opts["name"])       # 'default'
```

### Custom Filter Function

```python
def only_positive(key, value):
    return isinstance(value, (int, float)) and value > 0

opts = SmartOptions(
    incoming={'timeout': -5, 'retries': 3},
    defaults={'timeout': 30, 'retries': 1},
    filter_fn=only_positive
)

print(opts["timeout"])  # 30 (negative filtered)
print(opts["retries"])  # 3 (positive, accepted)
```

## Access Patterns

```python
opts = SmartOptions({'a': 1, 'b': 2})

# Path notation (primary)
print(opts["a"])        # 1
print(opts["missing"])  # None (no error)

# Nested path access
print(opts["x.y.z"])    # None (missing path)

# Containment
print('a' in opts)   # True

# Iteration
for key in opts:
    print(key)       # 'a', 'b'

# Convert to dict
d = opts.as_dict()   # {'a': 1, 'b': 2}
```

## Real-World Example

Complete CLI application configuration:

```python
from typing import Annotated
from genro_toolbox import SmartOptions
import sys

def serve(
    app_dir: Annotated[str, 'Path to application directory'],
    host: Annotated[str, 'Server host'] = '127.0.0.1',
    port: Annotated[int, 'Server port'] = 8000,
    workers: Annotated[int, 'Number of workers'] = 4,
    debug: Annotated[bool, 'Enable debug mode'] = False,
):
    """Start the application server."""
    # Option 1: Single SmartOptions with env and argv (recommended)
    config = (
        SmartOptions('config.yaml') +              # 1. Config file
        SmartOptions('config.local.yaml') +        # 2. Local overrides
        SmartOptions(serve, env='MYAPP', argv=sys.argv[1:])  # 3. defaults < env < argv
    )

    # Option 2: Compose with + operator for full control
    # config = (
    #     SmartOptions(serve) +                    # 1. Function defaults
    #     SmartOptions('config.yaml') +            # 2. Config file
    #     SmartOptions('ENV:MYAPP') +              # 3. Environment (strings)
    #     SmartOptions(serve, sys.argv[1:])        # 4. CLI args (highest)
    # )

    print(f"Starting server at {config['host']}:{config['port']}")
    print(f"App: {config['app_dir']}, Workers: {config['workers']}")
    if config["debug"]:
        print("Debug mode enabled")

if __name__ == '__main__':
    serve()
```

Config file (`config.yaml`):

```yaml
host: 0.0.0.0
workers: 8
middleware:
  - cors
  - compression
apps:
  - name: api
    module: api:app
  - name: admin
    module: admin:app
```

Usage:

```bash
# Use defaults + config file
./app.py /path/to/app

# Override port via CLI
./app.py /path/to/app --port 9000 --debug

# Override via environment
MYAPP_WORKERS=16 ./app.py /path/to/app
```

## API Reference

```python
class SmartOptions(TreeDict):
    """
    Convenience namespace for option management, built on TreeDict.

    Args:
        incoming: One of:
            - Mapping with runtime kwargs
            - str path to config file (YAML, JSON, TOML, INI)
            - str 'ENV:PREFIX' for environment variables
            - Path object to config file
            - Callable to extract defaults from signature
        defaults: One of:
            - Mapping with baseline options
            - list[str] as argv when incoming is callable (legacy)
            - None
        env: Environment variable prefix (e.g., "MYAPP" for MYAPP_HOST).
            Only used when incoming is a callable. Types from signature
            are used for conversion.
        argv: Command line arguments list. Only used when incoming is
            a callable. Types from signature are used for conversion.
        ignore_none: Skip incoming entries where value is None
        ignore_empty: Skip empty strings/collections from incoming
        filter_fn: Custom filter callable(key, value) -> bool

    When incoming is a callable with env/argv:
        - Defaults come from function signature
        - env values override defaults (with type conversion)
        - argv values override env (with type conversion)
        Priority: defaults < env < argv

    Operators:
        +: Merge two SmartOptions (right side wins)
        in: Check key existence
        []: Path notation access (returns None for missing)
    """

    def as_dict(self) -> dict[str, Any]:
        """Return a copy of current options as dict."""
        ...

    def __add__(self, other) -> SmartOptions:
        """Merge with another SmartOptions or dict."""
        ...
```

## See Also

- [extract_kwargs Guide](extract-kwargs.md) - Prefix-based kwargs extraction
- [Best Practices](best-practices.md) - Production patterns
- [API Reference](../api/reference.md) - Complete API documentation
