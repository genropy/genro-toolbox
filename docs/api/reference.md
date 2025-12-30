# API Reference

Complete API documentation for Genro-Toolbox.

## extract_kwargs

```{eval-rst}
.. autofunction:: genro_toolbox.extract_kwargs
```

### Function Signature

```python
def extract_kwargs(
    _adapter: Optional[str] = None,
    _dictkwargs: Optional[Dict[str, Any]] = None,
    **extraction_specs: Any
) -> Callable[[F], F]
```

### Parameters

**_adapter** : `Optional[str]`
: Name of a method on `self` that will be called to pre-process `kwargs` before extraction.
  The adapter method receives the `kwargs` dict and can modify it in-place.

**_dictkwargs** : `Optional[Dict[str, Any]]`
: Optional dictionary of extraction specifications. When provided, this is used instead of `**extraction_specs`.
  Useful for dynamic extraction specifications.

**extraction_specs** : `Any`
: Keyword arguments where keys are prefix names and values specify extraction behavior:
  - `True`: Extract parameters with this prefix and remove them from source (`pop=True`)
  - `dict`: Custom extraction options (`pop`, `slice_prefix`, `is_list`)

### Returns

**Callable[[F], F]**
: Decorated function that performs kwargs extraction

### Examples

See [extract_kwargs Guide](../user-guide/extract-kwargs.md) for detailed examples.

## SmartOptions

```{eval-rst}
.. autoclass:: genro_toolbox.SmartOptions
   :members:
   :special-members: __init__
```

### Class Signature

```python
class SmartOptions(TreeDict):
    def __init__(
        self,
        incoming: Mapping[str, Any] | str | Path | Callable[..., Any] | None = None,
        defaults: Mapping[str, Any] | list[str] | None = None,
        *,
        env: str | None = None,
        argv: list[str] | None = None,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Callable[[str, Any], bool] | None = None,
    )
```

### Parameters

**incoming** : `Mapping | str | Path | Callable | None`
: One of:
  - Mapping with runtime kwargs
  - str path to config file (YAML, JSON, TOML, INI)
  - str 'ENV:PREFIX' for environment variables
  - Path object to config file
  - Callable to extract defaults from signature

**defaults** : `Mapping | list[str] | None`
: Mapping with baseline options, or argv list when incoming is callable (legacy).

**env** : `str | None`
: Environment variable prefix (e.g., "MYAPP" for MYAPP_HOST). Only used when incoming is callable.

**argv** : `list[str] | None`
: Command line arguments list. Only used when incoming is callable.

**ignore_none** : `bool`
: When True, skip incoming entries where the value is `None`. Default: False.

**ignore_empty** : `bool`
: When True, skip empty strings/collections from incoming entries. Default: False.

**filter_fn** : `Callable[[str, Any], bool] | None`
: Optional custom filter function receiving `(key, value)` and returning True if the pair should be kept.

### Methods

**as_dict() → dict[str, Any]**
: Return a copy of current options as a dictionary.

**__add__(other) → SmartOptions**
: Merge two SmartOptions (right side wins).

### Examples

See [SmartOptions Guide](../user-guide/smart-options.md) for detailed examples.

## TreeDict

```{eval-rst}
.. autoclass:: genro_toolbox.TreeDict
   :members:
   :special-members: __init__, __getitem__, __setitem__, __delitem__
```

### Class Signature

```python
class TreeDict:
    def __init__(
        self,
        data: dict[str, Any] | str | None = None,
    )
```

### Parameters

**data** : `dict | str | None`
: Initial data. Can be:
  - dict: Used directly as underlying data
  - str: Parsed as JSON
  - None: Empty TreeDict

### Key Features

- **Path string access**: `td["a.b.c"]` accesses nested keys
- **Auto-creates intermediate dicts** on write
- **Returns None for missing keys** (no KeyError)
- **List access with #N syntax**: `td["items.#0.id"]`
- **Thread-safe access** via context manager
- **Async-safe access** via async context manager

### Methods

**as_dict() → dict[str, Any]**
: Return underlying data as dict.

**walk(expand_lists: bool = False) → Iterator[tuple[str, Any]]**
: Iterate all paths and leaf values.

**from_file(path: str | Path) → TreeDict** (classmethod)
: Load from JSON, YAML, TOML, or INI file.

### Examples

```python
td = TreeDict({"user": {"name": "Alice"}})
td["user.name"]           # "Alice"
td["missing"]             # None
td["settings.theme"] = "dark"  # auto-creates intermediate dicts

# List access
td = TreeDict({"items": [{"id": 1}, {"id": 2}]})
td["items.#0.id"]         # 1

# Thread-safe
with td:
    td["counter"] = td["counter"] + 1

# Async-safe
async with td:
    td["counter"] = td["counter"] + 1
```

See [README](https://github.com/genropy/genro-toolbox) for more examples.

## safe_is_instance

```{eval-rst}
.. autofunction:: genro_toolbox.safe_is_instance
```

### Function Signature

```python
def safe_is_instance(obj: Any, class_name: str) -> bool
```

### Parameters

**obj** : `Any`
: Object to check

**class_name** : `str`
: Fully qualified class name (e.g., "builtins.int", "package.module.ClassName")

### Returns

**bool**
: True if obj is an instance of the class, False otherwise

### Examples

See [safe_is_instance Guide](../user-guide/safe-is-instance.md) for detailed examples.

## ASCII Table

### render_ascii_table

```{eval-rst}
.. autofunction:: genro_toolbox.ascii_table.render_ascii_table
```

### Function Signature

```python
def render_ascii_table(data: dict, max_width: Optional[int] = None) -> str
```

### Parameters

**data** : `dict`
: Table structure containing:
  - `headers`: List of column definitions (name, type, format, align, hierarchy)
  - `rows`: List of row data (list of values)
  - `title` (optional): Table title
  - `max_width` (optional): Maximum table width in characters

**max_width** : `Optional[int]`
: Override max_width from data dict. Default: use data's max_width or 120

### Returns

**str**
: Formatted ASCII table with borders and alignment

### render_markdown_table

```{eval-rst}
.. autofunction:: genro_toolbox.ascii_table.render_markdown_table
```

### Function Signature

```python
def render_markdown_table(data: dict) -> str
```

### Parameters

**data** : `dict`
: Table structure (same format as render_ascii_table)

### Returns

**str**
: Markdown-formatted table

### Examples

See [ASCII Table Guide](../user-guide/ascii-table.md) for detailed examples.

## tags_match

```{eval-rst}
.. autofunction:: genro_toolbox.tags_match
```

### Function Signature

```python
def tags_match(
    rule: str,
    values: set[str],
    *,
    max_length: int = 200,
    max_depth: int = 6,
) -> bool
```

### Parameters

**rule** : `str`
: Boolean expression string (e.g., `"admin&!internal"`).

**values** : `set[str]`
: Set of tag strings to match against.

**max_length** : `int`
: Maximum allowed length for the rule string. Default: 200.

**max_depth** : `int`
: Maximum nesting depth for parentheses. Default: 6.

### Returns

**bool**
: True if the expression matches the given values.

### Raises

**RuleError**
: If the rule is invalid or exceeds limits.

### Operators

| Symbol | Keyword | Meaning |
|--------|---------|---------|
| `,` or `\|` | `or` | OR (either matches) |
| `&` | `and` | AND (both must match) |
| `!` | `not` | NOT (must not match) |
| `()` | - | Grouping |

### Grammar

```text
expr     := or_expr
or_expr  := and_expr (('|' | ',' | 'or') and_expr)*
and_expr := not_expr (('&' | 'and') not_expr)*
not_expr := ('!' | 'not') not_expr | primary
primary  := '(' expr ')' | TAG
TAG      := [a-zA-Z_][a-zA-Z0-9_]* (excluding keywords)
```

### Examples

See [tags_match Guide](../user-guide/tags-match.md) for detailed examples.

## RuleError

```{eval-rst}
.. autoclass:: genro_toolbox.RuleError
```

Exception raised when a tag expression is invalid.

Inherits from `ValueError`.

## get_uuid

```{eval-rst}
.. autofunction:: genro_toolbox.get_uuid
```

### Function Signature

```python
def get_uuid() -> str
```

### Returns

**str**
: 22-character sortable unique identifier.

### Format

The ID consists of:
- `Z`: Version marker (distinguishes from legacy UUIDs, sorts after them)
- 9 characters: microseconds since 2025-01-01 UTC (base62 encoded)
- 12 characters: cryptographically secure random (base62 encoded)

### Properties

- Lexicographically sortable by creation time (UTC)
- URL-safe (alphanumeric only)
- 22 characters (compatible with legacy Genro ID columns)
- Timestamp valid for ~440 years from 2025
- Collision probability ~10^-19 for same microsecond

### Examples

```python
from genro_toolbox import get_uuid

uid = get_uuid()  # e.g., "Z00005KmLxHj7F9aGbCd3e"
len(uid)          # 22
uid[0]            # 'Z'
uid.isalnum()     # True

# IDs are sortable by time
ids = [get_uuid() for _ in range(3)]
sorted(ids) == ids  # True
```

## smartasync

```{eval-rst}
.. autofunction:: genro_toolbox.smartasync
```

### Function Signature

```python
def smartasync(method: Callable) -> Callable
```

### Parameters

**method** : `Callable`
: Method or function to decorate (async or sync).

### Returns

**Callable**
: Wrapped function that works in both sync and async contexts.

### How It Works

Automatically detects the execution context and adapts:

| Context | Method | Behavior |
|---------|--------|----------|
| Sync | Async | `asyncio.run()` |
| Sync | Sync | Direct call |
| Async | Async | Return coroutine (for await) |
| Async | Sync | `asyncio.to_thread()` |

### Features

- Auto-detection of sync/async context using `asyncio.get_running_loop()`
- Asymmetric caching: caches True (async), always checks False (sync)
- Works with both class methods and standalone functions
- Compatible with `__slots__` classes

### Examples

```python
from genro_toolbox import smartasync

class DataManager:
    @smartasync
    async def fetch_data(self, url: str):
        async with httpx.AsyncClient() as client:
            return await client.get(url).json()

manager = DataManager()

# Sync context - no await needed
data = manager.fetch_data("https://api.example.com")

# Async context - use await
async def main():
    data = await manager.fetch_data("https://api.example.com")
```

### Cache Reset

For testing, you can reset the cache:

```python
manager.fetch_data._smartasync_reset_cache()
```

## Helper Functions

### filtered_dict

```python
def filtered_dict(
    data: Optional[Mapping[str, Any]],
    filter_fn: Optional[Callable[[str, Any], bool]] = None,
) -> Dict[str, Any]
```

Return a dict filtered through `filter_fn`.

**Parameters**:
- `data`: Source mapping (can be None)
- `filter_fn`: Optional filter callable `(key, value) → bool`

**Returns**: Filtered dictionary

## dictExtract (Internal)

Internal utility function used by `extract_kwargs`. Not part of the public API.

```python
def dictExtract(
    mydict: dict,
    prefix: str,
    pop: bool = False,
    slice_prefix: bool = True,
    is_list: bool = False
) -> dict
```

Returns a dict of items with keys starting with prefix.

---

## Type Definitions

```python
F = TypeVar('F', bound=Callable[..., Any])
```

Type variable for decorated function preservation.

---

## See Also

- [User Guide](../user-guide/extract-kwargs.md) - Complete feature documentation
- [Examples](../examples/index.md) - Real-world usage examples
- [Best Practices](../user-guide/best-practices.md) - Production patterns
