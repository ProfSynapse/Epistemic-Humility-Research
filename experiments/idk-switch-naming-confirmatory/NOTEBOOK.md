# idk-switch-naming-confirmatory notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-31 -- Lead ruling: runtime_image_digest repin (capture-error repair)

`instrument.runtime_image_digest` is repinned from
`sha256:0421dc9cf32691bd0f093eb153b9e900f2be418cdd466f341d598415a92657ee` to
`sha256:fe732c8fb4c82ea1a1acd1df3766a6fe854de750f1416d934e3c66231dfff801`.

Why: `unix:///var/run/docker.sock` in this WSL distro is backed by two
different daemons depending on whether Docker Desktop is running (see
mechinterp-cells `reference/modal-launch.md`, "One socket, two Docker
daemons"). The sign-time capture ran `docker image inspect
mechinterp-runner:local` while Docker Desktop was CLOSED, so it answered
from the WSL-native dockerd's separate image store and pinned an image that
appears in no build record anywhere in the program (grep for the old digest
across all NOTEBOOKs and logs: zero hits). The validated runtime this
amendment's prose intends ("the pinned mechinterp runner container") is the
Desktop-store build recorded in
`experiments/gemma4-e4b-kv-seam-quarantine/NOTEBOOK.md` (2026-07-29 entry):
rebuilt with `accelerate==1.14.0` after Synaptic-Tuner PR #148 / EHR PR
#353, tuner revision `61899a29c11a60edba9d0a0b35c56d0a20b07d75`,
`transformers==5.12.1`, and the runtime that executed all of kv-seam
Phase A.

Verification performed before this ruling (2026-07-31, Desktop open,
`docker info` shows `Operating System: Docker Desktop` with `nvidia` under
`Runtimes`): `docker image inspect mechinterp-runner:local` returns
`sha256:fe732c8f...`; an in-container smoke printed the entrypoint
provenance line (`torch 2.9.1+cu128`, `transformers 5.12.1`,
`image_git_revision 61899a29...`, `cuda_available true`) and `nvidia-smi`
saw the RTX 3090. These values match the kv-seam NOTEBOOK build record
exactly.

Scope: manifest field only. No gate, seed, arm, or instrument-file change;
all 17 `instrument.pins` sha256s are untouched. This is a pinned-surface
repair under the standing discipline (pinned-surface changes are lead
decisions, recorded with reason), correcting the recorded value to the
image the signed prose already describes, not a substitution of runtimes
after the fact: no generation stage has run yet (only the CPU row
materialization), so nothing has executed in either image under this
registration.

### 2026-07-31 -- Launch: smoke then full generation sweep, local 3090

PI launch authorization on record 2026-07-31 ("Let's run c1 locally and
queue up idk for after it"); C1 completed and the kv-seam cell resolved
(PR #365) the same day, so the queue condition is met. Preflight passed
immediately before launch per the one-socket-two-daemons rule: docker
info shows Operating System: Docker Desktop with an nvidia runtime, and
mechinterp-runner:local inspects to the signed (repinned) digest
sha256:fe732c8f... Sequence: pipeline.py smoke (instrument validation,
tiny row set), lead verifies the smoke artifact, then pipeline.py
generate (4 arms x 400 rows, sampled decode, seed 20260802), which
hard-halts before the judge lane per the registered governance boundary.
Run logs under analysis/runlog/; provenance line required in each log.

### 2026-07-31 -- Lead ruling: second runtime_image_digest repin (dependency repair)

`instrument.runtime_image_digest` repinned from `sha256:fe732c8f...` to
`sha256:894cb31b87d87092b249ef6abfb00791e5b3b824dff6c5bd61cdbecfb04887a7`.

Why: the first in-container smoke attempt failed at
`from MechInterp.config import ...` with `ModuleNotFoundError: pydantic`
(run log analysis/runlog/, two attempts: the first also surfaced the
uninitialized synaptic-tuner submodule in this worktree, since checked
out at the recorded gitlink 34c89fc4). The shared runner image never
carried pydantic; every earlier consumer of MechInterp.cell ran under
the naming battery's documented base-conda deviation
(write-direction-naming-battery AMENDMENT.md:272-273), which had it.
Fix follows the accelerate precedent exactly (kv-seam NOTEBOOK
2026-07-29): pydantic==2.12.4 added to the shared, project-agnostic
Dockerfile (Synaptic-Tuner PR #150, commit 49cebc2b), image rebuilt
with that revision as build-arg, in-image verification `pydantic
2.12.4`. No pip-install-into-running-container (the README's named
anti-pattern). Preflight before the digest capture per the
one-socket-two-daemons rule: docker info showed Operating System:
Docker Desktop with the nvidia runtime.

Scope: manifest field only, same as the first repin; all 17 instrument
pins untouched; no generation stage has run (both smoke attempts died
at import, before model load).

### 2026-07-31 -- Repin: pipeline.py directions path (bin/exp repin, audit-trailed)

Third smoke attempt failed at load_directions:
FileNotFoundError on write-direction-naming-battery/analysis-committed/
directions/hs20/c_hat.json. Build-time ruling 5 established at sign that
the naming battery never committed a directions/ tree and corrected
cell.yaml and experiment.yaml inputs to the committing cell
(qwen35-4b-midband-doubt-snap), but pipeline.py's hardcoded
directions_dir constant was missed by that correction and by the lead's
pre-sign review. Fix: DOUBT_SNAP_COMMITTED constant, directions_dir
repointed; no other logic touched. CPU suite 30/30 after the change.
Repinned via bin/exp repin (pipeline.py fc4b7d93 -> 211e6f23, reason
recorded in instrument.repins). No generation has run; all three failed
smokes died before model load or at artifact load, touching no rows.

### 2026-07-31 -- Third runtime digest repin: gcc for triton JIT

Smoke attempt 4 (analysis/runlog/) failed inside fla's l2norm kernel with
triton "RuntimeError: Failed to find C compiler": triton JIT-compiles its
CUDA driver utils and the flash-linear-attention kernels for Qwen3.5's
gated-deltanet layers at first use, and the runner image carried no C
compiler. This never surfaced in the parent because the naming battery
ran on the local base conda stack, not in the container (parent
AMENDMENT runtime provenance). Fix is in the image, not the instrument:
gcc and libc6-dev added to the runner Dockerfile on the same
Synaptic-Tuner PR #150 branch as the pydantic fix (tuner rev 879c0d0).
Rebuild verified in-image: gcc 11.4.0, pydantic 2.12.4, transformers
5.12.1. Daemon preflight at capture: Operating System: Docker Desktop,
nvidia runtime present. instrument.runtime_image_digest repinned
sha256:894cb31b... -> sha256:a4076961bef8ece2d2aaadedd5a855a7bcfd3e48
21cbbc1b8815dbaa83ced15e. No generation row has ever been produced; all
failures were pre-model-load or pre-first-token instrument validation.

### 2026-07-31 -- Fourth runtime digest repin: python3.10-dev headers

Smoke attempt 5 cleared every earlier blocker (correct daemon, correct
digest, pydantic, gcc; full 426-shard Qwen3.5-4B weight load) and then
failed in triton's cuda_utils stub compile with "Python.h: No such file
or directory": triton invokes gcc with -I/usr/include/python3.10, which
exists only with the python3.10-dev headers; libc6-dev alone is not
sufficient. Fix on the same Synaptic-Tuner PR #150 branch (tuner rev
1dab1f3). Rebuild verified in-image: /usr/include/python3.10/Python.h
present, gcc 11.4.0, pydantic 2.12.4. Daemon preflight at capture:
Docker Desktop, nvidia runtime. instrument.runtime_image_digest
repinned sha256:a4076961... -> sha256:45847a60a08b3684818c5974d5412c8a
9d4bafd8d7f441c29b091ee580694434. Still no generation row ever
produced; the failure fired inside the first forward pass before any
token was sampled.

### 2026-07-31 -- Smoke PASSED (attempt 6); generation sweep dispatched

Smoke attempt 6 in the rebuilt image (digest sha256:45847a60...,
python3.10-dev headers) PASSED: 8/8 positive rows, readback target
12.608188, mean measured 12.628116, max abs err 0.0230 within
tolerance, parity ok, offtarget_abs_max 0.0, PIPELINE_EXIT=0. Lead
verified the printed verdict block directly from the run log. Per the
registered launch sequence (launch-authorization entry), the lead now
dispatches pipeline.py generate: 4 arms x 400 rows, sampled decode,
seed 20260802, per-arm runlog resume, hard-halt before the judge lane
per the registered governance boundary.

### 2026-07-31 -- Generation sweep and screen complete; judge lane opens

Generation: 1600/1600 rows (4 arms x 400), sampled decode temperature
0.7 top_p 0.9, generation_sampling_seed 20260802, elapsed 1252.8s,
image sha256:45847a60..., per-arm runlogs 400/400/400/400. Screen
(deterministic F5/F4, last automated stage): F5 degenerate 1/1600
(a_dose_1). F4 explicit-IDK per arm: a_baseline 15/400, a_dose_0p5
163/400, a_dose_1 260/400, a_placebo_1 6/400. Screened-in for the
judge pool: 385/237/139/394. No gate is adjudicated by these raw
counts; N1/N2/N3 fire only from the registered arithmetic after the
blinded judge lane. Pipeline emitted its registered governance halt;
the judge lane now proceeds LEAD-RUN: pool build with embedded decoys,
pool hash committed before any grading, isolated context-free
opus-tier judges per shard, grade application by hash, then the
N1/N2/N3 arithmetic and gate adjudication.

### 2026-07-31 -- Judge pool built; pool hashes committed BEFORE grading

build_judge_pool.py (full-pool mode, seed 20260803): 21 shards, 55-56
rows each, n_core_total 1155 (equals the screened-in total exactly),
25 embedded clear-positive decoys (target 25), opaque ids salted
(id_salt_sha256 committed, salt itself gitignored). Per the blinded
discipline the full manifest of per-shard pool_sha256 hashes is copied
to analysis-committed/full_pool_manifest.json and committed NOW, before
any judge sees any shard. Containment verified: manifest carries ids,
hashes, and counts only, no text. Shard files and id maps remain under
gitignored analysis/shards/. Judges are dispatched next: one fresh,
context-free opus-tier agent per shard, each receiving the rendered
rubric and bare {opaque_id, text} rows only.

### 2026-07-31 -- Judge grading complete; graded hashes committed BEFORE unblind

21/21 fresh context-free opus-tier judges returned graded files. Lead
batch verification over every shard: row count equals input count,
positional opaque_id join exact, labels restricted to F1/F2/F3, no
extra keys. Pooled over 1180 rows (1155 core + 25 decoys): F1 660,
F2 410, F3 110. apply_judge_grades.py commit-hash run for all 21
shards (role judge); the graded-file sha256 manifest is copied to
analysis-committed/graded_manifest.json and committed NOW, before
apply-full-pool reads any id map (registered unblinding-order
guarantee). Graded files themselves remain under gitignored
analysis/judge_grades/.

### 2026-07-31 -- Unblind, decoy gate, lead spot-check

apply-full-pool: 1155 core payload rows applied; in-run clear-positive
decoy agreement 25/25 = 1.0000, clearing the registered
min_clear_positive_agreement 0.92 floor (cell.yaml judge_lane). Lead
spot-check per the registered n=30: sample drawn with seed 20260803
over the unblinded pool, lead re-graded all 30 against the pinned
rubric text: 30/30 agreement with the judge labels. Three rows (a
leading-Yes with an "often considered" qualifier, a leading-No with an
"unlikely to completely" qualifier, a committed-Yes with a "generally"
tail) sit near the F1/F2 line; in each the judge's call follows the
rubric's precedence of the qualified core claim, and the lead does not
overturn any. Stability regrade shard selected deterministically
(seed 20260803 -> shard index 4, isnc_fullpool_shard_04); a fresh
context-free opus judge is regrading it now, reported non-gating.

### 2026-07-31 -- Gate adjudication (lead)

Preconditions: judge-lane in-run validity 25/25 = 1.0000 >= 0.92 floor;
lead spot-check 30/30 completed before this adjudication; N2
NOT-ADJUDICABLE guard clear (graded non-F4 rows 237 and 139, both >= 50).

N1 (IDK endpoint jump): a_dose_1 F4 260/400 = 0.6500 vs a_baseline
15/400 = 0.0375; diff +0.6125; primary paired bootstrap 95% CI
[0.5650, 0.6600]; lead-re-derived Newcombe cross-check [0.5591, 0.6599].
CI lower bound 0.5650 > registered floor 0.15. N1 PASS.

N2 (no graded intermediate): baseline F2+F3 share 0.4150. Gated arms:
a_dose_0p5 share 0.2600 (delta -0.1550), a_dose_1 share 0.1629 (delta
-0.2521). Neither rises 0.10 over baseline; the hedged share FALLS
monotonically with dose, the registered mode-switching signature.
N2 PASS. Non-gating report: a_placebo_1 share 0.4000 (delta -0.0150).

N3 (placebo band): |a_placebo_1 F4 0.0150 - a_baseline 0.0375| =
0.0225 <= 0.05 band. N3 PASS. Non-gating bootstrap diff CI
[-0.0425, -0.0025].

All three registered name-earning gates PASS on the fresh generations.
Per the registered claim rule the name IDK switch is EARNED for this
actuator at the pinned hs20 operating point. Stability regrade
(non-gating) in flight; resolution package goes to the PI for approval
before Outcome/resolve/PR.
