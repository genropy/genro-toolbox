# Installation

Genro-Toolbox is a Python package that can be installed via pip.

## Requirements

- Python 3.10 or higher
- No external dependencies (pure Python standard library)

## Install from PyPI

```bash
pip install genro-toolbox
```

## Install from Source

For development or to get the latest changes:

```bash
git clone https://github.com/genropy/genro-toolbox.git
cd genro-toolbox
pip install -e ".[dev]"
```

## Verify Installation

```python
import genro_toolbox
print(genro_toolbox.__version__)
# Output: 0.3.0

from genro_toolbox import extract_kwargs
print(extract_kwargs.__doc__)
```

## Optional Dependencies

### Development

For running tests and linting:

```bash
pip install genro-toolbox[dev]
```

This installs:
- pytest (testing)
- pytest-cov (coverage)
- ruff (linting)

### Documentation

For building documentation:

```bash
pip install genro-toolbox[docs]
```

This installs:
- sphinx
- sphinx-rtd-theme
- sphinx-autodoc-typehints
- myst-parser
- sphinxcontrib-mermaid

## Next Steps

- [Quick Start Guide](quickstart.md) - Get started in 5 minutes
- [extract_kwargs Guide](extract-kwargs.md) - Learn the decorator in detail
- [Best Practices](best-practices.md) - Production usage patterns
