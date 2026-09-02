---
name: host-docker-run
description: Run the synaptic_host prepared Docker training path on the Windows host - materialize the link-free model inventory in a throwaway container, assert the preconditions and early assertions, probe the mount source, then re-issue the one unchanging training command until the durable phase stops advancing. Use when running, re-running, or diagnosing a prepared-path Docker training run from Windows, or when a run appears stalled, unpublished, or failed. This skill is about USING the committed Host CLI through checked-in operator scripts; it never modifies synaptic_host, the synaptic-tuner submodule, or the committed provider profile.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Prepared-path Docker training run on the Windows host

The prepared path runs the real SFT entrypoint in a Docker container on the
Windows host, through committed configuration only. The container argv is
recomputed from the engine's locked closure manifest and compared for exact
equality before any container exists, so the workload is not a design variable.
Everything below is about the operator surface around it.

Design of record: `docs/architecture/prepared-path-alpine-diagnostic.md`.

## The two commands

Both run under **Windows Host Python**, never WSL Python.

```
python.exe .skills\host-docker-run\scripts\materialize_model_inventory.py
python.exe .skills\host-docker-run\scripts\run_prepared_training.py
```

Add `--probe-only` to the driver to run the preconditions, the mount-source
probe and the early assertions without starting a training run. Add
`--verify-only` to the materialization script to re-check an existing inventory
without starting a container.

## Prerequisites

1. **A clean released checkout on an NTFS drive, produced with `git.exe`.** The
   project root must be a Windows drive-letter path. A UNC root is refused, and
   a distro-ext4 root cannot work either, because the stage translator raises
   unless the stage path has a Windows drive. Mount sources are DERIVED from the
   project root, so no storage root can be moved off that drive.
2. **The branch head is published.** The training config is read as a committed
   git blob at the locked project commit, not from the working tree. An edited
   but uncommitted config cannot take effect.
3. **The model inventory is materialized and link-free.** See below.
4. **Docker Desktop with the Linux engine**, context `desktop-linux`, endpoint
   `npipe:////./pipe/dockerDesktopLinuxEngine`. Do not pass an endpoint flag to
   the Host: it probes and re-asserts the descriptor itself.
5. **Exactly one `docker.exe` on the Windows PATH.** WSL carries two other
   docker binaries and they must not be the ones found. The composition counts
   candidates and raises unless there is exactly one.
6. **The nvidia runtime.** The device ruling is GPU and the code delta is zero.
   The CPU branch is unreachable: the trainer spawns a worker that imports
   unsloth at module top level, and `adamw_8bit` plus `bf16: true` have no CPU
   fallback and no override.

## Materializing the model inventory

The inventory lives at
`<project_root>\.synaptic\model-inventory\models--<namespace>--<repo>\snapshots\<revision>\`.
The location is not an operator choice: the storage location ref is
`project://.synaptic/model-inventory` and `project://` roots are joined onto the
project root.

The download runs in a **throwaway `python:3.12-slim` container** driven by plain
`docker.exe`, never through `synaptic_host`. There is no host conda environment
and no venv; everything model-related goes through Docker. No downloader is
added to the Host.

That throwaway container is the only thing on this path with network access. It
needs no credential for a public repository, so it runs with no `-e` flag and
the script never reads a token.

The materialized tree must satisfy five invariants or admission fails:

| # | Invariant |
|---|---|
| 1 | No symlink and no reparse point, in the tree or in the four directories above it |
| 2 | Relative paths NFC-normalized, no backslash |
| 3 | No case-colliding paths |
| 4 | Regular files only, at least one, at most 20 000 |
| 5 | Nothing changes during the read; every file is hashed with a before/after identity check |

**Invariant 1 is the trap.** A Hugging Face cache can lay a snapshot out as
symlinks into a `blobs/<sha>` store, and copying such a directory verbatim is
rejected outright as `model snapshot contains a redirect`. The script copies with
`shutil.copyfile`, which dereferences, so the result is real files under both
layouts.

You do not have to record integrity evidence yourself. The Host re-hashes every
file during resolution and again after staging, and folds the result into
`staged_model_inventory_digest`, one of the digests the content-addressed stage
key is built from. If a single inventory byte changes, the stage key changes.

## Running

Re-issue **one unchanging command**. There is no separate reconcile verb: the
CLI has one command, each invocation performs exactly one cut dispatched on the
durable phase, and re-running it is how an operator reconciles.

```
python.exe -m synaptic_host training run --provider docker --config project://training/smokes/docker-sft.json --destination local-default
```

Eight argv tokens exactly, which is what the fixed-arity parser demands.

**It takes at least THREE post-submit cuts, not two.**

1. an **observe** cut, which may repeat while the container runs,
2. a **verify** cut, which writes `ARTIFACTS_VERIFIED` and publishes nothing,
3. a **publish** cut, which is always a separate call.

Reading `published == False` after one reconcile is the correct behaviour of a
healthy system. An acceptance script that reconciles once and concludes failure
has measured nothing. The driver loops until the phase stops advancing and logs
the verify and publish cuts separately, rather than counting.

The command result on stdout does **not** carry the durable phase. The phase is
`docker_run_mutations.phase` in `<project_root>\.synaptic\state\training.sqlite3`,
and the publication row is `publication_records_v1` in the same file. The driver
opens that file read-only.

## Early assertions

Each is cheap and each exists to surface a known unknown with its true cause
rather than let it appear later disguised as something else.

| # | Assertion | Why |
|---|---|---|
| A1 | GPU visible inside the container | The image's `NVIDIA_REQUIRE_CUDA` bands top out below the host driver, so a toolkit rejection would look unrelated |
| A2 | `/artifacts` writable by the non-root container user `unsloth:runtimeusers` over a `wsl.localhost` bind | A read-only `/artifacts` fails late and confusingly |
| A3 | The container's Python matches the profile at full patch level | The trainer demands full patch-level equality and refuses otherwise |
| A4 | The snapshot exists at the cache path and contains no links | Confirms the inventory design end to end before training starts |

The container user in A2 is not a guess: `preparer-host` measured the committed
image's `User` as `unsloth:runtimeusers` and recorded it in
`docs/preparation/environment-model-prepared-path-alpine-diagnostic.md`.

The driver also probes the **mount source** before the first real run. The
emitted bind source is `\\wsl.localhost\<distro>\<drive_mount_root>\<drive>\...`.
Inside the `docker-desktop` distro, `/mnt` is that distro's own ext4 and the host
drives are drvfs under `/mnt/host`. A stale `/mnt/f` skeleton can survive there
from a legacy bind, which is worse than absence because it looks plausible, so
the probe fails an empty listing as well as a failed bind.

If the probe fails, the fix is a **configuration** change, not a code change:
switch `docker_host.drive_mount_root` and `wsl_distro` to the fallback pair and
re-probe. The driver never edits the profile.

## Reading a failure

**Read `trainer.stderr.log` before diagnosing anything from the exit code.** The
driver prints it first on failure. A LoRA adapter defect fails inside the
container at artifact assembly, before `final_model.tar` exists, so the Host sees
only a non-zero trainer exit, and the only stderr line may be an opaque worker
rejection with exit 2. Without that log the defect is indistinguishable from a
GPU, mount, or image problem.

A second reason a run looks broken when it is not: while the container runs, the
observe cut returns the record unchanged. That is not a stall.

## Do not

- Do not create a host conda environment or venv. Everything model-related runs
  through Docker.
- Do not use a `/mnt/f`-style 9p path as a mount source. Mount sources are
  derived, and the drvfs path inside the engine's distro is the one that exists.
- Do not switch the prepared composition from `--mount type=bind` to `-v`. The
  hard failure on a missing source is the point; `-v` would create the source
  directory silently.
- Do not pass `-H` or an endpoint flag to the Host. It resolves and re-asserts
  the endpoint itself.
- Do not add a downloader, cache framework, or compatibility layer to the Host.
  The materialization script is an operator tool, not a Host feature.
- Do not use the legacy same-process composition facade. The prepared path is
  disjoint from it and stays disjoint by changing nothing.
- Do not run the suites with a directory glob. Use explicit test file paths: the
  rtk proxy reports "No tests collected" for globs. Use an explicit 3.11+
  interpreter.

## Outputs

Run outputs, probe output and run records go under `scratch/`, which is
gitignored. The scripts themselves are tracked here, because a gitignored script
is not a reusable workflow.

The design originally placed the scripts in `scratch/test-phase/`. The record of
why they live here instead is the team-lead's dated amendment to sections 11 and
13.1 of `docs/architecture/prepared-path-alpine-diagnostic.md`.
