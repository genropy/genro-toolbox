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
class SmartOptions(SimpleNamespace):
    def __init__(
        self,
        incoming: Optional[Mapping[str, Any]] = None,
        defaults: Optional[Mapping[str, Any]] = None,
        *,
        ignore_none: bool = False,
        ignore_empty: bool = False,
        filter_fn: Optional[Callable[[str, Any], bool]] = None,
    )
```

### Parameters

**incoming** : `Optional[Mapping[str, Any]]`
: Mapping with runtime kwargs. Values override defaults after filtering. Can be None.

**defaults** : `Optional[Mapping[str, Any]]`
: Mapping with baseline options. Can be None.

**ignore_none** : `bool`
: When True, skip incoming entries where the value is `None`. Default: False.

**ignore_empty** : `bool`
: When True, skip empty strings/collections from incoming entries. Default: False.
  Empty values include: `""`, `[]`, `()`, `{}`, `set()`, etc.

**filter_fn** : `Optional[Callable[[str, Any], bool]]`
: Optional custom filter function receiving `(key, value)` and returning True if the pair should be kept.
  Applied before `ignore_none` and `ignore_empty`.

### Methods

**as_dict() → Dict[str, Any]**
: Return a copy of current options as a dictionary.

### Examples

See [SmartOptions Guide](../user-guide/smart-options.md) for detailed examples.

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

### make_opts

```python
def make_opts(
    incoming: Optional[Mapping[str, Any]],
    defaults: Optional[Mapping[str, Any]] = None,
    *,
    filter_fn: Optional[Callable[[str, Any], bool]] = None,
    ignore_none: bool = False,
    ignore_empty: bool = False,
) -> SimpleNamespace
```

Merge incoming kwargs with defaults and return a SimpleNamespace.

Similar to `SmartOptions` but returns a plain `SimpleNamespace` without the `as_dict()` method.

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
