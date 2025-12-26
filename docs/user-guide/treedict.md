# TreeDict

TreeDict is a hierarchical dictionary that provides dot notation path access to nested data structures.

## Basic Usage

```python
from genro_toolbox import TreeDict

# Create from nested dict
td = TreeDict({"user": {"name": "Alice", "prefs": {"theme": "dark"}}})

# Path string access
td["user.name"]         # "Alice"
td["user.prefs.theme"]  # "dark"

# Missing keys return None (no KeyError)
td["missing"]           # None
td["user.missing"]      # None
```

## Creating TreeDict

### From dict

```python
td = TreeDict({"a": {"b": {"c": 1}}})
```

### From JSON string

```python
td = TreeDict('{"user": {"name": "Alice"}}')
```

### From config file

```python
# Supports JSON, YAML, TOML, INI
td = TreeDict.from_file("config.yaml")
td = TreeDict.from_file("settings.json")
td = TreeDict.from_file("config.toml")
td = TreeDict.from_file("app.ini")
```

### Empty TreeDict

```python
td = TreeDict()
td["settings.theme"] = "dark"  # auto-creates intermediate dicts
```

## Writing Values

TreeDict auto-creates intermediate dictionaries when writing:

```python
td = TreeDict()

# This creates {"settings": {"db": {"host": "localhost"}}}
td["settings.db.host"] = "localhost"
td["settings.db.port"] = 5432

td.as_dict()
# {"settings": {"db": {"host": "localhost", "port": 5432}}}
```

## List Access

Use `#N` syntax to access list elements:

```python
td = TreeDict({
    "users": [
        {"name": "Alice", "role": "admin"},
        {"name": "Bob", "role": "user"}
    ]
})

td["users.#0.name"]   # "Alice"
td["users.#1.role"]   # "user"
td["users.#0"]        # {"name": "Alice", "role": "admin"}
```

## Deleting Keys

```python
td = TreeDict({"a": {"b": 1, "c": 2}})

del td["a.b"]
td.as_dict()  # {"a": {"c": 2}}

# Delete from list
td = TreeDict({"items": [1, 2, 3]})
del td["items.#0"]
td["items"]  # [2, 3]
```

## Walking All Paths

Iterate over all paths and values:

```python
td = TreeDict({
    "user": {"name": "Alice"},
    "settings": {"theme": "dark"}
})

for path, value in td.walk():
    print(f"{path} = {value}")

# Output:
# user.name = Alice
# settings.theme = dark
```

### Expanding Lists

```python
td = TreeDict({"items": [{"id": 1}, {"id": 2}]})

for path, value in td.walk(expand_lists=True):
    print(f"{path} = {value}")

# Output:
# items.#0.id = 1
# items.#1.id = 2
```

## Thread-Safe Access

TreeDict provides context managers for thread-safe operations:

### Synchronous (threading)

```python
td = TreeDict({"counter": 0})

# Thread-safe read-modify-write
with td:
    td["counter"] = td["counter"] + 1
```

### Asynchronous (asyncio)

```python
td = TreeDict({"counter": 0})

async with td:
    td["counter"] = td["counter"] + 1
```

The lock protects all operations within the `with` block. Always use the root TreeDict for locking.

## Converting Back to Dict

```python
td = TreeDict({"user": {"name": "Alice"}})

# Get underlying data
data = td.as_dict()  # {"user": {"name": "Alice"}}
```

## SmartOptions Relationship

`SmartOptions` extends `TreeDict` with additional features for configuration management:

```python
from genro_toolbox import SmartOptions

# SmartOptions IS-A TreeDict
opts = SmartOptions({"server": {"host": "localhost"}})
opts["server.host"]  # "localhost" - TreeDict path access works
```

See [SmartOptions Guide](smart-options.md) for configuration-specific features.

## Use Cases

### Configuration Access

```python
config = TreeDict.from_file("config.yaml")

db_host = config["database.host"]
db_port = config["database.port"]
debug = config["app.debug"]
```

### Building Nested Structures

```python
response = TreeDict()
response["status"] = "success"
response["data.user.id"] = 123
response["data.user.name"] = "Alice"
response["meta.timestamp"] = "2025-01-01"

response.as_dict()
# {
#     "status": "success",
#     "data": {"user": {"id": 123, "name": "Alice"}},
#     "meta": {"timestamp": "2025-01-01"}
# }
```

### Safe Navigation

```python
# No need for defensive coding
config = TreeDict({"app": {}})

# These return None instead of raising KeyError
config["app.missing.deep.path"]  # None
config["nonexistent"]            # None
```
