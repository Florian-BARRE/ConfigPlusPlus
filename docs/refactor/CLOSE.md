# Refactoring campaign — close (2026-11-09)

This directory (`docs/refactor/`) holds the configplusplus refactoring campaign's record: the
read-only audit (`audit.md`), the validated target architecture (`architecture.md`, moved here
from `docs/architecture.md` at close), and the wave/ticket plan (`plan.md`). All waves are merged
to `main`; this file is the short before/after summary and the corrected record.

## Scope
Bring the package internals and the test suite to coding-standards, and migrate the tooling from
Poetry to uv — without changing the public contract or behaviour. Reference pattern: the sibling
`loggerplusplus`.

## Result (all merged 2026-11-09, each a reviewed PR)
- **Security (3):** stop leaking env-var values in the cast-error paths.
  - #40 BUG-01 — `env()` cast-error message de-leaked.
  - #41 BUG-02 — `env_list()` item value de-leaked.
  - #42 BUG-03 — `from exc` -> `from None`, so the value leaves the traceback (intentional
    behaviour change; the goldens were re-pinned).
- **Structure (4):**
  - #43 R-03 — `utils.py` -> `env.py` (name matches its role); `test_utils.py` -> `test_env.py`.
  - #44 R-04 — the duplicated display/masking pipeline -> one shared `ConfigDisplayMixin` in
    `_display.py`; both loaders keep their own item-collection strategy.
  - #45 R-05 — the loaders import the `_display` engine directly (decoupled from the facade).
  - #46 R-06 — test-suite dedup: a shared `tests/conftest.py`, 9 duplicate blocks consolidated.
- **Tooling (1):**
  - #47 R-01 — Poetry -> uv: PEP 621 + hatchling, a PEP 735 `dev` group, a committed `uv.lock`;
    uv in CI, checks and docs. (Sensitive — merged by the maintainer, not the queue.)

The public contract stayed frozen throughout: `__all__` (9 names) and the private
`YamlConfigLoader` members the downstream `Stockstream` consumes (`__post_init__`, `_raw_config`,
dotted `get`). Final: **246 tests, 100% line coverage** (up from 133 cases at audit time; the
characterization net — PRs #35/#37/#38 — added the remaining cases as the safety net).

## Corrected record (the docs above are a point-in-time snapshot)
- **`_mask_if_secret` is LIVE production code, not dead.** After R-04 it lives once in
  `ConfigDisplayMixin` (`_display.py`) and is called by `to_dict(mask=True)` and `render()`. The
  audit/plan "dead helper" label only ever applied to `_grouped_items`.
- **`_grouped_items` (`base.py`) is test-only.** It is not called by the package's own render path —
  only by `tests/test_base.py`. Its removal is a valid, separate follow-up (below); it was deferred
  to keep the waves behaviour-preserving.
- **Test counts:** 186 was the count when the characterization net landed (R-02, #35/#37/#38); the
  final count at close is **246**. (The audit's "1454 lines" was a miscount — the pre-campaign test
  total was 1434; noted at `plan.md`.)

## Follow-ups (for the maintainer; NOT done by the campaign)
1. **Release pipeline is still Poetry-based.** `publish.yml` (a `never_alone` file, off-limits to
   agents) runs `pipx install poetry` / `poetry version -s` / `poetry build`. After R-01 the build
   backend is `hatchling` and `[tool.poetry]` is gone, so `poetry build` (and possibly
   `poetry version -s`) will likely fail at the next release. A companion change (a PEP 621 version
   read + `uv build`) is required; the maintainer decides it.
2. **Drop the test-only `_grouped_items`** (`base.py:47`, plus the `_group_by_prefix` import at
   `base.py:10` that exists only for it) and its 3 callers in `tests/test_base.py` (lines 106, 200,
   296), repointing those grouping assertions to the `render(grouped=True)` golden. A separate,
   behaviour-preserving change that alters the test count, so its own wave.
