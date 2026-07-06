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
`experiment/phase1/probe/cloud/modal_al_true_a0.py` (on the `amendment-al`
branch). Clone it for a new cell rather than writing a Modal app from scratch, as
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
3. **`.spawn()` in the local_entrypoint, plus `modal run --detach`.** A client
   that dies (gracefully or not) with `.remote()` in flight cancels the input;
   spawn-then-exit leaves nothing to cancel. (Killed both AK Stage 1 arms.)
4. **xet off in the image env AND re-exported in the function**:
   `HF_HUB_DISABLE_XET=1`, `HF_HUB_ENABLE_HF_TRANSFER=0`.
5. **Verify staging inputs exist before launch** (see the check-before-prep
   step below) — a missing input caught at launch time wastes a paid boot.

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
- **Staging namespace.** Cloud-cell prep artifacts are namespaced by `RUN_TAG`
  under `professorsynapse/eh-al-prep-staging`.

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
