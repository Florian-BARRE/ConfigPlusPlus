# Refactor plan: configplusplus

> Phase 4 of the refactoring campaign (`codebase-refactoring`, `references/plan.md`).
> Written after Validation Point 1 (target architecture approved by florian, 2026-11-08) and the
> phase-3 characterization safety net (PR #35, #37, #38, merged). Validated: **PENDING**
> (team-leader -> florian) — this is VALIDATION POINT 2.

## Ground rules (unchanged during the campaign)

- Public contract FROZEN: `__all__` (9 names), public signatures, docs, examples. A layout move
  changes no public name, signature, or behaviour. The frozen surface ALSO includes the private
  members Stockstream consumes (`__post_init__`, `_raw_config`, dotted `get`) — pinned by the net.
- Behaviour is preserved by the phase-3 characterization net (PR #35/#37/#38, merged, 100% coverage).
- One ticket = one change = one branch = one worktree = one reviewed PR. Autonomous mode: the merge
  queue merges reviewed green PRs; **R-01 (uv) routes to florian's merge** (sensitive).
- A bug found during a wave = its own ticket (already split out as BUG-01).

## Status

- **R-02 (characterization net): DONE** — PR #35 (yaml), #37 (display + masking), #38 (env), merged.
  Full suite 186 passed / 100% line coverage (gate `--cov-fail-under=95` in CI `quality.yml`).

## Waves (recommended order)

Each wave is a separate branch/worktree, reviewed, CI green before merge. Each depends on the
previous wave being merged (the base moves forward). The net guards the structural waves: if a net
golden fails, that is the net doing its job (revert the wave, do not weaken the net).

### Wave 1 — BUG-01 (security, prioritized)
- **Goal:** fix the env cast-error message leaking the raw value (the `env` function, ex
  `utils.py:134`): a sensitive var that fails its cast must not surface in clear in the
  exception/traceback.
- **Files:** `src/configplusplus/utils.py` (the cast-error path); `tests/characterization/test_env.py`
  (update the golden it pins — the "rides on the net" step).
- **Acceptance:** the cast-error message no longer embeds the raw value (the key and the expected
  type, not the value); the env golden is updated to the new message; full suite green; no other
  behaviour change.
- **Risk:** changes a public error message (documented behaviour) — the net pins old -> new. Low.
- **Merge:** autonomous (security-critical: state it in the PR body).

### Wave 2 — R-03 (rename utils.py -> env.py)
- **Goal:** remove the principle-2 "utils" red flag: rename the module `utils.py` -> `env.py` (its
  four public functions keep their frozen names; only the module path moves); rename the test
  `test_utils.py` -> `test_env.py`; update the facade import.
- **Files:** `src/configplusplus/utils.py` -> `src/configplusplus/env.py` (git mv);
  `src/configplusplus/__init__.py` (the env import path only, `__all__` unchanged);
  `tests/test_utils.py` -> `tests/test_env.py` (git mv + any `configplusplus.utils` reference).
- **Acceptance:** `__all__` unchanged; `from configplusplus import env, env_list, env_optional,
  safe_load_envs` still works; full suite green. The net `tests/characterization/test_env.py`
  coexists with `tests/test_env.py` (the `tests/test_display.py` + `tests/characterization/
  test_display.py` precedent already proves there is no module-name collision).
- **Risk:** low (pure rename; the facade preserves the public names). The module path is not public
  (docs import via the facade; only tests imported `configplusplus.utils`).
- **Merge:** autonomous.

### Wave 3 — R-04 (ConfigDisplayMixin — the main structural gain)
- **Goal:** remove the base<->yaml display duplication. Add `ConfigDisplayMixin` to `_display.py`
  providing the shared pipeline (collect items -> mask -> render, `__repr__`/`__str__`, the
  `_sensitive_keywords` / `_display_format` defaults) with a `_collect_items()` hook for the two
  collection strategies (class-level UPPERCASE attrs vs public instance attrs). `ConfigMeta`/
  `ConfigBase` (base.py) and `YamlConfigLoader` (yaml_loader.py) use the mixin; remove the dead
  `ConfigMeta._mask_if_secret` / `_grouped_items` and their test-only callers.
- **Files:** `src/configplusplus/_display.py` (+ `ConfigDisplayMixin`); `src/configplusplus/base.py`
  (use the mixin, drop the dead helpers); `src/configplusplus/yaml_loader.py` (use the mixin, keep
  its collection strategy); the test that only called the dead helpers (removed or repointed).
- **Acceptance:** no frozen public name or signature changes; both loaders still produce identical
  render/repr output (the net goldens pass unchanged); the dead helpers are gone; coverage >= 95%.
- **Risk:** medium (touches both loaders' display path) — the net is the guard.
- **Merge:** autonomous.

### Wave 4 — R-05 (normalize _display imports)
- **Goal:** replace the ordering-coupled `from configplusplus import _display` with direct submodule
  imports `from configplusplus._display import ...` in `base.py` and `yaml_loader.py`.
- **Files:** `src/configplusplus/base.py`, `src/configplusplus/yaml_loader.py`.
- **Acceptance:** imports are direct submodule imports; full suite green.
- **Risk:** trivial. (Could be folded into Wave 3; kept separate for a clean diff.)
- **Merge:** autonomous.

### Wave 5 — R-06 (test suite cleanup)
- **Goal:** dedup the 9 duplicate test blocks and add a shared `tests/conftest.py` (the
  `_isolate_environ` snapshot promoted from the env tests, shared fixture classes, and the
  render-all / unknown-format helpers), converting the ad-hoc fixtures to shared ones. The
  characterization net stays intact (it is never weakened).
- **Files:** `tests/conftest.py` (new); `tests/test_*.py` (dedup + use the conftest). The
  characterization files remain the goldens.
- **Acceptance:** no test weakened or removed (the kit blocks fewer assertions); coverage >= 95%;
  the 9 duplicate blocks consolidated into shared fixtures/helpers; full suite green.
- **Risk:** low (test-only) but a large surface — all in the one branch.
- **Merge:** autonomous.

### Wave 6 — R-01 (Poetry -> uv, SENSITIVE)
- **Goal:** uv-only tooling. Backend `poetry-core` -> `hatchling`
  (`[tool.hatch.build.targets.wheel] packages=["src/configplusplus"]`); delete `[tool.poetry]`;
  `[project]` **stays** (release-please reads `[project].version`); dev deps -> PEP 735
  `[dependency-groups].dev` (caret -> PEP 440); commit `uv.lock` (verified NOT gitignored); delete
  the disk-only `poetry.lock`; CI `quality.yml`, checks `.aidk/project.toml`, `orca.yaml`,
  `AGENTS.md`, `README.md`, `docs/`: poetry -> uv (`uv sync --locked` / `uv run` / `uv build`).
  **`publish.yml` is NOT edited** (never_alone) — flagged to florian for the coupled companion
  (`poetry version -s` -> a PEP 621 version read; `poetry build` -> `uv build`).
- **Files:** `pyproject.toml`, `.github/workflows/quality.yml`, `.aidk/project.toml`, `orca.yaml`,
  `AGENTS.md`, `README.md`, `docs/` (the non-publish poetry references), + new `uv.lock`.
- **Acceptance:** `uv sync --locked` resolves; `uv run pytest` (full suite, >= 95%); `uv build`
  produces the wheel; no poetry reference remains in CI/checks/docs (the flagged `publish.yml`
  excepted); CI green.
- **Risk:** HIGH (install files + CI + release-pipeline coupling). Own wave, own review, CI green
  before merge.
- **Merge:** **routes to florian's merge** (sensitive) even in autonomous mode. `publish.yml` stays
  untouched; florian decides the coupled `publish.yml` change separately.

## Recommended sequence

BUG-01 -> R-03 -> R-04 -> R-05 -> R-06 -> R-01.

R-01 is independent of the structural waves; it is gated by florian, so it can run in parallel and
does not hold up the rest.

## Close (phase 6)

- A small structure test asserting the target layout (no `utils.py`, `env.py` present, `__all__`
  intact, no `ConfigMeta._mask_if_secret` / `_grouped_items`, direct `_display` imports) — its own PR.
- coding-standards conformance recorded in `AGENTS.md` (the conventions the package now follows).
- Campaign docs archived under `docs/refactor/` with a short before/after summary; the before/after
  report (structure + coverage) goes to the team-leader.
- Report the close to the team-leader (campaign done).

## Open questions (for Validation Point 2)

- Confirm the wave order (BUG-01 first as prioritized; R-01 last / parallel, florian-gated).
- R-05 separate or folded into R-04? (default: separate, for a clean diff.)
- `docs/refactor/audit.md` says the tests are "1454 lines"; the real total is 1434 (flagged by the
  reviewer; the docs PR was committed verbatim). Fix in a small follow-up or at the close.
