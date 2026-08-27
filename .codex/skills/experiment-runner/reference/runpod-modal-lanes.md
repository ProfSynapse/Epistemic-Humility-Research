# RunPod and Modal execution lanes (this project)

Beyond the local RTX 3090 lane and the HF Jobs probe lane
([probe-cloud-cells.md](probe-cloud-cells.md)), this project runs cloud cells on
two more providers. The provider mechanics are generic and documented in the
Synaptic-Tuner fine-tuning skill; do not re-explain them here.

- RunPod wrapper lane: tuner
  `.skills/fine-tuning/reference/runpod-jobs.md` (launcher
  `scripts/runpod_run_job.py`, lifecycle, gotchas, staging prerequisite).
- Modal lane: tuner `.skills/fine-tuning/reference/modal-jobs.md` (detached
  launch, image setup, crash-proof resume pattern).

This file records only the project-specific choices layered on top.

## The three-lane reality

| Lane | Use for | Parity |
|------|---------|--------|
| Local RTX 3090 | development, pilot, smoke, and any 4h+ atomic work | reference lane |
| RunPod (3090) | parity-locked cells run interchangeably with local | byte-exact parity PROVEN on the TRUE A0 cell (1662/1662 rows identical to local 3090) |
| Modal (A10G) | NEW surfaces / elastic or crash-prone long runs | A10G is a different architecture; NOT yet parity-evidenced, so not for regenerating a parity-locked cell |

Rule: a parity-locked cell may run on local 3090 or RunPod-3090 without
re-validation. Modal A10G is fine for a NEW cell surface, but do not use it to
regenerate a parity-locked result until Modal has its own parity evidence.

The Modal crash-proof skeleton for probe cells lives at
`experiments/radial-anti-propensity-steering/cloud/modal_al_true_a0.py`.
Clone it for a new cell rather than writing a Modal app from scratch, as
`modal_ak_stage1.py` did.

## Wrapper-authoring checklist (each item has killed a paid run)

Check every NEW Modal/cloud wrapper against all of these before launch; each
one is cheap to verify by eye and expensive to learn live:

1. **Idempotent clone.** Retries land on a WARM container where the workspace
   already exists; a bare `git clone` dies with exit 128 and every retry
   repeats it, so the app stops silently (dashboard shows no live app). Guard:
   `if not os.path.isdir(os.path.join(workspace, ".git")): clone`, then
   `fetch` (check=False) + `checkout <pin>`. (Killed item-11 r1 retries AND
   AK Stage 2 r1 retries.)
2. **argparse negative-leading values.** A dose grid like `-2,-1,0,1,2` passed
   as a separate argv entry (`["--alphas", ALPHAS]`) is read as a new flag:
   "expected one argument". Always use the equals form
   (`[f"--alphas={ALPHAS}"]`) for any value that can start with `-`. (Killed
   the AK Stage 2 r1 full sweep after its smoke had already passed.)
3. **Modal detach shape.** A client that dies (gracefully or not) with
   `.remote()` in flight cancels the input; spawn-then-exit leaves nothing to
   cancel. The older safe pattern is `.spawn()` in a local entrypoint plus
   `modal run --detach`, but verify it immediately with `modal app list` and
   `modal app logs`: if the app is detached with zero tasks and no function logs,
   nothing is running. The more direct shape is
   `modal run --detach path/to/app.py::run_one_cell --arg ...`, which runs the
   remote function itself and avoids local-entrypoint lifecycle ambiguity.
   (Killed both AK Stage 1 arms; the zero-task local-entrypoint variant later
   bit the doubt-snap cross-family Qwen relaunch.)
4. **xet off in the image env AND re-exported in the function**:
   `HF_HUB_DISABLE_XET=1`, `HF_HUB_ENABLE_HF_TRANSFER=0`.
5. **Verify staging inputs exist before launch** (see the check-before-prep
   step below) — a missing input caught at launch time wastes a paid boot.
6. **Volume-backed resume before big batches.** Mount row-output and committed
   summary directories on a Modal Volume before the first GPU subprocess, and
   `commit()` periodically while long tuner subprocesses run. A replacement
   worker cannot resume from scratch-local JSONL even when the underlying tuner
   command has `--resume`.

## Launch discipline

- **Fresh approval, every paid launch.** Each cost-incurring launch needs
  explicit user approval naming the cell/model/lane in the current conversation.
- **Dry-run first.** Run the launcher's `--dry-run` and inspect the resolved spec
  before any real submission.
- **Launch as a background task from a scratchpad script**, not an inline
  foreground command, so a long submission does not block the session.
- **Babysitter death is asymmetric.** A dead babysitter does NOT cancel a
  detached Modal run (it keeps going; monitor via `modal app logs <app-id>`), but
  it DOES orphan a RunPod pod into a re-run/billing loop. Sweep an orphaned pod
  by hand per the RunPod reference gotcha (`DELETE /v1/pods/<id>`, confirm 204,
  re-query until null).
- **After launch, prove the app is doing work.** `modal run --detach` returning
  "App completed" can mean only that the local entrypoint finished. Check for a
  live task or function logs under the app id. If there are zero tasks and no
  remote-function logs, relaunch the function entrypoint directly.
- **One writer per cell namespace.** If an earlier launch looked inert and you
  relaunch, stop the ambiguous earlier app before the replacement writes the same
  Modal Volume path. Duplicate workers for one `(RUN_TAG, cell_id)` can corrupt
  or race checkpoint/resume files even when each worker is individually
  resumable.
- **Staging namespace.** Cloud-cell prep artifacts are namespaced by `RUN_TAG`
  under `professorsynapse/eh-al-prep-staging`.

## Modal volume-get gotchas

`modal volume get` has two distinct failure modes on directory downloads.
Neither raises an error, so both require after-the-fact verification against
an expected manifest.

**Variant 1 — silent concatenation.** Modal CLI 1.5.1 has an unsafe edge case
for directory downloads: running `modal volume get` with a remote directory and
a nonexistent, file-like local destination can concatenate the directory's
contents into one bogus local file. Never interpret that concatenated output as
a model, adapter, checkpoint, or other valid artifact.

For an artifact bundle, pre-create the local destination directory and fetch an
exact allowlist of named files individually. Alternatively, use the Modal SDK
to download the bundle into an ignored `.partial` tree. In either path, verify
the relative filenames, byte sizes, and hashes against the expected manifest or
allowlist. Fail closed on missing, unexpected, duplicate, or concatenated
artifacts, and atomically promote the verified tree to its final location only
after every check passes.

**Variant 2 — silent partial download.** Separately, `modal volume get` can
report success while transferring only a fraction of a large directory's
files, with no error surfaced. In
`experiments/llama-atlas-gated-wide-instrument-retest`, pulling a 2956-file
`tensors/` directory from a Modal Volume via the CLI downloaded only ONE file
across three repeated attempts (once returning 0 bytes, once 358KB), despite
each attempt reporting success. The workaround was to bypass the CLI entirely
and use the Modal Python SDK directly: enumerate the volume with
`Volume.iterdir(recursive=True)` and pull each file with
`read_file_into_fileobj`. After switching to the SDK-based pull, all 2956
files landed and the downstream anchor-coverage check came back 2956/2956 =
1.0.

Treat both variants as the same underlying lesson: never trust a `modal volume
get` success message for a multi-file directory transfer. Count the files (or
otherwise checksum/verify) after every such pull, and prefer the SDK
(`Volume.iterdir` + `read_file_into_fileobj`) over the CLI for bulk directory
retrieval.

## Checkpoint staging registry

Cloud cells reference checkpoints by HF repo + revision, never a local path and
never `main`. The registry of staged/published repos + revisions is
`docs/public-artifacts.md`; treat that as the SSOT and do not duplicate its rows
here.

Add a check-before-prep step to the cell-prep checklist: before staging or
launching, confirm every base/adapter/dataset repo the cell references already
exists on the Hub at a pinned revision.

```python
from huggingface_hub import repo_info
repo_info("<org>/<repo>", repo_type="model", revision="<full-sha>")
```

A missing repo or a moving `main` pin caught at prep time is free; caught at
launch time it wastes a paid boot. When staging a local LoRA `final_model/` dir
as an adapter repo, exclude the auto-generated `README.md` and `training_args.bin`
(see the tuner staging-prerequisite section for why); consumers pass the base
model explicitly.
