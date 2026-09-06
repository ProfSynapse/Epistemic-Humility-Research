# Modal smoke execution runbook — released checkout `34d6623d`

Prepared by devops-modal on task #494 (TEST #424 of feature #420, team
session-832e1b8a). **Nothing in this document was executed against the
provider.** Every command below is prepared for the lead to run; the author ran
only the local probes listed in section 3, none of which reaches Modal, reads a
credential, or mutates the account.

Record query answered by the secretary on 2026-09-06. Both memory ids are
current and neither is superseded, so both are cited here:
`9dfad232b19056be0a93e932204d259b` (TEST push-boundary arc, tasks #475-#483:
documentation and audit discipline behind the 27-commit push at `34d6623d`,
nothing in it touching provisioning or rotation) and
`aebbc30467abafe72d670ce49b999853` (CODE arc record, which carries the
provisioning and rotation material). The reply was checked against every step.
**No step changed.** What it confirms, what it corrects, and the one item it
does not corroborate are in section 1.1.

---

## 1. Scope and boundary

Scope A: deploy, start, observe and verify **one** isolated Modal job, then
**stop before publication**. The lead executes every step. auditor-run verifies
afterwards.

Governing rulings, all in `docs/architecture/prepared-path-alpine-diagnostic.md`:

| Ruling | What it fixes here |
|---|---|
| 29.3 ruling (1) | Two keys, three refs. Rotation obligations: pre-smoke Host key rotation is **not optional**; worker-channel retirement is **closeout only**. |
| 29.7 ruling (5) | The app name is a module constant and does not vary. Isolation is by **dedicated provider environment**. |
| 29.9 ruling (7) | The isolation triple, the fixed Secret key set, and the standing safety properties. Egress is **unrestricted** at this pin. |
| 29.11 rulings (9) and (10) | The overlap trap and the artifact-kind divergence are **assertions to read**, not steps to perform. |
| 29.12 | Gate order. No submit before G1-G6 are green. The dry run is **not a gate**. |

Where 29.15 supersedes a body figure, 29.15 governs; its baseline is Host
`0371d495`, and the Host tree is byte-identical for every symbol cited below at
the release sha `34d6623d`.

### 1.1 Record confirmations (secretary reply, 2026-09-06)

Five items bear on this runbook. None of them changed a step.

1. **The isolation triple survives; only the application half of the earlier
   plan-mode framing is superseded.** The secretary first wrote that the
   environment ruling contradicts the whole triple, then corrected that in a
   second message. The corrected reading is the one this runbook already
   follows: the two Volumes and the Secret **are** the triple and they live in
   the dedicated environment; only the app name stays constant, because it is a
   module constant (29.7 ruling (5)). Step 4 creates all three. Step 8 addresses
   the app by name **plus** environment for exactly this reason, and the boxed
   warning there is the consequence.

2. **This runbook writes no configuration file, and the reason is not the one
   the record gives.** The instruction is right and is followed: a step that
   wrote a new configuration file to select the environment would not work. The
   *mechanism* relayed from blocker #457, that the filename is fixed in code
   with no path parameter, is **false, and was already false when it was
   written**. Measured in the released checkout:

   ```
   sed -n '345,350p' synaptic_host/modal_provider.py
     -> def load(cls, context: ProjectContext, path: Path | None = None) -> "ModalHostConfigV1":
     ->     selected = path or context.config_root / "providers" / "modal.json"
     ->     ...must live below the host config root

   sed -n '683,686p' synaptic_host/modal_provider.py
     -> def load(cls, context: ProjectContext, config_path: Path | None = None,
     -> ) -> "ModalProviderAuthorityV1":
     ->     config = ModalHostConfigV1.load(context, config_path)

   rtk proxy grep -rn "ModalProviderAuthorityV1.load|ModalHostConfigV1.load" \
       --include=*.py .
     -> synaptic_host/modal_provider.py:686   (the internal thread-through)
     -> synaptic_host/modal_training.py:596   (the only production entry)
     -> seven further call sites, all under tests/
   ```

   An override parameter **does** exist and is threaded end to end. Three facts
   make a new configuration file useless anyway, and a step that supplied one
   would be refused rather than silently ignored:

   - **The only production entry passes none.** `modal_training.py:596` is the
     sole non-test call site outside the loader's own thread-through, so there
     is no second production route that might pass an override.
   - **An override may not point anywhere.** The resolved path must sit below
     the host configuration root or the load raises
     `ValueError("Modal host config must live below the host config root")`
     (`modal_provider.py:348-350`). A step aiming at a file elsewhere on the
     operator machine is refused at load.
   - **The file must be committed.** The loader reads the committed git blob,
     not the worktree file (`_read_committed_configuration_v1`, C1 per 29.5(f)),
     so an uncommitted override would not be seen even inside the root.

   **This is an authoring error, not a moved citation, and the two need opposite
   repairs.** The override parameter was introduced on 2026-08-29 and the
   containment guard on 2026-08-26, both **before** the blocker carrying the
   contrary mechanism was filed:

   ```
   git.exe log -S 'config_path: Path | None = None' --format='%h %ad %s' \
       --date=short -- synaptic_host/modal_provider.py
     -> 52f9464f 2026-08-29 Add Modal provider policy authority

   git.exe log -S 'must live below the host config root' --format='%h %ad %s' \
       --date=short -- synaptic_host/modal_provider.py
     -> f74c3880 2026-08-26 feat(training): compose host-owned Modal pipeline
   ```

   A moved citation is repointed and its author is blameless. A mechanism that
   was false at its own authoring sha is corrected and reported to the author.
   The two are indistinguishable in a relayed message and are separated only by
   one history search, so run it whenever a cited mechanism fails to reproduce.
   Independently confirmed by the secretary against the same checkout; the
   record note carrying the false mechanism is corrected. #457's instruction
   half stands unchanged.

3. **Two standing user rulings do not transfer to this lane, and neither fails
   for want of a flag.** Network-disabled: the training container is its own
   source materializer and clones project and engine from inside itself as its
   first act, so denying egress breaks the lane rather than hardening it, and a
   repo-wide search for a network-blocking flag returns zero. Credential-free
   container: falsified by measurement, the container reads two named Secret
   keys and injects both into the trainer subprocess. Neither is encoded as a
   precondition here, neither appears in the DO-NOT-RUN table of section 7, and
   neither may be added later as one. This agrees with 29.9 ruling (7) above.

4. **Who executes is a standing session ruling, not merely this dispatch's
   wording.** The team-lead executes every account-mutating or credential-bearing
   provider step from the released checkout: environment, Volumes, Secret, key
   rotations, deploy and the single paid submit. Teammates prepare the command
   lines and verify afterwards, and no teammate is handed a credential. The first
   paid submit and any object creation are additionally confirmed with the user
   at the moment of execution. The DIRECT-INVOCATION steps 3 and 4 sit inside
   this ruling rather than beside it: a few typed lines that change no file,
   prepared by the author and executed by the lead.

5. **Whether the environment must pre-exist is a measurement, not a ruling.**
   The record does not carry it and the secretary declined to assert it. It is
   settled in section 4 question (1) from probe A (the SDK default
   `create_if_missing: bool = False`) and probe B (the creation command's own
   help output). A separate creation command is therefore required, and it is
   step 2, executed by the lead under item 4.

One item is **not** corroborated. The record carries no caller census for the
rotation module or for the deploy entry, so finding 1 of section 9, that no
production caller exists for either, is **new** rather than confirmed. Nothing
in the record contradicts it. The secretary notes a precedent pointing the same
way: a handoff in this arc claimed five acceptance gates where the commit landed
four, and the rule the lead adopted from it is to enumerate a deliverable set
from the commit rather than from the dispatch wording. That is the instrument
used for finding 1.

---

## 2. Baseline, measured

Every figure in this section was measured by the author at authoring time with
the command shown. Nothing here is relayed.

```
"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' rev-parse HEAD
  -> 34d6623d88dd61cfe0ca36b2afb522edbf5bd867

"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' ls-tree HEAD -- synaptic-tuner
  -> 160000 commit 5db2809d0160b166a0d2b133b97368ddcfe426ce	synaptic-tuner

"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' status --porcelain
  -> (empty: clean)
```

run with cwd `/mnt/f/Code/ehr-release-34d6623d`.

Configuration, read directly from `training/providers/modal.json` in the
released checkout (`cat training/providers/modal.json`), not relayed:

| Field | Value |
|---|---|
| `environment_name` | `synaptic-smoke-v1` |
| `volumes.control_name` | `synaptic-training-control-smoke-v1` |
| `volumes.artifact_name` | `synaptic-training-artifacts-smoke-v1` |
| `runtime_secret.name` | `synaptic-training-runtime-smoke-v1` |
| `runtime_secret.required_keys` | `HF_TOKEN`, `SYNAPTIC_EVIDENCE_MAC_KEY` |
| `deployment.timeout_seconds` | `3600` |
| `budget` | `100` minor units, `USD` |
| `profile` | `modal-a10-v1` |

Existence checks for every path this runbook names, all run with cwd
`/mnt/f/Code/ehr-release-34d6623d`:

```
find training -type f
  -> training/artifacts.json
     training/fixtures/modal-smoke.jsonl
     training/providers/docker.json
     training/providers/modal.json
     training/smokes/docker-sft.json
     training/smokes/modal-sft.json
     training/storage.json

ls -la .synaptic
  -> /usr/bin/ls: cannot access '.synaptic': No such file or directory

ls -d /mnt/c/Users/Joseph/AppData/Local/Programs/Python/Python312/python.exe
  -> /mnt/c/Users/Joseph/AppData/Local/Programs/Python/Python312/python.exe
```

> **Read every governed document with unproxied git.** The rtk proxy returned a
> mangled result for the author's first heading grep on the ruling document
> (it printed a cross-file match list that did not exist). Every read behind
> this runbook was re-run through `rtk proxy <cmd>` or the absolute `git.exe`.

---

## 3. Local probes the author ran

Permitted by the dispatch; none reached Modal and none carried a credential.
The submit container was started with **no** `-e` flags, so it held no token.

**Probe A — SDK signatures inside `synaptic-modal-submit:34d6623d`:**

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm synaptic-modal-submit:34d6623d python3 -c "<inspect.signature>"
```

printed:

```
modal 1.5.4
Environment.from_name (name: str, *, create_if_missing: bool = False, client=None)
Volume.from_name (name: str, *, environment_name=None, create_if_missing: bool = False, version=None, create_options=None, client=None)
Secret.from_name (name: str, *, environment_name=None, required_keys: list[str] = [], client=None)
App.lookup (name: str, *, client=None, environment_name=None, create_if_missing: bool = False)
has Environment.objects.create: True
```

**Probe B — the modal CLI's environment creation surface**, same image, same
no-credential invocation:

```
python3 -m modal environment create --help
  -> Usage: python -m modal environment create [OPTIONS] NAME
     Create a new environment in the current workspace.
     Options: --restricted, -h/--help
```

**Probe C — the Windows Host Python's package set:**

```
'/mnt/c/Users/Joseph/AppData/Local/Programs/Python/Python312/python.exe' -c \
  "import sys, importlib.util; print(sys.version.split()[0]); \
   print('modal', importlib.util.find_spec('modal'))"
  -> 3.12.7
  -> modal ABSENT
```

Probe C is load-bearing and is why step 4 runs where it does. See section 4,
question (2).

---

## 4. The eight questions, settled from code

### (1) Must the environment `synaptic-smoke-v1` pre-exist? **YES.**

`ExplicitModalHostSession.from_credentials` calls

```python
environment = sdk.Environment.from_name(config.environment_name, client=client)
environment.hydrate()
```

at `modal_provider.py:748-749`, and again in `observe_scope` at `:769-771`.
Neither call passes `create_if_missing`. Probe A measured the SDK default:

```
Environment.from_name (name: str, *, create_if_missing: bool = False, ...)
```

Default `False`. **The Host will never create the environment.** `hydrate()` on
an absent environment raises, so every credential-bearing Host command fails
until the environment exists.

Creation command, from probe B, run inside the submit container (step 2).

### (2) Is the triple created by a separable deploy step? **YES, and the step has no caller.**

`ModalHostSession.deploy` (`modal_provider.py:1010`) creates the triple itself
at `:1083-1097`: `Volume.objects.create` twice and `Secret.objects.create`
carrying `HF_TOKEN` and `SYNAPTIC_EVIDENCE_MAC_KEY = authenticator.encoded_key`
(`:1101`). It then writes `provider-state.json` (`:1109`). It is a complete,
separable step.

It is also **uncalled in production.** Measured:

```
rtk proxy grep -rn "\.deploy(" --include=*.py synaptic_host tests
  -> synaptic_host/modal_provider.py:962         (the SDK's own objects.app.deploy)
  -> tests/synaptic_host/test_modal_provider.py  (17 call sites)
```

`modal_training.py` builds the session with
`ExplicitModalHostSession.from_credentials` at `:620` and **never calls
`.deploy`**. The submit path instead loads `ModalProviderAuthorityV1` at
`modal_training.py:596`, whose `state` field is a `ModalProviderStateV1`
(`modal_provider.py:610`) — the record `deploy` writes. So the submit path
**requires** a prior deploy and cannot perform one.

**Consequence for 29.12:** G5 `--check` **can** be green before the paid
submit, and must be. The order is: create environment → rotate → deploy →
G5 `--check` → submit. This is reported to the lead as a settled answer, not
chosen silently.

**Where deploy runs.** Probe C measured `modal ABSENT` from the Windows Host
Python. `deploy` needs the SDK. So the deploy step runs **inside the submit
container**, which carries modal 1.5.4, with the released checkout bind-mounted.
The rotation step (question 3) needs no SDK and runs under the Windows Host
Python. The two steps therefore use different interpreters against the same
`state_root`. See the UNVERIFIED register, item U-1: whether the container's
uid 1000 can create and write `F:/Code/ehr-release-34d6623d/.synaptic` over the
DrvFs bind is **not settled**, and it is the one thing most likely to stop the
smoke at step 4.

### (3) The Host evidence-key rotation

`rotate_host_evidence_key(context)` (`modal_key_rotation.py:55-80`) builds
`FileHmacAuthenticator.from_context(context, key_ref=HOST_EVIDENCE_KEY_REF)`,
calls `_remove_key_file(authenticator.key_path)`, then `initialize()`.

**The path it removes:** `state_root/modal/evidence-hmac.key`, named in 29.3
and in the function's own docstring. Path only. Never open it, never report its
size.

**Why the delete is load-bearing**, quoted from the module docstring
(`modal_key_rotation.py:16-21`):

> `FileHmacAuthenticator.initialize()` creates with `O_EXCL` and, on
> `FileExistsError`, reads the existing key back and returns it. So
> `initialize()` alone is a read, never a rotation.

**Confirmation by the lead:** existence and mtime of the path, nothing else.
`_remove_key_file` returns `False` on an absent file and does not raise
(`:39-52`), so the procedure is correct on a host that never held the key —
which is this host. See question (4).

### (4) How the worker key reaches the Secret, and the stale-key risk

`build_worker_authenticator(context)` (`modal_provider.py:60-76`) opens
`state_root/modal/worker-hmac.key`. `deploy` calls `authenticator.initialize()`
at `modal_provider.py:1071` and then puts `authenticator.encoded_key` into the
Secret at `:1101`.

`initialize()` is `O_EXCL` and therefore a **read** on an existing file. So if a
stale worker key from the 2026-08-26 deployment were present at that path, the
**old key material would be uploaded into the new Secret**, which is exactly the
outcome 29.3 ruling (1) forbids.

**Measured answer: it is absent here.**

```
ls -la /mnt/f/Code/ehr-release-34d6623d/.synaptic
  -> No such file or directory
```

The entire private-storage chain is absent from the released checkout, so
neither `evidence-hmac.key` nor `worker-hmac.key` exists in it. The 2026-08-26
keys live under whatever project root was used then, which is a different tree
and is **not read** by this runbook. Both `initialize()` calls will therefore
mint fresh material.

**This is a property of executing from a fresh released checkout, not a
property of the code.** It is the load-bearing precondition of the whole
rotation ruling on this run, so step 3 makes the lead *verify absence* rather
than assume it, and step 3b removes the worker key if it is ever present.

### (5) The G5 `--check` invocation

Step 5. `--rotation-recorded-at` takes the UTC timestamp the lead recorded at
step 3. The `--check` arm is **UNEXERCISED** (recorded as a Known limitation in
`.skills/host-modal-run/SKILL.md`), so it is marked UNVERIFIED (U-2).

### (6) The single submit, observation, stop, and evidence

The submit argv is fixed at exactly eight tokens by `_parse`
(`cli.py:497-512`): `["training", "run"]` followed by three
`--name value` pairs drawn from `{--provider, --config, --destination}`.

- `--provider modal`
- `--config` must start with `project://training/` (`cli.py:522-523`), so
  `project://training/smokes/modal-sft.json`
- `--destination` must equal `provider-staging` for modal
  (`cli.py:23` `_DESTINATION`, refused otherwise at `:852-862`)

**Budget, timeout and retries are NOT flags.** `100` minor units USD and
`3600` seconds come from `training/providers/modal.json` (section 2), and
`retries=0` is an engine deployment constant per 29.9. The dispatch phrase "the
submit command with budget 100, timeout 3600, retries 0" describes the
configuration those values are read from, not arguments to type. Changing them
would mean editing the configuration file, which this task forbids.

The config file is read from the **committed git blob**, never the worktree
(`cli.py:885-887`, the C1 fix of 29.5(f)), so an uncommitted edit would not
take effect and a dirty checkout is refused earlier.

Observation, stop and evidence: step 8 and step 9.

### (7) The optional X4 dry run

29.12: "The dry run is not a gate... If it is run at all it is run inside the
submit container, as an observation, and its passing proves nothing about the
four items G3 and G4 cover." Step 6, optional, skippable.

### (8) DO-NOT-RUN

Section 7.

---

## 5. Preconditions

1. Docker Desktop running; the Linux engine reachable on the constructed
   endpoint. Check: `docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine version --format "{{.Server.Version}}"`.
2. Released checkout clean at `34d6623d`, gitlink `5db2809d` (section 2
   commands).
3. G2, G3 and G5-offline green (#489). Step 1 re-confirms cheaply.
4. `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` available to the lead's shell.
   See U-3.
5. `HF_TOKEN` available. `/mnt/f/Code/Toolset-Training/.env` carries the name;
   there is no `.env` in the released checkout or the worktree.

### The credential mechanism, from code

`launcher.py:37` defines `_MODAL_CREDENTIAL_ENV = ("MODAL_TOKEN_ID",
"MODAL_TOKEN_SECRET")`. At `:712-720` the launcher reads each name from
`os.environ` of the **parent process**, validates it through
`_validated_child_environment_value` (4096-byte bound), and places it into the
closed child environment block built at `:710`. If either is missing the dict is
**cleared** and the child receives neither, which surfaces as
`CREDENTIALS_UNAVAILABLE` (`cli.py:1072-1077`).

So: the operator sets both names in the **process environment** of the command
that starts the run. They never appear in argv and never land in a durable
artifact.

For container steps, pass them with `-e NAME` and **no** `=value`, so docker
inherits the value from the host environment and the value never enters the
docker.exe command line:

```
-e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET
```

Never write `-e MODAL_TOKEN_ID=...`.

---

## 6. The steps

Notation: `PY312` is
`C:\Users\Joseph\AppData\Local\Programs\Python\Python312\python.exe`;
`DOCKER` is
`/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe`;
`ENDPOINT` is `npipe:////./pipe/dockerDesktopLinuxEngine`;
`RELEASE` is `F:/Code/ehr-release-34d6623d` (Windows) and
`/mnt/f/Code/ehr-release-34d6623d` (WSL).

---

### Step 0 — confirm the checkout

**cwd** `/mnt/f/Code/ehr-release-34d6623d`. **Credentials** none.
**Account effect** none.

```
"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' rev-parse HEAD
"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' ls-tree HEAD -- synaptic-tuner
"/mnt/c/Program Files/Git/cmd/git.exe" -c safe.directory='*' status --porcelain
```

**Expected** `34d6623d88dd61cfe0ca36b2afb522edbf5bd867`; gitlink
`5db2809d0160b166a0d2b133b97368ddcfe426ce`; empty porcelain.

**Recovery** Any deviation stops the run. A dirty checkout is not a smoke
condition; re-cut the release rather than cleaning in place.

---

### Step 1 — re-confirm G2, G3, G5-offline

**cwd** `/mnt/f/Code/ehr-release-34d6623d`. **Credentials** none.
**Account effect** none.

```
SUBMIT_IMAGE_TAG=synaptic-modal-submit:34d6623d \
  bash .skills/host-modal-run/container/build.sh --g2 --no-build
python3 .skills/host-modal-run/scripts/g3_engine_lock_digests.py --expect 0
python3 .skills/host-modal-run/scripts/g5_isolation_triple.py
```

**Expected** G2 six checks pass, exit 0. G3 `0 of 7` mismatches, exit 0. G5
offline: S1/S2/S3 pass, **S4 REFUSED** (no rotation attestation yet), exit 1.
The S4 refusal is correct at this point and is not a failure.

**Note** `build.sh` has no `--no-cache` flag. `--no-build` gates the existing
image `synaptic-modal-submit:34d6623d`, which #489 built with a forced full
rebuild. Do not rebuild here; if a rebuild is ever needed, call docker.exe
directly with `--no-cache` under a sha-carrying tag (recorded as follow-up
#492).

**Recovery** Any red here stops the run before a single account action.

---

### Step 2 — create the dedicated environment

**cwd** any. **Credentials** `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`, passed by
name only. **Account effect** CREATES the provider environment
`synaptic-smoke-v1`. **Must not touch** the existing environment or any object
in it.

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm -e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET \
  synaptic-modal-submit:34d6623d \
  python3 -m modal environment create synaptic-smoke-v1
```

**Expected** a short confirmation naming the created environment. Exit 0.

**Verify immediately:**

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm -e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET \
  synaptic-modal-submit:34d6623d \
  python3 -m modal environment list
```

`synaptic-smoke-v1` present. Do not inspect the existing environment's contents.

**Recovery** If it already exists, the create will refuse; that is acceptable
only if the lead created it in a previous attempt of this same runbook. An
environment of this name created by anything else is a stop-and-report.
Deleting an environment is on the DO-NOT-RUN list.

**Auditor later** confirms exactly one new environment and no change to the
existing one.

---

### Step 3 — rotate the Host evidence key (DIRECT-INVOCATION)

**cwd** `F:/Code/ehr-release-34d6623d`. **Interpreter** Windows Host Python.
**Credentials** none. **Account effect** none; this is local only.

**3a. Verify absence first** (the load-bearing precondition of question 4):

```
"%PY312%" -c "import pathlib,sys; r=pathlib.Path(r'F:\Code\ehr-release-34d6623d'); p=r/'.synaptic'; print('synaptic_exists', p.exists()); print('listing', sorted(str(q.relative_to(r)) for q in p.rglob('*')) if p.exists() else [])"
```

**Expected** `synaptic_exists False`. If it is `True`, list the paths (names
only, never contents) and go to 3b before deploying.

**3b. Rotate.** DIRECT-INVOCATION: `modal_key_rotation.py` has no CLI caller
anywhere in the released checkout, measured by the author:

```
rtk proxy grep -rn "modal_key_rotation\|rotate_host_evidence_key\|retire_worker_channel" .
  -> only tests/synaptic_host/test_modal_key_rotation.py
```

so the lead types the invocation. The engine import root is established the way
`cli.py:941 _establish_engine_import_root` does, by **appending** to
`sys.path`. `PYTHONPATH` is never exported.

```
"%PY312%" -c "import sys; sys.path.append(r'F:\Code\ehr-release-34d6623d'); sys.path.append(r'F:\Code\ehr-release-34d6623d\synaptic-tuner'); from tuner.project.manifest import load_project_manifest; from synaptic_host.modal_key_rotation import rotate_host_evidence_key; import pathlib; root=pathlib.Path(r'F:\Code\ehr-release-34d6623d'); m=load_project_manifest(root/'synaptic.yaml'); ctx=m.create_context(engine_root=root/'synaptic-tuner', invocation_cwd=root); a=rotate_host_evidence_key(ctx); print('key_ref', a.key_ref); print('key_path', a.key_path); print('exists', a.key_path.exists()); import datetime; print('mtime_utc', datetime.datetime.utcfromtimestamp(a.key_path.stat().st_mtime).isoformat()+'Z')"
```

The `ProjectContext` construction is derived from `modal_training.py:590-595`,
which is the only place in the Host that builds one:

```python
manifest = load_project_manifest(project / "synaptic.yaml")
context = manifest.create_context(engine_root=engine, invocation_cwd=project)
```

**Expected output shape** four lines: `key_ref modal-evidence-v1`; `key_path`
ending `\.synaptic\...\modal\evidence-hmac.key`; `exists True`; an ISO-8601
`mtime_utc` within seconds of now. **Record that timestamp** — step 5 needs it.
No key material is printed and none may be.

**Verify immediately** existence and mtime only:

```
"%PY312%" -c "import pathlib,datetime; p=pathlib.Path(r'<key_path from above>'); print(p.exists(), datetime.datetime.utcfromtimestamp(p.stat().st_mtime).isoformat()+'Z')"
```

**3c. If 3a reported a pre-existing worker key**, remove it before step 4,
citing 29.3 ruling (1): `initialize()` is `O_EXCL` and would otherwise upload
stale material into the new Secret.

```
"%PY312%" -c "import pathlib; p=pathlib.Path(r'F:\Code\ehr-release-34d6623d')/'.synaptic'; import sys; [print('would remove', q) for q in p.rglob('worker-hmac.key')]"
```

Inspect the printed paths, then remove them by path with the same idiom
(`q.unlink()`), never opening them. On a clean released checkout this step is a
no-op and prints nothing.

**Recovery** If the rotation raises, nothing has reached the account yet.
Read the cause line, fix, re-run. The procedure is idempotent: a second run
deletes the key it just minted and mints another, which is harmless but changes
the recorded timestamp, so re-record it.

---

### Step 4 — deploy: create the isolation triple (DIRECT-INVOCATION)

**cwd** container `/workspace`. **Interpreter** the submit container's
`python3` (modal 1.5.4), because probe C measured `modal ABSENT` from the
Windows Host Python. **Credentials** `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`,
`HF_TOKEN`, all by name only. **Account effect** CREATES two Volumes and one
Secret in `synaptic-smoke-v1`, and deploys the app into it. **Must not touch**
the existing environment or its 2026-08-26 objects.

**This step is UNVERIFIED (U-1).** See the register. Run it only after reading
U-1 and its probe.

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm \
  -e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET -e HF_TOKEN \
  -v F:/Code/ehr-release-34d6623d:/workspace \
  -w /workspace \
  synaptic-modal-submit:34d6623d \
  python3 -c "import os,sys,pathlib; root=pathlib.Path('/workspace'); sys.path.append(str(root)); sys.path.append(str(root/'synaptic-tuner')); from tuner.project.manifest import load_project_manifest; from synaptic_host.modal_provider import ExplicitModalHostSession, ModalHostConfigV1, build_worker_authenticator; import modal; m=load_project_manifest(root/'synaptic.yaml'); ctx=m.create_context(engine_root=root/'synaptic-tuner', invocation_cwd=root); cfg=ModalHostConfigV1.load(ctx); client=modal.Client.from_credentials(os.environ['MODAL_TOKEN_ID'], os.environ['MODAL_TOKEN_SECRET']); s=ExplicitModalHostSession.from_credentials(sdk=modal, client=client, config=cfg); w=build_worker_authenticator(ctx); st=s.deploy(context=ctx, authenticator=w, hf_token=os.environ['HF_TOKEN']); print('deployed'); print('worker_key_ref', w.key_ref); print('state_written', (ctx.state_root/'modal'/'provider-state.json').exists())"
```

**Derived from:** `deploy` signature at `modal_provider.py:1010-1017`
(keyword-only `context`, `authenticator`, `hf_token`); the worker-authenticator
entry refusal at `:1019` (`_require_worker_authenticator`, so the Host key is
refused here by construction); triple creation at `:1083-1097`; the worker key
into the Secret at `:1101`; `provider-state.json` written at `:1109`. The
session constructor is `from_credentials` as used at `modal_training.py:620`.
`ModalClientBinding` construction and the SDK-version equality live at
`:740-762`.

**Expected output shape** `deployed`; `worker_key_ref modal-worker-v1`;
`state_written True`.

**Refusals you may legitimately meet, and what each means:**

| Message | Meaning | Action |
|---|---|---|
| `Modal SDK must be exactly 1.5.4` (`:743`) | wrong image | stop; rebuild the pinned image |
| `Modal provider is already deployed for this host` (`:1027`) | `provider-state.json` exists | **do not delete it**; read it. 29.6 write-once. |
| `HF_TOKEN is required to bind the named Modal Secret` (`:1037`) | env not set | set it and re-run |
| `Modal deployment resource collision` (`:1062`) | a named object or the app already exists in the environment | stop and report; do not adopt |

**Verify immediately** with step 5.

**Recovery, part-way** The deploy writes the journal before creating objects
(`:1067-1069`) and the state file last (`:1109`). If it dies between, the
journal exists and the state file does not; a re-run reads the journal and
continues, refusing if the config digest changed (`:1046`). **Never delete the
journal or the state file to force a retry** — 29.6 names them write-once and
the refusal text says to read rather than remove.

**Auditor later** confirms exactly two Volumes and one Secret in
`synaptic-smoke-v1` and no object created or modified in the existing
environment.

---

### Step 5 — G5 `--check` with the rotation timestamp

**cwd** `/mnt/f/Code/ehr-release-34d6623d`. **Credentials** by name only.
**Account effect** read-only lookups. **UNVERIFIED (U-2):** the `--check` arm
has never executed.

```
python3 .skills/host-modal-run/scripts/g5_isolation_triple.py \
  --check --rotation-recorded-at "<the mtime_utc recorded at step 3>"
```

**Expected** S1 four names distinct; S2 the two required Secret keys; S3 4/4
standing safety literals; S4 rotation ACCEPTED given the attestation. Exit 0.

The `--check` arm looks objects up with `create_if_missing=False`
(`modal_provider.py:785-821` is the same shape), so it can **confirm** the
triple and can never create it.

**Recovery** A red S1 means the four names are not distinct, which would mean
the smoke is pointed at the existing deployment: stop immediately. A red S4
means the attestation timestamp does not satisfy the ordering rule; re-check
that the step 3 timestamp precedes the step 4 deploy.

---

### Step 6 — optional X4 dry run (observation, NOT a gate)

29.12: the dry run is provably free, provably blocked at the installed SDK
version, cannot catch B-19, and if run at all is run **inside the submit
container**. Its passing proves nothing about G3 or G4. Skipping it is fully
compliant. If run, record the output and treat it as an observation only.

---

### Step 7 — the single paid submit

**cwd** container `/workspace`. **Credentials** `MODAL_TOKEN_ID`,
`MODAL_TOKEN_SECRET` by name only; `HF_TOKEN` reaches the training container
through the named Secret, not through this command. **Account effect** starts
ONE paid job. **Must not touch** the existing environment.

This runs from the Linux submit container, which is BINDING: the modal branch
cannot be entered without the authority the Linux-gated `launcher.py` re-exec
mints, and a direct dispatch from the Windows driver returns
`BOOTSTRAP_UNAVAILABLE`.

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm \
  -e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET \
  -v F:/Code/ehr-release-34d6623d:/workspace \
  -w /workspace \
  synaptic-modal-submit:34d6623d \
  python3 -m synaptic_host training run \
    --provider modal \
    --config project://training/smokes/modal-sft.json \
    --destination provider-staging
```

**Derived from** `__main__.py:18-33` (argv, project root
`Path(__file__).resolve().parents[1]`, engine root `project_root/"synaptic-tuner"`);
`_parse` at `cli.py:497-512` (exactly eight tokens, the three option names);
`_config_components` at `cli.py:515-527` (the `project://training/` prefix);
`_DESTINATION` at `cli.py:23`.

**Budget/timeout/retries** are configuration, not flags. See question (6).

**Expected output shape** a single JSON result envelope with
`status` `submitted`, `code` `SUBMITTED`, and a populated `provider_job_ref`,
`run_id`, `effect_id`, `submitted_at` (the `TrainingRunCommandResultV2` field
order is rebuilt and equality-checked at `cli.py:1090-1098`). Exit status is
the envelope's.

**If it fails**, the code names the stage: `CREDENTIALS_UNAVAILABLE`,
`BOOTSTRAP_UNAVAILABLE`, `PREFLIGHT_REJECTED`, `START_UNAVAILABLE` and so on
(`cli.py:39-55`), and a cause line goes to **stderr** (`__main__.py:69-76`,
`cli.py:1114-1118`). Read the cause line; G6 requires a refusal to name its own
cause.

**Recovery** A failure before `SUBMITTED` has not started a job. A failure
after leaves a durable row; do **not** re-run to retry. Re-running mints a new
run id by design (29.6), and this smoke is authorised for **one** job.

---

### Step 8 — observe and stop

**Credentials** by name only. **Account effect** read-only, except the stop.

**Observe:**

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm -e MODAL_TOKEN_ID -e MODAL_TOKEN_SECRET \
  synaptic-modal-submit:34d6623d \
  python3 -m modal app logs synaptic-training-v1 -e synaptic-smoke-v1
```

`modal app logs` fetches the last 100 entries and exits by default; `-f`
streams. Measured from `python3 -m modal app logs --help` (probe, no
credentials). `modal app list` gives running/deployed/recently-stopped apps.

> The app name is `synaptic-training-v1` **in the new environment**. That is
> 29.7: the app name is a module constant and does not vary; isolation comes
> from the environment. Always pass `-e synaptic-smoke-v1`. A log or stop
> command without the environment flag may address the **existing** deployment,
> which the user ruled untouched. This is the single most dangerous omission in
> this runbook.

**Stop criterion.** Stop when either holds:

1. The run reaches a terminal state (the trainer completes one step —
   `max_steps: 1` in `training/smokes/modal-sft.json` — and the container
   exits), or
2. Wall-clock exceeds the configured `timeout_seconds` of `3600`, or the lead
   judges the job is not progressing.

**Stop command** (only if the job must be stopped early):

```
python3 -m modal app stop synaptic-training-v1 -e synaptic-smoke-v1
```

Note `modal app stop` **permanently stops the App and terminates its running
containers** (its own help text). It is not a pause.

---

### Step 9 — read the run-acceptance evidence

**Credentials** none for the local half. **Account effect** none.

**Durable rows.** `SqliteTrainingRepository.from_context`
(`sqlite_repository.py:102-111`) resolves the database to
`context.state_root / "training.sqlite3"`, and asserts `state_root` stays below
`project_root/.synaptic`. Derive the path rather than hardcoding a segment:

```
"%PY312%" -c "import sys,pathlib; root=pathlib.Path(r'F:\Code\ehr-release-34d6623d'); sys.path.append(str(root)); sys.path.append(str(root/'synaptic-tuner')); from tuner.project.manifest import load_project_manifest; m=load_project_manifest(root/'synaptic.yaml'); ctx=m.create_context(engine_root=root/'synaptic-tuner', invocation_cwd=root); print(ctx.state_root/'training.sqlite3')"
```

Then read the rows. Tables created at `sqlite_repository.py:215-272`:

| Table | Why it matters here |
|---|---|
| `lifecycle_records` | the run's lifecycle phases and verification status |
| `modal_preparations` | the Modal-specific durable preparation row |
| `evidence_replay` | replay protection for evidence documents |
| `consumed_grants` | the one-shot grant this run consumed |
| `provider_preparations` | provider-side preparation record |

```
"%PY312%" -c "import sqlite3,sys; db=sys.argv[1]; c=sqlite3.connect(db); c.row_factory=sqlite3.Row; [print(t, [dict(r) for r in c.execute('SELECT * FROM '+t)]) for t in ('lifecycle_records','modal_preparations','evidence_replay','consumed_grants','provider_preparations')]" "<database path>"
```

**Evidence documents.** Per 29.3, the container emits the log chunk, log
metadata plus tag, terminal evidence plus tag, and on success the completion
manifest plus tag, every tag under `modal-worker-v1`; the Host verifies those
three under `modal-worker-v1` and the source and deployment attestations under
`modal-evidence-v1`. Confirm the **refs**, never the key material.

**Console-log secret sweep, by SHAPE, with a decoy control.**

Sweep the captured console output for credential-shaped strings rather than for
the values you happen to know. A sweep for known values verifies the
disclosure, not the exposure.

```
grep -nEc "\bak-[A-Za-z0-9]{8,}|\bas-[A-Za-z0-9]{8,}|\bhf_[A-Za-z0-9]{20,}|[A-Za-z0-9+/]{40,}={0,2}" <console capture file>
```

**Decoy control, and it is required.** Before trusting a zero, append one line
containing a synthetic, never-real string of each shape to a **copy** of the
capture and re-run the identical sweep. It must report a non-zero count. A
sweep that has never been shown to fire is not evidence that nothing leaked.
Delete the decoy copy afterwards. Never place a real credential in the decoy.

**29.11 assertions to READ, not steps to run.** Ruling (9): the manifest
overlap set is empty at the checked-in configuration and is pinned by a
configuration test. Ruling (10): the artifact-kind divergence between lanes is a
deliberate lane difference pinned by an assertion. Confirm both are green in
the acceptance-predicate module (test-host, #487); neither is an operator
action.

---

## 7. DO-NOT-RUN

| Do not run | Why |
|---|---|
| `retire_worker_channel` | 29.3: **closeout only**. It deletes the Secret. Running it before or during the smoke destroys the channel the run needs. |
| Any teardown: deleting Volumes, the Secret, the environment, or the app | Out of scope. The old app `synaptic-training-v1` is decided at closeout, not here. |
| Any command addressed to the existing environment or any 2026-08-26 object | User decision: untouched **and unread**. Every command carries `-e synaptic-smoke-v1`. |
| `modal app stop` without `-e synaptic-smoke-v1` | It may address the existing deployment. |
| Deleting `provider-state.json`, `deployment-journal.json`, or any key file to force a retry | 29.6 write-once. The refusal text names what to read, not what to remove. |
| Reading the contents of any key file or Secret | Credential material. Paths, refs, existence and mtime only. |
| `git push` | No push, by standing ruling. |
| Editing anything in the released checkout | Execution uses only a released checkout; edits invalidate the run. |
| A second submit | This smoke is authorised for exactly one paid job. |

---

## 8. UNVERIFIED register

Each item states what is unsettled, why the author could not settle it, and the
**one read-only probe** that would settle it for the lead.

**U-1 — can the submit container write `.synaptic` in the released checkout?**
Step 4 runs under the container's uid 1000 against a DrvFs bind of
`F:/Code/ehr-release-34d6623d`, and `deploy` creates the private-storage chain
there (`_ensure_private_chain` call sites at `modal_provider.py:532`, `:565`,
`:1286`). The docker lane needed B-9 (`--user`) and B-11 (chain repair) for
exactly this class of problem; the modal submit container carries none of that
machinery. The author could not settle it because settling it means **writing
into the released checkout**, which this task forbids.

*Probe for the lead, read-only, no credentials:*

```
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker.exe" \
  --host npipe:////./pipe/dockerDesktopLinuxEngine \
  run --rm -v F:/Code/ehr-release-34d6623d:/workspace -w /workspace \
  synaptic-modal-submit:34d6623d \
  sh -c 'id; touch .synaptic-probe && echo WRITABLE && rm -f .synaptic-probe || echo NOT-WRITABLE'
```

This writes and immediately removes one probe file at the checkout root. If the
lead prefers a checkout with **zero** writes, run the same probe against a
throwaway copy of the directory instead. If it reports `NOT-WRITABLE`, step 4
cannot run as written and that is a **BLOCKER for a ruling**, not something to
patch in the runbook: the remedies (a `--user` flag, a different state root, or
running deploy from a Linux-side path) each change where the Host's private
storage lives, which is an architecture decision.

**U-2 — the G5 `--check` arm has never executed.** Recorded as a Known
limitation in `.skills/host-modal-run/SKILL.md`. Step 5 is its first run. It
issues real `modal.Volume.from_name` / `modal.Secret.from_name` lookups with
`create_if_missing=False` and `.hydrate()`. Settled only by running it, which
requires credentials. If it errors on its own plumbing rather than on a real
mismatch, treat that as a script defect, not a gate failure, and report it.

**U-3 — where the operator's Modal token pair lives.** The mechanism is settled
from code (section 5). The operator-side half is not: the lead measured no
`MODAL_TOKEN_ID` or `MODAL_TOKEN_SECRET` line in
`/mnt/f/Code/Toolset-Training/.env`, and there is no `.env` in the released
checkout or the worktree. The author may not read a credential store.

*Probe for the lead — name-only presence, prints no value and no length:*

```
"%PY312%" -c "import os,sys; sys.stdout.write(str({k: (k in os.environ) for k in sys.argv[1:]}))" MODAL_TOKEN_ID MODAL_TOKEN_SECRET HF_TOKEN
```

Expected `{'MODAL_TOKEN_ID': True, 'MODAL_TOKEN_SECRET': True, 'HF_TOKEN': True}`
in the shell that will run steps 2, 4 and 7. Never echo a value.

**U-4 — the exact `provider_job_ref` and app identifier for step 8.** The log
and stop commands address the app by name plus environment, which is derivable.
If Modal requires the `ap-` app id instead, take it from
`python3 -m modal app list -e synaptic-smoke-v1`.

---

## 9. Findings for the lead (not steps)

1. **No production caller exists for `ModalHostSession.deploy` or for either
   rotation procedure.** Both are exercised only by tests. The triple-creating
   operator step of 29.9 is code nothing shipped invokes. That is why steps 3
   and 4 are DIRECT-INVOCATION. Recorded as a follow-up beside #492: the Host
   owes a CLI entry for provisioning and rotation.
2. **The Windows Host Python has no Modal SDK** (probe C), so the Host-side
   provisioning entry cannot be driven from the mandated Host interpreter at
   all today. That is the structural reason step 3 and step 4 use different
   interpreters, and it deserves an architecture decision rather than a
   permanent runbook workaround.
3. **U-1 may be a blocker.** If the container cannot write the private-storage
   chain in the released checkout, the smoke cannot proceed as designed.
4. The dispatch describes budget, timeout and retries as parts of the submit
   command. They are configuration values, not flags; the runbook says so at
   question (6) rather than inventing arguments that `_parse` would reject.
