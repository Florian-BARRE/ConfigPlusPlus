"""Shared secret-masking and value-formatting helpers for the config loaders.

Both ``ConfigMeta`` (env/class configs) and ``YamlConfigLoader`` render and mask
values; keeping that logic here means a masking change is made once, not twice.
"""

import pathlib
from typing import Any

# The default sensitive-keyword set. A config may extend it via a class-level
# ``_sensitive_keywords`` attribute — extend only, never narrow (masking is a
# safety feature: downstream apps debug-log their whole config at startup).
DEFAULT_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "SECRET",
    "API_KEY",
    "PASSWORD",
    "TOKEN",
    "CREDENTIAL",
)


def is_sensitive(key: str, keywords: tuple[str, ...]) -> bool:
    """Return True if the key name contains any sensitive keyword (case-insensitive)."""
    upper = key.upper()
    return any(keyword in upper for keyword in keywords)


def mask_if_secret(key: str, value: Any, keywords: tuple[str, ...]) -> Any:
    """Mask a value when its key looks sensitive.

    ``None`` and non-sensitive values pass through unchanged. Short secrets
    (<= 6 chars) become ``***hidden***``; longer ones keep only their edges.
    """
    if value is None:
        return None
    if not is_sensitive(key, keywords):
        return value
    s = str(value)
    if len(s) <= 6:
        return "***hidden***"
    return f"{s[:3]}…{s[-2:]} (hidden)"


def format_value(value: Any) -> Any:
    """Resolve ``pathlib.Path`` values to readable absolute strings for display."""
    if isinstance(value, pathlib.Path):
        return str(value.resolve())
    return value
