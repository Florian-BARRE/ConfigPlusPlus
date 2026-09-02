"""
Base classes for configuration management with beautiful display
"""

from typing import Any

from configplusplus import _display


class ConfigMeta(type):
    """
    Metaclass to provide pretty printing and helpers on configuration classes.

    Automatically adds:
    - to_dict(): Convert config to dictionary
    - Pretty __repr__ with grouped display
    - Secret masking for sensitive values
    """

    def to_dict(cls, *, mask: bool = False) -> dict[str, Any]:
        """
        Return all UPPERCASE, non-callable attributes as a dict.

        Attributes are collected across the whole MRO, so a config subclass
        inherits the UPPERCASE fields of its parents (a child value overrides
        a parent value of the same name).

        Args:
            mask: When True, sensitive values are masked (safe to log). When
                False (default), raw values are returned.

        Returns:
            Dictionary containing all configuration values
        """
        result: dict[str, Any] = {}
        for klass in reversed(cls.__mro__):
            for k, v in vars(klass).items():
                if k.isupper() and not k.startswith("_") and not callable(v):
                    result[k] = v

        if mask:
            keywords = getattr(
                cls, "_sensitive_keywords", _display.DEFAULT_SENSITIVE_KEYWORDS
            )
            result = {
                k: _display.mask_if_secret(k, v, keywords) for k, v in result.items()
            }
        return result

    def _mask_if_secret(cls, key: str, value: Any) -> Any:
        """
        Mask potentially sensitive values (API keys, tokens, secrets, passwords).

        Args:
            key: Configuration key name
            value: Configuration value

        Returns:
            Masked value if sensitive, original value otherwise
        """
        keywords = getattr(
            cls, "_sensitive_keywords", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        return _display.mask_if_secret(key, value, keywords)

    def _grouped_items(cls) -> dict[str, list]:
        """
        Group configuration items by prefix before first underscore.

        Example:
            QDRANT_URL and QDRANT_PORT -> grouped under "QDRANT"

        Returns:
            Dictionary mapping prefixes to list of (key, value) tuples
        """
        items = cls.to_dict()
        groups: dict[str, list] = {}

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

            max_key_len = max(len(k) for k, _ in items)

            for key, value in sorted(items, key=lambda kv: kv[0]):
                display_value = _display.format_value(cls._mask_if_secret(key, value))
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

    Extending the masked keywords (extend only, never narrow):
        class MyConfig(ConfigBase):
            _sensitive_keywords = ConfigBase._sensitive_keywords + ("PRIVATE_KEY",)
    """

    # Sensitive-keyword set used by the display/masking layer. Override in a
    # subclass by extending this tuple; never remove a keyword.
    _sensitive_keywords: tuple[str, ...] = _display.DEFAULT_SENSITIVE_KEYWORDS

    def __repr__(self) -> str:
        """Instance-level repr uses the class pretty repr."""
        # Call the metaclass __repr__ directly
        return ConfigMeta.__repr__(type(self))

    def __str__(self) -> str:
        """Instance-level str uses the class pretty repr."""
        # Call the metaclass __repr__ directly
        return ConfigMeta.__repr__(type(self))
