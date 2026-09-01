# Family Atlas Surface Residualization Control notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-22: Launched the signed real CPU analysis through
  `experiments/common/launch_detached.sh`. Active wrapper PID 346951 and Python
  PID 346952; log and exit-code sidecar are under this experiment's ignored
  `analysis/`. A sandboxed process check could not see the live host process,
  which prompted a second identical launcher under tmux. A host-level check
  detected both; the second process group and supervisor were terminated,
  leaving exactly one signed run. Both commands were byte-identical and shared
  the same instrument fingerprint. No threshold, endpoint, or instrument file
  changed.
- 2026-07-22: PI selected scoreboard option 1, approved signing, and approved
  the real CPU analysis launch. `bin/exp sign` pinned `cell.yaml`, `gates.yaml`,
  the analysis harness, and its focused tests. No instrument threshold or
  endpoint changed after signing.
- 2026-07-22: Scaffolded from updated `main` with `bin/exp new` as a Tier 3
  registered lab diagnostic. The decisive design uses full-population
  cross-fitted residualization and contains no matching gate. No activation
  tensor was opened and no controlled profile was computed.
- 2026-07-22: Added private reusable exhaust for fit-row alignment, surface
  matrices, and per-layer out-of-fold predictions. Only hashes, shapes,
  profiles, and gates may be promoted. Draft remains unsigned and the real CPU
  run is not authorized.
- 2026-07-22: Pre-sign source preflight passed for both substrates without
  computing a profile. Gemma joined 2,815 of 2,815 captured rows with 1,301 fit
  rows, 43 hidden states, width 2,560, and coverage 1.0. Qwen joined 1,768 of
  1,768 rows with 1,325 fit rows, 37 hidden states, width 2,560, and coverage
  1.0. The focused unit suite passed 12 tests; the synthetic hs2 plant was
  relocated with normalized deviation 0.02473 against the registered 0.05
  ceiling. These are instrument-validation facts, not experimental outcomes.

- 2026-09-01: aggregate data exhaust published (batch 4 of the backfill, task-56c61a; PI-approved in-conversation 2026-09-01). Copy-everything mirror of analysis-committed plus README + PROVENANCE; aggregate shape, no row text, zero exclusions. 3 files / ~92 KB, built at repo commit 90190c43.
- HF repo: `professorsynapse/eh-family-atlas-surface-residualization-control` (dataset)
- HF revision: `80895e395c220b6a8e0f8dec3c290987acfe057e`
