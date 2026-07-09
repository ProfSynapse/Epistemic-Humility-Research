# Causal-Pilot Core Config Archive

This directory archives legacy Phase 3 causal-pilot core configs formerly stored under `experiment/phase1/probe/config/`.

Migration subset: the causal-pilot core slice of `C001` from `docs/migration/phase1-probe-config-terrain.md`.

Owner decision: archive-only historical provenance for the legacy Phase 3 local causal-pilot readiness spec, runner template, full candidate inventory, local sweep plan, and changed-row diagnostic. These files remain referenced by historical sweep configs and procedural runbook text, but they are not the home for new experiment instruments.

The component group contains:

- `phase3_causal_pilot_smoke.yaml` - readiness-only smoke spec; does not authorize generation;
- `phase3_causal_pilot_gpu_smoke.yaml` - generation-enabled runner template;
- `phase3_causal_pilot_full_candidates.yaml` - full local candidate inventory;
- `phase3_causal_pilot_local_sweep.yaml` - local sweep plan using the archived runner and candidate source.
- `phase3_causal_pilot_changed_row_probability_slice.yaml` - bounded logit-only diagnostic for the two candidates that previously moved generation/top-1 rows.

New evidence-producing cells belong under `experiments/<slug>/`; shared reusable inputs belong under `experiments/common/` only after promotion by a second active experiment. This archive folder preserves the historical Phase 3 runner surface for provenance and replay.
