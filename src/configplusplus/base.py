"""
Base classes for configuration management with beautiful display
"""

from typing import Any, Dict
import pathlib


class ConfigMeta(type):
    """
    Metaclass to provide pretty printing and helpers on configuration classes.

    Automatically adds:
    - to_dict(): Convert config to dictionary
    - Pretty __repr__ with grouped display
    - Secret masking for sensitive values
    """

    def to_dict(cls) -> Dict[str, Any]:
        """
        Return all UPPERCASE, non-callable attributes as a dict.

        Returns:
            Dictionary containing all configuration values
        """
        return {
            k: v for k, v in cls.__dict__.items() if k.isupper() and not callable(v)
        }

    def _mask_if_secret(cls, key: str, value: Any) -> Any:
        """
        Mask potentially sensitive values (API keys, tokens, secrets, passwords).

        Args:
            key: Configuration key name
            value: Configuration value

        Returns:
            Masked value if sensitive, original value otherwise
        """
        if value is None:
            return None

        key_upper = key.upper()
        sensitive_keywords = ("SECRET", "API_KEY", "PASSWORD", "TOKEN", "CREDENTIAL")

        if any(keyword in key_upper for keyword in sensitive_keywords):
            s = str(value)
            if len(s) <= 6:
                return "***hidden***"
            return f"{s[:3]}…{s[-2:]} (hidden)"

        return value

    def _grouped_items(cls) -> Dict[str, list]:
        """
        Group configuration items by prefix before first underscore.

        Example:
            QDRANT_URL and QDRANT_PORT -> grouped under "QDRANT"

        Returns:
            Dictionary mapping prefixes to list of (key, value) tuples
        """
        items = cls.to_dict()
        groups: Dict[str, list] = {}

        for k, v in items.items():
            prefix = k.split("_", 1)[0]  # e.g., QDRANT_URL -> QDRANT
            groups.setdefault(prefix, []).append((k, v))

        return groups

    def __repr__(cls) -> str:
        """
        Pretty multi-line representation of the configuration.

        Returns:
            Formatted string with grouped configuration display
        """
        lines = ["\n"]
        lines.append("╔════════════════════════════════════════════╗")
        lines.append(f"║  {cls.__name__.upper().center(40)}  ║")
        lines.append("╚════════════════════════════════════════════╝")

        groups = cls._grouped_items()

        # Sort groups by name for deterministic output
        for prefix in sorted(groups.keys()):
            lines.append("")  # blank line
            lines.append(f"▶ {prefix}")
            items = groups[prefix]

            if not items:
                continue

            max_key_len = max(len(k) for k, _ in items)

            for key, value in sorted(items, key=lambda kv: kv[0]):
                display_value = cls._mask_if_secret(key, value)

                # Make paths nicer to read
                if isinstance(display_value, pathlib.Path):
                    display_value = str(display_value.resolve())

                lines.append(f"    {key.ljust(max_key_len)} = {display_value!r}")

        lines.append("")  # final blank line
        return "\n".join(lines)


class ConfigBase(metaclass=ConfigMeta):
    """
    Base class for all configuration classes.

    Provides:
    - Pretty printing via metaclass
    - to_dict() method for serialization
    - Automatic grouping and display of config values

    Usage:
        class MyConfig(ConfigBase):
            DATABASE_HOST = "localhost"
            DATABASE_PORT = 5432
            SECRET_API_KEY = "secret123"

        print(MyConfig)  # Pretty formatted output
    """

    def __repr__(self) -> str:
        """Instance-level repr uses the class pretty repr."""
        # Call the metaclass __repr__ directly
        return ConfigMeta.__repr__(type(self))

    def __str__(self) -> str:
        """Instance-level str uses the class pretty repr."""
        # Call the metaclass __repr__ directly
        return ConfigMeta.__repr__(type(self))
