"""Shared secret-masking and value-rendering engine for the config loaders.

Both ``ConfigMeta`` (env/class configs) and ``YamlConfigLoader`` mask and render
their values. Keeping the masking *and* the frame/row drawing here means a change
is made once, not twice, and both loaders offer the same set of display formats.
"""

import json
import pathlib
from typing import Any

# The default sensitive-keyword set. A config may extend it via a class-level
# ``_sensitive_keywords`` attribute — extend only, never narrow (masking is a
# safety feature: downstream apps debug-log their whole config at startup).
DEFAULT_SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "SECRET",
    "API_KEY",
    "PASSWORD",
    "TOKEN",
    "CREDENTIAL",
)

# Display formats accepted by ``render`` and by the ``_display_format`` attribute
# / ``render(fmt=...)`` argument of both loaders. ``boxed`` is the default and
# reproduces the historical framed output.
DISPLAY_FORMATS: tuple[str, ...] = ("boxed", "table", "json", "dotenv", "flat")

# Inner width of the ╔══╗ frame; kept constant so framed output stays stable.
_BOX_WIDTH: int = 44
# Value column is truncated past this width in the ``table`` format.
_MAX_TABLE_VALUE_WIDTH: int = 60

Items = list[tuple[str, Any]]


def is_sensitive(key: str, keywords: tuple[str, ...]) -> bool:
    """Return True if the key name contains any sensitive keyword (case-insensitive)."""
    upper = key.upper()
    return any(keyword in upper for keyword in keywords)


def mask_if_secret(key: str, value: Any, keywords: tuple[str, ...]) -> Any:
    """Mask a value when its key looks sensitive.

    ``None`` and non-sensitive values pass through unchanged. Short secrets
    (<= 6 chars) become ``***hidden***``; longer ones keep only their edges.
    """
    if value is None:
        return None
    if not is_sensitive(key, keywords):
        return value
    s = str(value)
    if len(s) <= 6:
        return "***hidden***"
    return f"{s[:3]}…{s[-2:]} (hidden)"


def format_value(value: Any) -> Any:
    """Resolve ``pathlib.Path`` values to readable absolute strings for display."""
    if isinstance(value, pathlib.Path):
        return str(value.resolve())
    return value


def render(
    title: str,
    items: Items,
    *,
    fmt: str = "boxed",
    subtitle: str | None = None,
    grouped: bool = False,
    empty_marker: str | None = None,
) -> str:
    """Render already-masked config items in the requested format.

    Args:
        title: Config class name shown in the header.
        items: ``(key, value)`` pairs whose values are already masked/formatted.
        fmt: One of :data:`DISPLAY_FORMATS`.
        subtitle: Optional line under the header (e.g. a YAML file path). Honoured
            by ``boxed``, ``table`` and ``flat``; ignored by ``json``/``dotenv``.
        grouped: Group keys by the prefix before the first underscore (``boxed``
            only). Other formats are always flat.
        empty_marker: Text shown when ``items`` is empty.

    Returns:
        The formatted, ready-to-print string.

    Raises:
        ValueError: If ``fmt`` is not a known display format.
    """
    if fmt not in DISPLAY_FORMATS:
        raise ValueError(
            f"Unknown display format {fmt!r}; choose from {', '.join(DISPLAY_FORMATS)}"
        )

    if fmt == "boxed":
        return _render_boxed(
            title, items, subtitle=subtitle, grouped=grouped, empty_marker=empty_marker
        )
    if fmt == "table":
        return _render_table(title, items, subtitle=subtitle, empty_marker=empty_marker)
    if fmt == "flat":
        return _render_flat(title, items, subtitle=subtitle, empty_marker=empty_marker)
    if fmt == "json":
        return json.dumps(dict(items), indent=2, default=str, ensure_ascii=False)
    return _render_dotenv(items)


def _header(title: str) -> list[str]:
    """Build the ╔══╗ frame lines around the (upper-cased) title."""
    bar = "═" * _BOX_WIDTH
    return [
        "\n",
        f"╔{bar}╗",
        f"║  {title.upper().center(_BOX_WIDTH - 4)}  ║",
        f"╚{bar}╝",
    ]


def _group_by_prefix(items: Items) -> dict[str, Items]:
    """Group items by the prefix before the first underscore (QDRANT_URL -> QDRANT)."""
    groups: dict[str, Items] = {}
    for key, value in items:
        groups.setdefault(key.split("_", 1)[0], []).append((key, value))
    return groups


def _render_boxed(
    title: str,
    items: Items,
    *,
    subtitle: str | None,
    grouped: bool,
    empty_marker: str | None,
) -> str:
    """Historical framed output: grouped (4-space) or flat (2-space) rows."""
    lines = _header(title)
    if subtitle is not None:
        lines += ["", f"▶ {subtitle}"]

    if not items:
        if empty_marker is not None:
            lines += ["", f"  {empty_marker}"]
        lines.append("")
        return "\n".join(lines)

    if grouped:
        groups = _group_by_prefix(items)
        for prefix in sorted(groups):
            group = groups[prefix]
            width = max(len(k) for k, _ in group)
            lines += ["", f"▶ {prefix}"]
            for key, value in sorted(group, key=lambda kv: kv[0]):
                lines.append(f"    {key.ljust(width)} = {value!r}")
    else:
        width = max(len(k) for k, _ in items)
        lines.append("")
        for key, value in sorted(items, key=lambda kv: kv[0]):
            lines.append(f"  {key.ljust(width)} = {value!r}")

    lines.append("")
    return "\n".join(lines)


def _render_table(
    title: str, items: Items, *, subtitle: str | None, empty_marker: str | None
) -> str:
    """Aligned two-column grid with box-drawing borders."""
    lines = ["\n", title.upper()]
    if subtitle is not None:
        lines.append(subtitle)

    if not items:
        if empty_marker is not None:
            lines += ["", f"  {empty_marker}"]
        lines.append("")
        return "\n".join(lines)

    body = [
        (key, _truncate(repr(value), _MAX_TABLE_VALUE_WIDTH))
        for key, value in sorted(items, key=lambda kv: kv[0])
    ]
    key_w = max(len("KEY"), *(len(k) for k, _ in body))
    val_w = max(len("VALUE"), *(len(v) for _, v in body))

    top = f"┌{'─' * (key_w + 2)}┬{'─' * (val_w + 2)}┐"
    sep = f"├{'─' * (key_w + 2)}┼{'─' * (val_w + 2)}┤"
    bottom = f"└{'─' * (key_w + 2)}┴{'─' * (val_w + 2)}┘"

    lines += [
        "",
        top,
        f"│ {'KEY'.ljust(key_w)} │ {'VALUE'.ljust(val_w)} │",
        sep,
    ]
    for key, value in body:
        lines.append(f"│ {key.ljust(key_w)} │ {value.ljust(val_w)} │")
    lines += [bottom, ""]
    return "\n".join(lines)


def _render_flat(
    title: str, items: Items, *, subtitle: str | None, empty_marker: str | None
) -> str:
    """Aligned ``KEY = value`` lines with no frame — compact for logs/grep."""
    lines = ["\n", title.upper()]
    if subtitle is not None:
        lines.append(subtitle)

    if not items:
        if empty_marker is not None:
            lines += ["", f"  {empty_marker}"]
        lines.append("")
        return "\n".join(lines)

    width = max(len(k) for k, _ in items)
    lines.append("")
    for key, value in sorted(items, key=lambda kv: kv[0]):
        lines.append(f"{key.ljust(width)} = {value!r}")
    lines.append("")
    return "\n".join(lines)


def _render_dotenv(items: Items) -> str:
    """``KEY=value`` lines, ready to paste into a ``.env`` file."""
    return "\n".join(
        f"{key}={_dotenv_value(value)}"
        for key, value in sorted(items, key=lambda kv: kv[0])
    )


def _dotenv_value(value: Any) -> str:
    """Quote a dotenv value only when it contains characters that need it."""
    s = str(value)
    if s == "" or any(ch in s for ch in " #\"'\n\t"):
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s


def _truncate(text: str, width: int) -> str:
    """Trim ``text`` to ``width`` characters, marking the cut with an ellipsis."""
    return text if len(text) <= width else text[: width - 1] + "…"


class ConfigDisplayMixin:
    """Shared mask -> render pipeline of both loaders (collect -> mask -> render).

    ``ConfigMeta`` (env side, the *class* is the config) and ``YamlConfigLoader``
    (yaml side, an *instance* is the config) differ only in how they gather the
    values to display, so each supplies :meth:`_collect_items` (and, optionally,
    the layout hooks below); everything else lives here, once. It is a plain
    mixin, not an ABC: the two access models stay genuinely separate.

    ``_sensitive_keywords`` and ``_display_format`` are the two documented
    extension points; a subclass extends the keywords (never narrows them).
    """

    _sensitive_keywords: tuple[str, ...] = DEFAULT_SENSITIVE_KEYWORDS
    _display_format: str = "boxed"

    def _collect_items(self) -> dict[str, Any]:
        """Return the raw ``{key: value}`` pairs to display (loader-specific)."""
        raise NotImplementedError

    def _display_title(self) -> str:
        """Config name shown in the header (the class name by default)."""
        return type(self).__name__

    def _display_layout(self) -> dict[str, Any]:
        """Extra keyword arguments for :func:`render` (subtitle, grouping...)."""
        return {}

    def _display_value(self, value: Any) -> Any:
        """Prepare one (already masked) value for display."""
        return format_value(value)

    def _mask_if_secret(self, key: str, value: Any) -> Any:
        """Mask ``value`` when ``key`` matches one of the sensitive keywords."""
        return mask_if_secret(key, value, self._sensitive_keywords)

    def to_dict(self, *, mask: bool = False) -> dict[str, Any]:
        """Return the config values as a dict.

        Args:
            mask: When True, sensitive values are masked (safe to log). When
                False (default), raw values are returned.
        """
        result = self._collect_items()
        if mask:
            result = {k: self._mask_if_secret(k, v) for k, v in result.items()}
        return result

    def render(self, *, fmt: str | None = None, mask: bool = True) -> str:
        """Render the configuration as a string in the requested format.

        Args:
            fmt: One of :data:`DISPLAY_FORMATS`. Defaults to ``_display_format``.
            mask: When True (default), sensitive values are masked — keep it True
                for anything that may be logged. Pass False only for a raw dump.

        Raises:
            ValueError: If ``fmt`` is not a known display format.
        """
        chosen = fmt if fmt is not None else self._display_format
        items = [
            (
                key,
                self._display_value(
                    self._mask_if_secret(key, value) if mask else value
                ),
            )
            for key, value in self.to_dict().items()
        ]
        return render(
            self._display_title(), items, fmt=chosen, **self._display_layout()
        )

    def __repr__(self) -> str:
        """Pretty representation in the configured ``_display_format``."""
        return type(self).render(self)

    def __str__(self) -> str:
        """String representation uses the pretty repr."""
        return type(self).render(self)
