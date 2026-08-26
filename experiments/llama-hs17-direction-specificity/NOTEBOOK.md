# Llama hs17 mid-band direction-specificity census notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-25 — full run complete, gates adjudicated, resolved

Full 17-arm run on the local RTX 3090 (lane approved at sign). Terminal state:
`analysis-committed/llama-3.2-3b/specificity_summary.json`. LG-G1 PASS
(0.7282), LG-G2 PASS (ratio 8.25), LG-G3 NOT-ADJUDICABLE (KU fired 0/334, the
pre-stated expected disposition). Lead independently re-derived every gate
number from the raw per-arm runlogs (`analysis/llama-3.2-3b/runlog/
hs17_specificity/`, gitignored scratch) — exact match with the summary.
Verdict and full table in `AMENDMENT.md` Outcome.

Run incidents (harness-level, no design change, no goalpost movement):

1. **Crash 1 — backends import.** First launch died at model_lib render:
   `ModuleNotFoundError: backends`. Cause: the parent's `render.fn =
   'backends:render_probe_prompt'` resolved against an untracked scratch
   `backends.py` that no longer existed; the smoke stub had bypassed
   `run_one_row` so the smoke could not catch it. Fix: runner binds the
   tracked `experiments/common/knowledge_probe/backends.py` onto `sys.path`
   with a fail-closed existence check; verified with a real render before
   relaunch.
2. **Crash 2 — tuner readback device bug.** Arm 0 completed (1206 rows);
   arm 1 row 1 died with a cpu/cuda `RuntimeError` in
   `MechInterp/intervention/hooks.py` — the pre-edit readback snapshot cast
   `self.direction` to float64 without moving it to the hidden-state device.
   One-line fix mirroring the existing device-align pattern; Synaptic-Tuner
   PR #154 (branch `fix/readback-pre-proj-device`, commit 3a21774d). This
   worktree's submodule WORKING TREE is checked out at the fix commit; the
   gitlink is deliberately unchanged until that PR merges.
3. Relaunch resumed from per-arm runlog checkpoints (arm 0 not re-run) and
   proceeded cleanly through all 17 arms on the fixed code path.
4. **Monitor false alarm at completion**: the lead's watch expected the
   summary at `analysis-committed/specificity_summary.json` but the runner
   writes `analysis-committed/llama-3.2-3b/specificity_summary.json`, so a
   STALL fired after the post-write quiet period. State verified on disk;
   run had completed normally. Lesson: watch conditions should match on
   artifact name anywhere under the committed dir, not a hardcoded path.

### 2026-08-25 — pre-sign feasibility probe (required before sign)

Every arm confirmed constructible from committed data (verified by direct
artifact read in the primary checkout, lead session):

- Frozen directions exist: `analysis-committed/llama-3.2-3b/layers/hs17/u_d_hs17.json`,
  `c_hat_hs17.json` (plus pos/neg controls) in the parent tree.
- Dose recoverable: `full_summary.json /layers/hs17/dose_target = 4.954897429720482`,
  `readback_mean = 4.968763927602852`.
- Standardization/gate: `build_manifest_layers.json` (hidden_dim 3072),
  `gate_fit_layers.json` present.
- Row pools: `reused_rows_manifest.json` — confab_held_out 872,
  known_correct_answered_held_out 334; parent primary result cross-checked
  647/872 = 0.7420 (`full_summary.json /primary/best_mid_confab_clean_tighten`).
- Gap the design covers: the parent committed NO undosed held-out
  clean_tighten baseline → arm 0 (undosed baseline) is registered to supply
  the lift denominator. Self-blinding intact: no result computed, only
  existence/coverage checked.
- Random-arm recipe reproducible: `np.random.RandomState(seed).normal`,
  unit-normalized (matches the committed 4.5-cell draw's recorded recipe);
  census seeds 910001..910015 pre-registered in `gates.yaml`, disjoint from
  historical seed 20260707.

- (add dated entries as the experiment progresses)
