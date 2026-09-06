# Modal smoke of the prepared path: the external surface

PREPARE artifact for task #429, feature #73. Author: devops-modal. Written
2026-09-06 (UTC clock read in the same turn as the measurements below).

Scope: everything the Modal smoke depends on that is **outside** the Host
source tree, measured rather than recalled. Host worktree
`_worktrees/ehr-submodule-cloud-api-v1-host-clean` at branch
`feat/submodule-cloud-api-v1-host`; engine submodule pinned at
`ce539b70`, confirmed both ends (`ls-tree HEAD synaptic-tuner` returns
`160000 commit ce539b705a9d…`, and the submodule's own `rev-parse HEAD`
returns the same).

Everything here was read or executed read-only. No submit, no deploy, no
paid call. One blocker was found and is reported separately as B-19
(task #431).

---

## 0. Reading rules for this document

Two conventions matter for anyone re-measuring these numbers.

**Blob hashes, not worktree hashes.** This is a Windows DrvFs checkout.
`git check-attr` reports `text: auto` on
`synaptic-tuner/requirements/modal-launcher-v1.lock`, and that file's
worktree copy is CRLF (CR=39, LF=39) while its blob is LF. A raw
`sha256sum` of the working tree therefore disagrees with the recorded
digest even when the file is correct, and `git status` still reports the
file clean because git applies the filter when comparing and a raw hash
does not. Every digest in this document was taken through
`git cat-file blob HEAD:<path>`. Any future check of the runtime lock
from a Windows checkout must do the same or it will manufacture a false
positive. The `.py` members have CR=0 and are unaffected.

**Counts come from an instrument, not from a list.** Where this document
gives a count, the command that produced it is named. Section 2 in
particular corrects a figure carried in the plan.

---

## 1. The Modal SDK pin: four sites, one authority

**Question.** Four places name a Modal SDK version. The machine here has
1.5.1 installed. Which version would a submit container built from the
lock actually carry, and is this a B-5 class defect?

**Answer: exactly 1.5.4, and it is not B-5 class.** The four sites agree
on 1.5.4 and one of them is authoritative and hash-locked.

| Site | Value | Role |
|---|---|---|
| `synaptic-tuner/requirements/modal-launcher-v1.lock:22` | `modal==1.5.4` with a sha256 hash | the authority |
| `tuner/execution/providers/modal/facade.py:18` | `EXACT_MODAL_SDK_VERSION = "1.5.4"` | the runtime gate |
| `tuner/execution/providers/modal/modal-runtime-v1.lock.json` | `sdk_version: "1.5.4"` | the recorded lock |
| `ModalRuntimeLockV1.__post_init__`, `config.py:180` | rejects any lock whose `sdk_version != "1.5.4"` | the schema refusal |

The lock file's line 2 reads: *"Regenerate deliberately; installs must
use `--require-hashes` and must not resolve."* `launcher.py:401-402`
installs exactly that way:

```
str(uv), "pip", "install", "--python", str(python),
"--require-hashes", "--only-binary", ":all:",
```

`--require-hashes` disables resolution, so the installed version is the
pinned one and no range can widen it. A submit container built from this
lock carries 1.5.4 and nothing else.

**All four sites live inside the pinned read-only engine submodule.** The
Host root carries no `pyproject.toml` and no `requirements*.txt`; that
absence is measured, not assumed. So the Host cannot drift from the
engine on this value.

**`requirements-cloud.txt:14` (`modal>=0.73.0`) is inert for Modal v1.**
Its only code reference is an error-message string in
`tuner/cloud/hf_jobs.py:106`, which belongs to a different provider. It
does not feed the Modal v1 launcher.

**Not B-5 class.** B-5 is a closure-manifest member edited without
regenerating the manifest. Nothing here is a closure member and all four
sites agree. (A genuine B-5 class defect does exist at this pin, but on
different files: see section 8.)

**1.5.1 on this machine is a fact about the operator's environment, not
about the submit container.** It matters only because it blocks the
offline dry run, which is section 6.

---

## 2. The engine namespace at `ce539b70`: 33 names, 3 modules, all present

**Correction to the dispatch premise, carried on task #429 as
`metadata.dispatch_correction`.** The plan's line 41 says "the fourteen
names". Fourteen came from a one-module reading of
`modal_provider.py`'s `synaptic_tuner.api.v1.modal` import. Measured by
grep over **both** Host modules, the figures are different, and even the
one block the plan was reading holds **fifteen** names, not fourteen.
This document reports the instrument's count and never reconciles toward
fourteen.

**Instrument.** `grep -n '^\s*\(from\|import\)\s'` over
`synaptic_host/modal_provider.py` (1077 lines) and
`synaptic_host/modal_training.py` (660 lines), then each multi-line
import block printed verbatim and its names counted.

| Engine module | via `modal_provider.py` | via `modal_training.py` | distinct |
|---|---|---|---|
| `synaptic_tuner.api.v1` | 1 | 12 | 12 |
| `synaptic_tuner.api.v1.modal` | 15 | 5 | 20 |
| `tuner.project.manifest` | 0 | 1 | 1 |
| **total** | | | **33** |

`ProjectContext` is the only name imported by both modules, which is why
1 + 12 gives 12 distinct.

**The module set is three, and it spans two top-level packages.**
`synaptic_tuner` and `tuner` are both engine packages, both regular
packages with `__init__.py`, both resolved from the submodule.
`tuner.project.manifest` is easy to miss because every other engine
import in these two files starts with `synaptic_tuner`.

**A fourth import is dynamic and is not an engine name.**
`modal_training.py:364` does `importlib.import_module("modal")`. That is
the Modal SDK itself, resolved on the submitting host at call time, not
the engine namespace. It is the reason the SDK must be present on the
submit side and is picked up again in section 7.

**Every one of the 33 names resolves at `ce539b70`.** Result: 33 FOUND,
0 MISSING. The census ran with `sys.path[0]` bound to the worktree
submodule, from a neutral working directory, and `PYTHONPATH` was never
exported.

**The engine-binding convention, corrected.** The plan proposed asserting
`synaptic_tuner.__file__` starts with the engine root. That convention
fails on exactly the case it exists to catch: a namespace package has
`__file__ is None`, so reading it raises `AttributeError`/`TypeError`
rather than reporting a wrong binding. The corrected form, used here and
recommended for the ARCHITECT ruling and the TEST-phase convention, is:

- resolve with `importlib.util.find_spec(name)`;
- if `spec.origin` is a real path, assert it is relative to the engine
  root;
- if `spec.origin` is `None` or `"namespace"`, assert every entry of
  `spec.submodule_search_locations` is relative to the engine root, and
  treat an empty search-location list as a failure;
- pair that with a separate assertion that the gitlink equals
  `ce539b70`, because containment proves *which tree* and the gitlink
  proves *which commit*. Neither implies the other.

All three engine modules reported `origin contained=True` and resolved
under the submodule.

**A measurement hazard worth recording for TEST.** The first census run
died inside `dataclasses` with a `sqlite3.ProgrammingError`, because a
stale `inspect.py` in the scratch directory shadowed the standard
library: the script's own directory sits on `sys.path` and wins for
stdlib names. Any import-census harness must run from a directory that
contains no stdlib-named module. This is the same class as the run-8
wrong-tree import incident recorded as follow-up #215: the search path,
not the intended target, decides what gets imported.

---

## 3. The Modal environment: all four objects exist, owned by the user

Measured with read-only listings only. No secret value was read,
displayed, or logged, and no length of one was recorded.

Environment `main`:

| Object | Name | State | Created | Created by |
|---|---|---|---|---|
| App | `synaptic-training-v1` (`ap-jefnCdxyJ8H1pCBxng9cU8`) | **deployed**, 0 tasks | 2026-08-26 07:12 EDT | joseph-86429 |
| Volume | `synaptic-training-control-v1` | present | 2026-08-26 05:27 EDT | joseph-86429 |
| Volume | `synaptic-training-artifacts-v1` | present | 2026-08-26 05:27 EDT | joseph-86429 |
| Secret | `synaptic-training-runtime-v1` | present, last used 2026-08-26 10:46 EDT | 2026-08-26 05:27 EDT | joseph-86429 |

Commands run: `modal volume list --env main`,
`modal secret list --env main`, `modal app list --env main`.

**These are the names the code demands.** `training/providers/modal.json`
declares `environment_name: "main"`, the two volume names and the secret
name; `deployment_v1.py:17` fixes `APP_NAME = "synaptic-training-v1"`.
All four match what exists.

**Ownership is the operator's own account,** so nothing here is shared
infrastructure and no other party's resources are involved.

**Three consequences ARCHITECT should weigh.**

1. **The app is already deployed and predates this work by ten days.**
   Something deployed `synaptic-training-v1` on 2026-08-26 and the
   runtime secret was used at 10:46 EDT the same day. The smoke is
   therefore not first light for the *deployment*, only for the prepared
   path through it. What that earlier deployment contains, and whether it
   should be torn down or overwritten before the smoke, is unmeasured
   and is a decision, not a finding.

2. **`create_if_missing=False` means the code will not create these.**
   `deployment_v1.py:103-119` looks up both volumes with
   `create_if_missing=False` and the secret with an explicit
   `required_keys` list. They must pre-exist, and they do.

3. **The volume version is a live mismatch risk that the listing cannot
   show.** The code requests `version=MODAL_VOLUME_V1`, and
   `facade.py:19` sets `MODAL_VOLUME_V1 = 1`. The CLI listing does not
   print a volume's version, so I cannot confirm from here that these two
   volumes are version 1. If they were created as version 2, the lookup
   fails at submit. **Unmeasured, cause: the read-only listing does not
   expose the field.** A `modal volume get` or the API would settle it.

**Secret key coverage is asserted by the code, not by me.**
`modal_provider.py:168` fixes the runtime secret keys to exactly
`("HF_TOKEN", "SYNAPTIC_EVIDENCE_MAC_KEY")` and refuses any other tuple;
`training/providers/modal.json` declares the same two under
`runtime_secret.required_keys`. Whether the live secret actually carries
both keys is **unmeasured**: reading it would mean reading credential
material, which is forbidden. `Secret.from_name(..., required_keys=…)`
enforces it at submit time, so the failure would be loud and early
rather than silent.

---

## 4. The A10 rate is absent from the tree; here is the timeout ARCHITECT must rule

**The rate is not in the tree, and I searched for it.**

- `grep -rn "modal-a10-v1"` across the whole checkout returns matches
  only in `training/providers/modal.json` (lines 4 and 8) and in
  `scratch/ab54_drive/tests/…` fixtures. The profile name is a **label**,
  not a rate table. Nothing resolves it to a price.
- `grep -rniE "per_hour|price|rate_minor|usd_per|cost_per|hourly"` over
  `synaptic_host/modal_provider.py`, `synaptic_host/modal_training.py`
  and the whole `tuner/execution/providers/modal/` package returns
  **nothing**.
- The only prices anywhere in the tree belong to another provider's test
  fixtures at `synaptic-tuner/tests/cloud/conftest.py:133` and must not
  be used for Modal.

**The two bounds do not compose, which is the point.**

| Bound | Value | Where |
|---|---|---|
| Wall-clock timeout | 3600 s | `training/providers/modal.json` `deployment.timeout_seconds`, passed to `@app.function(timeout=…)` at `deployment_v1.py:142` |
| Budget ceiling | 100 minor units = USD 1.00 | `training/providers/modal.json` `budget.maximum_cost_minor_units`, enforced by `BoundedGrantProvider` at `modal_training.py:521-522` |
| Hard timeout range | 1 to 86400 s | asserted twice: `modal_provider.py:175` and `SubprocessSftRunner.__init__`, `runtime.py:212-213` |

Break-even is where one hour of A10 costs exactly USD 1.00. Above that
rate the **budget binds first** and the 3600 s timeout is dead headroom;
the run ends on a budget refusal rather than on a clock the Host set.
The aftermath of a budget refusal in the artifact volume has never been
measured on this path.

**The budget-derived timeout, once the rate `R` (USD per hour) is
known:**

```
timeout_seconds  =  floor( 3600 * (maximum_cost_minor_units / 100) / R )
                 =  floor( 3600 / R )        with the ceiling at USD 1.00
```

Apply a safety margin below that, so the Host's clock fires before the
budget does. Worked examples, so ARCHITECT can rule without redoing the
arithmetic:

| A10 rate (USD/hr) | Budget-derived bound | Verdict against the shipped 3600 s |
|---|---|---|
| 1.00 | 3600 s | exactly break-even |
| 1.10 | 3272 s | budget binds first |
| 2.00 | 1800 s | budget binds first, timeout is half dead |
| 3.00 | 1200 s | budget binds first |

**Recommendation to ARCHITECT: rule the timeout, do not inherit 3600 s.**
3600 s is a default that was never derived from the budget. Set the
smoke's `timeout_seconds` to the budget-derived bound with margin so
first light ends on a clock the Host controls. Obtaining `R` is a
one-line lookup against Modal's public pricing and is the only missing
input.

---

## 5. `required_environment` is on a different class than the dispatch said

**Premise correction.** The dispatch asked for
`ModalRuntimeLockV1.required_environment`. **That attribute does not
exist on that class.** `ModalRuntimeLockV1` is at
`tuner/execution/providers/modal/config.py:175-235`; its `__post_init__`
validates a closed key set of
`{schema_version, sdk_version, registry_reference, python, locked_files,
ml_stack}` and its properties are `registry_reference`, `sdk_version`,
`image_digest`, `python_implementation`, `python_version`,
`python_executable`, `python_executable_digest`. No environment at all.

The real `required_environment` is a **local variable** inside the
source-lock validator at `tuner/project/execution_source.py:489-500`,
the same construct already named in open blocker #153 as
"SourceLockV1 required_environment". This is the class follow-up #277
flags as holding **thirteen** keys, not eleven. I confirm thirteen:

```
PYTHONNOUSERSITE  PYTHONSAFEPATH  PYTHONPATH
SYNAPTIC_ENGINE_ROOT  SYNAPTIC_PROJECT_ROOT  SYNAPTIC_ARTIFACT_ROOT
SYNAPTIC_STATE_ROOT  SYNAPTIC_TRACKING_ROOT  SYNAPTIC_CACHE_ROOT
SYNAPTIC_TMP_ROOT  HF_HOME  TRANSFORMERS_CACHE  WANDB_DISABLED
```

**The check is a superset test, not equality.**
`execution_source.py:501` reads
`if any(environment.get(key) != value for key, value in required_environment.items())`.
Extra keys are permitted; the thirteen must each be present with the
exact value. Values are derived from the seven-name `roots` map
(`engine`, `project`, `artifacts`, `state`, `tracking`, `cache`, `tmp`).

**Does the environment block satisfy it? Yes, by construction, and the
Host contributes almost none of it.**

The Host declares only **two** keys in
`training/providers/modal.json` `runtime_environment`: `PATH` and
`LANG`. The engine builds the thirteen itself at
`resolution.py:562-576`, checks that any overlapping Host key agrees
(`resolution.py:577-579`, raising *"deployment runtime environment
conflicts with fixed isolation"*), then merges with the fixed block
winning:

```python
environment = {**locked_deployment.runtime_environment, **fixed_environment}
```

So the child environment is **15 keys**: the Host's 2 plus the engine's
13, with no overlap in the shipped configuration. The thirteen required
keys are satisfied because the same literal dict that the validator
demands is the one `resolution.py` writes.

**The consequence for ARCHITECT is the one blocker #153 already
records.** The Host cannot move `HF_HOME` or `TRANSFORMERS_CACHE` off
the cache root, because the engine pins both to
`{run_root}/cache/huggingface` and `{run_root}/cache/transformers` and
the validator refuses anything else. On the local Docker path this was
worked around by pointing them at `/tmp`; on the Modal path that
workaround is unavailable. The container roots are
`/workspace/engine`, `/workspace/project`, and
`/workspace/run/{run_id}/{artifacts,state,tracking,cache,tmp}`.

---

## 6. The free offline dry run: it cannot run here, and I can prove why

**Verdict: the dry run through `build_modal_deployment` is blocked before
any Modal call, so it is free but also empty. The go/no-go is
ARCHITECT's; the sufficient proof and the missing proof are both stated
below.**

**What I ran, and why it is provably network-free.**
`build_modal_deployment` is at `deployment_v1.py:86`. Its first
statement, `:95-96`, is

```python
if getattr(sdk, "__version__", None) != EXACT_MODAL_SDK_VERSION:
    raise ModalFacadeError("modal_sdk_version_mismatch")
```

and the first call that could open a socket is `sdk.Volume.from_name` at
`:103`. I passed a stub `sdk` object carrying **only** `__version__` and
no `Volume`, `Secret`, `Image` or `App` attribute at all. That is the
proof of freeness: had execution reached any network path, it would have
raised `AttributeError` on the stub instead. It did not.

| Arm | `sdk.__version__` | Result |
|---|---|---|
| installed version | `1.5.1` | `ModalFacadeError: modal_sdk_version_mismatch` |
| required, no client | `1.5.4` | `TypeError: explicit Modal client and worker are required` |
| required, bad spec | `1.5.4` | `TypeError: ModalDeploymentSpecV1 is required` |

**Sufficient proof that the dry run is free: obtained.** Two independent
guards refuse before the first Modal object is touched, and a stub with
no Modal attributes survives all three arms.

**What I could not obtain.** Whether the dry run would still be free
**at 1.5.4 with a real authenticated client**. Past the two guards it
calls `Volume.from_name`, `Secret.from_name` and
`Image.from_registry(...)`. Whether those are lazy handles or eager
lookups at 1.5.4 is a property of a third-party SDK at a version that is
not installed here, and installing it would change the operator's
environment. I did not install it and did not guess. `Secret.from_name`
taking `required_keys` and `client=` reads as a validating lookup, which
would mean a network call, but that is inference, not measurement.

**Two things ARCHITECT should weigh before treating a dry run as a
gate.**

1. **It would not have caught B-19.** The dry run exercises deployment
   construction. The stale-digest refusal fires container-side at
   `runtime.py:189-194`. Nothing on the submit side compares the lock to
   the files it names, so a green dry run says nothing about the class
   of defect that will actually stop the first paid submit.
2. **Running it needs 1.5.4 installed somewhere.** That is a submit
   container concern, which is section 7, not a change to the operator's
   host.

---

## 7. Submit-side container recipe: shape only

CODE phase owns the recipe. This is the shape it has to satisfy, with
each constraint tied to the line that imposes it. No Dockerfile here.

**What the submit container is.** The machine that runs the Host and
calls Modal. It is **not** the training container. It needs no GPU, no
CUDA, and not the unsloth image.

**Hard constraints.**

1. **`modal==1.5.4` exactly.** Not a floor, not a range.
   `deployment_v1.py:95` and `facade.py:71-74` compare
   `sdk.__version__` for equality and refuse anything else. Install from
   `synaptic-tuner/requirements/modal-launcher-v1.lock` with
   `--require-hashes --only-binary :all:`, matching
   `launcher.py:401-402`. Do not let a resolver near it.
2. **The engine at `ce539b70` on `sys.path`, established in code, never
   via `PYTHONPATH`.** Both `synaptic_tuner` and `tuner` are imported
   (section 2), and both live at the submodule root, so one entry covers
   both. B-15 was exactly this omission on the Docker provider. Bind it
   the way the corrected convention in section 2 describes, and assert
   the gitlink alongside it.
3. **Credentials injected at run time, never baked into an image
   layer.** A Modal token reaches the SDK through `MODAL_TOKEN_ID` /
   `MODAL_TOKEN_SECRET` or a mounted `.modal.toml`. Neither belongs in a
   layer, a build arg, or this repository. The two runtime secrets
   (`HF_TOKEN`, `SYNAPTIC_EVIDENCE_MAC_KEY`) are **not** submit-side at
   all: they are delivered inside the training container by the Modal
   Secret, and `SubprocessSftRunner.run` (`runtime.py:227-231`) reads
   them from `os.environ` there, raising exit 120
   `credential_unavailable` if absent.
4. **Egress to the Modal API is required by design.** The submit side is
   a client. This is not the training container's egress question.
5. **Pin the base image by digest** and keep the layer set minimal, for
   the same reason the trainer image is digest-pinned at
   `registry_reference`.

**What the container must NOT carry.**

- The trainer image or its ML stack. `ml_stack` (`torch`,
  `transformers`, `trl`) is recorded in the runtime lock for the
  *container*, not the submitter.
- Python 3.11.14 as a requirement. That version and
  `/opt/conda/bin/python3` are the **container-side** interpreter the
  lock pins (`config.py:185`). The submit side is not bound to it. Do
  not copy the constraint across the seam.
- Any project or engine source baked as a layer. The container
  materializes source by cloning both repositories at run time
  (`GitDualCloneMaterializer`); `add_local_python_source` is called with
  `copy=False`.

**Two shape facts CODE will need.**

- `BOOTSTRAP_SOURCE_MODULES = ("tuner", "synaptic_tuner")` at
  `deployment_v1.py:22` is what gets attached to the image, and it names
  both top-level packages, matching section 2's module set.
- The function is declared with `retries=0`,
  `restrict_modal_access=True`, `single_use_containers=True`,
  `include_source=False`, mounts `CONTROL_MOUNT = /workspace/control`
  and `ARTIFACT_MOUNT = /workspace/run` (`deployment_v1.py:134-145`).
  These are the standing safety properties and none of them should be
  relaxed for the smoke.

---

## 8. Blocker B-19, found while measuring section 1

Filed separately as task #431 and reported to team-lead. Recorded here
because it is external-surface evidence and it changes the sequencing.

**At `ce539b70`, two of the seven `locked_files` members recorded in
`modal-runtime-v1.lock.json` do not match the files they name.**

| Member | Recorded | Actual (blob) | |
|---|---|---|---|
| `modal_remote` (`tuner/execution/providers/modal/remote.py`) | `88d20d1abba8` | `8574b80084d3` | **drifted** |
| `sft_runtime` (`Trainers/sft/runtime_v1.py`) | `da1f0f0717a9` | `d838cc507036` | **drifted** |
| `dependency_lock` | `8273b49a3b61` | `8273b49a3b61` | matches |
| `deployment_wrapper`, `modal_mounted_io`, `modal_producer`, `modal_runtime` | | | match |

**Where it bites.** `runtime.py:189-194` re-hashes every locked member
against the freshly cloned engine and raises
`ModalRemotePhaseError(124, "locked_source_mismatch")`. That is inside
the paid container, after the image pull, after both clones, after the
gitlink check at `:179-183`, and before the trainer starts.

**Why it is B-5 class.** `c272b834` (2026-09-01 05:40, "Add offline SFT
worker bundle") regenerated the runtime lock. `c0cec778` (2026-09-01
09:57, "Close offline SFT execution path") then edited both drifted
members. `git merge-base --is-ancestor c272b834 c0cec778` confirms the
lock came first and nothing regenerated it through `ce539b70`.

**Why nothing upstream catches it.** `config.py:242-250`
`validate_selection` compares the selection against the lock, but
`resolution.py:191-193` builds that selection **from** the lock via
`locked_digest()`. It is self-consistent by construction and structurally
cannot observe file drift. The only lock-to-file comparison in the system
is the container-side one.

**`dependency_lock` was a false positive I caught before reporting.** A
first pass measured three mismatches using worktree hashes. See section 0
for the CRLF mechanism.

**Remedy is ARCHITECT's to rule**, and it is an engine change:
regenerate `modal-runtime-v1.lock.json` against `ce539b70`'s actual
files, which means an engine commit, a push, and a Host pin move under
the B-5 procedure, the route B-14 and B-16 took. Not touched here; the
submodule is read-only for this task.

---

## 9. Summary of what is measured, unmeasured, and owed

**Measured and settled.**

- The SDK pin resolves to 1.5.4 through a hash-locked authority; not B-5
  class; `requirements-cloud.txt` is inert (section 1).
- 33 engine names across 3 modules and 2 top-level packages, all present
  at `ce539b70`; the plan's "fourteen" is superseded (section 2).
- App, both volumes and the secret all exist in env `main`, owned by the
  operator; the app is already deployed (section 3).
- The A10 rate is absent from the tree; the budget-derived timeout
  formula and worked examples are in section 4.
- `required_environment` is thirteen keys on the source-lock validator,
  not on `ModalRuntimeLockV1`; the shipped 15-key child environment
  satisfies it by construction (section 5).
- The dry run is provably free and provably blocked at 1.5.1
  (section 6).
- B-19 (section 8).

**Unmeasured, with the cause named.**

| Item | Why | How to settle |
|---|---|---|
| Volume version of the two live volumes | the read-only listing does not print the field | `modal volume get`, or the API |
| Whether the live secret carries both required keys | reading it means reading credential material | leave it to `Secret.from_name(required_keys=…)` at submit; it fails loud |
| Whether the dry run stays network-free at SDK 1.5.4 | 1.5.4 is not installed and installing it would change the operator's host | run it inside the submit container of section 7 |
| What the 2026-08-26 deployment of `synaptic-training-v1` contains | out of scope for a read-only listing | a decision for ARCHITECT, not a measurement |
| The A10 hourly rate | not in the tree, by design | Modal public pricing |

**Owed to other owners.**

- The plan's line 51 still reads "`runtime.py` (git clone `:124-183`;
  secret keys `:208-233`)" after line 22 was corrected. The secret-key
  half is a residual half-fix. The plan is the lead's to fix and I have
  not touched it.
- `CLAUDE.md` was not written by any route, per the dispatch. Flagged
  here as required.
