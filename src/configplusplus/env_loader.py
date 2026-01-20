"""
Environment variable based configuration loader
"""

from typing import Any
from configplusplus.base import ConfigBase
from configplusplus.utils import env, env_optional
import pathlib


class EnvConfigLoader(ConfigBase):
    """
    Base class for environment variable based configuration.

    This class is 100% static with no __init__ - configuration is loaded
    from environment variables at class definition time.

    Features:
    - Automatic pretty printing via ConfigBase
    - Secret masking for sensitive values
    - Grouped display by configuration prefix

    Usage:
        from configplusplus import EnvConfigLoader, env

        class MyConfig(EnvConfigLoader):
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
        print(MyConfig.DATABASE_HOST)
        print(MyConfig)  # Pretty formatted output

    Helper Methods:
        You can use the env() helper function with various options:

        env(key)                                    # Required, str
        env(key, cast=int)                          # Required, int
        env(key, default="value")                   # Optional with default
        env(key, cast=bool, default=False)          # Bool casting
        env(key, cast=pathlib.Path)                 # Path casting
        env_optional(key, default=None)             # Explicitly optional

    Boolean Casting:
        When cast=bool, these strings are considered False:
        - "false", "False", "FALSE"
        - "0"
        - "no", "No", "NO"
        - "" (empty string)

        All other values are considered True.

    Secret Masking:
        Variables containing these keywords are automatically masked:
        - SECRET
        - API_KEY
        - PASSWORD
        - TOKEN
        - CREDENTIAL

        Example output: "sec...et (hidden)"
    """

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key (case-insensitive)
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            >>> MyConfig.get("DATABASE_HOST")
            "localhost"

            >>> MyConfig.get("MISSING_KEY", default="fallback")
            "fallback"
        """
        return getattr(cls, key.upper(), default)

    @classmethod
    def has(cls, key: str) -> bool:
        """
        Check if a configuration key exists.

        Args:
            key: Configuration key (case-insensitive)

        Returns:
            True if key exists, False otherwise

        Example:
            >>> MyConfig.has("DATABASE_HOST")
            True

            >>> MyConfig.has("MISSING_KEY")
            False
        """
        return hasattr(cls, key.upper())

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.

        Override this method in subclasses to add custom validation logic.

        Raises:
            RuntimeError: If validation fails

        Example:
            class MyConfig(EnvConfigLoader):
                DATABASE_HOST = env("DATABASE_HOST")
                DATABASE_PORT = env("DATABASE_PORT", cast=int)

                @classmethod
                def validate(cls) -> None:
                    super().validate()
                    if cls.DATABASE_PORT < 1024:
                        raise RuntimeError("DATABASE_PORT must be >= 1024")
        """
        pass
