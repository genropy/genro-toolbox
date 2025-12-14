# tags_match Guide

Boolean expression matcher for tag-based filtering.

## Overview

`tags_match` evaluates boolean expressions against a set of tags using a recursive descent parser. No `eval()` is used - safe direct evaluation during parsing.

**Key Features**:

- Boolean operators: AND, OR, NOT
- Parentheses for grouping
- Both symbol and keyword syntax
- Safety limits (length, nesting depth)
- Case-insensitive keywords

## Basic Usage

```python
from genro_toolbox import tags_match

# Simple tag check
tags_match("admin", {"admin", "user"})  # True
tags_match("admin", {"user"})  # False

# Empty rule always matches
tags_match("", {"admin"})  # True
```

## Operators

### OR Operator

Use `,` (comma), `|` (pipe), or `or` keyword:

```python
# All equivalent
tags_match("admin,public", {"public"})  # True
tags_match("admin|public", {"public"})  # True
tags_match("admin or public", {"public"})  # True

# Multiple OR
tags_match("a,b,c", {"c"})  # True
tags_match("a|b|c", {"d"})  # False
```

### AND Operator

Use `&` (ampersand) or `and` keyword:

```python
# All equivalent
tags_match("admin&internal", {"admin", "internal"})  # True
tags_match("admin and internal", {"admin", "internal"})  # True

# Missing one tag
tags_match("admin&internal", {"admin"})  # False
```

### NOT Operator

Use `!` (exclamation) or `not` keyword:

```python
# All equivalent
tags_match("!admin", {"public"})  # True
tags_match("not admin", {"public"})  # True

# Tag present
tags_match("!admin", {"admin"})  # False

# Double NOT
tags_match("!!admin", {"admin"})  # True
```

## Operator Precedence

Precedence (highest to lowest):
1. `NOT` (prefix)
2. `AND`
3. `OR`

```python
# a&b|c&d is parsed as (a AND b) OR (c AND d)
tags_match("a&b|c&d", {"a", "b"})  # True
tags_match("a&b|c&d", {"c", "d"})  # True
tags_match("a&b|c&d", {"a", "c"})  # False
```

## Grouping with Parentheses

Use parentheses to override precedence:

```python
# (admin OR public) AND internal
tags_match("(admin|public)&internal", {"admin", "internal"})  # True
tags_match("(admin|public)&internal", {"admin"})  # False

# NOT (admin AND internal)
tags_match("!(admin&internal)", {"admin"})  # True
tags_match("!(admin&internal)", {"admin", "internal"})  # False

# Nested grouping
tags_match("((admin|public)&internal)|superuser", {"superuser"})  # True
```

## Keyword Operators

Keywords are case-insensitive:

```python
tags_match("admin AND internal", {"admin", "internal"})  # True
tags_match("admin and internal", {"admin", "internal"})  # True
tags_match("admin And internal", {"admin", "internal"})  # True

tags_match("admin OR public", {"admin"})  # True
tags_match("NOT admin", {"public"})  # True
```

Mix symbols and keywords:

```python
tags_match("admin & public or internal", {"internal"})  # True
tags_match("!admin and not internal", {"public"})  # True
```

## Complex Expressions

```python
# Access control: (admin OR manager) AND NOT suspended
expr = "(admin|manager)&!suspended"
tags_match(expr, {"admin"})  # True
tags_match(expr, {"manager"})  # True
tags_match(expr, {"admin", "suspended"})  # False

# Feature flags: premium OR (beta AND early_adopter)
expr = "premium|(beta&early_adopter)"
tags_match(expr, {"premium"})  # True
tags_match(expr, {"beta", "early_adopter"})  # True
tags_match(expr, {"beta"})  # False
```

## Safety Limits

`tags_match` includes safety limits to prevent abuse:

```python
from genro_toolbox import tags_match, TagExpressionError

# Max length (default 200)
try:
    tags_match("a" * 201, {"a"})
except TagExpressionError as e:
    print(e)  # "Tag rule too long: 201 chars (max 200)"

# Max nesting depth (default 6)
try:
    tags_match("((((((((a))))))))", {"a"})
except TagExpressionError as e:
    print(e)  # "Tag rule too deeply nested (max 6)"

# Custom limits
tags_match("admin", {"admin"}, max_length=50, max_depth=3)
```

## Error Handling

```python
from genro_toolbox import tags_match, TagExpressionError

# Invalid character
try:
    tags_match("admin; drop table", {"admin"})
except TagExpressionError:
    pass  # "Invalid character in tag rule"

# Unmatched parenthesis
try:
    tags_match("(admin", {"admin"})
except TagExpressionError:
    pass  # "Expected RPAREN"

# Empty parentheses
try:
    tags_match("()", {"admin"})
except TagExpressionError:
    pass  # "Unexpected end of expression"
```

## Valid Tag Names

Tags must match pattern `[a-zA-Z_][a-zA-Z0-9_]*`:

```python
tags_match("admin", {"admin"})  # OK
tags_match("_private", {"_private"})  # OK (underscore prefix)
tags_match("admin_user", {"admin_user"})  # OK (underscore in name)
tags_match("level2", {"level2"})  # OK (numbers)
tags_match("AdminUser", {"AdminUser"})  # OK (mixed case)
```

Keywords (`and`, `or`, `not`) cannot be used as tag names:

```python
try:
    tags_match("and", {"and"})  # Error - "and" is operator
except TagExpressionError:
    pass

# But tags STARTING with keyword letters work fine
tags_match("android", {"android"})  # True
tags_match("notice", {"notice"})  # True
tags_match("order", {"order"})  # True
```

## Whitespace Handling

Whitespace around operators and parentheses is ignored:

```python
tags_match(" admin & internal ", {"admin", "internal"})  # True
tags_match("( admin | public )", {"admin"})  # True
tags_match("! admin", {"public"})  # True
```

## Real-World Examples

### Access Control

```python
def check_access(user_tags: set[str], required: str) -> bool:
    return tags_match(required, user_tags)

user = {"authenticated", "admin", "internal"}

check_access(user, "authenticated")  # True
check_access(user, "admin|superuser")  # True
check_access(user, "admin&internal")  # True
check_access(user, "admin&!suspended")  # True
check_access(user, "superuser")  # False
```

### Feature Flags

```python
def is_feature_enabled(flags: set[str], expression: str) -> bool:
    return tags_match(expression, flags)

user_flags = {"beta", "premium"}

is_feature_enabled(user_flags, "premium")  # True
is_feature_enabled(user_flags, "beta&premium")  # True
is_feature_enabled(user_flags, "enterprise")  # False
```

### Content Filtering

```python
def matches_filter(content_tags: set[str], filter_expr: str) -> bool:
    return tags_match(filter_expr, content_tags)

article_tags = {"python", "tutorial", "beginner"}

matches_filter(article_tags, "python")  # True
matches_filter(article_tags, "python&tutorial")  # True
matches_filter(article_tags, "(python|javascript)&!advanced")  # True
```

## API Reference

```python
def tags_match(
    rule: str,
    values: set[str],
    *,
    max_length: int = 200,
    max_depth: int = 6,
) -> bool:
    """Evaluate a boolean tag expression against a set of values.

    Args:
        rule: Boolean expression string (e.g., "admin&!internal").
        values: Set of tag strings to match against.
        max_length: Maximum allowed length for the rule string.
        max_depth: Maximum nesting depth for parentheses.

    Returns:
        True if the expression matches the given values.

    Raises:
        TagExpressionError: If the rule is invalid or exceeds limits.
    """
```

### Grammar

```
expr     := or_expr
or_expr  := and_expr (('|' | ',' | 'or') and_expr)*
and_expr := not_expr (('&' | 'and') not_expr)*
not_expr := ('!' | 'not') not_expr | primary
primary  := '(' expr ')' | TAG
TAG      := [a-zA-Z_][a-zA-Z0-9_]* (excluding keywords)
```

## See Also

- [SmartOptions Guide](smart-options.md) - Configuration management
- [Best Practices](best-practices.md) - Production patterns
- [API Reference](../api/reference.md) - Complete API documentation
