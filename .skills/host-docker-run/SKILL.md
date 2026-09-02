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

   Build it by cloning the **branch** and then verifying HEAD equals the target
   sha. Do NOT `git checkout <sha>`: that detaches HEAD, and a detached checkout
   cannot publish (see prerequisite 8).

   ```
   git.exe clone --branch <branch> <url> <dir>
   git.exe -C <dir> rev-parse HEAD    # must equal the target sha
   ```
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
7. **`--entrypoint env` works on the committed image — probe it ONCE before the
   first real run.** The prepared composition and the A1-A3 probes both rely on
   it, and the image's own `env` was never observed by the architect. Run:

   ```
   docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine run --rm \
     --pull never --network none --entrypoint env <image@sha256:...> \
     /opt/conda/bin/python3 -c "print('ok')"
   ```

   Expect exactly `ok`. If `env` is not on the image's PATH, the single-token
   fallback is `/usr/bin/env`. If the flag itself misbehaves, STOP and report
   rather than improvising: nothing on this path reads `Config.Entrypoint`
   back, so a daemon that silently ignored the flag would present as blocker
   B-4 all over again (architecture sections 17.9 and 17.11).
8. **The project checkout is on a branch that tracks `origin` at HEAD.**
   Publication closure resolves the source through `_verified_remote_source`,
   which needs an exact upstream branch and refuses otherwise. A detached HEAD
   surfaces only as `RESOLUTION_UNAVAILABLE` at cut 1, which names the symptom
   and not the cause — that is blocker B-6, and it cost a full diagnostic cycle
   on run 2. The driver now checks it as **P7** before anything touches Docker,
   failing with `P7-detached-head`, `P7-no-upstream`, `P7-remote-mismatch` or
   `P7-origin-unreachable` and printing the one-line remedy. That last tag is
   separate on purpose: when `ls-remote` cannot reach origin at all, the remedy is
   to check network access and rerun, NOT to push. A successful `ls-remote` that
   lists nothing is a different thing — origin really does not carry the branch —
   and stays a mismatch that a push fixes. Three conditions, all required:

   ```
   git.exe -C <root> branch --show-current                       # non-empty
   git.exe -C <root> config --local --get branch.<branch>.remote # exactly origin
   git.exe -C <root> ls-remote origin refs/heads/<branch>       # equals HEAD
   ```

   The **engine submodule may stay detached**: `GitCliLocalSourceInspector`
   substitutes its branch from the committed `.gitmodules`. The superproject may
   not. P7 is also the one precondition that touches the network, through
   `ls-remote`.

   Running the driver from a **working worktree** fails P7 by design: a worktree
   branch normally has no local upstream, so it is not a publishable source. The
   released checkout cloned with `--branch` is, and it is the only place a real run
   belongs. A P7 failure in a worktree is the check working, not a regression.

   The ref is built from the **local** branch name, because the engine inspector
   sets `GitSource.branch` from `git branch --show-current` and the Host then
   reads `refs/heads/<that name>` from origin. A local branch pushed to a
   differently-named remote branch therefore FAILS, even with an upstream set.
9. **`docker_host.container_user` equals the identity the pinned distro presents
   as owner of the project drive.** The prepared composition emits it as
   `--user <uid>:<gid>`. This is a configuration requirement, not a code one, and
   it exists because the container writes `/artifacts` over a `wsl.localhost`
   bind. The distro mounts the drive with `metadata`, so DrvFs honours stored
   POSIX modes: a fresh directory presents `0755` owned by the mount's `uid=`,
   and any other user gets `r-x`. That is blocker B-9, which stopped run 4 at
   assertion A2. Matching the OWNER rather than the mode is what makes this
   correct under any `umask` the mount can present.

   Read the value on the host, from the mount itself:

   ```
   wsl.exe -d Ubuntu-22.04 -- awk '$2=="/mnt/f"{print $4}' /proc/mounts
   ```

   Expect an options string containing `uid=1000,gid=1000`; those two numbers are
   the value. Substitute the committed `wsl_distro` and
   `<drive_mount_root>/<drive letter>` if either differs. Set the field in
   `training/providers/docker.json`, commit, and rebuild the released checkout —
   the profile is read as a git blob at the locked project commit, so an
   uncommitted edit cannot take effect.

   The driver checks it as **P8**, after the bind probe and before A1, failing
   with `P8-container-user-missing`, `P8-container-user-shape` or
   `P8-stage-writable-as-container-user` and printing the `/proc/mounts` command
   as the remedy. Only numeric `uid:gid` is accepted: a name in `--user` resolves
   against the **image's** `/etc/passwd`, which cannot express a host mount
   identity.

   Two things to expect rather than diagnose:

   - **P8 creates the stage parent.** A `--probe-only` pass now creates
     `.synaptic\state\docker\stages` if it is absent, by the same idempotent call
     the staging code makes. A run creates it anyway, but "no durable state was
     written" no longer holds for a probe-only pass. The driver prints one line
     when it creates it. P8 removes only its own `p8-probe` directory, never a
     stage, because stage reuse requires the artifact directories to be empty.
   - **`WARN P8-home` fires on every pass today, and is not a fault.** A numeric
     `--user` has no `/etc/passwd` entry, so the runtime sets `HOME=/`, which the
     user cannot write. That was measured directly on the committed image. It is
     a warning because a non-writable `HOME` is legitimate for a workload that
     never writes there. It is tracked as **B-9-R1** and settled by the trainer's
     own output, not by this probe.

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
| A2 | `/artifacts` writable over a `wsl.localhost` bind by the container user the profile declares | A read-only `/artifacts` fails late and confusingly |
| A3 | The container's Python matches the profile at full patch level | The trainer demands full patch-level equality and refuses otherwise |
| A4 | The snapshot exists at the cache path and contains no links | Confirms the inventory design end to end before training starts |

A1, A2 and A3 each pass `--entrypoint env` immediately before the image
reference, matching the token the prepared composition uses. Without it the
image's own entrypoint runs `supervisord` and discards the appended command,
so all three would start jupyter and time out at `T1-timeout` — the exact
disguised failure these assertions exist to prevent. The bind probe is
unaffected: it uses `python:3.12-slim`, not the profile image.

**P8 runs before A1**, after the bind probe, so the full order is `P1..P7` →
`B1` → `P8` → `A1` → `A2` → `A3` → `A4`. P8 and A2 are not redundant: P8 probes
the real **stage parent** and names the cause and the remedy for B-9, while A2
probes a scratch directory and keeps its continuity across earlier runs.

The container user in A2 is **read from `docker_host.container_user`**, the same
field the prepared composition uses, so the probe asserts the contract the run
will actually use. It used to be the hard-coded `unsloth:runtimeusers`, which
`preparer-host` had measured as the committed image's own `User`. That was
faithful only while the composition passed no `--user` at all; once it emits one,
a hard-coded name would fail a run the composition would have completed.

The driver also probes the **mount source** before the first real run. The
emitted bind source is `\\wsl.localhost\<distro>\<drive_mount_root>\<drive>\...`.
The committed pair is `Ubuntu-22.04` with `drive_mount_root` `/mnt`, where the
Windows drives are drvfs at `/mnt/<drive>`, so `F:` renders as
`\\wsl.localhost\Ubuntu-22.04\mnt\f\...`.

The `docker-desktop` distro was tried first and is **refuted by measurement**,
not merely unpreferred. Inside it `/mnt` is that distro's own ext4 and the host
drives are drvfs under `/mnt/host`, but the engine cannot resolve a source there
at all: it fails with `accessing specified distro mount service: stat
/run/guest-services/distro-services/docker-desktop.sock: no such file or
directory`. Do not switch back to it on the theory that a nested root is tidier.
A stale `/mnt/f` skeleton can also survive in that distro from a legacy bind,
which is worse than absence because it looks plausible, so the probe fails an
empty listing as well as a failed bind.

If the probe fails, the fix is a **configuration** change, not a code change:
switch `docker_host.drive_mount_root` and `wsl_distro` to another measured pair
and re-probe. The driver never edits the profile. Because the profile is read as
a git blob at the locked project commit, a changed value takes effect only once
it is committed and a new released checkout is built.

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
- Do not feed a shell program to a container with `subprocess.run(input=<str>,
  text=True)`. Text mode rewrites `\n` to `os.linesep`, so on Windows the
  container's `sh` receives CRLF and dies on `set -eu\r` with `Illegal option
  -`. The translation is the identity on Linux and WSL, so the defect is
  invisible everywhere except the host that matters. Send bytes; the
  materialization script does, and guards the invariant as
  `M3-stdin-newlines`.
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
