# Modal smoke of the prepared path: evidence, policy diff, and the launcher leakage question

PREPARE artifact for feature #420, phase #421, task #428. Pins: Host `d0888ed6`, engine `ce539b70`.
Companion: `modal-blocker-applicability-census.md`. Peers: #429 external surface, #430 Windows failing set.

Scope A: deploy, start, observe, verify one isolated job, stop before publication.

Every claim carries a `file:line` read at the pins. Claims about what a Modal-side artifact will
contain are marked **STRUCTURAL**: they are reads of what the code would write, not observations.
Nothing in this tree has ever executed a Modal job, so no Modal-side statement here is a measurement.

---

## 1. Evidence recovery

### 1.1 Host side, what a scope A run leaves

Four surfaces, all under the project's private storage root, `.synaptic`.

| Surface | Path / site | Written by |
|---|---|---|
| Provider state | `state_root/modal/provider-state.json` (`modal_provider.py:840`, written `:916`) | deployment lifecycle |
| Deployment journal | `state_root/modal/deployment-journal.json` (`:841`, read `:542`, written `:876`) | deployment lifecycle |
| Upgrade record | under `state_root/modal` (`:993`, written `:1023`) | provider upgrade path |
| Evidence signing key | `state_root/modal/evidence-hmac.key` (`security.py:669`) | the lane's authenticator |

Plus three SQLite tables created by the Modal arm: `lifecycle_records`
(`sqlite_repository.py:219`), `modal_preparations` (`:232`) and `evidence_replay` (`:242`).
These are distinct from the docker tables (`_DOCKER_TABLE_COLUMNS` at `:64-72`,
`provider_preparations` and `docker_run_mutations`) and from the publication tables
(`_COEXISTING_TABLES` at `:73-76`). **No new table is needed for the smoke.**

### 1.2 The property that governs retries: durable records are write-once

`_atomic_json` at `modal_provider.py:403-410` does three things in order: `mkdir(parents=True,
exist_ok=True)` on the parent, then

```
if path.exists() or path.is_symlink():
    raise FileExistsError("durable host record already exists")
```

then an `O_EXCL` create at mode `0o600`.

Two consequences the architect must rule on.

1. **A failed run leaves its records in place, and they refuse the next attempt at the same
   path.** This is deliberate (it is what makes the record durable), but it means "retry the
   smoke" is not a no-op: someone must decide whether the second attempt is a new run id with
   new paths, or whether the operator removes the record. The failure mode is a
   `FileExistsError` surfacing through the ninety-line handler as an opaque
   `COMPOSITION_UNAVAILABLE`, which is the B-18 class and is why that fix is a pre-submit gate.
2. **The `mkdir` on the parent is the SEC-F2 site.** It creates `.synaptic/state/modal/` with no
   private-chain construction, no B-11-R1 leaf-first repair and no validation. The mode `0o600`
   on the *file* is real protection; the *directory* it sits in inherits whatever the parent
   grants.

### 1.3 Which Host artifacts survive a failed run

All of them. Every surface in 1.1 is written before or during the job's lifecycle and none is
cleaned up on failure. That is good for a smoke: the run's own record is the deliverable, and a
refusal that names its code (gate G4 in the plan) plus these files is a complete diagnosis.

### 1.4 Modal side (STRUCTURAL, and #429 owns the measurement)

Declared in `training/providers/modal.json`, names only, no values:

- two volumes, `control_name` and `artifact_name`, which `deployment_v1.py:50-51` requires to
  be *distinct* (`"Modal control and artifact volumes must differ"`);
- one secret by name, with a required key pair;
- an app name that is a module constant (`deployment_v1.py:17`), **not** config-parameterised.

STRUCTURAL consequence, and it is the isolation question: because the app name is a constant and
the volume names are checked-in config, a smoke that reuses them shares the artifact volume with
every earlier and later run. The plan's separate-triple decision addresses the two volumes and
the secret; the app name is a code constant and cannot be varied by config alone.

What survives a failed run on the Modal side is **not determined by this tree**: volume retention
is an account property. #429 owns it. Do not infer retention from the code.

### 1.5 Reading evidence back without a credential in argv or a log

Three properties already hold and should be preserved rather than rebuilt.

- **Credentials never reach argv.** The token pair is read from the operator environment into a
  closed seven-name child allowlist at `launcher.py:632-639` (`_ALLOWED_CHILD_ENV` at `:34-36`,
  `_MODAL_CREDENTIAL_ENV` at `:37`), all-or-nothing: if either value fails validation the dict is
  cleared (`:635-637`). The Host composition itself refuses to resolve secret values at all
  (`modal_training.py:57-61`, wired at `:530`).
- **The engine excludes secrets from the deployment environment map** (`deployment_v1.py:60-70`)
  and screens forbidden symbols (`:58-64`).
- **The redactor does not yet cover this lane's two credential shapes** (`redaction.py:7-12`,
  `:21-24`). That is R4, and it is why the post-run value-shape sweep is a compensating control
  rather than a duplicate.

Recovery procedure that respects all three: read the four JSON surfaces and the three SQLite
tables directly from `.synaptic` on the submit host, and read the Modal-side job log through the
account, never by echoing the environment. No step requires a credential on a command line.

---

## 2. Manifest and model-inventory policy: the diff

This is a diff, not a restatement. Only the rows where the lanes **differ** are listed.

| Property | Docker lane | Modal lane | Consequence |
|---|---|---|---|
| Artifact kinds | absent. The canonical document is built at `docker_training.py:515-525` with no `required_kinds` field, and a non-test census of the identifier returns zero hits in that file | forwarded: `modal_resolver.py:768` reads `baseline.training_input.artifacts.required_kinds` | The Modal arm enforces an artifact-kind requirement the Docker lane discards. Everything the fourteen local runs proved about artifact selection was proved with this field **absent**. |
| Source delivery | staged: the Host archives the locked project inputs (B-12 shape) | cloned: `GitDualCloneMaterializer` (`modal_provider.py:759`); the container clones project and engine itself (`runtime.py:124-183`) and refuses with `project_clone_failed` / `engine_clone_failed` exit 124 at `:164-177` | Two different source contracts. Reconciling them would be the compatibility layer the standing rule forbids; the plan's C1 narrows the committed-source read instead. |
| Committed-blob config read | yes (`cli.py:874-884`) | no; falls through to a plain worktree read | This is C1, and it is why a released cut must precede the submit. |
| Environment pin | `SourceLockV1.required_environment`, 13 keys (`execution_source.py:489-500`), roots on the bind mount | same 13 keys, built by `resolution.py:563-575`, roots container-absolute at `/workspace/run/<run_id>/...` | Same contract, different roots. See 2.1. |
| Runtime lock | source lock pins the environment | `ModalRuntimeLockV1` (`config.py:175`) pins **no environment at all**: closed key set `{schema_version, sdk_version, registry_reference, python, locked_files, ml_stack}` | The B-10-R1 class does **not** reproduce here. See the census 5.4. |
| Image | profile-declared digest | same digest, via the runtime lock's `registry_reference`, which `deployment_v1.py:46-47` requires to be digest-pinned | Identical image; the engine builds the Modal function from the reference. No push. |

### 2.1 The overlap check, and the trap in it

`resolution.py:576-578`:

```
overlap = set(fixed_environment).intersection(locked_deployment.runtime_environment)
if any(locked_deployment.runtime_environment[key] != fixed_environment[key] for key in overlap):
    raise SourceLockError("deployment runtime environment conflicts with fixed isolation")
environment = {**locked_deployment.runtime_environment, **fixed_environment}
```

Measured at this pin: `training/providers/modal.json` declares `runtime_environment` keys
`{LANG, PATH}`. Intersection with the 13 fixed keys is **empty**. No conflict is possible at the
checked-in config, and the fixed values win the merge regardless.

**Trap:** adding any of the 13 (`HF_HOME`, `PYTHONPATH`, `SYNAPTIC_*_ROOT`, `WANDB_DISABLED`,
`TRANSFORMERS_CACHE`, ...) to that config with a different value makes the run refuse with
`SourceLockError` before submit. Cheap to trip, and the message names isolation rather than the
config file, so record it in the operator recipe.

### 2.2 Model inventory for the tiny model

The inventory is asserted by **revision literal**, never by downloading weights
(`materialize_model_inventory.py:90`). That property is lane-independent and carries to Modal
unchanged. The plan's checked-in entry-and-digest manifest is the right shape: it keeps the
no-downloader rule intact while giving the verifier something to compare against.

---

## 3. The launcher leakage question: one finding or two

### 3.1 What is actually there

`synaptic_host/launcher.py` builds environments in **two** places, and they are opposites.

**The child environment (closed, correct).** `:620-639` iterates `_ALLOWED_CHILD_ENV`, validates
each value, adds the credential pair all-or-nothing, then adds four marker and digest keys. Fail
closed.

**The uv environment (open).** `_uv_environment` at `:365-366` opens with

```
environment = dict(os.environ)
```

and then updates the `UV_*` keys. The entire operator environment is handed to the uv subprocesses.

### 3.2 The call graph decides it

- `_build_runtime` (`:378`) calls `_uv_binary` (`:388`) then `_uv_environment` (`:389`).
  `_build_runtime` has exactly one call site: `:616`, inside the recovery arm that fires when
  `_runtime_proof` raises. That is the **cache-miss / rebuild** path.
- `_uv_binary` (`:318`) is reached on **every** call, including `:237`. Its cache-hit arm at
  `:325-331` returns the cached binary when `binary.is_file()` and a sibling stamp file
  `.archive-sha256` *contains the expected hex string*. The binary itself is **not re-hashed**.
  The digest is verified only on first fetch, at `:345-346`.
- `_cache_root` is `project_root / ".synaptic" / "cache"` (`:64-65`), so the cached uv binary
  lives inside the same private-storage tree that B-11, B-11-R1, #170 and SEC-F2 govern.

### 3.3 The argument for ONE finding

Both halves are the same root cause: the launcher trusts its ambient host instead of pinning
what it consumes. One fix framing ("pin the launcher's inputs") covers the environment and the
binary together, one ruling covers both, and the pre-submit bundle already carries a launcher
change so the second half is nearly free to land beside it.

### 3.4 The argument for TWO findings

They differ on every axis a ruling turns on.

| Axis | Environment copy | Unhashed cache hit |
|---|---|---|
| Property | confidentiality: credentials flow **out** to a third-party process tree | integrity: unverified code runs **in** |
| Trigger | cache-**miss** only (`:616` → `:389`) | cache-**hit** only (`:325-331`) |
| When | first run on a cold cache | second and subsequent runs |
| Fix | local code change in `_uv_environment` | re-hash on hit, **or** bring `.synaptic/cache` under the private-chain ACL |
| Owner | coder, pre-submit bundle | overlaps SEC-F2 / #170 machinery |
| Plan status | in the six decided pre-submit fixes | recorded separately as "not a smoke blocker" |

And the decisive one: **the two triggers are mutually exclusive within a single run.** A cold-cache
run rebuilds (environment copy fires) and digest-verifies the binary (integrity holds). A
warm-cache run skips the rebuild (no environment copy) and trusts the stamp (integrity gap).
No single execution exhibits both. They cannot share a test, and a fix for either leaves the
other's trigger untouched.

### 3.5 Recommendation

**Two findings.** Keep R7 as the environment copy: pre-submit, already decided, fix in
`_uv_environment`. Split the cache-hit integrity gap out under its own identifier and rule it
**with SEC-F2 and #170**, not with R7, because its real fix surface is the `.synaptic` ACL chain
rather than the launcher's environment construction. Filing it under R7 would either drag a
non-blocking item into a blocking bundle, or let it be marked resolved when only the environment
allowlist landed. The second outcome is the dangerous one.

Caveat: this recommendation is a recommendation. The architect decides, and the one-finding
reading is coherent if the intent is a single "pin the launcher" ruling.

---

## 4. What the ARCHITECT must decide

A list, no designs.

1. **Retry semantics for the write-once durable records** (1.2): new run id, or operator removal,
   and which of the four surfaces may legitimately be deleted after a failed smoke.
2. **The shape of the SEC-F2 fix** at `modal_provider.py:403-404`, and whether it covers only
   `.synaptic/state/modal` or the whole `.synaptic/cache` subtree as well, which is what decides
   whether the cache-hit integrity item is discharged with it.
3. **One finding or two** on the launcher leakage (section 3), and if two, the identifier and
   disposition of the second.
4. **Whether the app-name constant** (`deployment_v1.py:17`) needs to vary for the smoke, given
   that config alone cannot isolate it while the two volumes and the secret can.
5. **Whether the CLOSEOUT bucket** (census section 4) is admitted into section 29, and where
   #339, #274 and #340 are recorded if so.
6. **Whether the overlap trap** (2.1) is prevented by a config test or only documented.
7. **Whether the artifact-kind divergence** (2, row 1) is a defect in the docker lane, a
   deliberate lane difference, or something the smoke should assert.

## 5. Boundary drain

- Modal-side retention, volume and secret existence, SDK installability: **#429**.
- Windows failing-set baseline and where X3 lands on the Modal path: **#430**.
- Nothing in this document required a credential, and no value appears in it.
