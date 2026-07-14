# Amendment AI Artifacts

Committed provenance and result artifacts for Amendment AI, Probe-as-Reward (PAR).

- `par_recalibration.json` records the trained-lineage recalibration pass that motivated the PAR sensor refit.
- `par_mining_yield.json` records the safe row-key/count-only PAR mining yield summary.
- `par_sensor_refit.json` and `par_sensor_refit_v2.json` record the v1 and serving-aligned v2 sensor refits.
- `amendment_ai_smoke.json` and `amendment_ai_smoke_v2.json` record the honest failed v1 smoke and the green v2 launch smoke.
- `amendment_ai_pool_manifest.json` records the committed training-pool and locked holdout counts/row keys; the text-bearing pool rows stay gitignored.
- `amendment_ai_truthfulqa_audit.md` records the construct audit that excluded TruthfulQA D-over rows.
- `amendment_ai_g2_reference_grpo_v2.json` pins the pre-outcome GRPO-v2 reference panel for AI-G2.

The runnable producers live under `experiments/probe-as-reward/scripts/`.
Compatibility wrappers remain at the old `archive/experiment/phase1/probe/par_*.py`
paths for historical command lines and imports.
