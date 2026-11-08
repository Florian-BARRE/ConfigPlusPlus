"""Characterization net: the display / render + masking boundary (PHASE 3).

This file pins the *current* output of the render engine
(``configplusplus._display``) and the secret-masking rules, byte for byte, so the
later structural move (``ConfigDisplayMixin``) is provably behaviour-preserving.

It is deliberately self-contained: it builds small item lists, calls the public
render engine directly, and ties a minimal ``EnvConfigLoader`` subclass to the
same goldens. It never reads the environment, the filesystem, or the network,
and the fake secret values are low-entropy placeholders that gitleaks does not
flag.

The goldens below are captured from the code *as it stands today* (not an ideal),
via ``_display.render`` and ``_display._dotenv_value`` / ``mask_if_secret``.
"""

import json

import pytest

from configplusplus import EnvConfigLoader, _display

# One fixed, representative item list: a grouped prefix (``DB_*``), an int, and
# a sensitive key whose value is already masked (the engine renders values it is
# handed, so we pass the masked form to pin the display layer itself).
ITEMS = [
    ("DB_HOST", "localhost"),
    ("DB_PORT", 5432),
    ("SECRET_API_KEY", "sec…23 (hidden)"),
]

# The title the goldens render under. It is the upper-cased name of ``_NetLoader``
# below, so the direct-engine and loader goldens share one expected string.
TITLE = "_NETLOADER"


class _NetLoader(EnvConfigLoader):
    """A minimal, leak-free loader whose masked items equal ``ITEMS`` exactly."""

    DB_HOST = "localhost"
    DB_PORT = 5432
    SECRET_API_KEY = "secret123"  # masked to 'sec…23 (hidden)'


# --- A. Exact output goldens for the four non-boxed formats -------------------


def test_table_golden():
    """The ``table`` format draws the exact bordered grid for the fixed items."""
    expected = (
        "\n\n_NETLOADER\n"
        "\n"
        "┌────────────────┬───────────────────┐\n"
        "│ KEY            │ VALUE             │\n"
        "├────────────────┼───────────────────┤\n"
        "│ DB_HOST        │ 'localhost'       │\n"
        "│ DB_PORT        │ 5432              │\n"
        "│ SECRET_API_KEY │ 'sec…23 (hidden)' │\n"
        "└────────────────┴───────────────────┘\n"
    )
    assert _display.render(TITLE, ITEMS, fmt="table") == expected


def test_json_golden():
    """The ``json`` format emits the exact two-space-indented document."""
    expected = (
        "{\n"
        '  "DB_HOST": "localhost",\n'
        '  "DB_PORT": 5432,\n'
        '  "SECRET_API_KEY": "sec…23 (hidden)"\n'
        "}"
    )
    assert _display.render(TITLE, ITEMS, fmt="json") == expected


def test_json_round_trip():
    """The ``json`` output parses back to exactly the expected dict."""
    parsed = json.loads(_display.render(TITLE, ITEMS, fmt="json"))
    assert parsed == {
        "DB_HOST": "localhost",
        "DB_PORT": 5432,
        "SECRET_API_KEY": "sec…23 (hidden)",
    }


def test_dotenv_golden():
    """The ``dotenv`` format emits bare or quoted KEY=value lines, no framing."""
    expected = 'DB_HOST=localhost\nDB_PORT=5432\nSECRET_API_KEY="sec…23 (hidden)"'
    assert _display.render(TITLE, ITEMS, fmt="dotenv") == expected


def test_flat_golden():
    """The ``flat`` format emits unframed, aligned ``KEY = value`` lines."""
    expected = (
        "\n\n_NETLOADER\n"
        "\n"
        "DB_HOST        = 'localhost'\n"
        "DB_PORT        = 5432\n"
        "SECRET_API_KEY = 'sec…23 (hidden)'\n"
    )
    assert _display.render(TITLE, ITEMS, fmt="flat") == expected


# --- B. Unknown-format error ---------------------------------------------------


def test_unknown_format_error_message():
    """An unknown format raises ValueError with the exact message naming the choices."""
    with pytest.raises(ValueError) as exc:
        _display.render(TITLE, ITEMS, fmt="nope")
    assert (
        str(exc.value)
        == "Unknown display format 'nope'; choose from boxed, table, json, dotenv, flat"
    )


# --- C. Dotenv quoting for the trigger set ------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("plain", "plain"),  # no trigger char -> bare
        ("with space", '"with space"'),  # space -> quoted
        ("", '""'),  # empty -> quoted
        ("single'", '"single\'"'),  # single quote -> quoted
        ('double"', '"double\\""'),  # double quote -> quoted + escaped
        ("back\\slash", "back\\slash"),  # backslash -> NOT quoted, not escaped
        ("hash#", '"hash#"'),  # # -> quoted
        ("line1\nline2", '"line1\nline2"'),  # newline -> quoted
        ("tab\tx", '"tab\tx"'),  # tab -> quoted
    ],
)
def test_dotenv_value_quoting(value, expected):
    """``_dotenv_value`` quotes only when a trigger char is present.

    Backslash and double quote are the only escaped characters; everything else
    (space, ``#``, newline, tab, single quote) is merely quoted.
    """
    assert _display._dotenv_value(value) == expected


def test_dotenv_quoting_through_format():
    """The same quoting rules hold when driven through the ``dotenv`` format."""
    items = [
        ("PLAIN", "plain"),
        ("SPACED", "with space"),
        ("EMPTY", ""),
        ("QUOTED", 'double"'),
        ("SLASH", "back\\slash"),
        ("HASHED", "hash#"),
        ("NEWLINE", "line1\nline2"),
        ("TABBED", "tab\tx"),
    ]
    assert (
        _display.render(TITLE, items, fmt="dotenv") == 'EMPTY=""\n'
        'HASHED="hash#"\n'
        'NEWLINE="line1\nline2"\n'
        "PLAIN=plain\n"
        'QUOTED="double\\""\n'
        "SLASH=back\\slash\n"
        'SPACED="with space"\n'
        'TABBED="tab\tx"'
    )


# --- D. Masking ----------------------------------------------------------------


def test_default_sensitive_keywords_tuple():
    """The default sensitive-keyword set is exactly these five, in this order."""
    assert _display.DEFAULT_SENSITIVE_KEYWORDS == (
        "SECRET",
        "API_KEY",
        "PASSWORD",
        "TOKEN",
        "CREDENTIAL",
    )


def test_mask_short_secret_fully_hidden():
    """A sensitive secret of 6 chars or fewer is replaced by ``***hidden***``."""
    assert (
        _display.mask_if_secret("API_KEY", "abc12", _display.DEFAULT_SENSITIVE_KEYWORDS)
        == "***hidden***"
    )


def test_mask_short_secret_at_boundary_six():
    """A 6-char secret is the boundary: still fully hidden."""
    assert (
        _display.mask_if_secret(
            "API_KEY", "123456", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        == "***hidden***"
    )


def test_mask_long_secret_keeps_edges():
    """A longer secret keeps only its first 3 and last 2 chars, marked hidden."""
    assert (
        _display.mask_if_secret(
            "API_KEY", "secret123", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        == "sec…23 (hidden)"
    )
    assert (
        _display.mask_if_secret(
            "API_KEY", "1234567", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        == "123…67 (hidden)"
    )


def test_mask_none_passes_through():
    """A ``None`` value is returned unchanged, even for a sensitive key."""
    assert (
        _display.mask_if_secret("API_KEY", None, _display.DEFAULT_SENSITIVE_KEYWORDS)
        is None
    )


def test_mask_non_sensitive_unchanged():
    """A non-sensitive value passes through unchanged."""
    assert (
        _display.mask_if_secret(
            "APP_NAME", "configplusplus", _display.DEFAULT_SENSITIVE_KEYWORDS
        )
        == "configplusplus"
    )


@pytest.mark.parametrize(
    "key",
    [
        "MY_SECRET",  # SECRET
        "service_api_key",  # API_KEY
        "db_password",  # PASSWORD
        "ACCESS_TOKEN",  # TOKEN
        "CREDENTIAL_STORE",  # CREDENTIAL
    ],
)
def test_mask_keyword_matches_case_insensitive(key):
    """All five sensitive keywords match case-insensitively and mask the same way."""
    assert (
        _display.mask_if_secret(key, "0123456789", _display.DEFAULT_SENSITIVE_KEYWORDS)
        == "012…89 (hidden)"
    )


def test_is_sensitive_is_case_insensitive():
    """``is_sensitive`` matches a lower-cased key against the keyword set."""
    assert (
        _display.is_sensitive("db_password", _display.DEFAULT_SENSITIVE_KEYWORDS)
        is True
    )
    assert (
        _display.is_sensitive("DB_HOST", _display.DEFAULT_SENSITIVE_KEYWORDS) is False
    )


# --- E. Empty-items marker per format -----------------------------------------


def test_empty_table_marker():
    """With no items, ``table`` emits only the framed title."""
    assert _display.render(TITLE, [], fmt="table") == "\n\n_NETLOADER\n"


def test_empty_json_marker():
    """With no items, ``json`` emits an empty object."""
    assert _display.render(TITLE, [], fmt="json") == "{}"


def test_empty_dotenv_marker():
    """With no items, ``dotenv`` emits the empty string."""
    assert _display.render(TITLE, [], fmt="dotenv") == ""


def test_empty_flat_marker():
    """With no items, ``flat`` emits only the upper-cased title."""
    assert _display.render(TITLE, [], fmt="flat") == "\n\n_NETLOADER\n"


# --- Public loader method tied to the engine goldens ---------------------------


def test_loader_table_matches_engine_golden():
    """``render(fmt='table')`` on a real loader equals the direct engine golden."""
    assert _NetLoader.render(fmt="table") == _display.render(TITLE, ITEMS, fmt="table")


def test_loader_json_matches_engine_golden():
    """``render(fmt='json')`` on a real loader equals the direct engine golden."""
    assert _NetLoader.render(fmt="json") == _display.render(TITLE, ITEMS, fmt="json")


def test_loader_dotenv_matches_engine_golden():
    """``render(fmt='dotenv')`` on a real loader equals the direct engine golden."""
    assert _NetLoader.render(fmt="dotenv") == _display.render(
        TITLE, ITEMS, fmt="dotenv"
    )


def test_loader_flat_matches_engine_golden():
    """``render(fmt='flat')`` on a real loader equals the direct engine golden."""
    assert _NetLoader.render(fmt="flat") == _display.render(TITLE, ITEMS, fmt="flat")
