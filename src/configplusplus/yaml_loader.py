"""
YAML file based configuration loader
"""

from typing import Any, Dict
import pathlib
import yaml
from loggerplusplus import loggerplusplus


class YamlConfigLoader:
    """
    Base class for YAML file based configuration.
    
    This class requires instantiation with a path to a YAML file.
    The YAML file is loaded in __init__, then __post_init__ is called
    for custom parsing logic.
    
    Features:
    - Automatic YAML loading
    - Post-initialization hook for custom parsing
    - Access to raw config data
    - Pretty printing support
    
    Usage:
        from configplusplus import YamlConfigLoader
        
        class MyYamlConfig(YamlConfigLoader):
            def __post_init__(self) -> None:
                # Parse the loaded YAML data
                self.database_host = self._raw_config["database"]["host"]
                self.database_port = self._raw_config["database"]["port"]
                
                # Parse nested structures
                self.features = [
                    Feature(**feature_data)
                    for feature_data in self._raw_config["features"]
                ]
        
        # Instantiate with path
        config = MyYamlConfig("config.yaml")
        print(config.database_host)
        print(config)  # Pretty formatted output
    
    YAML File Example:
        database:
          host: localhost
          port: 5432
        
        features:
          - name: search
            enabled: true
          - name: export
            enabled: false
    
    Attributes:
        config_path: Path to the loaded YAML file
        _raw_config: Raw dictionary loaded from YAML
        logger: LoggerPlusPlus logger instance
    """

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

    def _load_yaml(self) -> Dict[str, Any]:
        """
        Load and parse the YAML configuration file.
        
        Returns:
            Dictionary containing the parsed YAML data
            
        Raises:
            yaml.YAMLError: If the YAML file is invalid
        """
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.logger.error(f"Failed to parse YAML file: {e}")
            raise

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

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary, excluding private/special attributes.
        
        Returns:
            Dictionary containing all public instance attributes
        """
        return {
            k: v
            for k, v in self.__dict__.items()
            if not k.startswith("_") and k not in ("logger", "config_path")
        }

    def _mask_if_secret(self, key: str, value: Any) -> Any:
        """
        Mask potentially sensitive values.
        
        Args:
            key: Attribute name
            value: Attribute value
            
        Returns:
            Masked value if sensitive, original value otherwise
        """
        if value is None:
            return None

        key_lower = key.lower()
        sensitive_keywords = ("secret", "api_key", "password", "token", "credential")
        
        if any(keyword in key_lower for keyword in sensitive_keywords):
            s = str(value)
            if len(s) <= 6:
                return "***hidden***"
            return f"{s[:3]}…{s[-2:]} (hidden)"
        
        return value

    def __repr__(self) -> str:
        """
        Pretty representation of the configuration.
        
        Returns:
            Formatted string with configuration display
        """
        lines = ["\n"]
        lines.append("╔════════════════════════════════════════════╗")
        lines.append(f"║  {self.__class__.__name__.upper().center(40)}  ║")
        lines.append("╚════════════════════════════════════════════╝")
        lines.append("")
        lines.append(f"▶ Config Path: {self.config_path}")
        lines.append("")

        config_dict = self.to_dict()
        if not config_dict:
            lines.append("  (No configuration loaded)")
        else:
            max_key_len = max(len(k) for k in config_dict.keys())
            
            for key in sorted(config_dict.keys()):
                value = config_dict[key]
                display_value = self._mask_if_secret(key, value)
                
                # Handle paths
                if isinstance(display_value, pathlib.Path):
                    display_value = str(display_value.resolve())
                
                # Handle lists/dicts - show count
                if isinstance(display_value, list):
                    display_value = f"[{len(display_value)} items]"
                elif isinstance(display_value, dict):
                    display_value = f"{{{len(display_value)} keys}}"
                
                lines.append(f"  {key.ljust(max_key_len)} = {display_value!r}")

        lines.append("")
        return "\n".join(lines)

    def __str__(self) -> str:
        """String representation uses the pretty repr."""
        return self.__repr__()
