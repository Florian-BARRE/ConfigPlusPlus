"""
Characterization net for the YAML LOADING boundary of ``YamlConfigLoader``.

Phase 3 of the refactoring campaign: pin the *current* behaviour (the code as it
is today, not an ideal) so the later structural move of the display/masking code
into ``ConfigDisplayMixin`` is provably behaviour-preserving.

Self-contained: no conftest, no shared fixtures, no edits to other test files.
Every golden string was captured by driving the real loader (``python -c``
against a temp YAML), so each assertion matches what the code does TODAY.

Only the public/observed surface of ``YamlConfigLoader`` is exercised. The one
deliberate exception is the Stockstream private-member surface (``__post_init__``,
``_raw_config``, dotted ``get``) which is pinned on purpose.
"""

import pathlib

import pytest
import yaml

from configplusplus import YamlConfigLoader


def _write(tmp_path: pathlib.Path, name: str, text: str) -> pathlib.Path:
    """Write ``text`` to ``tmp_path/name`` and return its path."""
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# A. Exact-text errors
# ---------------------------------------------------------------------------


def test_file_not_found_full_message(tmp_path):
    """A missing file raises FileNotFoundError with the exact path message."""
    missing = tmp_path / "nope.yaml"
    with pytest.raises(FileNotFoundError) as exc:
        YamlConfigLoader(missing)
    assert str(exc.value) == f"Configuration file not found: {missing}"


def test_invalid_yaml_raises_yaml_error(tmp_path):
    """Unparseable YAML propagates yaml.YAMLError, naming the file."""
    p = _write(tmp_path, "bad.yaml", "a: 1\nb: [unterminated\n")
    with pytest.raises(yaml.YAMLError) as exc:
        YamlConfigLoader(p)
    assert str(p) in str(exc.value)


def test_non_mapping_toplevel_full_message(tmp_path):
    """A non-mapping top level raises TypeError with the exact type+path."""
    p = _write(tmp_path, "list.yaml", "- a\n- b\n")
    with pytest.raises(TypeError) as exc:
        YamlConfigLoader(p)
    assert str(exc.value) == f"Top-level YAML must be a mapping, got list: {p}"


def test_empty_file_is_empty_config(tmp_path):
    """An empty file parses to an empty config; get() returns its default."""
    p = _write(tmp_path, "empty.yaml", "")
    c = YamlConfigLoader(p)
    assert c._raw_config == {}
    assert c.get("anything", default="dflt") == "dflt"


# ---------------------------------------------------------------------------
# B. Dot-notation access (get / has)
# ---------------------------------------------------------------------------


def test_get_nested_path(tmp_path):
    """get() resolves a dotted path through nested mappings."""
    p = _write(tmp_path, "c.yaml", "database:\n  host: localhost\n  port: 5432\n")
    c = YamlConfigLoader(p)
    assert c.get("database.host") == "localhost"
    assert c.get("database.port") == 5432


def test_get_missing_key_returns_default(tmp_path):
    """get() on a missing key returns the default (or None without one)."""
    p = _write(tmp_path, "c.yaml", "database:\n  host: localhost\n")
    c = YamlConfigLoader(p)
    assert c.get("database.missing", default="fallback") == "fallback"
    assert c.get("top.missing", default=123) == 123
    assert c.get("top.missing") is None


def test_get_type_mismatch_returns_default(tmp_path):
    """get() descends into a scalar (TypeError) and returns the default."""
    p = _write(tmp_path, "c.yaml", "host: localhost\n")
    c = YamlConfigLoader(p)
    assert c.get("host.field", default="d") == "d"


def test_has_true_and_false(tmp_path):
    """has() is True for a resolvable path, False for a missing one."""
    p = _write(tmp_path, "c.yaml", "database:\n  host: localhost\n")
    c = YamlConfigLoader(p)
    assert c.has("database.host") is True
    assert c.has("database.missing") is False


def test_has_type_mismatch_is_false(tmp_path):
    """has() descends into a scalar (TypeError) and returns False."""
    p = _write(tmp_path, "c.yaml", "host: localhost\n")
    c = YamlConfigLoader(p)
    assert c.has("host.field") is False


# ---------------------------------------------------------------------------
# C. to_dict()
# ---------------------------------------------------------------------------


class _AttrConfig(YamlConfigLoader):
    """Loader exposing a fixed set of public attributes in __post_init__."""

    def __post_init__(self) -> None:
        self.api_key = "a-very-secret-value"
        self.short_secret = "abc"
        self.db_password = None
        self.host = "localhost"


def test_to_dict_excludes_private_and_special(tmp_path):
    """to_dict() keeps only public attributes, not _raw_config/logger/path."""
    c = _AttrConfig(_write(tmp_path, "c.yaml", "k: v\n"))
    d = c.to_dict()
    assert "_raw_config" not in d
    assert "logger" not in d
    assert "config_path" not in d
    assert d == {
        "api_key": "a-very-secret-value",
        "short_secret": "abc",
        "db_password": None,
        "host": "localhost",
    }


def test_to_dict_mask_masks_sensitive(tmp_path):
    """to_dict(mask=True) masks sensitive keys; the raw form keeps them clear."""
    c = _AttrConfig(_write(tmp_path, "c.yaml", "k: v\n"))
    assert c.to_dict(mask=True) == {
        "api_key": "a-v…ue (hidden)",
        "short_secret": "***hidden***",
        "db_password": None,
        "host": "localhost",
    }
    assert c.to_dict()["api_key"] == "a-very-secret-value"


# ---------------------------------------------------------------------------
# D. Display / masking (repr)
# ---------------------------------------------------------------------------


class _DisplayConfig(YamlConfigLoader):
    """Loader exposing the values the display rows pin."""

    def __post_init__(self) -> None:
        self.api_key = "a-very-secret-value"
        self.short_secret = "abc"
        self.db_password = None
        self.host = "localhost"
        self.items_list = [1, 2, 3]
        self.items_dict = {"a": 1, "b": 2}


def _display_repr(tmp_path: pathlib.Path) -> str:
    return repr(_DisplayConfig(_write(tmp_path, "c.yaml", "k: v\n")))


def test_repr_shows_class_name_and_config_path(tmp_path):
    """The repr shows the (upper-cased) class name and the Config Path."""
    p = _write(tmp_path, "c.yaml", "k: v\n")
    r = repr(_DisplayConfig(p))
    assert "DISPLAYCONFIG" in r
    assert f"Config Path: {p}" in r


def test_repr_collapses_list_and_dict(tmp_path):
    """Container values collapse to the exact '[N items]' / '{N keys}' rows."""
    r = _display_repr(tmp_path)
    assert "  items_list   = '[3 items]'" in r
    assert "  items_dict   = '{2 keys}'" in r


def test_repr_masks_short_secret(tmp_path):
    """A short sensitive value (<= 6 chars) renders as the exact hidden marker."""
    r = _display_repr(tmp_path)
    assert "short_secret = '***hidden***'" in r


def test_repr_masks_long_secret(tmp_path):
    """A long sensitive value keeps only its edges: first3…last2 (hidden)."""
    r = _display_repr(tmp_path)
    assert "api_key      = 'a-v…ue (hidden)'" in r


def test_repr_none_sensitive_is_none(tmp_path):
    """A None-valued sensitive attribute renders as None (not the marker)."""
    r = _display_repr(tmp_path)
    assert "db_password  = None" in r


def test_empty_config_repr_marker(tmp_path):
    """An empty config renders the exact 'No configuration loaded' marker."""
    r = repr(YamlConfigLoader(_write(tmp_path, "empty.yaml", "")))
    assert "(No configuration loaded)" in r


# ---------------------------------------------------------------------------
# E. The Stockstream private-member surface
#    (frozen even though private: a real consumer relies on these.)
# ---------------------------------------------------------------------------


class _StockstreamStyleConfig(YamlConfigLoader):
    # frozen private surface: consumed by Stockstream (see docs/architecture.md)
    def __post_init__(self) -> None:
        # (1) proves the hook runs during __init__
        self.post_init_called = True
        # (2) reads the parsed dict straight from the private member
        self.leaf = self._raw_config["nested"]["deep"]["leaf"]
        # (3) reaches the same value through dotted get()
        self.dotted = self.get("nested.deep.leaf")


def test_post_init_is_called_during_init(tmp_path):
    """Overriding __post_init__ makes it run as part of construction."""
    c = _StockstreamStyleConfig(
        _write(tmp_path, "c.yaml", "nested:\n  deep:\n    leaf: 42\nplain: 7\n")
    )
    assert c.post_init_called is True


def test_raw_config_is_the_parsed_dict(tmp_path):
    """_raw_config holds the exact parsed mapping from the YAML file."""
    c = _StockstreamStyleConfig(
        _write(tmp_path, "c.yaml", "nested:\n  deep:\n    leaf: 42\nplain: 7\n")
    )
    assert c._raw_config == {"nested": {"deep": {"leaf": 42}}, "plain": 7}
    assert c.leaf == 42


def test_dotted_get_reaches_nested_value(tmp_path):
    """self.get("a.b.c") reaches a nested value inside __post_init__."""
    c = _StockstreamStyleConfig(
        _write(tmp_path, "c.yaml", "nested:\n  deep:\n    leaf: 42\nplain: 7\n")
    )
    assert c.dotted == 42
