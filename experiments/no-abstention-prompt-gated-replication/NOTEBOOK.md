# No-abstention-prompt gated replication (cross-family) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-28 — Launch authorization and harness-build preflight (harness-builder agent)

**PI approved launch in-session 2026-08-28 on the canonical Linux checkout**
(lead relay). Lead's host preflight (relayed): 31/31 `cell.yaml` sha256 pins
verified, pinned JSONs load, render import assertions pass, staged pools
present for all five families.

**Harness-builder's own independent preflight**, run from a dedicated worktree
(`/home/profsynapse/code/ehr-worktrees/no-abstention-run`, branch
`exp/no-abstention-prompt-gated-replication-run`, off `main` at `1ea23af7`,
submodule `synaptic-tuner` initialized at its pinned commit
`6b01834b8192d1d875db9bfce3eaa8fd9e14334c`), via
`experiments/no-abstention-prompt-gated-replication/preflight.py`:

- **31/31 `cell.yaml` sha256 pins PASS**, independently re-verified against
  the artifacts on this host (not taken on the lead's report).
- **render.py import PASS**: the pinned no-abstention render imports cleanly;
  its own module-level assertions (abstention sentence present exactly once
  in the parent prompt, deleting it reproduces the registered no-abstention
  prompt byte-for-byte) fire without error;
  `NO_ABSTENTION_SYSTEM_PROMPT` (376 chars) matches the registered text
  verbatim; `assert_no_think_scaffolding` and `render()` both present.
- **Held-out pool counts: all five families match `cell.yaml` exactly**
  (qwen3-4b confab=185/known=258; qwen3.5-4b confab=1332/known=360;
  llama-3.2-3b confab=872/known=334; mistral-7b-v0.3 confab=1312/known=382;
  gemma-4-e4b confab=168/known=270).
- **One real defect found and fixed (not a spec change).** This worktree's
  git config had `core.symlinks=false`, so the two git-symlinked gemma
  manifests (`gemma4-e4b-kv-seam-quarantine/analysis-committed/gemma4-e4b/
  {split_manifest,eval_pool_manifest}.json`, both mode `120000` pointing into
  `experiments/common/artifacts/jspace-cross-family-gemma4-e4b/`) checked out
  as plain-text files containing the literal relative-path string instead of
  real symlinks, so their sha256 initially mismatched `cell.yaml`'s pins (29/31
  PASS on first run) and `json.load` failed outright. Root-caused (not
  tuned/patched around): set `git config core.symlinks true` in this worktree
  and re-checked out only those two files (`git checkout --
  <the two paths>`); both then resolve as real symlinks to the existing,
  correctly-sized target files under `experiments/common/artifacts/
  jspace-cross-family-gemma4-e4b/` and both sha256 now match `cell.yaml`
  exactly. No parent-experiment file was edited; this was a worktree checkout
  mechanics fix. Swept the rest of `experiments/` for the same failure mode
  (`git ls-files -s` filtered to mode `120000`): only these two symlinks exist
  under `experiments/`, and both are now resolved correctly.

**Lane finding (research task, not a spec change):** the task brief
anticipated a possible local/Modal split across families. Read each cited
parent Outcome's own NOTEBOOK.md for its host/lane before assuming one:
`j-space-midband-write-sweep-qwen3-4b` (qwen3-4b) ran via "local launch";
`j-space-cross-family-layer-contrast`'s `run_contrast.py --mode full` runs for
both llama-3.2-3b (PID 1231456) and mistral-7b-v0.3 (PID 1260218) show local
process IDs, no Modal job references; `qwen35-4b-midband-doubt-snap` ran "in
the background, on the local RTX 3090"; `gemma4-e4b-kv-seam-quarantine`'s
Stage 5b full run (the D1/hs15 0.7857/0.011 result `cell.yaml` cites) ran
inside the pinned local Docker image `mechinterp-runner:tf550` (`docker ps`
confirmed), not Modal. The "Modal" mentions found in these notebooks
(`gemma4-e4b-kv-seam-quarantine`'s "Phase B Modal lane"; a Modal
row-text-retention note in `j-space-cross-family-layer-contrast`) refer to
different phases/experiments than the specific operating-point Outcomes
`cell.yaml` cites. Conclusion: **all five families' cited operating-point
generation runs were local-lane**; there is no Modal-only family for this
cell to prepare-and-wait-on. Local RTX 3090 confirmed idle (`nvidia-smi`:
13 MiB / 24576 MiB used, 0% util) before proceeding.

Proceeding to harness build for all five families on the local lane.

### 2026-08-28 — Sign-blocker closure and sign (PI-authorized in session)

The four open items from the probe entry below are closed:

1. **Render pinned.** `render.py` in this directory imports the parent render
   (`experiments/doubt-snap-cross-family-confirmatory/render.py`, sha256
   a5a0b243ea20e70ae62d081fbcdca17f0c298a0a6878ff5698e7752ef3434876) and
   replaces only the prompt global. Import-time assertions enforce that the
   abstention sentence occurs exactly once in the parent prompt and that
   deleting it reproduces the registered no-abstention prompt byte for byte;
   import smoke-tested on this machine. The two-prompt diff, in full:

   REMOVED (the only diff): `If the answer is not known to you, say
   "I don't know the answer" rather than guessing. ` (one sentence plus its
   trailing space, between "Answer the user's question. " and "Return only a
   JSON object...").

2. **Llama random seed pinned:** 910016, the next value in the parent
   census's seed series (910001..910015), disjoint from all 15 used seeds.

3. **Judge instrument pinned** in `cell.yaml` `grading.pinned_instrument`:
   detector_v2.py, detector_v2_patterns.yaml, build_adjudication_pool.py,
   apply_adjudication.py from `experiments/abstention-wide-instrument-
   calibration/`, each sha256-pinned; adjudication contract rr2-verbatim /
   context-free-agent / sharded / decoys both types, per that experiment's
   instrument block.

4. **Gate floors frozen** in `gates.yaml` with derivations inline:
   G1 floor 0.4459 (= 0.5 x qwen3-4b with-prompt lift 165/185 = 0.891892,
   no_op abstention 0 by pool construction); G1b floor 0.3595 (= 0.5 x llama
   with-prompt lift 0.719037 = 635/872 - 8/872); G2 ceiling 0.0698 (= 2 x
   with-prompt cost 9/258 = 0.034884) with adjudicability floor N = 52
   (wilson_upper(0,52) = 0.0688 < 0.0698 <= wilson_upper(0,51) = 0.0700).

PI authorization: prediction, falsifier, and gate constructions were
adjudicated by the PI on 2026-08-28 (recorded in AMENDMENT.md and the session
note); the PI then directed sign and merge in-session ("so sign it for me then
lets pr and merge"). Signed via `bin/exp sign` on the Mac checkout; the GPU
run waits for separate launch approval on the canonical Linux checkout.

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
