"""
Tests for base configuration classes
"""

import pathlib
from configplusplus.base import ConfigBase


class SampleConfig(ConfigBase):
    """Sample configuration for testing."""

    DATABASE_HOST = "localhost"
    DATABASE_PORT = 5432
    API_ENDPOINT = "https://api.example.com"
    SECRET_API_KEY = "secret123456789"
    API_TIMEOUT = 30


def test_config_meta_to_dict():
    """Test ConfigMeta.to_dict method."""
    config_dict = SampleConfig.to_dict()

    assert "DATABASE_HOST" in config_dict
    assert "DATABASE_PORT" in config_dict
    assert "API_ENDPOINT" in config_dict
    assert "SECRET_API_KEY" in config_dict
    assert config_dict["DATABASE_HOST"] == "localhost"


def test_config_meta_to_dict_only_uppercase():
    """Test that to_dict only includes UPPERCASE attributes."""

    class MixedConfig(ConfigBase):
        UPPER_VALUE = "included"
        lower_value = "excluded"
        _private = "excluded"

    config_dict = MixedConfig.to_dict()

    assert "UPPER_VALUE" in config_dict
    assert "lower_value" not in config_dict
    assert "_private" not in config_dict


def test_config_meta_to_dict_no_callables():
    """Test that to_dict excludes callable attributes."""

    class CallableConfig(ConfigBase):
        VALUE = "included"

        @staticmethod
        def method():
            return "excluded"

    config_dict = CallableConfig.to_dict()

    assert "VALUE" in config_dict
    assert "method" not in config_dict


def test_config_meta_mask_if_secret():
    """Test secret masking."""
    # Test with secret keyword
    masked = SampleConfig._mask_if_secret("SECRET_API_KEY", "secret123456789")
    assert "secret123456789" not in str(masked)
    assert "hidden" in str(masked).lower()

    # Test with non-secret
    non_masked = SampleConfig._mask_if_secret("DATABASE_HOST", "localhost")
    assert non_masked == "localhost"


def test_config_meta_mask_short_secrets():
    """Test masking of short secret values."""
    masked = SampleConfig._mask_if_secret("API_KEY", "abc")
    assert masked == "***hidden***"


def test_config_meta_mask_various_keywords():
    """Test masking with various sensitive keywords."""
    sensitive_keys = [
        ("SECRET_VALUE", "test123"),
        ("API_KEY", "test123"),
        ("PASSWORD", "test123"),
        ("TOKEN", "test123"),
        ("CREDENTIAL", "test123"),
    ]

    for key, value in sensitive_keys:
        masked = SampleConfig._mask_if_secret(key, value)
        assert "test123" not in str(masked)
        assert "hidden" in str(masked).lower()


def test_config_meta_mask_none_value():
    """Test masking with None value."""
    result = SampleConfig._mask_if_secret("SECRET", None)
    assert result is None


def test_config_meta_grouped_items():
    """Test grouping of configuration items."""
    groups = SampleConfig._grouped_items()

    assert "DATABASE" in groups
    assert "API" in groups
    assert "SECRET" in groups

    # Check DATABASE group
    database_keys = [k for k, v in groups["DATABASE"]]
    assert "DATABASE_HOST" in database_keys
    assert "DATABASE_PORT" in database_keys


def test_config_meta_repr():
    """Test pretty representation."""
    repr_str = repr(SampleConfig)

    # Check structure
    assert "╔" in repr_str
    assert "╚" in repr_str
    assert "SAMPLECONFIG" in repr_str.upper()

    # Check groups
    assert "▶ DATABASE" in repr_str
    assert "▶ API" in repr_str

    # Check values
    assert "localhost" in repr_str
    assert "5432" in repr_str

    # Check secret is masked
    assert "secret123456789" not in repr_str
    assert "hidden" in repr_str.lower()


def test_config_meta_repr_with_paths():
    """Test repr with Path objects."""

    class PathConfig(ConfigBase):
        DATA_DIR = pathlib.Path("/tmp/data")

    repr_str = repr(PathConfig)

    # Path should be resolved and shown as string
    # On Windows, /tmp/data becomes C:\tmp\data
    assert "tmp" in repr_str
    assert "data" in repr_str


def test_config_base_instance_repr():
    """Test instance-level repr."""
    instance = SampleConfig()
    repr_str = repr(instance)

    # Should use class-level repr
    assert "SAMPLECONFIG" in repr_str.upper()
    assert "DATABASE" in repr_str


def test_config_base_instance_str():
    """Test instance-level str."""
    instance = SampleConfig()
    str_output = str(instance)

    # Should use class-level repr
    assert "SAMPLECONFIG" in str_output.upper()
    assert "DATABASE" in str_output


def test_config_base_str_equals_repr():
    """Test that str and repr are the same."""
    repr_output = repr(SampleConfig)
    str_output = str(SampleConfig)

    assert repr_output == str_output


def test_config_meta_empty_config():
    """Test with empty configuration."""

    class EmptyConfig(ConfigBase):
        pass

    config_dict = EmptyConfig.to_dict()
    assert len(config_dict) == 0

    repr_str = repr(EmptyConfig)
    assert "EMPTYCONFIG" in repr_str.upper()


def test_config_meta_single_item():
    """Test with single configuration item."""

    class SingleConfig(ConfigBase):
        SINGLE_VALUE = "test"

    groups = SingleConfig._grouped_items()
    assert "SINGLE" in groups
    assert len(groups["SINGLE"]) == 1


def test_config_meta_repr_deterministic():
    """Test that repr output is deterministic (sorted)."""

    class UnsortedConfig(ConfigBase):
        ZZZ_LAST = "z"
        AAA_FIRST = "a"
        MMM_MIDDLE = "m"

    repr_str = repr(UnsortedConfig)

    # Find positions of each key
    pos_aaa = repr_str.find("AAA_FIRST")
    pos_mmm = repr_str.find("MMM_MIDDLE")
    pos_zzz = repr_str.find("ZZZ_LAST")

    # Should be in alphabetical order
    assert pos_aaa < pos_mmm < pos_zzz


def test_config_meta_multiple_groups():
    """Test configuration with multiple groups."""

    class MultiGroupConfig(ConfigBase):
        DATABASE_HOST = "localhost"
        DATABASE_PORT = 5432
        API_ENDPOINT = "https://api.example.com"
        API_KEY = "key123"
        REDIS_HOST = "redis-server"
        REDIS_PORT = 6379

    groups = MultiGroupConfig._grouped_items()

    assert len(groups) == 3
    assert "DATABASE" in groups
    assert "API" in groups
    assert "REDIS" in groups

    assert len(groups["DATABASE"]) == 2
    assert len(groups["API"]) == 2
    assert len(groups["REDIS"]) == 2
