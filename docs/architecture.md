# Architecture: configplusplus

> Target architecture of the project, following `coding-standards`. Written in phase 2 of the
> refactoring campaign (codebase-refactoring). Base commit `fcd5349`. Validated on 2026-11-08 by
> florian (Validation Point 1). Stays as the project's living architecture document afterwards.

## Overview

configplusplus is a single PUBLIC PyPI library (not a multi-app). It provides typed configuration
classes loaded from environment variables or YAML, with a grouped display and automatic masking of
secrets. One package, one facade, 6 modules (~1034 lines, all < 400). Shape: a **library**
(`coding-standards` `python.md` / `project-shapes.md` library form) — a thin public facade over a
few cohesive modules. It has no entry point of its own: the "entry point" is the user's config
class body, where the `env(...)` helpers run (the library's intended config boundary).

The public contract is FROZEN (real consumers: the kit + sibling apps on this machine). During the
campaign only the **structure** moves; the **surface** (`__all__`, the public names, docs and
examples) does not. Behaviour is preserved by a characterization safety net.

## Tree (target)

```
src/configplusplus/
├── __init__.py        # facade: __all__ + re-exports only (names frozen; unchanged)
├── _display.py        # shared mask + render engine (leaf); + ConfigDisplayMixin
├── base.py            # ConfigMeta + ConfigBase (env-side base classes)
├── env_loader.py      # EnvConfigLoader (public env-side base: get / has / validate)
├── env.py             # NEW (was utils.py): env, env_optional, env_list, safe_load_envs
├── yaml_loader.py     # YamlConfigLoader (public yaml-side class)
└── py.typed           # PEP 561 marker
```

Removed: `utils.py` (renamed to `env.py`; its four functions keep their frozen public names, only
the module path moves). `_display.py` keeps its name (the leading underscore is correct: it is a
private engine behind the public `render()` method surface).

## Layers and dependencies

- One-way DAG: `_display` (leaf) <- `env`, `base`, `yaml_loader`; `base` <- `env_loader`;
  `__init__` (top) imports all. No cycles, no upward imports.
- Configuration is read only in `env.py` (`env` / `env_list` / `safe_load_envs`), called from the
  user's config class body; and in `yaml_loader.__init__` (path injected by the constructor). No
  config read at import, none in `base` / `env_loader` / `_display` (principle 4 respected).

## Modules (the package)

| Module | Responsibility | Main units | Form |
|---|---|---|---|
| `__init__` | public facade | `__all__`, re-exports | facade, no logic |
| `_display` | mask + render engine + shared display mixin | `render`, `mask_if_secret`, `_render_*`, `ConfigDisplayMixin` | pure engine + mixin |
| `base` | env-side base | `ConfigMeta` (metaclass), `ConfigBase` | metaclass + base class |
| `env_loader` | public env-side base | `EnvConfigLoader` (`get`/`has`/`validate`) | base class |
| `env` | env-var readers + `.env` loader | `env`, `env_optional`, `env_list`, `safe_load_envs` | public free functions |
| `yaml_loader` | yaml-side class | `YamlConfigLoader` | instance class |

## Families

The two loaders (env-side `EnvConfigLoader` via `ConfigBase`/`ConfigMeta`, yaml-side
`YamlConfigLoader`) share the **display/masking** concern. Today that shared logic
(`to_dict`-masking, `_mask_if_secret`, `render`, `__repr__`/`__str__`, `_sensitive_keywords`,
`_display_format`) is written **twice** — the main structural gap.

Target: a `ConfigDisplayMixin` (in `_display.py`) provides the shared pipeline (collect items ->
mask -> render, plus `__repr__`/`__str__` and the `_sensitive_keywords` / `_display_format`
defaults) with a `_collect_items()` hook for the two collection strategies (class-level UPPERCASE
attrs vs public instance attrs). The two access models stay genuinely separate; the mixin removes
the duplicated mask+render boilerplate **without touching any frozen name**. No forced ABC (the
access models differ enough that one contract would be over-abstraction).

## Cross-cutting choices

- **Configuration**: the user's config class is the composition root; `env()` / `YamlConfigLoader`
  are the only readers. **Tooling: uv only** (PEP 621 `pyproject` + committed `uv.lock`, hatchling
  backend, PEP 735 `[dependency-groups]` dev group). No Poetry.
- **Logging**: loggerplusplus (`safe_load_envs` binds `ENV_LOADER`; `YamlConfigLoader` binds its
  class name). Pure modules (`env` / `base` / `_display`) log nothing.
- **Errors**: fail-fast, named (`RuntimeError` for env cast/missing; `FileNotFoundError` /
  `yaml.YAMLError` / `TypeError` for YAML). Nothing silently swallowed.
- **Naming**: leading underscore = private (`_display`, `_render_*`, `_mask_if_secret`,
  `_collect_items`). Public names (in `__all__`) are frozen. `_sensitive_keywords` /
  `_display_format` are documented extension points (private-looking, de-facto public).

## Mapping table

| Current location | Content | Target location | Ticket | Status |
|---|---|---|---|---|
| `utils.py` | env, env_optional, env_list, safe_load_envs | `env.py` (rename; 4 names keep their public identity, re-exported from `__init__`) | R-03 | todo |
| `base.py` | `ConfigMeta` (`to_dict`/`render`/`__repr__` + dead `_mask_if_secret`/`_grouped_items`), `ConfigBase` | `base.py` (use `ConfigDisplayMixin`; remove the two dead helpers) | R-04 | todo |
| `yaml_loader.py` | `YamlConfigLoader` (re-implements `to_dict`/`_mask_if_secret`/`render`/`__repr__` + the 2 extension points) | `yaml_loader.py` (use `ConfigDisplayMixin`; keep its collection strategy) | R-04 | todo |
| `base.py` / `yaml_loader.py` | `from configplusplus import _display` (ordering-coupled) | direct `from configplusplus._display import ...` | R-05 | todo |
| `_display.py` | mask + render engine | `_display.py` + new `ConfigDisplayMixin` | R-04 | todo |
| `__init__.py` | facade re-exports | `__init__.py` (update the env import path only; `__all__` unchanged) | R-03 | todo |
| Poetry tooling | poetry-core backend, `[tool.poetry]`, poetry in CI/checks/docs, no lock | uv: hatchling, PEP 621 + PEP 735, committed `uv.lock`, uv in CI/checks/docs | R-01 | todo |
| `tests/` | per-module; 3 isolation styles; 9 duplicate blocks; no conftest; error messages not pinned | `tests/conftest.py` (shared `_isolate_environ` + fixture classes + render-all / unknown-format helpers); characterization goldens (7 error messages exact, 4 non-boxed formats, 5 dotenv chars); dedup the 9 blocks | R-02 (net) + R-06 (clean) | todo |

## Tooling (uv-only) — the sensitive wave (R-01)

- Backend `poetry-core` -> `hatchling` (`[tool.hatch.build.targets.wheel] packages=["src/configplusplus"]`).
- `[project]` **stays** (release-please reads `[project].version`); `[tool.poetry]` deleted; dev
  deps -> PEP 735 `[dependency-groups].dev` (caret -> PEP 440).
- Committed `uv.lock` (verified NOT gitignored — the loggerplusplus un-ignore gotcha does not
  apply); delete the disk-only `poetry.lock`.
- CI `quality.yml`, checks `.aidk/project.toml`, `orca.yaml`: `poetry install/run/build` ->
  `uv sync --locked` / `uv run` / `uv build`.
- `publish.yml` (release pipeline): **NOT edited** by the wave (never_alone); **flagged** to
  florian for the coupled companion (version read `poetry version -s` -> PEP 621; `poetry build`
  -> `uv build`).
- Sensitive (install files): own wave, own review, CI green before merge, **routes to florian's
  merge** even in autonomous mode.

## Decisions (validated at Validation Point 1 by florian)

- Keep the `_display.py` name (underscore is correct for a private engine).
- `utils.py` -> `env.py` (removes the principle-2 "utils" red flag; the 4 functions keep their
  frozen public names).
- Shared `ConfigDisplayMixin` in `_display.py` to remove the base<->yaml display duplication
  (Q1 — the main structural win; touches no frozen name; the safety net guards behaviour).
- Rename `test_utils.py` -> `test_env.py` with the module (Q2).
- The cast-error secret leak (Q3) is a **real security bug, its own prioritized ticket BUG-01**,
  fixed on its own wave riding the characterization net (it changes a public message).
- uv-only tooling in one sensitive wave; `publish.yml` flagged, not edited.

## Open questions

- (none — Validation Point 1 resolved Q1/Q2/Q3; see the Decisions above.)
- The net must also pin the **private members Stockstream consumes** on `YamlConfigLoader`
  (`__post_init__`, `_raw_config`, dotted `get`), even though they are private (team-leader
  confirmed at VP1).
