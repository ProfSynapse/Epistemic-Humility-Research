# caution-install-bounded-site-sweep notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-12T16:55Z - Stage 7 trained COMPLETE (exit 0, 25/25 invocations); launching raw_base controls (lead)

All trained control invocations finished across the two crash recoveries;
analysis-committed/trained/controls_summary.json written. Descriptive
shape recorded for stage 9 (NOT adjudicated here): random-direction draws
near zero at hs19/hs34 (0/154 all draws) and hs35 (2-11/154), but
high-variance at hs23 (98, 7, 38 of 154) and hs29 (8, 29, 92 of 154);
permuted_gate uniformly ~36-41% across sites (comparable to the ~37%
dosed-row fraction); raw_write_pos_ctrl strongly depth-dependent (5% at
hs29 to 91% at hs23). Gated stage-6 rates for comparison: 87-95%.

Launching run_controls.py --substrate raw_base under the pinned image
(digest re-verified before the launch verb). This entry precedes the
launch.

### 2026-08-12T15:05Z - Second host crash killed stage 7 mid-run; relaunching trained controls (lead)

Host crashed again mid-stage-7 (no exit_code written; detached wrapper died
with the host). State: 16 control invocations complete (hs19, hs23, hs29
full sets; hs34 permuted_gate); hs34 raw_write_pos_ctrl interrupted with
129 rows persisted; all completed artifacts intact; GPU idle. Relaunching
run_controls.py --substrate trained under the pinned image (digest
re-verified before the launch verb); resume by row_key continues the
interrupted invocation. This entry precedes the launch.

### 2026-08-12T02:45Z - Host restart killed stage 7 mid-run; relaunching trained controls (lead)

The host machine restarted ~21:29 local, killing the stage-7 container
(log exit_code 125, docker-kill artifact). State assessment: 3 control
invocations complete (hs19 permuted_gate, raw_write_pos_ctrl, random_1);
random_2 interrupted with 150 rows persisted; all completed stage outputs
and the repo intact; GPU idle. run_steer resumes by row_key from persisted
output.jsonl, so the relaunch re-verifies completed runs and continues
random_2 from its written rows. Relaunching run_controls.py --substrate
trained under the pinned image, digest re-verified before the launch verb.
This entry precedes the launch.

### 2026-08-12T00:35Z - Stage 6 COMPLETE both substrates (exit 0); launching stage 7 run_controls trained (lead)

Stage 6 raw_base finished exit 0: hs23:anchor, hs23:anchor_onward,
hs29:anchor_onward all rc=0; hs29:anchor correctly NOT_RUN (dose not
selected at stage 5); analysis-committed/raw_base/held_out_summary.json
written. Stage 6 is complete on both substrates with zero smoke failures
after the three PI-approved repairs.

Launching stage 7 run_controls.py --substrate trained (permuted_gate /
random_direction / orthogonalized control runs on cells stage 6 recorded
RAN), detached under the pinned image, digest re-verified before the
launch verb; raw_base leg to follow on completion. One GPU job at a time
preserved (stage-6 container exited; docker ps checked). This entry
precedes the launch.

### 2026-08-11T23:58Z - Stage 6 trained summary WRITTEN (exit 0); F8 third-consumer fix (PI-approved); launching raw_base leg

The stage-6 trained summarize relaunch resumed from the 5 completed cells
and wrote analysis-committed/trained/held_out_summary.json, exit 0. Stage 6
trained is COMPLETE.

First raw_base launch attempt failed loudly: run_held_out.py still required
a raw_base split manifest, which does not exist by design -- the 2026-08-10
F8 wiring pass converted extract_anchor.py and dose_calibrate.py to source
raw_base rows from rep2's verified 221-row anchor pool but missed this
third consumer. Launch-prep item 2 (materialize_rows_with_text_raw_base.py)
run first: 221/221 row_keys resolved, sha recorded in its own output,
file staged world-readable under analysis/ (gitignored).

PI-approved repin (third mid-run instrument repair, same audit process):
held_out_rows() now routes raw_base through
extract_anchor._raw_base_joined_rows() -- identical sourcing to the other
two consumers, hard-failing verification included; trained path
byte-identical. exp validate passes. Launching the raw_base held-out leg
under the pinned image (digest re-verified before the launch verb). This
entry precedes the launch.

### 2026-08-11T23:32Z - Stage 6 trained cells ALL rc=0; summary-write crash fixed (PI-approved); relaunching summarize pass

The stage-6 trained rerun (20:16Z launch, post smoke-fix) completed all 5
viable cells rc=0 with zero smoke failures -- the gate-active-first fix is
confirmed in production. Every behavioral output row is on disk. The
process then exited 1 at the final step: held_out_summary.json failed
write_json fail-closed on NaN, because wilson_ci_point(0,0) returns NaN
Wilson bounds for the baseline_undosed arm's F12 fired-only block, whose
denominator is zero by construction (strength 0.0 fires no rows). This
would recur on the raw_base leg identically.

PI-approved fix (second mid-run instrument repair, same audit process):
sweep_lib.py wilson_ci_point now records the undefined case as None with
n=0; defined rates byte-identical. Pin updated with append-only repins
entry; exp validate passes. Relaunching stage 6 trained to resume from the
completed rows and write the summary (short pass, no regeneration), then
the raw_base leg. Digest re-verified before each launch verb. This entry
precedes the launches.

### 2026-08-11T17:58Z - Stage 6 smoke false-failure diagnosed and fixed (PI-approved); relaunching trained leg

Stage 6 trained (16:57Z launch) exited 0 but all 5 viable cells failed the
tuner per-cell smoke rc=4 (write_ok true, parity_ok false) and were skipped;
zero behavioral rows generated, summary recorded the refusals. Opus
diagnosis (read-only), lead-verified at source: the tuner smoke's
off-target metric reports the NATURAL projection of gate-inactive rows onto
the direction (no before/after comparison), so any gated smoke arm fails
the 1e-3 tolerance on ~1-sigma natural projections. Stage 4 passed because
its ungated arm made the check vacuous; stage 6 is the first gated arm
through this smoke. Write fidelity at selected doses is excellent
(rel. error <= 0.36% vs 5% bar). Prior in-program occurrence with the same
fix: aq-sycophancy-activation-actuator (rows sorted gate-active-first).

Fix, PI-approved this hour: run_held_out.py now sorts the generated rows
file gate-active-first so the smoke probes real write rows.
Analysis-neutral: greedy decode, batch 1, order-independent aggregation.
The stage-6 smoke is not a registered gate quantity (g0e reads the stage-4
report). Pin updated with manual append-only repins audit entry in
experiment.yaml (bin/exp repin refuses on running status by design;
convention followed verbatim); exp validate passes. Tuner-side metric fix
approved as follow-up on a submodule branch, NOT checked out into the
running environment until this cell's sequence completes.

Relaunching stage 6 trained under the same pinned image (digest re-verified
before the launch verb). This entry precedes the launch.

### 2026-08-11T17:12Z - Stage 6 launch addendum: per-substrate flag; transient GPU error

Two launch corrections to the entry below. First attempt failed at container
start with a transient NVIDIA toolkit error (nvidia-container-cli ldcache:
ldconfig terminated signal 9), immediately after the stage-5 container
exited; retry started cleanly. Second, `run_held_out.py` requires
`--substrate {trained,raw_base}` (the usage error consumed one container
start); stage 6 therefore runs per-substrate like stage 5. Trained leg
launched 16:57Z detached under the same pinned image (digest re-verified
before each attempt); raw_base leg follows on completion. Container up,
model loading.

### 2026-08-11T17:05Z - Stage 5 raw_base COMPLETE (exit 0); launching stage 6 run_held_out (lead)

Stage 5 `dose_calibrate.py --substrate raw_base` finished exit 0 in ~40 min
(launched 16:22Z). Registered two-site reference scope (hs23, hs29 x two
positions = 4 cells) all dispositioned;
`analysis-committed/raw_base/dose_disposition.json` written. Shape notes for
stage-9 adjudication (recorded, not adjudicated): hs29:anchor
NOT_RUN_no_usable_rung on raw_base as well (cross-substrate repeat of the
anchor-position pattern); hs23:anchor SELECTED on a single usable rung
(ratio 0.554) with high recorded known-correct cost at n_records=24;
both anchor_onward spans SELECTED cleanly (6 and 4 usable rungs).

Runner subagent remains dormant (same notification-loss issue); lead
launches the next stage in the signed sequence directly:
`run_held_out.py` (stage 6: held-out ladder at selected doses, every viable
cell, plus raw-base anchors) via `docker_launch.sh` under the pinned image
`unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(digest to be re-verified char-for-char immediately before the launch verb).
Pre-launch checks: GPU free, analysis dirs world-writable (verified this
morning, unchanged). One GPU job at a time preserved. This entry precedes
the launch.

### 2026-08-11T17:35Z - Stage 5 trained COMPLETE (exit 0); launching stage 5 raw_base (lead)

Stage 5 `dose_calibrate.py --substrate trained` finished exit 0 after ~5.3 h
(launched 12:16Z). All 14 site x span cells dispositioned;
`analysis-committed/trained/dose_disposition.json` written. Shape note for
stage-9 adjudication (recorded, not adjudicated here): three anchor-position
spans (hs29, hs34, hs35) report NOT_RUN_no_usable_rung; all seven
anchor_onward spans SELECTED with 4-7 usable rungs; hs23:anchor and the
remaining anchor spans selected normally.

The runner subagent's wake signal did not fire (known notification-loss
issue; lead-side watcher observed completion). Per the standing
lead-monitors directive, the lead is launching the next stage in the signed
sequence directly: `dose_calibrate.py --substrate raw_base` via
`docker_launch.sh` under the pinned image
`unsloth/unsloth@sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
(digest re-verified char-for-char this launch). Pre-launch checks: GPU free
(no experiment container up), analysis/ and analysis-committed/ world-
writable. One GPU job at a time preserved. This entry precedes the launch.

### 2026-08-11T12:14Z - Stage 4 (write_smoke) COMPLETE, both substrates, exit 0

Ran in foreground succession (bounded timeouts), standard pre-launch checks
passed before each: `write_smoke.py --substrate trained
--i-know-this-runs-on-gpu` (exit 0, all 14 site x position combos
hs{13,16,19,23,29,34,35} x {anchor, anchor_onward} passed=True) then
`--substrate raw_base` (exit 0, all 4 combos hs{23,29} x {anchor,
anchor_onward} passed=True). 18/18 site x position write-accuracy checks
passed (n_rows=8, write_rel_tol=0.05, write_abs_floor=0.5 each). Wrote
`write_smoke_report.json` under both substrates' `analysis-committed/`
dirs. G0e is stage-9 / lead adjudication scope; this records the script's
own computed pass/fail per cell. Per `smoke` block in cell.yaml, this
proves write accuracy only, not behavioral effect. Proceeding to stage 5
(dose_calibrate, GPU) -- the largest single stage by budget (~6,900
generation-equivalents), so this one launches via the backgrounded sidecar
watcher plus the 30-minute staleness fallback rather than foreground.

### 2026-08-11T12:08Z - Stage 3 FULLY COMPLETE (both substrates, all three components)

Remaining stage-3 items run in quick foreground succession (bounded
timeouts, no notification dependency -- catches completion directly):

- `alin_profile.py --substrate raw_base` (docker, pinned image): exit 0.
  A_lin hs23=0.0, hs29=0.0226 (n=221). Wrote
  `analysis-committed/raw_base/alin_profile.json`.
- `build_random_directions.py --substrate trained` (host, CPU, pure numpy):
  exit 0. All 7 sites got 3 accepted draws each under SC1 hygiene (void
  counts 3-12 per site). Wrote
  `analysis-committed/trained/random_direction_ledger.json`.
- `build_random_directions.py --substrate raw_base` (host): exit 0. Both
  sites got 3 accepted draws each (voids 4-5). Wrote
  `analysis-committed/raw_base/random_direction_ledger.json`.

Stage 3 (build_directions + alin_profile + build_random_directions) is now
complete for both substrates. Proceeding immediately to stage 4
(write_smoke, GPU) per PI priority directive -- no idle wait between
stages.

### 2026-08-11T09:24Z - Stage 3 (alin_profile, trained substrate) COMPLETE, exit 0

Launched via `docker_launch.sh alin_profile.py --substrate trained` (pinned
image, CPU compute, loads the model's final-norm + lm_head tensors only via
transformers/peft -- routed through the pinned container for environment-pin
fidelity even though it never touches the GPU compute-wise). Standard
pre-launch checks passed (digest, GPU idle, world-writable, preflight).
Completed within about a minute of model load, exit 0. A_lin (top-1
logit-lens accuracy) per site, n=3955: hs13=0.0, hs16=0.0, hs19=0.0,
hs23=0.0, hs29=0.9937, hs34=0.9992, hs35=1.0. Wrote
`analysis-committed/trained/alin_profile.json`. Recorded as computed; the
`confound_rule` (|A_lin_a - A_lin_b| > 0.10) application to specific
contrasts is stage-9 / lead adjudication scope.

Note: this stage's per-stage watcher notification was again delayed by
several hours (same class of issue), discovered only via a lead disk check
and PI-directed priority nudge. Going forward, short CPU-adjacent stages are
run with a bounded foreground timeout where practical (catching completion
directly, no notification dependency); only genuinely long GPU stages use
the backgrounded sidecar watcher, now paired with a 30-minute run-log
staleness fallback per lead instruction.

### 2026-08-11T09:22Z - Stage 3 (build_directions, raw_base substrate) COMPLETE, exit 0

Launched via the detached log+`.exit_code` pattern (CPU, direct on host,
`python3 build_directions.py --substrate raw_base`; no GPU/docker needed --
import-only, no fitting). Completed within the same minute, exit 0. Both
sites IMPORTED cleanly from `j-space-midband-write-sweep-qwen3-4b`'s
committed directions (hs23 tau=0.139240, hs29 tau=0.120912; c_hat/u_d
sha256 prefixes recorded in the log only). Wrote
`analysis-committed/raw_base/build_gate_manifest.json`. Stage 3 is now
complete for both substrates. G0c/G0d for raw_base are N/A-imported per
design (the source amendment's own G0d governs; not silently defaulted).
Formal gate adjudication is stage-9 / lead scope.

### 2026-08-11T09:25Z - Stage-3 diagnosis: NOT stalled, completed exit 0 at ~02:14-ish; lead's disk check looked in the wrong tree

Lead flagged the stage-3 (`build_directions.py --substrate trained`)
in-harness background task as apparently stalled ~7h with no visible output,
because the disk check looked under `analysis/`. Retrieved the task's
captured stdout directly: `EXIT:0`, all 7 sites (hs13/16/19/23/29/34/35)
G0c=True (two-fit reproducibility and roundtrip both pass) and G0d=True
(gate AUC range 0.9722-0.9985, floor 0.90), `n_known_fit=184
n_confab_fit=106 n_unknown_refused=3236`, and the final write line for
`analysis-committed/trained/build_gate_manifest.json` present. Stage 3
(trained) is genuinely complete, not stalled -- its outputs live under
`directions/trained/<site>/` and `analysis-committed/trained/`, a different
subtree than the GPU stages' `analysis/extract_*` outputs, which is why the
prior disk check found nothing. Formal G0c/G0d gate adjudication remains
stage-9 / lead scope; this entry records the script's own computed numbers.

Root cause of the visibility gap: the in-harness background-task
completion notification for this run was delayed by roughly 7 hours (same
class of issue as the Monitor delay on stage 2 trained), not an actual
crash or hang. Per lead instruction, going forward every stage -- CPU or
GPU -- launches via the detached-log + `.exit_code`-sidecar pattern under
`analysis/logs/` (never an opaque in-harness background task), with a
`run_in_background` Bash watcher polling that sidecar, so state is always
disk-verifiable independent of any notification path.

Stage 3 raw_base substrate had NOT yet been run in this session as of this
check: its two direction files under `directions/raw_base/hs{23,29}/`
predate this sweep's stage-1 launch by several hours (mtime 2026-08-10
11:02, before mine_pool's 18:11 resume) and no
`analysis-committed/raw_base/build_gate_manifest.json` exists, so they are
leftover artifacts from earlier launch-prep wiring (BLOCKER #8), not this
run's output. No double-run risk: launching stage 3 raw_base now via the
standard detached pattern.

### 2026-08-10T22:28Z - Stage 2 (extract_anchor, raw_base substrate) COMPLETE, exit 0

Launched 22:23:34Z via `docker_launch.sh extract_anchor.py --substrate
raw_base --i-know-this-runs-on-gpu` (container
`caution-install-sweep-extract_anchor-20260810T222334Z`), after the standard
pre-launch checks: image digest re-verified char-for-char, GPU idle / zero
other containers, world-writable dirs re-confirmed (the just-completed
trained-substrate output dir `analysis/extract_trained/` landed at 755,
owned by the container's uid 1001 and not host-chmod-able, but not in this
launch's write path so not a blocker), preflight exit 0.

Completed 22:28Z, exit code 0. 222 output files (221 safetensors +
manifest.json) under `analysis/extract_raw_base/`. Anchor pool provenance:
rep2's registered 221-row multi-source held-out confab pool. G0b
seam-continuity check: min_cos=0.9999999999999998, pass=True. Container
exited and was removed; GPU confirmed released. Both substrates are now
extracted. Formal gate adjudication is stage-9 / lead scope.

### 2026-08-10T21:24Z - Stage 2 (extract_anchor, trained substrate) COMPLETE, exit 0

Launched 20:46:20Z via `docker_launch.sh extract_anchor.py --substrate trained
--i-know-this-runs-on-gpu` (container
`caution-install-sweep-extract_anchor-20260810T204620Z`), after the standard
pre-launch checks: image digest re-verified char-for-char, GPU idle / zero
other containers, `analysis/` and `analysis-committed/` world-writable
recursively, preflight exit 0.

Completed 21:24Z, exit code 0. Captured 3955/3955 rows (capture_rate
1.0000). G0b seam-continuity check (cache-condition invariance, 32-row fixed
seeded subset): min_cos=0.9999999999999998 over 1184 (row, hidden-state)
pairs, pass=True. Outputs at
`experiments/caution-install-bounded-site-sweep/analysis/extract_trained/`
(3955 safetensors files + manifest.json). Container exited and was removed
(`--rm`); GPU confirmed released. Formal G0b gate adjudication is stage-9 /
lead scope; this entry records the script's own computed numbers only.

Note: the interval Monitor watching this stage fired correctly but its
notification was delayed (arrived only after the stage had long finished,
per a known upstream Claude Code notification-delivery issue). Per lead
instruction, subsequent stages use a `run_in_background` Bash watcher polling
the `.exit_code` sidecar / worker PID every 60s instead of the Monitor tool.

### 2026-08-10T18:20Z - Terminology annotation added to AMENDMENT.md (semantic only, no goalpost moved)

Per PI direction (2026-08-10), added the additive "Terminology annotation"
section to AMENDMENT.md recording that this cell's working label "caution"
predates the 2026-08-10 terminology ruling and renders in program prose as
"abstention install" / "answerability-gated abstention snap". Signed text,
slug, filenames, config keys, gates, question, prediction, falsifier, and
all registered constants untouched and verbatim. AMENDMENT.md is not an
sha-pinned instrument file, so no repin is involved; `bin/exp validate`
remains OK. Committed with the results PR.

### 2026-08-10T18:10Z - Host restart during Stage 1: container lost, checkpoint intact, resumed

A host restart after the main-sweep launch (prior entry, 16:50Z) killed the
Stage 1 (`mine_pool.py --substrate trained`) container that had been running.
On session resume: `docker ps -a` showed zero running GPU containers for this
cell (only an unrelated `thd-test-pg` postgres container up); `nvidia-smi`
confirmed the GPU idle (0% util, 0 MiB used, no compute processes). The
Stage 1 checkpoint (`analysis/mined_known_generations_private.jsonl`) survived
the restart intact at 906 rows.

Standing pre-launch check found one violation: `analysis/logs` was `755` (not
world-writable), while `analysis/`, `analysis/smoke`, and
`analysis-committed/` were already `777`. Fixed with `chmod a+rwx` on the
directory (directories only, via `find -type d -exec chmod`; the checkpoint
file itself is owned by the container's uid 1001 and not chmod-able by the
host user, which is expected and fine since the same container user will
reopen and append to it). No file content touched; row count reconfirmed at
906 immediately before and after the permission fix, unchanged. Preflight
(`run_sweep.py preflight`) re-passed, exit 0.

Image digest re-verified char-for-char against `cell.yaml
execution.runtime_image_digest` / `experiment.yaml instrument.runtime_image_digest`
(`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
matches local `unsloth/unsloth:latest` image id `f21629b9ae4e`). Zero other
GPU containers running; GPU idle before relaunch. Resuming Stage 1 via the
registered detached launch path (`docker_launch.sh mine_pool.py --substrate
trained --i-know-this-runs-on-gpu`); resume-from-checkpoint is the registered
behavior, verified by the live kill-resume drill earlier today (16:17Z-16:28Z
entries above).

### 2026-08-10T16:50Z - Main sweep launch: PI approved, status flipped to running

PI approved the main sweep after merging PR #432. Registered budget 16 to
26 GPU-h on the local 3090, one GPU job at a time, pinned image digest
sha256:f21629b9ae4e re-verified at dispatch. experiment.yaml status set
signed -> running before the launch verb, per the launch guard. Dispatch
state: canonical main == origin/main (40f01e35), preflight exit 0,
docker_launch.sh mode 755, analysis/ and analysis-committed/
world-writable recursively (standing pre-launch check). Stages run as
registered via docker_launch.sh. The 36 drill rows in the stage-1
checkpoint are legitimate resume state, not cleared:
resume-from-checkpoint is the registered behavior and was verified by the
drill below. Run record and gate adjudication follow at completion; this
entry and the status flip are committed with the results PR.

### 2026-08-10T16:28Z - Item-27 kill-resume drill: PASSED. Resume verified, no recompute, no duplicates, clean stop

Third attempt, after lead adjudication of the prior entry: `analysis/` and
`analysis-committed/` set world-writable recursively (`chmod -R a+rwX`,
verified zero non-world-writable directories under either tree). No file
content changed under either tree by this fix; no repin required.

**Standing launch-procedure note**, per lead instruction: a pre-launch
world-writable check on `analysis/` and `analysis-committed/` is now part
of this cell's launch procedure -- the unsloth image runs as a non-root
user (uid 1001) and any CPU staging step that recreates either directory
re-introduces default `755`, which silently breaks every incremental
checkpoint write inside the container on the next GPU launch.

Preflight re-passed (exit 0) before launch; image digest re-verified
char-for-char; 0 containers running, GPU idle before launch.

**Drill sequence and counts (row text and questions excluded; row_key
counts only):**

| Step | Time (UTC) | Units on disk |
|---|---|---|
| Launch (Stage 1, `mine_pool.py --substrate trained`) | 16:28:53 | 0 (fresh checkpoint, confirmed by container's own resume log line) |
| Pre-kill snapshot | 16:31:39 | 21, all unique row_keys, 0 duplicates |
| `docker kill --signal=SIGKILL` on the container | 16:31:42 | 24 on disk at kill time (a few more landed between snapshot and kill) |
| Container removed (`--rm`), GPU confirmed released | 16:31:45 | -- |
| Identical relaunch | 16:32:04 | container's own log: "resume: 24 known-label rows already mined (1 known_correct_answered so far)" -- exact match to the 24 on disk at kill time |
| Growth watched post-resume | 16:32:42 - 16:32:55 | 25 -> 32 |
| `docker stop` (clean stop) | 16:33:02 | 36 final |

**Integrity check on the final checkpoint file**
(`analysis/mined_known_generations_private.jsonl`): 36 total lines, 36
unique `row_key`s, 0 duplicate keys, 0 unparseable lines (file fully
loadable via `json.loads` per line). The 21 `row_key`s captured in the
pre-kill snapshot are a strict subset of the final 36 (no data loss on
already-committed rows); 15 new rows were added after the snapshot,
consistent with generation continuing without recomputing the 24 rows
that existed at kill time.

**GPU budget consumed by the drill:** roughly 5 minutes of container
uptime across the killed run (2m49s, 16:29:01-16:31:42) and the resumed
run (56s of active generation plus stop overhead, 16:32:01-16:33:02),
well under the "few minutes at most" target; well short of any stage
completion.

**Verdict:** kill -9 resume on the real registered launch path is
CONFIRMED for Stage 1 (`mine_pool.py`): the harness correctly detects
already-mined `row_key`s via `analysis/mined_known_generations_private.jsonl`
on restart, does not recompute or duplicate them, and the checkpoint file
stays loadable and unique-keyed across a hard kill. GPU released and
confirmed idle after both the kill and the final clean stop; zero
containers left running.

### 2026-08-10T16:17Z - Item-27 kill-resume drill rerun: launch succeeded, container crashed at first checkpoint write, second defect found

Rerun after lead adjudication of the prior entry: `docker_launch.sh`
executable bit restored on the canonical working copy (git mode fix
committed on a separate branch, PR #432); content hash reverified
unchanged (`2efd1f8982844bd8fc2857214ced7b6252ac7bf6a3cfa1356baf63574b79733b`,
matches the `experiment.yaml` instrument pin, no repin). Preflight
(`run_sweep.py preflight`) re-passed, exit 0. GPU idle, zero containers
running, image digest re-verified char-for-char before relaunch.

Launch this time succeeded: container `caution-install-sweep-mine_pool-20260810T161732Z`
came up on the pinned image (`f21629b9ae4e`, matches
`sha256:f21629b9ae4ed...`), model/pool loading proceeded (confab=260,
known-label candidates=10000, already_probed=400, remaining=9600, resume
state read as 0 rows already mined -- correct for a fresh checkpoint).
The container then crashed with an uncaught `PermissionError` (Errno 13)
on its very first attempt to open the incremental checkpoint file
(`analysis/mined_known_generations_private.jsonl`) in append mode --
`sweep_lib.write_jsonl_row`'s `path.open("a", ...)` call. Root cause: the
container's non-root runtime user cannot write to the host-mounted
`analysis/` directory, which is `drwxr-xr-x` (owner-only write) on this
host, not world/group-writable. This is the same permission class this
cell's own earlier feasibility-probe Stage B relaunch hit and fixed
(NOTEBOOK 2026-08-08T23:14:50Z addendum, "output-directory permission
fix," `analysis/` and `analysis-committed/` set to 777) -- but that fix
was never reapplied to this checkpoint's specific output path, or the
directory reverted since.

Consequence: zero rows were ever written to the checkpoint file (it does
not exist on disk after the crash), so no partial progress existed to
kill -9 and resume against. The container exited on its own (docker exit
code 1) before any SIGKILL was sent; GPU confirmed released immediately
after (idle baseline util/mem, matches pre-launch reading), zero other
containers left running. Zero GPU minutes usefully consumed toward the
drill's purpose (a few seconds of model/pool load only).

Per the same binding invariant as the prior entry (no harness edits;
report and let the lead adjudicate), the directory permission was left
unchanged and no chmod was applied, even though a same-class fix has
prior-run precedent in this cell's own history. Reported to the lead;
resume verification is still outstanding.

### 2026-08-10T16:11Z - Item-27 live kill-resume drill: BLOCKED at launch, zero GPU minutes, defect found

Live kill -9 resume drill attempted per lead directive (PI-approved drill;
full sweep not approved). Preflight (`run_sweep.py preflight`) passed, exit
0. Pinned image digest verified char-for-char against `cell.yaml
execution.runtime_image_digest` / `experiment.yaml instrument.runtime_image_digest`
and the local `unsloth/unsloth:latest` image
(`sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`).
Zero other containers running, GPU idle (0 processes, baseline util/mem)
before launch.

Drill target: Stage 1 (`mine_pool.py --substrate trained
--i-know-this-runs-on-gpu`), launched via `experiments/common/launch_detached.sh`
wrapping `docker_launch.sh` exactly per that script's own documented usage
pattern. Launch failed immediately: `docker_launch.sh` is not executable
(`git ls-files -s` shows mode `100644`, no +x bit, as committed in
37ca6f24). The detached wrapper's exec attempt returned exit code 126
("Permission denied") before `docker_launch.sh`'s own body ran, so no
`docker run` was ever issued: `docker ps` stayed empty and `nvidia-smi`
showed no new process and unchanged idle util/memory throughout. Zero GPU
minutes consumed, zero units mined, no checkpoint file created, no
container touched the pinned image.

Per the drill's binding invariants (no harness-file edits; a defect stops
the drill for lead adjudication rather than being worked around), no chmod
or other fix was applied. This is a mode-bit-only defect (the file's own
content hash/pin is unaffected; a `chmod +x` would not change
`instrument.pins.docker_launch.sh`), but it blocks every direct invocation
of `docker_launch.sh` documented in its own usage header, so the pinned
launch path as committed cannot currently run. Reported to the lead;
resume verification itself was never reached and remains outstanding.

Lead adjudication (2026-08-10T16:20Z): mode-bit-only defect confirmed
(`git ls-files -s` mode 100644; content byte-identical to its
`instrument.pins` sha, so no content repin is required). Ruled a
build-environment launch repair, legitimate on a signed pre-run cell:
fixed via `git update-index --chmod=+x docker_launch.sh` on the
launch-prep branch (PR #432) and `chmod +x` on the canonical working
copy so the drill can rerun. No harness content changed, no gate
quantity involved. Drill to be re-attempted after the fix.

### 2026-08-10T16:15Z - Lead review of the materialization script; pinned into the instrument

Lead review of `materialize_rows_with_text_raw_base.py` (entry below):

- Verbatim-port claim verified against
  `j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py`: loader
  control flow (filter conditions, dedupe, idx increment placement) is
  identical; the port drops only the `label` and `_nq` dict fields, which do
  not affect row_key assignment or question resolution. `norm_q` matches
  `j-space-cross-family-layer-contrast/scorers.py:norm_question` character
  for character (same HIR-prefix regex, same transforms).
- Determinism re-verified by lead rerun: identical output sha256
  `78ed2041ccde4db8ddca2b23d53c70ba1e49b5b21bb8392a2776d7815e4b4f16`,
  preflight still exit 0.
- Containment verified: output written only under gitignored `analysis/`,
  fatal paths print row_keys only, summary prints counts and sha only.
- One wording fix in the docstring (prose-hygiene term), no logic change.
- Pinned into `experiment.yaml` (`instrument.modules` + `pins` +
  `persistence`, sha256 `04726d66aa399a15a8ca0848bf714444e68ac5dec142beb6a618e02868e51c94`)
  with a repin audit entry: new staging module added post-signing, pre-run;
  pure input staging, no gate quantity or protocol constant involved.
  `bin/exp validate` OK.

### 2026-08-10T15:52Z - Launch-prep materialization complete: preflight green (exit 0)

Per PR #430's launch-prep list, items 1-3. CPU only; no GPU verbs, no docker
run, no commits (per instruction). Canonical checkout
`/home/profsynapse/code/Epistemic-Humility-Research`, branch `main`.

- **Item 1, expansion corpus, PRESENT**: F16's expansion corpus
  (`mine_pool.EXPANSION_CANDIDATES`) --
  `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl` -- confirmed
  present in this worktree (13,496 lines, gitignored). No action needed.

- **Item 2, `analysis/rows_with_text_raw_base.jsonl` materialized**: new
  script `materialize_rows_with_text_raw_base.py` (gitignored output, tracked
  script) deterministically reconstructs question text for all 221 row_keys
  in rep2's committed raw_base anchor pool
  (`experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/
  multisource_pool_manifest.json`), which is ID/role/source/category_canon
  only per rep2's own containment policy and carries no text.

  Join method: rep2's mining script
  (`j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py`) builds
  each row_key as `msrc::<source>::<idx>`, where `idx` increments only over
  candidates from the three original dataset loaders (`datasets/kuq/
  knowns_unknowns.jsonl` unknown=true, `datasets/kuq/unknowns_all.jsonl`
  deduped, `datasets/selfaware/SelfAware.json` answerable=false) that survive
  a dual-exclusion filter (against the predecessor fit/held-out split and
  rep1's fresh pool, resolved to question text via two private candidate
  caches). This script verbatim-ports `resolve_excluded_questions`,
  `load_kuq_ku_unknown`, `load_kuq_ku_unknown_x`, and
  `load_selfaware_unanswerable` from that source script (norm_question is the
  same HIR-prefix-stripping normalizer already verbatim-ported into this
  experiment's own `probe_common.py`), reading the same git-tracked dataset
  files plus the two private exclusion-resolution caches at their migrated
  locations in this checkout (`experiments/divergent-pool-own-readout/
  analysis/phase1-migrated/probe/analysis/ah_stage0/candidates.jsonl` and
  `.../expansion/expansion_candidates.jsonl`, the same file as item 1).

  Because idx assignment only increments for candidates that survive
  exclusion, an incomplete exclusion set would silently misalign every
  downstream row_key. Guarded against this: the script recomputes
  `exclusion_resolution_counts` and hard-fails unless it matches rep2's own
  manifest-recorded counts EXACTLY (`predecessor_split_keys=739,
  rep1_pool_keys=2263, union_keys=3002, resolved_to_question=3002,
  unresolved_keys=0`) -- it did, on the first run, meaning the 166 `ah::`
  keys resolved via the migrated `candidates.jsonl` matched rep2's original
  resolution exactly, not just the more numerous `ahx::` keys. Additional
  hard-fail cross-checks, all passed: reconstructed `source` matches the
  manifest's `source` for every row_key; reconstructed `category_canon`
  matches the manifest's `category_canon` for every row_key (a genuine
  content check, not just an id match); per-source counts
  (kuq_ku_unknown=139, kuq_ku_unknown_x=6, selfaware_unanswerable=76) match
  `manifest["counts"]["selected_confab_by_source"]` exactly; zero empty
  question text; all 221 resolved (zero missing). No sampling -- all 221
  row_keys included deterministically every run.

  **Materialized file**: `analysis/rows_with_text_raw_base.jsonl` (gitignored
  per this experiment's `.gitignore` `analysis/` entry, confirmed via `git
  check-ignore -v`). 221 rows, 221 unique row_keys, every row `role:
  "confab"`, zero empty `question` fields. Fields:
  `{row_key, role, question, aliases, source, category}`, matching the
  schema `mine_pool.py` writes for the trained substrate's
  `rows_with_text.jsonl` so `extract_anchor.py`/`dose_calibrate.py` read one
  shape regardless of substrate. sha256
  `78ed2041ccde4db8ddca2b23d53c70ba1e49b5b21bb8392a2776d7815e4b4f16`. No row
  text (question or otherwise) appears in this notebook entry or elsewhere
  in a tracked path.

- **Item 3, preflight**: `python3 run_sweep.py preflight` now exits 0
  (`{"ok": true, "problems": []}`), both checks it runs (F16 corpus staged;
  `rows_with_text_raw_base.jsonl` covers all 221 registered row_keys with
  `role: "confab"`) satisfied by items 1-2 above. No harness code changed to
  reach this; both preflight checks were already correctly implemented
  (Round 3's `ALSO(a)`) and simply had nothing to check against until now.

- **No harness defect observed** this pass. `git status` over the touched
  and read experiment directories shows only the new tracked script
  (`materialize_rows_with_text_raw_base.py`) as untracked; the materialized
  `analysis/` output is gitignored and does not appear. No commits made.

### 2026-08-10T21:10Z - Round 4: raw_base gate-params handoff fix (tau/mu_d/sigma_d import), stray artifact cleanup. CPU smoke re-passed.

Follow-up to the 2026-08-10T18:45Z Round 3 entry, per lead adjudication of
the delta verify's one blocker and two minors. No git operations; CPU only.

- **Governed-text note (lead action, no code change here)**: the lead
  corrected the g0b quantity wording in `gates.yaml` and `AMENDMENT.md` to
  the cache-condition-invariance quantity (matching the Round 3
  `run_seam_check` implementation, which was already correct against the
  lead's Round 3 instruction but not yet against the governed text) and
  repinned `gates.yaml` (new sha256
  `ea176dac3635efd54cd346949da776db4f0996ef6570a5a950c03bf2e252a93d`,
  `experiment.yaml` repins block, dated 2026-08-10T15:18:14Z). No seam-check
  code changed this round; the implementation now matches the governed text
  it was already anticipating.

- **BLOCKER, RESOLVED -- raw_base gate-params handoff**: `run_import_raw_base`
  wrote `provenance.mu_d_over_fit_pool` / `sigma_d_over_fit_pool` (the
  source amendment's own spelling) and no `tau` at all, but
  `gate_scoring.load_gate_params` (the shared reader, left unmodified per
  instruction) reads canonical `provenance.mu_d` / `sigma_d` and
  `manifest["sites"][site]["tau"]` -- a KeyError waiting for Stage 6/8 to
  hit it on raw_base. Fixed on the import side only:
    - `build_directions.run_import_raw_base` now maps the source's
      `mu_d_over_fit_pool` / `sigma_d_over_fit_pool` onto canonical
      `mu_d` / `sigma_d` in the WRITTEN u_d copy's provenance (source
      spellings kept alongside, not replaced); hard-fails if the source
      fields this mapping depends on are absent.
    - Added `sweep_lib.raw_base_gate_fit_params(site)`: imports `tau`
      (`tau_frozen`, Youden-J) from the SAME source amendment's own
      `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/gate_fit_layers.json`
      (already G0d-gated there), hard-failing on a missing/malformed file
      or a missing/mismatched per-site entry; records that file's sha256 in
      manifest provenance too. `raw_base_direction_import` now returns
      these fields, and `run_import_raw_base` writes `tau` /
      `tau_frozen_method` / `gate_fit_source_path` / `gate_fit_sha256`
      into each site's `build_gate_manifest.json` entry.
    - **Live-driven, not just unit-tested**: ran the REAL
      `build_directions.run_import_raw_base` followed by the REAL
      `gate_scoring.load_gate_params("raw_base", "hs23"/"hs29")` end to
      end, both COMMITTED/DIRECTIONS_DIR redirected to a tempdir (never
      touching the tracked/gitignored real paths). Both sites resolved with
      no KeyError:
      hs23: u_d.shape=[2560], mu_d=-4.706120, sigma_d=3.841707,
      tau=0.139240 (tau_frozen_method=youden_j);
      hs29: u_d.shape=[2560], mu_d=1.535061, sigma_d=10.566303,
      tau=0.120912 (tau_frozen_method=youden_j). tau values match the
      lead's cited quotes exactly (hs23 0.13924013495876808, hs29
      0.12091211815721492), re-read from the source file, not hardcoded.
      g0_overall_pass True (g0c reproducible, g0d AUC>=0.90 both sites).

- **Minor #1, RESOLVED**: `sweep_lib._load_direction_json` now checks
  vector dimensionality (== 2560, Qwen3-4B hidden_dim) and that every entry
  is numeric and finite (extended slightly past the literal "numeric
  entries" ask to also reject NaN/Infinity, since a non-finite entry is
  technically still a Python float and would otherwise pass a bare type
  check -- flagged here in case a narrower reading was intended).

- **Minor #2, RESOLVED**: `g0d_note` now interpolates the actual measured
  source AUC (`auc_neg_z_d_on_fit`) it references instead of pointing at
  the source file without quoting a number. As a direct consequence,
  `g0d_pass` is now computed from that real value (`>= 0.90`, the same
  registered floor used elsewhere) rather than hardcoded True -- both sites
  still read True (hs23 AUC 0.9905, hs29 AUC 0.9984), so this round's
  behavior is unchanged, but the gate is no longer a rubber stamp.

- **Stray artifact cleanup**: deleted the two tracked pre-run artifacts
  Round 3's live tests left behind (`analysis-committed/gate_report.json`,
  `analysis-committed/raw_base/build_gate_manifest.json`) -- premature
  outputs from CPU verification, not real run evidence. This round's
  re-drive test wrote only to a tempdir (see above); `git status` confirmed
  clean before this report (only source `.py`/`.md` modifications and the
  pre-existing untracked harness scripts, no stray artifacts).

CPU smoke (`python3 run_sweep.py --smoke-harness`) re-ran clean after this
pass: exit 0, `gpu_touched: false`, `cleaned_up: true`. No threshold, band,
count, seed, or gate definition was changed; the fix repairs the import's
handoff to `gate_scoring.load_gate_params`, which itself was left
unmodified per instruction.

### 2026-08-10T18:45Z - Round 3: seam-check correction (BLOCKER #9), raw_base directions import (BLOCKER #8), four new defects, preflight subcommand. CPU smoke re-passed.

Follow-up to the 2026-08-10T14:30Z wiring-pass entry, per lead adjudication of
the verify re-review's two blockers and four new defects. No git operations;
CPU only.

- **BLOCKER #9, RESOLVED (regression, not incremental)**: the prior seam-
  continuity check (`extract_anchor.py compute_seam_continuity`) measured
  cosine between ADJACENT hidden-state layers within one forward pass --
  the wrong quantity; real residual streams never approach the registered
  0.999 floor between adjacent layers (re-reviewer measured min 0.043 on
  healthy committed data, hard-stopping Stage 2 on GOOD data). The
  REGISTERED quantity is cache-condition invariance of the SAME hidden
  state: min cosine between the SAME row's SAME hidden state, captured
  twice via direct `transformers` forward calls
  (`output_hidden_states=True`), once `use_cache=True` and once
  `use_cache=False`, never routed through the tuner's capture path (which
  hardcodes the flag). Replaced with `select_seam_check_rows()` (seeded,
  fixed 32-row subset, `random.Random(f"{seed}:seam_check")`),
  `seam_cosine_between_runs()` (pure math, CPU-testable), and
  `run_seam_check()` (the two forward calls, reusing the already-loaded
  model/tokenizer). Floor unchanged at 0.999. CPU-smoke-tested the
  comparison math on synthetic tensors: identical-vectors case gives
  min_cos ~1.0 (passes); a deliberately perturbed layer is correctly
  identified by both value and layer index; `select_seam_check_rows`
  called twice on the same input is deterministic. GPU execution (the real
  Qwen3 forward passes) happens at launch, per instruction -- Qwen is an
  unaffected family so this should read ~1.0 there; a failure would be a
  real red flag, not an artifact of the old wrong-quantity check.

- **BLOCKER #8, RESOLVED**: "a paired replication reuses the replicated
  operating point; it never refits." raw_base's Stage 3
  (`build_directions.py`) no longer fits anything -- it IMPORTS hs23/hs29
  `c_hat`/`u_d` unchanged from `j-space-midband-write-sweep-qwen3-4b`'s own
  committed, already-gated artifacts
  (`experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/{hs23,hs29}/{c_hat,u_d}_hs{23,29}.json`).
  Added `sweep_lib.raw_base_direction_import()`: loads and validates each
  file (schema_version == mechinterp-direction/v1, non-empty vector,
  provenance.hs_index matches the requested site), hard-fails (RuntimeError)
  on any missing or malformed source; live-tested both hard-fail paths
  (missing file, hs_index mismatch) plus the real import. `build_directions.py`
  now branches to `run_import_raw_base()` for raw_base, which writes the
  imported records (unchanged, plus an `import_provenance` block recording
  source path/sha256/identity) to `directions/raw_base/<site>/{c_hat,u_d}_<site>.json`
  and a `build_gate_manifest.json` reporting `mode: "imported"` with G0c/G0d
  marked N/A-imported (not silently defaulted to pass -- G0c is verified by
  re-reading and comparing sha256, G0d notes the source amendment's own
  gate already governs). Live-ran against the real committed artifacts:
    - `c_hat_hs23.json` sha256 `50c3b580d7077ae4c5ee4496aa075e9158ae57fd168961f3d1854cddce7f1a72`
    - `u_d_hs23.json` sha256 `3565c8a16670f7fe3542cd1e26ee66bc451e08f2e40718f6ea8e26f86cb0672b`
    - `c_hat_hs29.json` sha256 `e6872569423e8cca31a61c857d27a3a89e89aa5f7061924c9ce21faa672bf692`
    - `u_d_hs29.json` sha256 `8cebdf90ccf76ada347592a6f8ab7514fb5d8a75468ec091fde8c03805e9faf6`
  Lead: these four paths need adding to `experiment.yaml` `inputs:`/pins (not
  done by this pass -- experiment.yaml is the lead's own edit per the Round
  2 convention).

- **NEW DEFECT #1, RESOLVED**: `adjudicate_gates.g3_direction_specificity`'s
  `pass` now additionally requires `gated_lift > 0 AND max_draw_lift > 0`
  (guard, not a new threshold) -- a negative-lift arm can never represent
  direction-specific installation. CPU-smoke-tested with a synthetic case
  (negative gated_lift, negative max_draw_lift, numeric ratio >= 3.0 by
  sign cancellation) confirming the guard blocks the pass the old code
  would have granted.

- **NEW DEFECT #2, RESOLVED**: a non-finite ratio (only reachable when
  max_draw_lift == 0) now serializes as the string sentinel `"inf"`/`"-inf"`
  plus an explanatory `ratio_note` field, never bare JSON Infinity.
  `sweep_lib.write_json` now passes `allow_nan=False` to `json.dumps`
  globally, raising a clear `ValueError` naming the target path if any
  caller ever tries to write a non-finite float unsanitized. CPU-smoke-
  tested both: the g3 sentinel path, and `write_json` rejecting
  `float('inf')` / `float('nan')` directly.

- **NEW DEFECT #3, RESOLVED**: `run_sweep.py`'s smoke-harness G3 assertion
  no longer re-implements the lift/ratio/guard math inline; it now calls
  `adjudicate_gates.g3_direction_specificity(substrate, ctrl=..., ho=...)`
  directly on in-memory dicts shaped like the worked example (RG1 section
  5.1: gated lift +40.9pts, draws +13.3/-7.4/+21.8pts, ratio ~1.87x FAIL),
  via a new optional `ctrl`/`ho` parameter pair on that function -- keeps
  the smoke's "never touches real analysis-committed/*" invariant (no disk
  I/O) while eliminating the second, driftable copy of the gate math.
  Re-ran the full `--smoke-harness`: ratio reproduces 1.8716 (FAIL), exit 0,
  `gpu_touched: false`.

- **NEW DEFECT #4, RESOLVED**: `AMENDMENT.md`'s status line no longer reads
  "may now launch as confirmatory-tier-2 evidence" (wrong -- this cell is
  registered Tier 2 EXPLORATORY, not confirmatory). Reworded to match the
  body's own registration: signed, may launch per its gates; Tier 2
  EXPLORATORY, results reported separately from the locked headline matrix
  and never pooled with it, a positive result is a lead requiring a
  confirmatory replication registered before running it.

- **ALSO(a), RESOLVED**: added `run_sweep.py preflight` (dedicated
  subcommand, checked before the flag-based CLI schema). Checks (1) F16's
  expansion corpus (`mine_pool.EXPANSION_CANDIDATES`) is staged into the
  worktree, (2) `analysis/rows_with_text_raw_base.jsonl` covers all 221 of
  rep2's registered raw_base anchor pool row_keys AND each carries
  `role: "confab"` specifically, not just row_key presence. The same role
  check was added to the existing hard-fails in
  `extract_anchor.py._raw_base_joined_rows` and
  `dose_calibrate.py.calibration_pool` (previously checked row_key presence
  only). Live-ran `preflight` against this worktree's current (unstaged)
  state: correctly reports both problems by name, exit 1.

- **ALSO(b), RESOLVED -- G4 overlap disclosure, made pre-run**:
  `adjudicate_gates.g4_substrate_anchor` now computes and reports
  `dose_selection_overlap`: the count and fraction of raw_base rows that
  are BOTH dose-selected-on (`dose_calibrate.py`'s calibration pool, first
  `n_confab_fit_rows` row_keys sorted) AND scored in G4's denominator (the
  full rep2 221-row pool), computed from `cell.yaml`
  `dose_ladder.calibration_pool.n_confab_fit_rows` and
  `sweep_lib.raw_base_anchor_pool()` rather than hardcoded -- live-computed
  as 24/221 = 10.9%, matching the re-reviewer's measurement exactly.
  **Two-sided caveat, disclosed here pre-run**: raw_base has no registered
  FIT/HELD-OUT split, so this overlap is structural, not a bug to fix
  before launch -- but it means the 24 dose-selected rows are not held out
  from G4's evaluation population. This can bias the observed rate EITHER
  toward OR away from the reference Wilson interval (dosing at calibration
  time could shift those 24 rows' own downstream confab rate in either
  direction relative to the other 197), not exclusively toward a false
  containment pass. The write-up must state this disclosure, not treat a
  G4 PASS as unqualified.

CPU smoke (`python3 run_sweep.py --smoke-harness`) re-ran clean after every
change in this pass: exit 0, `gpu_touched: false`, `cleaned_up: true`. No
threshold, band, count, seed, or gate definition was changed; every fix
repairs the instrument's implementation of the design already registered in
`AMENDMENT.md`/`cell.yaml`/`gates.yaml`.

### 2026-08-10T14:30Z - Final wiring pass: F8 resolved per G4 (rep2 pool), F25 resolved by repin + assertion. CPU smoke re-passed.

Follow-up to the 2026-08-10T00:00Z remediation entry, per lead adjudication
of the two gaps that entry reported unresolved. No git operations; CPU only.

- **F8, RESOLVED** (was reported-unresolved): the lead read AMENDMENT.md's
  G4 block precisely -- there is no missing raw_base mining stage; the
  registered raw_base anchor population IS rep2's 221-row multi-source
  held-out confab pool
  (`experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/
  multisource_pool_manifest.json`), the same pool G4 cites for the hs23/
  hs29 reference rates. Added `sweep_lib.raw_base_anchor_pool()`: loads that
  manifest, cross-checks its confab count against the SAME experiment's
  independently-written `full_summary.json` (both read 221; verified live
  against the real committed artifacts, not just unit-tested), hard-fails
  on any mismatch or missing file, and returns provenance (manifest sha256
  c7ccbb980ba8e9788386d69c4338f71c4ab117960fb0eea58011c1507508c456,
  identity string). `extract_anchor.py`'s `_raw_base_joined_rows()` and
  `dose_calibrate.py`'s `calibration_pool()` now source raw_base's confab
  rows from this verified pool (all `split="held_out"`, matching rep2's own
  no-internal-split methodology) instead of the old blanket "no mining
  stage" error. `extract_anchor.py` records the pool's sha256 + identity
  string into that substrate's `manifest.json`, satisfying G4's "record
  which raw-base pool it ran on."
  **Residual gap, reported not silently closed**: rep2's committed manifest
  is deliberately ID/role-only (its own containment policy) -- it carries
  no question text. `rows_with_text_path("raw_base")` still needs to be
  populated with real text for these exact 221 row_keys before a GPU stage
  can run; both call sites now verify this precisely (naming exactly which
  of the 221 registered row_keys are missing text) rather than erroring
  vaguely. Live-tested this hard-fail path against the real repo state
  (text file absent): correctly names 221/221 missing, first 5 row_keys.
  **Design call flagged for lead review**: `dose_calibrate.py`'s raw_base
  calibration pool draws its confab side from the SAME 221 rows the anchor
  arm will later evaluate at Stage 6 (no separate FIT subset), since
  raw_base has no registered FIT/HELD-OUT split and rep2's own methodology
  didn't split this pool either; known_correct_answered has no registered
  raw_base source, so `known_correct_cost` reads a fixed, harmless 1.0
  tiebreaker for every rung. Flag if a different reading was intended.
- **F25, RESOLVED** (was reported-unresolved): the lead corrected
  `cell.yaml` substrates[0] (trained) `base_model` from the raw lineage
  repo (`unsloth/Qwen3-4B`) to the actual GPU-verified load target
  (`professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit` @
  `ac361232c001af0ed5b0386b06dafc35d5cd31ea`) and ran `bin/exp repin` (new
  cell.yaml sha256
  b118c1c4a045ca3230dbe8260f0a1d4e43929c0a81abff842352303cf47fb0c2, recorded
  in `experiment.yaml`'s `instrument.repins` block). `sweep_lib.py`'s
  `base_repo_and_revision()` no longer special-cases the trained substrate
  with a hardcoded return; it now reads (repo, revision) directly from
  `cell.yaml`'s substrates block for BOTH substrates (via the same
  `substrate_config()` every other call site uses), and asserts the trained
  substrate's cell.yaml values still equal the GPU-verified recipe
  (`TRAINED_BASE_REPO_VERIFIED`/`TRAINED_BASE_REVISION_VERIFIED`), failing
  loudly if a future cell.yaml edit silently drifts from what was actually
  verified to load. Live-tested against the real repinned cell.yaml: both
  substrates resolve correctly, assertion passes.
- `experiment.yaml`'s `inputs:` gained the F16 corpus path
  (`experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl`) and the two
  rep2 artifacts this pass reads (`multisource_pool_manifest.json`,
  `full_summary.json`). Bookkeeping only, not a re-sign.

**Verification.** `python3 run_sweep.py --smoke-harness` (all 4 CPU-only
phases) exits 0. Every `.py` file in the directory re-parses cleanly. The
four pinned instrument modules were re-hashed and still match
`experiment.yaml`'s `instrument.pins` exactly. `raw_base_anchor_pool()` and
the F25 assertion were both exercised live against the real committed
artifacts and real repinned `cell.yaml` in this worktree (not just
syntax-checked), confirming both the success and hard-fail paths behave as
documented.

### 2026-08-10T00:00Z - Red-team remediation (item 27): instrument repairs, pre-data. CPU smoke re-passed.

Harness-level fixes to implement the SIGNED design as registered, per the
red-team findings report. No registered threshold, band, count, seed, gate
definition, or falsifier changed. No data existed yet; these are pre-read
instrument repairs. Per-finding, terse:

- **F1/F13** (G3 lift math): `adjudicate_gates.py` `g3_direction_specificity`
  and `run_sweep.py`'s `--smoke-harness` Phase 4 mirror both previously
  computed a raw-rate ratio (`gated_rate / draw_rate`, no baseline
  subtraction). Rewritten to the registered RG1 criterion: per-cell lift =
  rate minus that SAME cell's own undosed baseline, for `gated` and for each
  of >=3 fresh draws; ratio = gated_lift / max(draw_lift). Smoke now asserts
  the corrected formula reproduces the RG1 worked example
  (read-then-actuate.md 5.1): ratio ~1.87-1.88, FAIL -- not the old bug's
  spurious PASS shape.
- **F2** (mine_pool.py question/category source): generation records
  verifiably carry no question text (`probe_stage_b.py`,
  `probe_census_extension.py` write only
  `{row_key,label,source,completion,n_new_tokens,terminated_naturally,
  **grade}`). DEVIATION from the literal instruction ("take from the
  generation record itself"): sourced from the full expansion-candidates
  corpus (`load_all_candidates()`), which does carry question/aliases/
  category per row_key, instead. Hard-fails (nonzero exit, no partial pool
  file) if any selected row still has empty question text. Counts/
  stratification unchanged.
- **F3** (docker_launch.sh image substitution): rewrote to resolve+run
  `unsloth/unsloth@<cell.yaml execution.runtime_image_digest>` by digest,
  exit 1 if not locally present, never substitutes mechinterp-runner. The
  prior script read the pin only to print a WARNING on mismatch while
  actually launching `mechinterp-runner:local` by tag.
- **F4**: single `load_split_manifest` helper added to `sweep_lib.py`
  (`json.loads`, not `load_jsonl` which mis-parsed the pretty-printed
  manifest object as JSONL and crashed 5 downstream consumers).
- **F5**: `mine_pool.py` gained `--substrate` (required) and
  `--i-know-this-runs-on-gpu`. `split_fit_heldout.py` registered as its own
  Stage "1b" in `run_sweep.py`'s STAGES dict (string keys, new STAGE_ORDER
  list), between mining (1) and extraction (2).
- **F6**: `install_pinned_loader` gained an optional `base_revision` param,
  bound via `functools.partial` only when passed. Threaded through
  `dose_calibrate.py` (whose `run_dose_calibration` has no `revision`
  parameter at all) without touching the tuner submodule or colliding with
  `run_steer` call sites, which already pass `revision` as a third
  positional.
- **F7**: `dose_calibrate.py` readback check rewritten so a MISSING
  `readback_measured`/`readback_commanded` (unmeasured row) fails, not
  vacuously passes via `or`'s short-circuit on `None`.
- **F8**: raw_base gets its own harness-internal (non-pinned, gitignored)
  `rows_with_text_path`/`split_manifest_path` via `sweep_lib.py`; consumers
  fail loudly rather than silently reusing the trained pool. cell.yaml's
  singular `surface.rows_path`/`surface.split_manifest` pins are untouched
  (hash-pinned) and remain implicitly trained-only, matching Stage 1's
  registered scope. UNRESOLVED GAP (reported, not silently closed): no
  registered mining stage exists anywhere in AMENDMENT.md's Run Plan for
  raw_base -- its anchor-pool POPULATION mechanism needs a lead design
  decision before Stage 2+ can run for raw_base. extract_anchor.py and
  dose_calibrate.py both raise a loud, substrate-aware error naming this gap
  rather than resolving it.
- **F9**: `extract_anchor.py` gained `compute_seam_continuity()` -- min
  cosine between consecutive hidden-state-index captures, over every
  extracted row -- persisted into that substrate's `manifest.json` and read
  into `adjudicate_gates.py`'s `g0_integrity` as
  `g0b_seam_continuity_<substrate>`. Previously never computed anywhere
  despite the docstring claiming it was.
- **F10**: `adjudicate_gates.py`'s `g0f_containment` was a hardcoded string.
  Replaced with a real recursive scan of every `.json`/`.jsonl` file under
  `analysis-committed/` for the row-text field names verified present in
  this harness's own producers (question, aliases, answer_text, completion,
  prompt, generation).
- **F11**: `adjudicate_gates.py`'s `g4_holding` used `all()` over a
  filtered generator that silently returns `True` when empty (e.g. every
  raw_base anchor cell NOT_RUN). Fixed to report
  `"UNKNOWN_no_ran_anchor_cells_instrument_void"` instead of a vacuous pass.
- **F12**: `run_held_out.py`'s `summarize_cell()` now persists BOTH the full
  held-out population rate and the fired-only rate (both numerators/
  denominators) for `known_correct_answered_held_out`.
  `adjudicate_gates.py`'s `g2_selectivity` implements gates.yaml's
  headline_rule literally: fired-only rate is the headline exactly when it
  exceeds the cap while the full-population rate passes; otherwise
  full-population is the headline. Measurement only, no new threshold.
- **F14**: `run_pairs.py` now verifies readback at BOTH pair members
  against the registered `dose_ladder.readback_tolerance` per row
  (`readback_a_within_tol`/`readback_b_within_tol`), and aggregates
  `frac_readback_within_tol` into each position's summary.
- **F15**: `run_pairs.py`'s generation call now uses `**gen_kwargs` from
  `MechInterp.cli._generation_kwargs(tokenizer, GenerationContract(...))`,
  the same generation-kwargs contract every other stage script uses,
  replacing manually duplicated `max_new_tokens`/`min_new_tokens`/
  `do_sample`/`num_beams`/`return_dict_in_generate` kwargs.
- **F16**: `mine_pool.py`'s hardcoded machine-local
  `CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")`
  replaced with a repo-root-relative `EXPANSION_CANDIDATES` path (via
  `sweep_lib.REPO_ROOT`), working both on host and under the container's
  `/workspace` mount. Resolved path for the lead to pin at experiment.yaml:
  `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl`.
- **F17**: added `sweep_lib.emit_provenance_line()`, called once from
  `install_pinned_loader()` (the shared choke point every GPU-verb script
  already calls before any model load), printing one provenance JSON line
  (runtime_image_digest, python/torch/cuda versions) to stdout, which
  `launch_detached.sh`/`docker_launch.sh` already redirect into the run
  log. `unsloth/unsloth:latest --entrypoint python3` overrides
  mechinterp-runner's own `print_provenance.py` entrypoint, so this
  Python-side emission is the correct fix, not a shell-side one.
- **F18**: `docker_launch.sh` rewritten for detached launch: dropped `-it`,
  added a deterministic `--name`, `--ipc=host`, and corrected the HF cache
  mount to `/home/unsloth/.cache/huggingface` with `HF_HOME`/
  `HUGGINGFACE_HUB_CACHE` set explicitly (the image runs as non-root uid
  1001, home `/home/unsloth`; the old `/root/.cache/huggingface` mount was
  silently unreachable by the container's own HF client).
- **F19**: `AMENDMENT.md`'s status line corrected from "DRAFT (not signed)"
  to reflect `experiment.yaml`'s actual state: `status: signed`,
  `sign_blocked_on: 'CLEARED 2026-08-09T02:10Z: P2/P3/P4 passed at the
  probe ... P1 satisfied by count under the pre-stated census criterion ...
  Signing authorized.'`. `cell.yaml`/`gates.yaml` untouched (hash-pinned;
  their `# DRAFT` header comments are inert prose, not machine-read).
- **F20**: `build_directions.py` now reloads each written u_d/c_hat JSON via
  `json.loads(path.read_text())["vector"]` and compares `np.array_equal`
  against the in-memory array; `g0c_pass` requires both the two-fit
  reproducibility check AND this roundtrip check.
- **F21**: `build_random_directions.py` now reads
  `max_abs_cos_vs_c_hat`/`max_abs_cos_vs_u_d` from `gates.yaml`'s
  `g3_direction_specificity.draw_hygiene_sc1` (previously loaded via
  `load_gates()` but never used -- a hardcoded `MAX_ABS_COS = 0.015`
  constant was used instead).
- **F22**: `mine_pool.py`'s `--target-known-correct` default is now derived
  (`math.ceil(REQUIRED_TOTAL_KNOWN_CORRECT * 1.10)` = 459) from the
  registered floor and a named 10% margin constant, not a bare hardcoded
  `460`.
- **F23**: `write_smoke.py`'s `cell_ok` now also requires
  `frac_within_tol == 1.0` (gates.yaml g0e_write_readback's actual pass_if),
  not just the tuner's own coarser all-or-nothing `passed` boolean.
- **F24**: local `.gitignore` gained `generated/` (claimed gitignored by
  `materialize_configs.py`'s own docstring but never actually entered) and
  `analysis-committed/_smoke_harness/` (the one committed-tree namespace a
  `--smoke-harness --keep-smoke-artifacts` run writes into). No leftover
  smoke artifacts were found on disk at fix time.
- **F25** (trained-base repo/revision, UNRESOLVED, flagged not silently
  resolved): `sweep_lib.base_repo_and_revision()` now prints a loud
  "UNRESOLVED-F25" warning (both identifiers) the first time it resolves
  the "trained" substrate's base repo/revision, so a real run's log
  visibly carries this open question instead of masking it. Investigation
  and lead recommendation are in the delegation's final report, not
  repeated here.
- Also fixed (same bug class as F8, not separately numbered):
  `write_smoke.py`'s `probe_rows()` was hardcoded to always read the
  trained substrate's `rows_with_text.jsonl` regardless of `--substrate`;
  now uses `sweep_lib.rows_with_text_path(substrate)`.

**Verification.** `python3 run_sweep.py --smoke-harness` (all 4 CPU-only
phases: pool construction, site iteration, checkpoint/resume, report
generation) exits 0 after every fix above, including the corrected G3 lift
math (regression-asserted against the RG1 worked example). `bash -n
docker_launch.sh` and `python3 -c "import ast; ast.parse(...)"` over every
touched `.py` file pass. The four pinned instrument modules
(`probe_common.py`, `probe_stage_a.py`, `probe_stage_b.py`,
`probe_census_extension.py`) were re-hashed and match `experiment.yaml`'s
`instrument.pins` exactly -- confirmed untouched.

### 2026-08-09T02:15Z - Census COMPLETE. P1 satisfied by count (260 >= 250). All probe checks pass; signing

**Census run.** Container caution-install-probe-census-20260809b exited 0.
Output: analysis/probe_census_generations_private.jsonl (gitignored,
row-level, never committed). 3096 rows generated, exactly the registered
remainder (M_u 3496 minus the probe's 400). Zero degenerate completions,
zero capture failures (3096/3096 captured).

**Lead adjudication of the pre-stated criterion (entry 2026-08-09T00:31:22Z,
criterion unchanged).** The registered role rule (feasibility_probe.yaml
grading.roles: confab = gold-unanswerable row where the checkpoint answers)
applied to the probe file reproduces the probe's own count exactly (33 of
400), and applied to the census file gives 227 of 3096. Row keys are
disjoint between the two files (overlap 0) and their union is exactly the
full 3496-row corpus, so no row is double-counted and none is missing.

  actual_total_confab_count = 33 + 227 = 260 >= 250  ->  P1 pool floor
  reachable BY COUNT on this checkpoint and corpus (measurement replacing
  extrapolation; the registered 250 floor unchanged).

Realized census rate 260/3496 = 7.44 pct, sitting between the probe point
estimate (8.25 pct) and the trained-checkpoint SelfAware census prior
(5.75 to 6.6 pct), as the bracketing recorded at census registration
anticipated. Margin over the floor is +10 rows; the held-out arithmetic the
floor was derived from still closes (260 x 0.60 = 156 >= 150).

**Probe verdict, final.** P1 PASS (by count, per the pre-stated criterion),
P2 PASS (1844.88 >= 417), P3 PASS (capture 1.0), P4 PASS (overlap 0).
sign_blocked_on is cleared in experiment.yaml (lead edit, this entry is its
audit record). The four probe modules (probe_common.py, probe_stage_a.py,
probe_stage_b.py, probe_census_extension.py) are added to instrument.modules
with persistence declarations so bin/exp sign pins them; the stage B and
census scripts resume from their private output jsonl, hence incremental.

The main cell's sweep harness does not exist yet and will need lead hand-pins
after signing (the known sign/repin tooling gap). No sweep generation has
run and no G gate has been read; this entry resolves the feasibility probe
only. The 16 to 26 GPU-h sweep launch remains a separate PI approval.

### 2026-08-09T00:31:22Z - Full-corpus confab CENSUS extension registered (PI-approved), launching

PI approved a full-corpus census extension after the 2026-08-09T00:15:59Z
Stage B P1 FAIL, to replace the 400-row Wilson-bound extrapolation with an
exact count. This entry pre-states the design and the fixed criterion before
any docker verb runs, per the same blinding discipline as Stage B.

**What runs.** `probe_census_extension.py` generates on the REMAINING
gold-unanswerable (label `unknown`) candidates not already probed by Stage
B: M_u = 3496 total, 400 already probed in Stage B, so **3096 remaining**
(computed CPU-side just now: `total M_u = 3496`, `already probed = 400`,
`remaining = 3096`, matches `3496 - 400` exactly). Deterministic order:
remaining rows sorted by `row_key`. Same generation contract as Stage B
(max_new_tokens 200, min_new_tokens 1, greedy, eos includes `<|im_end|>`,
enable_thinking false), same first-JSON read policy, same role grading
(`confab` / `unknown_refused`) -- `probe_census_extension.py` imports
`load_model_and_tokenizer`, `generate_one`, and `grade_row` directly from
`probe_stage_b.py` rather than re-deriving them, so the two runs are the
same instrument. No answerable/known-label rows are generated by this
script -- the remaining-row set is unknown-label only, so
known_correct_answered stays exactly Stage B's 89, unchanged.

**Fixed criterion (stated here, before the census runs).** The registered
pool floor `required_total_confab: 250`
(`feasibility_probe.yaml pass_criterion.derivation`) is unchanged. This
census answers it by COUNT instead of by Wilson-bound extrapolation:

  actual_total_confab_count (Stage B's 33 confab out of 400, plus this
  census's confab count out of the remaining 3096, over the full M_u=3496)
  >= 250  -->  the P1 pool floor is reachable by count on this checkpoint
              and corpus (measurement replacing extrapolation)
  actual_total_confab_count < 250  -->  the pool floor is unreachable on
              this checkpoint and corpus; the lead records the transfer
              question as blocked by the checkpoint's own over-refusal

**Corroborating prior, recorded for context (not part of the criterion).**
The SelfAware full census on this exact checkpoint gives 5.75% [4.94%,
6.59%] three-seed answer-on-unknown, and 68/1032 on the seed-1 deployment
eval -- brackets the P1 floor's implied rate from below. Stage B's 8.25%
point estimate on 400 rows brackets it from above. The census resolves
which side of that bracket the true full-corpus count falls on.

**Launch details.**
- Config: `experiments/caution-install-bounded-site-sweep/probe_census_extension.py`.
- Container recipe: identical to the successful Stage B relaunch (`unsloth/unsloth:latest`,
  digest `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  `--gpus all --ipc=host --entrypoint python3`, HF cache mounted at
  `/home/unsloth/.cache/huggingface` with `HF_HOME`/`HUGGINGFACE_HUB_CACHE`
  set explicitly, worktree mounted at `/workspace`, output dirs already
  world-writable from the earlier fix).
- Expected wall-clock: roughly 80-90 minutes at the measured 33.47 rows/min
  (3096 rows / 33.47 rows-per-min approx 92.5 min, consistent with the
  lead's 80-90 min estimate).
- Preflight to be run immediately before the docker verb: GPU idle check,
  Docker Desktop engine + nvidia runtime check, digest char-for-char
  verification, zero other containers running (one GPU job at a time).
- Output: private `analysis/probe_census_generations_private.jsonl`
  (gitignored, resumable), public
  `analysis-committed/probe_census_extension.json` (counts/rates/throughput
  only, no row text).

### 2026-08-09T00:15:59Z - Stage B GPU run COMPLETE. Probe result: P1 FAIL, P2/P3/P4 PASS, overall FAIL

Container `caution-install-probe-stage-b-20260808e` exited code 0 at
2026-08-08T23:48:43Z. 800/800 sampled rows generated and graded (400
unknown, 400 known), zero resume needed, zero crashes. Cross-verified role
counts computed independently from the raw private generations file
(`analysis/probe_generations_private.jsonl`) against the container's own
committed `analysis-committed/probe_role_yield.json`: identical
(n_captured=800, n_confab=33, n_known_correct_answered=89,
n_unknown_refused=367).

**Throughput (measured, replaces the 20-45 min engineering estimate).**
elapsed 1434.0 s (23.9 min) for 800 rows, 33.47 rows/minute, mean 30.84 new
tokens/row.

**P1-P4 arithmetic, literal, no adjudication:**

| Check | Count | n | Point rate | Wilson lower 95% | x M_u/M_a | Product | Threshold | Direction | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| P1 confab supply | confab=33 | 400 | 0.0825 | 0.0593 | M_u=3496 | 207.47 | >= 250 | floor | **FAIL** |
| P2 known-correct supply | known_correct=89 | 400 | 0.2225 | 0.1845 | M_a=10000 | 1844.88 | >= 417 | floor | **PASS** |
| P3 capture | captured=800 | 800 | 1.0000 | n/a | n/a | n/a | >= 0.90 | floor | **PASS** |
| P4 disjointness | overlap=0 | n/a | n/a | n/a | n/a | n/a | == 0 | equality | **PASS** (carried from Stage A) |

Overall (all four must pass): **FAIL**, on P1 alone.

**Row-id manifest.** 800 row_keys (ids only, no question/answer text)
written to the gitignored `analysis/probe_row_id_manifest.txt`, sorted,
newline-joined, trailing newline. sha256:
`7827c210901f36313548e01848c0b062b0e6687fad9044f921b546af3fca96ad`.

**Containment check.** `analysis-committed/probe_role_yield.json` and
`probe_corpus_inventory.json` carry counts, rates, intervals, products, and
throughput only -- no row text, question text, aliases, or generations, per
the pinned containment scheme. Full generations (with completion text)
remain under the gitignored `analysis/probe_generations_private.jsonl`.

**Docker digest** used for this run: `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`, verified char-for-char before launch (see the 2026-08-08T23:23:28Z entry above).

No adjudication is recorded here; the lead decides whether P1's failure
blocks signing, and if so among what the pass_criterion's `fail_meaning`
names as the options (narrow to raw-base substrate, enlarge/change corpus,
or record the transfer question as unaskable on this checkpoint). The
registered pool floors (`required_total_confab: 250`) are not renegotiated
here.

### 2026-08-08T23:23:28Z - Stage B GPU relaunch (permissions fixed, item-25 released the GPU)

Relaunching Stage B under the same pre-registered spec as the
2026-08-08T23:04:36Z entry, after the 2026-08-08T23:14:50Z addendum's
output-directory permission fix. Nothing else changed: same
`probe_stage_b.py`, same seed (20260707), same 800 sampled rows from Stage A
(`analysis/probe_sampled_rows_private.jsonl`, unmodified), same substrate,
same generation contract, same pinned digest.

- Preflight immediately before this entry: GPU idle (`nvidia-smi`, 0 MiB, 0%
  util), Docker Desktop engine active with `nvidia` runtime, 0 other
  containers running, `docker image inspect unsloth/unsloth:latest --format
  '{{.Id}}'` = `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  (matches `feasibility_probe.yaml execution.runtime_image_digest`
  char-for-char), `analysis/` and `analysis-committed/` confirmed still `777`
  from the earlier fix.
- The GPU was released by the item-25 Arm A extraction per the lead's GO
  message; one GPU job at a time is in force.
- Container name: `caution-install-probe-stage-b-20260808e`.

### 2026-08-08T23:04:36Z - Feasibility probe Stage A run, Stage B GPU launch

Stage A (CPU corpus inventory) ran and completed: `experiments/caution-install-bounded-site-sweep/probe_stage_a.py`.
M_u (gold-unanswerable candidates) = 3496, M_a (gold-answerable candidates) =
10000, P4 disjointness overlap = 0 (PASS, checked against the full
`datasets/triviaqa-rc-nocontext/train.jsonl`, 138384 rows / 76521 distinct
normalized questions, a conservative superset of the WS-0 pinned 20k-row
training subset). P1/P2 arithmetic precheck: both possible (best-case bounds
3462.74 and 9904.87 against thresholds 250 and 417), so Stage B is not
preemptively blocked. 800 rows (400 unknown + 400 known) sampled uniformly
without replacement at seed 20260707 and written to the gitignored
`analysis/probe_sampled_rows_private.jsonl`. Public output:
`analysis-committed/probe_corpus_inventory.json`.

Launching Stage B (GPU, undosed baseline generation + role grading) now, per
`feasibility_probe.yaml stage_b_role_yield`:

- Config: `experiments/caution-install-bounded-site-sweep/probe_stage_b.py`,
  reading `analysis/probe_sampled_rows_private.jsonl` from Stage A.
- Seed: 20260707 (generation is greedy/deterministic; the seed governs the
  Stage A draw this stage consumes).
- Substrate: base `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`
  @ `ac361232c001af0ed5b0386b06dafc35d5cd31ea`, adapter
  `professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` @
  `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e`.
- Docker image: `unsloth/unsloth:latest`, digest
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  (verified present locally via `docker image inspect` before this entry was
  written; matches `feasibility_probe.yaml execution.runtime_image_digest`
  char-for-char).
- Expected wall-clock: 20-45 minutes (feasibility_probe.yaml's own estimate;
  this run measures the real rate).
- GPU: confirmed idle before launch (`nvidia-smi`, 0 MiB used, 0% util). One
  GPU job at a time.

### 2026-08-08T23:14:50Z - Stage B launch FAILED (output-directory permissions); fixed, NOT retried, GPU now held by another job

Addendum to the 2026-08-08T23:04:36Z Stage B launch entry above. Container
`caution-install-probe-stage-b-20260808d` (the fourth launch attempt of that
entry, after three earlier attempts failed on Hugging Face cache path/lock
permission issues under the container's non-root user and were not
GPU-billed) exited code 1 at 2026-08-08T23:11:27Z, about 3 minutes after
generation started.

**Root cause.** The base model and adapter loaded successfully (checkpoint
shards loaded, LoRA applied, `eos_ids = [151645]` resolved) and the FIRST
row's generation and grading completed. The crash was
`PermissionError: [Errno 13] Permission denied:
'/workspace/experiments/caution-install-bounded-site-sweep/analysis/probe_generations_private.jsonl'`
on the first attempted write. Cause: `unsloth/unsloth:latest` runs as
non-root uid 1001 (`unsloth`), but `analysis/` and `analysis-committed/` were
created by Stage A running natively on the host as `profsynapse` at the
default `755`, so the container user could traverse but not write into them.
This is the exact documented gotcha in
`.skills/experiment-runner/reference/local-runtime.md` ("Detached docker run
output dirs need world-write because the Unsloth container runs as a
NON-ROOT user (uid 1001)"); it was not applied before this launch.

**Rows generated: 0.** No `analysis/probe_generations_private.jsonl` file
exists on disk; the crash happened on the file's first `open("a")` call,
before any bytes were written. No partial/corrupt generation data exists to
clean up.

**Fix applied (CPU-side only, no GPU touched).** `chmod a+rwX` on
`experiments/caution-install-bounded-site-sweep/analysis/` and
`analysis-committed/` (now `777 profsynapse:profsynapse`, matching the
project's documented fix). `probe_stage_b.py` itself needs no code change:
`write_jsonl_row` and the public-output write already `mkdir(parents=True,
exist_ok=True)` before opening, so the permission fix on the two top-level
dirs is sufficient (Stage A's private-sample file and Stage A's public
inventory file are unaffected; both were already written successfully by the
native, non-container Stage A run before this).

**Status: NOT retried.** Per the lead's instruction, the GPU is now held by
the item-25 Arm A extraction (about 40-60 minutes). One GPU job at a time is
in force; this probe's Stage B will not relaunch until the lead gives an
explicit go. The exited container `caution-install-probe-stage-b-20260808d`
is left in place (not removed) for inspection; it is not consuming GPU.

### 2026-08-08 - Seventh site hs35 added pre-sign by lead adjudication of N2

The lead accepted Registration note N2 and independently verified its evidence,
so the registered search space is now seven write sites rather than six. Added:
**hs35, decoder block 34, relative depth 0.972**, the site the historical
`caution_direction_L35` hooks.

Verified evidence, one line: `c_hat_hs34.json` and `c_hat_L34.json` both carry
`layer: 33` with sigma 13.23002622164185, so the program's inherited site hooks
block 33, while
`archive/experiment/phase1/probe/steering/build_equiv_direction.py` documents
`block = layer - 1` and sets `best_layer = block`, so `caution_direction_L35`
hooks block 34, one block later. Without hs35 the sweep would not cover the site
whose claim it revises.

Files touched: `cell.yaml` (site added to the trained substrate's site list and
to the sites block, the not-registered comment removed, A_lin scope now seven
sites), `AMENDMENT.md` (Axis 1 table and prose, A_lin control, falsifier
searched-space sentence, the no-site-outside-the-registered clause, run plan
stage 2, budget section, D1 combination count, D3, N2), `gates.yaml` (new
`registered_sites` block enumerating the space the gates are scored over),
`experiment.yaml` (question). `TODO.md` is untouched; N1 remains the lead's to
apply.

Budget revised from 15 to 25 GPU hours to **16 to 26**, about 23,200
generation-equivalents up from about 21,900. The seventh site adds roughly
1,300, about 6%, because only the smoke, calibration, and held-out ladder stages
scale with site count; mining, extraction, controls, and pair count do not.

The feasibility probe is unaffected. It measures corpus yield and generation
throughput on the trained checkpoint and never touches a site: it loads no
direction, installs no hook, and its pass criterion is a function of role counts
and corpus size only. `feasibility_probe.yaml` was not edited.

hs34 and hs35 are adjacent by construction. They are reported as two distinct
reference sites and never as a swept span, since single-block resolution is not
claimed anywhere in this design.

The experiment was and remains draft and unsigned, so this is a pre-registration
refinement rather than a change to a signed space.

### 2026-08-08 - Pre-registration of the pre-sign feasibility probe (tier 3, BLOCKS SIGNING)

Instrument config: `feasibility_probe.yaml` (pinned at signing alongside
`cell.yaml` and `gates.yaml`).

**Tier and why.** Tier 3, lab notebook, per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`. Decision
question 3 routes preflight and diagnostic work to the lab notebook, and the
routing table places a preflight for a cell at tier 3. The same reference's
section "Pre-sign feasibility probe: every arm must be constructible from real
data" makes this specific check mandatory before signing, and records that it is
allowed and required even under a self-blinding rule, because self-blinding
forbids computing the result before signing and does not forbid confirming that
an arm can be built. That section also names the failure this rule exists to
prevent: the M4 cell defined an arm consuming a field that did not exist on its
test population, and the gap survived both signing and a full pre-sign red team
because nobody checked coverage.

**What is in doubt.** The main cell's G0a requires 150 held-out confab rows and
250 held-out known_correct_answered rows on the trained clean-SFT to GRPO-v2
checkpoint. That checkpoint over-refuses. A checkpoint that refuses may
confabulate too rarely to fill a confab pool, and may answer answerable
questions too rarely to fill a known-correct pool. Role labels are
behavior-dependent and cannot be ported from the raw-base pool
(`.skills/mechinterp-cells/reference/read-then-actuate.md`, section 1.1), so the
existing raw-base counts say nothing about this substrate. Both populations are
therefore at risk and both are probed.

**Blinding boundary, stated before the run.** The probe may compute role counts
and rates, corpus inventory counts, capture rate, and generation throughput. It
may not compute any steered quantity, any direction fit, any gate AUC, any tau,
any tighten rate, or any AUROC. Computing any of those would consume the main
cell's blind, and the probe's outputs would stop being coverage.

**Arms.** One. An undosed baseline: unsteered greedy generation, graded for role
labels. No direction is loaded and no hook is installed anywhere in this probe.

**Stages.**

| Stage | Device | What it does | Output |
|---|---|---|---|
| A, corpus inventory | CPU | counts available gold-unanswerable rows (M_u) and gold-answerable rows (M_a); verifies zero overlap with the training pools consumed by this lineage | `analysis-committed/probe_corpus_inventory.json` |
| B, role yield | GPU | draws 400 gold-unanswerable and 400 gold-answerable rows uniformly without replacement at seed 20260707, generates undosed, grades roles, records throughput | `analysis-committed/probe_role_yield.json` |

Stage B's generation contract is identical to the main cell's
`surface.generation`, so role labels come from the same instrument the main cell
will use. The role read policy is asserted as first-JSON rather than inherited,
because the grader can read the whole completion and let trailing prose reach a
role label; the gemma family atlas recorded 22 of 2815 split rows disagreeing
between the two reads.

**Why n = 400 per population.** The Wilson 95% half-width at n = 400 is about 4.0
points at p = 0.20 and about 2.1 points at p = 0.05, which is enough precision to
decide whether the corpus can supply the required pool. Drawn rows are recorded
by id so the main cell's Stage 1 mining reuses these generations rather than
repeating them, which makes the probe cost recoverable rather than additional.

**Token budget.** 800 rows at `max_new_tokens` 200 with `min_new_tokens` 1, so a
worst case of 160,000 new tokens and a realistic figure well below that, since
well-formed JSON answers terminate early.

**GPU minutes: 20 to 45, estimated.** This is an engineering estimate, not a
governed number: no governed document in this repository records wall-clock for
the predecessor cells, so no measured rate exists to cite. The estimate assumes
batched greedy generation of a 4B bf16 model on the local 3090 at roughly 25 to
50 rows per minute, plus one model load. Stage B is instrumented to record its
own measured rows-per-minute and mean new tokens precisely so this estimate can
be replaced by a measurement, both here and in the main cell's run plan.

**Pass criterion, fixed before the run.** Derivation: FIT_FRAC is 0.40, so
held-out is 60% of a pool; 150 held-out confab requires 250 total, and 250
held-out known-correct requires 417 total.

| Check | Expression | Direction |
|---|---|---|
| P1 confab supply | `wilson_lower_95(confab / 400) * M_u >= 250` | floor |
| P2 known-correct supply | `wilson_lower_95(known_correct / 400) * M_a >= 417` | floor |
| P3 capture | answer capture rate on probed rows `>= 0.90` | floor |
| P4 disjointness | training-pool overlap count `== 0` | equality |

The Wilson lower bound is used rather than the point estimate, so the probe
passes only if the corpus supplies the pool at the pessimistic end of the
estimate. P3 is the atlas AG0a bar: a checkpoint that cannot be cleanly mined
stops here.

**Disposition.** All four checks pass: signing of the main cell is unblocked,
and the measured throughput replaces the engineering estimate in the AMENDMENT
run plan. Any check fails: the main cell is not signed in its current form, the
counts are recorded here, and the lead chooses among narrowing the cell to the
raw-base substrate, enlarging or changing the corpus, or recording the transfer
question as unaskable on this checkpoint. The registered pool floors are not
lowered to obtain a pass.

**Containment.** Committed outputs are counts, rates, intervals, and throughput
only. Question text, aliases, gold answers, and generations stay under the
gitignored `analysis/` directory.

### 2026-08-08 - Draft registration filled

`AMENDMENT.md`, `experiment.yaml`, `cell.yaml`, `gates.yaml`, and
`feasibility_probe.yaml` filled from the session design draft (docs/preparation working file, not a
tracked artifact; superseded by this registration), under the lead's
adjudicated decisions: corrected transfer framing, substrate option (c), the
six-site search space, feasibility probe required and blocking, and the
superseded disposition for the un-re-derivable paper 3 section 6 citation.
Status stays draft. Three design questions were resolved at registration and are
recorded in `AMENDMENT.md` under "Design decisions at registration": calibration
pool size (D1), gate site co-located with write site (D2), and site naming
across the two index conventions (D3). Two items need the lead and are recorded
under "Registration notes for the lead": the burn-down row 27 wording (N1) and
the finding that the historical write site is one decoder block later than the
program's inherited site and therefore sits outside the adjudicated search space
(N2).

## 2026-08-12T20:40Z — Mid-run repair #4 (PI-approved, Option B): raw_base pos_ctrl readout import in run_controls.py; raw_base controls relaunch

Stage-7 raw_base controls (launched 20260812T190559Z) exited 1 after 1
completed invocation (hs23 permuted_gate, preserved on disk):
FileNotFoundError on `directions/raw_base/hs23/source_directions/pos_ctrl_hs23.json`.
Root cause is the fourth F8-class raw_base consumer gap: run_controls.py
built the pos_ctrl readout path unconditionally under the local
`directions/<substrate>/<site>/source_directions/` tree, but raw_base never
fits pos_ctrl — BLOCKER #8 import posture; build_directions.py writes no
raw_base `source_directions/` by design.

PI presented two options; approved Option B ("b is fine"): route the
raw_base pos_ctrl readout to the SOURCE amendment's committed, already-gated
artifact `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/<site>/source_directions/pos_ctrl_<site>.json`
— the same import-not-refit pattern already used for c_hat/u_d via
`sweep_lib.raw_base_direction_import`. The registered orthogonalization
control (AMENDMENT Controls) carries no substrate carve-out, so this keeps
the full control battery on both substrates. Trained path byte-identical.
No threshold, band, seed, or gate touched.

Repin (manual append-only entry, `bin/exp repin` refuses on running
status): run_controls.py 48d2f0fd → 28d867ca. `exp validate` OK (109).
CPU smoke-harness pass OK (0.11s, gpu_touched false).

Relaunching stage-7 raw_base controls now (same image digest, verified
below; resume-by-row_key skips the completed hs23 permuted_gate rows).

## 2026-08-12T23:20Z — Stage-7 raw_base controls COMPLETE; stage-8 lead adjudications; stage-8 trained launch

Stage-7 raw_base controls finished clean (all invocations rc=0, container
exited, `analysis-committed/raw_base/controls_summary.json` written).
Cells: hs23:anchor, hs23:anchor_onward, hs29:anchor_onward RAN;
hs29:anchor NOT_RUN_no_held_out_run (consistent with the stage-6
disposition). Repair #4's imported pos_ctrl readout ran clean at all
three cells (smoke passed each time). Counts (confab clean_tighten /221):
hs23:anchor permuted 117, pos_ctrl 78, random [5, 67, 68];
hs23:anchor_onward permuted 192, pos_ctrl 187, random [64, 44, 83];
hs29:anchor_onward permuted 200, pos_ctrl 61, random [48, 3, 23];
baseline_undosed 6/221 everywhere. Stage 7 is now complete on BOTH
substrates.

Stage-8 lead adjudications of run_pairs.py's two flagged ambiguities
(protocol interpretation, lead scope; no registered quantity moved):
1. Magnitude split: EQUAL split of the best single site's calibrated
   setpoint across the two members (setpoint/2 each, converted to each
   site's own gain). The registration (cell.yaml multi_site.magnitude_match;
   AMENDMENT Axis 4) binds only that TOTAL commanded displacement is
   magnitude-matched to the best single site with readback verified at
   both members; equal split is the plainest reading of "split across".
2. Partition and ranking: in-band = site-table status `new_in_band`
   (hs13/hs16/hs19) per the registered site-table vocabulary — hs23
   `anchor_band_upper_edge` is NOT in-band; rank key =
   fit_confab_clean_tighten (the key the registered dose selection_rule
   already uses); lowest/highest = relative_depth.
3. Substrate scope: pairs run on TRAINED only. Axis 4's eligibility is
   "cleared dose viability on Axis 3"; raw_base doses are imported per
   BLOCKER #8, never Axis-3 calibrated, so raw_base sites cannot be
   eligible, and the axis's question (bounded search for transfer) is a
   trained-lineage question. Budget row 8 (3 pairs x 400 rows) carries no
   raw-base term.

Launching stage 8 `run_pairs.py --substrate trained` now (same pinned
image digest, verified at launch).

## 2026-08-13T00:05Z — Stage-8 pairs COMPLETE (trained); pair-1 NOT-RUN disposition; stage-9 adjudication next

Stage 8 ran clean (exit 0, 15 min, pairs_summary.json written). Eligible
sites: hs19, hs23, hs29, hs34, hs35 (Axis-3 dose-viable, per
dose_disposition.json).

Pair dispositions:
- best_in_band_x_second_best_in_band: NOT-RUN, insufficient in-band
  viable sites (only hs19 of the in-band trio hs13/hs16/hs19 cleared
  Axis-3 dose viability; the registered insufficient-sites disposition
  applies to this rule). run_pairs.py silently omits the pair from
  pairs_summary.json rather than recording NOT-RUN; disposition is
  recorded HERE as the governed record. No gate scores on pairs
  (G3 companion reporting only), so no pin change warranted mid-run.
- best_in_band_x_best_out_of_band: hs19 x hs23, equal-split setpoint
  33.90 each, readback within tolerance 1.0 at both members.
  confab clean_tighten: anchor 6/149 (4.0%), anchor_onward 148/149
  (99.3%).
- lowest_eligible_x_highest_eligible: hs19 x hs35, equal-split setpoint
  66.55 each, readback within tolerance 1.0 at both members.
  confab clean_tighten: anchor 8/149 (5.4%), anchor_onward 149/149
  (100%).

All GPU stages (4-8) of the item-27 sequence are now complete on both
substrates. Proceeding to stage 9 `adjudicate_gates.py` (CPU, G1-G4
scoring). Gate adjudication and verdict are lead scope; verdict lifts to
the PI.

## 2026-08-13T00:45Z — Stage-9 adjudication (lead): gate verdicts, G4 position adjudication, falsifier disposition

`adjudicate_gates.py` ran clean (CPU); `analysis-committed/gate_report.json`
written. Lead adjudications on the report:

1. G0 integrity: ALL PASS both substrates (incl. containment scan, 20
   files, 0 violations).
2. Dose viability: 5 trained cells SELECTED (all anchor_onward);
   every non-selected cell is a recorded NOT_RUN_no_usable_rung WITH its
   full 8-rung table in dose_disposition.json (verified for all 14
   trained + 4 raw_base cells). The gate_report "reading" completeness
   condition is satisfied.
3. G1 actuation: PASS at all five selected cells (rates 0.870-0.955,
   Wilson lower 0.808-0.909, n=154). The registered prediction's G1
   clause ("no registered site and position clears G1") is WRONG.
4. G2 selectivity: NOT-ADJUDICABLE (vacuous) at all five cells:
   n_fired_known 4-20, below the registered floor of 35 (AMENDMENT
   G2 three-way disposition). Per registration, this may not be cited as
   evidence of harmlessness.
5. G3 direction specificity: PASS at hs35:anchor_onward only
   (ratio 12.18 >= 3.0). FAIL hs23 (1.50) and hs29 (1.52). FAIL hs19 and
   hs34 under the pre-registered positivity guard (2026-08-10, NEW
   DEFECT #1 in adjudicate_gates.py: max_draw_lift == 0 cannot evidence
   a 3x-over-noise-floor claim); their draw lifts were all exactly 0.
6. G4 substrate anchor: HOLDS — lead adjudication on position scope.
   The published reference rates (rep2 194/221, 205/221) were produced
   with the write applied anchor_onward
   (j-space-layer-contrast-rep2-multisource/AMENDMENT.md line 177:
   "Fired rows receive the frozen c_hat erase-write at the calibrated
   setpoint, anchor_onward"). The paired-replication comparison G4
   registers is therefore defined at anchor_onward only:
   hs23 0.8824 IN [0.8281, 0.9147]; hs29 0.9140 IN [0.8856, 0.9549].
   The raw_base hs23:anchor cell (0.5385) is an operating point the
   source never published; it is recorded as an exploratory positional
   variant, NOT a G4 quantity. The script's g4_holding=false ANDed
   containment across positions including this unregistered comparison;
   the adjudicated G4 verdict is HOLDS. No goalpost moved: the gate's
   registered quantity is reproduction of the published rates, which
   exist only at anchor_onward.
7. Falsifier: DOES NOT FIRE. The only G3-passing cell
   (hs35:anchor_onward) has G2 NOT-ADJUDICABLE, and the falsifier
   requires G1 pass AND adjudicable G2 AND G3 pass at one registered
   cell. No cell satisfies the conjunction.
8. dose_selection_overlap disclosure (24/221 = 10.9%) carried in the
   report per the 2026-08-10 pre-run NOTEBOOK caveat.

Net reading lifted to the PI: paper 3's bounded-search statement is NOT
overturned (falsifier silent), the instrument is valid (G4 holds), but
the registered prediction failed its G1 clause — installation actuates
at every viable site at the anchor_onward position (87-95%), with
direction specificity clearing at one site (hs35) and selectivity
unmeasurable at these firing rates. Exploratory lead; promotion requires
confirmatory replication per the registered rule. Resolution wording and
terminal status await PI decision.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 1 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 23 files / ~0.77 MB, built at repo commit b642b7c6.

- HF repo: `professorsynapse/eh-caution-install-bounded-site-sweep` (dataset)
- HF revision: `e6e7dea57cf4ca06e046f70e5201648039088d28`
