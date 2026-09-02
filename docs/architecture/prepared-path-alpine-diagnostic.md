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
