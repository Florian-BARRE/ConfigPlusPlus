"""Shared fixtures and helpers for the unit tests.

Only the repeated SETUP lives here (environment isolation, config-class
factories, the sample YAML file, two small assertion/loop helpers). Every test
keeps its own assertions.

Nothing here is ``autouse``: ``tests/characterization/`` is a frozen,
conftest-free safety net and must not be affected by this module. Isolation is
applied per file with ``pytestmark = pytest.mark.usefixtures("isolate_environ")``.

Helpers are exposed as fixtures returning a callable (the canonical pytest
pattern), so test modules never import from this file.
"""

import os
import pathlib
from collections.abc import Callable, Iterable, Iterator
from typing import Any

import pytest
import yaml

from configplusplus import EnvConfigLoader, YamlConfigLoader, _display, env

# --------------------------------------------------------------------------- #
# Environment
# --------------------------------------------------------------------------- #


@pytest.fixture
def isolate_environ() -> Iterator[None]:
    """Snapshot os.environ and restore it after each test.

    load_dotenv mutates the process environment; without this every test would
    leak variables into the next one.
    """
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


@pytest.fixture
def setup_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the test environment variables (undone by monkeypatch)."""
    monkeypatch.setenv("TEST_STRING", "hello")
    monkeypatch.setenv("TEST_INT", "42")
    monkeypatch.setenv("TEST_BOOL_TRUE", "true")
    monkeypatch.setenv("TEST_BOOL_FALSE", "false")
    monkeypatch.setenv("TEST_PATH", "/tmp/test")
    monkeypatch.setenv("SECRET_TEST_KEY", "secret123456")


@pytest.fixture
def env_config_cls(setup_env_vars: None) -> type[EnvConfigLoader]:
    """An EnvConfigLoader class reading the variables of ``setup_env_vars``.

    The class body calls ``env(...)`` when it is created, so it is built here,
    after the variables are set. It is named ``TestConfig`` on purpose: the repr
    test reads the class name.
    """

    class TestConfig(EnvConfigLoader):
        """Test configuration class."""

        TEST_STRING = env("TEST_STRING")
        TEST_INT = env("TEST_INT", cast=int)
        TEST_BOOL = env("TEST_BOOL_TRUE", cast=bool)
        SECRET_KEY = env("SECRET_TEST_KEY")

    return TestConfig


# --------------------------------------------------------------------------- #
# YAML
# --------------------------------------------------------------------------- #


@pytest.fixture
def sample_yaml_file(tmp_path: pathlib.Path) -> str:
    """Create a temporary YAML file for testing and return its path as a str."""
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

    path = tmp_path / "sample.yaml"
    path.write_text(yaml.dump(config_data))
    return str(path)


@pytest.fixture
def features_config_cls() -> type[YamlConfigLoader]:
    """A YamlConfigLoader class exposing the sample file's ``features`` list."""

    class ListConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.features = self._raw_config["features"]

    return ListConfig


@pytest.fixture
def database_config_cls() -> type[YamlConfigLoader]:
    """A YamlConfigLoader class exposing the sample file's ``database`` dict."""

    class NestedConfig(YamlConfigLoader):
        def __post_init__(self) -> None:
            self.database_config = self._raw_config["database"]

    return NestedConfig


# --------------------------------------------------------------------------- #
# Helpers (fixtures returning a callable)
# --------------------------------------------------------------------------- #


@pytest.fixture
def assert_masked() -> Callable[..., None]:
    """Return a helper asserting no secret leaks and the mask marker shows."""

    def _assert_masked(text: str, *secrets: str) -> None:
        for secret in secrets:
            assert secret not in text
        assert "hidden" in text.lower()

    return _assert_masked


@pytest.fixture
def render_each_format() -> Callable[..., Iterator[tuple[str, str]]]:
    """Return a helper yielding ``(fmt, obj.render(fmt=fmt))`` per format.

    Defaults to every advertised format; pass ``formats`` for a subset.
    """

    def _render_each_format(
        obj: Any, formats: Iterable[str] | None = None
    ) -> Iterator[tuple[str, str]]:
        for fmt in formats if formats is not None else _display.DISPLAY_FORMATS:
            yield fmt, obj.render(fmt=fmt)

    return _render_each_format
