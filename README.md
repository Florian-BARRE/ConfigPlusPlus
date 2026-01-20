# ConfigPlusPlus

> Beautiful configuration management for Python with environment variables and YAML support

[![PyPI version](https://badge.fury.io/py/configplusplus.svg)](https://pypi.org/project/configplusplus/)
[![Python](https://img.shields.io/pypi/pyversions/configplusplus.svg)](https://pypi.org/project/configplusplus/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

✨ **Beautiful Display** - Pretty formatted configuration output with automatic grouping and secret masking

🔐 **Secret Masking** - Automatically hides sensitive values (API keys, passwords, tokens)

🌍 **Environment Variables** - Load configuration from environment variables with type casting

📄 **YAML Support** - Load configuration from YAML files with custom parsing

🎯 **Type Casting** - Automatic type conversion (str, int, float, bool, Path)

🏷️ **Static & Instance** - Support for both static class-based and instance-based configs

## Installation

```bash
pip install configplusplus
```

Or with Poetry:

```bash
poetry add configplusplus
```

## Quick Start

### Environment-Based Configuration

```python
from configplusplus import EnvConfigLoader, env
import pathlib

class AppConfig(EnvConfigLoader):
    # Required variables
    DATABASE_HOST = env("DATABASE_HOST")
    DATABASE_PORT = env("DATABASE_PORT", cast=int)
    
    # Optional with defaults
    DEBUG_MODE = env("DEBUG_MODE", cast=bool, default=False)
    
    # Paths
    DATA_DIR = env("DATA_DIR", cast=pathlib.Path)
    
    # Secrets (automatically masked in output)
    SECRET_API_KEY = env("SECRET_API_KEY")

# Use as static class
print(AppConfig.DATABASE_HOST)
print(AppConfig)  # Beautiful formatted output
```

**Output:**
```
╔════════════════════════════════════════════╗
║              APPCONFIG                     ║
╚════════════════════════════════════════════╝

▶ DATABASE
    DATABASE_HOST = 'localhost'
    DATABASE_PORT = 5432

▶ DEBUG
    DEBUG_MODE = False

▶ DATA
    DATA_DIR = '/var/data/myapp'

▶ SECRET
    SECRET_API_KEY = 'sec...et (hidden)'
```

### YAML-Based Configuration

```python
from configplusplus import YamlConfigLoader

class UiConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Parse the loaded YAML data
        self.app_name = self._raw_config["application"]["name"]
        self.theme = self._raw_config["display"]["theme"]
        
        # Parse nested structures
        self.filters = [
            FilterConfig(**f) 
            for f in self._raw_config["filters"]
        ]

# Instantiate with path
config = UiConfig("config.yaml")
print(config.app_name)
print(config)  # Beautiful formatted output
```

## Environment Variables

### Basic Usage

```python
from configplusplus import env

# String (default)
DATABASE_HOST = env("DATABASE_HOST")

# Integer
DATABASE_PORT = env("DATABASE_PORT", cast=int)

# Boolean
DEBUG_MODE = env("DEBUG_MODE", cast=bool)

# Float
TEMPERATURE = env("TEMPERATURE", cast=float)

# Path
DATA_DIR = env("DATA_DIR", cast=pathlib.Path)

# With default value
TIMEOUT = env("TIMEOUT", cast=int, default=30)

# Optional (won't raise if missing)
OPTIONAL = env("OPTIONAL", required=False, default=None)
```

### Boolean Casting

When `cast=bool`, these strings are considered `False`:
- `"false"`, `"False"`, `"FALSE"`
- `"0"`
- `"no"`, `"No"`, `"NO"`
- `""` (empty string)

All other values are considered `True`.

### Loading .env Files

```python
from configplusplus import safe_load_envs

# Load .env file with logging
safe_load_envs()  # Loads from ".env"

# Load from custom path
safe_load_envs("config/.env")

# Silent loading
safe_load_envs(verbose=False)
```

## YAML Configuration

### Basic Usage

```python
from configplusplus import YamlConfigLoader

class MyConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Access raw YAML data
        self.database_host = self._raw_config["database"]["host"]
        self.database_port = self._raw_config["database"]["port"]
```

### Helper Methods

```python
config = MyConfig("config.yaml")

# Get values with dot notation
host = config.get("database.host")
port = config.get("database.port")

# Get with default
timeout = config.get("api.timeout", default=30)

# Check if key exists
if config.has("database.host"):
    print("Database configured")

# Convert to dictionary
config_dict = config.to_dict()
```

## Advanced Features

### Custom Validation

```python
class ValidatedConfig(EnvConfigLoader):
    DATABASE_PORT = env("DATABASE_PORT", cast=int)
    
    @classmethod
    def validate(cls) -> None:
        super().validate()
        if cls.DATABASE_PORT < 1024:
            raise RuntimeError("DATABASE_PORT must be >= 1024")

# Validate configuration
ValidatedConfig.validate()
```

### Structured Data from YAML

```python
from dataclasses import dataclass
from typing import List

@dataclass
class FilterConfig:
    name: str
    type: str
    enabled: bool = True

class UiConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Parse list of structured objects
        self.filters: List[FilterConfig] = [
            FilterConfig(**f)
            for f in self._raw_config["filters"]
        ]
```

### Multiple Configuration Sources

```python
# Combine environment and YAML configs
class AppConfig(EnvConfigLoader):
    # From environment
    SECRET_API_KEY = env("SECRET_API_KEY")
    DATABASE_HOST = env("DATABASE_HOST")
    
    # Load YAML for features
    @classmethod
    def load_features(cls) -> None:
        yaml_config = YamlConfigLoader("features.yaml")
        cls.FEATURES = yaml_config.get("features")

AppConfig.load_features()
```

## Secret Masking

Variables containing these keywords are automatically masked in output:
- `SECRET`
- `API_KEY`
- `PASSWORD`
- `TOKEN`
- `CREDENTIAL`

Example:
```python
SECRET_API_KEY = "sk_live_abc123xyz789"
# Output: "sk_...89 (hidden)"

PASSWORD = "short"
# Output: "***hidden***"
```

## Configuration Grouping

Configuration values are automatically grouped by prefix:

```python
class AppConfig(EnvConfigLoader):
    DATABASE_HOST = env("DATABASE_HOST")
    DATABASE_PORT = env("DATABASE_PORT", cast=int)
    API_ENDPOINT = env("API_ENDPOINT")
    API_KEY = env("API_KEY")
```

**Output shows grouped display:**
```
▶ DATABASE
    DATABASE_HOST = 'localhost'
    DATABASE_PORT = 5432

▶ API
    API_ENDPOINT = 'https://api.example.com'
    API_KEY = 'key...23 (hidden)'
```

## Real-World Examples

### FastAPI Application Config

```python
from configplusplus import EnvConfigLoader, env, safe_load_envs
import pathlib

safe_load_envs()

class APIConfig(EnvConfigLoader):
    # Server
    HOST = env("HOST", default="0.0.0.0")
    PORT = env("PORT", cast=int, default=8000)
    
    # Database
    DATABASE_URL = env("DATABASE_URL")
    DATABASE_POOL_SIZE = env("DATABASE_POOL_SIZE", cast=int, default=10)
    
    # Redis
    REDIS_HOST = env("REDIS_HOST", default="localhost")
    REDIS_PORT = env("REDIS_PORT", cast=int, default=6379)
    
    # Security
    SECRET_JWT_KEY = env("SECRET_JWT_KEY")
    TOKEN_EXPIRE_MINUTES = env("TOKEN_EXPIRE_MINUTES", cast=int, default=60)
    
    # Features
    ENABLE_CORS = env("ENABLE_CORS", cast=bool, default=True)
    ENABLE_DOCS = env("ENABLE_DOCS", cast=bool, default=False)
    
    @classmethod
    def validate(cls) -> None:
        if cls.PORT < 1024 or cls.PORT > 65535:
            raise RuntimeError("Invalid PORT")

# Use in FastAPI
from fastapi import FastAPI

app = FastAPI(
    title="My API",
    docs_url="/docs" if APIConfig.ENABLE_DOCS else None,
)
```

### Document Processing Pipeline Config

```python
from configplusplus import YamlConfigLoader
from typing import List
from dataclasses import dataclass

@dataclass
class ProcessorConfig:
    name: str
    enabled: bool
    priority: int

class PipelineConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Parse processors
        self.processors: List[ProcessorConfig] = [
            ProcessorConfig(**p)
            for p in self._raw_config["processors"]
        ]
        
        # Parse paths
        self.input_dir = pathlib.Path(self._raw_config["paths"]["input"])
        self.output_dir = pathlib.Path(self._raw_config["paths"]["output"])
        
        # Parse settings
        self.batch_size = self._raw_config["settings"]["batch_size"]
        self.max_workers = self._raw_config["settings"]["max_workers"]

# Load configuration
config = PipelineConfig("pipeline.yaml")

# Use in pipeline
for processor in sorted(config.processors, key=lambda x: x.priority):
    if processor.enabled:
        print(f"Running {processor.name}")
```

## Documentation

- **Quick Reference**: See [REFERENCE.md](REFERENCE.md) for a cheat sheet
- **Detailed Guide**: See [USAGE.md](USAGE.md) for comprehensive documentation
- **Examples**: Check the `examples/` directory for working code samples

## Links

- **PyPI**: https://pypi.org/project/configplusplus/
- **GitHub**: https://github.com/Florian-BARRE/ConfigPlusPlus
- **Issues**: https://github.com/Florian-BARRE/ConfigPlusPlus/issues

## License

MIT License - See [LICENSE](LICENSE) file for details.

**Author**: Florian BARRE
