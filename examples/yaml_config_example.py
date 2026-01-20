"""
Example usage of YamlConfigLoader
"""

from typing import List
from dataclasses import dataclass
from configplusplus import YamlConfigLoader


@dataclass
class FilterConfig:
    """Configuration for a single filter."""

    name: str
    type: str
    label: str
    values: List[str]
    enabled: bool = True


@dataclass
class CardFieldConfig:
    """Configuration for a card field."""

    name: str
    label: str
    type: str
    visible: bool = True


class UiConfig(YamlConfigLoader):
    """UI Configuration loaded from YAML file."""

    def __post_init__(self) -> None:
        """Parse the loaded YAML configuration."""

        # Parse application settings
        app_config = self._raw_config.get("application", {})
        self.app_name = app_config.get("name", "Unknown App")
        self.app_version = app_config.get("version", "0.0.0")
        self.debug_mode = app_config.get("debug", False)

        # Parse filters configuration
        self.filters: List[FilterConfig] = []
        for filter_data in self._raw_config.get("filters", []):
            self.filters.append(FilterConfig(**filter_data))

        # Parse card configuration
        self.card_fields: List[CardFieldConfig] = []
        for card_data in self._raw_config.get("card", []):
            self.card_fields.append(CardFieldConfig(**card_data))

        # Parse display settings
        display_config = self._raw_config.get("display", {})
        self.theme = display_config.get("theme", "light")
        self.items_per_page = display_config.get("items_per_page", 10)
        self.show_toolbar = display_config.get("show_toolbar", True)


def main() -> None:
    """Demonstrate YamlConfigLoader usage."""
    print("=" * 50)
    print("YamlConfigLoader Example")
    print("=" * 50)

    # Load configuration from YAML file
    config = UiConfig("examples/config.yaml")

    # Display the full configuration
    print(config)

    # Access parsed values
    print("\n--- Application Settings ---")
    print(f"App Name: {config.app_name}")
    print(f"App Version: {config.app_version}")
    print(f"Debug Mode: {config.debug_mode}")

    print("\n--- Display Settings ---")
    print(f"Theme: {config.theme}")
    print(f"Items Per Page: {config.items_per_page}")
    print(f"Show Toolbar: {config.show_toolbar}")

    # Access structured data
    print("\n--- Filters ---")
    for filter_config in config.filters:
        status = "✅" if filter_config.enabled else "❌"
        print(f"{status} {filter_config.label} ({filter_config.type})")
        print(f"   Values: {', '.join(filter_config.values[:3])}...")

    print("\n--- Card Fields ---")
    for field in config.card_fields:
        visibility = "👁️" if field.visible else "🚫"
        print(f"{visibility} {field.label} [{field.type}]")

    # Use helper methods
    print("\n--- Using Helper Methods ---")
    print(f"Has 'application': {config.has('application')}")
    print(f"Get theme: {config.get('display.theme')}")
    print(f"Get missing key: {config.get('missing.key', default='N/A')}")

    # Convert to dictionary
    print("\n--- Convert to Dictionary ---")
    config_dict = config.to_dict()
    print(f"Total config attributes: {len(config_dict)}")


if __name__ == "__main__":
    main()
