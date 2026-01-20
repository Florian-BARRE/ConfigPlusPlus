"""
Utility functions for configuration management
"""

from typing import Any, TypeVar
from dotenv import load_dotenv
from loggerplusplus import loggerplusplus
from loggerplusplus import formats as lpp_formats
import sys
import os

T = TypeVar("T")


def safe_load_envs(env_path: str = ".env", verbose: bool = True) -> bool:
    """
    Load environment variables from .env file with detailed logging.

    Args:
        env_path: Path to the .env file (default: ".env")
        verbose: Whether to log loading information (default: True)

    Returns:
        True if file was loaded successfully, False otherwise

    Example:
        >>> safe_load_envs()
        ✅ Loaded environment file: .env
        True
    """
    if verbose:
        loggerplusplus.add(
            sink=sys.stdout,
            level="DEBUG",
            format=lpp_formats.ShortFormat(),
        )
        env_logger = loggerplusplus.bind(identifier="ENV_LOADER")

    # Try with leading slash first (absolute path)
    success = load_dotenv(f"/{env_path}")

    if success and verbose:
        env_logger.info(f"✅ Loaded environment file: /{env_path}")
    elif not success:
        # Try without leading slash (relative path)
        success = load_dotenv(env_path)
        if success and verbose:
            env_logger.info(f"✅ Loaded environment file: {env_path}")
        elif verbose:
            env_logger.info(f"ℹ️ Environment file not found: {env_path}")

    if verbose:
        loggerplusplus.remove()

    return success


def env(
    key: str, *, default: Any = None, cast: type = str, required: bool = True
) -> Any:
    """
    Read environment variable with optional type casting and default value.

    Args:
        key: Environment variable name
        default: Default value if not found (default: None)
        cast: Type to cast the value to (default: str)
        required: Whether the variable is required (default: True)

    Returns:
        The environment variable value, cast to the specified type

    Raises:
        RuntimeError: If required variable is missing and no default provided

    Examples:
        >>> env("DATABASE_PORT", cast=int, default=5432)
        5432

        >>> env("DEBUG_MODE", cast=bool, default=False)
        False

        >>> env("API_KEY")  # Required by default
        RuntimeError: missing required env var API_KEY
    """
    val = os.getenv(key, default)

    if val is None:
        if required:
            raise RuntimeError(f"missing required env var {key}")
        return None

    # Special handling for boolean casting from string
    if cast == bool and isinstance(val, str):
        return val.strip().lower() not in {"false", "0", "no", ""}

    return cast(val)


def env_optional(key: str, *, default: Any = None, cast: type = str) -> Any:
    """
    Read optional environment variable with type casting.

    Convenience wrapper for env() with required=False.

    Args:
        key: Environment variable name
        default: Default value if not found (default: None)
        cast: Type to cast the value to (default: str)

    Returns:
        The environment variable value, cast to the specified type, or default

    Example:
        >>> env_optional("OPTIONAL_FEATURE", cast=bool, default=False)
        False
    """
    return env(key, default=default, cast=cast, required=False)
