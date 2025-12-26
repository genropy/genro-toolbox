# genro-toolbox API Reference

## SmartOptions

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
    ): ...

    def as_dict(self) -> dict[str, Any]: ...
    def __add__(self, other: SmartOptions | Mapping) -> SmartOptions: ...
```

**Parameters**:
- `incoming`: One of:
  - Mapping with runtime kwargs
  - str path to config file (YAML, JSON, TOML, INI)
  - str 'ENV:PREFIX' for environment variables
  - Path object to config file
  - Callable to extract defaults from signature
- `defaults`: Mapping with default values, or argv list when incoming is callable (legacy)
- `env`: Environment variable prefix (e.g., "MYAPP" for MYAPP_HOST)
- `argv`: Command line arguments list
- `ignore_none`: Skip `None` values from incoming
- `ignore_empty`: Skip empty strings/collections from incoming
- `filter_fn`: Custom filter `(key, value) -> bool`

**Behavior**:
- `incoming` values override `defaults`
- Path notation access: `opts["key"]`, `opts["server.host"]`
- Mutable: `opts["key"] = value`, `del opts["key"]`
- `as_dict()` returns copy
- Merge with `+` operator: right side wins
- Nested dicts become SmartOptions
- String lists become feature flags
- List of dicts indexed by first key value

---

## TreeDict

```python
class TreeDict:
    def __init__(self, data: dict[str, Any] | str | None = None) -> None: ...

    def __getitem__(self, path: str) -> Any: ...
    def __setitem__(self, path: str, value: Any) -> None: ...
    def __delitem__(self, path: str) -> None: ...
    def __contains__(self, key: str) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[str]: ...

    def get(self, key: str, default: Any = None) -> Any: ...
    def keys(self) -> Any: ...
    def values(self) -> Any: ...
    def items(self) -> Any: ...
    def as_dict(self) -> dict[str, Any]: ...
    def walk(self, expand_lists: bool = False) -> Iterator[tuple[str, Any]]: ...

    @classmethod
    def from_file(cls, path: str | Path) -> TreeDict: ...
```

**Features**:
- Path notation access: `td["a.b.c"]`
- Auto-creates intermediate dicts on write
- Returns None for missing keys
- List access via #N syntax: `td["items.#0.id"]`
- Thread-safe access via context manager: `with td: ...`
- Async-safe access: `async with td: ...`
- Supports JSON, YAML, TOML, INI file loading

---

## extract_kwargs

```python
def extract_kwargs(
    _adapter: str | None = None,
    _dictkwargs: dict[str, Any] | None = None,
    **extraction_specs: Any
) -> Callable[[F], F]: ...
```

**Parameters**:
- `_adapter`: Method name on `self` to preprocess kwargs
- `_dictkwargs`: Dict alternative to `**extraction_specs`
- `**extraction_specs`: Prefix specifications
  - `prefix=True`: Extract and pop (default)
  - `prefix={'pop': False}`: Extract but keep in kwargs
  - `prefix={'slice_prefix': False}`: Keep prefix in keys

**Behavior**:
- Creates `{prefix}_kwargs` dict parameter
- Reserved word `class` → `_class`
- Works with methods (self) and functions
- Always returns `{}`, never `None`

**Example specs**:
```python
@extract_kwargs(logging=True, cache={'pop': False})
def func(self, logging_kwargs=None, cache_kwargs=None, **kwargs): ...
```

---

## safe_is_instance

```python
def safe_is_instance(obj: Any, class_full_name: str) -> bool: ...
```

**Parameters**:
- `obj`: Object to check
- `class_full_name`: Full path `"module.ClassName"`

**Behavior**:
- Checks MRO (includes subclasses)
- No import required
- Cached for performance
- Returns `False` for non-existent classes

**Examples**:
```python
safe_is_instance(42, "builtins.int")        # True
safe_is_instance([], "builtins.list")       # True
safe_is_instance(myobj, "pkg.BaseClass")    # True if subclass
```

---

## render_ascii_table

```python
def render_ascii_table(
    data: dict,
    max_width: int | None = None
) -> str: ...
```

**Data structure**:
```python
{
    "title": str | None,           # Optional title
    "max_width": int,              # Default 120
    "headers": [
        {
            "name": str,           # Column name
            "type": str,           # "str"|"int"|"float"|"bool"|"date"|"datetime"
            "format": str | None,  # Format spec (e.g., ".2f", "dd/mm/yyyy")
            "align": str,          # "left"|"right"|"center"
            "hierarchy": {"sep": str} | None,  # Hierarchical display
        },
        ...
    ],
    "rows": [[value, ...], ...],
}
```

**Type formatting**:
- `bool`: "yes"/"true"/"1" → "true", "no"/"false"/"0" → "false"
- `date`: ISO → custom format (e.g., "dd/mm/yyyy")
- `datetime`: ISO → "YYYY-MM-DD HH:MM:SS" or custom
- `float`: Custom format spec (e.g., ".2f")

---

## render_markdown_table

```python
def render_markdown_table(data: dict) -> str: ...
```

Same data structure as `render_ascii_table`.

**Output**:
```markdown
| Name | Value |
| --- | --- |
| Alice | 25 |
```

---

## tags_match

```python
def tags_match(rule: str, values: set[str]) -> bool: ...
```

Match boolean expressions against a set of tags.

**Operators**:
- OR: `,`, `|`, `or`
- AND: `&`, `and`
- NOT: `!`, `not`
- Parentheses for grouping

**Examples**:
```python
tags_match("admin", {"admin", "user"})       # True
tags_match("admin,public", {"public"})       # True (OR)
tags_match("admin&internal", {"admin"})      # False (AND)
tags_match("!admin", {"public"})             # True (NOT)
tags_match("(admin|public)&!internal", {"admin"})  # True
```

---

## Helper Functions

### filtered_dict

```python
def filtered_dict(
    data: Mapping[str, Any] | None,
    filter_fn: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any]: ...
```

### dictExtract

```python
def dictExtract(
    mydict: dict,
    prefix: str,
    pop: bool = False,
    slice_prefix: bool = True,
    is_list: bool = False,  # unused
) -> dict: ...
```
