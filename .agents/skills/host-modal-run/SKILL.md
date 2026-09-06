---
name: host-modal-run
description: Build and use the submit-side container for the Modal smoke of the prepared path, and run the offline gates G2, G3 and G5 that must pass before a paid submit. Covers the hash-locked modal==1.5.4 image, the WSL-to-Windows build-context translation, the engine-on-sys.path containment check, the engine lock digest instrument that reads blobs rather than worktree files, and the isolation-triple checklist. Use when preparing, gating, or diagnosing a Modal submit from the Windows host. This skill never modifies synaptic_host or the synaptic-tuner submodule, and it makes no Modal call.
allowed-tools: Read, Bash, Write, Grep, Glob
---

# Submit-side container and pre-submit gates for the Modal smoke

The Modal smoke sends the prepared path to a serverless GPU instead of a local
Docker container. Everything in this skill happens BEFORE that submit, on the
operator machine, without credentials and without a provider call. The point is
that every failure this lane can find for free is found for free: a submit that
fails after the paid pull and clone costs money and tells you less.

Design of record: `docs/architecture/prepared-path-alpine-diagnostic.md`,
section 29. Rulings (5) in 29.7, (7) in 29.9, (8) in 29.10, and the gate table
in 29.12.

**The dry run is not a gate.** 29.12 says so explicitly. G2, G3 and G5 are.

## Directory choice

29.10 rules what the container must and must not carry, but names no location
for the recipe. This skill sits at `.skills/host-modal-run/`, beside
`.skills/host-docker-run/`, because the two are peers: same operator, same
machine, same prepared path, different provider. The local lane's skill is
frozen scaffold and is not touched by anything here.

`CLAUDE.md` is NOT written by this skill or by anything in it. It is a generated
mirror of `AGENTS.md` and the sync tool does not touch it.

## The four commands

```bash
bash .skills/host-modal-run/container/build.sh              # build the image
bash .skills/host-modal-run/container/build.sh --g2         # build, then gate G2
python3 .skills/host-modal-run/scripts/g3_engine_lock_digests.py --expect 0
python3 .skills/host-modal-run/scripts/g5_isolation_triple.py --rotation-recorded-at <iso8601>
```

`--no-build` runs G2 against an image already built. `--expect` turns G3's
reading into an exit code. G5 takes `--check` to add the provider existence
lookups; without it, it makes no call at all.

## The submit container

`container/Dockerfile` builds a submit-only image. It carries the Modal SDK and
nothing else.

| Property | Value | Why |
|---|---|---|
| Base | `python@sha256:528257d4...`, from `python:3.11-slim-bookworm` | Digest-pinned, so the recipe cannot drift under a moving tag. |
| Interpreter | CPython 3.11.16, x86_64 | Matches the cp311 x86_64 wheels the launcher closure was built for. |
| SDK | `modal==1.5.4`, exactly | `deployment_v1.py` and the facade compare for EQUALITY, not a floor. |
| Install | `--require-hashes --only-binary :all: --no-deps` | Makes the lock's "must not resolve" literal. |
| Build context | `synaptic-tuner/requirements/` | Holds exactly one file, the lock. The daemon receives one file. |
| PATH | 28 bytes | Measured by G2 against the 4096-byte bound. |
| User | numeric `1000:1000`, no passwd entry | The pinned base has no `useradd`; a numeric id needs no entry. |
| HOME | `/tmp` | An unset HOME expands `~` to `/`, and a library then fails on a write it should never have attempted. |
| ENTRYPOINT | empty | B-4 on the local lane was an image ENTRYPOINT swallowing the workload argv. |

What is deliberately absent, and what would go wrong if it were present:

- **Engine and project source.** The deployment attaches sources with copy
  disabled and the training container clones at run time. A source layer here
  would be a second, divergent copy that nothing reconciles. Source is
  bind-mounted read-only instead.
- **A trainer image or any ML stack.** This container submits. It never trains.
- **Any credential.** They reach the SDK in-process at submit time. Never a
  layer, never argv, never a durable artifact. G2 check C6 measures this.
- **A container-side interpreter pin.** The engine runtime lock pins CPython
  3.11.14 at `/opt/conda/bin/python3` for the TRAINING container. That pin is
  container-side and does not cross the seam, so it does not constrain this
  image.

### Three things about the build that fail as something else

1. **The build context is not the Dockerfile's directory.** Run it from the
   engine's `requirements/` directory or the COPY fails with a message about a
   missing file, which reads as a broken recipe rather than a wrong context.
2. **Docker Desktop is a Windows process.** Called from WSL, `docker.exe` reads
   every path as a Windows path. A POSIX build context or `-v` source is not
   resolved, it is misresolved. `build.sh` translates with `wslpath -w`.
3. **The endpoint is constructed, not looked up.** B-13 (section 22) recorded
   that `docker context inspect` needs USERPROFILE to resolve the `.docker`
   config directory and fails opaquely without it. `build.sh` names
   `npipe:////./pipe/dockerDesktopLinuxEngine` with `--host`, so no context
   lookup happens at all.

No network policy is asserted anywhere in this lane. Egress is unrestricted at
this pin by user ruling, and the standing network-disabled wording from the
local lane does not transfer here.

## Gate G2, the submit container

Runs inside the container. Six checks, ordered so that C2 runs before anything
touches `sys.path`.

| Check | Establishes |
|---|---|
| C2 | No engine or project source is baked into the image. Must run FIRST: if `tuner` already resolves, a layer carries it. |
| C1 | `modal.__version__` is exactly `1.5.4`. |
| C3 | After the submit process puts the engine root on `sys.path` in code, `tuner` resolves INSIDE that root. |
| C4 | The engine tree is at the commit the superproject pins. |
| C5 | The container PATH is under 4096 bytes, and the operator PATH length is recorded. |
| C6 | No credential-class name is present in the container environment. |

**C3 uses `importlib.util.find_spec`, never `module.__file__`.** A namespace
package has `__file__ = None`, so reading the attribute raises on exactly the
shape the check exists to catch: a stray `sys.path` entry that makes `tuner`
resolve as a namespace portion. The check handles both shapes, takes `origin`
for a regular package and `submodule_search_locations` for a namespace one, and
asserts CONTAINMENT of every location rather than matching a path substring.

**C3 and C4 are separate on purpose and neither implies the other.**
Containment proves which TREE was imported. It says nothing about which COMMIT
that tree sits at: a dirty or differently checked-out submodule passes C3
unchanged. The gitlink proves the commit and says nothing about what actually
got imported. The gate needs both, so `build.sh` measures the gitlink on the
host (where git lives) and passes both values in.

**C5 and the 4096-byte bound.** `launcher.py` rejects any allowlisted child
environment value over 4096 bytes, so `ensure_and_reexec` fails under a long
PATH. The operator PATH was measured at 5248 bytes in a WSL shell and 3903 on
Windows. That is why the container sets its own short PATH instead of
inheriting one. A violating OPERATOR PATH is reported as a warning, not a gate
failure, because the container's own PATH is what the gate governs. Follow-up
#432 asks G2 to record the operator length, and it does.

## Gate G3, the engine lock digests

**Read the blob, not the worktree.** `modal-runtime-v1.lock.json` records a
sha256 per locked member, computed from git content. On a Windows checkout the
worktree bytes are not the git content: `.gitattributes text=auto` translates
LF to CRLF on checkout. A worktree-hashing script therefore reports a defect
that does not exist, and hides the count that does.

The script hashes `git cat-file blob <sha>:<path>` for every member and for the
lock itself, so the reading survives the checkout platform, the worktree state,
and a submodule that is not checked out at the pin at all.

Its self-check, printed as a second column every run:

| Blob mismatches | Meaning |
|---|---|
| 2 (`modal_remote`, `sft_runtime`) | B-19 open, as recorded at engine ce539b70. Correct instrument. |
| 0 | B-19 remediated: the lock regenerated at the pin and the Host gitlink moved to it. G3 passes. |
| 3 | The script read the WORKTREE. The third name is `dependency_lock` and its only difference is line endings. Fix the instrument; do not file a third defect. |

Measured at ce539b70 on 2026-09-06: blob 2, worktree 3. The two columns are
printed together so the distinction is never a matter of trust.

`--engine-root` defaults to the sibling submodule and `--sha` defaults to the
gitlink in the superproject HEAD tree, deliberately rather than to the
submodule's own HEAD: a checked-out submodule can sit on any commit, and G3
must measure the pin.

A Windows `git.exe` rejects a POSIX path given to `-C` with a fatal exit 128.
Every git call in these scripts sets the working directory and omits `-C`.

## Gate G5, the isolation triple

Three clauses, knowable three different ways, which is why the gate is a
checklist and not a probe.

- **Isolation is configuration** and is fully decidable offline. Ruling (5)
  settled that the app name is a module constant and cannot vary from Host
  configuration, so isolation is carried by the provider environment and the
  three object names beside it. All four live in
  `training/providers/modal.json`.
- **Existence is a provider property.** Nothing local can decide whether the
  environment, the two Volumes and the Secret exist in the account. That needs
  credentials and a call, so it is off by default. With `--check` the script
  asks only for existence BY NAME, with `create_if_missing` False on every
  call, and never reads a Secret's contents.
- **Rotation is an operator act and no probe can see it.** Reading a key to
  prove it changed would defeat the purpose. It is recorded as a dated
  attestation passed in with `--rotation-recorded-at`, and the gate refuses to
  report itself satisfied without one.

The offline half checks four things: that the four names are all distinct from
the four the existing deployment uses (ruling (9) in 29.11 asks for exactly
this overlap test); that the declared key set is exactly the two ruling (7)
fixes; that the standing safety properties of the worker function are
unrelaxed, read from the blob at the pinned engine sha; and that a rotation
attestation was supplied.

The four object names are configuration identifiers, not credentials, and the
script prints them. It never prints a credential name, value, or length.

### Why the configuration file is edited in place

Blocker B-20: the dedicated environment cannot be selected by adding a NEW
configuration file. `ModalHostConfigV1.load` hardcodes the filename
`modal.json` when given no path, the `path` and `config_path` parameters are
dead because the sole production caller passes none, and a second manifest is
not selectable either because the loader uses the literal `synaptic.yaml`. The
ruling was to edit `training/providers/modal.json` in place, with no Host code
change and no new seam. The loader enforces an exact key set, so the file
admits no comment key; this section is where that explanation lives instead.

## What this skill does not do

- It makes no Modal call. Not a deploy, not a submit, not a lookup, unless you
  pass `--check` to G5 with credentials present.
- It creates and deletes nothing in the account.
- It does not touch the existing deployment's environment, Volumes or Secret.
  G5 check S1 exists to prove that the smoke's four names do not collide with
  them.
- It never modifies `synaptic_host/` or the `synaptic-tuner` submodule.

## Known limitation

The `--check` arm of G5 is UNEXERCISED. It was authored but never run, because
the task that produced it was forbidden from making any Modal call. Everything
else in this skill is exercised: the image builds, G2 passes inside it, and G3
and G5's offline half were run and their checks were each shown to go red under
the condition they exist to catch. Treat the first live `--check` as the step
that validates that arm, and read its failures as possibly the script's rather
than the account's.
