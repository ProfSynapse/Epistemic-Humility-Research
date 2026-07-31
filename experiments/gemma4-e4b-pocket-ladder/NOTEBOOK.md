# Gemma-4-E4B pocket ladder: hs25/hs26/hs27, sharing ON notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

### 2026-07-31 -- Signed; runtime digest recorded

Signed 2026-07-31 with both scoreboard calls entered beforehand
(orchestrator and PI, both: no direction-specific actuation; the PI call
recorded from an explicit same-day selection). Lead addition immediately
post-sign, before any run: instrument.runtime_image_digest set to
mechinterp-runner:tf550
sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8,
the transformers==5.5.0 image every gemma kv-seam-adjacent GPU verb runs
in (kv-seam NOTEBOOK 2026-07-29 build record; same image that ran C1).
Recorded per the local-runtime invariant (digest is a sibling of pins,
captured with the Desktop-engine preflight passing). No launch is
authorized by this entry; the cell awaits its own launch approval after
the IDK-switch sweep completes.

### 2026-07-31 -- LAUNCH AUTHORIZATION (user-approved) and staging execution

The PI approved launch 2026-07-31 ("launch it docker is up") after the
IDK-switch sweep resolved and merged. Docker Desktop preflight to be
verified immediately before the first GPU verb; every GPU verb runs in
the pinned mechinterp-runner:tf550 image
(sha256:479b7ca7891ab328ce7f04adffb949ef8086e3cf0d87676a3577d1d76cd845c8,
recorded in instrument.runtime_image_digest at fbd16834), IMAGE_DIGEST
env passed at docker run.

Staging contract EXECUTED per AMENDMENT.md "Staged inputs": all four
artifacts copied from the canonical checkout's harvested
gemma4-e4b-kv-seam-quarantine tree into this cell's gitignored
analysis/gemma4-e4b/, and every sha256 recomputed at staging time
matches the registered value exactly (anchor_extract.safetensors
b7197418..., anchor_extract_manifest.json 060c3f3b...,
split_manifest.json 8d228117..., eval_rows.jsonl 7a2784bd...). The two
row-text-bearing files live in analysis/ only, never
analysis-committed/. Worktree submodule initialized at the branch's
recorded gitlink (34c89fc4, the tuner rev Phase A and C1 validated).

Registered run sequence, transcribed from the design (G0-KV item 1
fail-closed inside each stage): build_directions.py --family gemma4-e4b
--site-set pocket; gate_fit.py --site-set pocket (FIT); calibrate_dose.py
--site-set pocket (Stage 1, FIT usable-dose rule, NOT-RUN on zero usable
rungs, no re-laddering); run_contrast.py --site-set pocket --mode smoke,
lead verifies, then --mode full (Stage 2, held-out G1/G2/G3);
pocket_rollup.py. cell.yaml surface.expected_config_sha is hand-filled
from the tuner's printed config_sha after the first run, per the sign
output reminder.
