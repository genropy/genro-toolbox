# MultiDefault Guide

Complete guide to using `MultiDefault` for multi-source configuration loading.

## Overview

`MultiDefault` loads configuration from multiple sources and merges them into a single flat dictionary. It implements the `Mapping` protocol, making it directly usable as the `defaults` parameter of `SmartOptions`.

**Key Features**:
- Load from multiple sources (dict, files, environment variables)
- Later sources override earlier ones
- Automatic flattening of nested structures
- Explicit type conversion with `types` parameter
- Skip missing files with `skip_missing=True`
- Supports `.ini`, `.json`, `.toml`, `.yaml` files

## Basic Usage

```python
from genro_toolbox import MultiDefault, SmartOptions

# Load from multiple sources
defaults = MultiDefault(
    {'server_host': '0.0.0.0', 'server_port': 8000},  # base defaults
    'config.ini',                                       # file config
    'ENV:MYAPP',                                        # env vars
)

# Use with SmartOptions
opts = SmartOptions(
    incoming={'server_port': 9000},
    defaults=defaults,
)

print(opts.server_host)  # from file or env
print(opts.server_port)  # 9000 (from incoming)
```

## Supported Sources

### Python Dictionary

Dictionaries are used directly. Nested dicts are flattened with underscore separator:

```python
defaults = MultiDefault(
    {'server': {'host': 'localhost', 'port': 8000}}
)

# Results in: {'server_host': 'localhost', 'server_port': '8000'}
print(defaults['server_host'])  # 'localhost'
```

### INI Files

Standard ConfigParser format. **All values are strings**.

```ini
# config.ini
[server]
host = localhost
port = 8000

[logging]
level = INFO
```

```python
defaults = MultiDefault('config.ini')

# Results in: {'server_host': 'localhost', 'server_port': '8000', 'logging_level': 'INFO'}
print(defaults['server_port'])  # '8000' (string!)
```

### JSON Files

JSON format. **Types are preserved** (int, float, bool, etc.).

```json
{
    "server": {
        "host": "localhost",
        "port": 8000
    },
    "debug": true
}
```

```python
defaults = MultiDefault('config.json')

print(defaults['server_port'])  # 8000 (int!)
print(defaults['debug'])        # True (bool!)
```

### TOML Files

TOML format (requires Python 3.11+ or `tomli` package). **Types are preserved**.

```toml
[server]
host = "localhost"
port = 8000

[features]
debug = true
timeout = 30.5
```

```python
defaults = MultiDefault('config.toml')

print(defaults['server_port'])      # 8000 (int)
print(defaults['features_timeout']) # 30.5 (float)
```

### YAML Files

YAML format (requires `pyyaml` package). **Types are preserved**.

```yaml
server:
  host: localhost
  port: 8000

features:
  debug: true
  tags:
    - api
    - v2
```

```python
defaults = MultiDefault('config.yaml')

print(defaults['server_port'])    # 8000 (int)
print(defaults['features_tags'])  # ['api', 'v2'] (list)
```

### Environment Variables

Load from environment variables with a prefix. **All values are strings**.

```bash
export MYAPP_SERVER_HOST=localhost
export MYAPP_SERVER_PORT=8000
export MYAPP_DEBUG=true
```

```python
defaults = MultiDefault('ENV:MYAPP')

# Results in: {'server_host': 'localhost', 'server_port': '8000', 'debug': 'true'}
print(defaults['server_port'])  # '8000' (string!)
```

## Type Conversion

By default, values from `.ini` files and environment variables are strings. Use the `types` parameter for explicit conversion:

```python
defaults = MultiDefault(
    'config.ini',
    'ENV:MYAPP',
    types={
        'server_port': int,
        'features_debug': bool,
        'features_timeout': float,
    }
)

print(defaults['server_port'])      # 8000 (int)
print(defaults['features_debug'])   # True (bool)
print(defaults['features_timeout']) # 30.5 (float)
```

### Boolean Conversion

String values are converted to `True` if they match (case-insensitive):
- `"true"`, `"yes"`, `"on"`, `"1"`

All other values convert to `False`.

```python
defaults = MultiDefault(
    {'debug': 'yes', 'verbose': 'no'},
    types={'debug': bool, 'verbose': bool}
)

print(defaults['debug'])    # True
print(defaults['verbose'])  # False
```

## Priority Order

Sources are processed in order, with later sources overriding earlier ones:

```
hardcoded dict < config file < local file < env vars < incoming (SmartOptions)
```

Example:

```python
# config.ini has server_port = 8000
# Environment has MYAPP_SERVER_PORT=9000

defaults = MultiDefault(
    {'server_port': 7000},  # lowest priority
    'config.ini',            # overrides dict
    'ENV:MYAPP',             # overrides file
    types={'server_port': int}
)

print(defaults['server_port'])  # 9000 (from env)

# SmartOptions incoming has highest priority
opts = SmartOptions(
    incoming={'server_port': 5000},
    defaults=defaults,
)

print(opts.server_port)  # 5000 (from incoming)
```

## Skip Missing Files

Use `skip_missing=True` to silently ignore missing files:

```python
defaults = MultiDefault(
    'base.ini',        # must exist
    'local.ini',       # may not exist
    'ENV:MYAPP',
    skip_missing=True,
)
```

Without `skip_missing`, a `FileNotFoundError` is raised for missing files.

## Flattening Nested Structures

Nested dictionaries are flattened using underscore as separator:

```python
data = {
    'server': {
        'host': 'localhost',
        'ssl': {
            'enabled': True,
            'cert': '/path/to/cert'
        }
    }
}

defaults = MultiDefault(data)

print(defaults['server_host'])        # 'localhost'
print(defaults['server_ssl_enabled']) # True
print(defaults['server_ssl_cert'])    # '/path/to/cert'
```

## Integration with SmartOptions

`MultiDefault` is designed to work seamlessly with `SmartOptions`:

```python
from genro_toolbox import MultiDefault, SmartOptions

class AppConfig:
    DEFAULTS = {
        'server_host': '0.0.0.0',
        'server_port': 8000,
        'server_debug': False,
        'cache_ttl': 300,
    }

    def __init__(self, config_file=None, **kwargs):
        sources = [self.DEFAULTS]
        if config_file:
            sources.append(config_file)
        sources.append('ENV:MYAPP')

        defaults = MultiDefault(
            *sources,
            skip_missing=True,
            types={
                'server_port': int,
                'server_debug': bool,
                'cache_ttl': int,
            }
        )

        self.opts = SmartOptions(
            incoming=kwargs,
            defaults=defaults,
            ignore_none=True,
        )

    @property
    def server_port(self):
        return self.opts.server_port

# Usage
config = AppConfig('config.ini', server_debug=True)
print(config.opts.server_host)   # from file or env
print(config.opts.server_port)   # from file or env (int)
print(config.opts.server_debug)  # True (from kwargs)
```

## Extracting Grouped Config

Use `dictExtract` to extract a subset of configuration by prefix:

```python
from genro_toolbox import MultiDefault, SmartOptions, dictExtract

defaults = MultiDefault(
    'config.ini',
    types={'server_port': int, 'cache_ttl': int}
)

opts = SmartOptions(defaults=defaults)

# Extract only server-related config
server_config = dictExtract(opts.as_dict(), 'server_')
# {'host': 'localhost', 'port': 8000}

# Extract only cache-related config
cache_config = dictExtract(opts.as_dict(), 'cache_')
# {'ttl': 300, 'backend': 'redis'}
```

## API Reference

```python
class MultiDefault(Mapping[str, Any]):
    """
    Multi-source configuration loader.

    Args:
        *sources: Configuration sources. Can be:
            - dict: Used directly (flattened if nested)
            - str (file path): Load from file (.ini, .json, .toml, .yaml)
            - str "ENV:PREFIX": Load from environment variables
            - pathlib.Path: Load from file

        skip_missing: If True, silently skip missing files.
            Default: False.

        types: Dict mapping keys to types for explicit conversion.
            Example: {'port': int, 'debug': bool}
    """

    def __init__(
        self,
        *sources: Any,
        skip_missing: bool = False,
        types: dict[str, type] | None = None,
    ): ...

    def resolve(self) -> dict[str, Any]:
        """Resolve all sources and return merged flat dictionary."""
        ...

    @property
    def sources(self) -> tuple[Any, ...]:
        """Original source specifications."""
        ...

    @property
    def skip_missing(self) -> bool:
        """Whether missing files are skipped."""
        ...

    @property
    def types(self) -> dict[str, type]:
        """Type conversion map."""
        ...
```

## Helper Functions

```python
# Flatten nested dict
from genro_toolbox.multi_default import flatten_dict

flat = flatten_dict({'a': {'b': 1}})  # {'a_b': 1}

# Load specific file types
from genro_toolbox.multi_default import load_ini, load_json, load_toml, load_yaml

ini_data = load_ini('config.ini')
json_data = load_json('config.json')
toml_data = load_toml('config.toml')
yaml_data = load_yaml('config.yaml')

# Load from environment
from genro_toolbox.multi_default import load_env

env_data = load_env('MYAPP')  # {'server_host': '...', ...}
```

## See Also

- [SmartOptions Guide](smart-options.md) - Intelligent options merging
- [Best Practices](best-practices.md) - Production patterns
- [API Reference](../api/reference.md) - Complete API documentation
