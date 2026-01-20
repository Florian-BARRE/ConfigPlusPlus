# ConfigPlusPlus Usage Guide

## Table of Contents
1. [Installation](#installation)
2. [Environment-Based Configuration](#environment-based-configuration)
3. [YAML-Based Configuration](#yaml-based-configuration)
4. [Advanced Usage](#advanced-usage)
5. [Best Practices](#best-practices)

## Installation

```bash
# Using pip
pip install configplusplus

# Using Poetry
poetry add configplusplus

# Development installation
git clone https://github.com/Florian-BARRE/ConfigPlusPlus.git
cd ConfigPlusPlus
poetry install
```

## Environment-Based Configuration

### Basic Structure

```python
from configplusplus import EnvConfigLoader, env, safe_load_envs
import pathlib

# Load .env file
safe_load_envs()

class AppConfig(EnvConfigLoader):
    """Application configuration from environment variables."""
    
    # Simple string values
    APP_NAME = env("APP_NAME", default="MyApp")
    
    # Type casting
    PORT = env("PORT", cast=int, default=8000)
    DEBUG = env("DEBUG", cast=bool, default=False)
    TIMEOUT = env("TIMEOUT", cast=float, default=30.0)
    
    # Paths
    DATA_DIR = env("DATA_DIR", cast=pathlib.Path)
    
    # Required values (will raise if missing)
    DATABASE_URL = env("DATABASE_URL")
    
    # Optional values
    OPTIONAL_FEATURE = env("OPTIONAL_FEATURE", required=False, default=None)
    
    # Secrets (automatically masked)
    SECRET_API_KEY = env("SECRET_API_KEY")
```

### Type Casting Examples

```python
# Integer
PORT = env("PORT", cast=int)  # "8000" -> 8000

# Float
TEMPERATURE = env("TEMPERATURE", cast=float)  # "0.7" -> 0.7

# Boolean (flexible string parsing)
DEBUG = env("DEBUG", cast=bool)  
# "true" / "1" / "yes" -> True
# "false" / "0" / "no" / "" -> False

# Path
DATA_DIR = env("DATA_DIR", cast=pathlib.Path)  # "/var/data" -> Path("/var/data")

# List (requires custom parsing)
ALLOWED_HOSTS = env("ALLOWED_HOSTS", default="").split(",")
```

### Validation

```python
class DatabaseConfig(EnvConfigLoader):
    HOST = env("DB_HOST")
    PORT = env("DB_PORT", cast=int)
    NAME = env("DB_NAME")
    
    @classmethod
    def validate(cls) -> None:
        """Custom validation logic."""
        super().validate()
        
        if cls.PORT < 1024 or cls.PORT > 65535:
            raise RuntimeError("Port must be between 1024-65535")
        
        if not cls.HOST:
            raise RuntimeError("Host cannot be empty")

# Validate on startup
DatabaseConfig.validate()
```

### Accessing Configuration

```python
# Static access (recommended)
print(AppConfig.DATABASE_URL)
print(AppConfig.PORT)

# Helper methods
value = AppConfig.get("PORT", default=8000)
has_key = AppConfig.has("DATABASE_URL")

# Convert to dictionary
config_dict = AppConfig.to_dict()

# Pretty print
print(AppConfig)  # Shows beautiful formatted output
```

## YAML-Based Configuration

### Basic Structure

```python
from configplusplus import YamlConfigLoader
from typing import List
from dataclasses import dataclass

class MyConfig(YamlConfigLoader):
    """Configuration from YAML file."""
    
    def __post_init__(self) -> None:
        """Parse YAML data after loading."""
        
        # Simple values
        self.app_name = self._raw_config["app"]["name"]
        self.version = self._raw_config["app"]["version"]
        
        # Nested values
        self.db_host = self._raw_config["database"]["host"]
        self.db_port = self._raw_config["database"]["port"]
        
        # Type conversion
        self.debug = bool(self._raw_config["app"].get("debug", False))

# Load configuration
config = MyConfig("config.yaml")
```

### Working with Structured Data

```python
@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str

@dataclass
class Feature:
    name: str
    enabled: bool
    priority: int = 0

class AppConfig(YamlConfigLoader):
    def __post_init__(self) -> None:
        # Parse database config
        self.database = DatabaseConfig(
            **self._raw_config["database"]
        )
        
        # Parse list of features
        self.features: List[Feature] = [
            Feature(**f) 
            for f in self._raw_config["features"]
        ]
        
        # Get enabled features
        self.enabled_features = [
            f for f in self.features if f.enabled
        ]

# Usage
config = AppConfig("config.yaml")
print(f"Database: {config.database.host}:{config.database.port}")
for feature in config.enabled_features:
    print(f"Feature: {feature.name}")
```

### YAML File Examples

**Simple configuration:**
```yaml
app:
  name: "My Application"
  version: "1.0.0"
  debug: false

database:
  host: "localhost"
  port: 5432
  name: "myapp"
  user: "admin"
  password: "secret"
```

**Complex configuration:**
```yaml
application:
  name: "Document Processor"
  version: "2.0.0"
  
features:
  - name: "ocr"
    enabled: true
    priority: 1
  - name: "export"
    enabled: false
    priority: 2

processors:
  - type: "pdf"
    extensions: [".pdf"]
    max_size_mb: 50
  - type: "image"
    extensions: [".jpg", ".png"]
    max_size_mb: 10

paths:
  input: "/data/input"
  output: "/data/output"
  temp: "/tmp/processing"
```

### Helper Methods

```python
config = MyConfig("config.yaml")

# Get with dot notation
host = config.get("database.host")
port = config.get("database.port")

# Get with default
timeout = config.get("api.timeout", default=30)

# Check existence
if config.has("features.ocr"):
    print("OCR enabled")

# Access raw config
raw_data = config._raw_config

# Convert to dict
config_dict = config.to_dict()
```

## Advanced Usage

### Combining Environment and YAML

```python
class HybridConfig(EnvConfigLoader):
    """Combine environment variables and YAML."""
    
    # From environment
    SECRET_API_KEY = env("SECRET_API_KEY")
    DATABASE_URL = env("DATABASE_URL")
    
    # Load YAML for features
    _yaml_config = None
    
    @classmethod
    def load_yaml(cls, path: str) -> None:
        """Load YAML configuration."""
        from configplusplus import YamlConfigLoader
        
        class YamlPart(YamlConfigLoader):
            def __post_init__(self) -> None:
                self.features = self._raw_config.get("features", [])
        
        cls._yaml_config = YamlPart(path)
        cls.FEATURES = cls._yaml_config.features

# Use it
HybridConfig.load_yaml("features.yaml")
print(HybridConfig.SECRET_API_KEY)
print(HybridConfig.FEATURES)
```

### Dynamic Configuration Updates

```python
class DynamicConfig(EnvConfigLoader):
    """Configuration that can be updated at runtime."""
    
    FEATURE_FLAG = env("FEATURE_FLAG", cast=bool, default=False)
    
    @classmethod
    def enable_feature(cls) -> None:
        """Enable feature at runtime."""
        cls.FEATURE_FLAG = True
    
    @classmethod
    def reload(cls) -> None:
        """Reload configuration from environment."""
        cls.FEATURE_FLAG = env("FEATURE_FLAG", cast=bool, default=False)

# Usage
DynamicConfig.enable_feature()
print(DynamicConfig.FEATURE_FLAG)  # True

DynamicConfig.reload()
print(DynamicConfig.FEATURE_FLAG)  # Back to env value
```

### Configuration Profiles

```python
class BaseConfig(EnvConfigLoader):
    """Base configuration."""
    APP_NAME = env("APP_NAME", default="MyApp")
    DEBUG = env("DEBUG", cast=bool, default=False)

class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(BaseConfig):
    """Production configuration."""
    DEBUG = False
    LOG_LEVEL = "WARNING"

# Select profile
ENV = env("ENVIRONMENT", default="development")

if ENV == "production":
    Config = ProductionConfig
else:
    Config = DevelopmentConfig

print(Config)
```

## Best Practices

### 1. Use .env Files for Development

```bash
# .env
DATABASE_URL=postgresql://localhost/myapp
SECRET_API_KEY=dev_key_123
DEBUG=true
```

```python
from configplusplus import safe_load_envs

# Load .env at startup
safe_load_envs()

class Config(EnvConfigLoader):
    DATABASE_URL = env("DATABASE_URL")
    # ...
```

### 2. Group Related Configuration

```python
class DatabaseConfig(EnvConfigLoader):
    """Database configuration only."""
    DATABASE_HOST = env("DATABASE_HOST")
    DATABASE_PORT = env("DATABASE_PORT", cast=int)
    DATABASE_NAME = env("DATABASE_NAME")

class RedisConfig(EnvConfigLoader):
    """Redis configuration only."""
    REDIS_HOST = env("REDIS_HOST")
    REDIS_PORT = env("REDIS_PORT", cast=int)

class AppConfig:
    """Main application config."""
    db = DatabaseConfig
    redis = RedisConfig

# Usage
print(AppConfig.db.DATABASE_HOST)
print(AppConfig.redis.REDIS_PORT)
```

### 3. Validate Early

```python
class Config(EnvConfigLoader):
    # ... configuration ...
    
    @classmethod
    def validate(cls) -> None:
        super().validate()
        # Add validation logic
        if cls.PORT < 1024:
            raise RuntimeError("Invalid port")

# Validate at startup
try:
    Config.validate()
except RuntimeError as e:
    print(f"Configuration error: {e}")
    sys.exit(1)
```

### 4. Document Configuration

```python
class Config(EnvConfigLoader):
    """
    Application configuration loaded from environment variables.
    
    Required variables:
        - DATABASE_URL: PostgreSQL connection string
        - SECRET_API_KEY: API authentication key
        
    Optional variables:
        - DEBUG: Enable debug mode (default: False)
        - PORT: Server port (default: 8000)
    """
    
    # Database connection string (required)
    DATABASE_URL = env("DATABASE_URL")
    
    # API authentication key (required, will be masked in logs)
    SECRET_API_KEY = env("SECRET_API_KEY")
    
    # Enable debug mode (optional, default: False)
    DEBUG = env("DEBUG", cast=bool, default=False)
    
    # Server port (optional, default: 8000)
    PORT = env("PORT", cast=int, default=8000)
```

### 5. Use Type Hints

```python
from typing import List, Dict
import pathlib

class Config(EnvConfigLoader):
    HOST: str = env("HOST")
    PORT: int = env("PORT", cast=int)
    DEBUG: bool = env("DEBUG", cast=bool, default=False)
    DATA_DIR: pathlib.Path = env("DATA_DIR", cast=pathlib.Path)
```

### 6. Create .env.example

```bash
# .env.example - Template for environment variables
# Copy to .env and fill in your values

# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# API Keys (get from https://example.com/api-keys)
SECRET_API_KEY=your_secret_key_here

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Paths
DATA_DIR=/var/data/myapp
LOG_FILE=/var/log/myapp/app.log
```

### 7. Keep Secrets Out of Code

```python
# ❌ BAD - Secrets in code
class Config(EnvConfigLoader):
    API_KEY = "sk_live_abc123"  # Never do this!

# ✅ GOOD - Secrets from environment
class Config(EnvConfigLoader):
    SECRET_API_KEY = env("SECRET_API_KEY")

# ✅ GOOD - Secrets from .env file (not committed to git)
safe_load_envs()
class Config(EnvConfigLoader):
    SECRET_API_KEY = env("SECRET_API_KEY")
```

### 8. Use Appropriate Defaults

```python
class Config(EnvConfigLoader):
    # Good defaults for common cases
    HOST = env("HOST", default="0.0.0.0")
    PORT = env("PORT", cast=int, default=8000)
    
    # No default for required secrets
    SECRET_API_KEY = env("SECRET_API_KEY")
    
    # Feature flags with safe defaults
    ENABLE_DEBUG = env("ENABLE_DEBUG", cast=bool, default=False)
    ENABLE_TELEMETRY = env("ENABLE_TELEMETRY", cast=bool, default=True)
```

## Troubleshooting

### Common Issues

**Issue: Missing required environment variable**
```python
RuntimeError: missing required env var DATABASE_URL
```
Solution: Set the variable in your environment or .env file

**Issue: Type casting error**
```python
ValueError: invalid literal for int() with base 10: 'abc'
```
Solution: Ensure the environment variable contains a valid value for the type

**Issue: YAML file not found**
```python
FileNotFoundError: Configuration file not found: config.yaml
```
Solution: Check the file path is correct and the file exists

**Issue: Secrets visible in logs**
Solution: Use keywords like SECRET_, API_KEY, PASSWORD in variable names for automatic masking

## More Examples

See the `examples/` directory for complete working examples:
- `env_config_example.py` - Environment-based configuration
- `yaml_config_example.py` - YAML-based configuration
- `.env.example` - Example environment file
- `config.yaml` - Example YAML configuration
