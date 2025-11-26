# Contributing

Guidelines for contributing to Genro-Toolbox.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/genropy/genro-toolbox.git
cd genro-toolbox
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Development Dependencies

```bash
pip install -e ".[dev,docs]"
```

This installs:
- Core package in editable mode
- Testing tools (pytest, pytest-cov)
- Documentation tools (Sphinx, MyST)

### 4. Run Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=genro_toolbox --cov-report=html
```

## Project Structure

```
genro-toolbox/
├── src/genro_toolbox/       # Source code
│   ├── __init__.py          # Public API
│   ├── decorators.py        # extract_kwargs implementation
│   ├── dict_utils.py        # SmartOptions and helpers
│   ├── typeutils.py         # safe_is_instance
│   └── ascii_table.py       # Table rendering
│
├── tests/                   # Test suite
│   ├── test_decorators.py
│   ├── test_dict_utils.py
│   ├── test_typeutils.py
│   └── test_ascii_table.py
│
├── docs/                    # Sphinx documentation
│   ├── conf.py              # Sphinx config
│   ├── index.md             # Landing page
│   ├── user-guide/          # User guides
│   ├── examples/            # Examples
│   ├── api/                 # API reference
│   └── appendix/            # Additional info
│
├── pyproject.toml           # Project metadata
├── LICENSE                  # Apache 2.0 license
└── README.md                # Project overview
```

## Coding Standards

### Python Style

Follow **PEP 8** with these specifics:

- **Line length**: 100 characters max
- **Indentation**: 4 spaces
- **Quotes**: Single quotes for strings (except docstrings)
- **Type hints**: Required for all public functions

### Type Hints

All public functions **must have type hints**:

```python
from typing import Optional, Dict, Any, Callable

def extract_kwargs(
    _adapter: Optional[str] = None,
    _dictkwargs: Optional[Dict[str, Any]] = None,
    **extraction_specs: Any
) -> Callable[[F], F]:
    """Decorator that extracts kwargs."""
    ...
```

### Docstrings

Use **Google style** docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """Short description.

    Longer description with more details.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Example:
        >>> my_function("test", 42)
        True
    """
    ...
```

## Testing Guidelines

### Test Organization

Tests are organized by concern:

```python
class TestExtractKwargsBasic:
    """Basic extract_kwargs functionality."""

    def test_extract_with_prefix(self):
        """Test extracting kwargs with prefix."""
        ...

class TestExtractKwargsAdapter:
    """Adapter functionality."""

    def test_adapter_called(self):
        """Test adapter is called."""
        ...
```

### Test Requirements

Every contribution should:

1. **Add tests** for new features
2. **Update tests** for changed behavior
3. **Maintain 95%+ coverage**
4. **Pass all existing tests**

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_decorators.py

# Run specific test
pytest tests/test_decorators.py::TestExtractKwargsBasic::test_extract_with_prefix

# With coverage
pytest --cov=genro_toolbox --cov-report=term-missing
```

## Documentation

### Building Docs Locally

```bash
cd docs
sphinx-build -b html . _build/html
```

View at `docs/_build/html/index.html`.

### Documentation Standards

1. **MyST Markdown**: Use MyST extensions
2. **Examples**: Include working code examples
3. **API docs**: Keep in sync with code

## Pull Request Process

### 1. Create Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation only
- `refactor/` - Code refactoring

### 2. Make Changes

- Write code
- Add tests
- Update docs
- Run tests locally

### 3. Commit

Use **conventional commits**:

```bash
git commit -m "feat: add support for nested extraction"
git commit -m "fix: handle missing adapter methods"
git commit -m "docs: update quickstart guide"
```

Prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Build/tooling

### 4. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create PR on GitHub with:

1. **Clear title** - What does it do?
2. **Description** - Why is it needed?
3. **Test coverage** - How is it tested?
4. **Breaking changes** - Any breaking changes?

### 5. Review Process

- **CI checks** must pass
- **Code review** by maintainer
- **Coverage** must not decrease
- **Docs** must be updated

## Release Process

(For maintainers only)

### Pre-Release Checklist

**CRITICAL**: Before creating a release, verify ALL version numbers are synchronized:

```bash
# 1. Check __init__.py version
grep "__version__" src/genro_toolbox/__init__.py

# 2. Check pyproject.toml version
grep "^version" pyproject.toml

# 3. Both MUST match!
```

### Step-by-Step Release Process

#### 1. Update Version Numbers

**IMPORTANT**: Update version in BOTH files:

**File 1: `src/genro_toolbox/__init__.py`**
```python
__version__ = "0.2.0"
```

**File 2: `pyproject.toml`**
```toml
[project]
name = "genro-toolbox"
version = "0.2.0"  # ← MUST match __init__.py
```

#### 2. Commit Version Updates

```bash
git add src/genro_toolbox/__init__.py pyproject.toml
git commit -m "build: bump version to 0.2.0"
git push origin main
```

#### 3. Create and Push Tag

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release v0.2.0: Brief description"

# Push tag (triggers CI/CD)
git push origin v0.2.0
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/genropy/genro-toolbox/issues)
- **Discussions**: [GitHub Discussions](https://github.com/genropy/genro-toolbox/discussions)

## Code of Conduct

### Our Standards

- **Be respectful** - Treat everyone with respect
- **Be constructive** - Provide helpful feedback
- **Be inclusive** - Welcome all contributors
- **Be patient** - We all started somewhere

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Unprofessional conduct

## License

By contributing to Genro-Toolbox, you agree that your contributions will be licensed under the **Apache License 2.0**.

## Recognition

Contributors are recognized in:
- GitHub contributors page
- Release notes
- Documentation (for major contributions)

Thank you for contributing!

## See Also

- [Architecture](architecture.md) - Technical design
- [Best Practices](../user-guide/best-practices.md) - Usage patterns
- [API Reference](../api/reference.md) - Complete API
