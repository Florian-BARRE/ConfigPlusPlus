"""
Utility functions for configuration management
"""

import os
import pathlib
import sys
from typing import Any

from dotenv import load_dotenv
from loggerplusplus import formats as lpp_formats
from loggerplusplus import loggerplusplus


def safe_load_envs(path: str | pathlib.Path, verbose: bool = True) -> bool:
    """
    Load all *.env files found at the given path (file or directory)
    with detailed logging.

    Args:
        path: Path to a directory containing *.env files
              OR path to a specific .env file.
        verbose: Whether to log loading information (default: True)

    Returns:
        True if at least one environment file was successfully loaded,
        False otherwise.

    Example:
        > safe_load_envs("./config")
        *.env files found: [PosixPath('config/.env'), PosixPath('config/dev.env')]
        ✅ Loaded environment file: config/.env
        ✅ Loaded environment file: config/dev.env
        True

        > safe_load_envs(".env")
        *.env files found: [PosixPath('.env')]
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
    else:
        env_logger = None

    path_obj = pathlib.Path(path)
    loaded_any = False

    # Collect all *.env files
    if path_obj.is_dir():
        env_files = sorted(path_obj.glob("*.env"))
    elif path_obj.is_file() and path_obj.suffix == ".env":
        env_files = [path_obj]
    else:
        env_files = []

    if verbose:
        env_logger.info(f"*.env files found: {env_files}")

    # Load all found *.env files
    if not env_files:
        if verbose:
            env_logger.warning(f"ℹ️ No *.env files found at path: {path_obj}")
    else:
        for env_file in env_files:
            success = load_dotenv(env_file)
            if success:
                if verbose:
                    env_logger.info(f"✅ Loaded environment file: {env_file}")
                loaded_any = True
            else:
                if verbose:
                    env_logger.warning(
                        f"⚠️ Failed to load environment file: {env_file}"
                    )

    if verbose:
        loggerplusplus.remove()

    return loaded_any


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
        > env("DATABASE_PORT", cast=int, default=5432)
        5432

        > env("DEBUG_MODE", cast=bool, default=False)
        False

        > env("API_KEY")  # Required by default
        RuntimeError: missing required env var API_KEY
    """
    val = os.getenv(key, default)

    if val is None:
        if required:
            raise RuntimeError(f"missing required env var {key}")
        return None

    # Special handling for boolean casting from string
    if cast is bool and isinstance(val, str):
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
        > env_optional("OPTIONAL_FEATURE", cast=bool, default=False)
        False
    """
    return env(key, default=default, cast=cast, required=False)
