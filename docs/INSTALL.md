# Installation Guide

## Installation

```bash
pip install configplusplus
```

## Quick Start

```python
from configplusplus import EnvConfigLoader, env

class Config(EnvConfigLoader):
    DATABASE_URL = env("DATABASE_URL")
    PORT = env("PORT", cast=int, default=8000)
    SECRET_API_KEY = env("SECRET_API_KEY")

print(Config)
```

## Development

```bash
git clone https://github.com/Florian-BARRE/ConfigPlusPlus.git
cd ConfigPlusPlus
poetry install
poetry run pytest
```

## Documentation

- **Quick Reference**: [REFERENCE.md](REFERENCE.md)
- **Complete Guide**: [USAGE.md](USAGE.md)
- **Examples**: `examples/` directory

## Links

- PyPI: https://pypi.org/project/configplusplus/
- GitHub: https://github.com/Florian-BARRE/ConfigPlusPlus

**Author**: Florian BARRE
