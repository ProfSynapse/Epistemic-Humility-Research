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
1b. **Launch from the released checkout itself.** `cd` into the release root
   before running either command, and do not set `PYTHONPATH` to another tree.
   Python puts the working directory at `sys.path[0]`, ahead of `PYTHONPATH`, so
   the working directory DECIDES which `synaptic_host` a run imports. The
   dangerous half is the silent one: if the directory you launch from has no
   `synaptic_host`, the child falls through to `PYTHONPATH` and imports a
   different tree with no warning at all, while every check that reports a
   commit still reports the release commit. Those checks answer "which tree is
   this?"; none of them answers "which tree will the code come from?".

   This is not hypothetical. It happened on run 8: the first wrapper invocation
   imported the package from a development worktree while the checkout identity
   reported the released commit.

   The driver checks it as **P11**, after P3 and before it reads the tree,
   failing with `P11-wrong-tree` and naming BOTH paths, or with
   `P11-package-not-found` / `P11-namespace-package` when the released checkout
   is incomplete. It resolves the package through `importlib.util.find_spec`,
   in a child using the same interpreter and the same working directory a real
   cut uses. The rule is containment under the project root you gave the
   driver, nothing more: running from a worktree is not refused by P11, and does
   not need to be, because P7 already refuses a worktree for a real run.

2. **The branch head is published.** The training config is read as a committed
   git blob at the locked project commit, not from the working tree. An edited
   but uncommitted config cannot take effect.
3. **The model inventory is materialized and link-free.** See below. This step
   creates `.synaptic` before the Host has ever run, and on Windows that
   directory and everything under it then carries the access list it inherits
   from the project directory. **That is expected and needs no action from you.**
   The Host repairs the chain at activation. Do not pre-protect `.synaptic`, and
   do not change this step to create it differently — see the note under
   prerequisite 9.
4. **Docker Desktop with the Linux engine RUNNING**, context `desktop-linux`,
   endpoint `npipe:////./pipe/dockerDesktopLinuxEngine`. Do not pass an endpoint
   flag to the Host. It does not read your context store at all: the prepared
   composition CONSTRUCTS that endpoint from the two constants above and asserts
   them (`docker_prepared_composition.py:149-158`), then proves the daemon alive
   with an explicit `--host` version probe. That is blocker B-13.

   **The daemon check is the version probe, and nothing else.** Run it once
   before the first run of a session:

   ```
   docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine version \
     --format "{{.Server.Version}}"
   ```

   Expect exit 0 and a version string; `29.3.1` when this was measured. Exit 1
   means the engine is not up, whatever else reports otherwise.

   **`docker context inspect` and `docker desktop status` do NOT prove the
   engine is up.** With Docker Desktop stopped, `docker.exe context inspect
   desktop-linux` still exits **0**, with stdout byte-identical to the running
   case, because it reads a local config store and never opens the pipe.
   `docker desktop status` and `docker desktop start` also misreport while the
   engine is absent. All three were measured with the engine stopped and again
   with it running (section 22.7). Do not substitute any of them for the probe.

   The driver checks this as **P10**, immediately after P2 and before anything
   else, failing with `P10-daemon-unavailable` and printing the remedy. P2 and
   P10 are not redundant: P2 proves the endpoint CONSTANT is the one the Host
   will assert, P10 proves that endpoint ANSWERS.

   P10 issues the probe under the composition's own child environment, which is
   exactly `SystemRoot`, `TEMP`, `TMP` and `WINDIR` by construction
   (`docker_prepared_composition.py:116`, enforced by `docker_v1/model.py:1144`
   and asserted by test E1 on every suite run), so **you never check that key set
   yourself** and a widening of it would fail the suite rather than a run. It
   carries **no `USERPROFILE`**, deliberately, and that absence is exactly what
   B-13 was: with no home, `docker context inspect` resolves a relative `.docker`
   path and exits 1. If one of the four keys is missing from your own shell, the
   driver fails with `P10-environment-incomplete` and names the key, because the
   Host folds that case into a message about the docker executable instead
   (`docker_prepared_composition.py:145`).
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

   Three things to expect rather than diagnose:

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
   - **An inherited `.synaptic` after a `--probe-only` pass is EXPECTED.** P8
     creates the stage parent with an ordinary directory call, exactly as
     prerequisite 3 creates `.synaptic` itself, so on Windows the whole chain
     carries the access list it inherits from the project directory. The Host
     **repairs** that chain at activation, from the never-protected state only,
     and only through the path that creates the storage. So a probe-only pass
     legitimately leaves an inherited chain behind, and the next real run fixes
     it. That is blocker **B-11**, which stopped run 5 at cut 1 before the
     repair existed.

     **Do not pre-protect `.synaptic`, and do not change P8 or the inventory
     step to create it protected.** Doing so would set the access list of the
     model inventory's parent *before* the inventory is written, which was never
     measured, and the path-based form of that call is destructive: it empties
     the access list of every child, leaving them unreadable to you, to WSL and
     to the container, while the Host's own validator still accepts the root.
     The failure is silent and the check stays green, which is why this note
     exists.

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

### The `B10-EVIDENCE` lines

Around every cut the driver prints two tagged lines. They are read-only
observations and change nothing about what the cut does. **Quote them verbatim
in the run report**; blocker B-10 closes on them.

```
B10-EVIDENCE cut=2 stage=<path> state_nonempty=true artifacts_nonempty=false tmp_nonempty=false tracking_nonempty=false
B10-EVIDENCE cut=2 result=<code> status=<status> exit=<n>
```

The first is read **before** the cut is issued, the second **after** it returns.
`stage=NONE` with `unknown` flags means no stage exists yet, which is normal
before staging.

Why it matters: staging re-verifies the artifact topology on **every** cut, and
four of the five directories under `<stage>\artifacts` must be empty, so the
first cut issued after the trainer writes there would fail
`START_UNAVAILABLE`. That is B-10. The reading to apply, from architecture
section 19.14:

| `state` at cut 2 | Cut 2 code | Conclusion |
|---|---|---|
| non-empty | not `START_UNAVAILABLE` | B-10 confirmed and fixed |
| non-empty | `START_UNAVAILABLE` | the fix is wrong or incomplete; re-open with the message |
| empty | any | **unconfirmed — a deferral, not a pass.** B-10 stays on the ledger as latent |

**Cut 2 is the cut to watch.** The stage is fresh at cut 1, so cut 1 settles
nothing. The driver prints a reminder at cut 2. The third row is the one most
easily misreported: if the trainer buffers and writes late, `state` can still be
empty at cut 2, and that is not evidence that B-10 is absent.

### The `CAPTURE` lines

Around cut 1 only, the driver subscribes to `docker events` before the cut is
issued and reports what it saw afterwards. This is the architecture section
22.11 row 4 first-container capture, using the corrected instrument required by
section 23.5 row 2: an event stream rather than a poll, because run 8's
container lived 0.7 s under a 1 s sample, and **no image-name filter**, because
the prepared composition creates from a digest-pinned reference that never
prints a repository tag. Matching happens in the driver, on the `synaptic-`
container name or on any `ai.synapticlabs.tuner.v1.` label, so a non-match is
counted and printed instead of vanishing.

Alongside the stream the driver takes a **census** of container ids, `ps -a`
with no filter, once before cut 1 and once after it. The census is what makes
`matched=0` readable: `parsed` counts every container event in the window,
including this driver's own `--rm` probes, so a non-zero `parsed` never proved
that a container existed (section 24.7, follow-up #219).

```
CAPTURE container events parsed=7 matched=1 other=6 unparseable=0 stream file: <path>
CAPTURE verdict=matched 1 container(s) captured. census before=3 after=4 created=1
CAPTURE container id=<12 hex> name=synaptic-<...> matched_on=name events=create,start,die
```

One of four verdicts is printed, and only the first three are readings:

- `verdict=matched` — the container was captured; the lines that follow are its
  id, image, exit code, timestamps and stderr.
- `verdict=no-container` — the census did not grow, so nothing was ever created.
  This is **not** a match failure. Read the Host envelope and the
  `synaptic-host:` cause line; the match keys are not the suspect. Run 9 was
  this case and the old two-state reading called it a miss.
- `verdict=match-failed` — the census grew and no key matched. Now the keys are
  the suspect: check the `synaptic-` name prefix and the
  `ai.synapticlabs.tuner.v1.` label paths, and read the `created|` ids and the
  `other|` names.
- `verdict=census-unavailable` — `ps` did not answer, so the report says the
  reading is ambiguous rather than guessing between the two above.

`capture-unavailable` is separate again: no event stream ran at all. The capture
never gates the run; the cut's own result codes remain the acceptance.

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

**P8 runs before A1**, after the bind probe, so the full order is `P1` → `P2` →
`P10` → `P3` → `P11` → `P5..P7` → `P9` → `B1` → `P8` → `A1` → `A2` → `A3` →
`A4`. P10 sits
directly after P2 because a stopped engine should cost one command, not a full
sweep including P7's network read. P8 and A2 are not redundant: P8 probes
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

### The cause line carries a class and a frame, never a message

An activation failure prints one line like this:

```
    stderr| synaptic-host: START_UNAVAILABLE ValueError at synaptic_host/security.py:422 in _win_validate_acl
```

Four fields, and only four: the durable result code, the exception CLASS, the
in-package file and line, and the enclosing function.

**The exception's own message text is not in that line, and is not anywhere else
you can see.** It is excluded deliberately (`_report_admission_cause`,
`docker_training.py:583-613`). Several of those messages are written for the
Host's own callers and name a condition you did not cause: a missing environment
key surfaces as a complaint about the docker executable
(`docker_prepared_composition.py:145`). So **never match on message text.**
Nothing in this skill asks you to look for a phrase, and any procedure that does
is matching a string the operator never receives. Match on the class and the
frame.

The frame is the part that identifies the failure. The line number moves
whenever anything above it changes, so read `file` and `in <function>` as the
identity and treat the number as a pointer into the current source.

*One paragraph, to be deleted when follow-up #207 lands.* Today the frame is the
**deepest** in-package frame (`_innermost_package_frame`,
`docker_training.py:561-580`). Several modules define a shared reporter called
`_fail`, and `docker_v1/model.py` also has `_platform_fail`. When the deepest
frame is one of those, the line names the messenger rather than the cause and
tells you almost nothing on its own; read the CALLER of that frame. Amendment
22.14 replaces the single frame with the deepest two, which removes this step.
Until it lands, expect it.

### `P9-locked-project-inputs`, and why project size is not a precondition

**The prepared path stages only the inputs the workload names, so the size of
your project is not a precondition.** Staging copies the two files the source
lock records for this run, the training config and the workload's dataset, each
read at the locked commit and checked against the digest the lock recorded. It
does not archive the repository. A research corpus, a datasets directory or a
folder of papers sitting beside the training config costs the run nothing,
because none of it is ever staged.

This is worth stating because the opposite used to be true, and the failure was
expensive. Run 6 archived the whole superproject at the locked commit,
412,794,880 bytes against a 256 MiB staging bound, and the run died before any
container existed (blocker B-12). The natural conclusion from that failure is
"keep the project small", and it is the wrong one. **Do not use `.gitattributes`
to shape what gets staged**, do not split the repository for this reason, and do
not prune history to get under a bound. The bound still exists, but section 21.7
repurposed it: it now measures the staged input set, so the only thing that can
exceed it is a genuinely enormous dataset, and the remedy for that is a smaller
dataset, not a smaller repository.

The driver reports the number before a run is issued, as **P9**, after P7 and
before the bind probe:

```
    P9-locked-project-inputs: derived by the DRIVER at <commit>
    P9-INPUT kind=training-config path=training/smokes/docker-sft.json bytes=1089
    P9-INPUT kind=training-dataset path=training/fixtures/modal-smoke.jsonl bytes=638
    P9-TOTAL count=2 bytes=1727 archive_bound=268435456 entries_bound=20000
    PASS P9-locked-project-inputs: ...
```

Three things to expect rather than diagnose:

- **P9 never stops a run.** It reports; the Host owns the refusal and admission
  is the gate. Over the bound it prints `WARN` and the run still proceeds to the
  point where admission decides. A `WARN` here is a prediction, not a verdict.
- **It says `derived by the DRIVER` because it is a second derivation.** The
  authoritative set is the one admission writes into the lock. The driver
  resolves the same pair independently, before a run exists to read a lock from,
  so the line names the commit and both paths deliberately: if it ever disagrees
  with the staged `source\project` tree, that disagreement should be visible
  rather than inferred. Section 21.4 names exactly this kind of quiet
  disagreement as the thing the design guards against.
- **`SKIP` means no number, and that is deliberate.** If the probe cannot read
  the commit or resolve the dataset ref it says so and reports nothing, rather
  than printing a total it is not sure of. Nothing downstream re-checks P9's
  arithmetic, so a plausible wrong number would travel further than no number.

### A wedged `.synaptic` chain, and the one case where deleting state is the remedy

**Before you delete anything under `.synaptic`, check whether
`.synaptic\state\training.sqlite3` exists.** Your own check is the only guard
here. Nothing in the Host performs it for you, and nothing refuses the deletion.

The symptom is an activation failure whose cause line names a private storage
frame:

```
    stderr| synaptic-host: START_UNAVAILABLE ValueError at synaptic_host/security.py:422 in _win_validate_acl
```

The line number moves with the clause that refused; the frame is the part that
identifies this. **The validator's own message is not in the output.** The cause
line carries the exception's class and frame only, and excludes the text
deliberately, so searching your console for the wording of the failure finds
nothing.

This is the B-11-R1 wedge. It happens only on a volume where a directory's
access list propagates to children that already exist, so `F:` has never
produced it. A wedged `state` is protected and carries entries the Host did not
write, which from inside the process is indistinguishable from a third party's
decision. The validator refuses it, and no later repair can reach it. The
two-pass leaf-first repair prevents new wedges; it does not heal one that
already exists.

**The check: does `.synaptic\state\training.sqlite3` exist?**

- **No: delete `.synaptic\state` and re-run.** The repair recreates the chain.
  This is safe in the wedge case specifically, and the reason is worth keeping
  rather than trusting: the wedge can only fire while a chain member is still in
  its never-protected state, which no tree that has completed an activation is.
  A genuinely wedged tree has therefore never completed one, and holds no
  durable rows and no key.
- **Yes: stop and report. Do not delete.** `state` holds the durable rows
  database (`training.sqlite3`), the Docker control key
  (`docker\control-hmac.key`) and the Modal evidence key
  (`modal\evidence-hmac.key`). Deleting the directory removes all three
  together, silently and permanently, and the next run mints a fresh key as
  though nothing had been lost. There is no prompt, no refusal, and no way
  back.

One thing to expect rather than diagnose: **the remedy is narrow.** Deleting
`.synaptic\state` answers this one cause line on a propagating volume. It is not
a general recovery step, and it is not a way to clear an unrelated failure.

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
