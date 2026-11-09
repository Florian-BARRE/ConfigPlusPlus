"""
Base classes for configuration management with beautiful display
"""

from typing import Any

from configplusplus._display import (
    DEFAULT_SENSITIVE_KEYWORDS,
    ConfigDisplayMixin,
    _group_by_prefix,
)


class ConfigMeta(ConfigDisplayMixin, type):
    """
    Metaclass to provide pretty printing and helpers on configuration classes.

    Automatically adds:
    - to_dict(): Convert config to dictionary
    - Pretty __repr__ with grouped display
    - Secret masking for sensitive values
    """

    def _collect_items(cls) -> dict[str, Any]:
        """
        Return all UPPERCASE, non-callable attributes as a dict.

        Attributes are collected across the whole MRO, so a config subclass
        inherits the UPPERCASE fields of its parents (a child value overrides
        a parent value of the same name).
        """
        result: dict[str, Any] = {}
        for klass in reversed(cls.__mro__):
            for k, v in vars(klass).items():
                if k.isupper() and not k.startswith("_") and not callable(v):
                    result[k] = v
        return result

    def _display_title(cls) -> str:
        """Config name shown in the header: the class name."""
        return cls.__name__

    def _display_layout(cls) -> dict[str, Any]:
        """Group the ``boxed`` rows by the prefix before the first underscore."""
        return {"grouped": True}

    def _grouped_items(cls) -> dict[str, list]:
        """
        Group configuration items by prefix before first underscore.

        Example:
            QDRANT_URL and QDRANT_PORT -> grouped under "QDRANT"

        Returns:
            Dictionary mapping prefixes to list of (key, value) tuples
        """
        return _group_by_prefix(list(cls.to_dict().items()))


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
    _sensitive_keywords: tuple[str, ...] = DEFAULT_SENSITIVE_KEYWORDS

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
