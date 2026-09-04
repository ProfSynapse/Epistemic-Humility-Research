# Host path simplification review — factual inventory

**Phase:** PREPARE (plan consultation). **Task:** #285, for the review plan #282 / follow-up #209.
**Tree read:** `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean` at HEAD
`557ce1be48363e18c405e869da95d341a639df96`; engine submodule pin `ce539b70`.
**Author:** preparer-b16. **Consumer:** architect-simplify (#286).

This document is evidence, not a verdict. It carries three factual sections the architect rules from,
then five short consultation sections. **It does not answer keep / simplify / replace for any layer.**
That is #286's to write.

Every claim below carries a `file:line`, a section number in
`docs/architecture/prepared-path-alpine-diagnostic.md` (cited as **diag:N**), or a task id. Where a number
is not recorded anywhere I write **not stated** rather than estimating.

---

## 0. Reading corrections the architect must not inherit

Four names in the brief for this task, and in #209, do not survive contact with the source. Carrying them
forward would produce a ruling against symbols that do not exist.

| The brief says | The source says | Evidence |
|---|---|---|
| `class SourceLockV1`, with thirteen keys | **No such class.** The thirteen keys are the `required_environment` dict inside `ExecutionSourceV1.__post_init__` | `synaptic-tuner/tuner/project/execution_source.py:358` (class), `:489-500` (the dict). `SourceLockV1` appears 11 times in the tree, all in prose and comments. Separate real symbols `SourceLock`, `SourceLockBindingV1`, `SourceLockError` are imported at `:20-22` and are different things. Task #277 is already open on this drift. |
| The thirteen-key count | Correct at thirteen. **diag:5108 says eleven and is wrong** | Audit #275 YELLOW-1, task #277, still unfixed at HEAD. Counted from the literal: 13. |
| `--user 1000:1000` is the container user | The value is **profile-derived, not a constant**. The grammar admits any `uid:gid` | `synaptic_host/docker_v1/control_private.py:46`; profile field at `synaptic_host/docker_prepared_composition.py:65` |
| B-7 would be removed by dropping `docker.exe` | **False.** B-7 is in a `git` child, not a docker child | `synaptic_host/security.py:1123` `class ScopedGitRemoteReader`, `:1130` `_run`, `:1142-1147` the `SystemRoot` carry, `:1149` `subprocess.run`, `:1169` `git ls-remote`. See section 3.4. |

One further scale correction. The brief says the Host is "25 modules, 17,255 lines". That is the top level
only. The package has three subpackages.

| Tree | Files | Lines |
|---|---|---|
| `synaptic_host/` top level | 25 | 17,255 |
| `synaptic_host/docker_v1/` | 22 | 13,491 |
| `synaptic_host/local_io_v1/` | 6 | 7,565 |
| `synaptic_host/bundle_io_v1/` | 4 | 1,798 |
| **Host total** | **57** | **40,109** |
| `tests/` total | 63 | 40,028 |
| of which cover the twelve layers below | 14 | 12,854 |

**The test tree is the same size as the source tree.** That ratio is itself an input to the review.

---

## 1. LAYER INVENTORY

Twelve layers. For each: what it is, where it lives, what it buys a desktop app on a user's own machine,
what it buys a web app driving cloud compute, and what it costs in lines, tests and blockers.

The two consumer columns are the analytic point of this section. Read them as a pair: a layer that buys
the same thing in both columns is load-bearing wherever the product goes; a layer that buys something in
one column and nothing in the other is a candidate the architect can price.

### 1.0 Summary table

| # | Layer | Defining site | Impl. lines | Blockers it participated in |
|---|---|---|---|---|
| 1 | Source lock (`ExecutionSourceV1`, 13 required env keys) | `synaptic-tuner/tuner/project/execution_source.py:358` | ~205 | B-10-R1, B-10-R2 (as cause) |
| 2 | Staging bound + scoped staging | `synaptic_host/docker_staging.py:45`, `:1296` | ~110 | B-12, B-9-R2, B-10, B-10-R2 |
| 3 | Admission resolver + 19-key container env | `synaptic_host/docker_training.py:432`, dict `:452-490` | 128 | B-9-R1, B-16, B-10-R1 |
| 4 | Composition policy + three digests | `synaptic_host/docker_v1/model.py:1135-1302` | ~115 | B-1, B-1', B-4, B-9 (digest churn) |
| 5 | HMAC evidence + `.synaptic` ACL chain | `synaptic_host/security.py:807`, `:1050` | ~555 | B-11, B-11-R1 |
| 6 | Sealed four-key CLI env + constructed endpoint | `synaptic_host/docker_prepared_composition.py:116`, `:149` | ~138 | B-13, B-7 (family only) |
| 7 | Worker closure manifest (66 members) | `synaptic-tuner/tuner/runtime/manifests/offline-sft-worker-v1.json` | ~166 Host + 675 engine | B-5, B-14, B-9-R1, B-16 |
| 8 | Container user + cache keys | `synaptic_host/docker_prepared_composition.py:65` | ~45 | B-9, B-9-R1, B-16 |
| 9 | Network-disabled, credential-free container | `synaptic_host/docker_v1/control_private.py:406` | ~60 | none |
| 10 | Result envelope + cause line | `synaptic_host/cause_line.py:116`, `synaptic_host/cli.py:331` | ~255 | B-11 (co-ruling), B-15 |
| 11 | Driver probes P1-P11 | `.claude/skills/host-docker-run/scripts/run_prepared_training.py:152-1107` | ~955 | B-6, B-9, B-12, B-13, B-15 (all as *detectors*) |
| 12 | Docker CLI verb enum + runner | `synaptic_host/docker_v1/model.py:1011`, `cli.py:680-990` | ~427 | B-4, B-13 |

### 1.1 Source lock — `ExecutionSourceV1`

**What it is.** A frozen dataclass that binds one execution to an exact pair of git commits, seven runtime
roots, a CPython version, and a closed environment map. Its `__post_init__` refuses anything that does not
match exactly.

**Where.** `synaptic-tuner/tuner/project/execution_source.py:358`; schema constant at `:26`. **This layer
is in the engine, not the Host.** The Host's job is to construct a value that satisfies it.

The thirteen `required_environment` keys, verbatim from `:489-500`:

```
PYTHONNOUSERSITE=1   PYTHONSAFEPATH=1        PYTHONPATH=<engine>
SYNAPTIC_ENGINE_ROOT SYNAPTIC_PROJECT_ROOT   SYNAPTIC_ARTIFACT_ROOT
SYNAPTIC_STATE_ROOT  SYNAPTIC_TRACKING_ROOT  SYNAPTIC_CACHE_ROOT
SYNAPTIC_TMP_ROOT    HF_HOME=<cache>/huggingface
TRANSFORMERS_CACHE=<cache>/transformers      WANDB_DISABLED=true
```

Enforced at `:501-502` with `.get(key) != value` — subset-exact, so extra keys are permitted and the
Host's 19-key dict passes as a superset. Adjacent invariants in the same `__post_init__`: seven exact roots
`:418-419`, non-aliasing `:426`, source/writable disjointness `:445-461`, CPython pin `:462-472`.

**Desktop app on a user's machine.** Reproducibility, not threat. It is the statement that this run is
this pair of commits under this interpreter with these roots, so a run can be replayed or attributed
later. On a user's own machine the adversary and the operator are the same person, so its security value
is close to zero; its provenance value is the whole point.

**Web app driving cloud compute.** The same statement becomes a trust boundary rather than a note. A
tenant's run must be pinned to source the tenant cannot alter after admission, and `HF_HUB_OFFLINE` /
`WANDB_DISABLED` / `PYTHONNOUSERSITE` are the isolation the operator sells. Here it is load-bearing.

**Cost.** ~205 lines. Directly caused **B-10-R1** (`#153`, open): the `HF_HOME` pin to the cache root
cannot be moved from the Host, because the lock refuses any other value at admission, and
`execution_source.py` is itself a closure member so the change is the full B-5 shape. The Host records
this in a nine-line comment at `synaptic_host/docker_training.py:472-480`. B-10-R1 in turn is the direct
cause of **B-10-R2** (`#280`, open), the blocker that stopped run 11.

### 1.2 Staging bound and scoped staging

**What it is.** Two things now. A byte bound on what may be staged, and, since B-12, a rule that what gets
staged is exactly the source lock's own `inputs` descriptors rather than the whole superproject.

**Where.** `synaptic_host/docker_staging.py:45` `_MAX_PROJECT_ARCHIVE_BYTES = 256 * 1024 * 1024`
(268,435,456), siblings `_MAX_PROJECT_EXPANDED_BYTES` `:46`, `_MAX_PROJECT_ENTRIES = 20_000` `:47`.
Enforcement at `:1338-1339`. Scoped staging is `_stage_locked_project_inputs` `:1296-1364`, re-verified by
`_verify_staged_project_inputs` `:1367-1407` with a set equality at `:1382-1384`. Blobs are read from the
commit via `_git_selected_blobs` `:1092`, never from the checkout.

**Desktop.** Bounded work and a defence against a runaway stage on the user's own disk. The set equality
also gives a real reproducibility property: the staged tree is provably the recorded input set, not
whatever the working tree happened to hold.

**Cloud.** A hard resource bound per tenant, which is a billing and denial-of-service control, not a nicety.
The read-from-commit rule matters more here because the checkout is not the tenant's to trust.

**Cost.** ~110 lines, 6 dedicated tests (`tests/synaptic_host/test_docker_staging.py:347,370,397,434,472,511`),
plus 7 driver-side assertions. **B-12** (`#179`) is entirely this layer: the superproject archive was
412,794,880 bytes against the 268,435,456 bound, an overshoot of 144,359,424, to deliver *one JSONL
fixture* (diag:3499-3518). The ledger calls B-12 "the first platform-independent blocker in this
workstream" (diag:3511-3512). The layer also owns **B-9-R2**, **B-10** and **B-10-R2** through
`_verify_artifact_topology`, treated in section 3.5.

The layer carries one self-documented dead belt: `_MAX_PROJECT_EXPANDED_BYTES` is unreachable by
construction and is retained as defence in depth, argued in a ten-line comment at `:1396-1405`. Removing
it was priced at "eight files to delete a constant nobody can reach" (diag:4398).

### 1.3 Admission resolver and the 19-key container environment

**What it is.** `DockerAdmissionResolverV1` builds the exact environment the container will run under, and
the seven roots it is expressed in.

**Where.** `synaptic_host/docker_training.py:432`. Roots dict `:446-451`. Environment dict literal
`:452-490`. Second parallel construction at `:911-943`.

The nineteen keys, counted from the literal: `PATH`, `PYTHONNOUSERSITE`, `PYTHONSAFEPATH`, `PYTHONPATH`,
`SYNAPTIC_ENGINE_ROOT`, `SYNAPTIC_PROJECT_ROOT`, `SYNAPTIC_ARTIFACT_ROOT`, `SYNAPTIC_STATE_ROOT`,
`SYNAPTIC_TRACKING_ROOT`, `SYNAPTIC_CACHE_ROOT`, `SYNAPTIC_TMP_ROOT`, `HF_HOME`, `TRANSFORMERS_CACHE`,
`HOME`, `XDG_CACHE_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, `USER`, `WANDB_DISABLED`.

**Desktop.** Determinism. The container's environment is authored in one place and is the same on every
machine, which is what makes a user-side reproduction meaningful.

**Cloud.** The same dict is the isolation contract: no inherited operator environment reaches the tenant's
process, and the empty-secrets digest (`:506-509`) is signed into the lock so a later secret requirement
changes the lock digest.

**Cost.** 128 lines. Caused **B-9-R1** (four unredirected cache keys) and **B-16** (the `USER` key). Both
were *enumeration* failures: the ledger's own phrasing is "B-7 was an unenumerated environment variable"
and "B-9-R1 is an unenumerated set of cache writers", concluding "the enumeration argument has now failed
twice on this workstream" (diag:1814-1816). With B-16 it has now failed three times, all in this layer or
its siblings. Each failure costs an engine allowlist edit **plus** closure regeneration **plus** a pin
move, because the allowlist lives in two engine files that are themselves closure members.

### 1.4 Composition policy and the three digests

**What it is.** Three chained sha256 digests over canonical JSON: an environment digest, an endpoint
descriptor digest, and a policy digest that transitively covers both.

**Where.** Environment digest `synaptic_host/docker_v1/model.py:1138`, computed `:1180`, self-checked
`:1162-1166`. Descriptor digest `:1214-1215`, canonical body `:1205-1211`. Policy digest `:1232`, computed
`:1298`, body `:1261-1271` — which includes `endpoint_descriptor_digest` and `environment_digest`, so it is
the root of the chain. Durability equality at `docker_prepared_composition.py:228-230`. Persisted at
`docker_execution_state.py:195,213,231,293`.

**Desktop.** Tamper-evidence against accidental drift, mainly. It catches a changed profile or a changed
endpoint between the durable row and the live composition, which is a correctness property.

**Cloud.** The same chain is the audit record: a stored digest lets an operator prove after the fact which
policy a run executed under. In a multi-tenant setting that is the difference between an assertion and
evidence.

**Cost.** ~115 lines. No blocker is attributable to the digests themselves. They are, however, the reason
several small fixes were not small: adding one profile field changes `profile.digest`, which changes the
provider policy digest, the execution context, the plan fingerprint and the stage key (diag:430-434). B-1's
fix touched five files for that reason (diag:409), and B-9's touched eight (diag:1560-1586).

**Note for the architect:** none of the three digest properties carries a docstring stating why it exists.
The rationale is recoverable only from the diagnostic document.

### 1.5 HMAC evidence and the `.synaptic` private-storage ACL chain

**What it is.** Two things bolted together. A keyed-HMAC authority family that signs and verifies thirteen
typed record kinds, and the Windows-ACL / POSIX-mode machinery that guarantees the key file's directory
chain is private.

**Where.** Sign `synaptic_host/security.py:1050-1058` (`purpose + b"\0" + payload`, domain-separated),
verify `:1060-1062` with `hmac.compare_digest`. Thirteen authorities at `synaptic_host/docker_v1/authority.py:142-190`.
Chain entry `security.py:672-701`. Ensure/repair `:807`, two-pass, leaf-first at `:856-863`, root-first
create at `:864-876`. Windows repair `:536`, predicate `:467-531`, validator `:445` → `:388-439`. POSIX
`:718`, `:754-775`, `:783-805`.

What stays refused, each with a line: an explicit non-inherited ACE `:529-530`; an already-protected DACL
`:514`; a NULL DACL `:510`; another user's directory `:515` / `:768`; a reparse point or symlink `:573` /
`:755`; a non-directory `:572` / `:755`.

**Desktop.** This is the layer whose value proposition is weakest on a single-user machine and it is worth
stating plainly. The threat it defends is another *local* principal reading or forging the HMAC key. On a
desktop app the user is the machine's owner; an attacker with a local account able to write the user's
project directory has already won by editing the project. What it does buy is integrity of the durable
rows against accidental corruption and against a second tool writing the same tree.

**Cloud.** Here the same layer is doing real work, but only if the Host runs on the *server*. The key
authenticates control-plane records that a tenant must not forge. If the cloud shape is instead "the web
app calls a provider API and the Host never touches a shared machine", this layer's threat model does not
apply in that form either.

**Cost.** The single most expensive layer: **~555 lines of the 1,169 in `security.py`**, and
`tests/synaptic_host/test_security.py` is 1,093 lines with 20 named tests. It caused **B-11** and
**B-11-R1**, which is two blockers and two imPACT cycles (#161 cycle 7, #176 cycle 8). B-11-R1 has the
sharpest finding in the whole record: on volumes where the inherited set propagates, "the repair
manufactures the one state its own predicate is written to refuse, on the object it is trying to fix, and
then refuses it" (diag:3291-3293). The mechanism is still recorded as a hypothesis, not a fact, because the
author had "asserted a mechanism twice in this section and been wrong twice" (diag:3320-3321).

One residual is open and untouched: **#170**, the durable rows database under `.synaptic` keeps inherited
ACEs after the B-11 repair (diag section 20.18).

### 1.6 Sealed four-key CLI environment and the constructed endpoint

**What it is.** The exact, order-sensitive environment handed to the `docker.exe` child, plus a hard-coded
endpoint that replaced a `docker context` lookup.

**Where.** Built `synaptic_host/docker_prepared_composition.py:116-120`; enforced by tuple equality at
`synaptic_host/docker_v1/model.py:1144-1149`; per-value Windows-drive-path check `:1155`; key-name denylist
`:1156-1161` refusing `DOCKER_*`, `TOKEN`, `AUTH`, `PROXY`. Endpoint constructed
`docker_prepared_composition.py:149-158`, pinned at `model.py:1193-1203`, placed in argv at
`docker_v1/cli.py:806-807`.

The four keys: `SystemRoot`, `TEMP`, `TMP`, `WINDIR`. No `PATH`, no `HOME`, no `USERPROFILE`. The endpoint:
`npipe:////./pipe/dockerDesktopLinuxEngine`. **There is no `unix://` string anywhere in `synaptic_host/`;
this layer is Windows-only by construction.**

**Desktop.** It prevents the operator's ambient environment from steering the docker client — a real
property, since `DOCKER_HOST` or a proxy variable in the user's shell would otherwise silently redirect the
run.

**Cloud.** Almost nothing, because in a cloud shape there is no operator shell to seal against; the process
environment is whatever the service defines. The layer's value is proportional to how untrusted the ambient
environment is, and a server's own environment is the most controlled one in the product.

**Cost.** ~138 lines and 12 dedicated tests. It caused **B-13** outright (`#196`, imPACT cycle 10): the
four-key tuple omitted `USERPROFILE`, so `docker context inspect` resolved a relative `.docker` path and
exited 1, before any container had ever been created on this path. The ledger's summary is the sharpest
sentence in the document: "the path spends its only dependency on the operator's profile to learn a
constant it already has written down twice" (diag:3916-3917).

The B-13 fix produced the endpoint construction, which is now *cheaper* than what it replaced, and it
deleted a whole module (`docker_v1/endpoint.py`, task #204).

### 1.7 Worker closure manifest

**What it is.** A signed inventory of the engine files the container is allowed to execute.

**Where.** `synaptic-tuner/tuner/runtime/manifests/offline-sft-worker-v1.json`. Measured directly from the
file: `member_count` **66**, `len(members)` **66**, `payload_bytes` **685,534**, `closure_digest`
`0cc5ec57a2f7f13f451a35af7dab9d221e2d6981e296c0bf308e19c2eaa2b3a0`. Every member carries exactly
`('git_mode', 'path', 'sha256', 'size_bytes')`.

Generated by `synaptic-tuner/scripts/regenerate_offline_sft_worker_closure.py` (409 lines). Verified
Host-side by `_load_locked_closure` `synaptic_host/docker_staging.py:1129-1244` — the digest is recomputed
twice, once from the declared document and once from observed blob values. Staged tree re-verified by
`_verify_staged_closure` `:1278-1293`. Loaded engine-side by
`load_offline_sft_worker_closure` at `synaptic-tuner/tuner/runtime/offline_sft_worker.py:396`.

**Desktop.** Genuine value, and it is the layer whose desktop and cloud cases are closest. The user's own
machine is exactly where an engine file could have been edited by hand between clone and run; the manifest
is what makes "the engine at commit X" mean the bytes and not the label.

**Cloud.** The same property, plus the tenancy one: the code the tenant's container runs is the code the
operator published.

**Cost.** ~166 Host lines + 675 engine lines + 409 regenerator lines. It participated in four blockers, and
its real cost is *procedural*: any edit to any of the 66 members forces the full B-5 shape — regenerate,
push, move the pin. The ledger records that shape running three times (B-5, B-9-R1 #147, B-14 #226) plus a
fourth for B-16, and calls it out at diag:5181-5182. That is the recurring tax the review should price.

**One asymmetry worth the architect's attention.** B-14 deleted the engine's exec-bit equality because
DrvFs cannot report the mode. **The Host-side equivalent still checks it**: `docker_staging.py:1289-1291`
calls `_verify_file_mode(info, executable=member.git_mode == "100755")`. The two sides no longer agree.

### 1.8 Container user and cache keys

**What it is.** A profile-declared numeric `uid:gid` emitted as `--user`, plus seven environment keys that
steer every cache the trainer writes.

**Where.** Profile field `synaptic_host/docker_prepared_composition.py:65`; grammar
`synaptic_host/docker_v1/control_private.py:46` (`(?:0|[1-9][0-9]{0,6}):(?:0|[1-9][0-9]{0,6})`); argv
`:404-410`. Cache keys `docker_training.py:481-488`.

Five of the seven caches go to `/tmp` (`HOME`, `XDG_CACHE_HOME`, `TORCH_HOME`, `TRITON_CACHE_DIR`, plus
`USER` as the identity that makes them resolvable). **`HF_HOME` and `TRANSFORMERS_CACHE` do not**, because
the source lock pins them to the cache root. That split is B-10-R1, and it is the direct cause of B-10-R2.

**Desktop.** Essential and irreducible. This is the layer that makes a container write files a Windows user
can afterwards read. It is not hardening; it is function.

**Cloud.** Equally essential, for the same reason, against whatever the cloud provider's mount semantics
are.

**Cost.** ~45 lines, but the highest blocker density per line in the inventory: **B-9**, **B-9-R1** and
**B-16** all live here, three of the twenty-one. The chain is worth stating because it is the clearest
example of hardening generating its own follow-on work:

> the DrvFs mount presents uid 1000 → so the container must run as `--user 1000:1000` (B-9) → so `HOME` is
> `/` and unwritable, because 1000 is not in the image's password database (B-9-R1) → so the caches are
> redirected → and `getpass.getuser()` still falls through to `pwd.getpwuid(1000)` and raises inside
> `torch._inductor` (B-16).

Three blockers, two engine allowlist edits, two closure regenerations, two pin moves, all downstream of one
mount property. The ledger states the attribution: "This is a consequence of the B-9 fix, not a defect in
it. B-9 is correct and stays" (diag:5043-5044).

### 1.9 Network-disabled, credential-free container

**What it is.** `--network none` plus four independent mechanisms that prove no credential reaches the
container or the docker client.

**Where.** `--network none` emitted at `control_private.py:406`, refused otherwise at
`synaptic_host/docker_provider.py:172-173`. The four credential mechanisms: empty secret-requirements
digest signed into the lock `docker_training.py:506-509`; secret-key transport refusal
`docker_v1/binding.py:765-768`; forbidden dispatch environment `docker_staging.py:51-53`
(`PYTHONPATH`, `PYTHONHOME`, `PYTHONUSERBASE`, `HF_TOKEN`) enforced as an empty intersection at
`:1653-1656`; CLI-environment key denylist `model.py:1156-1161`.

**Desktop.** Strong and cheap. Offline execution is a correctness property as much as a security one: it is
what makes a run reproducible rather than dependent on what a registry served that day.

**Cloud.** The same, and here it is also the tenancy boundary.

**Cost.** ~60 lines. **Zero blockers.** This is the only layer in the inventory that has cost nothing and
caught its class of problem by construction. The architect should note the contrast with layers 5 and 6,
which cost 693 lines and four blockers between them.

### 1.10 Result envelope and cause line

**What it is.** An 18-code result enum with a 13-field envelope, and a one-line stderr renderer that names
where a failure happened without ever naming what it said.

**Where.** `synaptic_host/cause_line.py` (135 lines); `report_cause_line_v1` `:116`, two-frame renderer
`:58`. Codes `synaptic_host/cli.py:40-57`; envelope `to_dict` `:307-322`; shared `_failure` helper `:331`;
code/field agreement invariant `:289-305`.

**Desktop.** High value, and the record proves it: run 5 failed with `START_UNAVAILABLE` and no message at
all, and "recovering the cause cost a cycle and a purpose-built probe" (`docker_training.py:562-589`). On a
user's machine there is no operator to read a server log, so the one line the user can paste is the entire
support channel.

**Cloud.** Equally high, and it is the layer that most directly serves the "api / agent friendly" goal in
#209: a structured envelope with a closed code set is what a calling service can branch on.

**Cost.** ~255 lines, `tests/synaptic_host/test_cause_line.py` 349 lines. Participated in **B-11** as a
co-ruling and **B-15**, where the renderer had to move out of `docker_training.py` precisely because that
module imports the engine and B-15 *is* a failure of that import.

**A cost the architect should weigh separately.** Section 22.14 chose to render the deepest *two* in-package
frames rather than one, because eight modules use a two-line `_fail` helper whose deepest frame is the same
for all 28 call sites behind `_platform_fail` (diag:4303-4306). That is a diagnostic complication caused by
a code idiom, not by a requirement.

### 1.11 Driver probes P1-P11

**What it is.** An operator-side pre-flight that refuses to issue a run until eleven preconditions hold.

**Where.** `.claude/skills/host-docker-run/scripts/run_prepared_training.py` (2,074 lines); probes
`:152-1107`; tests `tests/skills/host_docker_run/test_run_prepared_training_probes.py` (1,927 lines).

| Probe | Function | Checks |
|---|---|---|
| P1 | `:185` | exactly one `docker.exe` on PATH |
| P2 | `:217` | the desktop-linux context points at the expected npipe endpoint |
| P3 | `:317` | project root is a drive path, not a UNC |
| P4 | `:333` | the committed profile reads, runtime section complete |
| P5 | `:452` | profile carries `docker_host.drive_mount_root` (B-1) |
| P6 | `:492` | working-tree config matches the committed blob |
| P7 | `:705` | checkout is on a branch tracking origin at HEAD (B-6) |
| P8 | `:961` | stage parent writable by the profile's container user (B-9) |
| P9 | `:563` | reports what will be staged; never gates (B-12) |
| P10 | `:233` | daemon answers the same probe the composition uses (B-13) |
| P11 | `:359` | `synaptic_host` resolves under the project root, not a worktree (#215) |

**Desktop.** This layer is where the desktop/cloud asymmetry is starkest. Every probe exists because a
human operator can get the environment wrong. A desktop *app* has no operator shell, no PATH ambiguity, no
worktree confusion and no branch state — the app controls all of it. **Most of P1-P11 is scaffolding for the
current manual procedure, not for either product shape.**

**Cloud.** Less again. P1, P2, P3, P6, P7 and P11 have no cloud analogue at all.

**Cost.** ~955 lines of driver plus 1,927 lines of test — **2,882 lines, larger than any production layer in
this inventory**. It caused no blockers. It *detected* B-6, and it is the reason B-12, B-13 and B-15 were
diagnosed as fast as they were. Its value has been diagnostic, and it is honest to say that value was real:
five of the eleven probes were added in direct response to a blocker that had already cost a cycle.

### 1.12 Docker CLI verb enum and runner

**What it is.** A seven-member enum, of which **five are wired and two are dead**, and a bounded subprocess
runner that parses the CLI's text output back into typed records.

**Where.** `synaptic_host/docker_v1/model.py:1011-1018`: `VERSION`, `CREATE`, `START`, `STOP`, `INSPECT`,
`PS`, `LOGS`. **`STOP` and `LOGS` have zero call sites in `synaptic_host/`.** Runner `cli.py:680-990`;
spawn `:691-695`; argv shape `:806-807`.

There is no `RUN`, no `EXEC`, no `PULL`, no `EVENTS`, no `WAIT`, no `RM` and no `CONTEXT`. The container is
created and started separately, never with `docker run`.

**Desktop and cloud.** This layer buys nothing on its own; it is the transport. Its properties (bounded
output, no shell, explicit env, digest-pinned image) are real but are properties of *how* it shells out, not
of shelling out.

**Cost.** ~427 lines plus roughly 4,200 lines of test across seven files. It caused **B-4** and **B-13**.
Section 3 prices what replacing it would change.

---

## 2. BLOCKER COSTING

### 2.1 Categories, and a stated convention

The task asks for totals per category, which implies exclusive buckets, but the record does not support
exclusive buckets: the ledgers have no applied categorisation scheme at all. What they have is (a) a
consistent *severity* vocabulary — Blocking / Minor / Future / Note / Blocker candidate / ruled — (b) an
ad-hoc *provenance* vocabulary used in prose at the point of argument (platform-independent, engine-side,
Host-only, pre-existing, latent, masked, source defect, environment precondition, operator step, fixture
defect), and (c) exactly one named cross-blocker family, "the scrubbed-environment family (B-7, B-9-R1,
B-13)" at diag:4420.

So the categories below are **mine, not the record's**. I assign each blocker one **primary** category so
the totals sum to the blocker count, and record a **co-attribution** where the ledger supports a second.
Totals are reported both ways so the architect can see how much any conclusion depends on the convention
rather than on the evidence.

- **P — product logic.** Would have bitten on any platform.
- **W — Windows-plus-hardening interaction.** Needs both the platform and a layer we chose.
- **E — engine defect.** The fix was in the submodule.
- **H — harness or operator defect.** The fix was in a script, a procedure or a fixture.

### 2.2 The table

| Blocker | Task | Primary | Co-attr | Found on | Closed on | Layer (primary) | Fix size |
|---|---|---|---|---|---|---|---|
| B-1 | #84 | W | — | pre-run-1, by reading | run 2 | composition policy | 5 files; lines not stated |
| B-1' | #96 | W | — | run 1 | run 2 | composition policy | not stated |
| B-2 | #85 | E | P | pre-run-1, by reading | never exercised | engine internals | not stated |
| B-3 | #95 | H | — | run 1 | run 2 | operator script | not stated |
| B-4 | #97 | P | — | run 1 | run 2 | CLI verb/create argv | **2 production files** |
| B-5 | #116 | P | — | after run 2 | procedural | worker closure manifest | procedure, not a diff |
| B-6 | #118 | H | — | run 2 | run 3 | operator procedure | not stated |
| B-7 | #120 **open** | W | — | run 3 | fixed #121, **never exercised** | scrubbed git child env | not stated |
| B-8 | — | *unclassifiable* | — | — | — | — | no task, no subject, 2 mentions |
| B-9 | #128 **open** | W | — | run 4 | shipped run 5, observed run 8 | container user | **8 Host + 2 driver files** |
| B-9-R1 | #141/#147 | E | W | probe #131 | shipped run 5 | engine allowlist + cache keys | 2 engine files + regen + pin |
| B-9-R2 | diag 18.20 | P | — | by reading, run 4-5 | superseded by B-10 | staging re-verification | none |
| B-10 | #137 **open** | P | — | by reading, pre-run-5 | **still latent** | staging re-verification | **2 Host production files** |
| B-10-R1 | #153 **open** | P | E | coder-user #149 | **open** | source lock | none landed |
| B-10-R2 | #280 **open** | P | — | run 11 | **open** | staging re-verification | none |
| B-11 | #160 | W | H | run 5 | run 6 | `.synaptic` ACL chain | security.py + docker_training.py |
| B-11-R1 | #175 **open** | W | H | step 0 on #174 | shipped run 7 | `.synaptic` ACL chain | one spec item, two passes |
| B-12 | #179 | P | — | run 6 | run 7 | staging bound | 8 items, 1 file + driver + skill |
| B-13 | #196 | W | — | run 7 | run 8 | sealed CLI env | **2 files, 3 changes in one function** |
| B-14 | #217 | E | W | run 8 | run 10 | engine internals | **4 lines**, 1 module + regen |
| B-15 | #243 | P | H | run 9 | run 10 | entry point / import root | 1 insertion + **~30-line new file** |
| B-16 | #256 | W | E | run 10 | run 11 | container user + env dict | **1 Host key** + 2 engine files + regen |

Twenty-one classifiable rows. B-8 is listed for completeness and excluded from every total: it appears
twice in the diagnostic (`:1654`, `:2775`) with no task, no section and no subject line anywhere.

### 2.3 Totals

**By primary category only (sums to 21):**

| Category | Count | Blockers |
|---|---|---|
| P — product logic | **8** | B-4, B-5, B-9-R2, B-10, B-10-R1, B-10-R2, B-12, B-15 |
| W — Windows-plus-hardening | **8** | B-1, B-1', B-7, B-9, B-11, B-11-R1, B-13, B-16 |
| E — engine defect | **3** | B-2, B-9-R1, B-14 |
| H — harness / operator | **2** | B-3, B-6 |

**Counting co-attribution as well (28 attributions over 21 rows):**

| Category | Primary | Co | Total |
|---|---|---|---|
| P | 8 | 1 | 9 |
| W | 8 | 2 | 10 |
| E | 3 | 1 | 4 |
| H | 2 | 3 | 5 |

The convention moves the P/W ordering but not the shape: **product logic and Windows-plus-hardening are
each roughly 40% of the record, and neither dominates.** Any argument that the pain was "mostly Windows" or
"mostly our own hardening" is not supported by the evidence either way.

### 2.4 The counterfactual column, which is the decision-relevant one

For each blocker: **is there a single hardening layer whose removal would have made this blocker
impossible?**

| Layer removed | Blockers made impossible | Count |
|---|---|---|
| staging re-verification on every cut (`_verify_artifact_topology`) | B-9-R2, B-10, B-10-R2 | **3** |
| `.synaptic` ACL chain validation | B-11, B-11-R1 | **2** |
| worker closure manifest | B-5 | 1 |
| scrubbed child environment (git remote reader) | B-7 | 1 |
| engine trainer allowlist | B-9-R1 | 1 |
| source lock `required_environment` exactness | B-10-R1 | 1 |
| sealed four-key CLI environment | B-13 | 1 |
| engine exec-bit equality | B-14 | 1 |
| container user (`--user`) | B-16 | 1 |
| **Subtotal — attributable to a removable layer** | | **12** |
| **Not removable by dropping a layer** | B-1, B-1', B-2, B-3, B-4, B-6, B-9, B-12, B-15 | **9** |

**Twelve of twenty-one blockers were made possible by a hardening layer that could be removed. Nine would
have happened anyway.** Two layers account for five of the twelve.

Three caveats the architect must carry with that number:

1. **Removing `--user` re-opens B-9.** B-16 is impossible without `--user`, but so is writing to the bind.
   My B-16 spike measured that `--user 1001:102`, the image's own identity, also works. So the honest
   statement is not "remove the layer" but "a different value in the same layer would have avoided B-16".
2. **Removing the staging bound would not have fixed B-12's substance.** The defect was staging 393.7 MiB
   to deliver one file (diag:3518); the bound only made it visible. Removing the bound hides the defect.
3. **Four of the six open blockers have shipped fixes.** #120, #128, #137, #175 are open because the
   acceptance observation was never made, not because code is unwritten. Only #153 and #280 are unfixed.

### 2.5 Found by reading versus found by running

| How found | Count | Blockers |
|---|---|---|
| By reading the source | 6 | B-1, B-2, B-5, B-9-R2, B-10, B-10-R1 |
| By running (runs 1-11) | 14 | the rest |
| By a purpose-built probe, not a run | 1 | B-9-R1 (probe #131) |

Runs 1 through 7 produced no container at all. The first container was created on **run 8** (#218), the
first training on **run 11** (#279). Eleven runs to one training step.

### 2.6 META-BLOCK cycles

A negative finding first, because it bounds what can be said. **The two ledgers contain the string
`META-BLOCK` exactly twice**, both referring to #154 (diag:2147, review:203). The diagnostic contains no
numbered imPACT cycle list. The numbering exists only in task titles.

| Cycle | Task | Subject | Trigger |
|---|---|---|---|
| 1-5 | *unnumbered* | — | No task carries a cycle 1-5 label. #123 names "imPACT cycle 2-3" as B-5 + B-6/P7 + B-7 together, without saying which is which. #138 is an unnumbered ALERT naming B-7, B-9, B-10 and the B-9-R1 rePACT at once, which is why 1-5 cannot be split cleanly. |
| 6 | #154 | B-10-R1, HF cache roots pinned by the lock | coder-user #149 measured 3 regressions attempting the `/tmp` move, 0 without |
| 7 | #161 | B-11, Host refuses its own private storage root | run 5 cut 1, `START_UNAVAILABLE` with no message |
| 8 | #176 | B-11-R1, chain repair wedges on the temp volume | test-host step 0 on #174, three of three trials |
| 9 | #180 | B-12, superproject archive exceeds the bound | run 6 staging raise at `docker_staging.py:1299` |
| 10 | #197 | B-13, CLI environment omits `USERPROFILE` | run 7 |
| 11 | #218 | B-14, engine member-mode predicate on DrvFs | run 8, container `8dda2cee75a7` exit 31 after 0.7 s |
| 12 | **does not exist** | — | B-15 (#243) and B-16 (#256) were filed as plain BLOCKER tasks with no ALERT. The next ruling of that shape is ruling C on #280, which opened **this review** (#282) instead of a twelfth cycle. |

**#209 says "thirteen blockers, ten imPACT cycles, no container before run 8". At HEAD that reads
twenty-one blockers, eleven numbered cycles, and the first training on run 11.** The brief was written
after run 8 and has not been updated; the architect should not carry its counts.

---

## 3. THE DOCKER ENGINE API ALTERNATIVE

**Status of this section: research only. Nothing here has been executed.** No pipe was opened, no HTTP
request was issued, no container was created by any route other than the existing one. Claims about the
transport are read from source and specification, and are marked accordingly. My B-16 spike settled every
claim by executing against an image already on the host; that method does not transfer here, and I have not
substituted confidence for measurement.

### 3.1 What the current path actually needs `docker.exe` for

Five live verbs. Two more are declared and dead.

| Verb | Argv the Host builds | What it does with the output | Engine API equivalent |
|---|---|---|---|
| `version` | `--format {{.Server.Version}}` (`docker_prepared_composition.py:174`) | **Nothing.** Only `liveness.outcome` is read (`:177-178`); the version string is discarded | `GET /version` (swagger:10734) |
| `create` | 20+ tokens (`control_private.py:404-428`) | `_parse_create_ref` (`cli.py:221-227`): strip one `\n`, require exactly 64 hex bytes | `POST /containers/create` (swagger:8412) |
| `start` | `start <64-hex>` (`start.py:322-324`) | **Nothing.** `capture_stdout=False` (`cli.py:863`) | `POST /containers/{id}/start` (swagger:8945) |
| `inspect` (container) | `--type container <ref>` (`cli.py:941-943`) | `_project_container` (`cli.py:388-514`) re-types ~20 fields by hand | `GET /containers/{id}/json` (swagger:8615) |
| `inspect` (image) | `--type image <digest>` (`cli.py:909-911`) | Reads `Id` only (`:919-922`) | `GET /images/{name}/json` (swagger:10187) |
| `ps` | `--all --quiet --no-trunc --filter name=^/<n>$` (`cli.py:878-883`) | `_parse_inventory` (`cli.py:290-311`): split lines, each 64-hex, dedupe, sort, cap 64 | `GET /containers/json` (swagger:8338) |
| `STOP` | — | **zero call sites** | — |
| `LOGS` | — | **zero call sites**; the public surface refuses logs at `docker_publication.py:275-276` | — |

Endpoint paths verified against the official Moby specification
(`https://raw.githubusercontent.com/moby/moby/master/api/swagger.yaml`, 473,773 bytes, `version: "1.56"` at
`:25`). All six needed endpoints exist. `GET /containers/{id}/wait` (`:9477`) and `GET /events` (`:10906`)
also exist and would replace the *driver's* capture instrument, which today shells to `docker events` and
`docker wait` outside the Host.

Every argv is prefixed identically at `cli.py:806-807`:
`(executable, "--host", endpoint, verb, *arguments)`.

### 3.2 What text parsing would disappear

Six sites parse CLI text that the HTTP API returns as structured JSON.

| Site | `file:line` | What goes away |
|---|---|---|
| `_parse_create_ref` | `cli.py:221-227` | 64-hex-with-trailing-newline handling; the API returns `{"Id": "..."}` |
| `_parse_inventory` | `cli.py:290-311` | newline splitting, dedupe, sort, 64-line cap; the API returns a JSON array |
| `_parse_inspect` | `cli.py:276-287` | **including the one-element-array unwrap at `:285-287`, which is a pure CLI artifact** — `GET /containers/{id}/json` returns the object directly |
| `_project_container` | `cli.py:388-514` | stays in substance, but stops re-typing text; notably the `State.StartedAt` string surgery at `:486-497` (truncate/pad the fraction to 6 digits, `Z` → `+00:00`) |
| `version` digesting | `cli.py:811-819` | a Go-template dependency on `{{.Server.Version}}` |
| child-process framing | `cli.py:680-798` | two drain threads `:709-716`, per-stream and combined byte caps `:718-749`, `process.wait` `:758`, two-pass close/join `:769-775`, terminate→kill cleanup `:610-678` |

The last row is the largest single saving and the least obvious: roughly 120 lines exist purely because
output arrives as two raw pipes from a child process.

### 3.3 What it would cost

**Two routes, and they price very differently.**

**Route A — the Docker SDK for Python.** Read from `docker/docker-py` `pyproject.toml` at `main`:

```
dependencies = [
    "requests >= 2.26.0",
    "urllib3 >= 1.26.0",
    "pywin32>=304; sys_platform == \"win32\"",
]
```

**`synaptic_host` currently imports zero third-party packages.** I enumerated every top-level import across
all 57 files: stdlib plus `tuner` and `synaptic_tuner` only. Route A takes that from zero to three (four
counting `pywin32`'s transitive install footprint) in a package whose entire design is exact types and
closed sets.

Route A also inherits a known sharp edge, documented in docker-py's own source
(`docker/transport/npipeconn.py`): *"When re-using connections, urllib3 tries to call select() on our
NpipeSocket instance, causing a crash. To circumvent this, we override `_get_conn`, where that check
happens."*

**Route B — stdlib `http.client` over a ctypes pipe handle.** This is where I was wrong in my teachback and
must correct the record. I predicted that reaching the pipe from the standard library alone would need
`pywin32` or a new ctypes shim. **The shim already exists in this codebase, in production, with tests.**

| Primitive | Already bound? | Where |
|---|---|---|
| `CreateFileW` | **yes** | `synaptic_host/security.py:171-176`; also `docker_staging.py:334-338` |
| `ReadFile` | **yes** | `synaptic_host/security.py:195-199` |
| `WriteFile` | **yes** | `synaptic_host/security.py:200-204` |
| `CloseHandle` | **yes** | `docker_staging.py:339-340` |
| `FlushFileBuffers` | **yes** | `security.py:205-206` |
| `CreateEvent` / `WaitForSingleObject` / `CancelIo` / `GetOverlappedResult` | **no** | nowhere in the tree |
| `WaitNamedPipe` / `SetNamedPipeHandleState` / `GetNamedPipeInfo` | **no** | nowhere in the tree |

`http.client.HTTPConnection` accepts a duck-typed socket: assign `conn.sock` an object providing `sendall`
and `makefile("rb")`. That is exactly the seam docker-py exploits with its own `NpipeSocket`.

So the new surface for Route B is **not** the pipe handle, which is already solved here. It is:

1. **Timeouts.** docker-py opens the pipe with `FILE_FLAG_OVERLAPPED` and implements every read and write
   as `OVERLAPPED` + `CreateEvent` + `WaitForSingleObject` + `CancelIo` + `GetOverlappedResult`
   (`npipesocket.py:52-64`, `:134-169`). Without overlapped I/O a hung daemon hangs the Host. Today the
   30,000 ms bound is enforced by killing a child process (`cli.py:723`, `:758`), which is a much blunter
   and much simpler mechanism. **This is the single most important cost in this section.**
2. **`ERROR_PIPE_BUSY` (0xe7).** All pipe instances busy is a normal condition. docker-py retries up to 10
   times with a 1 s sleep (`npipesocket.py:65-76`).
3. **Byte-mode.** docker-py does *not* call `SetNamedPipeHandleState`; it reads `GetNamedPipeInfo` flags
   and relies on the pipe's default. Whether that default is safe to assume is **unverified by execution**
   here.
4. **API version pinning.** From the Moby spec `:49-60`: prefixing `/v1.56/` locks the version; an
   unsupported version returns HTTP 400; **"Using the API without a version-prefix is deprecated and will
   be removed in a future release."** A pinned version becomes a new committed constant, in the same family
   as the endpoint constant B-13 introduced. The spec also warns the schema is open, so a client must
   ignore unknown response properties — which is the opposite of this codebase's exact-key discipline and
   is a real design tension, not a detail.

**How a desktop app would ship it.** Route A means bundling three packages plus `pywin32`'s DLLs into the
desktop installer. Route B means shipping the same pure-Python package the Host already is. For a product
that must run on a user's machine without a Python toolchain, that difference is material.

### 3.4 Which blockers become impossible, and which do not

This is where the premise in #209 and in the brief for this task needs correcting.

| Blocker | Eliminated by the Engine API? | Why |
|---|---|---|
| **B-13** | **Yes, outright** | The blocker is `docker context inspect` needing a home directory. An HTTP client reads no config file, resolves no context, and has no home. The endpoint is already a constant at `docker_prepared_composition.py:150`. |
| **the four-key sealing itself** | **Yes** | The layer exists only because there is a `docker.exe` child to seal an environment for. No child, no child environment: ~138 lines and 12 tests go with it, and with them the whole "scrubbed environment" failure class *for docker*. |
| **B-4** | **Weakened, not eliminated** | `POST /containers/create` takes `Entrypoint` as an explicit JSON field rather than a flag you can omit. The decision to override the image's entrypoint is still one someone has to make. |
| **B-7** | **NO. The premise is wrong.** | B-7 is not a docker child. `ScopedGitRemoteReader._run` (`security.py:1130`) scrubs the environment for **`git ls-remote`** (`:1169`) via `subprocess.run` (`:1149`); the `SystemRoot` carry is at `:1142-1147`. Admission reads a git remote whatever the docker transport is. B-7 is untouched. |
| **B-9** | **NO, and this must be said precisely** | The DrvFs bind is the same object under either transport. `POST /containers/create` carries `HostConfig.Binds` and `User` with the same semantics as `--mount` and `--user`. The mount still presents uid 1000; the container still must adopt it. **No part of B-9 changes.** |
| **B-16** | **No** | Downstream of `--user`, which is unchanged. |
| **B-14** | **No** | Engine-side, and about DrvFs file modes. |
| **B-1 / B-1'** | **No** | The bind-source mapping into the WSL distro is a property of Docker Desktop, not of the client. |

**Net: one blocker of twenty-one eliminated outright, plus the removal of one ~138-line layer and one
failure class.** The brief's estimate of "B-7, B-13, part of B-9" overstates it by roughly a factor of
three. B-13 alone is the honest answer, and the layer deletion is the honest bonus.

### 3.5 What the engine would have to know: nothing

Searched the submodule directly.

- The three files on the container-side execution path — `tuner/runtime/offline_sft_worker.py`,
  `tuner/training/methods/sft.py`, `tuner/runtime/verification.py` — contain **zero** matches for
  `docker`, `container`, `/proc/1/cgroup` or `dockerenv`. The engine never detects that it is in a
  container.
- Its only knowledge is environment variables and absolute paths: `verification.py:624-647` demands an
  exact `required_env` map and `:660-680` an exact argv. Those roots are `/source/*` and `/artifacts/*`
  because the **Host** chose them at `docker_training.py:446-451`.
- The engine does contain a typed provider port package the Host imports from,
  `tuner/execution/providers/docker_provider_v1/`, whose `ports.py:1` docstring reads: *"Injected Docker v1
  boundaries. No shell, daemon client, or SDK is imported here."*

**So the transport change is Host-only.** No engine edit, no closure regeneration, no pin move — which
makes it, procedurally, one of the cheapest structural changes available in this codebase. That is a
notable contrast with every environment-key change, each of which costs the full B-5 shape.

### 3.6 What publication reads from `cache/` after training

The decisive question for ruling B-10-R2 against B-10-R1. The answer is short.

**Publication reads nothing from `cache/`. Exactly one site in the entire Host reads it after the container
exits, and that site is the verifier that is failing.**

| Module | Roots it reads | `file:line` |
|---|---|---|
| `docker_publication.py` | `<artifact_root>/artifacts` and the staged `source_root` | `:264`, `:345-351` |
| `publication_composition.py` | engine / project / state roots, storage registry, spool | `:169`, `:175-176`, `:450-452` |
| `publication_store.py` | `project_root/.synaptic`, `state_root/training.sqlite3` | `:114-118` |
| `artifact_spool.py` | the borrowed spool root | `:643-645` |
| `artifact_destinations.py` | none; parses config bytes | `:402` |
| `local_artifact_destination.py` | `data_ref` / `control_ref` from the destination config | `:603-613` |
| `verified_artifact_source.py` | **no filesystem access at all**; reaches artifacts through the public Runs API | `:228`; docstring `:1` |
| `docker_execution.py` (verification) | `state/runtime-v1-inventory.json`, then `artifacts/` | `:854-855`, `:908-910`, `:930-944` |
| **`docker_staging.py`** | **`root / "cache"`** | **`:1545`** |

The one site, verbatim, `docker_staging.py:1543-1554`:

```
1543	    if tuple(sorted(names)) != _ARTIFACT_DIRECTORY_NAMES:
1544	        raise ValueError("artifact preparation topology is incomplete or extended")
1545	    _verify_inventory_at(entries, root / "cache")
1546	    if expect_unused_artifacts:
1547	        for name in _EMPTY_ARTIFACT_DIRECTORY_NAMES:
```

`_verify_inventory_at` (`:1459-1496`) walks the whole subtree and demands **set equality on both files and
directories**: extra files fail at `:1474-1475`, extra directories at `:1476-1479`. `cache/huggingface/`
therefore fails, and `expect_unused_artifacts` — computed once at `docker_training.py:887-890` — gates only
the emptiness loop below it, never line 1545.

Three facts the architect can rule from:

1. The **model inventory** under `cache/model` (~25 files) is consumed only by the **engine, inside the
   container**: `verification.py:675` passes `--model-cache-dir {cache}/model`, and `:639-643` sets
   `SYNAPTIC_MODEL_SNAPSHOT`. After the container exits, nothing on the Host needs it.
2. The **HuggingFace tree** under `cache/huggingface` and `cache/transformers` exists only because the
   source lock pins `HF_HOME` and `TRANSFORMERS_CACHE` there
   (`execution_source.py:497-498`), which is B-10-R1.
3. `_ARTIFACT_DIRECTORY_NAMES` (`:49`) includes `cache`, and `_EMPTY_ARTIFACT_DIRECTORY_NAMES` (`:50`)
   deliberately excludes it — because the inventory lives there. The design assumed `cache/` held exactly
   the inventory and nothing else. The lock's HF pin broke that assumption, and line 1545 is where the
   break surfaces.

The comment at `:1513-1520` classifies everything before `:1546` as identity that "runs unconditionally on
every cut", and only the emptiness loop as being "about USE". **Line 1545 is inside the unconditional
block, and it is a USE check wearing an identity check's clothes.** That is the finding.

---

## 4. Consultation

### 4.1 Scope in my domain

Mine: the factual record above. The layer inventory with citations, the blocker costing with a stated and
declared convention, the transport research, and the `cache/` read map.

Not mine, and deliberately absent: the keep / simplify / replace verdict per layer, any judgement about
whether a layer is worth its cost, and any sequencing recommendation. Those are #286's.

I have also not proposed a fix for B-10-R2 or B-10-R1. Section 3.6 gives the architect what it needs to
rule; the ruling is not a preparer's.

### 4.2 Dependencies and interfaces

- **Host → engine.** One-directional and narrow. The engine defines `ExecutionSourceV1` and the trainer
  allowlist; the Host constructs values that satisfy them. Every environment-key change is therefore an
  engine change plus a closure regeneration plus a pin move. That has now happened four times.
- **Host → Docker.** Five live CLI verbs through one bounded runner. Replaceable without touching the
  engine (section 3.5).
- **Host → operator.** Eleven driver probes and a checked-in materialization script. This interface exists
  only for the current manual procedure and has no analogue in either product shape.
- **Engine → container.** Environment variables and absolute paths only. No container awareness.
- **Blocking for #286:** nothing. This document is the input; the architect can rule from it.

### 4.3 Key decisions and trade-offs the evidence surfaces

I am naming the trade-offs, not resolving them.

1. **Enumeration versus allowlist.** Three blockers (B-7, B-9-R1, B-16) are the same shape: a variable
   nobody enumerated. The design answers "which environment keys are allowed" with a closed list in two
   engine files that are themselves closure members. The cost of being wrong is an engine release. The
   ledger already noticed twice; this document makes it three.
2. **Where the cost concentrates.** Two layers — the `.synaptic` ACL chain and the staging re-verification —
   account for five of the twenty-one blockers and roughly 665 lines. Layer 9, the network-disabled
   credential-free container, cost 60 lines and zero blockers. Cost is not evenly distributed and the
   review should not treat "hardening" as one thing.
3. **The test tree equals the source tree.** 40,028 test lines against 40,109 source lines, with 12,854
   lines covering the twelve layers here. Any layer removed frees roughly its own size again in tests.
4. **The driver is the largest single artifact in the inventory** at 2,882 lines including tests, caused no
   blockers, detected several, and serves neither product shape.
5. **The two consumer columns rarely diverge except in three places** — layers 5, 6 and 11. The rest of the
   inventory buys roughly the same thing for a desktop app and a web app, which is a stronger argument for
   the design than a blocker count alone suggests.

### 4.4 Risks and concerns

- **Section 3 is unverified by execution.** No pipe was opened. The overlapped-I/O cost, the byte-mode
  assumption and the `ERROR_PIPE_BUSY` behaviour are read from docker-py's source and the Moby spec, not
  measured here. A ruling that turns on transport feasibility should be gated on a spike, not on this
  document.
- **Citation drift is a measured hazard in this record.** diag:4353-4356 documents that every citation in
  one subsection drifted without any of them being edited, and diag:5361-5363 records that three of six
  corrections landing with section 25 were pure line drift. I have cited symbols alongside lines where a
  symbol exists. Line numbers here are true at `557ce1be` and only there.
- **One published count is known wrong and unfixed.** diag:5108 says the lock binds eleven keys; it binds
  thirteen. Task #277 is open on it.
- **Four of the six open blockers have shipped fixes** and are open for want of an observation. A review
  that counts open blockers as unfinished work will overstate the remaining debt by four.
- **My category assignment is mine.** The record supports none of the four buckets as a scheme. I have
  reported totals both ways for that reason, and section 2.3 shows the shape does not depend on the
  convention. It would be an error to quote a single total as though the ledgers had produced it.
- **B-8 cannot be classified.** Two mentions, no task, no subject. If it matters to a count, it needs to be
  found, not assumed.

### 4.5 Recommended approach for the review itself

Not a recommendation about the layers. A recommendation about how to rule on them.

1. **Rule per layer against section 2.4, not section 2.3.** The category totals describe history. The
   counterfactual column describes what removing something would actually have bought.
2. **Treat the two consumer columns as the test.** A layer that buys the same property in both columns is
   settled. The three that diverge — the ACL chain, the CLI sealing, the driver probes — are where the
   review has something to decide.
3. **Rule B-10-R2 before B-10-R1.** Section 3.6 shows nothing downstream reads `cache/`, so the question
   at line 1545 is answerable Host-only, with no engine edit, no closure regeneration and no pin move.
   B-10-R1 is the full B-5 shape. They are not the same size of decision.
4. **Gate any transport ruling on a spike, not on section 3.** One measured probe against the pipe would
   settle the overlapped-I/O question, which is the only real cost in Route B.
5. **Rule on the driver separately from the Host.** It is the largest artifact and the one least connected
   to either product shape; bundling it with the hardening layers will produce a worse answer for both.

---

## 5. What is still missing, and what the user must be asked

### 5.1 Research not done

| Gap | Why it matters | How to close it |
|---|---|---|
| No pipe was ever opened | The entire Route B cost estimate turns on overlapped I/O | One spike: open `\\.\pipe\dockerDesktopLinuxEngine` with the existing `CreateFileW` binding, issue `GET /v1.56/version`, read the response |
| Byte-mode assumption unverified | docker-py never sets it; whether the default is safe here is unknown | `GetNamedPipeInfo` on a live handle |
| POSIX/macOS transport unexamined | There is no `unix://` string in `synaptic_host/`; the endpoint layer is Windows-only by construction | Read what the Modal and HF Jobs providers assume before designing a portable endpoint |
| Modal and HF Jobs providers not inventoried | `modal_provider.py` (1,077), `modal_resolver.py` (775), `modal_training.py` (660) are 2,512 lines that reuse these same layers, and #209 places this review *before* that work | A second inventory pass, or an explicit decision to rule on the local path alone |
| B-8 unidentified | It is a gap in the blocker series | Search the task history outside #84-#280 |
| Per-blocker line counts | The ledgers record files touched but almost never lines; only B-14 (4 lines) and B-15 (~30) are numeric | `git log --stat` over the fix commits, which I did not run because the release clones are out of bounds for me |

### 5.2 Questions for the user

These are decisions, not research gaps. None can be resolved by reading more code.

1. **Which of the two consumer shapes is the Host itself for?** The whole inventory reprices depending on
   whether the Host runs on the user's machine, on the server, or on both. Layers 5 and 6 in particular are
   worth very different amounts under each answer.
2. **In the cloud shape, does the Host run on a shared machine?** The HMAC and ACL chain defends a local
   key file against a local principal. If the cloud shape is per-tenant isolation at the container or VM
   level, that threat is already handled elsewhere and the layer is paying twice.
3. **Is a third-party dependency acceptable in `synaptic_host`?** It has zero today, and that is a design
   choice with real value for a desktop installer. Route A costs three packages plus `pywin32`. Route B
   costs new ctypes surface instead. The user should choose which currency to spend before the architect
   prices the options.
4. **Does the manual driver survive the product?** 2,882 lines exist to make a human operator's environment
   safe. If both product shapes are apps, the review should say whether the driver is a temporary
   scaffold to be retired or a permanent diagnostic tool to be maintained.
5. **Is macOS or Linux local execution in scope?** The endpoint layer is Windows-only by construction. If
   the desktop app ships on more than Windows, that is a design requirement, not a portability nicety, and
   it changes the transport question materially.

---

*Prepared by preparer-b16 for task #285. Read-only against `557ce1be`; no source file was modified. Section
3 is research, not measurement.*
