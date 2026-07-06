# Launching a cell on Modal (cloud lane)

`modal_steer_cell.py` is ONE parameterized wrapper for any cell. It clones the
research repo at a pinned commit, runs `steer_cell.py` against a config that lives
inside the repo at that commit, checkpoints the untracked provenance to a Modal
Volume, and uploads the small result artifacts to a staging dataset. No
per-amendment constants live in the wrapper - everything comes from the flags.

## The one-liner

```bash
HF_TOKEN=... modal run --detach \
  experiment/phase1/probe/cloud/modal_steer_cell.py \
  --config experiment/phase1/probe/steering/configs/my_cell.yaml \
  --repo-commit <40-hex> \
  --staging-prefix professorsynapse/eh-<amendment>-staging \
  --arm primary \
  --gpu A10G
```

- `--config` is a path INSIDE the cloned repo at `--repo-commit`, so the exact
  signed `cell.yaml` (whose sha the amendment pinned) is what runs. Commit and
  push the config first, then pass its commit.
- `--repo-commit` pins the checkout. The clone is idempotent (a respawn re-fetches
  and re-checks-out the same commit into the same workspace).
- `--staging-prefix` is the private HF dataset repo the JSON/JSONL artifacts land
  in (via `cloud/upload_result.py`).
- Add `--smoke` to run the smoke pass that records the state file, or
  `--force-no-smoke` to run a full arm without one. Omit `--arm` to run every arm.
- `--gpu` selects the accelerator (default A10G); `--run-tag` overrides the derived
  tag (default `steer-<config-stem>-<commit8>`).

## Why `--detach`

Plain `modal run` creates an EPHEMERAL app that dies with the launching client; a
multi-hour cell would be lost on disconnect (this happened to AL A0 at 1350/1662
rows). `--detach` keeps the app alive server-side. The wrapper also sets
`retries=3` so a container death respawns the function, and the native runner
resume + Volume checkpoint continues from the last committed rows.

## Checkpoint + resume

A daemon thread mirrors the runner's out_dir into `Volume/ckpt/<run_tag>/out`
every 120s and `vol.commit()`s; every checkpoint exception is swallowed so a bad
checkpoint never kills the run. On (re)start the wrapper restores that subtree into
the out_dir so the runner's row-level resume skips completed work. After the run a
`DONE` marker is written into the checkpoint dir.

## After it finishes

Pull the artifacts from the staging dataset (or the Volume), grade the arm rows
with the amendment's grader, and run `score_gates.py` locally. Cloud runs produce
the same provenance shape as local; grading + gates are lane-independent.

## Cost + approval

A cloud launch incurs cost and needs explicit user approval in the conversation.
Never launch, cancel, or delete a Modal app without it. See the gotchas reference
for the xet hang and the reap-proof spawn pattern.
