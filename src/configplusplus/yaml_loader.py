"""
YAML file based configuration loader
"""

import pathlib
from typing import Any

import yaml
from loggerplusplus import loggerplusplus

from configplusplus import _display


def _collapse_container(value: Any) -> Any:
    """Summarise list/dict values as ``[N items]`` / ``{N keys}`` for display."""
    if isinstance(value, list):
        return f"[{len(value)} items]"
    if isinstance(value, dict):
        return f"{{{len(value)} keys}}"
    return value


class YamlConfigLoader:
    """
    Base class for YAML file based configuration.

    Instantiated with a path: the file is loaded in ``__init__``, then
    ``__post_init__`` runs for custom parsing. Supports dot-notation access
    (``get``/``has``), ``to_dict(mask=...)`` and multi-format display via
    ``render``. See ``examples/yaml_config_example.py`` for a full example.

    Attributes:
        config_path: Path to the loaded YAML file.
        _raw_config: Raw dictionary loaded from YAML.
        logger: LoggerPlusPlus logger instance.
    """

    # Sensitive-keyword set used by the display/masking layer. Extend it in a
    # subclass (never narrow it); masking is a safety feature.
    _sensitive_keywords: tuple[str, ...] = _display.DEFAULT_SENSITIVE_KEYWORDS

    # Default format used by print()/repr(). Override in a subclass with any of
    # configplusplus.DISPLAY_FORMATS, or pass fmt= to render() one-off.
    _display_format: str = "boxed"

    def __init__(self, config_path: str | pathlib.Path) -> None:
        """
        Initialize the YAML config loader.

        Args:
            config_path: Path to the YAML configuration file

        Raises:
            FileNotFoundError: If the configuration file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
        """
        # Setup logger
        self.logger = loggerplusplus.bind(identifier=self.__class__.__name__)

        # Convert to Path object
        self.config_path = pathlib.Path(config_path)

        # Validate file exists
        if not self.config_path.exists():
            msg = f"Configuration file not found: {self.config_path}"
            self.logger.error(msg)
            raise FileNotFoundError(msg)

        # Load the YAML file
        self._raw_config = self._load_yaml()
        self.logger.debug(f"Loaded configuration from: {self.config_path}")

        # Call the post-init hook for custom parsing
        self.__post_init__()

    def _load_yaml(self) -> dict[str, Any]:
        """
        Load and parse the YAML configuration file.

        Returns:
            Dictionary containing the parsed YAML data

        Raises:
            yaml.YAMLError: If the YAML file is invalid
        """
        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML file: {e}")
            raise

        # An empty file parses to None; treat it as an empty config.
        if data is None:
            return {}
        if not isinstance(data, dict):
            msg = (
                f"Top-level YAML must be a mapping, got {type(data).__name__}: "
                f"{self.config_path}"
            )
            self.logger.error(msg)
            raise TypeError(msg)
        return data

    def __post_init__(self) -> None:
        """
        Hook called after YAML file is loaded.

        Override this method in subclasses to parse the loaded _raw_config
        and set instance attributes.

        Example:
            def __post_init__(self) -> None:
                self.database = DatabaseConfig(**self._raw_config["database"])
                self.features = [
                    Feature(**f) for f in self._raw_config["features"]
                ]
        """
        pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the raw config using dot notation.

        Args:
            key: Key in dot notation (e.g., "database.host")
            default: Default value if key not found

        Returns:
            Value from config or default

        Example:
            >>> config.get("database.host")
            "localhost"

            >>> config.get("missing.key", default="fallback")
            "fallback"
        """
        keys = key.split(".")
        value = self._raw_config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the raw config using dot notation.

        Args:
            key: Key in dot notation (e.g., "database.host")

        Returns:
            True if key exists, False otherwise

        Example:
            >>> config.has("database.host")
            True

            >>> config.has("missing.key")
            False
        """
        keys = key.split(".")
        value = self._raw_config

        try:
            for k in keys:
                value = value[k]
            return True
        except (KeyError, TypeError):
            return False

    def to_dict(self, *, mask: bool = False) -> dict[str, Any]:
        """
        Convert config to dictionary, excluding private/special attributes.

        Args:
            mask: When True, sensitive values are masked (safe to log). When
                False (default), raw values are returned.

        Returns:
            Dictionary containing all public instance attributes
        """
        result = {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k not in ("logger", "config_path")
        }
        if mask:
            result = {k: self._mask_if_secret(k, v) for k, v in result.items()}
        return result

    def _mask_if_secret(self, key: str, value: Any) -> Any:
        """
        Mask potentially sensitive values.

        Args:
            key: Attribute name
            value: Attribute value

        Returns:
            Masked value if sensitive, original value otherwise
        """
        return _display.mask_if_secret(key, value, self._sensitive_keywords)

    def render(self, *, fmt: str | None = None, mask: bool = True) -> str:
        """
        Render the configuration as a string in the requested format.

        Parsed list/dict attributes are collapsed to ``[N items]`` / ``{N keys}``
        (the YAML loader holds arbitrary parsed objects, not flat scalars). Every
        format — ``json``/``dotenv`` included — is a masked display rendering, not
        a re-loadable export of the raw file.

        Args:
            fmt: One of ``configplusplus.DISPLAY_FORMATS``
                (``"boxed"``, ``"table"``, ``"json"``, ``"dotenv"``, ``"flat"``).
                Defaults to the instance ``_display_format`` (``"boxed"``).
            mask: When True (default), sensitive values are masked — keep it True
                for anything that may be logged. Pass False only for a raw dump.

        Returns:
            The formatted configuration string.

        Raises:
            ValueError: If ``fmt`` is not a known display format.
        """
        chosen = fmt if fmt is not None else self._display_format
        items = [
            (
                key,
                _collapse_container(
                    _display.format_value(
                        self._mask_if_secret(key, value) if mask else value
                    )
                ),
            )
            for key, value in self.to_dict().items()
        ]
        return _display.render(
            self.__class__.__name__,
            items,
            fmt=chosen,
            subtitle=f"Config Path: {self.config_path}",
            grouped=False,
            empty_marker="(No configuration loaded)",
        )

    def __repr__(self) -> str:
        """Pretty representation of the configuration in its ``_display_format``."""
        return self.render()

    def __str__(self) -> str:
        """String representation uses the pretty repr."""
        return self.render()
