# SmartOptions Guide

Complete guide to using `SmartOptions` for intelligent option merging.

## Overview

`SmartOptions` is a convenient namespace class for managing configuration options with intelligent merging, filtering, and defaults.

**Key Features**:
- Merge incoming options with defaults
- Filter None values automatically
- Filter empty collections (strings, lists, dicts)
- Custom filter functions
- Attribute-style access with dict conversion

## Basic Usage

```python
from genro_toolbox import SmartOptions

# Incoming options override defaults
opts = SmartOptions(
    incoming={'timeout': 5},
    defaults={'timeout': 1, 'retries': 3}
)

print(opts.timeout)  # 5 (from incoming)
print(opts.retries)  # 3 (from defaults)
```

## Filtering Options

### Ignore None Values

When `ignore_none=True`, None values in incoming options are skipped, preserving defaults:

```python
opts = SmartOptions(
    incoming={'timeout': None, 'tags': []},
    defaults={'timeout': 10, 'tags': ['default']},
    ignore_none=True
)

print(opts.timeout)  # 10 (default kept, None ignored)
```

### Ignore Empty Collections

When `ignore_empty=True`, empty strings, lists, dicts, etc. are skipped:

```python
opts = SmartOptions(
    incoming={'tags': [], 'name': ''},
    defaults={'tags': ['prod'], 'name': 'default'},
    ignore_empty=True
)

print(opts.tags)  # ['prod'] (default kept, empty list ignored)
print(opts.name)  # 'default' (default kept, empty string ignored)
```

**Empty values** include:
- Empty strings: `""`
- Empty lists: `[]`
- Empty tuples: `()`
- Empty dicts: `{}`
- Empty sets: `set()`

### Custom Filter Function

Use `filter_fn` for custom filtering logic:

```python
def only_positive(key, value):
    """Keep only positive numbers."""
    return isinstance(value, (int, float)) and value > 0

opts = SmartOptions(
    incoming={'timeout': -5, 'retries': 3, 'port': 0},
    defaults={'timeout': 30, 'retries': 1, 'port': 8080},
    filter_fn=only_positive
)

print(opts.timeout)  # 30 (negative filtered, default kept)
print(opts.retries)  # 3 (positive, accepted)
print(opts.port)     # 8080 (zero filtered, default kept)
```

## Converting to Dict

Use `as_dict()` to get a dictionary copy:

```python
opts = SmartOptions({'timeout': 2}, {})
config_dict = opts.as_dict()

print(config_dict)  # {'timeout': 2}

# Modifications don't affect original
config_dict['timeout'] = 99
print(opts.timeout)  # 2 (unchanged)
```

## Dynamic Attributes

SmartOptions supports dynamic attribute modification:

```python
opts = SmartOptions({'timeout': 2}, {})

# Update existing attribute
opts.timeout = 7
print(opts.as_dict())  # {'timeout': 7}

# Add new attribute
opts.new_flag = True
print(opts.as_dict())  # {'timeout': 7, 'new_flag': True}

# Delete attribute
del opts.timeout
print(opts.as_dict())  # {'new_flag': True}
```

## Use Cases

### API Client Configuration

```python
class APIClient:
    def __init__(self, **kwargs):
        # Merge user config with defaults
        self.config = SmartOptions(
            incoming=kwargs,
            defaults={
                'timeout': 30,
                'retries': 3,
                'verify_ssl': True,
                'user_agent': 'SmartClient/1.0'
            },
            ignore_none=True  # User can pass None to skip override
        )

    def request(self, url):
        response = requests.get(
            url,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers={'User-Agent': self.config.user_agent}
        )
        return response

# Use with defaults
client = APIClient()

# Override some settings
client = APIClient(timeout=60, retries=5)

# Explicitly keep default by passing None
client = APIClient(timeout=None, retries=10)
```

### Plugin Configuration

```python
class Plugin:
    def configure(self, user_config=None, **kwargs):
        # Combine explicit config with kwargs
        all_config = {**(user_config or {}), **kwargs}

        self.options = SmartOptions(
            incoming=all_config,
            defaults=self.get_defaults(),
            ignore_empty=True  # Empty values mean "use default"
        )

    def get_defaults(self):
        return {
            'enabled': True,
            'log_level': 'INFO',
            'cache_size': 100,
            'workers': 4
        }

# Configure with dict
plugin.configure({'log_level': 'DEBUG'})

# Configure with kwargs
plugin.configure(enabled=False, workers=8)

# Mix both
plugin.configure({'log_level': 'WARNING'}, cache_size=200)
```

### CLI Argument Processing

```python
import argparse

def process_cli_args(args):
    """Process CLI args, falling back to config file defaults."""

    # Load defaults from config file
    with open('config.json') as f:
        file_config = json.load(f)

    # Merge: CLI args override file config
    opts = SmartOptions(
        incoming=vars(args),  # argparse Namespace → dict
        defaults=file_config,
        ignore_none=True  # argparse sets None for unspecified args
    )

    return opts

parser = argparse.ArgumentParser()
parser.add_argument('--host', default=None)
parser.add_argument('--port', type=int, default=None)
args = parser.parse_args()

config = process_cli_args(args)
# Unspecified CLI args fall back to config file
```

## Combining with extract_kwargs

SmartOptions works great with `extract_kwargs`:

```python
from genro_toolbox import extract_kwargs, SmartOptions

class Service:
    DEFAULT_LOGGING = {
        'level': 'INFO',
        'format': 'json',
        'file': None
    }

    @extract_kwargs(logging=True)
    def __init__(self, name, logging_kwargs=None):
        self.name = name

        # Merge user logging config with defaults
        self.logging = SmartOptions(
            incoming=logging_kwargs,
            defaults=self.DEFAULT_LOGGING,
            ignore_none=True
        )

        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=self.logging.level,
            format=self.logging.format
        )

# All logging options from defaults
service = Service('api')

# Override specific logging options
service = Service('api', logging_level='DEBUG')

# Or use dict style
service = Service('api', logging={'level': 'WARNING', 'file': 'app.log'})
```

## API Reference

```python
class SmartOptions(SimpleNamespace):
    """
    Convenience namespace for option management.

    Args:
        incoming: Mapping with runtime kwargs (can be None)
        defaults: Mapping with baseline options (can be None)
        ignore_none: Skip incoming entries where value is None
        ignore_empty: Skip empty strings/collections from incoming
        filter_fn: Custom filter callable(key, value) → bool
    """

    def __init__(
        self,
        incoming: Optional[Mapping[str, Any]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
        *,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Optional[Callable[[str, Any], bool]] = None,
    ): ...

    def as_dict(self) -> Dict[str, Any]:
        """Return a copy of current options as dict."""
        ...
```

## See Also

- [extract_kwargs Guide](extract-kwargs.md) - Prefix-based kwargs extraction
- [Best Practices](best-practices.md) - Production patterns
- [API Reference](../api/reference.md) - Complete API documentation
