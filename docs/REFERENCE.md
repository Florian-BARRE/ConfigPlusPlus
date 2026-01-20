# ConfigPlusPlus - Quick Reference

## Installation

```bash
pip install configplusplus
# or
poetry add configplusplus
```

## Environment Config (Static)

```python
from configplusplus import EnvConfigLoader, env, safe_load_envs

# Load .env file
safe_load_envs()

class Config(EnvConfigLoader):
    # String (default)
    HOST = env("HOST")
    
    # With type casting
    PORT = env("PORT", cast=int)
    DEBUG = env("DEBUG", cast=bool)
    RATE = env("RATE", cast=float)
    DATA_DIR = env("DATA_DIR", cast=pathlib.Path)
    
    # With defaults
    TIMEOUT = env("TIMEOUT", cast=int, default=30)
    
    # Optional
    OPTIONAL = env("OPTIONAL", required=False, default=None)
    
    # Secrets (auto-masked)
    SECRET_API_KEY = env("SECRET_API_KEY")
    
    # Validation
    @classmethod
    def validate(cls) -> None:
        if cls.PORT < 1024:
            raise RuntimeError("Invalid port")

# Usage
print(Config.HOST)
print(Config)  # Pretty output
Config.validate()
```

## YAML Config (Instance)

```python
from configplusplus import YamlConfigLoader
from typing import List
from dataclasses import dataclass

@dataclass
class Feature:
    name: str
    enabled: bool

class Config(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Simple values
        self.app_name = self._raw_config["app"]["name"]
        
        # Structured data
        self.features: List[Feature] = [
            Feature(**f) for f in self._raw_config["features"]
        ]

# Usage
config = Config("config.yaml")
print(config.app_name)
print(config)  # Pretty output
```

## Helper Functions

```python
# Load environment files
safe_load_envs()                    # Load .env
safe_load_envs("config/.env")       # Custom path
safe_load_envs(verbose=False)       # Silent

# Read environment variables
env("KEY")                           # Required string
env("KEY", cast=int)                 # Required int
env("KEY", default="value")          # Optional with default
env("KEY", cast=bool, default=False) # Bool with default
env("KEY", required=False)           # Explicitly optional
```

## Boolean Casting

```python
# These are False:
"false", "False", "0", "no", ""

# Everything else is True:
"true", "True", "1", "yes", "anything"
```

## Helper Methods

```python
# EnvConfigLoader
Config.get("KEY", default="fallback")
Config.has("KEY")
Config.to_dict()
Config.validate()

# YamlConfigLoader
config.get("app.name")                    # Dot notation
config.get("app.timeout", default=30)     # With default
config.has("app.name")                    # Check exists
config.to_dict()                          # Convert to dict
```

## Secret Masking

Auto-masked keywords:
- SECRET
- API_KEY
- PASSWORD
- TOKEN
- CREDENTIAL

```python
SECRET_API_KEY = "sk_live_abc123"
# Output: "sk_...23 (hidden)"
```

## Type Casting

```python
env("PORT", cast=int)           # "8000" → 8000
env("RATE", cast=float)         # "0.5" → 0.5
env("DEBUG", cast=bool)         # "true" → True
env("PATH", cast=pathlib.Path)  # "/data" → Path("/data")
```

## Validation

```python
class Config(EnvConfigLoader):
    PORT = env("PORT", cast=int)
    
    @classmethod
    def validate(cls) -> None:
        super().validate()
        if cls.PORT < 1024 or cls.PORT > 65535:
            raise RuntimeError("Invalid PORT")

Config.validate()  # Raises RuntimeError if invalid
```

## Configuration Grouping

```python
class Config(EnvConfigLoader):
    DATABASE_HOST = env("DATABASE_HOST")
    DATABASE_PORT = env("DATABASE_PORT", cast=int)
    API_KEY = env("API_KEY")
    API_TIMEOUT = env("API_TIMEOUT", cast=int)

# Output groups by prefix:
# ▶ DATABASE
#     DATABASE_HOST = 'localhost'
#     DATABASE_PORT = 5432
# ▶ API
#     API_KEY = 'key...23 (hidden)'
#     API_TIMEOUT = 30
```

## YAML Structure

```yaml
# config.yaml
app:
  name: "My App"
  version: "1.0.0"

database:
  host: "localhost"
  port: 5432

features:
  - name: "search"
    enabled: true
  - name: "export"
    enabled: false
```

```python
class Config(YamlConfigLoader):
    def __post_init__(self) -> None:
        self.app_name = self._raw_config["app"]["name"]
        self.db_host = self._raw_config["database"]["host"]
        self.features = self._raw_config["features"]
```

## Combining Both

```python
# Infrastructure from env
class InfraConfig(EnvConfigLoader):
    SECRET_API_KEY = env("SECRET_API_KEY")
    DATABASE_URL = env("DATABASE_URL")

# Features from YAML
class AppConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        self.features = self._raw_config["features"]

# Use both
print(InfraConfig.SECRET_API_KEY)
config = AppConfig("config.yaml")
print(config.features)
```

## .env File

```bash
# .env
DATABASE_URL=postgresql://localhost/mydb
SECRET_API_KEY=sk_live_abc123
DEBUG=true
PORT=8000
TIMEOUT=30
```

## Common Patterns

### FastAPI Config
```python
class APIConfig(EnvConfigLoader):
    HOST = env("HOST", default="0.0.0.0")
    PORT = env("PORT", cast=int, default=8000)
    DATABASE_URL = env("DATABASE_URL")
    SECRET_JWT_KEY = env("SECRET_JWT_KEY")
    ENABLE_CORS = env("ENABLE_CORS", cast=bool, default=True)
```

### Multiple Configs
```python
class DatabaseConfig(EnvConfigLoader):
    HOST = env("DB_HOST")
    PORT = env("DB_PORT", cast=int)

class RedisConfig(EnvConfigLoader):
    HOST = env("REDIS_HOST")
    PORT = env("REDIS_PORT", cast=int)

class AppConfig:
    db = DatabaseConfig
    redis = RedisConfig
```

### Environment Profiles
```python
class BaseConfig(EnvConfigLoader):
    DEBUG = False

class DevelopmentConfig(BaseConfig):
    DEBUG = True

class ProductionConfig(BaseConfig):
    DEBUG = False

ENV = env("ENVIRONMENT", default="development")
Config = DevelopmentConfig if ENV == "dev" else ProductionConfig
```

## Links

- **PyPI**: https://pypi.org/project/configplusplus/
- **GitHub**: https://github.com/Florian-BARRE/ConfigPlusPlus
- **Author**: Florian BARRE
