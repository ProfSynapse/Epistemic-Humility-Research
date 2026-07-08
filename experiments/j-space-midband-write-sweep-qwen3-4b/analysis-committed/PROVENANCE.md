# J-Space Mid-Band Write Sweep Provenance

This experiment is a local raw-base Qwen3-4B layer-site sweep for the resolved
`doubt-gated-caution-tighten` mechanism. It refits the doubt gate and caution
snap direction separately at hs23, hs26, hs29, and hs34, then compares the best
J-space mid-band layer against hs34 on the predecessor held-out surface.

Committed public inputs:

- `experiments/common/doubt-gated-caution-tighten-heldout-split/split_manifest.json`
  is the promoted ID-only FIT/HELD-OUT manifest from
  `doubt-gated-caution-tighten`.
- `experiments/common/doubt-gated-caution-tighten-heldout-split/PROVENANCE.md`
  records the promotion and containment rule.
- `experiments/doubt-gated-caution-tighten/analysis-committed/full_summary.json`
  is cited as the predecessor resolved result, not used as row text.

Local private/runtime inputs:

- Question text is materialized at run time from the private HF dataset
  `professorsynapse/eh-al-prep-staging`, file
  `pools/a0_pool_v21_questions.jsonl`.
- Known-correct aliases are read from local canonical AH-A0/mined-row scratch,
  following the predecessor materialization scheme.
- Runtime row text is written only to gitignored
  `experiments/j-space-midband-write-sweep-qwen3-4b/analysis/rows_with_text.jsonl`.

Committed outputs after a run:

- Per-layer fitted direction JSONs under `analysis-committed/layers/`.
- `analysis-committed/build_manifest_layers.json`.
- `analysis-committed/gate_fit_layers.json`.
- `analysis-committed/smoke_summary.json`, promoted after the pre-outcome G0
  stop. No full held-out summary exists for this run.

Containment:

- Do not commit question text, aliases, raw generations, answer text,
  safetensors activation scratch, or row-level scored generations.
- `analysis/` remains gitignored and is the only place row text/materialized
  runtime pools should live.
