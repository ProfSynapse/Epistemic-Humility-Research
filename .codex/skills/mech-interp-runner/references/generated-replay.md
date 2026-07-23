# Generated-Answer Replay

Load this when running the behavioral gate after logit diagnostics identify a
candidate.

Use generation mode only for behavior gates after logit diagnostics identify a
candidate. Generation mode supports `no_vector_baseline`,
`activation_addition`, `activation_subtraction`, and `sign_flip`.

Require generated replay before claiming:

- answer recovery,
- reduced over-refusal,
- improved calibrated abstention,
- or user-facing behavioral improvement.

Score refusal, correctness, truthfulness, and per-row deltas against baseline.
Inspect changed rows manually, especially refusal-to-answer flips.
Interpret deltas against the replay's own no-vector baseline, not only the
behavior-cell labels used to select rows. Deterministic replay baselines can
drift from the earlier scored behavior overlay, so summaries should report
baseline and intervention counts side by side.

Use the replay analyzer for completed generation sweeps:

```bash
python experiments/common/mechinterp/generation_replay_analysis.py \
  --root archive/experiment/phase1/probe/analysis/example_generation_sweep \
  --out archive/experiment/phase1/probe/analysis/example_generation_sweep/summary_latest
```

This writes `summary.json`, `summary.csv`, and `changed_rows.csv`. Treat the
automatic alias/refusal matching as triage; inspect changed rows before making
behavior claims.
