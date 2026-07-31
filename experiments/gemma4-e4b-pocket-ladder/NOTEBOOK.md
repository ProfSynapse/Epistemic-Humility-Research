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

### 2026-07-31 -- Staging correction: split_manifest destination

First build_directions attempt failed fail-closed on a lead staging
placement error: split_manifest.json had been copied into analysis/
instead of its registered destination analysis-committed/gemma4-e4b/
(experiment.yaml instrument.staging). Moved to the registered
destination, sha256 re-verified at the new path (8d228117... exact
match), no other staged file affected, no stage produced any output
before the fail-closed stop. Side note: the failed container run left
analysis-committed/gemma4-e4b root-owned; ownership restored to the
host user via the pinned container before the move. Relaunching the
FIT stages.

### 2026-07-31 -- Stage 1 (FIT dose calibration) lead adjudication

FIT stages completed in the pinned tf550 container: build_directions,
gate_fit, calibrate_dose all ran --family gemma4-e4b --site-set pocket.
calibrate_dose exited 1; that exit is the tool's designed signal
(calibrate_dose.py:391-394 gates exit status on the mid-band arm set
only) and the summary artifact
analysis/gemma4-e4b/dose_calibration_summary.pocket.json is complete.
Adjudication is from the artifact, not the exit code.

Per-arm ruling under the registered Stage 1 rule (collapse-free rung,
FIT confab-tighten rate >= 0.5 floor, readback within tol):

- **E1/hs25: usable dose found; proceeds to Stage 2.** Four rungs clear
  the floor collapse-free (0.361 and 0.554 at rate 0.500, 0.85 and
  1.304 at rate 0.750; all cost 0.000, readback 1.000; 2.0 collapses at
  0.429). The tool selected ratio 0.85, dose 81.615.
- **E2/hs26: dose-viability NOT-RUN.** Max confab-tighten rate 0.375 at
  ratio 0.85, below the 0.5 floor at every rung. Neither a pass nor a
  fail; no re-laddering, no tuning, per the registered rule.
- **E3/hs27: dose-viability NOT-RUN.** Max rate 0.250 at ratio 0.85;
  collapse onset already at 1.304 (0.286). Same ruling.
- **hs40 (late reference): null as expected.** Max rate 0.250 with
  collapse from 0.85 up (0.667 to 1.000), matching the doubt-snap
  late-site expectation. Non-gating.

Selection-rule note, recorded so the ruling is accurate about what the
instrument did: the amendment's prose transcription reads "selects the
first collapse-free rung whose FIT clean_tighten rate clears the same
0.5 floor". The pinned tool's choose_dose() (calibrate_dose.py:99)
actually orders usable rungs by highest confab-tighten rate, then
lowest known-correct cost, then lower ratio as tie-break, with the
in-code comment "ratified selection rule". At hs25 this picks 0.85
(0.750 rate) over the first floor-clearing rung 0.361 (0.500), with
0.85 beating 1.304 on the lower-ratio tie-break. The script is
byte-identical (sha256 match verified today) to the parent quarantine
cell's pinned calibrate_dose.py, so the "transcribed rule, unchanged"
clause binds to the parent instrument's actual behavior; the prose
"first" is an imprecise paraphrase, and the tool's selection stands,
observed and not second-guessed, exactly as in the parent cell. The
usable/NOT-RUN determinations, which are the gating part of Stage 1,
are unaffected by this discrepancy: both readings agree on which arms
have a usable dose.

Consequences under the registered design: Stage 2 (run_contrast smoke,
lead verify, then full held-out G1/G2/G3) runs for E1/hs25 only, with
P1 active (conditional on E1's usable dose) and C0 baseline; E2/E3 and
their P2/P3 controls do not run. This matches the pre-registered
scoreboard expectation of dose-viability NOT-RUN deepening the D4/hs23
pattern at the deeper sites, with E1 as the only arm shallow enough to
carry a usable dose.

### 2026-07-31 -- Stage 2 smoke verified; full run launched

run_contrast.py --mode smoke completed exit 0 in the pinned tf550
container. Lead verification from
analysis/gemma4-e4b/smoke_summary.pocket.json: arms restricted to
E1/hs25 exactly as the Stage 1 adjudication requires (late arm
excluded), injected dose 81.615 with readback mean 81.492 and
frac_readback_within_tol 1.0, collapse_rate_on_dosed 0.0, confab_tighten
4/4 on the 8-row smoke slice, held-out pools present (confab 168,
known_correct_answered 270), g0_smoke_pass true. The fired-only
NOT-ADJUDICABLE disposition at n=4 is a smoke-slice artifact of the 35
floor and is non-gating. Proceeding to --mode full (held-out G1/G2/G3
for E1 with P1 and C0) per the registered sequence.
