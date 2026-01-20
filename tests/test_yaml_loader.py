"""
Tests for YamlConfigLoader
"""

import pytest
import pathlib
import tempfile
import yaml
from configplusplus import YamlConfigLoader


@pytest.fixture
def sample_yaml_file():
    """Create a temporary YAML file for testing."""
    config_data = {
        "database": {"host": "localhost", "port": 5432, "name": "testdb"},
        "api": {
            "endpoint": "https://api.example.com",
            "timeout": 30,
            "secret_key": "secret123",
        },
        "features": [
            {"name": "search", "enabled": True},
            {"name": "export", "enabled": False},
        ],
        "settings": {"debug": False, "log_level": "INFO"},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    pathlib.Path(temp_path).unlink()


class SimpleYamlConfig(YamlConfigLoader):
    """Simple test configuration."""

    def __post_init__(self) -> None:
        self.database_host = self._raw_config["database"]["host"]
        self.database_port = self._raw_config["database"]["port"]
        self.api_endpoint = self._raw_config["api"]["endpoint"]
        self.debug = self._raw_config["settings"]["debug"]


def test_yaml_config_loader_init(sample_yaml_file):
    """Test YamlConfigLoader initialization."""
    config = SimpleYamlConfig(sample_yaml_file)

    assert config.config_path == pathlib.Path(sample_yaml_file)
    assert config._raw_config is not None
    assert isinstance(config._raw_config, dict)


def test_yaml_config_loader_post_init(sample_yaml_file):
    """Test __post_init__ parsing."""
    config = SimpleYamlConfig(sample_yaml_file)

    assert config.database_host == "localhost"
    assert config.database_port == 5432
    assert config.api_endpoint == "https://api.example.com"
    assert config.debug is False


def test_yaml_config_loader_file_not_found():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        SimpleYamlConfig("nonexistent.yaml")


def test_yaml_config_loader_invalid_yaml():
    """Test that invalid YAML raises error."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = f.name

    try:
        with pytest.raises(yaml.YAMLError):
            SimpleYamlConfig(temp_path)
    finally:
        pathlib.Path(temp_path).unlink()


def test_yaml_config_loader_get_method(sample_yaml_file):
    """Test get method with dot notation."""
    config = SimpleYamlConfig(sample_yaml_file)

    assert config.get("database.host") == "localhost"
    assert config.get("database.port") == 5432
    assert config.get("api.endpoint") == "https://api.example.com"
    assert config.get("settings.debug") is False


def test_yaml_config_loader_get_with_default(sample_yaml_file):
    """Test get method with default value."""
    config = SimpleYamlConfig(sample_yaml_file)

    assert config.get("missing.key", default="fallback") == "fallback"
    assert config.get("database.missing", default=None) is None


def test_yaml_config_loader_has_method(sample_yaml_file):
    """Test has method."""
    config = SimpleYamlConfig(sample_yaml_file)

    assert config.has("database.host") is True
    assert config.has("database.port") is True
    assert config.has("missing.key") is False


def test_yaml_config_loader_to_dict(sample_yaml_file):
    """Test to_dict method."""
    config = SimpleYamlConfig(sample_yaml_file)
    config_dict = config.to_dict()

    assert "database_host" in config_dict
    assert "database_port" in config_dict
    assert "api_endpoint" in config_dict
    assert "debug" in config_dict

    # Private attributes should be excluded
    assert "_raw_config" not in config_dict
    assert "logger" not in config_dict
    assert "config_path" not in config_dict


def test_yaml_config_loader_repr(sample_yaml_file):
    """Test repr output."""
    config = SimpleYamlConfig(sample_yaml_file)
    repr_str = repr(config)

    assert "SIMPLEYAMLCONFIG" in repr_str.upper()
    assert "Config Path:" in repr_str
    assert "database_host" in repr_str


def test_yaml_config_loader_secret_masking(sample_yaml_file):
    """Test secret masking in repr."""

    class SecretConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.api_secret_key = self._raw_config["api"]["secret_key"]
            self.database_password = "mypassword123"

    config = SecretConfig(sample_yaml_file)
    repr_str = repr(config)

    # Secrets should be masked
    assert "secret123" not in repr_str
    assert "mypassword123" not in repr_str
    assert "hidden" in repr_str.lower()


def test_yaml_config_loader_with_lists(sample_yaml_file):
    """Test handling of list data."""

    class ListConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.features = self._raw_config["features"]

    config = ListConfig(sample_yaml_file)

    assert len(config.features) == 2
    assert config.features[0]["name"] == "search"
    assert config.features[1]["enabled"] is False


def test_yaml_config_loader_repr_with_lists(sample_yaml_file):
    """Test repr shows list item count."""

    class ListConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.features = self._raw_config["features"]

    config = ListConfig(sample_yaml_file)
    repr_str = repr(config)

    # Should show count, not full list
    assert "[2 items]" in repr_str


def test_yaml_config_loader_with_nested_dicts(sample_yaml_file):
    """Test handling of nested dictionary data."""

    class NestedConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.database_config = self._raw_config["database"]

    config = NestedConfig(sample_yaml_file)

    assert isinstance(config.database_config, dict)
    assert config.database_config["host"] == "localhost"


def test_yaml_config_loader_repr_with_dicts(sample_yaml_file):
    """Test repr shows dict key count."""

    class DictConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.database_config = self._raw_config["database"]

    config = DictConfig(sample_yaml_file)
    repr_str = repr(config)

    # Should show count, not full dict
    assert "{3 keys}" in repr_str


def test_yaml_config_loader_path_handling(sample_yaml_file):
    """Test Path object handling."""

    class PathConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.data_dir = pathlib.Path("/tmp/data")

    config = PathConfig(sample_yaml_file)
    repr_str = repr(config)

    # Paths should be resolved
    # On Windows, /tmp/data becomes C:\tmp\data
    assert "tmp" in repr_str
    assert "data" in repr_str


def test_yaml_config_loader_empty_post_init(sample_yaml_file):
    """Test that empty __post_init__ works."""

    class EmptyConfig(YamlConfigLoader):
        pass

    config = EmptyConfig(sample_yaml_file)

    # Should have raw config but no parsed attributes
    assert config._raw_config is not None
    assert len(config.to_dict()) == 0


def test_yaml_config_loader_str_method(sample_yaml_file):
    """Test str method."""
    config = SimpleYamlConfig(sample_yaml_file)

    str_output = str(config)
    repr_output = repr(config)

    # str and repr should be the same
    assert str_output == repr_output
