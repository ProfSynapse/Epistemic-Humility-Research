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
