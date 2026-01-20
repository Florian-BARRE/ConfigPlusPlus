"""
Example usage of EnvConfigLoader
"""

import pathlib
import sys
from configplusplus import EnvConfigLoader, env, safe_load_envs

# Load environment variables from .env file
safe_load_envs(".env")


class RuntimeConfig(EnvConfigLoader):
    """Runtime configuration loaded from environment variables."""
    
    # ──── Paths ────
    ROOT_DIR = pathlib.Path(__file__).resolve().parent
    DATA_DIR = env("DATA_DIR", cast=pathlib.Path, default=ROOT_DIR / "data")
    
    # ──── Database ────
    DATABASE_HOST = env("DATABASE_HOST", default="localhost")
    DATABASE_PORT = env("DATABASE_PORT", cast=int, default=5432)
    DATABASE_NAME = env("DATABASE_NAME")
    DATABASE_USER = env("DATABASE_USER")
    DATABASE_PASSWORD = env("DATABASE_PASSWORD")  # Will be masked in output
    
    # ──── API ────
    SECRET_API_KEY = env("SECRET_API_KEY")  # Will be masked in output
    API_TIMEOUT = env("API_TIMEOUT", cast=int, default=30)
    API_MAX_RETRIES = env("API_MAX_RETRIES", cast=int, default=3)
    
    # ──── Features ────
    ENABLE_DEBUG = env("ENABLE_DEBUG", cast=bool, default=False)
    ENABLE_CACHE = env("ENABLE_CACHE", cast=bool, default=True)
    ENABLE_LOGGING = env("ENABLE_LOGGING", cast=bool, default=True)
    
    # ──── Logging ────
    LOG_LEVEL = env("LOG_LEVEL", default="INFO")
    LOG_FILE = env("LOG_FILE", cast=pathlib.Path, default=ROOT_DIR / "app.log")
    
    # ──── AI Models ────
    CHAT_MODEL = env("CHAT_MODEL", default="gpt-4")
    EMBEDDINGS_MODEL = env("EMBEDDINGS_MODEL", default="text-embedding-ada-002")
    CHAT_TEMPERATURE = env("CHAT_TEMPERATURE", cast=float, default=0.7)
    CHAT_MAX_TOKENS = env("CHAT_MAX_TOKENS", cast=int, default=4000)
    
    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        super().validate()
        
        if cls.DATABASE_PORT < 1024 or cls.DATABASE_PORT > 65535:
            raise RuntimeError("DATABASE_PORT must be between 1024 and 65535")
        
        if cls.API_TIMEOUT <= 0:
            raise RuntimeError("API_TIMEOUT must be positive")
        
        if not 0 <= cls.CHAT_TEMPERATURE <= 2:
            raise RuntimeError("CHAT_TEMPERATURE must be between 0 and 2")


def main() -> None:
    """Demonstrate EnvConfigLoader usage."""
    print("=" * 50)
    print("EnvConfigLoader Example")
    print("=" * 50)
    
    # Display the full configuration
    print(RuntimeConfig)
    
    # Access individual values
    print("\n--- Accessing Individual Values ---")
    print(f"Database Host: {RuntimeConfig.DATABASE_HOST}")
    print(f"Database Port: {RuntimeConfig.DATABASE_PORT}")
    print(f"Debug Mode: {RuntimeConfig.ENABLE_DEBUG}")
    print(f"Chat Model: {RuntimeConfig.CHAT_MODEL}")
    
    # Use helper methods
    print("\n--- Using Helper Methods ---")
    print(f"Has DATABASE_HOST: {RuntimeConfig.has('DATABASE_HOST')}")
    print(f"Has MISSING_KEY: {RuntimeConfig.has('MISSING_KEY')}")
    print(f"Get LOG_LEVEL: {RuntimeConfig.get('LOG_LEVEL')}")
    print(f"Get MISSING with default: {RuntimeConfig.get('MISSING', 'fallback')}")
    
    # Validate configuration
    print("\n--- Validation ---")
    try:
        RuntimeConfig.validate()
        print("✅ Configuration is valid")
    except RuntimeError as e:
        print(f"❌ Configuration error: {e}")
    
    # Convert to dictionary
    print("\n--- Convert to Dictionary ---")
    config_dict = RuntimeConfig.to_dict()
    print(f"Total config keys: {len(config_dict)}")
    print(f"Config keys: {list(config_dict.keys())[:5]}...")


if __name__ == "__main__":
    main()
