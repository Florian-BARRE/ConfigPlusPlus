"""
Characterization net for the ENV PARSING boundary (refactoring campaign, phase 3).

These tests pin the CURRENT behaviour of the env helpers — ``env``,
``env_optional``, ``env_list`` and ``safe_load_envs`` — through their public
surface only, with real assertions on the EXACT returned values and EXACT error /
log message strings (no partial ``match=`` on the goldens). They exist so the
later structural move (``utils.py`` -> ``env.py`` + ``ConfigDisplayMixin``) is
provably behaviour-preserving: after the move, this net must stay green
unchanged.

Self-contained: fixtures come from ``monkeypatch`` and ``tmp_path`` only — no
``conftest``, no shared state. Deterministic and leak-free.
"""

import os
import pathlib

import pytest

from configplusplus import env, env_list, env_optional, safe_load_envs

# --------------------------------------------------------------------------- #
# A. Exact-text error messages (the 4 goldens)
# --------------------------------------------------------------------------- #


def test_env_missing_required_message(monkeypatch):
    """A required variable that is absent raises RuntimeError naming the key."""
    monkeypatch.delenv("CPLT_MISSING", raising=False)
    with pytest.raises(RuntimeError) as exc:
        env("CPLT_MISSING")
    assert str(exc.value) == "missing required env var CPLT_MISSING"


def test_env_bad_cast_message_hides_raw_value(monkeypatch):
    """A value that fails to cast raises RuntimeError naming the var and type only.

    # BUG-01 (fixed): the message no longer embeds the raw value, which used to
    # surface a sensitive var in clear. The golden now pins the safe text; the
    # value is asserted absent (not shown).
    """
    monkeypatch.setenv("CPLT_BADINT", "notanint")
    with pytest.raises(RuntimeError) as exc:
        env("CPLT_BADINT", cast=int)
    assert str(exc.value) == "env var CPLT_BADINT could not be cast with int"
    # BUG-01: the raw value must NOT appear in the message.
    assert "notanint" not in str(exc.value)


def test_env_list_missing_required_message(monkeypatch):
    """A required list variable that is absent raises RuntimeError naming the key."""
    monkeypatch.delenv("CPLT_LIST_MISSING", raising=False)
    with pytest.raises(RuntimeError) as exc:
        env_list("CPLT_LIST_MISSING")
    assert str(exc.value) == "missing required env var CPLT_LIST_MISSING"


def test_env_list_bad_item_cast_message(monkeypatch):
    """An item that fails to cast raises RuntimeError naming the key and the item."""
    monkeypatch.setenv("CPLT_BADITEM", "80,nope")
    with pytest.raises(RuntimeError) as exc:
        env_list("CPLT_BADITEM", cast=int)
    assert str(exc.value) == (
        "env var CPLT_BADITEM item 'nope' could not be cast with int: "
        "invalid literal for int() with base 10: 'nope'"
    )


# --------------------------------------------------------------------------- #
# B. Type coercion
# --------------------------------------------------------------------------- #


def test_env_cast_int(monkeypatch):
    monkeypatch.setenv("CPLT_INT", "42")
    assert env("CPLT_INT", cast=int) == 42


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("0", False),
        ("no", False),
        ("No", False),
        ("NO", False),
        ("", False),
        # surrounding whitespace is stripped before the membership test
        (" false ", False),
        ("FALSE ", False),
    ],
)
def test_env_cast_bool_falsey(monkeypatch, raw, expected):
    monkeypatch.setenv("CPLT_BOOL", raw)
    assert env("CPLT_BOOL", cast=bool) is expected


@pytest.mark.parametrize(
    "raw",
    ["true", "True", "TRUE", "1", "yes", "Yes", "YES", "anything"],
)
def test_env_cast_bool_truthy(monkeypatch, raw):
    monkeypatch.setenv("CPLT_BOOL", raw)
    assert env("CPLT_BOOL", cast=bool) is True


def test_env_cast_float(monkeypatch):
    monkeypatch.setenv("CPLT_FLOAT", "3.14")
    assert env("CPLT_FLOAT", cast=float) == 3.14


def test_env_cast_path(monkeypatch):
    monkeypatch.setenv("CPLT_PATH", "/tmp/foo")
    value = env("CPLT_PATH", cast=pathlib.Path)
    assert value == pathlib.Path("/tmp/foo")
    assert isinstance(value, pathlib.Path)


def test_env_default_cast_is_str(monkeypatch):
    monkeypatch.setenv("CPLT_STR", "hello")
    value = env("CPLT_STR")  # cast defaults to str
    assert value == "hello"
    assert isinstance(value, str)


def test_env_set_var_wins_over_default(monkeypatch):
    """When the variable is set, the set value wins over ``default``."""
    monkeypatch.setenv("CPLT_WIN", "real")
    assert env("CPLT_WIN", default="fallback") == "real"


def test_env_default_returned_when_var_missing(monkeypatch):
    """When the variable is absent, ``default`` is returned as-is (not re-cast)."""
    monkeypatch.delenv("CPLT_DEFCAST", raising=False)
    assert env("CPLT_DEFCAST", default=7, cast=int) == 7


def test_env_optional_unset_no_default_is_none(monkeypatch):
    monkeypatch.delenv("CPLT_OPT", raising=False)
    assert env_optional("CPLT_OPT") is None


def test_env_optional_unset_returns_default(monkeypatch):
    monkeypatch.delenv("CPLT_OPT", raising=False)
    assert env_optional("CPLT_OPT", default="fb") == "fb"


def test_env_optional_unset_default_is_cast(monkeypatch):
    """A castable string default is cast when the variable is absent."""
    monkeypatch.delenv("CPLT_OPT", raising=False)
    assert env_optional("CPLT_OPT", default="30", cast=int) == 30


def test_env_optional_set_and_cast(monkeypatch):
    monkeypatch.setenv("CPLT_OPT", "30")
    assert env_optional("CPLT_OPT", cast=int) == 30


def test_env_optional_bad_cast_message(monkeypatch):
    """env_optional reuses env's bad-cast message verbatim.

    # BUG-01 (fixed): env_optional shares env's cast path, so its message is
    # re-pinned to the safe text (var name + expected type, no raw value).
    """
    monkeypatch.setenv("CPLT_OBTC", "notanint")
    with pytest.raises(RuntimeError) as exc:
        env_optional("CPLT_OBTC", cast=int)
    assert str(exc.value) == "env var CPLT_OBTC could not be cast with int"
    # BUG-01: the raw value must NOT appear in the message.
    assert "notanint" not in str(exc.value)


# --------------------------------------------------------------------------- #
# C. env_list
# --------------------------------------------------------------------------- #


def test_env_list_split_and_strip(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "a, b ,c")
    assert env_list("CPLT_LIST") == ["a", "b", "c"]


def test_env_list_drops_empty_items(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "a,,b,,c,")
    assert env_list("CPLT_LIST") == ["a", "b", "c"]


def test_env_list_cast_int(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "80, 443")
    assert env_list("CPLT_LIST", cast=int) == [80, 443]


def test_env_list_custom_separator(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "/a:/b:/c")
    assert env_list("CPLT_LIST", sep=":") == ["/a", "/b", "/c"]


def test_env_list_empty_string_is_empty(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "")
    assert env_list("CPLT_LIST") == []


def test_env_list_whitespace_only_is_empty(monkeypatch):
    monkeypatch.setenv("CPLT_LIST", "   ")
    assert env_list("CPLT_LIST") == []


def test_env_list_unset_optional_no_default_is_empty(monkeypatch):
    monkeypatch.delenv("CPLT_LMISS", raising=False)
    assert env_list("CPLT_LMISS", required=False) == []


def test_env_list_unset_returns_default(monkeypatch):
    monkeypatch.delenv("CPLT_LMISS", raising=False)
    assert env_list("CPLT_LMISS", required=False, default=["x", "y"]) == ["x", "y"]


def test_env_list_default_wins_even_when_required(monkeypatch):
    """A provided ``default`` is returned even when ``required=True``."""
    monkeypatch.delenv("CPLT_LMISS", raising=False)
    assert env_list("CPLT_LMISS", required=True, default=["x"]) == ["x"]


# --------------------------------------------------------------------------- #
# D. safe_load_envs
# --------------------------------------------------------------------------- #


def test_safe_load_envs_default_cwd_env(tmp_path, monkeypatch):
    """Default path is ``.env`` resolved against the current directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("SLE_DEFAULT=1\n")
    assert safe_load_envs(verbose=False) is True
    assert os.environ.get("SLE_DEFAULT") == "1"


def test_safe_load_envs_missing_default_cwd_is_false(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert safe_load_envs(verbose=False) is False


def test_safe_load_envs_explicit_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("SLE_EXPLICIT=2\n")
    assert safe_load_envs(env_file, verbose=False) is True
    assert os.environ.get("SLE_EXPLICIT") == "2"


def test_safe_load_envs_named_env_file(tmp_path):
    env_file = tmp_path / "dev.env"
    env_file.write_text("SLE_NAMED=5\n")
    assert safe_load_envs(env_file, verbose=False) is True
    assert os.environ.get("SLE_NAMED") == "5"


def test_safe_load_envs_directory_globs_all_env(tmp_path):
    (tmp_path / ".env").write_text("SLE_A=a\n")
    (tmp_path / "dev.env").write_text("SLE_B=b\n")
    (tmp_path / "prod.env").write_text("SLE_C=c\n")
    assert safe_load_envs(tmp_path, verbose=False) is True
    assert os.environ.get("SLE_A") == "a"
    assert os.environ.get("SLE_B") == "b"
    assert os.environ.get("SLE_C") == "c"


def test_safe_load_envs_non_env_path_is_false(tmp_path):
    other = tmp_path / "config.yaml"
    other.write_text("key: value\n")
    assert safe_load_envs(other, verbose=False) is False


def test_safe_load_envs_missing_path_is_false(tmp_path):
    assert safe_load_envs(tmp_path / "does_not_exist.env", verbose=False) is False


def test_safe_load_envs_verbose_false_is_silent(tmp_path, capsys):
    (tmp_path / ".env").write_text("SLE_SILENT=1\n")
    assert safe_load_envs(tmp_path / ".env", verbose=False) is True
    assert capsys.readouterr().out == ""


def test_safe_load_envs_verbose_no_files_message(tmp_path, capsys):
    """The no-files branch logs the exact 'No *.env files' warning and returns False."""
    assert safe_load_envs(tmp_path / "missing.env", verbose=True) is False
    out = capsys.readouterr().out
    assert f"ℹ️ No *.env files found at path: {tmp_path / 'missing.env'}\n" in out


def test_safe_load_envs_verbose_failed_load_message(tmp_path, capsys):
    """A matching but empty .env yields the exact 'Failed to load' warning."""
    (tmp_path / "empty.env").write_text("")
    assert safe_load_envs(tmp_path / "empty.env", verbose=True) is False
    out = capsys.readouterr().out
    assert f"⚠️ Failed to load environment file: {tmp_path / 'empty.env'}\n" in out


def test_safe_load_envs_verbose_leaves_no_sink(tmp_path, capsys):
    """A verbose call removes its own sink: a following verbose call still works,
    and a silent call after it produces no output."""
    (tmp_path / ".env").write_text("SLE_LEAK=1\n")

    assert safe_load_envs(tmp_path / ".env", verbose=True) is True
    first = capsys.readouterr().out
    assert "✅ Loaded environment file:" in first

    # A leaked sink would double-emit on the next verbose call.
    assert safe_load_envs(tmp_path / ".env", verbose=True) is True
    second = capsys.readouterr().out
    assert second.count("Loaded environment file") == 1

    # A silent call after a verbose one must produce no output.
    safe_load_envs(tmp_path / ".env", verbose=False)
    assert capsys.readouterr().out == ""
