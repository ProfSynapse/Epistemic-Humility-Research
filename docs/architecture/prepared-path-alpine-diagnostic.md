# Real-trainer tiny-model host run through the untouched prepared path — ARCHITECT

Phase: ARCHITECT. Feature #73 (plan step 3, reshaped; former steps 3-6 merged).
Owner: `architect-run`. Upstream: PREPARE tasks #80 (`preparer-path`) and #81
(`preparer-host`), plus the consultant blocker filed as task #84.

Worktree: `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean`
Branch `feat/submodule-cloud-api-v1-host-clean`, head `e1439de3`.
Engine submodule `synaptic-tuner` pinned at `aec998ee` — read, never modified.

All `file:line` citations were read from the working tree at head. Where a
number differs from `docs/architecture/native-windows-publication-closure.md`
(pinned to `85b922fc`), this document is the live one.

---

## 0. Status — read this first

The design below is complete and executable **except for one gate that no
design can open**, because the code that closes it is inside the pinned engine.

| # | Item | State |
|---|---|---|
| B-1 | Mount source names a path that does not exist in the `docker-desktop` distro | **Resolved by design** (section 6). Code fix specified. |
| B-2 | LoRA `adapter_config.json` cannot satisfy the engine's locked-model-ref equality | **BLOCKED** (section 7). Escalated to team-lead. Needs a user ruling or a one-run probe. |

Everything else — device, model inventory, opt-in surface, run recipe,
reconcile discipline, acceptance contract, reusable workflow, secrets — is
settled and is unaffected by how B-2 is ruled. B-2 changes **where the run
stops**, not how it starts.

Three findings reverse or replace a PREPARE recommendation. They are stated
here rather than buried, because each one changes what CODE and TEST do.

1. **The CPU branch is dead, so decision D3 costs nothing.** The `nvidia`
   literal at `docker_training.py:825` needs no change, because CPU was never
   reachable. Section 3.
2. **Mount sources cannot be put on distro ext4.** `preparer-host` recommended
   it; the code forbids it twice over. The project root must be a Windows drive
   path, and that dissolves the F-1(c) conflict the lead asked me to resolve.
   Section 6.
3. **The opt-in needs no new file and no code.** The committed smoke is already
   a valid `--config` ref. Section 5.

---

## 1. What the user ruled, and what it commits us to

The user ruled D1 option A on 2026-09-02: run the **real SFT entrypoint**
through the **untouched prepared path**, with the tiny SmolLM2 snapshot
already pinned in the committed smoke, materializing the model inventory first.

That ruling is forced by two seams PREPARE found and I re-verified:

- The container argv is recomputed from the engine's locked closure manifest
  and compared for exact equality, raising before any container exists
  (`synaptic_host/docker_staging.py:1552-1587`). The closure entrypoint is read
  as a git blob at the pinned engine commit and is
  `Trainers/sft/runtime_v1.py`.
- Artifact verification delegates into the engine's content-bound
  `SFT_ARTIFACT_CONTRACT` (`synaptic_host/docker_execution.py:851`, `:972`).

So the workload is not a design variable. What remains a design variable is
everything around it, and that is what this document decides.

---

## 2. The run, end to end, as it will actually execute

One operator command, re-run until the phase stops advancing:

```
python.exe -m synaptic_host training run \
    --provider docker \
    --config project://training/smokes/docker-sft.json \
    --destination local-default
```

Eight argv tokens exactly, which is what the fixed-arity parser demands
(`synaptic_host/cli.py:494`, option loop `:500-509`).

Each invocation performs **one cut**, dispatched on the durable phase
(`synaptic_host/docker_training.py:920-953`):

| Invocation | Entry phase | What happens | Exit phase |
|---|---|---|---|
| 1 | none | admission, staging, submit | `SUBMITTED` |
| 2..N | `SUBMITTED` | observe the process; while the container runs, nothing changes | `SUBMITTED`, then `PROCESS_SUCCEEDED` or `PROCESS_FAILED` |
| N+1 | `PROCESS_SUCCEEDED` | verify artifacts through the engine | `ARTIFACTS_VERIFIED` or `PROCESS_FAILED` |
| N+2 | `ARTIFACTS_VERIFIED` | compose the publication and publish | stays `ARTIFACTS_VERIFIED` |

There is **no separate reconcile verb**. The CLI has one command. Re-running it
is how an operator reconciles. This is the single most misreadable thing about
the run and it is why section 9 states the reconcile count concretely.

---

## 3. Decision — device is GPU, and the code delta is zero

**Ruling: GPU. Do not make `docker_training.py:825` profile-driven. Do not
widen `training/providers/docker.json:24-26`. D3 is withdrawn.**

PREPARE framed D3 as a choice. It is not one, because the CPU branch cannot
run at all. The entrypoint itself is stdlib-only and would tolerate CPU, but it
spawns a second process that does not:

- `Trainers/sft/runtime_v1.py:1329-1344` runs `subprocess.run(invocation.argv, ...)`;
  argv is built at `:1164-1167` and targets `tuner/runtime/offline_sft_worker.py`.
- That worker ends at `tuner/runtime/offline_sft_worker.py:632-639` with
  `runpy.run_path` on `Trainers/sft/train_sft.py`.
- `Trainers/sft/train_sft.py:137` is `from unsloth import is_bfloat16_supported`,
  unconditional and at module top level, with `import torch` at `:135`.
- Two further pins have no CPU fallback and no flag to override them:
  `optim: "adamw_8bit"` (`Trainers/sft/configs/config.yaml:66`, a bitsandbytes
  optimizer) and `bf16: true` (`:68`), consumed at `train_sft.py:1206-1208`
  where both branches call unsloth's GPU-capability probe.

So "CPU with a two-line delta" was a two-line delta plus an unverified premise
plus two unoverridable GPU pins. The honest device ruling is GPU, and it is
also the ruling with no code change, which is the outcome the constraints
prefer.

**Why this weakens no production guarantee: it changes nothing.** The literal
at `docker_training.py:825` stays a literal, the profile keeps
`"allowed": ["nvidia"]`, and the `--gpus driver=nvidia,device=0` flag the
composition emits for kind `nvidia` (`docker_v1/control_private.py:396-397`) is
the flag the run wants.

**Stated risk, carried from the lead's addendum, not resolved here.** The
image's `NVIDIA_REQUIRE_CUDA` bands top out below driver 566 and this host runs
610.88. Whether the container toolkit rejects, warns, or ignores that is
untested. If it rejects, the failure will look unrelated to the design. TEST
asserts GPU visibility inside the container as an early step (section 9) so
this surfaces with its true cause.

---

## 4. Decision — the model inventory

### 4.1 What the Host demands, quoted

Resolution is `resolve_docker_model_inventory_v1`
(`synaptic_host/docker_model_inventory.py:195-262`), called from
`docker_training.py:658-663` before activation.

The storage binding must be exactly this, or admission fails
(`docker_model_inventory.py:20-24`, checked at `:237-246`):

```
    _ROOT_REF      = "docker-model-inventory-source"
    _LOCATION_REF  = "project://.synaptic/model-inventory"
    _PERMIT_REF    = "permit-docker-model-inventory-source"
    binding.access is RootAccessV1.READ_ONLY
```

**All four already match the committed `training/storage.json:40-45`. No
storage change is needed.** The profile preconditions at
`docker_model_inventory.py:213-219` (`cache_admission is True`,
`network_mode == "none"`, `inventory_root_ref == "docker-model-inventory-source"`)
are likewise already satisfied by `training/providers/docker.json:14`, `:35`,
`:44`.

The on-disk layout is fixed (`docker_model_inventory.py:249-251`):

```
    <project_root>/.synaptic/model-inventory/
        models--HuggingFaceTB--SmolLM2-135M-Instruct/
            snapshots/
                12fd25f77366fa6b3b4b768ec3050bf629380bac/
                    <the snapshot's files>
```

The repo id is split and validated at `docker_model_inventory.py:78-88`:
exactly two `/`-parts, each matching `[A-Za-z0-9][A-Za-z0-9._-]{0,95}`, none
ending in `.` or `-`, none containing `..` or `--`. The revision must be 40
lowercase hex (`:25`, `:223`) and `model.revision` must equal
`model.tokenizer_revision` (`:220-221`). The committed smoke satisfies all of
this (`training/smokes/docker-sft.json:5-7`).

### 4.2 The five properties the materialized tree must have

These are the ones a careless materialization breaks. Every one of them raises.

| # | Property | Enforced at |
|---|---|---|
| 1 | **No symlinks and no reparse points**, anywhere in the tree or in the four directories above it | `docker_model_inventory.py:145-146`, `:62-75` |
| 2 | Relative paths **NFC-normalized**, no backslash | `:148-149` |
| 3 | **No case-colliding paths** | `:150-153` |
| 4 | Regular files only, no special files, at most 20 000, at least one | `:159-166`, `:27` |
| 5 | Nothing changes during the read; every file is hashed with a before/after identity check | `:91-123`, `:182-191` |

**Property 1 is the trap.** `huggingface_hub`'s default cache layout makes
`snapshots/<rev>/<file>` a **symlink** into `blobs/<sha>`. A materialization
that copies a normal HF cache directory will be rejected outright with
`"model snapshot contains a redirect"`. The tree must be real files.

### 4.3 How the operator materializes it — outside the Host, through Docker

The user's standing constraint (lead ruling, 2026-09-02) is that no conda
environment exists on the host and everything model-related runs through
Docker. Materialization is therefore an operator step in a throwaway container,
run with plain `docker.exe` and never through `synaptic_host`. **No downloader
is added to the Host**, which is what the constraints require.

The step, in shape (the checked-in script in section 11 is the real artifact):

```
docker.exe run --rm \
  -v "<project_root>\.synaptic\model-inventory:/out" \
  python:3.12-slim \
  sh -c 'pip install --no-cache-dir "huggingface_hub" && \
         python - <<PY
from huggingface_hub import snapshot_download
import pathlib, shutil
REPO="HuggingFaceTB/SmolLM2-135M-Instruct"
REV="12fd25f77366fa6b3b4b768ec3050bf629380bac"
tmp = snapshot_download(REPO, revision=REV, local_dir="/tmp/snap")
name = "models--" + REPO.replace("/", "--")   # models--HuggingFaceTB--SmolLM2-135M-Instruct
dest = pathlib.Path("/out") / name / "snapshots" / REV
dest.mkdir(parents=True, exist_ok=True)
for p in sorted(pathlib.Path(tmp).rglob("*")):
    if p.is_file() and not p.is_symlink():
        target = dest / p.relative_to(tmp)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)   # copyfile, never copy2 or symlink
PY'
```

> **Lead amendment 2026-09-02 (sketch defect, found by coder-workflow):** the guard `p.is_file() and not p.is_symlink()` above is wrong under the huggingface_hub cache layout that section 4.2 describes: every snapshot entry is a symlink into `blobs/<sha>`, so the guard is false for every file, the loop copies nothing, and the Host later rejects an EMPTY snapshot at `docker_model_inventory.py:165-166`. The checked-in script (`.skills/host-docker-run/scripts/materialize_model_inventory.py`) keeps only a resolves-to-a-regular-file test, lets `shutil.copyfile` dereference, skips a leading `.cache` component, and exits non-zero from inside the container if zero files were copied. Do not copy the sketch's guard.

`python:3.12-slim` is already present locally (`preparer-host`, image list), so
this pulls no new image. `copyfile` is load-bearing: it dereferences, which is
what turns the HF cache's symlinks into the real files property 1 demands.

**Integrity evidence recorded.** Two independent records, neither of which the
operator writes:

1. The Host re-hashes every file during resolution
   (`docker_model_inventory.py:91-123`) and again after copying it into the
   stage (`_copy_inventory` at `docker_staging.py:1349-1395`, re-verified by
   `_verify_inventory_at` at `:1398-1435`).
2. The result is folded into a single digest,
   `staged_model_inventory_digest` (`docker_staging.py:1708`, `:1766`), which
   is one of the eight digests the content-addressed `stage_key` is built from
   (`docker_staging.py:1745-1754`).

**How the run proves the inventory was used.** Four ways, all durable or
in-container:

- The `stage_key` changes if a single inventory byte changes, so the stage the
  run used is bound to the exact tree.
- `staged_model_inventory_digest` is on the durable preparation record.
- Inside the container, `_require_local_model_snapshot`
  (`Trainers/sft/runtime_v1.py:654-719`) re-checks the canonical path, the
  offline env pins, the absence of links, containment under the cache root, and
  that the directory name equals the revision.
- After loading, the trainer asserts the model and tokenizer both resolve to
  that exact snapshot (`Trainers/sft/src/model_loader.py:229-238`).

### 4.4 Where the inventory lives, and the ext4 question

It lives under the **Host project root**, because the location ref is
`project://.synaptic/model-inventory` and `project://` roots are joined onto
`project_root` (`synaptic_host/local_io_v1/config.py:151-153`).

`preparer-host` recommended putting mount sources and artifact destinations on
distro ext4 under `/home/profsynapse`. **That is not reachable, and section 6
shows why.** The inventory therefore lives on the same Windows drive as the
project root. This is not a compromise the design chose; it is the only shape
the code admits.

The container reaches the snapshot at
`/artifacts/cache/model/models--HuggingFaceTB--SmolLM2-135M-Instruct/snapshots/12fd25f7.../`,
because staging copies it under the stage's `cache` directory
(`docker_staging.py:1708`) and `cache` is the one artifact directory allowed to
be non-empty (`_EMPTY_ARTIFACT_DIRECTORY_NAMES`, `docker_staging.py:49-50`).
That matches the path the trainer computes at
`Trainers/sft/runtime_v1.py:636-652` exactly.

---

## 5. Decision — the opt-in surface adds no code and no file

**Ruling: use the existing committed smoke as the `--config` ref. Add nothing.**

D4 offered four options. The zero-surface one is available and it is already
committed, so the design takes it.

`--config` accepts any ref under `project://training/`
(`synaptic_host/cli.py:512-537`). The component regex
(`cli.py:26`, `_COMPONENT = ^[^\\/?#%\x00-\x1f\x7f]+$`) admits dots, so
`project://training/smokes/docker-sft.json` is a valid ref with no parser
change. The file it names is already a `synaptic-training-input/v1` document
pinning the SmolLM2 snapshot at `max_steps: 1`
(`training/smokes/docker-sft.json:2-7`, `:18`).

Two consequences worth stating rather than discovering:

- The config is read as a **committed git blob** at the locked project commit
  (`docker_training.py:589-593`), not from the working tree. Any new or edited
  config must be committed before it can be used. Using the existing smoke
  avoids that entirely.
- `training/smokes/docker-sft.json:40-43` requests only two artifact kinds. The
  Host discards that and substitutes its own five-role tuple
  (`docker_training.py:47-50`, applied at `:528-531`). This is expected, not a
  mismatch.

**D6 is ruled out explicitly. No new destination, no new storage root, no new
database table.**

- There is exactly one destination, `local-default` with adapter
  `host.local/v1` (`training/artifacts.json:6-8`), and Windows is selected at
  runtime by `os.name` beneath it
  (`synaptic_host/publication_composition.py:394-413`). Adding a
  Windows-specific destination would break the provider-neutrality ruling the
  prior architecture set, so it is not added.
- The four storage roots the run needs already exist
  (`training/storage.json:22-45`).
- The durable record is a row in the existing `publication_records_v1`
  (`synaptic_host/publication_store.py:164-180`, insert `:229-244`). Nothing
  the diagnostic does needs a table that is not there.
- The SQLite file location is not an operator choice: it is
  `<project_root>/.synaptic/state/training.sqlite3`, forced at
  `synaptic_host/sqlite_repository.py:107-111`, which also refuses a state root
  that is not below the project's `.synaptic` directory.

---

## 6. Decision — the mount-source mapping fix (blocker B-1)

### 6.1 What is wrong

`preparer-host` measured it (task #84). The committed profile pins
`"wsl_distro": "docker-desktop"` (`training/providers/docker.json:37-40`). The
translator renders a drive-letter stage path as `/mnt/<drive>/<relative>`
(`synaptic_host/docker_v1/prepared.py:44-52`) and the UNC is built by plain
concatenation (`prepared.py:223`):

```
    unc = "\\\\wsl.localhost\\" + self._distro + request.posix_path.replace("/", "\\")
```

So the emitted bind source is
`\\wsl.localhost\docker-desktop\mnt\f\Code\Toolset-Training\...`. Inside the
`docker-desktop` distro, `/mnt` is that distro's own ext4 and the host drives
are drvfs at `/mnt/host/{c,e,f}`. The emitted path does not exist. `/mnt/f`
survives there as an empty skeleton from a legacy bind, which is worse than
absence because it looks plausible; the mount still fails, because
`control_private.py:404-407` uses `--mount type=bind`, which fails hard on a
missing source. **Keep it `--mount`. Do not switch to `-v`, which would create
the source directory silently.**

### 6.2 There is no contradiction between the two guards

The lead asked me to resolve an apparent conflict: `config.py` refuses a UNC
project root while the mount contract requires a `wsl.localhost` source. The
conflict does not exist, and the reason matters for CODE.

The two guards act on **different representations of the same path**, and the
translator is the bridge between them.

- The project root is refused if it opens on two separators
  (`local_io_v1/config.py:113-119`, helper at `:44-55`). So it must be a
  drive-letter path.
- Independently, `_wsl_path` **raises** unless the stage path has a Windows
  drive (`prepared.py:46-47`: `len(drive) != 2 or drive[1] != ":"`). So a
  distro-ext4 project root could not work even if `config.py` allowed it.
- The mount source is then *derived*, not configured, so it is always a
  `wsl.localhost` UNC and always satisfies `docker_safe_unc_v1`
  (`docker_v1/control_contract.py:124-165`).

**Therefore the "storage root split" idea is impossible and must not be
attempted.** A non-`project://` storage location must still be component-wise
contained under the project root (`config.py:171-177`), so no root can be moved
off the drive the project lives on.

**And therefore `preparer-host`'s ext4 recommendation is withdrawn.** I overrule
it on the evidence above. The project root stays on `F:` (NTFS, measured
reparse-clean from the drive root down), which is also what dissolves the
F-1(c) question.

### 6.3 The fix — a profile-driven drive-mount root

**Ruling: make the drive-mount prefix a committed profile value. Do not
hard-code a `docker-desktop` special case in Host code.**

Add `docker_host.drive_mount_root` to the committed profile, thread it to the
translator, and render `{drive_mount_root}/{drive}/{relative}`.

The rationale is not tidiness. Two candidate values are live and **neither is
proven**:

| Candidate | Emitted source | Status |
|---|---|---|
| `/mnt/host` with distro `docker-desktop` | `\\wsl.localhost\docker-desktop\mnt\host\f\...` | Path exists in the distro [measured]. Windows-side UNC read denied, WinError 5 — but the engine resolves the source inside the distro, so that is a proxy, not a verdict. |
| `/mnt` with distro `Ubuntu-22.04` | `\\wsl.localhost\Ubuntu-22.04\mnt\f\...` | Path exists [measured]. Adds a Windows-to-WSL-to-9p hop, and pins a committed profile to one operator's distro name. |

Making the prefix configuration is what turns the choice between them into a
**value TEST selects from a probe**, rather than a second code change after the
first one fails. That is the whole argument for this shape.

I prefer `/mnt/host` with `docker-desktop`: it names where `F:` genuinely
appears in the distro where the engine runs, and it keeps the committed profile
describing Docker Desktop rather than a user distro. `Ubuntu-22.04` + `/mnt` is
the fallback, reachable by editing one committed value.

### 6.4 The exact code delta

Five files. Every call site was enumerated, not estimated.

| File | Change |
|---|---|
| `training/providers/docker.json:37-40` | add `"drive_mount_root": "/mnt/host"` |
| `synaptic_host/docker_provider.py` | dataclass field beside `wsl_distro` (`:93`); validate in `__post_init__` beside `:122`; widen the exact field set at `:157-159`; read it in `from_mapping` at `:183`; emit it in `to_dict` at `:222` |
| `synaptic_host/docker_prepared_composition.py` | parameter on `compose_docker_prepared_platform_v1` (`:83-87`) and its gate (`:93-97`); field on `DockerPreparedPlatformV1` (`:56-72`); pass at `:154`; pass to the adapter at `:206-209` |
| `synaptic_host/docker_training.py:879-882` | pass `drive_mount_root=snapshot.profile.drive_mount_root` |
| `synaptic_host/docker_v1/prepared.py` | `_wsl_path(path, root)` at `:44-52`; adapter field; the two calls at `:100-101` |

Validation for the new value: absolute POSIX path, no trailing slash, and it
must pass `canonical_wsl_path_v1` (`docker_v1/model.py:605-630`), which the
rendered full path must satisfy anyway. `docker_safe_unc_v1` needs no change —
I checked both predicates accept `/mnt/host/f/...` and
`\\wsl.localhost\docker-desktop\mnt\host\f\...`.

**Make the parameter required, not defaulted.** A default of `/mnt` would let a
caller silently reproduce the defect. Three existing test call sites must pass
it: `tests/synaptic_host/test_docker_prepared_composition.py:86` and
`tests/synaptic_host/docker_v1/test_prepared.py:98`, `:149`.

**Digest consequence, stated so nobody debugs it later.** The new field enters
`to_dict`, so `profile.digest` changes, which changes the provider policy
digest, the execution context, the plan fingerprint and the stage key. That is
correct and harmless for a first run, but it means any pre-existing durable row
from an earlier attempt belongs to a different plan and will not be resumed.

---

## 7. BLOCKED — the LoRA adapter reference equality (blocker B-2)

This is filed as task #85 and escalated to team-lead. **No design in this
document opens it**, because the rejecting code is inside the pinned engine.

### 7.1 The defect

Verification requires the LoRA adapter config to echo the locked model ref
exactly:

```
    tuner/runtime/verification.py:251-254
        locked_model_ref = workload.document["configuration"]["document"]["model"]["ref"]
                         -> "HuggingFaceTB/SmolLM2-135M-Instruct"

    tuner/runtime/verification.py:940-953   (_valid_model_config)
        document.get("peft_type") == "LORA"
        and document["base_model_name_or_path"] == locked_model_ref
```

The in-container twin raises first
(`Trainers/sft/runtime_v1.py:1803-1814`,
`RuntimeV1Error("trainer adapter config is not recognizable LoRA")`).

But the trainer loads the base model **by local snapshot path, deliberately**
(`Trainers/sft/src/model_loader.py:208-228`, with the reason documented at
`:176-179`: unsloth otherwise silently rewrites a Hub name to an optimized
mirror with a different commit identity), and asserts that
`model.config._name_or_path` is that path (`:232-235`). PEFT stamps
`base_model_name_or_path` from the model's `name_or_path`, so
`adapter_config.json` will carry the snapshot directory, not the repo id.
Nothing rewrites it: `base_model_name_or_path` has only readers across
`Trainers/`, and `_archive_artifact`
(`Trainers/sft/runtime_v1.py:1676-1698`) streams files verbatim.

### 7.2 Why it cannot be designed around

- **A non-LoRA full fine-tune would pass**, because the else branch of
  `_valid_model_config` only wants a non-empty `model_type` string. Every LoRA
  flag is optional at the runtime layer (`Trainers/sft/runtime_v1.py:1244-1253`,
  each guarded by `if key in sft`). But `apply_lora_adapters` is called
  **unconditionally** at `Trainers/sft/train_sft.py:1159`, so omitting
  `--lora-r` only falls back to the `config.yaml` default and LoRA is still
  applied. There is no workload that reaches a full fine-tune.
- **Making the model ref a path is closed.** Both
  `docker_model_inventory.py:78-88` and `tuner/runtime/dispatch.py:194-208`
  require a one-or-two-part repo id and derive the cache directory name from it.

### 7.3 Where it fails and how it will look

Inside the container, at artifact assembly, **before `final_model.tar` exists**.
The Host therefore sees a non-zero trainer exit, not a verification verdict. If
it surfaces through the worker's fail-closed path, the only stderr line is the
opaque `OFFLINE_SFT_WORKER_REJECTED` with exit 2
(`tuner/runtime/offline_sft_worker.py:645-648`).

**TEST must read `<SYNAPTIC_TRACKING_ROOT>/trainer.stderr.log`
(`Trainers/sft/runtime_v1.py:1231-1232`) before diagnosing anything from the
exit code.** Without that, this defect is indistinguishable from a GPU problem,
a mount problem, or an image problem.

### 7.4 The one unread thing, and the recommendation

I could not read the `peft`/`transformers`/`unsloth` versions installed in the
committed image. That is the only way this passes. Every version readable in
this tree behaves as described, and the PEFT assignment is stable across
versions, so I rate the defect likely but not certain.

**Recommended: probe before deciding.** Run the real command once and read
`trainer.stderr.log`. If it fails at `runtime_v1.py:1811`, the defect is
confirmed on this image and the pin question goes to the user. If it passes,
the blocker dissolves. This costs one run that the plan needs anyway, and it
converts an unread third-party version into a measured fact before anyone
proposes moving a pin.

### 7.5 What still succeeds if B-2 is real

The run still proves, on the untouched prepared path: admission, model
inventory resolution and staging, closure staging with argv equality, Windows
platform composition, container create and start with the real image, the
observe cut, the durable SQLite record, and replay idempotency. It stops at
verification. That is materially more than the plan had before, and it is why
the rest of this document stands regardless.

---

## 8. Artifacts, and the two archives that must pass

For the record, so TEST knows what "success" looks like when B-2 is resolved.

Five artifacts, written **flat at the artifact root**
(`Trainers/sft/runtime_v1.py:1663-1665`), plus the inventory file one level
away:

| Role | File | Written at |
|---|---|---|
| `workload_record` | `/artifacts/workload.json` | `runtime_v1.py:1421-1423` |
| `training_lineage` | `/artifacts/training_lineage.json` | `:1437-1444` |
| `training_metrics` | `/artifacts/training_metrics.json` | `:1445-1452` |
| `final_model` | `/artifacts/final_model.tar` | `:1453-1464` |
| `tokenizer` | `/artifacts/tokenizer.tar` | `:1465-1473` |
| (inventory) | `/artifacts/state/runtime-v1-inventory.json` | `:1474-1483` |

**Precondition:** the artifact root must be empty when the trainer starts
(`runtime_v1.py:1393`), which is exactly what staging guarantees
(`docker_staging.py:50`).

The tokenizer archive is expected to pass. SmolLM2 is a byte-level BPE
tokenizer, and every file `save_pretrained` writes for it —
`tokenizer_config.json`, `tokenizer.json`, `special_tokens_map.json`,
`vocab.json`, `merges.txt`, `added_tokens.json`, and `chat_template.jinja` on
recent transformers — is inside the allowlist at
`tuner/runtime/verification.py:76-81`, and each content check holds.

**One latent hazard for later, not triggered by this run.** `aux_head.safetensors`
and `aux_head_config.json` (`Trainers/sft/train_sft.py:1466-1479`) are in
neither the selection nor the ignore set, so any future run that enables the
auxiliary head dies at
`Trainers/sft/runtime_v1.py:1791` with
`"trainer model output contains an unsupported file"`. Recorded here so it is
not rediscovered.

---

## 9. The run recipe for TEST

### 9.1 Prerequisites, in order

1. **Windows Python, not WSL Python.** Use the checked-in recipe
   `scratch/test-phase/winpy2.sh`, which is `winpy.sh` plus
   `GIT_CONFIG_GLOBAL` for git long-path support. **Use `winpy2.sh`, because
   the activation path shells out to git.** It sets `WSLENV=PYTHONPATH` and
   `PYTHONPATH` in Windows form with `;` separators.
2. **The project root is a Windows drive path.** `F:` is NTFS and measured
   reparse-clean from the drive root down. The project root is computed from
   the package location (`synaptic_host/__main__.py:19`,
   `Path(__file__).resolve().parents[1]`), so it is chosen by which checkout
   Windows Python imports.
3. **Exactly one `docker.exe` on the Windows PATH.** The composition requires
   exactly one candidate and raises otherwise
   (`docker_prepared_composition.py:103-121`). Assert this before the run: WSL
   has two other docker binaries and they must not be the ones found.
4. **Do not pass an endpoint flag.** The npipe endpoint is not an operator
   choice. The Host probes `docker context inspect desktop-linux` and then
   re-asserts the descriptor equals
   `npipe:////./pipe/dockerDesktopLinuxEngine` exactly
   (`docker_prepared_composition.py:140-146`). Passing `-H` yourself is only
   for the read-only probes in step 5.
5. **Materialize the model inventory** (section 4.3) and confirm the tree is
   link-free before running anything.
6. **Probe the mount source before the first real run** (blocker B-1's
   residual): confirm the engine can bind
   `\\wsl.localhost\docker-desktop\mnt\host\f\...`. If it cannot, switch
   `docker_host.drive_mount_root` to `/mnt` and `wsl_distro` to `Ubuntu-22.04`
   and re-probe. This is a configuration change, not a code change.

### 9.2 The command sequence

The same command, repeated. Nothing else.

```
scratch/test-phase/winpy2.sh -c "import synaptic_host"      # import smoke first
# then, per cut:
python.exe -m synaptic_host training run \
    --provider docker \
    --config project://training/smokes/docker-sft.json \
    --destination local-default
```

Expected phase transitions, and what each result means:

| Cut | Expect | Meaning |
|---|---|---|
| 1 | `SUBMITTED` | container created and started |
| 2..N | `SUBMITTED` while running | `docker_execution.py:1201-1202` (branch at `:1201`) returns the record unchanged on `RUNNING`. **This is not a stall.** |
| N+1 | `PROCESS_SUCCEEDED` or `PROCESS_FAILED` | `:1217-1220` |
| N+2 | `ARTIFACTS_VERIFIED` | verify cut, `:1164-1181`. Publishes nothing. |
| N+3 | published | publish cut, `:1137-1163` |

### 9.3 What "reconcile at least twice" means concretely

PREPARE's D7 said at least two. **It is at least three post-submit cuts**, and
the third is the one people forget:

1. an **observe** cut, which may repeat while the container runs,
2. a **verify** cut, which writes `ARTIFACTS_VERIFIED` and publishes nothing,
3. a **publish** cut, which is always a separate call
   (`docker_training.py:927-949` constructs the publication only in the
   `ARTIFACTS_VERIFIED` branch).

**Reading `published == False` after one reconcile is the correct behaviour of
a healthy system.** An acceptance script that reconciles once and concludes
failure has measured nothing.

### 9.4 Container naming is a non-issue

The mission listed `--name` collision avoidance against the three running
containers. It cannot happen. The name is derived, not chosen:
`"synaptic-" + command_digest[:24]`
(`synaptic-tuner/tuner/execution/providers/docker_provider_v1/model.py:588-589`,
labels built at `:1346-1354`). It cannot collide with `cc-test-pg`,
`heuristic_lamarr` or `youthful_margulis`. No design element is needed here.

---

## 10. Acceptance contract

### 10.1 Early assertions, before the long wait

These catch the known unknowns with their true cause, instead of letting them
surface later disguised as something else. Each one is cheap.

| # | Assertion | Why it exists |
|---|---|---|
| A1 | GPU is visible inside the container | The image's `NVIDIA_REQUIRE_CUDA` bands top out below the host's driver 610.88; a toolkit rejection would otherwise look like an unrelated failure |
| A2 | `/artifacts` is writable by the container's non-root user `unsloth:runtimeusers` over a `wsl.localhost` bind | Unmeasured, flagged by the lead. A read-only `/artifacts` fails late and confusingly |
| A3 | The container's `/opt/conda/bin/python3` reports exactly `3.11.14` | `Trainers/sft/runtime_v1.py:1121-1138` demands a **full patch-level** match against the profile's `python_version` (`training/providers/docker.json:8`) and refuses otherwise |
| A4 | The staged snapshot exists at the cache path and contains no links | Confirms the inventory design end to end before training starts |

### 10.2 What TEST asserts on success

| Surface | Assertion | Evidence |
|---|---|---|
| Artifacts | five roles present, in the normalized order `final_model, tokenizer, training_lineage, training_metrics, workload_record` | `docker_execution.py:708`, `:714-719`; sorted at `:1006-1008` |
| Inventory file | byte-exact canonical JSON, exactly three top-level keys, schema `synaptic-artifact-inventory/v1`, the run's own `workload_fingerprint`, exactly five rows of exactly four keys | `docker_execution.py:877-899` |
| Verification | `VERIFIED`, with all five semantic checks non-empty and passed | `tuner/runtime/verification.py:274-280`, `:1167-1180` |
| Publication | one row in `publication_records_v1` for `destination_ref` `local-default` | `publication_store.py:164-180`, `:229-244` |
| Durable record | phase `ARTIFACTS_VERIFIED`, container ref and submit time present | `docker_training.py:715-719` |
| Replay | re-running after publication changes nothing and raises nothing | optimistic concurrency `docker_execution.py:1059-1065`; closed transition table `docker_execution_state.py:690-735` |
| Stage reuse | a second identical run reuses the stage and re-verifies it byte for byte | `docker_staging.py:1611-1648` |

### 10.3 The M-8 / A-2 assertions, corrected

The mission asked for "positive M-8/A-2 assertions" in the host run. One of the
two cannot be asserted there, and saying so is the point.

- **Assertable in the host run.** `SUBMITTED` requires three things, not two:
  `not outcome.reconcile_required`, a container ref, and a submit time
  (`docker_training.py:715-719`). Any cut that sets `RECONCILE_REQUIRED` must
  therefore **not** report a submitted run. TEST asserts this positively.
- **Not assertable in the host run.** The
  `PUBLICATION_COMPOSITION_ABSENT` directive
  (`docker_execution.py:1137-1159`, directive returned at `:1157-1159`) is reachable **only under a race**: the
  publish cut builds its own publication whenever the phase is
  `ARTIFACTS_VERIFIED` (`docker_training.py:927-949`), so a sequential operator
  can never see it. It belongs in a CODE-phase unit test that drives
  `reconcile` with `publication=None` against a verified record. Trying to
  force it from the host run would mean contriving a concurrent activation,
  which proves nothing about this feature.

### 10.4 Residuals R-3 and R-4

| Residual | What settles it | Where |
|---|---|---|
| R-3, five-role emission | The verify cut returning `ARTIFACTS_VERIFIED` **is** the settlement: the result type refuses anything but the exact five-role tuple, so a verified record is proof the engine emitted all five | `docker_execution.py:708`, `:714-719` |
| R-4 | A Windows publication that completes with no unexplained `IO_FAILED` | `local_io_v1/windows.py:193-198`, `:1050-1083` |

Both probes that PREPARE queued are already settled by `preparer-host` and need
no further work: an empty relative name under a directory handle returns
`STATUS_SUCCESS`, and `ntpath.realpath` never introduces a `\\?\` prefix, not
even at 460 characters. The second retires the `CONFIG_INVALID` false-refusal
concern for drive-letter project roots, which is exactly the shape this run
uses.

---

## 11. Reusable workflow, per the repo's tooling discipline

The recipe must not be a throwaway. Two checked-in artifacts and one skill
update.

| Artifact | Purpose |
|---|---|
| `scratch/test-phase/` run records | Per-run evidence only, not the workflow |
| A checked-in materialization script (see below) | Builds the model inventory reproducibly, in a container, with no host Python environment |
| A checked-in run driver | Wraps the repeated `training run` cut, prints the phase after each cut, and stops when the phase stops advancing |

**Placement.** The materialization script and the run driver belong beside the
existing Windows recipes in `scratch/test-phase/`, because that is where
`winpy.sh` and `winpy2.sh` already live and the run is host-specific. The
durable knowledge — that the container argv is locked, that reconcile needs
three cuts, that the model inventory must be link-free, and that
`trainer.stderr.log` is the first thing to read on failure — belongs in a skill.

> **Lead amendment 2026-09-02 (placement):** `scratch/` is gitignored (`.gitignore:9`), so nothing under `scratch/test-phase/` can be a checked-in artifact; `winpy.sh`/`winpy2.sh` are untracked. The materialization script and run driver live in a NEW canonical skill under `.skills/<skill>/scripts/` (the repo's tracked convention), mirrors synced with `bin/sync_skills.py` scoped to that skill. `scratch/test-phase/` keeps run RECORDS only. Raised by auditor-run (YELLOW); ruled by the lead; coder-workflow records the final paths with `git check-ignore` in its HANDOFF. Citation slip (auditor finding, no design change): `docker_safe_unc_v1` lives at `docker_v1/control_contract.py:124-150`; `docker_v1/model.py:605-630` is `canonical_wsl_path_v1` only. Two more record corrections after CODE: the section 10.3/13.1 "new" reconcile `publication=None` test already existed at `tests/synaptic_host/test_docker_execution.py:648` (no duplicate was added); and section 6.4's "three existing test call sites" was about ten sites across five test files, because exact-field profile validation makes every literal profile mapping a call site and `DockerPreparedPlatformV1` is constructed positionally.

**Skill update.** Add a prepared-Docker-path section to the canonical
`.skills/` tree, then sync the mirrors with the repo's sync script and its
`--check` mode. Do not hand-edit a mirror.

**Flagged, not done.** The worktree root has a tracked `CLAUDE.md`. I did not
read, write, or modify it, and no step of this design writes it. If the
knowledge above should also be pinned there, that is the orchestrator's call.

---

## 12. Secrets hygiene

The run introduces no credential exposure. Checked against the PREPARE section
5 table and re-verified at the cited lines.

| Channel | Why this run is safe |
|---|---|
| Prepared argv | The value set is closed: exactly `bundle.dispatch.environment` with `overrides=()` (`control_private.py:410-411`; `docker_prepared_composition.py:210-216`). The environment is cross-checked three ways before use (`control_private.py:384-390`), so no ambient variable leaks in |
| Network | `--network none` and `--pull never` are both emitted unconditionally (`control_private.py:392-393`). Nothing inside can reach a registry, and the image is never fetched |
| Secret requirements | The digest is over a document with `"secrets": []`, bound into the plan and the profile (`docker_training.py:479-483`, `:809-812`). This run does not change it |
| Staged source | Sources are locked git objects only, never the dirty tree (`docker_staging.py:1693-1700`) |
| Logs | There is no `logging`, no `logger` and no `print` on this path. The argv is never persisted in plaintext; everywhere it is durable it is a digest (`docker_v1/control_contract.py:1233-1243`) |
| Inventory | The materialized tree is model weights and tokenizer files. It is mounted **read-only** into the container as part of `/artifacts/cache`, and the Host binding requires `RootAccessV1.READ_ONLY` (`docker_model_inventory.py:241`) |
| Artifact directory | Mounted writable, so it must not be pointed at a directory holding credentials. It is not: it is a freshly created stage under `.synaptic/state/docker/stages/` |

Two things the design deliberately does **not** do, because each would break a
property above: it adds no container environment variable (which would change
`dispatch.environment`, the projection digest and the stage key), and it adds
no debug print of a create invocation (which would defeat the redacted
`__repr__` and raising `__reduce__` at `control_private.py:68-77`).

One residual, not introduced here: a secret embedded in an operator's own
submit command lands base64-encoded in `provider_preparations.record_json`.
The command in section 9.2 contains no secret.

---

## 13. Files to touch, and files that must not be touched

### 13.1 Touch

| Path | Change | Trigger |
|---|---|---|
| `training/providers/docker.json` | add `docker_host.drive_mount_root` | B-1 |
| `synaptic_host/docker_provider.py` | carry the new field (5 sites, section 6.4) | B-1 |
| `synaptic_host/docker_prepared_composition.py` | carry it to the mount adapter (4 sites) | B-1 |
| `synaptic_host/docker_training.py:879-882` | pass it | B-1 |
| `synaptic_host/docker_v1/prepared.py` | `_wsl_path` gains the root; 2 call sites | B-1 |
| `tests/synaptic_host/test_docker_prepared_composition.py:86` | pass the new argument | B-1 |
| `tests/synaptic_host/docker_v1/test_prepared.py:98`, `:149` | pass the new argument | B-1 |
| `tests/synaptic_host/docker_v1/test_prepared.py` | **new** test pinning the rendered source against the measured layout | B-1, per the #84 ruling |
| `tests/synaptic_host/test_docker_execution.py` | **new** test driving `reconcile` with `publication=None` on a verified record | section 10.3 |
| `scratch/test-phase/` | run records only (scripts moved to `.skills/<skill>/scripts/`, see the section 11 amendment) | section 11 |
| `.skills/` canonical tree, then mirror sync | prepared-path knowledge | section 11 |
| `docs/architecture/prepared-path-alpine-diagnostic.md` | this document | always |

### 13.2 Do not touch

| Path | Why |
|---|---|
| `synaptic-tuner/` — the whole submodule at `aec998ee` | Pinned. Includes the closure manifest, `tuner/runtime/verification.py` and `Trainers/sft/`. **B-2 lives here and is escalated rather than edited.** |
| `synaptic_host/docker_staging.py:1533-1588` | `_verify_worker_closure_binding`. The argv equality check is the strongest guarantee on the path |
| `synaptic_host/docker_execution.py` verifier | Delegates to the engine contract; not weakened |
| `synaptic_host/docker_v1/composition.py` | Legacy same-process facade. No production module imports it and the prepared path is already disjoint. It stays disjoint by changing nothing |
| `tests/synaptic_host/docker_v1/test_real_docker_wsl.py` | The legacy Alpine test. Not the acceptance gate: it drives the legacy facade, hand-builds its endpoint, uses a different distro, and its gate requires a POSIX process, which is the opposite of this lane |
| `synaptic_host/artifact_destinations.py`, `local_artifact_destination.py`, `artifact_spool.py` | Provider neutrality depends on the registry not learning a platform exists |
| `synaptic_host/publication_store.py` | No new table |
| `training/artifacts.json` | No Windows-specific destination |
| `training/storage.json` | Already correct; no new root |
| `training/smokes/docker-sft.json` | Already correct; using it unchanged is the opt-in |
| `synaptic_host/local_io_v1/posix.py`, `windows.py` guards | Ruled untouched; B-1 is fixed at the translator, not by relaxing a guard |
| `CLAUDE.md` anywhere | Orchestrator-managed |

### 13.3 Test plan — CODE phase versus TEST phase

**CODE phase, all platform-neutral and runnable on Linux:**

1. The rendered mount source equals the expected string for a given
   `drive_mount_root`, distro and stage path. This is the regression test the
   #84 ruling asks for, and it must assert the **full** source string, not just
   that it starts with the UNC prefix.
2. A profile missing `drive_mount_root` is refused, and a non-absolute or
   trailing-slash value is refused.
3. `reconcile` with `publication=None` on an `ARTIFACTS_VERIFIED` record
   returns the `PUBLICATION_COMPOSITION_ABSENT` directive, writes nothing, and
   does not report a submitted run.
4. The existing suites still pass against the stable Linux baseline of **12
   failed, 11 skipped** in three known families (Windows drive path, absolute
   Windows docker executable, locked Git object). Assert the failures by
   **cause**, not by a pass total: the pass count rises whenever tests are
   added, so pinning it is a rotting assertion.

**TEST phase, on the Windows host only:**

5. The prerequisites and early assertions A1-A4 (sections 9.1, 10.1).
6. The mount-source bind probe (B-1 residual), before the first real run.
7. The command sequence and phase transitions (section 9.2).
8. The acceptance surface (section 10.2), or, if B-2 is confirmed,
   `trainer.stderr.log` read and the failure attributed to
   `Trainers/sft/runtime_v1.py:1811` rather than to the platform.

Two standing traps for whoever runs the suites: use **explicit test file
paths, never a directory glob**, because the rtk proxy reports "No tests
collected" for globs and reformats output; and use an explicit 3.11+
interpreter, because `test_docker_training.py` cannot be collected under 3.10.

---

## 14. Where I overrule PREPARE, and where the docs disagree

| # | PREPARE said | This document rules | Evidence |
|---|---|---|---|
| 1 | D3 is a real choice between CPU and GPU | GPU; the CPU branch does not exist | `Trainers/sft/train_sft.py:137`, `:1159`; `configs/config.yaml:66`, `:68` |
| 2 | Put mount sources and artifact roots on distro ext4 under `/home/profsynapse` | Impossible; the project root must be a Windows drive path and everything is derived from it | `docker_v1/prepared.py:46-47`; `local_io_v1/config.py:113-119`, `:171-177` |
| 3 | Mount sources render as `\\wsl.localhost\Ubuntu-22.04\...` | They render with the **committed** distro, which is `docker-desktop` | `training/providers/docker.json:37-40`; `docker_training.py:881` |
| 4 | D7: reconcile at least twice | At least three post-submit cuts; the observe cut is separate and may repeat | `docker_execution.py:1190-1218`, `:1160`, `:1137` |
| 5 | Assert M-8/A-2 positively in the run | Only the `SUBMITTED` half is assertable there; the directive branch is race-only and belongs in a unit test | `docker_training.py:927-949`; `docker_execution.py:1137-1159`, directive returned at `:1157-1159` |
| 6 | D4 may need a new committed config | The existing smoke is already a valid ref; add nothing | `cli.py:512-537`, `:26`; `training/smokes/docker-sft.json` |
| 7 | D6 might want an isolated storage root | Not needed; all four roots exist and a non-project root must be contained under the project anyway | `training/storage.json:22-45`; `config.py:171-177` |
| 8 | `--name` collision avoidance is a design concern | It is derived from a digest and cannot collide | engine `docker_provider_v1/model.py:588-589` |

The prior architecture document says nothing about the WSL distro or the mount
source at all. I checked. That is why B-1 survived a full design, a full
implementation and a review: **no document ever claimed the mount source was
correct, so nothing was ever wrong to be caught.**

---

## 15. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | B-2 is real and the run stops before verification | High | Section 7. Probe first; escalated as task #85 |
| R2 | The engine cannot bind `/mnt/host/f` either | High | Section 6.3 makes the alternative a config value, not a second code change; probed before the first real run |
| R3 | The driver-band mismatch makes the toolkit reject `--gpus` | Medium | Assertion A1 surfaces it with its true cause |
| R4 | `/artifacts` is not writable by the non-root container user | Medium | Assertion A2, before the long wait |
| R5 | The image's Python is not exactly `3.11.14` | Medium | Assertion A3; the check is a full patch-level equality and refuses otherwise |
| R6 | The materialized inventory carries symlinks and is rejected | Low | `copyfile` dereferences; verified before the run |
| R7 | Reading `published == False` after one cut is misread as failure | Low but historically the most likely | Section 9.3 states the count concretely |
| R8 | The new profile field changes the plan fingerprint, so an earlier durable row is not resumed | Low | Stated in section 6.4; expected, not a defect |

---

## 16. Citation drift found while verifying

Recorded rather than silently reconciled, because these are the numbers CODE
and TEST will follow.

1. **The reconcile directive moved.** PREPARE cites the
   `PUBLICATION_COMPOSITION_ABSENT` return at
   `docker_execution.py:1153-1155`. At head it is `:1157-1159`, inside the
   branch opening at `:1137`. PREPARE's own citations were taken at the same
   head, so this is a drift within PREPARE, not against it. Every other
   `docker_execution.py` number I re-derived matched: `:1137`, `:1164`,
   `:1201`, `:1217`.
2. **The executable-discovery block is wider than cited.** PREPARE cites
   `docker_prepared_composition.py:107-121`; the block genuinely opens at
   `:103`.
3. **Everything in `docker_provider.py` matched exactly**: `:93`, `:122`,
   `:158`, `:183`, `:222`.

No disagreement of substance was found between PREPARE and the code. The two
substantive gaps this document adds — B-1 and B-2 — are gaps in **coverage**,
not contradictions: PREPARE never examined the committed `wsl_distro` value,
and never read the trainer body.

---

## 17. Amendment 2026-09-02 — ruling on B-4 (the prepared composition passes no `--entrypoint`)

Raised by `test-host` on the first host run (blocker #97; test report section 5).
This section is the design ruling. It supersedes nothing above; sections 1-16
never considered the image's `ENTRYPOINT`, which is the gap.

### 17.1 The measured defect

The committed image has `Entrypoint=["/usr/local/bin/entrypoint.sh"]` and
`Cmd=null`, and that script ends in `exec /usr/bin/supervisord` without ever
running `exec "$@"`. The prepared composition appends the locked closure argv
as **CMD** (`control_private.py:412-413`) and passes no `--entrypoint`, so the
argv is discarded and the container starts jupyter, ollama and sshd instead of
the trainer. Measured, not inferred: `test-host` ran the image with a command
appended and watched supervisord take over.

### 17.2 Ruling: option C — a fixed passthrough entrypoint, CMD unchanged

**Set `--entrypoint env` on the prepared create command and leave the workload
argv as the whole CMD.**

`env` with no `NAME=VALUE` operands is the POSIX identity: it `exec`s its
argument vector unchanged, replacing itself, so the container's main process
becomes exactly `worker.interpreter` running the locked entrypoint script. The
executed argv is byte-identical to the argv the closure equality check pins at
`docker_staging.py:1555-1567`, and `Config.Cmd` still holds that argv in full.

I recommend this over both offered options, and the reason is not taste — the
other two are closed by code.

### 17.3 Why option A as framed is closed

Option A (Host passes the interpreter as the entrypoint, remaining argv as CMD)
**breaks the create verification**. Two digests are computed over different
things and then compared:

| Site | Digested over |
|---|---|
| `create.py:405-406` | `workload.arguments` — the **full** locked argv |
| `cli.py:429`, `:494-495` | `config.get("Cmd")` from `docker inspect` — **CMD only** |

`verification.py:30-31` requires `projection.argument_count ==
specification.argument_count` and the two digests equal. Today they match
because CMD *is* the whole argv. Move `argv[0]` into `--entrypoint` and CMD
becomes `argv[1:]`, so the count differs by one and the digests differ. The
create cut would fail verification on every run.

Making it work would mean editing `create.py:405-406` to digest `arguments[1:]`
and `cli.py:196` to match — which removes `argv[0]`, the interpreter, from the
only thing that pins the executed command. That trades a working trainer for a
weaker pin. Refused.

**The empty reset `--entrypoint ""` is also closed**, and this one is absolute:
`_argv_token_v1` (`model.py:1021-1032`) rejects any empty argv token, so an
empty string cannot exist inside a `DockerCLICommandV1`. Allowing it would mean
weakening a validator that also bans control characters and non-NFC text. Not a
trade worth making, and not one this feature is authorized to make.

### 17.4 Why option B is closed

Option B (require an image whose entrypoint `exec "$@"`) contradicts the
committed digest pin at `training/providers/docker.json:5`. It needs a rebuilt
and re-pinned image, and it relocates a Host contract into a property of an
image that **nothing on this path verifies** — no code reads
`Config.Entrypoint`. A silent regression in a future image would resurface this
same blocker with no signal. The Host, not the image, must guarantee that the
locked argv runs.

### 17.5 Constant, not a profile field — and why this differs from B-1

B-1 became `docker_host.drive_mount_root` because measurement produced two
genuinely competing candidates and the design could not pick between them; a
config value let TEST choose without a second code change. **That reasoning does
not transfer here.** There is one correct behaviour — run the locked argv with
no image wrapper — and `env` expresses it on any POSIX image. Making it
configurable would buy nothing and cost the exactness below.

Define it once:

```python
_CONTAINER_ENTRYPOINT_V1 = "env"
```

in `control_private.py`, imported by `cli.py`. A constant lets the create-argv
parser assert the **exact** token, matching how `--network none`, `--gpus` and
the owned labels are already treated. A profile field would force either a
shape-only check or a new parameter on the `create_container` Protocol
(`ports.py:266`, `cli.py:815`, `control_private.py:189`) — four sites and their
tests, to make a universal constant look local.

### 17.6 Insertion point

Both edits go in the **fixed** region, after the `--memory` pair and before the
optional `--gpus` branch, so the parser stays straight-line and `--gpus` remains
the only conditional.

**Compose** — `control_private.py:391-394`, extend the list literal so it ends:

```python
"--memory", str(runtime.memory_bytes),
"--entrypoint", _CONTAINER_ENTRYPOINT_V1,
```

**Validate** — `cli.py`, insert between the memory block and line 115:

```python
if arguments[index:index + 2] != ("--entrypoint", _CONTAINER_ENTRYPOINT_V1):
    raise ValueError
index += 2
```

**Guard the `env` operand rule** — `env` treats a leading `NAME=VALUE` token as
an assignment rather than a program. The locked argv always begins with
`worker.interpreter`, but that is an invariant to assert, not assume. In
`control_private.py`, inside the existing type gate at `:330-340`:

```python
if "=" in workload.arguments[0] or workload.arguments[0].startswith("-"):
    raise ValueError
```

`DockerWorkloadV1.__post_init__` already guarantees `arguments` is non-empty, so
the index is safe.

### 17.7 Effect on the fingerprint and the durable row

- **Closure argv equality (`docker_staging.py:1533-1588`): untouched.** It
  compares `bundle.dispatch.argv`, a staging-side value. Nothing there changes.
- **`DockerCreateSpecificationV1`: untouched.** `argument_count` and
  `arguments_digest` are over `workload.arguments`, which is unchanged.
- **`command_digest`: changes**, because the create argv gains two tokens. This
  is self-consistent — the composition, the parser, the label projection and the
  `docker_run_mutations` row all derive from the same command — and it is the
  intended signal that the command changed.
- **Plan fingerprint: unchanged.** It is built from the plan and source lock,
  not the CLI argv.

### 17.8 Files a coder touches

| File | Change |
|---|---|
| `synaptic_host/docker_v1/control_private.py` | `_CONTAINER_ENTRYPOINT_V1` constant; two tokens at `:391-394`; `argv[0]` guard in the gate at `:330-340` |
| `synaptic_host/docker_v1/cli.py` | import the constant; exact two-token check inserted before `:115` |

Two production files. **No** engine file, no `composition.py`, no
`DockerHostCreateV1` constructor, no Protocol change, no profile field, no
schema or durable-row change.

**Must not be touched:** `synaptic-tuner/` (pin `aec998ee`);
`docker_staging.py:1533-1588`; `create.py:405-406`; `cli.py:429`, `:494-495`;
`verification.py:30-31`; `model.py:1021-1032`; `docker_v1/composition.py`;
`training/providers/docker.json`.

### 17.9 Tests

**CODE phase**, added to `tests/synaptic_host/docker_v1/`:

1. `test_control_contract.py` — the composed create argv contains
   `("--entrypoint", "env")` immediately after the `--memory` pair, on both the
   GPU and non-GPU branches.
2. `test_control_contract.py` — CMD is still the complete workload argv:
   `arguments[image_index + 1:] == workload.arguments`. This is the regression
   guard for 17.3; it fails if anyone later moves `argv[0]` into the entrypoint.
3. `test_cli.py` — `_validate_create_command` rejects a command with the
   entrypoint pair absent, with a different value, and in the wrong position.
4. `test_control_contract.py` — a workload whose `arguments[0]` contains `=` or
   starts with `-` is refused (17.6).
5. `test_create.py` — `DockerCreateSpecificationV1.argument_count` is unchanged
   by the amendment, pinning that verification still matches.

Existing `test_cli.py` create-command fixtures (`:820`, `:830`, `:837`, `:865`,
`:886`, `:984`) construct create argv and **will fail** until the pair is added
to the fixture builder. That is expected, and updating them is in scope.

**TEST phase**: one probe before the first real run, since I could not run
docker and the image's `env` was never observed:

```
docker.exe --host <npipe> run --rm --pull never --network none \
  --entrypoint env <image@sha256:…> /opt/conda/bin/python3 -c "print('ok')"
```

Expected `ok`. If `env` is absent, the single-token fallback is `/usr/bin/env`;
if the flag itself misbehaves, stop and report rather than improvising.

### 17.10 The driver's A1-A3 probes

`_assert_a1_gpu` (`run_prepared_training.py:329-333`),
`_assert_a2_artifacts_writable` (`:353-360`) and `_assert_a3_python_version`
(`:378-382`) all append a command to the profile image with no entrypoint
override, so each would start supervisord and time out at 300 s, reporting
`T1-timeout` for three assertions whose purpose is to name a true cause.

Add `"--entrypoint", "env"` to all three `_run` argv lists, immediately before
the image reference. The driver must import or restate the same token the
composition uses so the probes assert the same contract; a comment naming
`control_private._CONTAINER_ENTRYPOINT_V1` is sufficient, since the driver is a
checked-in script outside the package. The bind probe is unaffected because it
uses `python:3.12-slim`. Edit the canonical copy under `.skills/` and re-sync
mirrors with `bin/sync_skills.py`; never hand-edit a mirror.

### 17.11 Residual: the observed entrypoint is unverified

`cli.py:429` reads `Config.Cmd` only. Nothing reads `Config.Entrypoint` back
from `docker inspect`, so after this amendment the create argv is pinned by the
parser and `command_digest`, but the entrypoint the daemon actually applied is
**not** compared against what was requested. A daemon that silently ignored the
flag would present as B-4 again.

Closing it means adding an `entrypoint_digest` to
`DockerCreateSpecificationV1`, the inspect projection and
`verification.py` — a durable-record schema change, which is larger than this
blocker and outside what the constraints authorize here. I am **naming it, not
deferring it silently**: it is a decision for the lead and the user, and the
17.9 probe plus the trainer actually producing output is the interim evidence
that the flag took effect.

---

## 18. Amendment 2026-09-02 — ruling on B-9 (the container user cannot write the artifact bind)

**Blocker** #128, raised by `test-host` on run 4 (#127; report
`docs/testing/prepared-path-alpine-diagnostic.md` section 15.4).
**Baseline for every citation below**: Host worktree at `7546169e`, submodule
`synaptic-tuner` at `4a01fc55`. Line numbers are read at that commit; re-verify
against `git show 7546169e:<path>` rather than a working tree that coders are
editing.

**User ruling 2026-09-02 (option A)**: the machine's `/etc/wsl.conf` stays as it
is. Acceptance evidence must come from an unmodified host, so the prepared path
must stop depending on undeclared mount policy. Remedy 1 (host-wide automount
edit) and remedy 2 (a different distro) are **rejected** and are not reopened
here. This section rules on remedy 3 and specifies the P8 precondition.

### 18.1 The measured defect, and what it is not

The prepared composition passes **no `--user`**
(`control_private.py:394-399`), so the container runs as the image's own
`User=unsloth:runtimeusers` (uid 1001, gid 102) and binds `/artifacts`
read-write over `\\wsl.localhost\Ubuntu-22.04\mnt\f\...`
(`control_private.py:410-411`). The pinned distro mounts the project drive with
`metadata;uid=1000;gid=1000;umask=22;fmask=11`, so DrvFs honours stored POSIX
modes; a directory with no stored mode presents as `0755` owned by uid 1000 and
uid 1001 gets `r-x`.

`test-host` isolated it single-variable — same image, same bind shape, same
default user, only the host-side mode differing: `755` denies, `777` writes —
and controlled it against run 2's own probe directory, which now fails
identically. So this is **not** a regression of the new checkout, not a Host
source defect of the B-7 kind, and not an in-checkout operator step of the B-6
kind. It is an undeclared **environment precondition**.

One part of the run-4 account is inference and is treated as such: that runs 1-3
mounted the drive without `metadata`. The earlier mount cannot now be observed.
**Nothing in this ruling depends on it.** The design below is justified from two
things that are still measurable: the current mount options, and the composition
source.

### 18.2 The principle — match the mount's OWNER, do not fight its MODE

The mount presents two separable facts: an **owner identity** (`uid=`, `gid=`)
and a **mode policy** (`metadata`, `umask=`, `fmask=`). B-9 is a mode-policy
failure, and every remedy that attacks the mode has to reach a surface the Host
is not allowed to use. The owner identity is different: it is a mount option,
it is stable for the life of the mount, and **the owner of a directory has
`rwx` under every mode policy the mount can present** — `umask=22` gives `755`,
`umask=77` gives `700`, and a no-`metadata` mount gives `0777`. Owner-matching
is therefore correct in the current environment, correct in the earlier
environment run 4 could not reproduce, and correct under any umask a future boot
might apply.

That is the ruling in one line: **the prepared path stops depending on the
mount's mode policy by declaring, and adopting, the mount's owner identity.**

### 18.3 Ruling — candidate (a), `--user` from a committed profile field

The prepared composition emits `--user <uid>:<gid>`, sourced from a new
committed profile field `docker_host.container_user` in
`training/providers/docker.json`, and the create-argv parser asserts its shape
at a fixed position. For this host the value is `"1000:1000"`, which is the
`uid=`/`gid=` pair the report measured in `/proc/mounts` (section 15.4).

Why this and not something cleverer:

- It is the **only lever inside the composition**. Docker's `--mount type=bind`
  has no uid-remap option on the Docker Desktop WSL2 backend, and group
  matching cannot help: the directory presents `755`, so the group has no write
  bit either.
- It is **policy-independent** (18.2), which is exactly what the user's
  ruling requires: the design must not assume anything about `wsl.conf`.
- It **declares** the host fact instead of assuming it. B-9 exists because the
  prepared path had an unwritten requirement. A profile field converts the
  unwritten requirement into a committed, auditable, operator-settable value,
  and P8 fails by name when the value is wrong.
- It is **secret-free**. The value is two integers. It appears in the prepared
  command text and in the durable `command_digest` input, and carries no
  credential.

**Cost in the committed profile.** `docker_host` gains one key. The profile is
read as a committed git blob at the locked project commit, so the value only
takes effect once committed **and a new released checkout is built** — the same
mechanism that governed B-1' (task #100). `profile.digest` changes, and it
already flows into `provider_runtime_requirements_digest` and
`provider_policy_digest` (`docker_training.py:484`, `:508`); both are computed
from the profile, so no committed constant needs updating, only tests that pin
the digest or the profile's key set.

**Cost in the closure manifest: none, confirmed.**
`tuner/runtime/manifests/offline-sft-worker-v1.json` is loaded from the engine
submodule at the locked engine commit (`docker_staging.py:1678-1680`) and its
members are engine source files; the Host recomputes and compares them. No Host
file is a member, so no Host-side change can invalidate it. The B-5 regeneration
ruling (#117) is not reopened.

**Cost in the prepared command text.** Two extra argv elements. The locked
workload argv is appended unchanged after the image reference
(`control_private.py:416-417`) and is not touched.

### 18.4 Why candidate (b) is closed — the Host cannot set the presented mode

Candidate (b) was: have the Host create the stage directory group- or
world-writable. It is refused because no surface the Host is permitted to use
can set the mode DrvFs presents.

- **Windows Host Python cannot.** `os.chmod` on Windows toggles only the
  read-only attribute; it does not write the Linux mode. The staging code
  already knows this and says so in its own shape: `_apply_file_mode` branches
  on `os.name == "nt"` and sets `stat.S_IREAD` instead of a POSIX mode
  (`docker_staging.py:161-165`), and `_verify_file_mode` returns `True`
  unconditionally on Windows (`:168-174`). A design that assumed Windows Python
  could stamp `0777` would contradict code already written on the premise that
  it cannot.
- **The WSL side could, and is out of bounds.** With `metadata`, a WSL-side
  `chmod` writes the stored mode, which is why `test-host`'s 777 experiment
  worked. The standing constraint is that WSL is used only for mount
  translation, and the team lead confirmed that reading on 2026-09-02. Calling
  `wsl.exe ... chmod` from the staging path would breach it, and would make
  every run depend on a second interpreter on the host.
- **A privileged preparation container could, and is worse.** A root container
  chmod-ing the bind would add a Docker step to a function whose contract is
  explicitly "without Docker or network I/O" (`docker_staging.py:1658`), and
  would introduce a privileged container into a path whose whole point is a
  network-disabled, credential-free, non-root workload.
- **NTFS ACLs do not reach it.** When no stored mode exists, DrvFs derives the
  presented mode from the mount's `umask`/`fmask`, not from the ACL. This is
  consistent with the measurement that creator does not matter: a WSL `mkdir`
  and a Windows Python `mkdir` present identically.

### 18.5 Why candidate (c) is closed — named volume, tmpfs, or a relocated stage

Rejected on two independent grounds.

- **The staging invariant forbids it.** The stage root must live below the Host
  state root, which must live below `<project>/.synaptic`
  (`docker_staging.py:1681-1685`, which raises "Docker staging must remain
  below Host state"). The project is on the F: drive, so the stage cannot be
  moved off DrvFs without changing where Host state lives — a far larger change
  than the blocker.
- **It would be the compatibility layer the user forbade.** A named volume or
  tmpfs for `/artifacts` plus a post-run copy inserts a second artifact
  location, a copy step, and a new failure mode between the trainer's output and
  the verifier's content-bound contract. It also breaks the identity the
  verifier depends on: the Host verifies artifacts by reading the same directory
  it bound. This is exactly the "untouched prepared path" the feature exists to
  exercise.

### 18.6 Candidate (d) — nothing in the code already provides it

Checked, not assumed. There is **no** user, uid, or run-as support anywhere in
the Host: a search for `--user`, `"user"`, `user_id`, `uid` and `run_as` across
`synaptic_host/` returns nothing, and the same search across the engine's
`tuner/execution/providers/docker_provider_v1/` returns nothing. `DockerRuntimeV1`
carries cpu, memory, timeout, accelerator devices and network mode only
(`control_private.py:353-361`). Candidate (d) is empty; the field has to be
added.

### 18.7 Profile field, not a constant — and why this differs from B-4

Section 17.5 ruled the entrypoint a **constant** because there was one correct
behaviour that `env` expresses on any POSIX image. That test is applied here and
comes out the other way. There is no universally correct uid: the right value is
whatever identity the pinned distro presents as owner of the project drive, and
that is a property of the host, not of the design. This is B-1-shaped, not
B-4-shaped, and it takes the B-1 answer — a `docker_host` field beside
`wsl_distro` and `drive_mount_root`, which already declare *where* the drive
appears. `container_user` declares *who owns it there*.

Section 17.5's objection to a profile field — that it would force a new
parameter on the `create_container` Protocol across four sites — does not apply,
because the value never reaches `create_container`. It reaches the argv builder
only, by the construction route in 18.8.

### 18.8 Insertion points

**(1) Compose** — `control_private.py`, in the fixed region after the
`--entrypoint` pair and before the optional `--gpus` branch, so `--gpus` remains
the only conditional (the rule 17.6 established). The list literal at `:394-399`
ends:

```python
"--entrypoint", _CONTAINER_ENTRYPOINT_V1,
"--user", container_user,
```

`container_user` is a new keyword-only parameter on
`DockerPrivateCreateInvocationFactoryV1.build` (`:323-327`), validated inside
the existing type gate at `:329-346` against the grammar in 18.8(3).

**(2) Validate** — `docker_v1/cli.py`, in `_validate_create_command`, inserted
immediately after the entrypoint block at `:116-118`:

```python
if arguments[index:index + 1] != ("--user",):
    raise ValueError
index += 1
user = arguments[index]
index += 1
if _CONTAINER_USER_V1.fullmatch(user) is None:
    raise ValueError
```

The parser asserts the **shape**, not the value. That matches how the parser
already treats `--cpus` and `--memory` — bounded digit strings, checked for form
(`cli.py:99-115`) — while reserving exact-token equality for universal constants
such as `--network none` and `--entrypoint env`. A profile-derived value cannot
be value-pinned in a parser that has no access to the profile.

**(3) The grammar.** Numeric only:

```python
_CONTAINER_USER_V1 = re.compile(r"(?:0|[1-9][0-9]{0,6}):(?:0|[1-9][0-9]{0,6})\Z")
```

Names are refused deliberately. A name in `--user` resolves against the
**image's** `/etc/passwd`, which cannot express a host mount identity; only
numeric ids cross that boundary with their meaning intact.

**(4) Thread the value by construction, not by call.**
`container_user` becomes a **required keyword-only field on
`DockerHostCreateV1`** (`docker_v1/create.py`), read by both `prepare_admission`
and `create_once` when they call `build`.

This is the load-bearing implementation decision, and the reason is
correctness, not tidiness. The value is consumed at **three** call sites —
`docker_prepared_composition.py:242-249` (admission) and
`docker_execution.py:1086-1092` and `:1122-1128` (create and reconcile-create) —
and admission publishes an expected-create binding that `create_once` compares
against its own preflight (`create.py:191-199`). If the three sites could be
given different values, a mismatch would surface as an opaque admission
rejection. Binding the value once on the object makes divergence impossible by
construction, and leaves all three call signatures unchanged.

The two production construction sites are
`docker_prepared_composition.py:231-241` (in scope; pass
`container_user=platform.container_user` beside the existing
`endpoint_descriptor_digest` and `cli_policy_digest`, which are already
platform-derived constructor values) and `docker_v1/composition.py:382-396`
(the legacy path). **The field takes no default.** A default would let the
legacy path silently compose a create command with a different user than the
prepared path — the silent-divergence class this workstream was already bitten
by in B-4. The legacy site is kept constructible by adding the field to its
request dataclass (near `composition.py:151`) and passing it through: two lines,
no fallback, and the prepared path is not routed through it.

**(5) Carry it to the platform and the profile.**

- `docker_prepared_composition.py:55-77`: `DockerPreparedPlatformV1` gains
  `container_user: str` with the same shape validation, beside `distro` and
  `drive_mount_root`.
- `docker_prepared_composition.py:88-106`:
  `compose_docker_prepared_platform_v1` gains a `container_user` keyword and
  validates it in the same guard.
- `docker_training.py:881-882`: pass `container_user=snapshot.profile.container_user`
  beside the two existing fields.
- `docker_provider.py`: field at `:136-137`, validation at `:166-167`, the key
  set at `:202-203` (a `frozenset` — an unlisted key is rejected, so the parser
  must be extended or the new profile will not load), construction at
  `:227-229`, and `to_dict` at `:266-269`.

**(6) The stage directory itself is not changed.** `_create_artifact_topology`
(`docker_staging.py:1438-1443`) and the `mkdtemp`/`mkdir` sequence at
`:1687-1698` stay exactly as they are. That is the point of the ruling: the
Host keeps creating the stage the only way it can, and the container is told who
to be.

### 18.9 Effect on the closure, the fingerprint and the durable row

- **Closure argv equality (`docker_staging.py:1533-1588`): untouched.** It
  compares `bundle.dispatch.argv` — interpreter, entrypoint and the
  canonical-workload flags — against a value rebuilt from the locked closure
  (`:1552-1580`). Docker flags are not in that comparison.
- **Worker closure manifest: untouched**, per 18.3.
- **`command_digest` and the `docker_run_mutations` row: changed by value, not
  by shape.** The create argv gains two elements, so its digest changes. That is
  the same effect B-4 had and needs no schema change. A run started before this
  amendment and reconciled after it would see a digest mismatch; there is no such
  run, because no run has ever reached create (`.synaptic\state` has never
  existed — report sections 13.6 and 15.6).
- **`DockerCreateSpecificationV1` (`create.py:400-410`)**: the specification
  already carries a `working_directory_digest`. A `container_user_digest`
  alongside it is **ruled out** (lead ruling on open question 2, 2026-09-02):
  `command_digest` already covers the value, so `DockerCreateSpecificationV1`
  gains no new field. A coder who adds one has left the ruling.

### 18.10 The writable-`HOME` question is engine-side and is NOT ruled here

Changing the container's uid raises a second question that must be named rather
than assumed away: `--user 1000:1000` is an id with no entry in the image's
`/etc/passwd`, so the runtime sets `HOME=/`, which uid 1000 cannot write. Some
of the trainer's dependencies write under `Path.home()`.

Most of the risk is already retired by the design as it stands. Every writable
root is redirected under `/artifacts` (`docker_training.py:444-449`,
`writable_capability_root="/artifacts"` at `:474`), and `HF_HOME` and
`TRANSFORMERS_CACHE` are explicitly redirected into `/artifacts/cache`
(`:461-462`). `PYTHONNOUSERSITE=1` is set (`:452`).

What remains cannot be fixed on the Host, and I am naming that rather than
recommending a Host edit that would be rejected at runtime. The engine declares
an environment allowlist at
`synaptic-tuner/tuner/training/methods/sft.py:52-63`, and it **does not contain
`HOME` or `TMPDIR`**. The allowlist is enforced, not decorative:
`Trainers/sft/runtime_v1.py:1145-1157` requires
`set(planned_environment).issubset(set(allowed_environment))` and raises
`RuntimeV1Error("resolved runtime environment violates portable requirements")`
otherwise. So adding `HOME` to the Host's environment dict would be **rejected
by the engine**. Doing it properly means an engine allowlist change, a new
engine commit, and — if that file is a closure member — a closure regeneration
of the B-5 shape. That is a rePACT, not a line in this ruling.

Two things follow, and both are in scope for me to specify:

1. **P8 measures it and reports it, and does not fail on it** (18.11). Whether
   the workload needs a writable `HOME` is unproven; a non-writable `HOME` is
   legitimate today, so the correct severity is a warning, not an error.
2. It goes on the deferred ledger as **B-9-R1** (18.16), to be settled by run 5's
   own output rather than by argument.

Note also that the offline flags the engine requires
(`runtime_v1.py:669-670`) are supplied by the engine's own dispatch layer
(`tuner/runtime/dispatch.py:169-186` sets `HF_HUB_OFFLINE` and
`TRANSFORMERS_OFFLINE` to `"1"`), not by the Host's environment dict. Their
absence from `docker_training.py:450-464` is not a defect; I checked before
filing one.

### 18.11 P8 — `P8-stage-writable-as-container-user`

**What it proves.** That the effective container user the composition will use
can create, write and delete inside a bind whose source is created the same way,
and in the same place, as the real stage directory.

**Where the probe directory goes.** Under the real stage parent:
`<released checkout>\.synaptic\state\docker\stages\p8-probe`, created by the
driver with Python's `mkdir(parents=True, exist_ok=True)` — the identical call
the staging code makes at `docker_staging.py:1686`. This is deliberate and
answers the fidelity requirement directly. The presented mode of a fresh
directory comes from the mount policy, not from its creator, so a scratch
throwaway would in fact be equivalent **on this host** — but that equivalence is
an inference from one measurement, and the stage root is the location that
actually matters. Probing the real parent removes the inference.

Two consequences the operator must know, and the driver must print:

- A `--probe-only` pass now creates `.synaptic\state\docker\stages` if it does
  not exist. That is the same directory the run creates anyway, by the same
  idempotent call, but it changes the "no durable state was written" line that
  runs 1-4 could report. The driver prints one line saying it created the stage
  parent.
- P8 removes **only** its own `p8-probe` directory and the file inside it. It
  never removes the stage parent, and it never touches an existing stage.
  It must also never write inside a stage: `_verify_artifact_topology`
  (`docker_staging.py:1446-1481`) requires the four writable artifact
  directories to be empty, so a stray probe file inside a stage would break
  stage reuse.

**How it writes as the image's own user.** One container run, using the same
two conventions the composition uses — `--entrypoint env` (section 17.2, so the
image's `entrypoint.sh` cannot discard the argv) and the `--user` value read
from `docker_host.container_user`:

```
docker.exe --host npipe:////./pipe/dockerDesktopLinuxEngine run --rm \
  --pull never --network none \
  --user <docker_host.container_user> \
  --mount type=bind,source=<rendered UNC of the p8-probe directory>,destination=/artifacts \
  --entrypoint env <image@sha256:...> \
  sh -c 'id; touch /artifacts/.p8probe && rm /artifacts/.p8probe && echo WRITABLE; \
         printf "HOME=%s " "$HOME"; test -w "$HOME" && echo home-writable || echo home-not-writable'
```

The UNC is rendered by the driver's existing `_mount_source`
(`run_prepared_training.py:410-412`), so P8 and the composition agree on the
mount source by construction.

**Pass condition.** `WRITABLE` in stdout and exit 0. The `id` line is echoed
into the report so the effective user is evidence, not assumption.

**Warning, not failure.** `home-not-writable` prints a `WARN P8-home` line
naming B-9-R1 and continues. A non-writable `HOME` is legitimate for a workload
that never touches it; failing on it would refuse valid configurations.

**Failure message.** It must name the effective user, the rendered UNC, the
child's stderr, and — this is the part that makes it a precondition rather than
a symptom — the remedy:

```
FAILED P8-stage-writable-as-container-user: <user> could not write /artifacts over
  <UNC>: <stderr>
  The prepared path requires docker_host.container_user to equal the identity the
  pinned WSL distro presents as owner of the project drive. Read it with:
    wsl.exe -d <distro> -- awk '$2=="<drive_mount_root>/<letter>"{print $4}' /proc/mounts
  and set docker_host.container_user in training/providers/docker.json to that
  uid:gid, then commit and rebuild the released checkout. This is blocker B-9.
```

**Position.** After P7 and after the B1 bind probe; before A1. P8 cannot precede
B1, because it needs a bind that is already proven to resolve — otherwise a
mount-source fault would surface as a permission message. It precedes every
assertion because a non-writable stage makes the rest of the run moot. Final
order: `P1..P7` → `B1` → `P8` → `A1` → `A2` → `A3` → `A4`.

**Relation to A2.** A2 stays exactly where it is, as the last-line check, and is
amended only in 18.12. The two are not redundant: P8 probes the **stage root**
and names the **cause and the remedy**; A2 probes a scratch directory and has
continuity across runs 1-4. The overlap costs one short container run and buys
a named precondition, which is the hardening P7 gave B-6.

**Skill text.** P8 becomes prerequisite **9** in
`.skills/host-docker-run/SKILL.md`, written in the style of prerequisite 7
(`SKILL.md:61-75`): a short statement of the requirement, the copy-pasteable
command, the expected output, and what to do when it fails.

### 18.12 The driver's A2 must follow the composition

A2 currently hardcodes `--user unsloth:runtimeusers`
(`run_prepared_training.py:489`). Today that is faithful by coincidence: the
composition passes no `--user`, so the container runs as the image's default,
which is that name. **After this amendment it becomes wrong**, and would fail a
run that the composition would have completed — a false blocker.

A2 must read `docker_host.container_user` from the same profile the composition
reads and pass that. This is the same principle 17.10 applied to the entrypoint:
the probes assert the same contract the composition uses. Its pass line changes
to name the effective user it actually used, rather than the literal
`unsloth:runtimeusers` (`:501`).

### 18.13 Declaring the environment precondition in words

**Ruled: the skill must declare it; the profile carries the field and nothing
more.**

After the fix the requirement is no longer "the mount must be world-writable",
which was a policy the prepared path could not state and could not check. It is
"`docker_host.container_user` must equal the identity the pinned distro presents
as owner of the project drive" — a configuration requirement, expressed by a
named field and enforced by P8.

- **The skill declares it in prose**, in prerequisite 9, because an operator
  bringing up a new host needs to know how to determine the value. The
  `/proc/mounts` command in the P8 failure message is the procedure and belongs
  in the skill text too.
- **The profile does not gain prose.** JSON carries no comments, and a field
  named `container_user` sitting beside `wsl_distro` and `drive_mount_root`
  already reads as what it is. Adding a parallel description key would create a
  second place for the requirement to go stale.
- **The report and this section carry the history**, so the next reader learns
  why the field exists rather than only that it does.

### 18.14 Files each coder touches

**Host coder (composition and profile)** — all paths relative to the Host
worktree:

| File | Change |
|---|---|
| `training/providers/docker.json` | add `docker_host.container_user: "1000:1000"`; touch nothing else, preserve key order |
| `synaptic_host/docker_provider.py` | field `:136-137`, validation `:166-167`, key set `:202-203`, construction `:227-229`, `to_dict` `:266-269` |
| `synaptic_host/docker_training.py` | pass `container_user=` at `:881-882` |
| `synaptic_host/docker_prepared_composition.py` | platform field and guard `:55-77`, factory keyword and guard `:88-106`, constructor argument `:231-241` |
| `synaptic_host/docker_v1/create.py` | required keyword-only constructor field; pass to `build` at `:393-398` |
| `synaptic_host/docker_v1/control_private.py` | `build` keyword and guard `:323-346`; argv emission after `:398` |
| `synaptic_host/docker_v1/cli.py` | `_CONTAINER_USER_V1`; parser block after `:116-118` |
| `synaptic_host/docker_v1/composition.py` | legacy request field near `:151` and pass-through at `:382-396`, so the legacy site stays constructible; no fallback, no routing change |

**`coder-workflow` (skill and driver)**:

| File | Change |
|---|---|
| `.skills/host-docker-run/scripts/run_prepared_training.py` | `_check_p8_stage_writable`, called after the B1 bind probe and before A1; A2 reads `docker_host.container_user` (`:474-501`) |
| `.skills/host-docker-run/SKILL.md` | prerequisite 9 (P8) in the style of item 7; amend the A2 line under "Early assertions" |
| mirrors | `python3 bin/sync_skills.py --write --skill host-docker-run`, then `--check --skill host-docker-run`; never hand-edit a mirror |

The two lanes do not collide: no file appears in both lists. They share one
contract — the profile key name `docker_host.container_user` — which is fixed by
this section.

**Files that must NOT be touched**: `synaptic-tuner/` in any form (the engine pin
does not move for this ruling), `tuner/runtime/manifests/offline-sft-worker-v1.json`,
`docker_staging.py`'s stage creation and topology verification, the closure argv
equality check, the artifact verifier, the publication composition and the
destination registry, and any `CLAUDE.md`.

### 18.15 Tests

Host-side, added beside the tests that already pin the create argv:

1. **Composition** — the create argv contains `("--user", "<profile value>")`
   immediately after the `--entrypoint` pair and before any `--gpus`.
2. **Parser** — `_validate_create_command` rejects a missing `--user`, a
   `--user` in the wrong position, a name-form value, an empty value, and an
   out-of-range value; and accepts the committed shape.
3. **No divergence** — admission and create compose byte-identical argv for the
   same inputs. This is the test that would catch a regression of the 18.8(4)
   construction decision if someone later re-introduces a per-call parameter.
4. **Profile** — a profile without `container_user` is rejected by
   `docker_provider.py`'s key set, and a non-numeric value is rejected by the
   field validation.
5. **Existing pins** — every test that pins the committed profile's key set, its
   `to_dict` output, or `profile.digest` is updated with the same strength it had
   before (`test_docker_provider.py`, `test_prepared.py`,
   `test_docker_prepared_composition.py`, `test_docker_training.py`,
   `test_create.py`). Grep first, list every hit and its disposition in the
   HANDOFF.

There is no automated test for P8: the driver is a checked-in operator script
outside the package, and its evidence is the pasted probe output in the run
report.

### 18.16 Deferred ledger entries

For `docs/review/native-windows-publication-closure.md`, under the deferred
ledger:

- **B-9-R1 (Future, engine).** The prepared path does not give the container a
  writable `HOME`, and the engine's `allowed_environment`
  (`tuner/training/methods/sft.py:52-63`) does not admit `HOME` or `TMPDIR`,
  enforced as a subset check at `Trainers/sft/runtime_v1.py:1145-1157`. Under
  `--user` the id has no `passwd` entry, so `HOME=/` and is not writable. Not
  fixable on the Host. Settle from P8's `home-writable` line and run 5's trainer
  output; if it bites, it is an engine allowlist change plus a Host environment
  addition plus a closure regeneration of the B-5 shape.
- **B-9-R2 (Note, pre-existing).** `_verify_artifact_topology`
  (`docker_staging.py:1446-1481`) requires `artifacts`, `state`, `tmp` and
  `tracking` to be **empty**, and it runs on the reuse path as well as on fresh
  staging (`:1791`). A completed run writes into those directories, and a replay
  recomputes the same `stage_key`, so re-staging after a successful run would
  raise "artifact writable directory is not empty". Unrelated to B-9 and not
  introduced by it, but it sits directly on run 5's replay path and on section
  10.2's stage-reuse contract, which is still unproven.
- **B-9-R3 (Note).** Nothing reads `Config.User` back from `docker inspect`, so
  the effective user the daemon applied is not compared against the one
  requested. This is the same shape as the entrypoint residual in 17.11 and has
  the same fix and the same cost — a durable-record schema change. Named, not
  silently deferred.
- **B-9-R4 (Note).** That runs 1-3 mounted the drive without `metadata` is an
  inference that can no longer be tested. It is recorded because it explains the
  timing, and it is load-bearing for nothing in this ruling.

### 18.17 What this ruling does not settle

B-7 and B-2 remain unexecuted on the shipped path: run 4 stopped in the driver's
assertion block, upstream of the single Host command, so the `SystemRoot` fix and
the repo-id stamp have still never run for real. B-8 is unchanged. This ruling
clears the gate in front of them; it is not evidence about them.

### 18.18 Addendum 2026-09-02 — reconciling 18.10 with the 14 keys the Host already passes

Probe #131 (`test-host`, task #131) confirmed both halves of 18.10's premise on
the real image: as `--user 1000:1000` the container starts normally, `id` reports
uid 1000 / gid 1000, `getent passwd 1000` is empty, `HOME=/`, and `/` is not
writable. It then raised a fair objection: if the engine enforces an environment
allowlist, how does the Host already pass 14 keys including `HF_HOME`?

There is no contradiction, and the answer is the whole of sub-question 1.

**All 14 keys the Host passes are already inside the allowlist.** The Host's
environment dict is `docker_training.py:450-464`: `PATH`, `PYTHONNOUSERSITE`,
`PYTHONSAFEPATH`, `PYTHONPATH`, the seven `SYNAPTIC_*` roots, `HF_HOME`,
`TRANSFORMERS_CACHE`, `WANDB_DISABLED`. The engine's `allowed_environment` at
`synaptic-tuner/tuner/training/methods/sft.py:52-63` has 27 entries and contains
every one of those 14. The subset check at
`Trainers/sft/runtime_v1.py:1145-1157` therefore passes today. It is a
*subset* check, not an equality check, so a shorter list is legal and a longer
one is not.

**Verified at the committed blob `4a01fc55`, the five keys in question are all
absent:**

| Key | In `allowed_environment` at `4a01fc55`? |
|---|---|
| `HOME` | no |
| `XDG_CACHE_HOME` | no |
| `TORCH_HOME` | no |
| `TRITON_CACHE_DIR` | no |
| `TMPDIR` | no |

**Ruling on sub-question 1: the fix is NOT Host-only.** Adding any of those five
to `docker_training.py:450-464` makes `planned_environment` a strict superset of
`allowed_environment`, and `runtime_v1.py:1152-1157` raises
`RuntimeV1Error("resolved runtime environment violates portable requirements")`.
The run fails later and less legibly than it does today. This is outside
`coder-user`'s lane and must not be attempted there.

`tuner/training/methods/sft.py` **is a closure member.** Parsing
`tuner/runtime/manifests/offline-sft-worker-v1.json` at `4a01fc55` gives
`member_count 66` and the path is in the member set. So the correct shape is the
B-5 shape and nothing smaller: edit the allowlist, regenerate the closure
manifest, new engine commit, submodule pin moved on the Host, new released
checkout. That is a rePACT, and under the TEST-phase constraint it is a blocker
to be routed, never a patch.

**There is no Host-side bypass, and I would not design one if there were.** The
container's environment is not assembled from the Host dict directly at compose
time. `docker_prepared_composition.py:226-229` takes it from
`request.staging.worker_bundle.dispatch.environment` — the staged bundle,
computed by engine code — and `control_private.py:400-401` asserts that the
materialized pairs' keys equal `workload.environment_keys` exactly, under an
HMAC binding. Passing a key to the daemon that the declared runtime environment
does not carry would be a deliberate divergence between what the run says it
does and what it does. That is the one thing this whole path exists to prevent.

One fact in the engine's favour: `HOME` is not forbidden. The engine's own
refusal set is `dispatch.py:46-48`, `{"PYTHONHOME", "PYTHONUSERBASE",
"HF_TOKEN"}`. `HOME` is admissible in principle; it is merely not yet admitted.

### 18.19 Sub-question 2 — the caches go under `/tmp`, and `/artifacts` is foreclosed

`test-host`'s integration note suggested pointing the unredirected caches at
`roots['cache']` or `roots['tmp']`, on the reasoning that both sit inside
`writable_capability_root="/artifacts"` and that this is tidier than the engine
cloud lane's `/tmp`. It is tidier, and it does not work. I am refusing my own
side's suggestion on measured grounds.

**No subdirectory of `/artifacts` is a legal cache location**, because the stage
verifier requires that tree to stay byte-exact:

- `_verify_artifact_topology` (`docker_staging.py:1446-1481`) requires the five
  directory names exactly (`:1473`), then requires `artifacts`, `state`, `tmp`
  and `tracking` to be **empty** (`:1475-1478`, "artifact writable directory is
  not empty").
- For `cache` it calls `_verify_inventory_at` (`:1474`), which walks the tree
  recursively and demands **set equality on both files and directories**
  (`:1414` "content-addressed model inventory has missing or extra files";
  `:1418` "content-addressed model inventory has extra directories").

So a single HuggingFace lock file under `/artifacts/cache/huggingface`, or a
single triton kernel under `/artifacts/tmp`, fails re-verification. This is not
a style preference; it is the inventory contract.

**This also means the already-shipped `HF_HOME=/artifacts/cache/huggingface`
(`docker_training.py:461`) is on the same collision course**, and
`TRANSFORMERS_CACHE` at `:462` with it. They are legal only for as long as the
libraries write nothing there. I am naming that; I am not designing it away in
this addendum, because it is the same defect as 18.20 and belongs with it.

**Does the Host pre-create those directories?** Yes, and it answers `test-host`'s
open question 2 affirmatively: `_create_artifact_topology`
(`docker_staging.py:1438-1443`) creates all five of `artifacts`, `cache`,
`state`, `tmp`, `tracking` before the container starts. It does **not** create
their subdirectories, and the point is moot given the paragraph above.

**Ruling: `/tmp`.** It is writable for uid 1000 without any new mount (probe
#131, measured), it is container-local and discarded, which is right for caches
that carry no durable value on a network-disabled offline run, and it is outside
every tree the stage verifier inspects. It also has direct precedent inside the
engine: `tuner/cloud/hf_training_image_lock.py:658-666` and `:708-715` already
run a foreign uid (`--user 65534:65534`) with `HOME=/tmp/home`, `HF_HOME=/tmp/hf`,
`XDG_CACHE_HOME=/tmp/xdg`, `TORCH_HOME=/tmp/torch`. `test-host` found that
precedent and it is the correct one to follow.

I do **not** recommend copying that lane's `--tmpfs /tmp:...` mount. `/tmp` is
already writable in this image, a new `--tmpfs` would be a new argv token and a
parser change for no measured gain, and it would compete with the `--user`
insertion that #134 is landing right now.

### 18.20 A finding outside the four sub-questions — B-9-R2 is run-blocking, not a replay note

This is outside what I was asked and I am stating it as a ruling rather than
withholding it, because it gates whether run 5 can reach the evidence that
settles sub-question 4.

When I wrote B-9-R2 in 18.16 I described it as a replay concern. That was too
narrow. The staging verification is not once per run; it is **once per cut**:

1. `execute_docker_training_admission_v1` (`docker_training.py:535-680`) is the
   single entry for every cut of the one unchanging Host command. It calls
   `_activate_docker_training_v1` at `:667`. There is no phase guard between
   admission and that call — the durable phase is read inside activation, after
   staging.
2. `stage_docker_worker_v1` is the first substantive statement of activation
   (`:790`), before any cut-selection logic.
3. `stage_docker_worker_v1` runs `_verify_artifact_topology(final_artifacts,
   model_inventory)` at `docker_staging.py:1791`, on **every** call. The
   `if not final_stage.exists()` guard at `:1775` governs only promotion of the
   temporary stage, not verification.
4. An exception there is caught at `docker_training.py:673-674` and mapped to
   `START_UNAVAILABLE`.

**Consequence:** the first cut issued after the trainer has written anything
under `/artifacts/{artifacts,state,tmp,tracking}` — or anything at all under
`/artifacts/cache` — fails with `START_UNAVAILABLE`. The observe, verify and
publish cuts of run 5 are exactly those cuts.

**What is proven and what is not.** The code path above is proven by reading it.
What is *not* observed is a run actually writing there: no run has reached
training yet. The design intends those writes — `SYNAPTIC_STATE_ROOT`,
`SYNAPTIC_ARTIFACT_ROOT` and `SYNAPTIC_TRACKING_ROOT` point into those
directories and exist for no other purpose — but the cut at which it first bites
is an inference, not a measurement. I am not going to soften that into a
certainty.

I do not rule the fix here. It is a change to the staging contract (verify only
on the promotion path, or verify a recorded pre-run digest instead of emptiness),
not a line, and it is unrelated to B-9. It needs its own blocker and its own
ruling. **Recommendation to the lead: raise it as B-10 and route it before run
5**, because if it holds, run 5 cannot produce the observation that sub-question
4 depends on.

### 18.21 Sub-question 3 — set `HOME`, and set the specific cache keys as well

Both, not one or the other.

`HOME` earns its place because the enumeration argument has now failed twice on
this workstream: B-7 was an unenumerated environment variable (`SystemRoot`), and
B-9-R1 is an unenumerated set of cache writers. Setting `HOME` catches the
writers nobody has listed, which is the class that has actually bitten us.
`test-host` made this argument in their open question 3 and it is correct.

The specific keys earn their place because an explicit declared environment is
auditable, and because the engine's own lane already declares them explicitly
rather than relying on `HOME` alone.

**Proposed key set, for the rePACT to implement — four keys, not five:**

| Key | Value | Basis |
|---|---|---|
| `HOME` | `/tmp/home` | mirrors `hf_training_image_lock.py:662` |
| `XDG_CACHE_HOME` | `/tmp/xdg` | mirrors `:663` |
| `TORCH_HOME` | `/tmp/torch` | mirrors `:663`; probe #131 measured `torch.hub.get_dir()=/.cache/torch/hub`, unwritable |
| `TRITON_CACHE_DIR` | `/tmp/triton` | **not** in the engine lane; see below |

`TMPDIR` is deliberately excluded. Probe #131 measured
`tempfile.gettempdir()=/tmp`, already writable, so adding it would widen the
allowlist for no measured need. The smallest expansion that is provably required
is the right one.

`TRITON_CACHE_DIR` is the one key with no precedent in the engine lane, and the
reason is instructive rather than alarming: that lane locks and verifies an
image, it never trains, so triton never compiles a kernel there. Our lane does
train. Probe #131 measured triton's default as `/.triton`, unwritable. Note
`test-host`'s own honesty flag on that value — it came from an `expanduser`
fallback, not from triton's API — so the *path* is well-founded but its
provenance is weaker than torch's.

**Residual, named not hidden:** nothing pre-creates `/tmp/home`, `/tmp/xdg`,
`/tmp/torch` or `/tmp/triton`. The Host cannot, since `/tmp` is not bound. The
libraries create their own cache roots with `exist_ok=True`, which is why the
engine's lane works without pre-creation, but that is a property of those
libraries rather than a guarantee of ours. It is cheap to confirm from run 5's
output and expensive to assume.

### 18.22 Sub-question 4 — do not block run 5 on this, and do not run probe-4

**It cannot land this cycle**, because 18.18 shows it is not Host-only. There is
no version of this that `coder-user` can ship into the next released checkout.
The choice is therefore not "this cycle vs deferred" but "block run 5 on a
rePACT vs run and learn".

**Ruling: run.** Ship #134 and #135, build the checkout, run 5.

The reason is that B-9-R1 is still **unproven as active**. Probe #131 measured
where the caches *would* go; it did not measure whether anything writes to them.
`test-host` was scrupulous about that distinction and it is the whole of the
decision. Blocking a released checkout on a rePACT to fix a defect that may be
latent inverts the cost. Run 5 is the strictly better instrument: it exercises
the real trainer with the real model, and it has to happen regardless, because
B-2 and B-7 have still never executed on the shipped path (18.17). If a cache
write fails, that failure is both the proof that R1 is active and the name of the
exact variable to admit. If it does not, R1 is latent and stays on the ledger
with evidence behind it instead of an argument.

**Do not run probe-4 (`import unsloth` as uid 1000).** It does not answer the
question it is aimed at. Triton compiles kernels at first kernel launch, not at
import, so a clean import would not show that the triton cache is untouched, and
a failing import would only show a subset of the writers. It would produce a
comfortable green with no information in it. Run 5 dominates it at comparable
cost.

**One sequencing condition.** This ruling assumes run 5 can reach the training
step. If 18.20 holds, it cannot, and the ordering becomes: settle B-10, then run
5, then rule on B-9-R1 from its output. I flag that as a dependency rather than
resolving it, because B-10 is not mine to rule.

### 18.23 Ledger amendments

For `docs/review/native-windows-publication-closure.md`, replacing the two
entries as written in 18.16:

- **B-9-R1 (Future, engine — rePACT shape now known).** Verified at `4a01fc55`:
  the trainer allowlist is declared in TWO closure members and both must be
  widened together, the Python list at `tuner/training/methods/sft.py:52-63` and
  the closed enum at `schemas/synaptic-sft-workload-v1.schema.json`
  (`properties/runtime_requirements/properties/allowed_environment`), 27
  identical entries in each. Neither admits `HOME`, `XDG_CACHE_HOME`,
  `TORCH_HOME`, `TRITON_CACHE_DIR` or `TMPDIR`, while both admit all 14 keys the
  Host passes today. Widening only the Python list leaves the schema rejecting
  the four new keys. Both are closure members, so the fix is an engine edit to
  both copies plus closure regeneration plus a pin move — never a Host patch.
  (Amended 2026-09-02: the original #136 citation named only the Python copy;
  coder-engine-r1 found the second at #147 and widened both; engine `ba844137`.) Caches go to `/tmp`, not `/artifacts`
  (18.19). Proposed keys: `HOME=/tmp/home`, `XDG_CACHE_HOME=/tmp/xdg`,
  `TORCH_HOME=/tmp/torch`, `TRITON_CACHE_DIR=/tmp/triton`. Still unproven as
  active; settle from run 5's output, not from argument.
- **B-9-R2 (superseded — see B-10).** Escalated from a replay note to a
  run-blocking finding: staging re-verifies on every cut, not once per run
  (`docker_training.py:667`, `:790`; `docker_staging.py:1791`), so the first cut
  after any write under `/artifacts` fails with `START_UNAVAILABLE`. Also
  forecloses `/artifacts` as a cache location and puts the shipped
  `HF_HOME=/artifacts/cache/huggingface` (`docker_training.py:461`) on the same
  collision course. Needs its own ruling.

### 18.24 What this addendum does not settle

It does not rule B-10, and the fix there is a change to the staging contract that
I have deliberately not sketched, because sketching it inside a B-9 addendum
would prejudge a ruling that deserves its own candidates. It does not prove that
any cache is written during a real run; that remains the open measurement and run
5 is the instrument. It does not touch #134 or #135, which are correct as
dispatched and should ship unchanged.

## 19. Amendment 2026-09-02 — ruling on B-10 (staging re-verifies the artifact topology on every cut)

### 19.1 The defect, restated from source

`execute_docker_training_admission_v1` (`docker_training.py:535-680`) is the
single entry for every cut of the one unchanging Host command. It calls
`_activate_docker_training_v1` at `:667` with no phase guard. Staging is that
function's first substantive statement (`:790`), and
`stage_docker_worker_v1` runs `_verify_artifact_topology(final_artifacts,
model_inventory)` at `docker_staging.py:1791` on every call — the
`if not final_stage.exists()` guard at `:1775` governs only promotion of the
temporary stage.

`_verify_artifact_topology` (`:1446-1481`) then requires `artifacts`, `state`,
`tmp` and `tracking` to be **empty** (`:1475-1478`). A training run writes into
those directories. So the first cut issued after the trainer writes anything
fails, and `docker_training.py:673-674` maps it to `START_UNAVAILABLE`.

This is pre-existing. B-9 did not introduce it and does not fix it.

### 19.2 Two constraints that eliminate most of the candidate space

**Constraint 1 — staging cannot be skipped on a later cut.** `provisional`
embeds `stage=staging.projection` (`docker_training.py:901`), `request` carries
it (`:904`), and `:917-918` raises `"durable Docker command differs from replay"`
when the replayed `provisional` differs from the stored one. So
`stage_docker_worker_v1` must still run on every cut and must still return a
byte-identical projection. Only the **verification** may become conditional, and
only the part of it that is about use rather than identity.

**Constraint 2 — the phase is not readable where staging happens, but it can
be.** The repository is opened at `:875` and the mutation row loaded at `:919`,
roughly 130 lines after the stage call at `:790`. That ordering is not
load-bearing: `run` (`:843`) is built from `source_lock.run_id` and
`project_ref`, and `repository` from `context` and `clock`. All four are direct
parameters of `_activate_docker_training_v1` (`:734-737`), so both statements can
move above `:790` without depending on staging.

### 19.3 The distinction the contract is missing

`_verify_artifact_topology` does two different jobs in one pass:

| Check | Line | Kind |
|---|---|---|
| root is a real directory, not a symlink or reparse point | `:1455-1461` | identity |
| exactly the five directory names, each a real directory | `:1463-1473` | identity |
| `/artifacts/cache` equals the model inventory exactly | `:1474` | identity |
| `artifacts`/`state`/`tmp`/`tracking` are empty | `:1475-1478` | **use state** |

The identity checks answer "is this the stage we prepared". They must run on
every cut, because they cover the tree that determines what executes. The
emptiness check answers "has anything run against this stage yet". That is a
precondition, and only the caller knows whether it holds.

### 19.4 Ruling — candidate (c), with candidate (a) supplying the predicate

They are not competitors. (c) says *what* becomes conditional; (a) says *what it
is conditional on*. The ruling is both.

**1. `_verify_artifact_topology` takes a required keyword-only parameter.**

```
def _verify_artifact_topology(
    root: Path,
    entries: tuple[DockerModelInventoryEntryV1, ...],
    *,
    expect_unused_artifacts: bool,
) -> None:
```

The loop at `:1475-1478` runs only when `expect_unused_artifacts` is true.
Everything above it is untouched and unconditional.

**2. `stage_docker_worker_v1` takes the same required keyword-only parameter**
under the same name, and forwards it at `:1791`. One term for one thing.

**No default on either.** This is the same rule I applied to `container_user` in
18.3: a default lets a future caller silently get the weaker behaviour, and the
weaker behaviour here is the one that admits an unverified stage.

**3. The caller computes it from the durable phase.** In
`_activate_docker_training_v1`, move `run = TrainingRunRef(...)` (`:843`) and
`repository = SqliteTrainingRepository.from_context(...)` (`:875`) above the
stage call at `:790`, and add:

```
prior = repository.load_docker_run_mutation(run.project_ref, run.run_id)
expect_unused_artifacts = prior is None or prior.phase in {
    DockerRunPhaseV1.CREATE_ADMITTED,
    DockerRunPhaseV1.CREATE_ATTEMPTED,
    DockerRunPhaseV1.CREATED,
}
```

`current = repository.load_docker_run_mutation(...)` at `:919` **stays where it
is and is not replaced by `prior`.** The two reads have different meanings:
`prior` is the state before this cut did anything and may legitimately be
`None`; `current` is read after `create_docker_prepared_run` may have inserted
the row (`:912`) and must not be `None` (`:920-921`). Collapsing them would make
the first cut's `None` reachable at `:920`.

### 19.5 Why the boundary sits between `CREATED` and `START_ADMITTED`

`DockerRunPhaseV1` (`docker_execution_state.py:314-324`) is
`CREATE_ADMITTED, CREATE_ATTEMPTED, CREATED, START_ADMITTED, START_ATTEMPTED,
SUBMITTED, RECONCILE_REQUIRED, PROCESS_SUCCEEDED, PROCESS_FAILED,
ARTIFACTS_VERIFIED`.

`docker create` does not run the container's process. A container that has been
created but never started cannot have written to the bind. So the three phases
up to and including `CREATED` are exactly the phases in which the writable roots
must still be empty, and `START_ADMITTED` is the first phase in which a write is
explicable.

This is corroborated rather than invented: `docker_training.py:922-925` already
branches on precisely `{CREATE_ADMITTED, CREATE_ATTEMPTED, CREATED}` to choose
`.submit(request)`. The existing code already draws the line in the same place
for the same reason. The guard reuses that set rather than introducing a second,
independently-maintained notion of "not yet started".

`START_ATTEMPTED` falls outside the set, which is the conservative direction: a
start that was attempted may have succeeded, so the run may have written.

### 19.6 What a crashed run leaves behind — handled without operator cleanup

| Crash window | Durable phase left behind | Writable roots | Guard result |
|---|---|---|---|
| before `docker create` | `CREATE_ADMITTED` | empty | emptiness required, holds |
| during `docker create` | `CREATE_ATTEMPTED` | empty | emptiness required, holds |
| after create, before the `CREATED` write | `CREATE_ATTEMPTED` | empty | emptiness required, holds |
| after start, mid-training | `START_ADMITTED`+ | non-empty | emptiness not required, cut proceeds |
| after training, before publish | `PROCESS_SUCCEEDED` | non-empty | emptiness not required, cut proceeds |

No window requires an operator to delete a stage by hand, which was the failure
mode I was most worried about in the #139 teachback. The stage_key is recomputed
from the same inputs, so a crashed run's stage is re-entered rather than
orphaned, and every re-entry is still identity-verified in full.

**The check is not removed.** In the pre-start window it keeps its full force: a
stage whose writable roots are non-empty while the phase is still
`CREATE_ADMITTED` still raises, because nothing that the durable record admits
can explain that content. That is the tamper signal, and it survives intact.

### 19.7 Why candidate (b) is closed

A recorded verification digest reused on later cuts cannot do the job, and the
reason is not cost but possibility.

- **For the writable roots it is impossible.** Once the run starts, the Host has
  no expected value for their contents. It does not know what the trainer will
  write. A digest recorded pre-run proves only the pre-run state, which the
  durable phase already proves, more cheaply and without storage.
- **For the read-only tree it is redundant.** `_verify_reuse` (`:1784-1789`) and
  `_verify_inventory_at` (`:1474`) already provide exactly that guarantee, on
  every cut, unconditionally, and this ruling leaves both alone.
- **It would need somewhere durable to record the digest**, which is a new
  column or a new table. The standing constraints forbid a new table absent a
  review proving it unavoidable, and it is not unavoidable — it is unnecessary.

### 19.8 Why a bare phase guard at the activation level is closed

Skipping the `stage_docker_worker_v1` call on later cuts is the obvious cheap
fix and it is forbidden by Constraint 1 in 19.2. Without a projection there is no
`provisional`, and `:917-918` raises. Staging must run every time.

### 19.9 The author's intent, and what the tests already pin

`tests/synaptic_host/test_docker_training.py` installs a spy over
`_verify_artifact_topology` (`:593`, `:605-610`) and asserts at `:691-692` that
it fired once on the fresh stage, then at `:703-704` that it fired **again** on
the replay. So the original author did not merely allow re-verification on
reuse; they pinned it deliberately.

In the #139 teachback I said I would change the ruling if I found this. I have
found it, and it does not change the ruling — it sharpens it. What the author
pinned is that a **reused stage is re-verified**, and this ruling keeps that:
the verifier is still called on every cut and both assertions continue to pass
unchanged. What the author could not have modelled is that between two calls the
container may **legitimately** have written, because at the time the contract
was written the emptiness of the writable roots and the integrity of the stage
were the same predicate. One command growing several cuts separated them. The
fix therefore tells the verifier its precondition rather than weakening its
predicate, which is the disposition I argued for before I knew what the tests
said.

### 19.10 Candidate (d) — `HF_HOME` and `TRANSFORMERS_CACHE` must move to `/tmp`

Yes, and for a reason that stands on its own even if B-10 were fixed some other
way.

I checked the hypothesis I flagged in the #139 teachback as most likely to fall,
and it held. `SYNAPTIC_CACHE_ROOT` is a **read** root, not a scratch root: the
engine resolves the locked model snapshot at
`cache_root / "model" / <repository folder> / "snapshots" / <revision>`
(`tuner/runtime/dispatch.py:189-211`, `Trainers/sft/runtime_v1.py:634-660`). So
`/artifacts/cache` is an input tree, `_verify_inventory_at` is right to demand
exact equality, and this ruling keeps that check **unconditional on every cut**.

That decides `HF_HOME`. The only writers pointed into that input tree are the
Host's own `HF_HOME=/artifacts/cache/huggingface` and
`TRANSFORMERS_CACHE=/artifacts/cache/transformers` (`docker_training.py:461-462`).
If they stay, the first HuggingFace write creates a directory under `cache` and
`_verify_inventory_at` raises `"content-addressed model inventory has extra
directories"` — a check I am explicitly ruling must never be relaxed. So they
move, to `/tmp/hf` and `/tmp/transformers`, joining the four keys from 18.21.

**Scope note for `coder-engine-r1`: this does not grow the engine change.**
`HF_HOME` and `TRANSFORMERS_CACHE` are already in `allowed_environment`
(`sft.py:52-63`). Changing their **values** needs no allowlist edit and no
closure regeneration. Only the four new keys do.

**Amendment (lead, 2026-09-02, after coder-user #149).** The scope note above is
wrong about where the constraint sits. The allowlist admits the two keys, but
the engine's `SourceLockV1.__post_init__`
(`tuner/project/execution_source.py:489-502`) builds a `required_environment`
that pins `HF_HOME` to `roots["cache"] + "/huggingface"` and
`TRANSFORMERS_CACHE` to `roots["cache"] + "/transformers"` and raises
`SourceLockError("runtime environment does not bind the exact roots and
isolation")` on any other value, at admission (`RESOLUTION_UNAVAILABLE`). It is
a required-subset check: adding the four 18.21 keys is free, changing these two
values is refused (measured: 3 regressions in
`tests/synaptic_host/test_docker_training.py` with the move, 0 without). The same
pair is encoded at `tuner/runtime/verification.py:635-636` and
`Trainers/sft/runtime_v1.py:1207-1208`; `execution_source.py` is a closure
member, so the move is the full B-5 shape in the engine, not a Host edit. Filed
as **B-10-R1 (engine)**, task #153. User ruling (META-BLOCK #154, option A):
release without the move; run 5 measures whether anything writes under
`/artifacts/cache` in offline mode with the model resolved from the local
snapshot. Reading at cut 2: cache inventory-exact through the run means
unproven-as-active (ledger Future); `"content-addressed model inventory has
extra directories"` means active, engine rePACT with evidence. That failure
text is distinguishable from B-10's, which names the writable roots, so the two
cannot be confused in the B10-EVIDENCE lines. Host `ab929102` ships the four
keys and leaves `HF_HOME`/`TRANSFORMERS_CACHE` at their 4a01fc55 values.

### 19.11 Pricing against the standing constraints

| Constraint | Effect |
|---|---|
| No compatibility layer, no legacy fallback | None added. `composition.py` is not touched and gains no default. |
| No new database table | None. The guard reads an existing row through an existing method. |
| No downloader, no generic cache framework | None. |
| Closure manifest | **Host-side only, confirmed.** `docker_staging.py` and `docker_training.py` are Host repo files; every closure member is an engine path under `tuner/` or `Trainers/`. No regeneration. |
| Durable SQLite rows | Schema unchanged. One extra read of an existing row, earlier in the same function. |
| Plan fingerprint and `provisional` | Unchanged by the guard. `staging.projection` carries digests of the source manifest, worker projection, closure, inventory and storage configuration — none of them covers writable-root emptiness — so the projection is byte-identical and `:917-918` still holds. |

The `/tmp` cache move **does** change the environment dict, and therefore the
workload digest and the stage key. That is a consequence, not a defect: run 5
starts from a fresh stage regardless, which is what we want.

### 19.12 Coder-ready specification

**`synaptic_host/docker_staging.py`** (in neither B-9 lane, no collision):
1. `_verify_artifact_topology` — add required keyword-only
   `expect_unused_artifacts: bool`; wrap only the `for name in
   _EMPTY_ARTIFACT_DIRECTORY_NAMES` loop at `:1475-1478` in `if
   expect_unused_artifacts:`. Change nothing above it.
2. `stage_docker_worker_v1` (`:1650`) — add the same required keyword-only
   parameter; forward it at the `:1791` call.
3. **No new or reworded failure messages.** `"artifact writable directory is not
   empty"` stays verbatim; it is pinned by `match="not empty"`.

**`synaptic_host/docker_training.py`**, all inside
`_activate_docker_training_v1`. Anchor by statement, not line number, because
`coder-user`'s follow-up shifts the numbering:
4. Move the `run = TrainingRunRef(source_lock.run_id, project_ref)` statement
   and the `repository = SqliteTrainingRepository.from_context(context,
   clock=clock)` statement to immediately after the `authenticator = ...` block
   and before the `staging = stage_docker_worker_v1(...)` call.
5. Immediately before that call, add the `prior` read and the
   `expect_unused_artifacts` predicate exactly as written in 19.4, and pass the
   keyword to `stage_docker_worker_v1`.
6. Leave `current = repository.load_docker_run_mutation(...)` and its `None`
   guard where they are.

**Collision map.** `coder-user` owns the environment dict (`:450-464`) and the
profile pass-through (`:881`); `#134` has landed at `82e6fbd0`, so nothing is
live there now. The `/tmp` cache move in 19.10 is a `coder-user` edit confined to
two lines of the environment dict and is disjoint from items 4-6. Either order is
safe provided they are separate commits.

### 19.13 Tests

**Existing pins that must be updated in the same commit.** Enumerated rather
than discovered later:

- `tests/synaptic_host/test_docker_staging.py` — six direct calls at `:542`,
  `:546`, `:556`, `:560`, `:571`, `:578`, across
  `test_artifact_topology_requires_exact_empty_writable_directories`,
  `test_artifact_topology_rejects_extra_root_and_cache_directories` and
  `test_artifact_topology_rejects_special_slot_and_reparse_root`. Each gains
  `expect_unused_artifacts=True`, which preserves their current meaning exactly.
- `tests/synaptic_host/test_docker_training.py` — the `verify_artifacts` spy
  (`:605-610`) must accept and forward the keyword; the two
  `stage_docker_worker_v1` call sites (`:636`, `:693`) each gain
  `expect_unused_artifacts=True`. **The assertions at `:691-692` and `:703-704`
  stay unchanged and must still pass**, because the verifier is still called on
  both the fresh and the replay path. If either of those assertions has to
  change, the implementation has drifted from this ruling.

**New tests:**

1. Post-run cut passes: an artifact topology with a file in `state` and
   `expect_unused_artifacts=False` does not raise.
2. Identity survives the relaxation — the important one. With
   `expect_unused_artifacts=False` **and** a non-empty `state`: an extra
   directory under `cache` still raises `"extra directories"`; an extra root
   directory still raises `"incomplete or extended"`; a reparse root still
   raises `"redirected or invalid"`. This pins that the relaxation did not
   silently disable the identity half.
3. Predicate: `expect_unused_artifacts` is true for no durable row and for each
   of `CREATE_ADMITTED`, `CREATE_ATTEMPTED`, `CREATED`; false for
   `START_ADMITTED`, `START_ATTEMPTED`, `SUBMITTED`, `RECONCILE_REQUIRED`,
   `PROCESS_SUCCEEDED`, `PROCESS_FAILED`, `ARTIFACTS_VERIFIED`. Enumerate all
   ten so a future enum addition fails the test rather than defaulting into the
   permissive branch.
4. End-to-end replay: after writing a file into `state`, a replay whose durable
   phase is past `CREATED` succeeds, and a replay whose phase is still `CREATED`
   raises `"artifact writable directory is not empty"`.

### 19.14 What run 5 must observe to close B-10 on evidence

B-10 is proven by reading and has never been seen. The fix is correct
independently of that, but the *finding* closes only on an observation.

The stage is fresh at run 5 (19.11), so cut 1 tells us nothing. **The cut to
watch is the first observe cut after submit — cut 2.**

The driver must record, in this order, at cut 2:
1. whether `<stage>\artifacts\state` is non-empty on the Host before the cut is
   issued;
2. the command result code the cut returns.

Readings:

| `state` at cut 2 | Cut 2 code | Conclusion |
|---|---|---|
| non-empty | not `START_UNAVAILABLE` | **B-10 confirmed and fixed.** Close it. |
| non-empty | `START_UNAVAILABLE` | fix is wrong or incomplete; re-open with the message. |
| empty | any | **unconfirmed.** The reading stands unrefuted but untested; B-10 stays on the ledger as latent and the next cut with a non-empty `state` settles it. |

The third row is the honest one and I expect it is possible: if the trainer
buffers and writes late, `state` may still be empty at cut 2. That is not a pass,
it is a deferral, and it must be reported as one.

### 19.15 Ledger row

- **B-10 (Blocker, ruled).** Staging re-verifies on every cut
  (`docker_training.py:667`, `:790`; `docker_staging.py:1791`), and
  `_verify_artifact_topology` requires the four writable roots empty
  (`:1475-1478`), so the first cut after the trainer writes under `/artifacts`
  fails `START_UNAVAILABLE` (`docker_training.py:673-674`). Ruled in section 19:
  the emptiness check becomes conditional on a required keyword-only
  `expect_unused_artifacts`, computed by the caller from the durable phase
  (`prior.phase in {CREATE_ADMITTED, CREATE_ATTEMPTED, CREATED}`, or no row);
  every identity check stays unconditional. `HF_HOME` and `TRANSFORMERS_CACHE`
  move to `/tmp` alongside the R1 keys, because `/artifacts/cache` is a read root
  (`dispatch.py:189-211`) whose exact-equality check must never be relaxed. No
  new table, no schema change, no closure regeneration, projection byte-identical.
  Closes on run 5 cut 2 per 19.14, and stays open as latent if `state` is empty
  at that cut.

### 19.16 What this ruling does not settle

It does not make the writable roots tamper-evident after a run starts. That is
not a gap I am deferring; it is not knowable Host-side, because the Host has no
expectation for what the trainer writes. The tamper surface that matters — the
source closure and the model inventory, which together determine what executes —
stays verified on every cut. It also does not settle whether the trainer writes
early enough for cut 2 to confirm the finding, which is 19.14's third row and
belongs to run 5.

## 20. Amendment 2026-09-02 — ruling on B-11 (the Host refuses the private storage chain the operator created first)

Run 5 passed every precondition and the whole of admission for the first time in
this workstream, then failed at activation cut 1 with `START_UNAVAILABLE` and no
message (report section 17.2). The cause, recovered by test-host from a
gitignored loader-hook probe that reproduced the same `input_digest`, is that the
Host refuses its own HMAC private storage root because the operator recipe
created it first and Windows gave it an inherited access list.

This ruling is written against the authoring baseline `be97a082`. Line numbers
below are that baseline's; coder-user should expect them to move.

### 20.1 The defect, restated from source

`FileHmacAuthenticator.for_docker` (`security.py:510-543`) fixes the private
storage root at `<project_root>\.synaptic` (`:523`), requires the host state root
to be confined below it (`:525-529`), and at `:534` calls
`_ensure_private_storage_directories`. That method (`:585-606`) derives the chain
`.synaptic` -> `.synaptic\state` -> `.synaptic\state\docker` and then does two
different things with it:

- it **creates** only the directories that do not exist (`:595-605`), and
- it **validates** every directory in the chain unconditionally (`:606`).

Creation and validation do not agree about what a private directory is.
`_win_create_private_directory` (`:286-295`) creates with the descriptor built at
`:275`, `O:<sid>G:<sid>D:P(A;;FA;;;SY)(A;;FA;;;<sid>)`. `_win_validate_acl`
(`:349-403`) demands exactly that shape back: a protected list (`:366-370`), the
current user as owner (`:371`), exactly two entries (`:382`), each of them
non-inherited, allow, and full access (`:389-394`), for the current user and
`S-1-5-18` (`:380`, `:397-401`). An ordinary directory creation produces none of
that. So any chain directory the Host did not create itself is refused forever,
and there is no path back: the method never repairs.

Test-host's measurement pins which clause fires. The owner was measured correct,
and the owner test shares one `if` expression with the protection test at
`:366-373`, so the failing predicate is the protection bit. The second probe
printed `ntfs ok` before failing, which clears `_win_require_ntfs` and the
directory and reparse-point attribute checks at `:406-416`. Report section 17.3
records the shape: owner correct, protection **False**, eleven entries, every one
inherited.

The one-variable control in report section 17.3 is what makes this a source
defect rather than a host quirk. Two directories in the same parent, same volume,
same user, differing only in creator, judged by the Host's own validator: the
ordinary creation is REFUSED, the Host private creator is ACCEPTED.

### 20.2 A citation correction, and who actually creates `.synaptic`

Report section 17.3 attributes the first creation to
`materialize_model_inventory.py:177`. That line is inside a generated program
that runs **in a container** and writes to `/out`; it never touches a Windows
path. The Host-side creation is `materialize_model_inventory.py:447`,
`output_root.mkdir(parents=True, exist_ok=True)`, where `output_root` is
`<project_root>/.synaptic/model-inventory` (`:431`). Instruction 2 of the
dispatch inherits the same citation, so this correction propagates: the operator
call site under discussion is `:447`, not `:177`.

The second creator is the driver's P8 stage-parent step, added for B-9. It calls
`stage_parent.mkdir(parents=True, exist_ok=True)` on
`.synaptic\state\docker\stages` (`run_prepared_training.py:582-590`), and its own
comment at `:585-588` says it mirrors the staging call deliberately, so the probe
measures the directory the run will use. P8 runs on a `--probe-only` pass, which
is why a probe-only run leaves the chain refused.

That comment cites `docker_staging.py:1686`. At this baseline `:1686` is a
storage-schema check; the staging call it means is `:1699-1700`. The citation
drifted when the B-10 implementation moved the file, and since section 20.13
edits this docstring anyway, the citation is corrected in the same edit. A second
Host-side ordinary creation sits at `docker_staging.py:1790`, for the stage's own
parent. Both are below `docker` and therefore off the validated chain, so neither
is in this ruling's scope.

So the chain has three directories and three different creators: `.synaptic` from
prerequisite 3, `state` and `docker` from P8, and `stages` from P8 and from
staging. Only `stages` is off the validated chain.

### 20.3 The hazard that decides the shape of the fix

The obvious repair is to rewrite the root's access list with the Host's protected
two-entry descriptor. On Windows that is not a local edit. The documented
behaviour of the access-control editor family is that setting a list on a
container **propagates** to existing children: inheritable entries are pushed
down, and inherited entries that are no longer valid are removed. Every entry on
the failing directory is inherited, so every entry on its children is too, and
the Host's descriptor publishes nothing inheritable. Recomputing a child whose
entries were all inherited from a parent that now publishes nothing leaves that
child with an **empty** list, which denies all access to everyone. The owner
keeps only the right to read and rewrite the list, not to read data. This is the
same trap as removing inheritance from a directory tree in one step.

Two populated subtrees hang below the chain and would be in the blast radius:

| Subtree | Contents | Consequence of an empty list |
|---|---|---|
| `.synaptic\model-inventory` | 25 files, 1 969 841 187 bytes, fingerprint `sha256:0e2a8df2…` | the bind that run 5 proved for the first time stops resolving; A4 and the container's own read both fail |
| `.synaptic\state\docker\stages` | the staged worker bundles | staging cannot write, so no cut can run |

That is the difference between a fix and a regression, and it is not settleable
from documentation. Measurement **B-11-M1** (task #165) resolves it by applying
the identical descriptor through three different calls against a populated
scratch tree and reading the children back. Section 20.8 records the result and
names the call.

### 20.4 The two failure states the validator cannot currently tell apart

The validator collapses two very different conditions into one refusal, and the
whole security argument for repair is that they are distinguishable.

**Never protected.** Every entry carries the inherited flag and the list is not
protected. This state is what the filesystem produces automatically for any
directory made by an ordinary creation call under an ordinary parent. It records
no decision by anybody: nobody chose those entries for this object, they are a
projection of an ancestor. It is the default, and reaching it needs no privilege
beyond making a directory.

**Tampered.** At least one entry is not inherited, or the list is already
protected. Writing an explicit entry, or setting protection, requires the right
to rewrite the list on that object, which means the writer is the owner or was
granted control. That is a decision by a principal, and it is not the Host's.

The Host may overwrite the first state because there is nothing there to
destroy and because replacing it can only remove access, never add it: the new
list names the current user and the local system account and nobody else. The
Host must not overwrite the second, because doing so would erase the evidence of
a third party's decision and would turn the repair path into a laundry for a
directory an attacker had prepared. An attacker cannot forge the first state to
hide a grant, because a grant they wrote is by definition a non-inherited entry.
The one move available to them is to place an inheritable grant on an **ancestor**
so the pre-created directory inherits access for them — and that grant is exactly
what protecting the directory removes. The repair therefore strictly narrows in
every case it is permitted to act.

### 20.5 Ruling — candidate (i), and the repair is owned by the ensure path

**Candidate (i) is adopted.** The Host repairs a chain directory it already owns.

**The repair is owned by `_ensure_private_storage_directories` (`:585-606`).**
Not `for_docker`, and emphatically not `_validate_private_directory` or
`_win_validate_acl`. The reason is a boundary the test suite already draws:
`test_private_storage_rejects_permissive_parent_without_repair`
(`tests/synaptic_host/test_security.py:411-422`) reaches the validator through
`private_storage_verified` and asserts that a permissive parent is refused
**without repair**, and every key operation is fail-closed after drift
(`:392-408`). Verification must stay a pure predicate with no side effects, or
that guarantee dissolves. The ensure path is the only place in the class whose
job is already to make the world match the contract, and it is the only place
that runs before a key is read or written.

`_ensure_private_storage_directories` takes a new **required keyword-only
parameter `repair: bool` with no default**, in the same shape as section 19.12's
`expect_unused_artifacts`. Every call site states its intent, and a future call
site cannot inherit a permissive default by accident.

- `for_docker:534` passes `repair=True`.
- `initialize:609` passes `repair=False`.

That gating is deliberate and it is what keeps the Modal lane out of this change.
`FileHmacAuthenticator.from_context` (`:502-508`) points the Modal authenticator
at `state_root/"modal"`, whose chain is one directory that only the Host ever
creates: no operator recipe, driver or front end pre-creates it, so the Modal
lane does not have this defect and gets no new behaviour. The standing constraint
"no Modal-lane change" is honoured literally. If a Modal front end ever begins
pre-creating that directory, the fix is to flip one argument.

**The repair never raises.** It either narrows the directory or does nothing, and
the unconditional validation at `:606` decides the outcome. A refused directory
fails with the same `ValueError` and the same message as today. This is not a
silent swallow: a swallow is dangerous when it lets a failure go unnoticed, and
here the check that matters runs immediately afterwards and is not conditional on
the repair having succeeded. If the repair cannot act, validation refuses exactly
as it does now.

### 20.6 The repair predicate, and what stays refused

On Windows the repair may act only when **all** of the following hold, evaluated
in this order on an open handle, never by path:

1. The object is a directory and is not a reparse point. This is the check
   already at `:412-416`, and it must run before any list work so
   `test_windows_docker_storage_rejects_directory_junction` (`test_security.py:520`)
   keeps refusing a junction.
2. The owner is the current user. An object owned by another principal is
   refused unchanged. Repairing it would be theatre: its owner retains the right
   to rewrite the list and can widen it again immediately.
3. The list is present and is **not** protected.
4. **Every** entry in the list carries the inherited flag. Zero non-inherited
   entries.

If all four hold, the repair writes the descriptor of section 20.8 through the
call named there. A repaired directory and a Host-created one differ in exactly
one respect, the inherit flags, and section 20.8 gives the reason: creation
happens before the directory has children, repair happens after, and inherit
flags exist only to govern children. Both shapes satisfy the validator, which
does not inspect those flags. If any clause fails, the repair does nothing and
validation refuses.

Refused, unchanged, with today's error:

| Condition | Why it stays refused |
|---|---|
| owner is not the current user | the owner can re-widen it; repairing hides that |
| any non-inherited entry present | somebody made a decision on this object; overwriting it is a tamper mask |
| list already protected but wrong shape | protection is only ever set deliberately |
| reparse point, junction, or not a directory | shape, not access; the repair fixes access only |
| no list present at all (a null list grants everyone) | not the never-protected signature; treat as deliberate |

The rule underneath the table is one sentence: **the repair may correct access,
never shape, and only from the state the filesystem produces by default.**

That sentence carries a premise, and section 20.21 exists because the shipped
code violated it. "The state the filesystem produces by default" means a state no
actor decided, and the Host is an actor. If the repair of one chain member can
alter the state of another, then walking the chain in the wrong order makes the
Host observe its own footprint at the next member and refuse it as somebody's
decision. The predicate is correct; the traversal order is what has to keep its
premise true. Section 20.21.5 rules that order.

### 20.7 Why content inside the chain is not a security precondition

The dispatch asks whether the directory must be empty, or may hold Host-authored
content only, and what foreign content means. On security grounds the answer is
that content is not a precondition at all, because the repair does not confer
trust on anything inside.

There is exactly one object below the chain that the Host trusts, and it is the
control key. It is created with an exclusive create and its own descriptor
(`_win_open_path` with `create=True`, `:318-330`), and every read validates it
independently on its own handle: not a directory, not a reparse point, exactly
one link, exactly 32 bytes, and its own access list checked by the same
`_win_validate_acl` (`_win_read_private_key`, `:428-460`). A key file planted by
somebody else carries an inherited list and is refused at `:440`, before a byte
of it is used. So content cannot become authority, and repairing the directory
around it changes nothing about that.

Everything else below the chain is either verified by content or rebuilt per run.
The model inventory is verified by count, size and fingerprint (report section
17, step 3, and the A4 probe). The stage tree is verified by
`_verify_artifact_topology` on every cut, which section 19 already rules on.
"Foreign content" is therefore not a category the repair needs to police, because
there is no unvalidated trusted object for it to name.

The one reason an emptiness precondition could still be required is not security
but availability: the propagation hazard of section 20.3. B-11-M1 removed it, so
there is no precondition on content from either direction.

### 20.8 The Windows call the repair issues, and the descriptor it writes

Measurement B-11-M1 (task #165, scripts and logs at `F:\Code\scratch-b11`) ran
the identical Host descriptor through three different calls against a populated
scratch tree built the same way run 5's tree was built, and answered four
questions per arm with the Host's own validator and the run 5 bind shape.

| Arm | Call | Validator | Owner reads | WSL reads | Container reads |
|---|---|---|---|---|---|
| A | `SetNamedSecurityInfoW`, by path | ACCEPT | **NO** | **NO** | **NO** |
| B | `SetKernelObjectSecurity`, by handle | ACCEPT | yes | yes | yes |
| C | `SetFileSecurityW`, by path | ACCEPT | yes | yes | yes |
| D | Host creator first, then ordinary population | ACCEPT | yes | yes | yes |
| E | arm A's call, descriptor entries made inheritable | ACCEPT | yes | yes | yes |

The hazard of section 20.3 is real and it is arm A. It left
`model-inventory`, `sub` and `probe.txt` with a list that is present and empty,
`ace_count 0`, which denies everyone including the owner. Only
`SetNamedSecurityInfoW` runs the automatic propagator; the children held nothing
but inherited entries and the Host descriptor publishes nothing inheritable, so
each child recomputed to nothing.

**Ruling. The repair issues `SetKernelObjectSecurity` on the handle it already
holds, and writes a protected descriptor whose two entries are inheritable:**

```
O:<sid>G:<sid>D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;<sid>)
```

That differs from the creation descriptor at `:275` in exactly one place, the
inherit flags on both entries, and it is deliberately a **combination** of two
separately measured facts rather than a copy of any single arm:

- The **call** decides whether children are recomputed. Arm B measured
  `SetKernelObjectSecurity` as non-propagating: the children came back unchanged
  at 11 and 7 inherited entries, and readable from Windows, from WSL and from
  the container as uid 1000.
- The **descriptor** decides what a recompute would produce. Arm E measured the
  inheritable form: the root comes back protected with two non-inherited entries
  at inherit flags `0x03` and the validator still ACCEPTs it, and the children
  come back with two properly sourced inherited entries and stay readable
  everywhere.

Those two properties are orthogonal, which is what makes the combination sound:
the call cannot change what an inheritable entry means, and the descriptor cannot
change whether the call propagates. Section 20.14's W1 and W5 pin both halves in
the shipped artifact so the combination is not left as an inference.

**Why the combination beats every single arm.**

- It beats **A** because A is destructive.
- It beats **C** on shape, not on outcome. C measured identically to B, but it is
  a path-based call. Every other opening in this module uses a handle opened with
  the reparse-point flag at `:313`, re-opens and compares identity (`:408-422`),
  and refuses a junction (`test_security.py:520-535`). A repair that decides on a
  handle and then writes by path reintroduces exactly the swap the module spends
  that effort closing, in the one code path whose entire subject is a security
  boundary. Instruction 1 of the dispatch puts it directly: a repair path must not
  become a tamper mask.
- It beats **E** on blast radius and on the same handle argument. E is safe and
  fully measured end to end, but it propagates, so activating it would rewrite the
  access lists of 25 inventory files and 1.97 GB of an operator's tree as a side
  effect of fixing three directories. The repair should do the least that makes
  the contract hold.
- It beats **B alone** on test-host's first caveat. After B the children are
  readable but incoherent: they carry entries marked inherited from a parent that
  publishes nothing, so any later event that runs the propagator above them
  reproduces arm A's outcome after the fact. With the inheritable descriptor that
  same later event recomputes them to the arm E state instead, which is benign
  and measured. The caveat is not accepted as a residual, it is closed by the
  descriptor.

So the immediate state is arm B's, the eventual state under any re-propagation is
arm E's, and arm A's state is unreachable from either.

**Consequences for the rest of this ruling.** There is no content precondition:
a populated chain is repaired in place, and section 20.7's security argument
stands on its own. Test-host's second caveat is already satisfied, because the
loop at `:594-606` covers all three chain directories and run 5 refused all
three. The repair is order-independent: a protected child is skipped by the
propagator, and an unprotected one satisfies the predicate either way.

**One finding that is not about the primitive.** In arm A the Host validator
**ACCEPTed** the root whose subtree it had just destroyed. That is correct
scoping, since the contract is about the directory and not its contents, but it
means the validator can never be the acceptance test for the repair. That is why
W5 exists and why run 6's row 3 in section 20.16 is load-bearing rather than
ceremonial. Arm F adds the reason it must be caught before merge and not after:
an owner can reset a damaged child, because an owner keeps the right to rewrite a
list even under an empty one, but repairing the top child does not repair its
descendants, so recovery has to walk the whole subtree.

**A claim of mine that the measurement retired.** In arguing that no design was
correct under both outcomes, I stated that making the entries inheritable would
push the root to four entries and break the validator's exact-two check. That is
wrong. `_win_validate_acl` inspects the entry type, the inherited flag and the
mask (`:389-394`); it does not inspect the inherit flags, and arm E confirms the
root passes at flags `0x03` with the count still two. The route I closed was
open. The measurement was still required, because whether that route propagates
benignly and whether the root still validates were both unknown, but it was
required for a different reason than the one I gave.

### 20.9 Symmetric behaviour on POSIX

The same absent-versus-existing asymmetry exists on POSIX, so the non-Windows
path is **not** left untouched.

`_create_private_directory` creates with `os.mkdir(path, 0o700)` (`:550-553`),
and `_validate_private_directory` demands the effective user as owner and mode
exactly `0o700` (`:576-577`). A directory a shell or a wrapper created before the
Host ran carries `0o755` under an ordinary umask and is refused forever, by the
identical mechanism. It has not been observed because the Host lane that
pre-creates directories is the Windows one, but the defect is in the shared
control flow, not in the platform branch.

The POSIX repair is `os.fchmod` on the descriptor `_validate_private_directory`
already opens, guarded by the same predicate translated:

1. the opened object is a directory and the path is not a symbolic link, using
   the checks already at `:571-575`,
2. `st_uid` equals the effective user id,
3. the mode grants more than `0o700`, and repairing means clearing the extra
   bits and nothing else.

Owned by another user, or a symbolic link, stays refused. Because POSIX modes do
not propagate, the hazard of section 20.3 has no POSIX counterpart, and a
populated directory is repaired with no effect on its children.

The repair acts on the descriptor, not the path, for the same reason the
validator re-opens and compares identity: a path can be swapped between the
decision and the action.

### 20.10 Ruling on the operator side — candidate (c), plus a documentation duty

**The operator recipe changes nothing. The Host repair carries it.** Neither
`materialize_model_inventory.py:447` nor the driver's P8 stage-parent creation
stops creating the directories, and neither calls the Host's private creator.

The dispatch requires an answer that holds for **any** wrapper or front end that
touches the project directory before the Host does, and that requirement decides
it on its own. The Host cannot compel a front end it has never seen to call
anything. Any rule of the form "creators must use the Host's private creator" is
unenforceable at exactly the moment it matters, which is the first time somebody
runs a script this repository did not write. A durable fix must therefore live
where the Host can guarantee it runs, and that is activation.

The other two options are worse for concrete reasons, not only on principle:

- **Stop creating `.synaptic` (candidate iii).** Not available to prerequisite 3.
  Its whole job is to write a tree under `.synaptic\model-inventory` before the
  Host has ever executed, so it must create the parent. Report section 17.3
  reaches the same conclusion for P8 by a different route.
- **Call the Host's private creator.** It couples a skill script to the Host's
  security internals and forces a new public creator onto the module surface. It
  also changes the access list of the inventory's parent *before* the inventory
  is written, which changes the shape of the one thing that finally worked in run
  5, and whether that is safe is arm D of B-11-M1 rather than a known.

Choosing candidate (c) does leave a window in which `.synaptic` is
group-accessible on a shared machine, between prerequisite 3 and the first
activation. That window holds no secret: the control key does not exist yet on a
first run, and on a later run it was created after a repair and is protected and
independently validated. The inventory inside the window is public model weights
whose integrity is checked by fingerprint, not by access control.

The complement is therefore a documentation duty, not code. Two places must say
that a pathlib-created chain is **expected** and is repaired at activation, so
that a future maintainer does not "fix" P8 by pre-protecting the directory and
reintroduce the arm-D question:

- the P8 docstring in `run_prepared_training.py` (near `:582-590`), and
- the `host-docker-run` skill, beside prerequisite 3 and prerequisite 9.

Because the skill tree has generated mirrors, that edit is canonical-first and
then synced; it is not a mirror edit.

### 20.11 Ruling on surfacing the activation cause

**A log line on stderr. No `cause` field, no new result schema, and no driver
change.**

The result model is fixed: `_failure` (`cli.py:331-353`) builds a
`TrainingRunCommandResultV2` with a positional field list and six trailing
`None`s, and `test_cli.py:468` pins the field-presence shape per code as a
four-tuple. Adding a field makes it a v3 result, ripples into that table, into
`__post_init__`'s operation-shape rules, and into every consumer of the JSON
line, all to carry a diagnostic whose only reader is a person. The dispatch says
no new result schema unless unavoidable, and it is avoidable.

It is avoidable because the driver **already** surfaces stderr. `_one_cut`
(`run_prepared_training.py:942-966`) parses the last stdout line as the result
JSON (`:956-962`) and then prints every stderr line with a `stderr| ` prefix
(`:963-965`). Run 5's cut 1 printed no such line, which is itself the measurement
that the Host currently writes nothing. So the whole fix is one line written to
stderr from inside the Host, and the operator sees it with no driver change at
all. stdout is untouched, so the result JSON stays byte-identical and the last
line stays parseable.

There is precedent in this codebase for exactly this shape. B-7's fix made
`ScopedGitRemoteReader` surface the child's own diagnosis instead of a bare exit
code, and its test
(`test_security.py:637-664`) pins the three properties that matter: the cause
reaches the operator, the text is length-bounded so a hostile source cannot flood
the log, and credential material is removed even though it should never have
reached that slice.

**Format.** One line, to stderr, from the two handlers in
`execute_docker_training_admission_v1`:

```
synaptic-host: <CODE> <ExceptionClassName> at <package-relative file>:<line> in <function>
```

For run 5's failure that reads:

```
synaptic-host: START_UNAVAILABLE ValueError at synaptic_host/security.py:373 in _win_validate_acl
```

**What it carries, and what it deliberately does not.** The frame is taken from
the innermost traceback frame whose file lies inside the `synaptic_host` package
directory, rendered relative to that package's parent so no user directory
appears. If there is no such frame, the frame renders as `<unknown>`. The
exception's own text is **excluded entirely**, and that exclusion is the point:
exception text is not under the Host's control. `FileNotFoundError` and `OSError`
render an absolute path and the platform's message; several engine errors render
a value they were checking. A rule that filters that text would be a rule about
strings nobody in this repository wrote. A frame identity is authored here, is
stable, and is precisely the information whose absence cost run 5 a cycle and
cost test-host a loader-hook probe to recover. The line is also length-bounded on
the same argument as the B-7 precedent.

**Applied to both handlers, not one.** The dispatch names `:695-696`
(`START_UNAVAILABLE`). The identical bare shape sits four lines above at
`:686-687` (`RESOLUTION_UNAVAILABLE`), guarding the model-inventory resolution
that B-8's stat-identity re-check lives behind. Same blindness, same cost if it
fires, one call each. This is a deliberate and small widening of the dispatch's
scope and it is flagged as such rather than made quietly.

**Where the code goes.** A module-level helper in `docker_training.py` that takes
the exception and the code and writes the line; the two handlers call it before
returning `fail(...)`. `synaptic_host` writes nothing to stderr today, so this is
new behaviour for the package, and it is confined to two failure paths that
already return an unavailable result.

### 20.12 Pricing against the standing constraints

| Constraint | Status |
|---|---|
| submodule-first, no engine change | held; nothing under `synaptic-tuner` is touched, no closure regeneration, no allowlist change |
| no downloader, cache framework, compatibility layer, legacy composition fallback | held; none introduced |
| no new database table, no schema change | held; the durable rows and the result model are untouched, which is the direct reason section 20.11 rules a log line |
| no Modal-lane change | held by the `repair=False` argument at `initialize:609`; the Modal authenticator's one-directory chain is Host-created and gets no new behaviour |
| B-10-R1 out of scope | held; nothing here touches `SourceLockV1` or the cache roots |
| no secrets in the prepared command, staged source, logs, report or inventory | held, and strengthened: the cause line is structurally incapable of carrying a value or an absolute path |
| container network-disabled and credential-free | held; nothing changes in the composition |
| Windows Host Python orchestrates only | held; the repair runs in the Host process, no new process is started |
| B-5 argv equality | unaffected; the composition, the closure and the prepared argv are untouched |

### 20.13 Coder-ready specification

All changes are in the Host repository on `feat/submodule-cloud-api-v1-host`.

**`synaptic_host/security.py`**

1. `_ensure_private_storage_directories` gains a required keyword-only
   `repair: bool` with no default. In the loop at `:594-606`, when a directory
   already exists, attempt the repair before validating; when it was just
   created, do not. Validation at `:606` stays unconditional and stays last.
2. Add a private repair helper that dispatches on `os.name`, returns `None`
   always, and raises nothing. It catches `OSError` and `ValueError` and returns.
   `ValueError` is in that set deliberately: `_private_storage_error()` returns a
   `ValueError`, and the descriptor construction at `:276-279` raises it, so a
   repair that reused that construction could otherwise raise out of a helper
   that must not.
3. Windows branch: apply the four-part predicate of section 20.6 in order on an
   open handle, and on success call `SetKernelObjectSecurity` on that same handle
   with the discretionary-list and protected-discretionary-list information flags,
   writing the descriptor of section 20.8. Build that descriptor through the same
   conversion `_win_security_attributes` uses at `:276-279`, from the string of
   section 20.8, so the two descriptors differ in one visible place and neither is
   retyped.
   The repair opens its **own** handle rather than extending `_win_open_path`
   (`:310-334`), because rewriting a list needs an access right that helper does
   not request and its three existing callers must not silently acquire. B-11-M1
   opened with the write-list and read-control rights together plus backup
   semantics, and that combination is measured to work. Keeping the new access
   confined to the repair also keeps `_win_open_path` off the changed-files list.
4. POSIX branch: apply the predicate of section 20.9 and `os.fchmod` the
   descriptor to `0o700`.
5. `for_docker:534` passes `repair=True`. `initialize:609` passes `repair=False`.
6. Do not touch `_validate_private_directory`, `_win_validate_acl`,
   `_win_validate_directory`, `_win_read_private_key`, `_win_create_private_directory`
   or `private_storage_verified`. The refusal surface and its message are unchanged.

**`synaptic_host/docker_training.py`**

7. Add a module-level cause helper producing the line of section 20.11.
8. Call it from the handler at `:686-687` with `RESOLUTION_UNAVAILABLE` and from
   the handler at `:695-696` with `START_UNAVAILABLE`, before the `return fail(...)`.
   Both handlers keep their bare `except BaseException` and keep returning the
   same code: the change is additive.

**`.skills/host-docker-run/` and the driver**

9. Documentation only, per section 20.10: state in the P8 docstring and in the
   skill that an inherited chain after a `--probe-only` pass is expected and is
   repaired at activation. Canonical `.skills/` first, then sync the mirrors with
   the repository's sync script. No behaviour change in the driver, and no change
   to `materialize_model_inventory.py`.

### 20.14 Tests

Windows-only, marked with the existing `WINDOWS_ONLY` skip, run on the Windows
Host Python from the released checkout the way the run 5 suite was run. These
cannot execute in the WSL suite and must not be written so that they silently
pass there.

| # | Test | Asserts |
|---|---|---|
| W1 | a chain directory pre-created by an ordinary `mkdir` is repaired | `for_docker` succeeds; the directory is protected, has exactly two non-inherited full-access entries for the current user and `S-1-5-18`, and **both entries carry the object-inherit and container-inherit flags**. The flag assertion is half of section 20.8's combination and is the half a copy-paste of the creation descriptor would silently lose |
| W2 | repair is idempotent | a second `for_docker` over the same tree still validates and changes nothing |
| W3 | a directory carrying one explicit non-inherited entry is refused | `ValueError` matching `private storage`; the entry is still there afterwards, proving the repair did not act |
| W4 | a directory already protected with the wrong entries is refused | same error; protection is deliberate, so it is the tampered state |
| W5 | a populated chain survives repair | a file written under `.synaptic` before activation is still readable by the owner after `for_docker` returns, **and its access list is unchanged**. This is the other half of section 20.8's combination, the non-propagating half, and it is the regression guard for section 20.3. Note that the Host validator accepts the root in the destroyed case too, so this test must read the child, not ask the validator |

POSIX, running in the ordinary WSL suite:

| # | Test | Asserts |
|---|---|---|
| P1 | a chain directory pre-created at `0o755` and owned by the current user is repaired to `0o700` and validates | the ensure path repairs |
| P2 | a symbolic link in the chain is refused | shape is never repaired |
| P3 | `private_storage_verified` still refuses a permissive parent without repairing it | this is the existing `test_security.py:411-422`, unchanged and still green. It is the proof that repair lives only in the ensure path |

Cause line, running in the WSL suite:

| # | Test | Asserts |
|---|---|---|
| C1 | the line names the class and the innermost `synaptic_host` frame | the file is package-relative, the function and line appear |
| C2 | the exception's own text never appears | raise an exception whose message contains an absolute path and a secret-shaped string, assert neither reaches the line, and assert the line's length bound. Mirrors `test_security.py:637-664` |
| C3 | stdout still carries exactly one parseable result line | the cause goes to stderr only, so the driver's `:956-962` parse is unaffected |

The driver needs no change, but it does need one new test. `_one_cut`'s stderr
printing at `:963-965` is currently uncovered:
`tests/skills/host_docker_run/test_run_prepared_training_probes.py` exercises
stderr only for the P8 failure path (`:389-393`), not for a cut. Add **D1**: a
fake cut whose stderr carries a cause line, asserting the driver prints it with
the `stderr| ` prefix and still parses the result JSON from the last stdout line.
Without D1 the whole of section 20.11 rests on an unpinned behaviour of the file
this ruling relies on not changing.

### 20.15 Files that must NOT be touched, and the pins on the files that are

| File | Why it stays |
|---|---|
| `synaptic-tuner/` in any form | engine is untouched; no allowlist, no schema, no closure regeneration |
| `synaptic_host/docker_v1/composition.py` | the legacy composition path stays unused |
| `synaptic_host/cli.py` | no result-schema change; this is the direct consequence of section 20.11 |
| the committed provider profile | B-9's `container_user` is unchanged |
| `/etc/wsl.conf` | user ruling of 2026-09-02, option A; acceptance evidence comes from an unmodified host |
| `/mnt/f/Code/ehr-release-ab741054` and its logs | run 5 state is preserved for reproduction |
| `materialize_model_inventory.py` | section 20.10 rules the operator side unchanged |

Pins on the files this ruling does change, enumerated so none of them is
discovered mid-implementation:

| Pin | Location | Disposition |
|---|---|---|
| permissive parent refused **without repair** | `test_security.py:411-422` | stays green unchanged; it is the boundary the ruling honours |
| default access list on a **key file** refused | `test_security.py:503-516` | stays green; the repair is directory-only |
| directory junction refused | `test_security.py:520-535` | stays green; predicate step 1 runs before any list work |
| fail-closed after drift | `test_security.py:392-408` | stays green; verification stays a pure predicate |
| result field-presence shape per code | `test_cli.py:468` and `:489` | stays green; no schema change |
| constructive `for_docker` uses under `tmp_path` | `test_docker_training.py:229`, `:638`; `test_docker_prepared_composition.py:188`, `:217`, `:239`, `:258`, `:523` | stay green; the repair is a no-op on a directory the Host created |
| `B10-EVIDENCE` line format | `test_run_prepared_training_probes.py:627-631` | stays green; the driver is unchanged |

### 20.16 What run 6 must observe

**B-11 itself.**

| Row | Observation | Reading |
|---|---|---|
| 1 | P8 on `--probe-only` may still leave an inherited chain | **expected**, not a failure. The ruling is Host-repair-only, so the chain is corrected at activation, not at probe time. Run 6 is judged against the design that shipped |
| 2 | cut 1 reaches the container | `START_UNAVAILABLE` does not recur; the run produces a stage, a durable row and a container reference |
| 3 | the inventory re-verify still passes **after** activation repaired the chain | re-run the inventory verification once cut 1 has returned, and get the same 25 files, 1 969 841 187 bytes and fingerprint `sha256:0e2a8df2…`. This is the acceptance row for section 20.3 and it is the one that would catch a propagation regression |
| 4 | if activation fails for any reason, the driver prints a `stderr\|` line naming the frame | this is the acceptance row for section 20.11, and it is the only row that is proved by a failure |
| 5 | after cut 1, record the protected flag, entry count and entry flags for the three chain directories and for `.synaptic\model-inventory` | corrected by section 20.21.8. The chain directories should each show protected with exactly two non-inherited full-access entries at flags `0x03`; the inventory should show its original entries preserved and still marked inherited, NOT converted and NOT protected, which is the measured F: end state of section 20.21.1. This row is now a **volume discriminator**: an inventory that comes back protected with explicit entries means the real tree behaves like the temp volume and B-11-R1 is live on it, which is a stop of its own. **An emptied access list is a stop** either way — it is the destructive arm A shape, and it fails test W5 as well

**Unchanged from earlier rulings, and still owed.**

| Blocker | Measurement |
|---|---|
| B-10 | the cut-2 evidence line of section 19.14. `state_nonempty=true` with a code other than `START_UNAVAILABLE` confirms the fix; an empty `state` is the deferral row, not a pass |
| B-10-R1 | list `<stage>\artifacts\cache` at cut 2 and at the end of the run. It stays user-deferred; run 6 measures it, it does not fix it |
| B-9-R1 | the trainer's own `/tmp` cache landing: `/tmp/torch`, `/tmp/triton`, `/tmp/xdg` and `/tmp/home` populated inside the container. The P8 probe's `HOME=/ home-not-writable` is the pre-existing measurement from task #131 and is not this evidence |

### 20.17 Ledger row

| Row | Content |
|---|---|
| 20.1 | B-11. `_ensure_private_storage_directories` (`security.py:585-606`) creates only absent directories and validates all of them, so a chain directory the operator created first is refused forever. Fix: a required keyword-only `repair: bool`, repair permitted only from the never-protected state, owned by the ensure path so verification stays a pure predicate. Windows and POSIX both. No engine change, no schema change, no Modal-lane change |
| 20.1a | B-11 primitive, measured by B-11-M1 (#165). `SetKernelObjectSecurity` on the handle, with a protected descriptor whose two entries are inheritable. The path-based editor call is DESTRUCTIVE: it empties the access list of every child, unreadable to the owner, to WSL and to the container, while the Host validator still accepts the root |
| 20.2 | B-11 cause surfacing. `docker_training.py:686-687` and `:695-696` swallow the cause. Fix: one stderr line carrying the exception class and the innermost `synaptic_host` frame, never the exception text. The driver already prints stderr at `run_prepared_training.py:963-965`, so no driver change |
| 20.3 | Citation correction. Report section 17.3 and dispatch instruction 2 cite `materialize_model_inventory.py:177` as the Host-side creator of `.synaptic`. That line runs in a container against `/out`. The Host-side creator is `:447` |
| 20.4 | Citation drift. The P8 docstring cites `docker_staging.py:1686` for the staging call it mirrors; at this baseline that is a storage-schema check and the call is `:1699-1700`. Corrected in the same docstring edit as row 20.2's documentation duty |
| 20.5 | B-11-R1. The shipped chain repair walks root first. On volumes where an ancestor's protected list is reconciled against existing children, repairing `.synaptic` converts `.synaptic\state` to protected with explicit entries, which section 20.6 must refuse and the validator rejects, wedging the chain permanently and unreachably. Measured absent on `F:` and present on the Windows temp volume, three trials each; `pytest tmp_path` is on the failing volume and the suite passes anyway because every fixture pre-creates the root alone. Fix: repair leaf first in a pass of its own, conditional on W6, fallback variant 3. Discriminator between the two volume classes stated as observed, with `SE_DACL_AUTO_INHERITED` on the child as the hypothesis and a one-read falsifier |

### 20.18 What this ruling does not settle

It does not make the chain private during the window between prerequisite 3 and
the first activation. That window is argued safe in section 20.10 rather than
closed, and the argument depends on the control key not existing yet on a first
run. If a future front end writes a secret under `.synaptic` before the Host has
run, the argument lapses and the operator side has to be revisited.

It does not give the Host a way to notice that a chain directory was widened
*between* activation and the trainer's exit. The validator runs at activation and
the key is re-validated on every use, so an attack in that window cannot reach
the key, but the directory itself is not watched.

**It does not re-permission what is already inside the chain, and B-11-M1 made
one consequence of that concrete.** After the repair the objects that were
already there keep the access lists they had, which on the measured host means
eleven inherited entries granting local groups modify access. Two of those
objects are worth naming. The model inventory is public model weights whose
integrity is checked by fingerprint, so a permissive list there costs nothing.
The durable rows database under `state` is a different matter: another local user
can write it, and the activation path compares a replay against it
(`docker_training.py:917-918`) and derives the section 19 emptiness predicate
from its phase. That exposure is **pre-existing**, not created here, and the
contract this ruling implements is about the directory chain rather than its
contents. It is recorded as a follow-up rather than fixed as a side effect,
because the choice to widen the repair into an operator's tree should be made
deliberately and not fall out of a primitive selection. The inheritable
descriptor means any later propagation narrows those objects rather than
destroying them.

It does not make a Host-created chain and a repaired chain identical. A created
directory publishes nothing inheritable, so objects made under it later get the
creating process's default list, which B-11-M1 arm D measured as owner, the local
system account and the logon session, and readable. A repaired directory
publishes owner and system inheritable. Both satisfy the validator and both are
readable; closing the difference would mean changing the shared creator, which
the Modal lane also uses, for no benefit this blocker needs.

It does not address the same never-repaired asymmetry anywhere outside this
class. The pattern of "create correctly, validate strictly, never reconcile" is a
shape, and this ruling fixes the one instance that has cost a cycle.

### 20.19 Addendum — three gaps found during implementation

Two of these are enumeration failures of mine, and they are the same failure
twice: I listed the instances I had read rather than sweeping the codebase for
the shape. Section 20.15 applied that discipline to test pins and found every
one; sections 20.5 and 20.11 did not apply it to call sites or to handlers.
Citations verified against `be97a082`.

#### 20.19.1 The ensure path has three callers, not two

`_ensure_private_storage_directories` is called from `for_docker:534`,
`initialize:609` and **`_key:693`**. Section 20.5 named the first two. The
required keyword-only flag forces a value at the third, so it has to be ruled.

**`_key:693` passes `repair=False`.** This is not a close call; section 20.5's
own rationale dictates it. `private_storage_verified` is literally
`self._key(); return True` (`:762-765`), and `encoded_key`, `sign` and `verify`
all reach the key the same way. If `_key` repaired, then reading the property
would repair as a side effect, `test_security.py:411-422` would fail by design
rather than by accident, and the fail-closed-after-drift guarantee at `:392-408`
would be inverted: drift would be silently corrected instead of detected. The
repair belongs to the path that makes the world match the contract, never to the
path that reports whether it does.

Nothing is lost by refusing to repair there. `for_docker` repairs at `:534`
before it ever touches the key, and both of its continuations — `initialize` at
`:540` and `_key` at `:542` — re-enter the ensure path afterwards, find a chain
that is already valid, and no-op.

This is also the clearest evidence that the required flag with no default was the
right shape. A default would have handed `_key` whatever that default was, and on
a permissive default it would have silently broken the drift guarantee with no
diff to review.

#### 20.19.2 The cause line moves into `fail`, and covers every handler

Section 20.11 said two handlers, and widened the dispatch's one to two. A sweep
of `execute_docker_training_admission_v1` for the shape finds **seven**, and
every one of them converts an exception into an outward result:

| Handler | Code returned | Stage it guards |
|---|---|---|
| `:601-602` | `COMPOSITION_UNAVAILABLE` | issuing the admission session |
| `:609-610` | `RESOLUTION_UNAVAILABLE` | proving the source |
| `:623-624` | `COMPOSITION_UNAVAILABLE` | config and profile blobs |
| `:647-648` | `DESTINATION_INVALID` | destination config and policy |
| `:677-678` | `RESOLUTION_UNAVAILABLE` | dataset, manifest and storage blobs, plan compile, plan verify |
| `:686-687` | `RESOLUTION_UNAVAILABLE` | model inventory resolution |
| `:695-696` | `START_UNAVAILABLE` | activation |

The collapse is worse than section 20.11 described. `RESOLUTION_UNAVAILABLE` is
returned by three different handlers and `COMPOSITION_UNAVAILABLE` by two, so the
outward code does not even identify which stage failed, let alone why. B-7 was
swallowed by one of the early three and cost a cycle; B-11 was swallowed by the
last and cost another. Leaving four of them blind would bank the same cost again.

**Ruling: the emission moves into the local `fail` closure at `:580-584`, and is
guarded on there being an exception currently being handled.** One edit, not
seven. Every handler is covered because every handler returns through `fail`, a
future handler cannot forget it, and the single non-exception caller at `:587`
emits nothing because no exception is active there. This supersedes section
20.11's two-site instruction and section 20.13 item 8, and it makes the diff
smaller than the ruling it replaces.

The closure is local to Docker admission. `_failure` in `cli.py:331-353` is
shared with the Modal lane and stays untouched, so the no-Modal-lane-change
constraint still holds. The line's content, its exclusions and its length bound
are unchanged from section 20.11: the code, the exception class, and the
innermost frame inside the Host package rendered package-relative, never the
exception's own text.

Test C1 gains one case: a failure raised in an early stage produces a line naming
that stage's frame, so the test pins that the coverage is the closure's and not
one handler's.

**Scope note, made openly.** The dispatch named one handler, section 20.11 named
two, the coders found a third, and the sweep finds seven. That is growth, and it
is the lead's call to trim. If it is trimmed, the coherent smaller shape is the
three on the path this workstream's blockers actually live on, `:677`, `:686` and
`:695`, kept as explicit per-handler calls. What should not happen is keeping the
closure form but excluding handlers, since the whole benefit of the closure is
that it cannot be selective.

#### 20.19.3 A fourth row for the 19.14 reading table

Section 19.14 gives three readings for cut 2, and all three presuppose that a cut
2 happened and that the stage existed so `state` could be read. The driver
produces a fourth outcome that none of them covers: **no evidence**. It arises
two ways, both seen already: cut 1 is refused and the loop exits, so no cut-2
line is emitted at all; or a line is emitted with the stage absent or lacking its
artifacts child, so the flag reads `unknown` rather than `true` or `false`.

Read the driver's own flag, and read it as three values, not two:

| `state_nonempty` at cut 2 | Cut 2 code | Row | Conclusion |
|---|---|---|---|
| `true` | not `START_UNAVAILABLE` | 19.14 row 1 | B-10 confirmed and fixed |
| `true` | `START_UNAVAILABLE` | 19.14 row 2 | fix wrong or incomplete; re-open |
| `false` | any | 19.14 row 3 | deferral: unrefuted but untested |
| `unknown`, or no cut-2 line | any | **20.19.3** | **no evidence** |

The distinction between the deferral row and this one is not pedantic. A deferral
asserts something about the trainer, that it may have buffered and not written
yet, and that assertion presupposes a trainer ran. No evidence asserts nothing at
all: the run never reached the measurement point. Reading `unknown` as `empty`
would file a run that never started as a statement about trainer timing.

Consequences when this row is drawn. B-10's ledger state is completely unchanged,
neither confirmed nor deferred nor weakened. The run's verdict belongs to whatever
blocker stopped it and not to B-10. And the run does not count against B-10's
evidence budget, so the next run still owes the cut-2 observation.

Run 5 was exactly this row, and report section 17.4 read it correctly in prose
before the row existed: no cut 2, so neither the confirmed row nor the deferral
row applies. Naming it means run 6 is read mechanically instead of relying on the
reporter noticing.

### 20.20 Amendment — the two probes do not conflict, and 20.8's mechanism was wrong

coder-user's W5 draft asserted that a child's access list is unchanged after the
repair, and it failed on the Windows host. Their isolated probe of the shipped
helper found that the immediate child **directory** keeps every entry with its
identity and mask intact, but its entries lose the inherited marking and the
child becomes protected. The grandchild directory, the child file and the deep
file are untouched. Nothing is emptied and no grant is removed.

That reads as a contradiction of B-11-M1 arm B, which reported the immediate
child directory unchanged at eleven inherited entries and unprotected. It is not
one.

#### 20.20.1 The hidden variable is the descriptor, not the call

B-11-M1's arms A to D all used the Host's **non-inheritable** descriptor,
`D:P(A;;FA;;;SY)(A;;FA;;;<sid>)`, obtained by calling the Host's own descriptor
builder and round-tripping it. Arm E was the only arm with the inheritable form,
and arm E changed the **call** at the same time. So the arms measured two
diagonal points, never the corner:

| | non-inheritable descriptor | inheritable descriptor |
|---|---|---|
| path call | arm A, destructive | arm E, benign, propagates fully |
| handle call | arm B, children untouched | **the ruled combination — unmeasured** |

Section 20.8 ruled that empty corner. coder-user has now measured it, on the
shipped helper, and it does not behave as section 20.8 predicted.

**The orthogonality claim is retired.** Section 20.8 argued that the call decides
whether children are recomputed and the descriptor decides what a recompute
produces, so the two could be combined freely. The descriptor's inherit flags
change what the handle call does to children, so the axes are not independent and
the warrant does not hold. This is the second claim of mine this section has
retired, and unlike the first it is the one my own handoff named as the risk:
the halves were measured, the whole was not, and that is exactly where it broke.

#### 20.20.2 What the combined behaviour appears to be

Read together, the two probes support one account, offered as a reading rather
than a guarantee. Setting a list that publishes inheritable entries obliges the
system to reconcile them against children that already exist. It does the least
destructive thing available at one level: instead of overwriting a child's
entries, which would lose grants, it converts that child's inherited entries to
explicit ones and marks the child protected, preserving its effective access and
removing it from the inheritance relationship. Once the child is protected there
is nothing left to reconcile beneath it, which is why the effect stops at one
level and why files, which cannot be containers for further inheritance, are not
touched.

Section 20.19.2 is the model for how much weight to put on that: it is a reading
that fits both measurements, and 20.20.4 names the one experiment that would
confirm or kill it.

#### 20.20.3 What changes, and what does not

**The ruled primitive does not change.** The handle call with the inheritable
descriptor stays. Every reason section 20.8 gave for the handle rather than the
path survives untouched, because those were about junction following and the
swap window, not about propagation. And the measured outcome is benign on the
axis that matters: no object is emptied, no grant is removed, every node stays
readable and listable.

**Section 20.8's closing sentence is struck.** "The immediate state is arm B's,
the eventual state is arm E's, and arm A's state is unreachable from either" is
false in its first two clauses. The correct statement is narrower and, on the
safety axis, stronger:

> The immediate state preserves every grant at every level. Immediate child
> directories become protected, which removes them from the repaired parent's
> inheritance relationship, so no later propagation from that parent can reach
> them — benign or destructive. Arm A's state remains unreachable, which was the
> point.

Test-host's incoherence caveat is therefore closed more firmly than section 20.8
claimed, and by a different route. Section 20.8 promised that a later propagation
would narrow the children; in fact a later propagation cannot reach them at all.

**One consequence is worth stating plainly, because it is the cost.** An
immediate child directory's grants are frozen as explicit and protected, so they
will never narrow on their own. For the model inventory that costs nothing, since
its contents are public weights verified by fingerprint.

**Two sentences that stood here are struck; see section 20.21.** They claimed the
freeze was moot for the state directory because the chain repairs it next, and
that follow-up #170 was unaffected because its subject is a file. Both are false.
The freeze on a chain member is not moot, it is disqualifying, and it is the whole
of B-11-R1. Files are converted too on the volume where the effect fires, so #170's
subject is reached after all. This is the third claim in this neighbourhood that
was asserted from a mechanism rather than measured, and the count is the point.

**W5 as coder-user rewrote it is correct and is adopted.** Pinning grant and mask
preservation plus listability is the right assertion, and it still fails on an
emptied list, which is the regression the test exists to catch. The original
"access list unchanged" wording was my error, not an implementation defect: it
encoded section 20.8's prediction rather than the property that matters.

**Run 6 row 3 does not change, and it matters more than before.** Re-verifying
the inventory after activation is now the only end-to-end check that this
one-level effect is harmless on the real tree rather than on a scratch analogue.
Add one cheap row beside it:

| Row | Observation | Reading |
|---|---|---|
| 5 | after cut 1, record the protected flag and entry count for the three chain directories and for `.synaptic\model-inventory` | the chain directories should each show the Host's two inheritable entries; the inventory should show its original entries preserved and marked explicit. Any emptied list is a stop |

The inventory half of that row is **superseded by section 20.21.8**: on `F:` the
inventory is not converted at all, so its entries stay inherited. The row as it
now stands in section 20.16 is the one run 6 is judged against.

#### 20.20.4 The measurement that would settle the mechanism

Not blocking. The shipped behaviour is already measured benign on the real
helper, and run 6 observes the real tree. But the account in 20.20.2 is a reading
of two probes taken on differently shaped trees, and this section now asserts it,
so it should be confirmed by an experiment that varies one thing:

On one tree, in the B-11-M1 harness, apply the handle call to the root twice on
two identical copies, once with the non-inheritable descriptor and once with the
inheritable one, and read back five nodes each: root, child directory, grandchild
directory, child file, deep file. If the inherit flags are the cause, the
non-inheritable copy reproduces arm B exactly and the inheritable copy reproduces
coder-user's result. If both copies show the conversion, the cause is the tree
shape or the harness and 20.20.2 is wrong.

A second, cheaper question worth the same trip: apply the full three-directory
chain repair to a tree shaped like the real one and read every node, so run 6's
row 5 has a predicted end state to be compared against rather than merely
recorded.

### 20.21 Amendment — the freeze is volume-dependent, and root-first wedges the chain permanently (B-11-R1)

Test-host's step 0 (task #174, `metadata.step0_result`; scripts and logs under
`F:\Code\scratch-b11\step0`) drove the shipped `_ensure_private_storage_directories`
on synthetic trees, three trials per variant, with the real helpers imported
read-only from the released checkout. It falsified my ordering prediction on `F:`
and confirmed the defect on the Windows temp volume. The deciding variable is
neither the order nor the descriptor. It is the volume.

#### 20.21.1 What was measured

On `F:\Code\scratch-b11\step0`, the shipped root-first order and both proposed
reorderings **all pass**, and land in an identical end state:

| Node | End state on `F:` |
|---|---|
| `.synaptic`, `state`, `docker` | protected, exactly two non-inherited entries, `SYSTEM` and the current user, `FILE_ALL_ACCESS`, flags `0x03` |
| `model-inventory` | **untouched**: not protected, 11 entries, all still inherited |
| grandchild directory | untouched, 11 inherited |
| grandchild file, immediate child file | untouched, 7 inherited |

Nothing is converted, nothing is protected, nothing is emptied, at any node
outside the chain. The inherited set `F:` carries has mixed flags: `0x13`, `0x10`
and `0x1B`.

On a tree under `C:\Users\...\AppData\Local\Temp`, the same code and the same
call **raises** `ValueError("HMAC private storage validation failed")`, three of
three. Repairing `.synaptic` converts its immediate children to explicit and
protected. `state` then arrives carrying three explicit entries, fails clauses 3
and 4 of section 20.6, is therefore not repaired, and validation rejects it.
`docker` is never reached. That volume's inherited set is three entries, all
`0x13`.

An immediate child **file**, `marker.txt`, is converted too.

#### 20.21.2 The severity: the repair creates a state its own predicate must refuse

This is worse than B-11, and the difference is worth naming precisely.

B-11 was *refused until fixed*. The operator's directory carried a state the
validator would not accept, and a fix in the Host made it acceptable. B-11-R1 is
*refused forever, and unreachable by the repair*. Once `state` has been converted
it is protected with zero inherited entries, which is exactly the shape section
20.6 rules a deliberate third-party decision. `_win_never_protected` can never
admit it again. Test-host confirmed the permanence directly: three consecutive
`ensure(repair=True)` calls on the same wedged tree all raise.

So the repair, on the affected volume, manufactures the one state its own
predicate is written to refuse, on the object it is trying to fix, and then
refuses it. The recovery the predicate leaves available is manual ACL surgery,
which the operator recipe explicitly tells operators not to perform.

The suite does not see any of this. `pytest`'s `tmp_path` lives on the volume
where the effect fires, so the Windows tests **run in the failing environment and
pass**, purely because every fixture pre-creates the chain root alone
(`test_security.py:750`, and `:864-867` adds a sibling, not a chain member) and
lets the Host create members two and three, which then carry the private
descriptor and need no repair. The environment was never the gap. The fixture was.

#### 20.21.3 Two corrections to section 20.20.2

**Files are converted.** Section 20.20.2 said files are not touched because they
cannot be containers for further inheritance. `marker.txt` was converted. The
claim is wrong, and it is wrong structurally rather than partially: containment
was the stated *reason* the effect stops at one level, and the file case shows the
effect is not about containment at all. Whatever bounds it, it is not that.

**Follow-up #170 is reached.** That follow-up records that the durable rows
database keeps inherited entries after repair. On the affected volume it does not
keep them; it gets them frozen explicit and protected when `docker` is repaired.
Neither outcome is private, so the follow-up's subject is unchanged, but its
description is now wrong on one volume class and should be restated when it is
picked up.

#### 20.21.4 What decides whether the freeze fires

**Stated as observed, because I have asserted a mechanism twice in this section
and been wrong twice.** What is measured is that two NTFS volumes on the same
machine, running the same code, differ: on one the effect fires on every
immediate child including files, on the other it fires on nothing at all.

The data supports one hypothesis worth testing, offered as a hypothesis:

> The discriminator is the **child's own descriptor control bits**, specifically
> `SE_DACL_AUTO_INHERITED` (`0x0400`), not the ACE flags and not the entry count.
> That bit is what marks an object as participating in automatic inheritance and
> therefore eligible to be recomputed when an ancestor's list changes. An object
> whose descriptor lacks it is exempt, which would explain why a whole tree on
> `F:` is inert while a whole tree on the temp volume is not, and why files behave
> the same as directories, since the bit is not about containment.

The falsifier is one cheap read: **before** repairing the parent, call
`GetSecurityDescriptorControl` on the immediate child on both volumes and compare
the `SE_DACL_AUTO_INHERITED` bit. If the temp child has it set and the `F:` child
does not, the hypothesis survives and the effect has a name. If both agree, it is
wrong and the discriminator is something else, and the honest position is the
observed one above.

The ACE-flag difference is the other candidate and I put less weight on it. `F:`
carries `0x10` entries, inherited but not inheritable, and `0x1B` entries, which
are inherit-only and do not apply to the object itself; the temp volume carries
only `0x13`. That is a real difference, but it describes what the child would
publish downward, and the effect under study is what happens **to** the child.

**Nothing in the fix depends on resolving this.** The ruling below must be, and
is, volume-independent. Detecting the volume class and branching on it is
explicitly refused: it would put a Windows-version-and-filesystem inference on the
path that decides whether private storage is private.

#### 20.21.5 Ruling — two-pass leaf-first, conditional, with a named fallback

**Repair leaf first, in a pass of its own, before the existing loop.**

Shape. Pass A, over `reversed(chain)`: if the member exists and `repair` is true,
repair it. Pass B: the existing loop at `security.py:841-855` with the `elif
repair` branch removed, so it creates missing members root first and validates
every member unconditionally and last. Evaluating existence in pass A, before any
creation, is also a more faithful reading of section 20.13 item 1 than the shipped
code: a member that exists at entry is pre-existing, one created in pass B is the
Host's own.

Why this and not a wider predicate. The predicate distinguishes states the
filesystem produced from states an actor decided. Widening it to accept the shape
the Host itself just produced would make the code unable to tell its own footprint
from a third party's, which is the tamper mask the predicate exists to prevent.
Reordering keeps the predicate exactly as it is, and section 20.6's new paragraph
records why the order is a correctness property rather than a style choice.

Why not change the descriptor. Making the repair descriptor non-inheritable would
also stop the freeze, and root-first would then work. It is refused: it reopens
section 20.8's combination, invalidates W1's flag assertions and W5's directory
clause, and discards the one property the inheritable descriptor was chosen for.
Ordering is smaller and reversible.

**This ruling is conditional, and the condition is not satisfied yet.** Variants 2
and 3 were run only on `F:`, where nothing propagates, so they demonstrated only
that the reorderings are harmless on an inert volume. The step that actually
matters — that repairing a parent leaves an **already-protected** child alone —
was never exercised, because on `F:` no child is ever protected by a repair. My
stated falsifier was not run.

The acceptance test is therefore **W6 on `tmp_path`** (section 20.21.7), which
runs on the volume where the effect fires. If W6 passes, this ruling is
confirmed by the only measurement that could have refuted it. If W6 fails, the
fallback is variant 3 and it is not a preference but a consequence: in a
straight-line chain, if a parent's write disturbs an already-protected child, then
no traversal order can avoid it, because every member except the root is some
member's child. The decision would then have to leave the loop — evaluate the
predicate on every member before any write, then repair in any order — accepting
that each write is authorised by a stale observation and that the write to member
two overwrites a protected list. **Coder-user must not choose between these.** W6
chooses.

#### 20.21.6 What the fix does not do, and the operator recovery

The fix prevents new wedges. It does not heal an existing one: a `state` that is
already protected with foreign explicit entries is refused by clause 3 whatever
the order, which is correct, because from inside the process that state is
indistinguishable from a third party's decision.

Recovery for an already-wedged tree is to **delete `.synaptic\state` and re-run**.
That is safe in the wedge scenario specifically, and the reason is worth writing
down rather than trusting: the wedge can only fire while a chain member is still
in the never-protected state, which after any successful activation it is not, so
a wedged tree has never completed an activation and therefore holds no control key
and no durable rows. If durable rows do exist, `for_docker:705-706` raises on a
missing key instead, and deletion is **not** safe. An operator who sees the cause
line naming the validator frame should check for durable rows before deleting
anything.

One cost of the ruling, on the affected volume only, stated because it is real:
repairing `docker` first converts `docker`'s own children, so the stage tree and
the durable rows database are frozen with the operator's broad entries made
explicit and permanent. Under the shipped order the pass wedged before reaching
them. This is not a regression introduced by the ordering — it is follow-up #170's
subject arriving one level deeper, and it is why 20.21.3 says that follow-up needs
restating.

#### 20.21.7 Tests

| # | Test | Asserts |
|---|---|---|
| W6 | **the whole chain pre-created by an ordinary `mkdir`**, on `tmp_path`: `.synaptic`, `state`, `docker`, plus a `stages` child and one immediate child file under `.synaptic` | `for_docker` succeeds; all three chain members end protected with exactly two non-inherited full-access entries at flags `0x03`; the non-chain child keeps every security identifier and mask it had, emptied for none. This is the acceptance test for section 20.21.5 and it must run on `tmp_path` rather than a fixture volume of its own choosing, because `tmp_path` is the volume where the effect fires |
| P4 | the same whole-chain fixture on POSIX at `0o755` | all three repaired to `0o700` and validated. Passes today; it pins the order-independence that POSIX gets for free, so a later reordering cannot quietly break it |

W1 is renamed to say **root**, not "a chain directory". Reading its current name
as chain coverage is what made this gap invisible for a whole release cycle, and a
name that overstates a fixture is a defect in the test even when the assertions are
right.

W2 through W5, the POSIX tests, the cause-line tests and D1 are unaffected, and so
is every pin in section 20.15: the reordering changes neither the predicate, the
descriptor, the validator, the refusal surface nor the error.

#### 20.21.8 Section 20.16 row 5, corrected

Row 5 predicted the inventory would end "preserved and marked explicit". On `F:`
it ends preserved and still **inherited**, because nothing propagates there at
all. The row is corrected in place, and it gains a second job: it now discriminates
which volume class the real tree is in. An inventory that comes back protected with
explicit entries means `F:` behaves like the temp volume, B-11-R1 is live on the
real tree, and that is a stop in its own right. The emptied-list stop condition is
unchanged and was unmet everywhere in step 0.

Run 6 proceeds on `F:` with the variant 1 `F:` readback of section 20.21.1 as row
5's predicted end state. B-11-R1 does not gate run 6; it gates feature closure and
the next release.

#### 20.21.9 Replacement for section 20.13 item 1

> 1. `_ensure_private_storage_directories` keeps its required keyword-only
>    `repair: bool` with no default, and splits into two passes. **Pass A**
>    iterates `reversed(chain)`; for each member that exists at entry, and only
>    when `repair` is true, it calls the repair helper. **Pass B** is the loop as
>    it stands at `security.py:841-855` with the `elif repair` branch removed: it
>    creates missing members root first and calls `_validate_private_directory` on
>    every member, unconditionally and last. No other behaviour changes. The repair
>    helper, the predicate, the descriptor, the validator and the error are all
>    untouched.

Items 2 through 9 stand as written.

#### 20.21.10 Ledger row

Row 20.5 is added to the section 20.17 table, where the rest of the ledger lives.

## 21. Amendment 2026-09-03 — ruling on B-12 (the prepared path stages the whole superproject)

Citations in this section are against Host `86e2a86c` and engine `ba844137`, the
tree this ruling was written from. Section 20 and its amendments are B-11 and
B-11-R1 and are unaffected by anything here.

### 21.1 The measurement

Run 6 (#174, report section 18) cleared B-11 on the real tree and then failed at
staging:

```
stderr| synaptic-host: START_UNAVAILABLE ValueError at synaptic_host/docker_staging.py:1299 in _git_archive
```

`_git_archive` (`docker_staging.py:1296-1300`) runs `git archive --format=tar
<commit>` over the whole repository and raises when `not raw or len(raw) >
_MAX_PROJECT_ARCHIVE_BYTES` (`:1298`, bound at `:45`). The call site is
`:1714-1717`, which archives `context.project_root` at
`source_lock.project_source.commit` into `source/project`.

| Quantity | Value |
|---|---|
| archive at `e00ab662` | 412,794,880 bytes |
| archive at `ab741054` (run 5) | 412,682,240 bytes |
| bound `_MAX_PROJECT_ARCHIVE_BYTES` | 268,435,456 bytes |
| overshoot | 144,359,424 bytes |
| `datasets/` tracked blobs | 222.2 MiB |
| `experiments/` tracked blobs | 74.1 MiB |
| `papers/` tracked blobs | 65.6 MiB |

The archive is non-empty, so it is the size half of `:1298` that fires. The run-5
checkout is over the bound too, so B-12 is latent since the path was written and
was masked by B-11, not introduced by it. It is the first platform-independent
blocker in this workstream: nothing about it depends on Windows, on the volume,
or on the ACL work of section 20.

### 21.2 Severity, and why nothing caught it

The three trees that blow the bound are the wrapping project's research corpus.
None of them is read by the trainer. The prepared path was staging 393.7 MiB of
papers and datasets to deliver, as this section establishes, one JSONL fixture.

Nothing caught it because the bound is only reachable through a real project. The
constructive tests build small trees under `tmp_path`, so the archive is
kilobytes and the predicate never fires. This is the same shape as B-11-R1's test
gap, and worth naming as a class: **a bound whose only realistic trigger is the
size of the operator's own repository cannot be exercised by a fixture that
builds the repository.** Section 21.14 rules the test that closes it.

### 21.3 What the container actually reads from `/source/project`

The sweep, since this is the fact the whole ruling turns on.

The staged tree is presented to the container as three roots. `_layout`
(`:1515-1531`) maps `source/engine` to `/source/engine` and `source/project` to
`/source/project`, both read-only, and the writable set to `/artifacts/*`.
`docker_training.py:445-457` sets `PYTHONPATH` and `SYNAPTIC_ENGINE_ROOT` to
`/source/engine` and `SYNAPTIC_PROJECT_ROOT` to `/source/project`.

**All executable code comes from the engine, never from the project.**
`PYTHONPATH` is `/source/engine` alone (asserted again at `:1689`), and the
worker's module set is projected from the locked closure
(`offline_sft_worker.py:464,500,550`), which is staged by digest from the engine
repository at `:1718-1721`.

**The model comes from the cache.** `_require_local_model_snapshot`
(`runtime_v1.py:654-659`) resolves the snapshot under `roots.cache`, which is
`/artifacts/cache`, populated by `_copy_inventory` at `:1722`.

**The control surface comes from `/source/control`,** written at `:1723-1747`:
`source-lock.json`, `storage.json`, `workload.json` as canonical bytes, and the
closure manifest. The workload is therefore delivered to the container as control
bytes, not read from the project tree.

**That leaves exactly one project read.** `runtime_v1.py:1074-1094` requires the
workload's dataset ref to start with `project://`, resolves it under
`roots.project` through `_resolve_relative` (`:909-932`), and then verifies two
things: that `dataset.revision` equals the locked project commit, and that the
file's SHA-256 equals the recorded `content_digest`. There is no directory walk of
the project root and no second read. The only other constraint on the root is
structural: `roots.engine` and `roots.project` must be distinct and must not
overlap the writable roots (`:886-906`).

The smoke workload confirms the shape: `training/smokes/docker-sft.json` names
`"dataset": {"ref": "project://training/fixtures/modal-smoke.jsonl"}` and takes
its model from a Hugging Face ref resolved out of the inventory.

**Conclusion: the container reads one file from `/source/project`.** Staging
393.7 MiB to deliver it is the defect, stated without reference to any bound.

### 21.4 Ruling

**Stage the project inputs the source lock already records, by digest, and retire
the whole-tree archive for the project.**

The scope is the set of project-relative paths carried in
`source_lock.inputs`, which `docker_training.py:278-281` populates with exactly
two descriptors, `training-config` and `training-dataset`, each built by
`_descriptor` (`:104-116`) and therefore already carrying `path`,
`git_object_id`, `size_bytes` and `sha256`.

`source/project` is created and populated with those members at their recorded
project-relative paths, each payload verified against its recorded size and
digest before it is written, and the staged tree verified to contain those
members and nothing else. `_git_archive` and the whole-tree extraction of the
project are removed from this path.

This satisfies every constraint the mission set. The subset is **derived**, from
the workload through admission, with no operator knob. It is **exact**: the lock
pins the commit, each descriptor pins the blob, and the Host now checks the blob
rather than trusting a tar. It is **reproducible**: two runs at the same lock
stage the same bytes by construction. It is **verifiable from the lock**: the
descriptors are the lock. And the bound stays real, as section 21.7 rules.

### 21.5 Why the scope is the lock's input set, not my reading of the engine

Section 21.3 establishes that today only the dataset is read. The scope ruled
above also stages the training config, which no engine read currently requires.
That is deliberate and it is the one place this ruling is not minimal.

The reason is a boundary question, not a size question. If the Host scoped to
"what I determined the engine reads", then the Host's staging correctness would
depend on the engine's internals, and the engine is a submodule that moves on its
own pin. An engine change that began reading its config from the project root
would turn a correct Host into a silently wrong one, and the failure would land
in a container, at a version boundary, far from the code that caused it. If the
Host instead scopes to "what the lock records this run as consuming", the Host
depends on a contract it owns and writes, and an engine that wants more must
either use a path the lock records or fail loudly.

The two files together are a few kilobytes. The size argument does not
distinguish them; the ownership argument does.

### 21.6 The mechanism, which is not a new one

`_git_selected_blobs` (`:1092-1105`) already runs `git archive --format=tar
<commit> -- <paths>`, the pathspec-scoped form, and already parses the result
into a path-keyed mapping. It is the mechanism the **engine closure** is staged
with. `_git_blob_metadata` (`:1049`) and `_git_blob` (`:1083`) already read a
single blob by object id at a commit with an exact size check.

So the ruling introduces no new primitive. It composes two paths this file
already proves: the pathspec-scoped read that stages the closure, and the
digest-verified write-then-reverify that `_stage_locked_closure` and
`_verify_staged_closure` (`:1259-1293`) perform. The project becomes the third
consumer of a shape that is twice-shipped, rather than the only consumer of a
whole-tree archive.

Reading by pathspec at the commit, rather than from the working tree, also keeps
the existing property that staging never depends on the state of the operator's
checkout.

### 21.7 What the bound now measures

`_MAX_PROJECT_ARCHIVE_BYTES` at `:45` stops being a bound on the operator's
repository and becomes a bound on the staged input set. It is not raised. It is
not lowered either, because a legitimate dataset can be large and the point of
the ruling is that the Host no longer has an opinion about the size of the
project.

Three checks remain and all stay real:

| Bound | Site | What it now measures |
|---|---|---|
| `_MAX_PROJECT_ARCHIVE_BYTES` | `:45` | total bytes of the staged project inputs |
| `_MAX_PROJECT_EXPANDED_BYTES` | `:46` | unchanged in meaning; now trivially satisfied |
| `_MAX_PROJECT_ENTRIES` | `:47` | number of staged project inputs |

The per-member size check is stronger than any of them, because each member's
length is compared to the size the lock recorded, which is an equality rather
than a ceiling.

### 21.8 The cause line

`:1298` and `:1304` share one message across two predicates, so run 6's cause
line named a frame but not a reason, and a human had to measure the archive to
learn which half fired. Split them.

| Condition | Message |
|---|---|
| the read produced no bytes | `exact project input is empty` |
| a member's length differs from the recorded size | `exact project input differs from its locked size` |
| a member's digest differs from the recorded digest | `exact project input differs from its locked digest` |
| the staged set does not equal the recorded set | `staged project inputs contain missing or extra files` |
| the total exceeds the bound | `exact project inputs exceed their bound` |

These are staging messages, not new result codes. The activation cause line of
section 20.11 already carries the class and the innermost frame, so the split
buys the reader the reason at no schema cost. No exception text reaches the
operator, per section 20.11, so these strings must stay free of paths and values.

### 21.9 A workload that references a path outside the scope

It cannot happen by construction, and that is the point: the scope is derived
from the workload, so the workload's own references define it. What can happen is
that a path the workload names is not a regular blob at the locked commit, and
that is already refused at admission by `_git_blob_metadata` (`:1067-1072`),
before a lock is issued.

The residual case is a **future** engine reading a project path the lock does not
record. That fails in the container with `project path reference does not exist`
(`runtime_v1.py:928`), which is loud, names the path, and is correct: the Host
did not stage it because nothing declared it. Section 21.18 records this as the
seam to watch.

### 21.10 SourceLockV1 does not change

Stated explicitly because the mission asked. **No schema change, no lock version
bump, no new field, no engine change, no closure regeneration.**

The scope is not new information. `docker_training.py:266-307` already records
every project-relative file this run touches, each as a full descriptor. The
ruling reads a field that is already written and already digested into the lock's
canonical bytes. That the answer was already in the lock is the strongest
evidence that scoping is the intended shape rather than a workaround.

`SourceLockV1.mode` stays `"superproject"` (`:259`). It describes the source
topology the lock was proved against, not the volume of bytes staged from it.

### 21.11 Rejected alternatives

| Rejected | Why |
|---|---|
| **raise `_MAX_PROJECT_ARCHIVE_BYTES`** | declined by the user on #180, and the reason holds independently: it moves the cliff instead of removing it, and makes success depend on how large the wrapping repository happens to be. The engine must be wrappable by any project, so any bound over a whole project is a bound on the user's research, which the Host has no business setting |
| **a documented project-shape precondition** | declined on #180. It exports the constraint to every wrapping project and contradicts wrappable-by-any-project. It also cannot be enforced, only documented, which makes it a class of blocker that only appears in someone else's repository |
| **`.gitattributes` `export-ignore` on the large trees** | it would work today and is one line, but it puts the Host's staging correctness in a file the wrapping project owns and can edit, and it silently changes what `git archive` produces everywhere else. Correctness must not depend on an operator-editable file that has other purposes |
| **operator-declared allowlist in the provider profile** | the lead confirmed the derived reading on #181. A declared allowlist adds a knob whose wrong setting fails inside a container, and a schema change, to express something admission already computes |
| **scope to the dataset alone** | minimal, but ties Host staging to a reading of engine internals across a submodule pin. Section 21.5 |
| **keep the whole-tree archive and stream it** | the bytes are not needed at all; making it cheaper to move them is solving the wrong problem |

### 21.12 Coder-ready specification

All changes in `synaptic_host/docker_staging.py` unless stated.

1. Add a private helper that stages the project inputs. It takes the repository
   path, the locked commit, and the input descriptors from the lock. It reads the
   members with `_git_selected_blobs` (`:1092`) using the descriptor paths as the
   pathspec, and for each descriptor compares the returned payload's length to
   `size_bytes` and its SHA-256 to `sha256` before writing. Raise the matching
   message from section 21.8 on any mismatch.
2. Write each member with `_write_new_regular` under a parent obtained from
   `_ensure_direct_parent`, and apply the file mode the same way
   `_stage_locked_closure` does at `:1273-1274`. Keep the
   `is_relative_to(destination)` escape check of `:1271-1272`.
3. Re-verify after writing, in the shape of `_verify_staged_closure`
   (`:1278-1293`): walk the staged project root, assert the set of relative paths
   equals the descriptor set exactly, and re-read each file to compare length and
   digest. The re-read is not redundant with step 1; it is what makes the staged
   tree, rather than the payload in memory, the thing that was verified.
4. Enforce the bounds of section 21.7 over the descriptor set: total bytes
   against `_MAX_PROJECT_ARCHIVE_BYTES` and count against `_MAX_PROJECT_ENTRIES`,
   before any write.
5. Replace the call at `:1714-1717` with a call to the new helper, passing
   `context.project_root`, `source_lock.project_source.commit` and the lock's
   input descriptors, and destination `source / "project"`. Keep its position:
   before `_stage_locked_closure` and `_copy_inventory`, so the ordering of the
   three staged roots is unchanged.
6. Delete `_git_archive` (`:1296-1300`) if step 5 leaves it with no callers, and
   confirm that by sweeping for the name rather than assuming. Leave
   `_extract_link_free` (`:1303-1346`) in place only if another caller exists;
   sweep for that too. Do not delete either on the strength of this sentence.
7. Split the shared messages per section 21.8. Do not add a result code, do not
   touch `cli.py`, do not change the activation cause reporter.
8. Do not change `_source_manifest` (`:1496-1512`). It digests what is staged, so
   it follows the new scope automatically, and the re-verify at `:1648-1654`
   compares it against the projection recorded from the same walk. This
   self-consistency is why no recorded digest has to be recomputed anywhere.

### 21.13 Driver and skill changes

**One driver probe, coder-workflow's.** Add a pre-run check that reports the
total size of the locked project inputs, so an operator sees the staged volume
before issuing a run rather than after a failed cut. It reports; it does not
gate, because the Host owns the refusal.

**Skill text.** The `host-docker-run` prerequisites currently say nothing about
project size, and after this ruling they should say nothing about it either. Add
one paragraph stating the opposite of what an operator might now assume: the
prepared path stages only the inputs the workload names, so the size of the
project is not a precondition and `.gitattributes` must not be used to shape it.
Canonical `.skills/` first, then the sync script.

**No change** to `run_prepared_training.py` cut handling, to
`materialize_model_inventory.py`, or to the B10-EVIDENCE line.

### 21.14 Tests

| # | Test | Asserts |
|---|---|---|
| S1 | a project whose tracked content greatly exceeds `_MAX_PROJECT_ARCHIVE_BYTES` stages successfully when its inputs are small | the acceptance test for B-12. It must build a repository whose archive exceeds the bound, which is the fixture the existing tests never built. Generate incompressible bytes rather than committing a large file |
| S2 | the staged project root contains exactly the lock's input paths and nothing else | the scope is a set equality, not a subset. This is the test that fails if a future change reintroduces a whole-tree stage |
| S3 | a descriptor whose recorded digest does not match the blob at the commit is refused | the digest check is load-bearing and is checked before the write |
| S4 | a descriptor whose recorded size does not match is refused with the size message, and an empty read is refused with the empty message | the section 21.8 split; two predicates, two distinguishable messages |
| S5 | the staged dataset is byte-identical to the blob at the locked commit, with the working tree dirtied at that path first | staging reads the commit, never the checkout |
| S6 | two consecutive stages of the same lock produce the same source manifest digest | reproducibility, and it pins that the scope itself is inside the digest |

S1 is the one that matters. Without it this ruling is verified only by tests that
could not have failed before it.

### 21.15 Pins and do-not-touch

| File | Why it stays |
|---|---|
| `synaptic-tuner/` in any form | no engine change, no allowlist, no schema, no closure regeneration |
| `synaptic_host/cli.py` | no result-schema change; section 21.8 is staging text only |
| `synaptic_host/docker_v1/composition.py` | the legacy path stays unused |
| the committed provider profile | no new field; the scope is derived, not declared |
| `materialize_model_inventory.py` | the inventory path is untouched |
| `/etc/wsl.conf` | user ruling of 2026-09-02 |
| the released checkouts and `F:\Code\scratch-b11` | preserved as evidence |

| Pin | Location | Disposition |
|---|---|---|
| source manifest digest recorded and re-verified | `:1648-1654`, `:1748-1760` | stays green; both sides derive from the same walk |
| worker closure binding | `:1738-1740` | stays green; the engine root is untouched |
| inventory staging and its cap | `:1349-1357` | stays green |
| `PYTHONPATH` equals `/source/engine` | `:1689` | stays green; this ruling makes it more true, not less |
| dual-clone roots distinct | `runtime_v1.py:886` | stays green; `source/project` still exists and is still distinct |
| constructive staging tests under `tmp_path` | the existing suite | stay green; small projects stage the same way |

### 21.16 What run 7 must observe

| Row | Observation | Reading |
|---|---|---|
| 1 | cut 1 passes staging | the acceptance row for B-12. A stage directory exists and a container reference is produced |
| 2 | the staged `source\project` tree, listed in full | it must contain exactly the two locked input paths. Anything else, and the scope is not what this section ruled |
| 3 | the staged dataset's SHA-256 | equals the `training-dataset` descriptor's `sha256` in `control\source-lock.json` |
| 4 | the container reaches the trainer and the dataset digest check passes | `runtime_v1.py:1088-1094` is the engine's independent confirmation that the scoped stage delivered the right bytes |
| 5 | everything section 20.16 rows 1 to 5 and the B-10, B-10-R1 and B-9-R1 measurements ask for | all of them have been blocked behind staging for two runs and become measurable for the first time |

Row 5 is the reason this blocker mattered: B-9's `--user`, B-9-R1's `/tmp`
caches, B-10's cut-2 evidence and B-10-R1's cache tree have never been observed,
because no container has ever been created on this path.

### 21.17 Ledger row

| Row | Content |
|---|---|
| 21.1 | B-12. `_git_archive` (`docker_staging.py:1296-1300`) staged the whole superproject at the locked commit; 412,794,880 bytes against the 268,435,456 bound at `:45`, raise at `:1299`, call at `:1714-1717`. Latent since the path was written, masked by B-11, platform-independent. The container reads exactly one file from `/source/project`, the workload's `project://` dataset (`runtime_v1.py:1074-1094`); code comes from `/source/engine`, the model from `/artifacts/cache`, the workload from `/source/control`. Fix: stage the project inputs the lock already records (`docker_training.py:278-281`), by digest, using the existing `_git_selected_blobs` and the `_stage_locked_closure` verify shape. No SourceLockV1 change, no engine change, no bound raise. The bound now measures the staged input set. Shared two-predicate messages at `:1298` and `:1304` split per section 21.8 |

### 21.18 What this ruling does not settle

**The engine could grow a project read the lock does not record.** Today the
contract is implicit: the engine happens to read only what admission happens to
record. This ruling makes the Host's half explicit and leaves the engine's half
where it was. The failure mode is loud and correct, so it is not a blocker, but
the seam is real and it is the natural subject of a later engine-side rule that
project reads must come from the recorded input set.

**Whether `git archive` at a pathspec is byte-reproducible across git versions**
is not settled and no longer matters. The ruling verifies payloads against
recorded digests and re-verifies the staged files, so reproducibility rests on
the digests rather than on the tar. That is the substantive reason to prefer the
digest-verified form over trusting a scoped archive, beyond its being the shape
already shipped twice.

**The `mode` field stays `"superproject"`.** If a future topology stages a
project that is not a superproject, that field and this scope will need to be
read together, and they are currently independent.
