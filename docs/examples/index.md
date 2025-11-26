# Examples

Real-world examples of using Genro-Toolbox.

## Genro Integration

Genro-Toolbox was designed to support Genro Kyō. Here's how it's used:

```python
from genro_toolbox import extract_kwargs

class Service:
    @extract_kwargs(logging=True, async_mode=True, plugins=True)
    def __init__(
        self,
        name=None,
        logging_kwargs=None,
        async_mode_kwargs=None,
        plugins_kwargs=None,
        **kwargs
    ):
        self.name = name or "service"

        # Setup logging plugin
        if logging_kwargs:
            self.plug(LoggingPlugin, **logging_kwargs)

        # Setup async mode
        if async_mode_kwargs:
            self.plug(AsyncPlugin, **async_mode_kwargs)

        # Custom plugins
        if plugins_kwargs:
            for plugin_name, plugin_config in plugins_kwargs.items():
                self.plug(plugin_name, **plugin_config)

# Usage
svc = Service(
    name="my_service",
    logging_level="DEBUG",
    logging_mode="silent",
    async_mode_enabled=True,
    async_mode_pool_size=10
)
```

## Web Framework Configuration

```python
from genro_toolbox import extract_kwargs

class WebApplication:
    @extract_kwargs(server=True, database=True, cache=True, auth=True)
    def __init__(
        self,
        name: str,
        server_kwargs=None,
        database_kwargs=None,
        cache_kwargs=None,
        auth_kwargs=None
    ):
        self.name = name

        # Server configuration
        self.server = self._setup_server(server_kwargs or {})

        # Database configuration
        self.db = self._setup_database(database_kwargs or {})

        # Cache configuration
        self.cache = self._setup_cache(cache_kwargs or {})

        # Auth configuration
        self.auth = self._setup_auth(auth_kwargs or {})

    def _setup_server(self, config):
        from werkzeug.serving import run_simple
        return {
            'host': config.get('host', '0.0.0.0'),
            'port': config.get('port', 8000),
            'threaded': config.get('threaded', True)
        }

    def _setup_database(self, config):
        from sqlalchemy import create_engine
        url = config.get('url', 'sqlite:///app.db')
        return create_engine(url, **config.get('options', {}))

    def _setup_cache(self, config):
        backend = config.get('backend', 'memory')
        if backend == 'redis':
            import redis
            return redis.Redis(**config.get('redis_options', {}))
        return {}

    def _setup_auth(self, config):
        return {
            'secret_key': config.get('secret_key', 'change-me'),
            'algorithm': config.get('algorithm', 'HS256'),
            'expiration': config.get('expiration', 3600)
        }

# Create application
app = WebApplication(
    name="myapp",
    server_host="0.0.0.0",
    server_port=8080,
    server_threaded=True,
    database_url="postgresql://localhost/mydb",
    cache_backend="redis",
    cache_redis_host="localhost",
    cache_redis_port=6379,
    auth_secret_key="my-secret-key",
    auth_expiration=7200
)
```

## CLI Tool Configuration

```python
import click
from genro_toolbox import extract_kwargs

class CLITool:
    @extract_kwargs(output=True, logging=True, performance=True)
    def __init__(
        self,
        output_kwargs=None,
        logging_kwargs=None,
        performance_kwargs=None
    ):
        self.output_config = output_kwargs or {}
        self.logging_config = logging_kwargs or {}
        self.perf_config = performance_kwargs or {}

    def run(self, data):
        # Apply configurations
        pass

@click.command()
@click.option('--output-format', default='json')
@click.option('--output-pretty/--output-compact', default=True)
@click.option('--logging-level', default='INFO')
@click.option('--logging-file', default=None)
@click.option('--performance-measure/--no-performance-measure', default=False)
def main(**kwargs):
    tool = CLITool(**kwargs)
    tool.run(data)
```

## Data Pipeline

```python
from genro_toolbox import extract_kwargs

class DataPipeline:
    @extract_kwargs(source=True, transform=True, sink=True, monitoring=True)
    def __init__(
        self,
        name: str,
        source_kwargs=None,
        transform_kwargs=None,
        sink_kwargs=None,
        monitoring_kwargs=None
    ):
        self.name = name

        # Setup source
        self.source = self._create_source(source_kwargs or {})

        # Setup transformations
        self.transforms = self._create_transforms(transform_kwargs or {})

        # Setup sink
        self.sink = self._create_sink(sink_kwargs or {})

        # Setup monitoring
        if monitoring_kwargs:
            self.monitor = self._create_monitor(monitoring_kwargs)

    def _create_source(self, config):
        source_type = config.get('type', 'file')
        if source_type == 'file':
            return FileSource(config.get('path'))
        elif source_type == 'database':
            return DatabaseSource(config.get('connection_string'))
        elif source_type == 'api':
            return APISource(config.get('endpoint'))

    def _create_transforms(self, config):
        transforms = []
        if config.get('normalize'):
            transforms.append(NormalizeTransform())
        if config.get('filter'):
            transforms.append(FilterTransform(config['filter']))
        if config.get('aggregate'):
            transforms.append(AggregateTransform(config['aggregate']))
        return transforms

    def _create_sink(self, config):
        sink_type = config.get('type', 'stdout')
        if sink_type == 'file':
            return FileSink(config.get('path'))
        elif sink_type == 'database':
            return DatabaseSink(config.get('connection_string'))
        return StdoutSink()

    def _create_monitor(self, config):
        return Monitor(
            metrics_enabled=config.get('metrics', True),
            tracing_enabled=config.get('tracing', False),
            logging_enabled=config.get('logging', True)
        )

# Usage
pipeline = DataPipeline(
    name="etl_pipeline",
    source_type="database",
    source_connection_string="postgresql://localhost/source_db",
    transform_normalize=True,
    transform_filter={"status": "active"},
    transform_aggregate={"by": "category"},
    sink_type="file",
    sink_path="/output/results.json",
    monitoring_metrics=True,
    monitoring_tracing=True
)
```

## See Also

- [User Guide](../user-guide/extract-kwargs.md) - Complete feature documentation
- [Best Practices](../user-guide/best-practices.md) - Production patterns
- [API Reference](../api/reference.md) - Full API
