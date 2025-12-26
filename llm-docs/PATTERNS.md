# genro-toolbox Usage Patterns

## SmartOptions Patterns

### Basic merge with defaults

```python
# From test: test_dict_utils.py::TestSmartOptions::test_basic_merge
opts = SmartOptions({"timeout": 5}, {"timeout": 1, "retries": 3})
opts["timeout"]  # 5 (incoming wins)
opts["retries"]  # 3 (from defaults)
```

### Ignore None and empty values

```python
# From test: test_dict_utils.py::TestSmartOptions::test_ignore_flags
opts = SmartOptions(
    {"timeout": None, "tags": []},
    {"timeout": 10, "tags": ["default"]},
    ignore_none=True,
    ignore_empty=True,
)
opts["timeout"]      # 10 (None ignored)
opts["tags.default"] # True (string list becomes feature flags)
```

### Mutable options

```python
# From test: test_dict_utils.py::TestSmartOptions::test_attribute_updates_are_tracked
opts = SmartOptions({"timeout": 2}, {})
opts["timeout"] = 7
opts["new_flag"] = True
del opts["timeout"]
opts.as_dict()  # {"new_flag": True}
```

### Custom filter function

```python
# SmartOptions with custom filter
opts = SmartOptions(
    {"timeout": None, "retries": 5},
    {"timeout": 2, "retries": 1},
    filter_fn=lambda _, value: value is not None,
)
opts["timeout"]  # 2 (None filtered)
opts["retries"]  # 5
```

### Nested path access

```python
# SmartOptions supports dot-path notation
opts = SmartOptions({
    "server": {"host": "localhost", "port": 8080}
})
opts["server.host"]  # "localhost"
opts["server.port"]  # 8080
```

---

## extract_kwargs Patterns

### Basic prefix extraction

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_with_prefix
@extract_kwargs(logging=True)
def func(self, name, logging_kwargs=None, **kwargs):
    return logging_kwargs

func(obj, "test", logging_level="INFO", logging_format="json", timeout=30)
# logging_kwargs = {"level": "INFO", "format": "json"}
# kwargs = {"timeout": 30}
```

### Multiple prefix groups

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_multiple_prefixes
@extract_kwargs(logging=True, cache=True)
def func(self, logging_kwargs=None, cache_kwargs=None, **kwargs):
    pass

func(obj, logging_level="INFO", cache_ttl=300, cache_backend="redis")
# logging_kwargs = {"level": "INFO"}
# cache_kwargs = {"ttl": 300, "backend": "redis"}
```

### Keep extracted in kwargs (pop=False)

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_extract_with_pop_false
@extract_kwargs(logging={'pop': False})
def func(self, logging_kwargs=None, **kwargs):
    return logging_kwargs, kwargs

# logging_kwargs = {"level": "INFO"}
# kwargs = {"logging_level": "INFO", "timeout": 30}  # still contains prefixed
```

### Merge with explicit kwargs

```python
# From test: test_decorators.py::TestExtractKwargsBasic::test_merge_with_existing_kwargs
@extract_kwargs(logging=True)
def func(self, logging_kwargs=None, **kwargs):
    return logging_kwargs

func(obj, logging_kwargs={"existing": "value"}, logging_level="INFO")
# logging_kwargs = {"existing": "value", "level": "INFO"}
```

### Adapter preprocessing

```python
# From test: test_decorators.py::TestExtractKwargsAdapter::test_adapter_called
class MyClass:
    def preprocess(self, kwargs):
        kwargs['injected'] = True

    @extract_kwargs(_adapter='preprocess', logging=True)
    def method(self, logging_kwargs=None, **kwargs):
        return kwargs

obj.method(logging_level="INFO")
# kwargs contains {'injected': True}
```

---

## safe_is_instance Patterns

### Check built-in types

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_builtin_types
safe_is_instance(42, "builtins.int")      # True
safe_is_instance("hello", "builtins.str") # True
safe_is_instance([1, 2], "builtins.list") # True
safe_is_instance({"a": 1}, "builtins.dict") # True
```

### Check with inheritance

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_subclass_recognition
class Base: pass
class Derived(Base): pass

obj = Derived()
safe_is_instance(obj, "module.Derived")  # True
safe_is_instance(obj, "module.Base")     # True (subclass)
safe_is_instance(obj, "builtins.object") # True (all objects)
```

### Check custom class without importing

```python
# From test: test_typeutils.py::TestSafeIsInstance::test_basic_instance_check
safe_is_instance(obj, "mypackage.models.BaseNode")
# No import of mypackage required
# Checks full MRO
```

---

## Table Patterns

### Basic ASCII table

```python
# From test: test_ascii_table.py::TestTableFromStruct::test_render_ascii_table_basic
data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Age", "type": "int"}
    ],
    "rows": [["Alice", "25"], ["Bob", "30"]]
}
print(render_ascii_table(data))
# +-------+-----+
# |Name   |Age  |
# +-------+-----+
# |Alice  |25   |
# +-------+-----+
# |Bob    |30   |
# +-------+-----+
```

### Table with type formatting

```python
# From test: test_ascii_table.py::TestTableFromStruct::test_render_ascii_table_with_types
data = {
    "headers": [
        {"name": "Active", "type": "bool"},
        {"name": "Score", "type": "float", "format": ".1f"}
    ],
    "rows": [["yes", 95.67], ["no", 87.32]]
}
# "yes" → "true", "no" → "false"
# 95.67 → "95.7", 87.32 → "87.3"
```

### Table with date formatting

```python
# From test: test_ascii_table.py::TestTableFromStruct::test_render_ascii_table_with_dates
data = {
    "headers": [
        {"name": "Date", "type": "date", "format": "dd/mm/yyyy"},
        {"name": "DateTime", "type": "datetime"}
    ],
    "rows": [["2025-11-24", "2025-11-24T10:30:00"]]
}
# "2025-11-24" → "24/11/2025"
# "2025-11-24T10:30:00" → "2025-11-24 10:30:00"
```

### Hierarchical table

```python
# From test: test_ascii_table.py::TestIntegration::test_hierarchy_table
data = {
    "headers": [
        {"name": "Path", "type": "str", "hierarchy": {"sep": "/"}},
        {"name": "Size", "type": "int"}
    ],
    "rows": [
        ["root/docs/file1.txt", "1024"],
        ["root/docs/file2.txt", "2048"],
        ["root/src/main.py", "4096"]
    ]
}
# Renders with tree-like indentation
```

### Markdown table

```python
# From test: test_ascii_table.py::TestRenderMarkdownTable::test_render_markdown_simple
data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Value", "type": "int"}
    ],
    "rows": [["Alice", "25"]]
}
print(render_markdown_table(data))
# | Name | Value |
# | --- | --- |
# | Alice | 25 |
```
