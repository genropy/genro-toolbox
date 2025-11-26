# Best Practices

Production-ready patterns for using Genro-Toolbox effectively.

## General Guidelines

### 1. Always Use Type Hints

```python
from typing import Optional, Dict, Any
from genro_toolbox import extract_kwargs

class MyService:
    @extract_kwargs(logging=True, cache=True)
    def __init__(
        self,
        name: str,
        logging_kwargs: Optional[Dict[str, Any]] = None,
        cache_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        self.name = name
        # ...
```

Type hints help IDEs, type checkers, and documentation tools.

### 2. Document Expected Parameters

```python
@extract_kwargs(logging=True)
def setup_logger(self, logging_kwargs: Optional[Dict[str, Any]] = None):
    """Setup logger with configuration.

    Args:
        logging_kwargs: Logging configuration with keys:
            - level (str): Log level (DEBUG, INFO, WARNING, ERROR)
            - format (str): Log format string
            - file (str): Optional log file path
    """
    config = logging_kwargs or {}
    # ...
```

### 3. Provide Sensible Defaults

```python
@extract_kwargs(logging=True)
def my_method(self, logging_kwargs=None):
    # Merge with defaults
    config = {
        'level': 'INFO',
        'format': '%(asctime)s - %(message)s',
        **(logging_kwargs or {})
    }
    # Now config always has required keys
```

## Common Patterns

### Pattern 1: Plugin Configuration

Use `extract_kwargs` to configure plugins cleanly:

```python
class Application:
    @extract_kwargs(logging=True, metrics=True, tracing=True)
    def __init__(
        self,
        name: str,
        logging_kwargs=None,
        metrics_kwargs=None,
        tracing_kwargs=None,
        **kwargs
    ):
        self.name = name

        # Each plugin gets its own config
        if logging_kwargs:
            self.register_plugin(LoggingPlugin(**logging_kwargs))

        if metrics_kwargs:
            self.register_plugin(MetricsPlugin(**metrics_kwargs))

        if tracing_kwargs:
            self.register_plugin(TracingPlugin(**tracing_kwargs))

# Clean initialization
app = Application(
    name="myapp",
    logging_level="DEBUG",
    logging_file="app.log",
    metrics_port=9090,
    metrics_enabled=True,
    tracing_endpoint="http://jaeger:14268"
)
```

### Pattern 2: Nested Object Creation

```python
class DatabaseConnection:
    @extract_kwargs(pool=True, ssl=True, retry=True)
    def __init__(
        self,
        host: str,
        port: int,
        pool_kwargs=None,
        ssl_kwargs=None,
        retry_kwargs=None
    ):
        self.connection = self._connect(host, port)

        if pool_kwargs:
            self.pool = ConnectionPool(**pool_kwargs)

        if ssl_kwargs:
            self.ssl_context = SSLContext(**ssl_kwargs)

        if retry_kwargs:
            self.retry_policy = RetryPolicy(**retry_kwargs)

# Usage
db = DatabaseConnection(
    host="localhost",
    port=5432,
    pool_size=20,
    pool_timeout=30,
    ssl_cert_file="/path/to/cert",
    ssl_key_file="/path/to/key",
    retry_attempts=3,
    retry_backoff=2.0
)
```

### Pattern 3: Configuration from Files

```python
import yaml
from genro_toolbox import extract_kwargs

class Service:
    @extract_kwargs(logging=True, cache=True)
    def __init__(self, logging_kwargs=None, cache_kwargs=None):
        self.logging = logging_kwargs
        self.cache = cache_kwargs

# Load from YAML
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Pass entire dicts
service = Service(
    logging=config.get("logging", {}),
    cache=config.get("cache", {})
)
```

## Performance Considerations

### Minimize Decorator Overhead

The `extract_kwargs` decorator is optimized with constant reuse, but avoid unnecessary nesting:

```python
# Good - one decorator
@extract_kwargs(logging=True, cache=True, db=True)
def setup(logging_kwargs=None, cache_kwargs=None, db_kwargs=None):
    pass

# Avoid - multiple decorators (unnecessary overhead)
@extract_kwargs(logging=True)
@extract_kwargs(cache=True)
@extract_kwargs(db=True)
def setup(logging_kwargs=None, cache_kwargs=None, db_kwargs=None):
    pass
```

### Use pop=False Only When Needed

By default (`param=True`), extracted parameters are removed from `kwargs`. Use `pop=False` only if you need parameters in both places:

```python
# Default: pop=True (efficient)
@extract_kwargs(logging=True)

# Only if you need params in both places:
@extract_kwargs(logging={'pop': False})
```

## Error Handling

### Validate Extracted Configuration

```python
@extract_kwargs(logging=True)
def setup_logging(self, logging_kwargs=None):
    config = logging_kwargs or {}

    # Validate required parameters
    required = ['level', 'format']
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required logging params: {missing}")

    # Validate values
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    if config['level'] not in valid_levels:
        raise ValueError(f"Invalid log level: {config['level']}")

    # Now safe to use
    logger = Logger(**config)
```

### Handle Optional Configurations Gracefully

```python
@extract_kwargs(logging=True, cache=True)
def __init__(self, logging_kwargs=None, cache_kwargs=None):
    # Logging is optional
    if logging_kwargs:
        try:
            self.logger = Logger(**logging_kwargs)
        except Exception as e:
            warnings.warn(f"Failed to setup logger: {e}")
            self.logger = None

    # Cache is required
    if not cache_kwargs:
        raise ValueError("cache configuration is required")

    self.cache = Cache(**cache_kwargs)
```

## Testing

### Test with Different Calling Styles

```python
def test_service_initialization():
    # Test prefix style
    service1 = Service(
        name="test",
        logging_level="DEBUG",
        logging_format="json"
    )
    assert service1.logging['level'] == "DEBUG"

    # Test dict style
    service2 = Service(
        name="test",
        logging={'level': 'DEBUG', 'format': 'json'}
    )
    assert service2.logging == service1.logging

    # Test boolean activation
    service3 = Service(name="test", logging=True)
    assert service3.logging == {}
```

### Mock for Testing

```python
@pytest.fixture
def mock_service():
    @extract_kwargs(logging=True)
    def create_service(logging_kwargs=None):
        return {"logging": logging_kwargs}

    return create_service

def test_with_mock(mock_service):
    result = mock_service(logging_level="INFO")
    assert result["logging"]["level"] == "INFO"
```

## Security Considerations

### Sanitize Parameters

```python
@extract_kwargs(db=True)
def connect_database(self, db_kwargs=None):
    config = db_kwargs or {}

    # Sanitize sensitive data before logging
    safe_config = {k: v for k, v in config.items() if k != 'password'}
    logger.info(f"Connecting to database: {safe_config}")

    # Use full config for connection
    return connect(**config)
```

### Avoid Injection Risks

```python
@extract_kwargs(query=True)
def execute_query(self, sql: str, query_kwargs=None):
    params = query_kwargs or {}

    # NEVER construct SQL from kwargs directly
    # query = f"SELECT * FROM users WHERE {params}"  # SQL injection!

    # Use parameterized queries
    query = "SELECT * FROM users WHERE name = ? AND age = ?"
    cursor.execute(query, (params.get('name'), params.get('age')))
```

## Integration with Other Tools

### With Pydantic

```python
from pydantic import BaseModel
from genro_toolbox import extract_kwargs

class LoggingConfig(BaseModel):
    level: str = "INFO"
    format: str = "%(message)s"
    file: Optional[str] = None

class Service:
    @extract_kwargs(logging=True)
    def __init__(self, logging_kwargs=None):
        # Validate with Pydantic
        config = LoggingConfig(**(logging_kwargs or {}))
        self.logger = Logger(
            level=config.level,
            format=config.format,
            filename=config.file
        )
```

### With dataclasses

```python
from dataclasses import dataclass, asdict
from genro_toolbox import extract_kwargs

@dataclass
class CacheConfig:
    ttl: int = 300
    backend: str = "memory"
    max_size: int = 1000

class Service:
    @extract_kwargs(cache=True)
    def __init__(self, cache_kwargs=None):
        config = CacheConfig(**(cache_kwargs or {}))
        self.cache = Cache(**asdict(config))
```

## See Also

- [extract_kwargs Guide](extract-kwargs.md) - Full feature documentation
- [Examples](../examples/index.md) - Real-world examples
- [API Reference](../api/reference.md) - Complete API
