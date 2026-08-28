# No-abstention-prompt gated replication (cross-family) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-28 — Pre-sign feasibility probe (required by AMENDMENT.md Design)

Performed by the lead session on the Mac checkout. Every value now in
`cell.yaml` was copied from a parent Outcome or committed artifact opened
during this probe; no value came from memory. Verification method: sha256 of
each artifact file plus a `json.load` of every artifact and pool manifest
(structural check, per operating rule 8).

Parent Outcomes opened and read this probe:

- `j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md` Outcome: hs23 is
  the best mid-band site (held-out 165/185 = 0.892 vs hs34 123/185 = 0.665).
- `j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md` Outcome: absolute
  setpoints hs23=25 (readback 25.0055), directions from
  j-space-midband-write-sweep-qwen3-4b.
- `qwen35-4b-midband-heldout/AMENDMENT.md` Outcome: frozen hs20 operating
  point promoted to a held-out claim; hs_index 20, dose_abs 12.6082
  (= 8 x sigma_c, gain_gated 8.0), loaded verbatim from the resolved ladder
  (`qwen35-4b-midband-doubt-snap`).
- `j-space-cross-family-layer-contrast/AMENDMENT.md` Outcome: llama best mid
  site hs17 (647/872 = 0.7420 PASS); mistral best mid site hs15
  (642/1312 = 0.4893, G1 marginal FAIL on the floor, recorded there as "not a
  collapse"); verdict INCONCLUSIVE at close-out — this cell reports mistral
  descriptively under G3 and relitigates nothing.
- `llama-hs17-direction-specificity/AMENDMENT.md` Outcome: hs17 replicates
  held-out (635/872 = 0.7282) and is direction-specific (effect ratio 8.25,
  K=15 random census seeds 910001..910015).
- `gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` Outcome: D1/hs15 is the best
  below-seam behavioural site (G1 PASS 0.7857, G2 PASS 0.011);
  direction-specificity not established for gemma (hs24/hs25 G3 FAILs per
  that Outcome and `gemma4-e4b-pocket-ladder`'s), and this cell does not
  claim it.

Artifact existence + load checks (all PASS; shas recorded in `cell.yaml`):

- qwen3-4b: `c_hat_hs23.json`, `u_d_hs23.json`, `random_direction_hs23.json`,
  `build_manifest_layers.json` (sigma_c 2.0297737163412064, decoder block 22),
  `dose_calibration_summary.json`. Role check: per the write-sweep
  PROVENANCE.md and `model_lib.py`, `c_hat` is the orthogonalized snap (write)
  direction and `u_d` the doubt (detector) direction; dose law erase_write,
  gain = setpoint / sigma_c.
- qwen3.5-4b: `directions/hs20/{c_hat,u_d}.json`, `build_manifest.json`
  (Qwen/Qwen3.5-4B rev 851bf6e8, sigma_c 1.576023489724997, tau_frozen
  -0.5897 recorded but NOT reused: threshold refits under the new prompt).
- llama-3.2-3b: `layers/hs17/{c_hat_hs17,u_d_hs17}.json`,
  `build_manifest_layers.json`, `dose_calibration_summary.json`
  (selected_doses.hs17 = 4.954897429720482 = ratio 0.361 x median_norm
  13.7255).
- mistral-7b-v0.3: `layers/hs15/{c_hat_hs15,u_d_hs15}.json`,
  `build_manifest_layers.json`, `dose_calibration_summary.json`
  (selected_doses.hs15 = 3.7646132819167275).
- gemma-4-e4b: `layers/hs15/{c_hat_hs15,u_d_hs15}.json`,
  `build_manifest_layers.shallow_ladder.json`,
  `dose_calibration_summary.shallow_ladder.json` (selected_doses.hs15 =
  173.65765096701432; cross-checked equal to
  `full_summary.shallow_ladder.json` layers.hs15.dose_target).

Frozen held-out pool checks (all manifests exist and `json.load`; held-out
counts match the parent Outcomes exactly):

- qwen3-4b: `experiments/common/doubt-gated-caution-tighten-heldout-split/
  split_manifest.json` — confab 185, known_correct_answered 258.
- qwen3.5-4b: `qwen35-4b-midband-heldout/analysis-committed/
  heldout_rows_manifest.json` — confab 1332, known_correct_answered 360.
- llama-3.2-3b: cross-family `reused_rows_manifest.json` — held-out confab
  872, known 334 (with `verified_sha256` of its own upstream reuse).
- mistral-7b-v0.3: cross-family `reused_rows_manifest.json` — held-out confab
  1312, known 382.
- gemma-4-e4b: kv-seam `split_manifest.json` — held-out confab 168, known 270
  (own fresh mine, `eval_pool_manifest.json` also pinned).

Question text is not in the repo (public-repo containment): pools reference
rows by id; row text stages privately per the parent cells' containment rules.
The run host (canonical Linux checkout) already holds the staged pools; the
launch preflight re-verifies the staging shas there before any GPU work.

Open items that BLOCK sign (left as TO_PIN_AT_SIGN in `cell.yaml`):

1. Pin this cell's `render.py` and record the two-prompt diff here (the
   deleted abstention sentence must be the only diff).
2. Pin the llama single-seed random-direction seed (no committed artifact;
   the parent census generated directions from seeds at run time).
3. Pin the exact sharded-judge configs (abstention-wide-instrument-calibration
   lineage).
4. Freeze G1/G1b numeric floors in `gates.yaml` from the parent with-prompt
   lifts, with derivations.
