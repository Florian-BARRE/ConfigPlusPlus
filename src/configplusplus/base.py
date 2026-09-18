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
        return _display._group_by_prefix(list(cls.to_dict().items()))

    def render(cls, *, fmt: str | None = None, mask: bool = True) -> str:
        """
        Render the configuration as a string in the requested format.

        Fields are grouped by the prefix before the first underscore in the
        ``boxed`` format; the other formats are flat.

        Args:
            fmt: One of ``configplusplus.DISPLAY_FORMATS``
                (``"boxed"``, ``"table"``, ``"json"``, ``"dotenv"``, ``"flat"``).
                Defaults to the class-level ``_display_format`` (``"boxed"``).
            mask: When True (default), sensitive values are masked — keep it True
                for anything that may be logged. Pass False only for a deliberate
                raw dump.

        Returns:
            The formatted configuration string.

        Raises:
            ValueError: If ``fmt`` is not a known display format.
        """
        chosen = fmt if fmt is not None else getattr(cls, "_display_format", "boxed")
        keywords = getattr(
            cls, "_sensitive_keywords", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        items = [
            (
                key,
                _display.format_value(
                    _display.mask_if_secret(key, value, keywords) if mask else value
                ),
            )
            for key, value in cls.to_dict().items()
        ]
        return _display.render(cls.__name__, items, fmt=chosen, grouped=True)

    def __repr__(cls) -> str:
        """
        Pretty representation of the configuration in its ``_display_format``.

        Returns:
            Formatted string produced by :meth:`render`.
        """
        return ConfigMeta.render(cls)


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

    # Default format used by print()/repr(). Override in a subclass with any of
    # configplusplus.DISPLAY_FORMATS. For a one-off format, call the
    # class-level render: MyConfig.render(fmt="table").
    _display_format: str = "boxed"

    def __repr__(self) -> str:
        """Instance-level repr uses the class pretty repr."""
        return ConfigMeta.__repr__(type(self))

    def __str__(self) -> str:
        """Instance-level str uses the class pretty repr."""
        return ConfigMeta.__repr__(type(self))
