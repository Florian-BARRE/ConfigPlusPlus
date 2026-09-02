"""Tests for the utils module: safe_load_envs, env and env_optional."""

import os
import pathlib

import pytest

from configplusplus import env, safe_load_envs
from configplusplus.utils import env_optional


@pytest.fixture(autouse=True)
def _isolate_environ():
    """Snapshot os.environ and restore it after each test.

    load_dotenv mutates the process environment; without this every test would
    leak variables into the next one.
    """
    saved = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(saved)


# --------------------------------------------------------------------------- #
# safe_load_envs
# --------------------------------------------------------------------------- #


def test_default_loads_dotenv_in_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("SLE_DEFAULT=1\n")

    assert safe_load_envs(verbose=False) is True
    assert os.environ["SLE_DEFAULT"] == "1"


def test_default_returns_false_when_no_dotenv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert safe_load_envs(verbose=False) is False


def test_explicit_dotenv_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SLE_EXPLICIT=2\n")

    assert safe_load_envs(env_file, verbose=False) is True
    assert os.environ["SLE_EXPLICIT"] == "2"


def test_nested_dotenv_file(tmp_path):
    nested = tmp_path / "config" / ".env"
    nested.parent.mkdir()
    nested.write_text("SLE_NESTED=3\n")

    assert safe_load_envs(nested, verbose=False) is True
    assert os.environ["SLE_NESTED"] == "3"


def test_pathlib_input(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SLE_PATHLIB=4\n")

    assert safe_load_envs(pathlib.Path(env_file), verbose=False) is True
    assert os.environ["SLE_PATHLIB"] == "4"


def test_named_env_file(tmp_path):
    env_file = tmp_path / "dev.env"
    env_file.write_text("SLE_NAMED=5\n")

    assert safe_load_envs(env_file, verbose=False) is True
    assert os.environ["SLE_NAMED"] == "5"


def test_directory_globs_all_env_files(tmp_path):
    (tmp_path / ".env").write_text("SLE_A=a\n")
    (tmp_path / "dev.env").write_text("SLE_B=b\n")
    (tmp_path / "prod.env").write_text("SLE_C=c\n")

    assert safe_load_envs(tmp_path, verbose=False) is True
    assert os.environ["SLE_A"] == "a"
    assert os.environ["SLE_B"] == "b"
    assert os.environ["SLE_C"] == "c"


def test_missing_path_returns_false(tmp_path):
    assert safe_load_envs(tmp_path / "does_not_exist.env", verbose=False) is False


def test_non_env_file_returns_false(tmp_path):
    other = tmp_path / "config.yaml"
    other.write_text("key: value\n")
    assert safe_load_envs(other, verbose=False) is False


def test_verbose_false_is_silent(tmp_path, capsys):
    (tmp_path / ".env").write_text("SLE_SILENT=1\n")
    safe_load_envs(tmp_path / ".env", verbose=False)
    assert capsys.readouterr().out == ""


def test_verbose_true_logs_and_leaves_no_sink(tmp_path, capsys):
    (tmp_path / ".env").write_text("SLE_VERBOSE=1\n")

    assert safe_load_envs(tmp_path / ".env", verbose=True) is True
    first = capsys.readouterr().out
    assert first != ""

    # A leaked sink would keep emitting; a silent call after a verbose one must
    # produce no output.
    safe_load_envs(tmp_path / ".env", verbose=False)
    assert capsys.readouterr().out == ""


# --------------------------------------------------------------------------- #
# env
# --------------------------------------------------------------------------- #


def test_env_required_missing_raises(monkeypatch):
    monkeypatch.delenv("ENV_ABSENT", raising=False)
    with pytest.raises(RuntimeError, match="ENV_ABSENT"):
        env("ENV_ABSENT")


def test_env_returns_default_when_absent(monkeypatch):
    monkeypatch.delenv("ENV_WITH_DEFAULT", raising=False)
    assert env("ENV_WITH_DEFAULT", default="fallback") == "fallback"


def test_env_optional_missing_returns_none(monkeypatch):
    monkeypatch.delenv("ENV_MISSING", raising=False)
    assert env("ENV_MISSING", required=False) is None


def test_env_cast_int(monkeypatch):
    monkeypatch.setenv("ENV_PORT", "5432")
    assert env("ENV_PORT", cast=int) == 5432


@pytest.mark.parametrize("raw", ["false", "False", "FALSE", "0", "no", "No", "NO", ""])
def test_env_cast_bool_falsey(monkeypatch, raw):
    monkeypatch.setenv("ENV_FLAG", raw)
    assert env("ENV_FLAG", cast=bool) is False


@pytest.mark.parametrize("raw", ["true", "True", "1", "yes", "anything"])
def test_env_cast_bool_truthy(monkeypatch, raw):
    monkeypatch.setenv("ENV_FLAG", raw)
    assert env("ENV_FLAG", cast=bool) is True


# --------------------------------------------------------------------------- #
# env_optional
# --------------------------------------------------------------------------- #


def test_env_optional_returns_default_when_unset(monkeypatch):
    monkeypatch.delenv("OPT_FEATURE", raising=False)
    assert env_optional("OPT_FEATURE", default=False, cast=bool) is False


def test_env_optional_casts_when_set(monkeypatch):
    monkeypatch.setenv("OPT_TIMEOUT", "30")
    assert env_optional("OPT_TIMEOUT", cast=int) == 30
