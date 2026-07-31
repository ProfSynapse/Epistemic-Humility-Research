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
