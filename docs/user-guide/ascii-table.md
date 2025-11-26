# ASCII Table

Generate beautiful ASCII and Markdown tables with advanced formatting, hierarchies, and zero dependencies.

## Overview

The `ascii_table` module provides utilities for creating formatted tables in both ASCII and Markdown formats. It supports:

- **Type-aware formatting** (str, int, float, bool, date, datetime)
- **Hierarchical data** with automatic indentation
- **Text wrapping** for long content
- **Column alignment** (left, right, center)
- **Custom date/time formats**
- **ANSI color support** (colors don't affect width calculations)
- **Markdown export** for documentation
- **Zero dependencies** - pure Python standard library

## Quick Start

### Basic Table

```python
from genro_toolbox.ascii_table import render_ascii_table

data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Age", "type": "int"},
        {"name": "Active", "type": "bool"}
    ],
    "rows": [
        ["Alice", "25", "yes"],
        ["Bob", "30", "no"],
        ["Charlie", "28", "true"]
    ]
}

print(render_ascii_table(data))
```

Output:
```
+---------+-----+--------+
| Name    | Age | Active |
+---------+-----+--------+
| Alice   | 25  | true   |
+---------+-----+--------+
| Bob     | 30  | false  |
+---------+-----+--------+
| Charlie | 28  | true   |
+---------+-----+--------+
```

### With Title

```python
data = {
    "title": "User List",
    "headers": [
        {"name": "Name", "type": "str"}
    ],
    "rows": [["Alice"], ["Bob"]]
}

print(render_ascii_table(data))
```

## Data Structure Format

### Headers

Each header is a dictionary with:

- **name** (required): Column name displayed in the table
- **type**: Data type - `str`, `int`, `float`, `bool`, `date`, `datetime` (default: `str`)
- **format**: Format string for the type (dates/floats)
- **align**: Text alignment - `left`, `right`, `center` (default: `left`)
- **hierarchy**: For hierarchical columns, dict with `sep` key (path separator)

Example:
```python
{
    "name": "Revenue",
    "type": "float",
    "format": ".2f",
    "align": "right"
}
```

### Rows

List of lists, where each inner list contains values for one row. Values are formatted according to their column's type.

### Table Options

- **title**: Optional title displayed above the table (centered)
- **max_width**: Maximum table width in characters (default: 120)

## Type Formatting

### String

```python
{"name": "Text", "type": "str"}
```

Converts any value to string.

### Integer

```python
{"name": "Count", "type": "int"}
```

Converts to integer, falls back to string if conversion fails.

### Float

```python
# Default formatting
{"name": "Value", "type": "float"}

# Custom format (2 decimal places)
{"name": "Price", "type": "float", "format": ".2f"}

# Scientific notation
{"name": "Large", "type": "float", "format": ".2e"}
```

Supports Python format specifications.

### Boolean

```python
{"name": "Active", "type": "bool"}
```

Converts various representations to `true`/`false`:
- `true`: "true", "yes", "1", True
- `false`: "false", "no", "0", False

### Date

```python
# ISO format output
{"name": "Date", "type": "date"}

# Custom format
{"name": "Date", "type": "date", "format": "dd/mm/yyyy"}
```

Date format tokens:
- `yyyy`: 4-digit year
- `yy`: 2-digit year
- `mm`: 2-digit month
- `dd`: 2-digit day

Input must be ISO format string (e.g., "2025-11-24").

### DateTime

```python
# Default format
{"name": "Created", "type": "datetime"}

# Custom format
{"name": "Created", "type": "datetime", "format": "yyyy-mm-dd HH:MM"}
```

DateTime format tokens:
- Date tokens (as above)
- `HH`: 2-digit hour (24h)
- `MM`: 2-digit minute
- `SS`: 2-digit second

Input must be ISO format string (e.g., "2025-11-24T10:30:00").

## Column Alignment

```python
data = {
    "headers": [
        {"name": "Name", "align": "left"},
        {"name": "Amount", "align": "right"},
        {"name": "Status", "align": "center"}
    ],
    "rows": [
        ["Product A", "1234.56", "OK"],
        ["Product B", "789.00", "WARN"]
    ]
}
```

Output:
```
+-----------+---------+--------+
| Name      |  Amount | Status |
+-----------+---------+--------+
| Product A | 1234.56 |   OK   |
+-----------+---------+--------+
| Product B |  789.00 |  WARN  |
+-----------+---------+--------+
```

## Hierarchical Data

Display tree structures with automatic indentation:

```python
data = {
    "headers": [
        {
            "name": "Path",
            "type": "str",
            "hierarchy": {"sep": "/"}  # Path separator
        },
        {"name": "Size", "type": "int"}
    ],
    "rows": [
        ["root/docs/file1.txt", "1024"],
        ["root/docs/file2.txt", "2048"],
        ["root/src/main.py", "4096"],
        ["root/src/utils/helper.py", "512"]
    ]
}

print(render_ascii_table(data))
```

Output:
```
+---------------------+------+
| Path                | Size |
+---------------------+------+
| root                |      |
+---------------------+------+
|   docs              |      |
+---------------------+------+
|     file1.txt       | 1024 |
+---------------------+------+
|     file2.txt       | 2048 |
+---------------------+------+
|   src               |      |
+---------------------+------+
|     main.py         | 4096 |
+---------------------+------+
|     utils           |      |
+---------------------+------+
|       helper.py     | 512  |
+---------------------+------+
```

Hierarchy features:
- Automatic indentation based on path depth
- Configurable separator character
- Parent nodes show structure, leaf nodes show data
- Only one hierarchy column supported per table

## Text Wrapping

Long text automatically wraps to fit within `max_width`:

```python
data = {
    "max_width": 50,
    "headers": [
        {"name": "Description", "type": "str"}
    ],
    "rows": [
        ["This is a very long description that will be wrapped to fit within the maximum width"]
    ]
}
```

## ANSI Color Support

ANSI escape codes are handled correctly - they don't affect width calculations:

```python
data = {
    "headers": [{"name": "Status"}],
    "rows": [
        ["\x1b[32mOK\x1b[0m"],      # Green
        ["\x1b[31mERROR\x1b[0m"]    # Red
    ]
}
```

Colors display in terminal but are stripped for width calculations.

## Markdown Export

Convert tables to Markdown format for documentation:

```python
from genro_toolbox.ascii_table import render_markdown_table

data = {
    "headers": [
        {"name": "Name", "type": "str"},
        {"name": "Value", "type": "int"}
    ],
    "rows": [
        ["Item A", "100"],
        ["Item B", "200"]
    ]
}

print(render_markdown_table(data))
```

Output:
```markdown
| Name | Value |
| --- | --- |
| Item A | 100 |
| Item B | 200 |
```

Markdown tables:
- Support all type formatting
- Use simple pipe-and-dash format
- Compatible with GitHub, GitLab, etc.
- Don't support hierarchies (flat structure)

## Complete Example

```python
from genro_toolbox.ascii_table import render_ascii_table

data = {
    "title": "Sales Report Q4 2025",
    "max_width": 80,
    "headers": [
        {"name": "Region", "type": "str", "align": "left"},
        {"name": "Revenue", "type": "float", "format": ".2f", "align": "right"},
        {"name": "Growth", "type": "float", "format": ".1f", "align": "right"},
        {"name": "Active", "type": "bool", "align": "center"},
        {"name": "Updated", "type": "date", "format": "dd/mm/yyyy"}
    ],
    "rows": [
        ["North America", 125430.50, 12.5, "yes", "2025-11-24"],
        ["Europe", 98765.25, 8.3, "yes", "2025-11-23"],
        ["Asia Pacific", 145678.00, 15.2, "true", "2025-11-22"],
        ["Latin America", 67890.75, -2.1, "no", "2025-11-21"]
    ]
}

print(render_ascii_table(data))
```

Output:
```
                          Sales Report Q4 2025
+---------------+-----------+--------+--------+------------+
| Region        |   Revenue | Growth | Active | Updated    |
+---------------+-----------+--------+--------+------------+
| North America | 125430.50 |   12.5 |  true  | 24/11/2025 |
+---------------+-----------+--------+--------+------------+
| Europe        |  98765.25 |    8.3 |  true  | 23/11/2025 |
+---------------+-----------+--------+--------+------------+
| Asia Pacific  | 145678.00 |   15.2 |  true  | 22/11/2025 |
+---------------+-----------+--------+--------+------------+
| Latin America |  67890.75 |   -2.1 |  false | 21/11/2025 |
+---------------+-----------+--------+--------+------------+
```

## API Reference

### Main Functions

#### `render_ascii_table(data, max_width=None)`

Generate ASCII table from data structure.

**Parameters:**
- `data`: Dictionary with `headers` and `rows` keys, optional `title` and `max_width`
- `max_width`: Override max width from data dict (default: use data's max_width or 120)

**Returns:** String containing formatted ASCII table

#### `render_markdown_table(data)`

Generate Markdown table from data structure.

**Parameters:**
- `data`: Dictionary with `headers` and `rows` keys

**Returns:** String containing Markdown table

### Utility Functions

#### `format_cell(value, coldef)`

Format a single cell value according to column definition.

#### `strip_ansi(text)`

Remove ANSI escape sequences from text.

#### `normalize_date_format(fmt)`

Convert custom date format to Python strftime format.

#### `parse_bool(value)`

Parse boolean value from various representations.

## See Also

- [SmartOptions](smart-options.md) - Option merging and filtering
- [extract_kwargs](extract-kwargs.md) - Kwargs extraction decorator
- [safe_is_instance](safe-is-instance.md) - Safe type checking
