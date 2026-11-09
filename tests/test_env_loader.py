"""
Tests for EnvConfigLoader
"""

import pathlib

import pytest

from configplusplus import EnvConfigLoader, env

pytestmark = pytest.mark.usefixtures("isolate_environ")


def test_env_string_casting(setup_env_vars):
    """Test string environment variable casting."""
    value = env("TEST_STRING")
    assert value == "hello"
    assert isinstance(value, str)


def test_env_int_casting(setup_env_vars):
    """Test integer environment variable casting."""
    value = env("TEST_INT", cast=int)
    assert value == 42
    assert isinstance(value, int)


def test_env_bool_casting_true(setup_env_vars):
    """Test boolean casting for true values."""
    value = env("TEST_BOOL_TRUE", cast=bool)
    assert value is True


def test_env_bool_casting_false(setup_env_vars):
    """Test boolean casting for false values."""
    value = env("TEST_BOOL_FALSE", cast=bool)
    assert value is False


def test_env_path_casting(setup_env_vars):
    """Test path environment variable casting."""
    value = env("TEST_PATH", cast=pathlib.Path)
    assert value == pathlib.Path("/tmp/test")
    assert isinstance(value, pathlib.Path)


def test_env_with_default():
    """Test environment variable with default value."""
    value = env("MISSING_VAR", default="default_value")
    assert value == "default_value"


def test_env_missing_required():
    """Test that missing required variable raises error."""
    with pytest.raises(RuntimeError, match="missing required env var"):
        env("MISSING_REQUIRED_VAR")


def test_env_optional():
    """Test optional environment variable."""
    value = env("MISSING_VAR", default=None, required=False)
    assert value is None


def test_env_config_loader_values(env_config_cls):
    """Test EnvConfigLoader loads values correctly."""

    assert env_config_cls.TEST_STRING == "hello"
    assert env_config_cls.TEST_INT == 42
    assert env_config_cls.TEST_BOOL is True


def test_env_config_loader_to_dict(env_config_cls):
    """Test to_dict method."""

    config_dict = env_config_cls.to_dict()

    assert "TEST_STRING" in config_dict
    assert "TEST_INT" in config_dict
    assert "TEST_BOOL" in config_dict
    assert config_dict["TEST_STRING"] == "hello"


def test_env_config_loader_get(env_config_cls):
    """Test get method."""

    assert env_config_cls.get("TEST_STRING") == "hello"
    assert env_config_cls.get("MISSING_KEY", default="fallback") == "fallback"


def test_env_config_loader_has(env_config_cls):
    """Test has method."""

    assert env_config_cls.has("TEST_STRING") is True
    assert env_config_cls.has("MISSING_KEY") is False


def test_env_config_loader_secret_masking(env_config_cls, assert_masked):
    """Test that secrets are masked in repr."""

    repr_str = repr(env_config_cls)

    # Secret should be masked
    assert_masked(repr_str, "secret123456")

    # Non-secret values should be visible
    assert "hello" in repr_str


def test_env_config_loader_repr(env_config_cls):
    """Test pretty repr output."""

    repr_str = repr(env_config_cls)

    assert "TESTCONFIG" in repr_str.upper()
    assert "TEST_STRING" in repr_str
    assert "=" in repr_str


def test_env_config_loader_validation(setup_env_vars):
    """Test custom validation."""

    class ValidatedConfig(EnvConfigLoader):
        TEST_INT = env("TEST_INT", cast=int)

        @classmethod
        def validate(cls) -> None:
            super().validate()
            if cls.TEST_INT < 0:
                raise RuntimeError("TEST_INT must be positive")

    # Should pass validation
    ValidatedConfig.validate()

    # Modify value to fail validation
    ValidatedConfig.TEST_INT = -1
    with pytest.raises(RuntimeError, match="TEST_INT must be positive"):
        ValidatedConfig.validate()


def test_bool_casting_variations(monkeypatch):
    """Test various boolean string representations."""
    test_cases = {
        "false": False,
        "False": False,
        "FALSE": False,
        "0": False,
        "no": False,
        "No": False,
        "": False,
        "true": True,
        "True": True,
        "1": True,
        "yes": True,
        "anything": True,
    }

    for string_val, expected in test_cases.items():
        monkeypatch.setenv("BOOL_TEST", string_val)
        result = env("BOOL_TEST", cast=bool)
        assert result is expected, f"Failed for '{string_val}'"
