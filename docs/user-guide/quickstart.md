# Quick Start

Get started with Genro-Toolbox in 5 minutes.

## Installation

```bash
pip install genro-toolbox
```

## Basic Usage

The `extract_kwargs` decorator is the main feature of Genro-Toolbox. It extracts keyword arguments by prefix into separate parameter groups.

### Example: Service Configuration

```python
from genro_toolbox import extract_kwargs

class MyService:
    @extract_kwargs(logging=True, cache=True)
    def __init__(self, name, logging_kwargs=None, cache_kwargs=None, **kwargs):
        self.name = name
        self.logging_config = logging_kwargs or {}
        self.cache_config = cache_kwargs or {}
        self.other_config = kwargs

    def show_config(self):
        print(f"Service: {self.name}")
        print(f"Logging: {self.logging_config}")
        print(f"Cache: {self.cache_config}")
        print(f"Other: {self.other_config}")

# Create service with prefixed parameters
service = MyService(
    name="api",
    logging_level="INFO",      # → logging_kwargs
    logging_format="json",     # → logging_kwargs
    cache_ttl=300,             # → cache_kwargs
    cache_backend="redis",     # → cache_kwargs
    timeout=30                 # → kwargs
)

service.show_config()
# Output:
# Service: api
# Logging: {'level': 'INFO', 'format': 'json'}
# Cache: {'ttl': 300, 'backend': 'redis'}
# Other: {'timeout': 30}
```

## Three Calling Styles

Genro-Toolbox supports three convenient ways to pass parameters:

### Style 1: Prefix Style (Most Explicit)

```python
service = MyService(
    name="api",
    logging_level="INFO",
    logging_format="json"
)
# logging_kwargs = {'level': 'INFO', 'format': 'json'}
```

### Style 2: Dict Style (Compact)

```python
service = MyService(
    name="api",
    logging={'level': 'INFO', 'format': 'json'}
)
# Same result as Style 1
```

### Style 3: Boolean Activation (Use Defaults)

```python
service = MyService(
    name="api",
    logging=True  # Activates with empty dict
)
# logging_kwargs = {}
```

## Multiple Prefix Families

Extract multiple groups of parameters:

```python
@extract_kwargs(logging=True, cache=True, db=True)
def setup_app(name, logging_kwargs=None, cache_kwargs=None, db_kwargs=None, **kwargs):
    print(f"Logging: {logging_kwargs}")
    print(f"Cache: {cache_kwargs}")
    print(f"Database: {db_kwargs}")
    print(f"Other: {kwargs}")

# All these parameters are organized automatically
setup_app(
    name="myapp",
    logging_level="DEBUG",
    logging_file="app.log",
    cache_ttl=600,
    cache_backend="memcached",
    db_host="localhost",
    db_port=5432,
    db_name="mydb",
    timeout=30
)
```

## Why Use extract_kwargs?

### Problem: Nested Configuration is Messy

**Without extract_kwargs** (verbose and unclear):

```python
def connect(host, port,
            logging_level=None, logging_format=None, logging_file=None,
            cache_ttl=None, cache_backend=None):
    # Too many parameters!
    logger = Logger(level=logging_level, format=logging_format, file=logging_file)
    cache = Cache(ttl=cache_ttl, backend=cache_backend)
```

**With extract_kwargs** (clean and flexible):

```python
@extract_kwargs(logging=True, cache=True)
def connect(host, port, logging_kwargs=None, cache_kwargs=None):
    if logging_kwargs:
        logger = Logger(**logging_kwargs)
    if cache_kwargs:
        cache = Cache(**cache_kwargs)
```

## Next Steps

- [Full extract_kwargs Guide](extract-kwargs.md) - Learn all features
- [Best Practices](best-practices.md) - Production patterns
- [Examples](../examples/index.md) - Real-world use cases
- [API Reference](../api/reference.md) - Complete API documentation
