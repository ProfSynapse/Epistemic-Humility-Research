# Llama hs17 mid-band direction-specificity census notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

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
