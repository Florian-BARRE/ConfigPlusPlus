# Audit: configplusplus

> Phase 1 of the refactoring campaign (`codebase-refactoring`, `references/audit.md`).
> Read-only snapshot of the code at commit `fcd5349`, on 2026-11-08. Four read-only
> explorers audited in parallel (package internals, tests, poetry->uv tooling, frozen public
> surface + consumers); this document is the merged result.

## Summary

- Entry points: none of its own (a library). The user's config class body is the composition root
  where `env(...)` runs; `YamlConfigLoader.__init__` (path injected) is the only file reader.
- Size: 6 modules, **1034 lines** (`__init__` 24, `_display` 244, `base` 161, `env_loader` 136,
  `utils` 211, `yaml_loader` 258), all < 400. Tests: 1454 lines, **122 defs / 133 cases, 100%
  line coverage** (the 95% gate is enforced in CI `quality.yml:45`, not pyproject).
- Main problems: (1) the two loaders are not unified — `to_dict`/`_mask_if_secret`/`render`/
  `__repr__`/`__str__`/`_sensitive_keywords`/`_display_format` written **twice**; (2) `utils.py`
  holds two concerns (env readers + `.env` loader) under a "utils" name (principle 2 red flag);
  (3) Poetry tooling everywhere (backend + CI + checks + docs), no lock; (4) tests pin no error
  *message* to exact text and no non-boxed display format to an exact output (characterization
  gap); 9 duplicate test blocks, no conftest.
- Clean zones to keep: `__init__` (textbook thin facade), `_display` (pure single-responsibility
  engine), the clean one-way DAG (no cycles), centralized secret masking (single source of truth),
  fail-fast named errors, no `print()`, no swallowed exceptions.
- One suspected bug: `utils.py:134` the env cast-error message embeds the **raw value** of the
  var — a sensitive var that fails its cast surfaces in clear in the exception/traceback (BUG-01).

## Zones

### `src/configplusplus/__init__.py` (24 L)
- **Role:** package facade; `__version__`/`__author__` + re-exports + `__all__`.
- **Complies** with principle 7 (short public facade): pure re-export, zero logic.
- **Notes:** minor coupling — `base`/`yaml_loader` do `from configplusplus import _display`
  (package-attribute import) relying on `__init__` importing `_display` first; a direct
  submodule import is the robust idiom.

### `src/configplusplus/_display.py` (244 L)
- **Role:** shared secret-masking + value-rendering engine used by both loaders.
- **Units:** constants `DEFAULT_SENSITIVE_KEYWORDS` (15-21), `DISPLAY_FORMATS` (26); free
  functions `is_sensitive` (36), `mask_if_secret` (42), `format_value` (58), `render` (65, public
  entry), `_header` (110), `_group_by_prefix` (121), `_render_boxed` (129), `_render_table` (166),
  `_render_flat` (203), `_render_dotenv` (225), `_dotenv_value` (233), `_truncate` (242).
- **Principle 5:** qualified free-function exception — pure stateless transformations, no family
  of objects to model; not a grab-bag.
- **Leading underscore:** CORRECT. Its functions are not in `__all__` and not in docs; it is the
  private implementation behind the public `render()`/`print()` surface. Keep the name.

### `src/configplusplus/base.py` (161 L)
- **Role:** `ConfigMeta` (metaclass) gives env-side config classes `repr`/`to_dict`/`render`/mask;
  `ConfigBase` is the user subclassing point.
- **Units:** `ConfigMeta` (10-121): `to_dict` (20), `_mask_if_secret` (50), `_grouped_items` (66),
  `render` (78), `__repr__` (114); `ConfigBase` (124-161): `_sensitive_keywords` (148),
  `_display_format` (153), `__repr__`/`__str__` (155-161).
- **Notes:** `_mask_if_secret` and `_grouped_items` are **test-only** surface — not called by the
  package's own render path, alive only via characterization tests; movable/removable.

### `src/configplusplus/env_loader.py` (136 L)
- **Role:** `EnvConfigLoader` (extends `ConfigBase`); adds `get` (75), `has` (96), `validate` (116)
  classmethods. ~60 of 136 lines are the class docstring. No env read here (reads happen in
  `utils.env` at the user's class-definition time).

### `src/configplusplus/utils.py` (211 L)
- **Role:** env-var readers + `.env` file loader.
- **Units:** `safe_load_envs` (15-87), `env` (90-135), `env_optional` (138-156), `env_list` (159-211).
- **Principle 2:** MILD deviation — two concerns (env-var reading vs `.env` file loading) under a
  "utils" name. All 4 functions are public (`__all__`); the **module name is movable** (docs import
  only via the facade; only tests import `configplusplus.utils`).
- **Secret-leak edge:** `utils.py:134` the cast-error message embeds the raw value (BUG-01).

### `src/configplusplus/yaml_loader.py` (258 L)
- **Role:** `YamlConfigLoader` — instance-based YAML config: path injected at construction,
  dot-notation `get`/`has`, `to_dict`, multi-format `render`.
- **Units:** `_collapse_container` (14), `YamlConfigLoader` (23-258): `_sensitive_keywords` (40),
  `_display_format` (44), `__init__` (46), `_load_yaml` (76), `__post_init__` (105), `get` (121),
  `has` (149), `to_dict` (176), `_mask_if_secret` (196), `render` (209), `__repr__`/`__str__`
  (252-258), `_raw_config` (70, documented, consumer-relied-on).
- **Notes:** does NOT inherit from `ConfigBase`; independently re-implements masking+render (the
  duplication root). Correct logging (binds class name, never logs values), fail-fast named errors.

### `tests/` (1454 L)
- **Coverage:** 122 defs / 133 cases, 100% line coverage per module. Gate `--cov-fail-under=95`
  is in CI (`quality.yml:45`), not pyproject.
- **Style:** plain `def test_*` (no test classes); 3 ad-hoc fixtures; **no conftest.py**. Three
  different env-isolation styles.
- **Duplication (9 blocks, phase-5 dedup):** 6x identical `TestConfig`, 3x `ListConfig`, 2x
  `DictConfig/NestedConfig`, 3x env-isolation styles, 4x render-all-formats loop, 3x unknown-format
  boundary, 2x `_display_format`-drives-repr, 3x secret-in-repr, 2x boxed snapshot.
- **Characterization gap:** none of the **7 public error messages** pinned to exact text; no
  **non-boxed** format pinned to an exact output (only boxed); dotenv quoting covers 4 of 9 chars.
- **Fragile:** order-assert, `/tmp` Path-repr tests, private-attr `_raw_config` asserts, manual
  `os.environ`/`tempfile` that leak on failure.

### Tooling / CI (Poetry surface)
- **No committed `poetry.lock`** (a disk-only one, ignored `.gitignore:109`); no `requirements.txt`.
- `.gitignore` does **NOT** ignore `uv.lock` (`#uv.lock` line 101 is commented) — the
  loggerplusplus un-ignore gotcha does not apply.
- `pyproject.toml` already PEP 621 (`[project]` present); the only `x-release-please-version`
  marker is in `__init__.py:5`; release-please reads `[project].version` (keep `[project]`).
- Poetry in: `pyproject.toml`, `quality.yml`, `.aidk/project.toml`, `orca.yaml`, `AGENTS.md`,
  `README.md`, `docs/`. **Release pipeline with poetry = `publish.yml` only** — must not change
  without florian (flag, do not edit).
- `ci.yml`/`codeql.yml`/`aidk-checks.yml`/`release-please.yml` have no poetry.

## Cross-cutting problems

| Problem | Where | Count |
|---|---|---|
| Display/masking logic written twice (base vs yaml) | base.py + yaml_loader.py | 6 units |
| "utils" grab-bag name, two concerns | utils.py | 1 |
| Package-attribute import ordering coupling | base.py:7, yaml_loader.py:11 | 2 |
| Dead test-only helpers | base.py `_mask_if_secret`/`_grouped_items` | 2 |
| No conftest, 3 env-isolation styles, 9 duplicate blocks | tests/ | 9 |
| Error messages not pinned; non-boxed formats not goldened | tests/ | 7 + 4 + 5 |
| Poetry tooling | 8 files | — |
| Secret value in cast-error message | utils.py:134 | 1 (BUG-01) |

## Risks

- **Published package with real consumers** — the surface is frozen (see the frozen contract in
  `docs/architecture.md`). A layout move must not change any public name, signature, or behaviour.
- **Characterization net must be in place before any structural move** (phase 3 before phase 5).
- **Sensitive tooling wave** (install files): own wave, own review, CI green, routes to florian.

## Open questions (resolved at Validation Point 1 by florian)

- Q1: unify the two loaders via `ConfigDisplayMixin` in `_display.py` — **YES**.
- Q2: rename `test_utils.py` -> `test_env.py` with the module — **YES**.
- Q3: the `utils.py:134` secret leak — **real security bug, own prioritized ticket BUG-01**, fixed
  on its own wave riding the characterization net (it changes a public message).
- Confirmed: the frozen surface includes the **private members Stockstream consumes** on
  `YamlConfigLoader` (`__post_init__`, `_raw_config`, dotted `get`) — the net must pin those.
