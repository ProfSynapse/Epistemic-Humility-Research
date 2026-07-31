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
