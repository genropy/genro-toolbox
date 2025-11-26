# genro-toolbox API Reference

## SmartOptions

```python
class SmartOptions(SimpleNamespace):
    def __init__(
        self,
        incoming: Mapping[str, Any] | None = None,
        defaults: Mapping[str, Any] | None = None,
        *,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Callable[[str, Any], bool] | None = None,
    ): ...

    def as_dict(self) -> dict[str, Any]: ...
```

**Parameters**:
- `incoming`: Runtime kwargs (override defaults)
- `defaults`: Default values
- `ignore_none`: Skip `None` values from incoming
- `ignore_empty`: Skip empty strings/collections from incoming
- `filter_fn`: Custom filter `(key, value) -> bool`

**Behavior**:
- `incoming` values override `defaults`
- Attribute access: `opts.key`
- Mutable: `opts.key = value`, `del opts.key`
- `as_dict()` returns copy

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

## Helper Functions

### filtered_dict

```python
def filtered_dict(
    data: Mapping[str, Any] | None,
    filter_fn: Callable[[str, Any], bool] | None = None,
) -> dict[str, Any]: ...
```

### make_opts

```python
def make_opts(
    incoming: Mapping[str, Any] | None,
    defaults: Mapping[str, Any] | None = None,
    *,
    filter_fn: Callable[[str, Any], bool] | None = None,
    ignore_none: bool = False,
    ignore_empty: bool = False,
) -> SimpleNamespace: ...
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
