"""Tests for the shared display/render engine."""

import json

import pytest

from configplusplus import _display

ITEMS = [
    ("DATABASE_HOST", "localhost"),
    ("DATABASE_PORT", 5432),
    ("REDIS_URL", "redis://localhost:6379"),
]


def test_display_formats_are_the_documented_set():
    """The advertised format list must stay in sync with what render accepts."""
    assert _display.DISPLAY_FORMATS == ("boxed", "table", "json", "dotenv", "flat")


def test_render_rejects_unknown_format():
    """An unknown format is a ValueError that names the valid choices."""
    with pytest.raises(ValueError) as exc:
        _display.render("Cfg", ITEMS, fmt="xml")
    message = str(exc.value)
    assert "xml" in message
    for fmt in _display.DISPLAY_FORMATS:
        assert fmt in message


def test_render_boxed_grouped():
    """Grouped boxed output frames the title and groups by prefix."""
    out = _display.render("Cfg", ITEMS, fmt="boxed", grouped=True)
    assert "╔" in out and "╚" in out
    assert "CFG" in out
    assert "▶ DATABASE" in out
    assert "▶ REDIS" in out


def test_render_boxed_flat_with_subtitle():
    """Flat boxed output shows the subtitle line and no group headers."""
    out = _display.render("Cfg", ITEMS, fmt="boxed", subtitle="Config Path: /x.yaml")
    assert "▶ Config Path: /x.yaml" in out
    assert "▶ DATABASE" not in out


def test_render_boxed_empty_shows_marker():
    """An empty config renders the empty marker."""
    out = _display.render("Cfg", [], fmt="boxed", empty_marker="(nothing)")
    assert "(nothing)" in out


def test_render_table_has_grid_and_headers():
    """Table output draws a bordered grid with KEY/VALUE headers."""
    out = _display.render("Cfg", ITEMS, fmt="table")
    assert "┌" in out and "┴" in out
    assert "KEY" in out and "VALUE" in out
    assert "DATABASE_HOST" in out


def test_render_table_truncates_long_values():
    """Values longer than the column cap are ellipsised."""
    long_value = "x" * 200
    out = _display.render("Cfg", [("K", long_value)], fmt="table")
    assert "…" in out
    assert "x" * 200 not in out


def test_render_table_empty_marker():
    """Empty table still renders the marker, no grid."""
    out = _display.render("Cfg", [], fmt="table", empty_marker="(none)")
    assert "(none)" in out
    assert "┌" not in out


def test_render_flat_aligns_pairs():
    """Flat output is unframed aligned KEY = value lines."""
    out = _display.render("Cfg", ITEMS, fmt="flat")
    assert "╔" not in out
    assert "DATABASE_HOST = 'localhost'" in out


def test_render_flat_empty_marker():
    """Flat output honours the empty marker."""
    out = _display.render("Cfg", [], fmt="flat", empty_marker="(none)")
    assert "(none)" in out


def test_render_json_is_parseable_and_sorted():
    """JSON output round-trips through json.loads with the same values."""
    out = _display.render("Cfg", ITEMS, fmt="json")
    parsed = json.loads(out)
    assert parsed == dict(ITEMS)


def test_render_json_falls_back_to_str_for_non_serialisable():
    """A non-JSON-native value is stringified rather than raising."""
    out = _display.render("Cfg", [("PATHS", {1, 2})], fmt="json")
    parsed = json.loads(out)
    assert isinstance(parsed["PATHS"], str)


def test_render_dotenv_plain_and_quoted():
    """Dotenv quotes only values that need it; others stay bare."""
    items = [
        ("PLAIN", "value"),
        ("SPACED", "a b"),
        ("EMPTY", ""),
        ("QUOTED", 'a"b'),
    ]
    out = _display.render("Cfg", items, fmt="dotenv")
    lines = dict(line.split("=", 1) for line in out.splitlines())
    assert lines["PLAIN"] == "value"
    assert lines["SPACED"] == '"a b"'
    assert lines["EMPTY"] == '""'
    assert lines["QUOTED"] == '"a\\"b"'


def test_mask_if_secret_short_and_long():
    """Short secrets are fully hidden; long ones keep only their edges."""
    keywords = _display.DEFAULT_SENSITIVE_KEYWORDS
    assert _display.mask_if_secret("API_KEY", "abc", keywords) == "***hidden***"
    masked = _display.mask_if_secret("API_KEY", "abcdefghij", keywords)
    assert masked.endswith("(hidden)")
    assert _display.mask_if_secret("API_KEY", None, keywords) is None
    assert _display.mask_if_secret("HOST", "localhost", keywords) == "localhost"
