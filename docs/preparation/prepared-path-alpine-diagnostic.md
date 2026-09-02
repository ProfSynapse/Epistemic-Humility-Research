# Prepared-path Alpine CPU diagnostic — PREPARE (code path)

Phase: PREPARE. Feature #73, plan step 3. Owner: `preparer-path` (code path).
Peer: `preparer-host` (Windows host facts — docker.exe, npipe endpoint, Windows
Python, image availability, mount translation measurements). This document
covers the CODE PATH only.

Worktree: `/mnt/f/Code/Toolset-Training/_worktrees/ehr-submodule-cloud-api-v1-host-clean`
Branch `feat/submodule-cloud-api-v1-host-clean`, head `e1439de3`.
Engine submodule `synaptic-tuner` pinned at `aec998ee` — read, never modified.

All `file:line` citations are worktree-relative and were read from the **working
tree at head**, not from the architecture doc's `85b922fc` baseline. The
architecture doc pins its own citations to `85b922fc` and deliberately does not
re-point them (`docs/architecture/native-windows-publication-closure.md:18-40`);
where a number here differs from that document, this document is the live one.

Upstream read: `docs/preparation/native-windows-publication-closure.md`,
`docs/architecture/native-windows-publication-closure.md`,
`docs/review/native-windows-publication-closure.md`.

---

## 0. Executive summary — read this before designing

**The container's command line is not a design variable.** It is recomputed by
the Host from the engine submodule's locked closure manifest and compared for
exact equality; any deviation raises before a container is ever created.

```
    docker_staging.py:1552-1568
        expected_entrypoint = (
            worker.roots_map["engine"] / worker.entrypoint
        ).as_posix()
        expected_argv = (
            worker.interpreter,
            expected_entrypoint,
            "--canonical-workload-file", transport.path.as_posix(),
            ...
        )
    docker_staging.py:1574,1578    worker.entrypoint.as_posix() == closure.entrypoint
                                   bundle.dispatch.argv == expected_argv
    docker_staging.py:1587         raise ValueError("worker bundle differs from the locked source closure")
```

`closure.entrypoint` is read as a **git blob at the pinned engine commit** from
`tuner/runtime/manifests/offline-sft-worker-v1.json`
(`docker_staging.py:32`), whose value today is `Trainers/sft/runtime_v1.py`.
So on the prepared path the container always runs the real SFT trainer entry
point. "A tiny CPU-only Alpine workload standing in for the engine" is not
reachable by configuration.

**The artifact contract is not a presence check.** Verification delegates into
the engine and requires, among other things, an uncompressed tar carrying a
structurally valid safetensors payload, a tokenizer archive, a byte-exact copy
of the canonical workload document, and a lineage document whose embedded
execution evidence must reproduce the trainer's own argv, environment, cwd and
outputs. Details and quotes in section 2. A shell one-liner cannot satisfy it.

**Three consequences for ARCHITECT.** They are stated here rather than buried
because they change what the diagnostic is, not merely how it is built.

1. Driving the *unmodified* prepared path with a stand-in workload is not
   possible. Something must give: the engine closure, the staging equality
   check, or the definition of "the same path". Section 8, decision D1.
2. The image reference cannot be `alpine:3.20`. `docker_provider.py:15` requires
   `^\S+@sha256:[0-9a-f]{64}$`, and the interpreter is a committed absolute
   path (`training/providers/docker.json:9`, `/opt/conda/bin/python3`) that no
   plain Alpine image provides. Section 3.
3. The profile hard-codes NVIDIA at activation —
   `AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",))` is a literal at
   `docker_training.py:825`, and `--gpus driver=nvidia,device=0` is appended
   whenever the kind is `nvidia` (`docker_v1/control_private.py:396-397`). A
   CPU-only run through this path needs that literal to become profile-driven.
   Section 3, decision D3.

Everything the diagnostic is *for* — activation on the native Windows host,
`ARTIFACTS_VERIFIED`, publication through the destination registry into the
local Windows destination, the durable SQLite record, reconcile and replay — is
downstream of the container and is reachable. The obstruction is confined to
what runs *inside* the container.

---

## 1. The prepared activation path, end to end

### 1.1 Call chain

| # | Step | Location |
|---|---|---|
| 1 | Operator entry `python -m synaptic_host training run --provider docker --config … --destination …` | `synaptic_host/__main__.py:17-20` |
| 2 | Fixed-arity parse; argv must be exactly 8 tokens | `cli.py:494`, `:497`, `:500-509` |
| 3 | Docker branch dispatches in-process (no isolated child) | `__main__.py:26-32`; `cli.py:973-976` |
| 4 | Admission: authenticate ingress, load committed blobs, compile plan | `docker_training.py:535-679` |
| 5 | Resolve destination from `training/artifacts.json` at the locked commit | `docker_training.py:604-626` |
| 6 | Compile the canonical training plan through the engine resolver | `docker_training.py:648-654` |
| 7 | Resolve the offline model inventory | `docker_training.py:658-663` |
| 8 | **Activation** | `docker_training.py:733-963` |
| 9 | Stage the worker (engine source, project source, control files, artifact roots) | `docker_training.py:790-794` → `docker_staging.py:1650-1795` |
| 10 | Build the prepared Docker profile (image, runtime, workload, roots, artifact contract) | `docker_training.py:814-842` |
| 11 | Compose the Windows platform (docker.exe, npipe endpoint, CLI policy) | `docker_training.py:879-882` → `docker_prepared_composition.py:83-154` |
| 12 | Open the SQLite repository, create or load the durable preparation | `docker_training.py:875-919` |
| 13 | Phase-dispatched cut: submit / publish / reconcile | `docker_training.py:920-953` |
| 14 | Map the outcome to the outward command result | `docker_training.py:682-730`, called at `:954-963` |

### 1.2 Staging — how the engine source is placed

Staging never copies the working tree. It reconstructs both source roots from
locked git objects.

- The engine closure manifest is read as a git blob at the locked engine commit;
  the source path is the module constant `docker_staging.py:32`
  (`tuner/runtime/manifests/offline-sft-worker-v1.json`).
- The manifest is validated for canonical form, exact field set, a recomputed
  self-digest, sorted unique members, and matching `member_count` /
  `payload_bytes` totals (`docker_staging.py:1146-1221`). Today: 66 members,
  683 234 payload bytes, closure digest `eeba2f42…41d7d3`, entrypoint
  `Trainers/sft/runtime_v1.py`.
- Every declared member is fetched by `git archive` and re-hashed;
  mismatch raises `"locked worker member differs from its declaration"`
  (`docker_staging.py:1230`).
- Members are written and then re-read from disk and compared on size, sha256
  and mode (`_verify_staged_closure`, `docker_staging.py:1278-1294`).
- The project tree is a link-free tar extraction of `git archive` at the locked
  project commit (`docker_staging.py:1693-1696`).

Stage layout, below the project root:

```
.synaptic/state/docker/stages/<stage_key>/source/engine     locked closure  -> /source/engine
.synaptic/state/docker/stages/<stage_key>/source/project    locked project  -> /source/project
.synaptic/state/docker/stages/<stage_key>/source/control/   6 control files -> /source/control
.synaptic/state/docker/stages/<stage_key>/artifacts/{artifacts,cache,state,tmp,tracking}  -> /artifacts
```

`_ARTIFACT_DIRECTORY_NAMES` at `docker_staging.py:49`; all but `cache` must be
empty (`:50`). `stage_key` is content-addressed over eight digests
(`docker_staging.py:1745-1754`), and promotion is a rename with
`except FileExistsError: pass` (`:1776-1784`), after which `_verify_reuse`
re-reads a pre-existing stage byte for byte (`:1611-1648`).

Control files are exactly six and an extra or a missing one raises
`"Docker control stage contains missing or extra files"`
(`_verify_control_files`, `docker_staging.py:1591-1609`):
`source-lock.json`, `storage.json`, `workload.json`, `source-manifest.json`,
`preparation-projection.json`, `offline-sft-worker-v1.json`.

### 1.3 What the container is given

There is **no `docker run`**. The verbs are `create` then `start`
(`docker_v1/model.py:1011-1018`). The create argv is built once at
`docker_v1/control_private.py:391-414` and independently re-parsed by
`_validate_create_command` (`docker_v1/cli.py:79-201`) before any subprocess
runs.

| Aspect | Value | Location |
|---|---|---|
| Executable | absolute Windows `docker.exe`, discovered from `PATH`, exactly one candidate required | `docker_prepared_composition.py:107-121` |
| Endpoint | `--host npipe:////./pipe/dockerDesktopLinuxEngine`, context `desktop-linux` | `docker_v1/endpoint.py:16`; re-asserted `docker_prepared_composition.py:143`; rendered `docker_v1/cli.py:788-793` |
| Image | the **digest alone** is passed positionally, plus `--pull never` | `control_private.py:412`, `:392`; validated `cli.py:193` |
| Mounts | exactly two `--mount` binds; no `-v` anywhere in `synaptic_host/` | `control_private.py:403-407` |
| — source | `\\wsl.localhost\<distro>\mnt\<drive>\…\source` → `/source`, `readonly` | `control_private.py:404-405` |
| — artifacts | `…\artifacts` → `/artifacts`, read-write | `control_private.py:406-407` |
| Network | `--network none` | `control_private.py:393`; also `create.py:420`, `control_contract.py:583`, `docker_provider.py:119-120` |
| User | **absent** — no `--user`, `--read-only`, `--cap-drop`, `--security-opt`, `--pids-limit`, `--entrypoint` | verified absent across `synaptic_host/` |
| Working dir | `--workdir /artifacts/tmp`; must start with `/artifacts/` | `control_private.py:408`; `:337`; `cli.py:166-172` |
| Env | one `--env KEY=VALUE` per entry, sorted, ≤64 entries, ≤4096 bytes each | `control_private.py:410-411`; `cli.py:179-191` |
| CPU / memory | `--cpus 1`, `--memory 17179869184` | `control_private.py:393-394`; `training/providers/docker.json:30`, `:32` |
| GPU | `--gpus driver=nvidia,device=0` when kind is `nvidia` | `control_private.py:396-397`; kind is the literal at `docker_training.py:825` |
| Labels | 15 owned `--label` pairs | `control_private.py:399-402` |
| Command | `workload.arguments` = `tuple(bundle.dispatch.argv)` | `control_private.py:413`; `docker_training.py:828` |

Mount translation is two hops, both in `synaptic_host/docker_v1/prepared.py`:

```
    prepared.py:44-51
    def _wsl_path(path: Path) -> str:
        value, drive = path.as_posix(), path.drive
        if len(drive) != 2 or drive[1] != ":" or not value.startswith(drive + "/"):
            raise ValueError("prepared Docker stage requires a Windows drive path")
        ...
        return f"/mnt/{drive[0].lower()}/{relative}"

    prepared.py:223
    unc = "\\\\wsl.localhost\\" + self._distro + request.posix_path.replace("/", "\\")
```

This is the check that makes the whole activation unreachable on Linux. The
harder gate fires earlier, at `docker_prepared_composition.py:93-97`:

```
    if (
        os_name != "nt" or docker_policy_ref != "docker-desktop-windows-v1"
        or type(wsl_distro) is not str or not wsl_distro
    ):
        raise ValueError("Windows Docker Host policy is unavailable")
```

### 1.4 The prepared command is never logged

There is no `logging`, no `logger`, and no `print` on this path. The argv is
never persisted in plaintext. Everywhere it is durably recorded it is a digest:
`docker_arguments_projection_digest_v1` hashes each argument individually and
then hashes the list (`docker_v1/control_contract.py:1233-1243`), consumed at
`docker_v1/create.py:406` and `docker_v1/cli.py:495`. Process output is retained
only as `stdout_size` / `stdout_digest` / `stderr_size` / `stderr_digest`
(`docker_v1/cli.py:794-806`).

### 1.5 The ARTIFACTS_VERIFIED gate and reconcile

`reconcile` is a one-cut-per-call state machine
(`docker_execution.py:1135-1218`). Ordered branches on the freshly loaded
record:

| Entry phase | Action | Writes | Location |
|---|---|---|---|
| `ARTIFACTS_VERIFIED` | publish | nothing (record stays verified) | `:1137`, `:1156-1159` |
| `PROCESS_SUCCEEDED` | verify artifacts | `ARTIFACTS_VERIFIED` on success, `PROCESS_FAILED` on INVALID, nothing on UNCERTAIN | `:1160`, `:1172-1177`, `:1167-1171`, `:1165-1166` |
| `LOOKUP_CREATE` / `LOOKUP_START` | re-run the same invocation, re-read | via the aggregate repository | `:1185-1189`, `:1115-1133` |
| `SUBMITTED`, or `RECONCILE_REQUIRED` + `OBSERVE_PROCESS` | observe the process | `PROCESS_SUCCEEDED` / `PROCESS_FAILED`, or `RECONCILE_REQUIRED` | `:1190-1216` |
| anything else | `from_record` | nothing | `:1218` |

So the verify cut and the publish cut are **always different calls**. Calling
reconcile once and reading `published == False` is the correct behaviour of a
healthy system, and the architecture doc names this as the most likely way the
smoke gets misread
(`docs/architecture/native-windows-publication-closure.md:1315-1322`).

The publication-absent branch is at `docker_execution.py:1138-1155`, ending:

```
    docker_execution.py:1153-1155
                return DockerPreparedRunOutcomeV1.from_reconcile_directive(
                    current, "PUBLICATION_COMPOSITION_ABSENT"
                )
```

`from_reconcile_directive` (`docker_execution.py:252-282`) is the only factory
whose reported phase differs from the record's; it drops the exit code and the
five-artifact inventory because the outcome invariant forbids them outside
`ARTIFACTS_VERIFIED`, and writes nothing durable.

The outward mapping requires three things for `SUBMITTED`, not two
(`docker_training.py:715-719`):

```
    submitted = (
        not outcome.reconcile_required
        and outcome.container_ref is not None
        and outcome.submitted_at is not None
    )
```

### 1.6 Publication and the durable record

Lazy, phase-gated construction at `docker_training.py:927-949`: the publication
is built only in the `ARTIFACTS_VERIFIED` branch and closed in a `finally`.
`compose_docker_publication_v1` (`docker_publication.py:442-489`) refuses
outright unless the loaded phase is already verified — `_verified_record` raises
`ARTIFACTS_UNVERIFIED` at `docker_publication.py:132-139`.

Its configuration is read out of the already-built prepared stage, so no
configuration file participates in the wiring
(`_configuration_for_request`, `docker_publication.py:342-351`):
`source/project/training/artifacts.json` and `source/control/storage.json`.
The binding is re-validated at `docker_publication.py:354-372`, and re-checked
again inside `publish` (`:393-407`).

`compose_host_publication_v1` (`publication_composition.py:416`) assembles:

| Component | Location |
|---|---|
| Platform port factory on `os.name == "nt"` | `publication_composition.py:394-413` |
| `LocalFilesystemV1(_local_filesystem_port_v1(), storage)` | `publication_composition.py:454` |
| `acquire_local_artifact_spool_v1` | `publication_composition.py:464` |
| `ImmutableArtifactDestinationRegistryV1` | `publication_composition.py:489` |
| `SqlitePublicationStoreV1.from_context(context)` | `publication_composition.py:500` |

The durable record is a SQLite row in `publication_records_v1`
(DDL `publication_store.py:164-180`, insert `:229-244`), with an index on
`(destination_ref, publication_id)` at `:179-180`. A second table,
`publication_ownership_nonces_v1`, backs transfer (`:181-189`). **No new table
is needed for the diagnostic.**

Replay idempotency rests on five independent mechanisms: optimistic
concurrency on every write (`docker_execution.py:1059-1065`), a closed
transition table (`docker_execution_state.py:690-735`, enforced inside the
SQLite transaction at `sqlite_repository.py:898`), phase-guarded dispatch,
single-shot invocations plus admission dedup
(`docker_v1/control_private.py:175-186`; `docker_execution.py:425-471`), and
content-addressed staging with byte-equality reuse verification
(`docker_staging.py:1611-1648`).

### 1.7 Every seam where "the engine" is assumed

This is the table ARCHITECT needs most.

| # | Seam | Where it binds | Changeable without touching the submodule? |
|---|---|---|---|
| S1 | Container **entrypoint** = `<engine root>/<closure entrypoint>` | `docker_staging.py:1552-1554`, `:1574` | **No.** Read from the engine manifest blob at the pinned commit. |
| S2 | Container **argv** must equal the recomputed tuple exactly | `docker_staging.py:1555-1568`, `:1578`, raise `:1587` | **No**, while S1 stands. |
| S3 | **Closure manifest source path** | `docker_staging.py:32` | No. Host constant naming an engine file. |
| S4 | **66 closure members** re-hashed against the manifest | `docker_staging.py:1230` | No. |
| S5 | **Interpreter** `/opt/conda/bin/python3` | `training/providers/docker.json:9`; `docker_provider.py:105-107` | **Yes.** Committed project config; must be absolute. |
| S6 | **Image** must be `ref@sha256:<64hex>` | `docker_provider.py:15`, `:100`; split `docker_training.py:799` | **Yes.** Committed project config. |
| S7 | **Accelerator kind** literal `nvidia` | `docker_training.py:825` | Host code change. Profile allows only `["nvidia"]` (`training/providers/docker.json:24-26`). |
| S8 | **Artifact roles** — Host substitutes its own five-tuple, discarding the smoke's `required_kinds` | `docker_training.py:47-50`, `:528-531` | Host code change. |
| S9 | **Inventory file** `state/runtime-v1-inventory.json` | `docker_execution.py:855` | No. Engine writes it. |
| S10 | **Inventory schema** `synaptic-artifact-inventory/v1`, exactly 3 keys, exactly 5 rows | `docker_execution.py:883-899` | No. |
| S11 | **`SFT_ARTIFACT_CONTRACT`** imported from the engine and used unconditionally | `docker_execution.py:851`, `:972` | No. Hard import of an SFT-specific constant. |
| S12 | **`WorkloadBindingVerifier`** semantic checks (5 of them) | `docker_execution.py:965-974`; engine `verification.py:201-280` | No. |
| S13 | **Closure manifest runtime path** `/source/control/offline-sft-worker-v1.json` bound into the lineage check | `docker_execution.py:967-969` | No. |
| S14 | **Artifact byte caps** from the profile | `docker_execution.py:856-857` | Yes, config. |

S1, S2, S9–S13 are the hard set. They are all rooted in the engine submodule or
in Host code that names engine constants.

---

## 2. The engine contract a stand-in must reproduce

Verification runs entirely Host-side after the container exits, in
`_DockerPreparedArtifactVerifierV1.verify` (`docker_execution.py:840-1012`).

### 2.1 Stage 1 — the inventory file

Path is fixed: `docker_execution.py:854-855`

```
        root = request.staging.artifact_root
        inventory_path = root / "state" / "runtime-v1-inventory.json"
```

Read with a hard 262 144-byte cap and a re-stat of the whole directory chain
before and after (`docker_execution.py:858-861`). Then, quoted in full
(`docker_execution.py:877-899`):

```
            document = json.loads(raw_inventory.decode("utf-8"))
            canonical = json.dumps(
                document, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
            if canonical != raw_inventory or set(document) != {
                "schema_version", "workload_fingerprint", "artifacts"
            } or document["schema_version"] != "synaptic-artifact-inventory/v1" or (
                document["workload_fingerprint"]
                != request.staging.worker_bundle.workload_fingerprint
            ):
                raise ValueError
            rows = document["artifacts"]
            if type(rows) is not list or len(rows) != 5:
                raise ValueError
            entries = tuple(ArtifactEntry(
                row["role"], row["path"], row["sha256"], row["size"]
            ) for row in rows if type(row) is dict and set(row) == {
                "role", "path", "sha256", "size"
            })
            if len(entries) != 5 or sum(item.size for item in entries) > maximum_total:
                raise ValueError
```

So: **byte-exact canonical JSON** (no trailing newline, sorted keys, compact
separators), exactly three top-level keys, the schema literal, the run's own
`workload_fingerprint`, and exactly five rows each with exactly four keys.

### 2.2 Stage 2 — the verification matrix

The result type refuses anything but a five-role tuple in this exact order
(`docker_execution.py:708`, `:714-719`):

```
            or verified != (len(self.artifacts) == 5 and type(self.inventory_digest) is str)
            ...
            or (
                verified and tuple(item.role for item in self.artifacts) != (
                    "final_model", "tokenizer", "training_lineage",
                    "training_metrics", "workload_record",
                )
            )
```

The order is a Host-side normalisation — the artifacts are re-sorted
alphabetically by role at `docker_execution.py:1006-1008` — so the engine may
emit in any order.

### 2.3 Stage 3 — integrity and semantics, in the engine

`docker_execution.py:965-974` hands everything to the engine:

```
            report = VerificationService(WorkloadBindingVerifier(
                closure_digest=request.preparation.stage.worker_source_closure_digest,
                closure_manifest_path=(
                    request.staging.worker_bundle.closure_manifest_runtime_path.as_posix()
                ),
            )).verify(
                provider_completed=True, process=ProcessResult(0),
                workload=workload, contract=SFT_ARTIFACT_CONTRACT,
                inventory=inventory, reader=reader,
            )
```

`VERIFIED` requires all of: inventory valid, integrity valid, **semantic checks
non-empty and all passed** (`synaptic-tuner/tuner/runtime/verification.py:1167-1180`).

The five semantic checks are
`synaptic-tuner/tuner/runtime/verification.py:274-280`:

| Check | Requirement |
|---|---|
| `workload_record_exact` | artifact bytes `== workload.canonical_bytes`, byte for byte (`verification.py:216-221`) |
| `lineage_binds_workload` | canonical-JSON lineage document passing `_validate_lineage_document` (`:237-242`) |
| `final_model_semantic` | `_validate_sft_archive(model_raw, "model", locked_model_ref=…)` (`:251-254`) |
| `tokenizer_semantic` | `_validate_sft_archive(tokenizer_raw, "tokenizer")` (`:261-263`) |
| `model_tokenizer_disjoint` | both valid, bytes differ, and member-name sets are disjoint (`:266-271`) |

### 2.4 What `_validate_sft_archive` demands

`synaptic-tuner/tuner/runtime/verification.py:793-937`. An **uncompressed tar**
(`tarfile.open(..., mode="r:")`, `:804`), every member a regular file with a
single flat path component, unique, non-empty, size-bounded (`:808-822`).

For `final_model` (`:830-862`, `:888-936`):

- Every member name must be in `_MODEL_CONFIGS`, `_MODEL_OPTIONAL`, be a
  safetensors index, or match `_MODEL_PAYLOAD`; otherwise reject (`:832-833`).
- Exactly one of `adapter_config.json` XOR `config.json` (`:889-892`).
- With `adapter_config.json`: `peft_type == "LORA"` and
  `base_model_name_or_path` equal to the locked model ref
  (`_valid_model_config`, `:947-952`).
- Payload names must match the chosen family, and unsharded means exactly
  `{family}.safetensors` with no index (`:893-896`, `:935-936`).
- Payloads are parsed as real safetensors streams
  (`_valid_safetensors_stream`, `:1047`), returning the contained tensor names
  and byte total; a sharded set must have a consistent index whose `weight_map`
  matches the per-shard tensor sets exactly (`:899-934`).

For `tokenizer` (`:863-885`): names restricted to
`_TOKENIZER_CONFIGS | _TOKENIZER_PAYLOADS | _TOKENIZER_OPTIONAL`, with
`_valid_tokenizer_config`, `_valid_tokenizer_json` and `_valid_tokenizer_sidecar`
applied per name.

Both return `bool(configs and payloads)` (`:937`) — a config **and** a payload
are both required.

### 2.5 What the lineage document demands

`_validate_lineage_document_unchecked`
(`synaptic-tuner/tuner/runtime/verification.py:358-394`): exactly nine top-level
keys, schema `synaptic-sft-training-lineage/v1`, the run's
`workload_fingerprint`, the workload's own `execution_source`,
`configuration_revision` and `identities` echoed back, `trainer_exit_code == 0`,
and `execution_evidence_sha256` equal to the sha256 of the canonical JSON of the
embedded evidence.

`_validate_execution_evidence` (`:397-448`) then requires exactly eleven keys,
`model` / `dataset` / `sft` deep-equal to the workload's configuration document
with JSON type equality, a non-empty string `argv` list, dict `environment` and
`outputs`, and `result == {"exit_code": 0, "status": "completed"}`. It finishes
in `_validate_evidence_paths_and_argv` (`:560`), which reconstructs the expected
trainer argv (`_expected_trainer_argv`, `:660`) and the observed runtime roots
(`_observed_runtime_roots`, `:482`), and pins
`"SYNAPTIC_WORKER_CLOSURE_MANIFEST": closure_manifest_path` (`:644`).

**Assessment.** Every field is derivable inside the container: the workload
document is mounted at `/source/control/workload.json`, the closure digest and
manifest path arrive as `SYNAPTIC_WORKER_CLOSURE_DIGEST` and
`SYNAPTIC_WORKER_CLOSURE_MANIFEST`, and the process knows its own argv, cwd and
environment. A stdlib-only Python writer could emit all five artifacts —
safetensors is a JSON header plus a length prefix, and `tarfile` and `json` are
in the standard library. What it could **not** do is *be* the process: argv is
pinned to the real entrypoint by S1/S2, and `_expected_trainer_argv` will be
reconstructed from the workload, so the evidence must report the trainer's argv
regardless of who writes it.

---

## 3. Existing opt-in, flag and command surfaces

### 3.1 There is no flag surface

`cli.py` has **no argparse**. The parser is fixed-arity
(`cli.py:494`, `:497`):

```
    if len(argv) != 8 or argv[:2] != ["training", "run"]:
        return None
```

and the option loop is `for index in range(2, 8, 2)` over exactly
`{--provider, --config, --destination}` (`cli.py:500-509`). **There is no
`--dry-run`, `--smoke` or boolean flag of any kind.** Adding a fourth option
means changing both the length check and the loop bound.

No `SYNAPTIC_*` opt-in environment variable is read anywhere under
`synaptic_host/`. Environment reads are allowlists for subprocesses only
(`cli.py:624-633`, `docker_prepared_composition.py:98`,
`docker_staging.py:1014-1019`, `security.py:839`).

The one existing opt-in precedent in the repository is a test gate:
`tests/synaptic_host/test_cold_bootstrap.py:963-966` skips unless
`SYNAPTIC_RUN_WSL_LAUNCHER_INTEGRATION == "1"`.

### 3.2 Image, executable and endpoint selection

| What | How | Location |
|---|---|---|
| Image | committed blob, digest-pinned | `training/providers/docker.json:5`; regex `docker_provider.py:15`; enforced `:100`, `:165` |
| Interpreter | committed blob, must be absolute | `training/providers/docker.json:9`; `docker_provider.py:105-107` |
| docker.exe | discovered from `PATH`, exactly one candidate, must be absolute and named `docker.exe` | `docker_prepared_composition.py:107-121` |
| Endpoint | `docker context inspect` probe, then exact-descriptor re-assertion | `docker_v1/endpoint.py:62-94`; `docker_prepared_composition.py:140-146` |
| Policy / distro | committed blob | `training/providers/docker.json:37-40` |

Three injection seams already exist on the platform factory and are exercised by
tests today: `os_name`, `executable_candidates`, `endpoint_resolver`
(`docker_prepared_composition.py:86-87`, used at `:113`, `:137`; tests at
`tests/synaptic_host/test_docker_prepared_composition.py:271-318`). **This is
the natural attachment point for a diagnostic opt-in that must not weaken the
production gate.**

### 3.3 The destination registry and the local-Windows destination

There is exactly **one** destination declared
(`training/artifacts.json:6-8`): `destination_ref` `local-default`,
`adapter_ref` `host.local/v1`. Admission is by adapter ref plus configuration
schema version, with no platform check
(`artifact_destinations.py:528-530`):

```
            registration = by_ref.get(declaration.adapter_ref)
            if registration is None or registration.configuration_schema_version != declaration.configuration_schema_version:
                raise ValueError("destination adapter registration is missing or incompatible")
```

**There is no separate local-Windows destination and none is needed.** Windows
is selected at runtime by `os.name` inside the publication composition
(`publication_composition.py:394-413`), beneath a single destination ref. This
matches the architecture doc's provider-neutrality ruling
(`docs/architecture/native-windows-publication-closure.md:196-200`). A
diagnostic that adds a Windows-specific destination would break that ruling.

Storage roots relevant here (`training/storage.json`):

| root_ref | location | lines |
|---|---|---|
| `artifact-local-default` | `project://.synaptic/artifacts` | 23-27 |
| `artifact-publication-control` | `project://.synaptic/publication-control` | 29-33 |
| `artifact-publication-spool` | `project://.synaptic/publication-spool` | 35-39 |
| `docker-model-inventory-source` | `project://.synaptic/model-inventory` | 41-45 |

`_PUBLICATION_SPOOL_ROOT_REF = "artifact-publication-spool"` at
`docker_training.py:57` is the only Host-side name for the spool.

---

## 4. Legacy surfaces to avoid

### 4.1 `synaptic_host/docker_v1/composition.py`

525 lines. Docstring line 1: *"Closed production composition for the same-process
Docker host facade."* Public surface: `DockerHostCompositionCodeV1` (`:86`),
`DockerHostCompositionErrorV1` (`:92`), `DockerHostCompositionRequestV1`
(`:133`), `compose_docker_host_v1` (`:466`). It exports nothing —
`__all__: tuple[str, ...] = ()` at `:525`.

**No production module imports it.** Every call site is a test:

| file:line | what |
|---|---|
| `tests/synaptic_host/docker_v1/test_composition.py:9`, `:13-17` | imports |
| `tests/synaptic_host/docker_v1/test_composition.py:161, 217, 247, 255, 443, 488` | six calls |
| `tests/synaptic_host/docker_v1/test_real_docker_wsl.py:31-34`, `:429` | import and one call |

`_activate_docker_training_v1` does **not** reach it. The activation imports
only `docker_prepared_composition` (`docker_training.py:767-770`), which imports
eleven `docker_v1` submodules at `docker_prepared_composition.py:23-51` —
`composition` is not among them. The other production `docker_v1` consumers are
`docker_execution.py:39-59` and `docker_execution_state.py:20`, also not
`composition`.

**How the new path avoids it:** by changing nothing. The prepared path is
already disjoint. The only way to reintroduce it is to import
`compose_docker_host_v1` deliberately.

### 4.2 The legacy Alpine Docker test

`tests/synaptic_host/docker_v1/test_real_docker_wsl.py`, 469 lines, **one test**:
`test_released_facade_starts_real_offline_pinned_container` (`:345`).

What it exercises: `compose_docker_host_v1(request)` (`:429`) — the dead legacy
facade — then `facade.start_run()` (`:433`), asserts phase `queued` (`:450`),
`docker wait` (`:453`), exit code 0 (`:455`), and that the artifact bytes
round-tripped (`:456`).

Workload (`:117-123`):

```
        (
            "sh",
            "-c",
            "cat /source/member-0000 > /artifacts/result; sleep 2",
        ),
```

Image `DockerImageV1("alpine:3.20", _IMAGE_DIGEST)` (`:140`) — note **ref and
digest as separate fields**, not the single `@sha256:` string the production
profile regex demands. CPU-only via `AcceleratorDeviceRequestV1("cpu", (), ())`
(`:143`).

Skipped by default (`:339-344`):

```
    @pytest.mark.skipif(
        os.name != "posix"
        or "WSL_INTEROP" not in os.environ
        or not _DOCKER_EXE.is_file(),
        reason="real Docker Desktop WSL integration",
    )
```

**Why it is not an acceptance gate for this work**, four independent reasons:

1. It drives the **legacy facade**, not the prepared path (§4.1).
2. It builds its endpoint descriptor by hand (`:271-282`), bypassing the
   `docker context inspect` probe that production requires.
3. It uses `wsl_distro="Ubuntu-22.04"` (`:266`), not the committed
   `docker-desktop`.
4. Its gate requires a **POSIX** process (`os.name != "posix"` skips), which is
   the opposite of the native-Windows-Host lane this feature exists to close.

It is, however, the **only** existing proof in the repository that a real
container can be created and started from this codebase, and its argv shape is a
useful reference for what a CPU-only container looks like.

---

## 5. Secrets hygiene

| Channel | Exposure | Guard | Location |
|---|---|---|---|
| Prepared argv `--env KEY=VALUE` | plaintext in the Windows process table during `docker create` | value set is closed: exactly `bundle.dispatch.environment`, `overrides=()` | `control_private.py:410-411`; `docker_prepared_composition.py:210-216` |
| Worker environment | — | forbidden-name frozenset checked at staging | `docker_staging.py:51-53`, `:1579-1582`, raise `:1587`; engine twin `tuner/runtime/dispatch.py:46-48`, `:166-167` |
| Secret requirements | — | digest over a document with `"secrets": []`, bound into plan and profile | `docker_training.py:479-483`, `:809-812` |
| Staged source | a **committed** credential in the project repo would be staged into `/source/project` | sources are locked git objects only, never the dirty tree; no content scan | `docker_staging.py:1693-1700` |
| Git subprocesses | credential helper / prompt | whitelist env, `GIT_TERMINAL_PROMPT=0`, `GIT_CONFIG_*` → `os.devnull` | `docker_staging.py:1012-1029` |
| Remote git reads | network-touching | stricter env, `stdin=DEVNULL`, `timeout=20`, 4096-byte bound; `ls-remote --refs` only | `security.py:836-861` |
| Tracebacks / reprs | argv and env values | `__repr__` returns `"…(<redacted>)"`; `__reduce__` and `__deepcopy__` raise | `control_private.py:68-77`, `:152-164`, `:247-259` |
| `docker inspect` read-back | container env values | stored as `key_digest` + `value_digest` only | `docker_v1/control_model.py:153-177` |
| Docker CLI process env | ambient `DOCKER_*`, `HF_TOKEN` | exactly four keys handed to `docker.exe` | `docker_prepared_composition.py:98-103` |
| Destination configuration | credential-shaped keys | banned-name tables and recursive rejection | `artifact_destinations.py:32-41`, `:84-93` |
| SQLite | argv | digest-only; the sole plaintext blob is `submit_command_base64`, the Synaptic submit command, not the docker argv | `docker_execution_state.py:217-219` |

**What the diagnostic must preserve.** Four properties, each of which a careless
diagnostic could silently break:

1. `--network none` and the empty secret-requirements digest. A diagnostic that
   needs to reach a registry would have to weaken one of them.
2. The closed environment set. Adding a `SYNAPTIC_DIAGNOSTIC=1` container
   environment variable changes `dispatch.environment`, which changes
   `projection_sha256`, which changes `stage_key` and the workload fingerprint.
   That is not a hazard, but it means the diagnostic and production runs are
   different stages by construction, which is a property worth stating rather
   than discovering.
3. Digest-only durable state. Nothing about the diagnostic may persist the argv
   in plaintext.
4. The redacted `__repr__` / raising `__reduce__` trio. A diagnostic that adds a
   debug print of a create invocation defeats them.

One residual, not introduced by this work: a secret embedded in the operator's
own submit command lands base64-encoded in `provider_preparations.record_json`.

---

## 6. The two queued host probes

Both are recorded in `docs/review/native-windows-publication-closure.md:147` and
`:162`, and both sit in the deferred ledger at `:168`.

### 6.1 Probe A — `STATUS_NO_SUCH_FILE` from a handle-relative open

**The code whose correctness depends on it.** `_PATH_INVALID_STATUSES` is a
closed frozenset of exactly four statuses
(`synaptic_host/local_io_v1/windows.py:193-198`), populated from the constants at
`:177-182`:

```
    _STATUS_OBJECT_NAME_NOT_FOUND = 0xC0000034
    _STATUS_OBJECT_PATH_NOT_FOUND = 0xC000003A
    _STATUS_FILE_IS_A_DIRECTORY   = 0xC00000BA
    _STATUS_NOT_A_DIRECTORY       = 0xC0000103
```

`STATUS_NO_SUCH_FILE` (`0xC000000F`) **is not defined anywhere in the module**.
The status mapping at `windows.py:570-581` routes anything unnamed to
`IO_FAILED`, which is the deliberate post-B-1 shape
(`docs/architecture/native-windows-publication-closure.md:1024-1034`).

The dependent predicate is `stat_at` (`windows.py:1050-1083`):

```
            except LocalIOErrorV1 as error:
                if error.code is LocalIOCodeV1.PATH_INVALID:
                    continue
                raise
```

with the closing reasoning at `:1077-1083`: both passes reporting
`PATH_INVALID` can only mean absent.

**What each outcome changes.**

| Outcome on the host | Consequence |
|---|---|
| `NtCreateFile` **cannot** return `STATUS_NO_SUCH_FILE` for a missing name opened relative to a directory handle on local NTFS | Nothing changes. The frozenset is complete; the residual retires. |
| It **can** | A legitimate absence raises `IO_FAILED` instead of returning `None`. This is a **broken flow, not a security hole** — `stat_at` fails closed rather than reporting a present object as absent. The fix is to add `0xC000000F` to `_PATH_INVALID_STATUSES` at `windows.py:193-198` and name the constant at `:177-182`. |

**How TEST settles it during the real run.** The publication path calls
`stat_at` on names that do not yet exist during the create-commit sequence, so a
real Windows publication that completes without an unexplained `IO_FAILED` is
evidence for the first outcome. A direct probe is cheaper and unambiguous: open
a known-missing name relative to a retained directory handle and read the raw
NTSTATUS before it is mapped.

### 6.2 Probe B — `ntpath.realpath` and the extended-length prefix

**The code whose correctness depends on it.** The two-separator refusal is a
single helper (`synaptic_host/local_io_v1/config.py:44-55`):

```
    def _opens_on_two_separators(value: str) -> bool:
        """Report whether a path's string form opens on two separators.
        ...
        """
        return len(value) >= 2 and value[0] in "\\/" and value[1] in "\\/"
```

applied to the **project root itself**, once, above the arm split
(`config.py:113-119`):

```
            if (
                type(raw) is not bytes
                or not project_root.is_absolute()
                or _opens_on_two_separators(str(project_root))
                or len(raw) > _MAX_CONFIG_BYTES
            ):
                raise _closed(LocalIOCodeV1.CONFIG_INVALID)
```

and again to a non-`project://` location at `config.py:159-160`.

The helper's docstring names the extended-length prefix `\\?\C:\...` as one of
the four refused families (`config.py:49`). The security reviewer's note
records the residual: that form is refused as an anchor but is believed
unreachable *because* `ntpath.realpath` strips the prefix — read from CPython
3.12 source, not measured on the host
(`docs/review/native-windows-publication-closure.md:162`).

The project root reaches this code having been through `resolve()`:
`Path(__file__).resolve()` at `synaptic_host/__main__.py:19` and
`Path(project_root).resolve(strict=True)` at `docker_training.py:567`.

**What each outcome changes.**

| Outcome on the host | Consequence |
|---|---|
| `ntpath.realpath` **never** emits `\\?\` for a drive-letter project root | Nothing changes. The refusal stays unreachable for legitimate roots and keeps its value against a configured UNC. Residual retires. |
| It **can** emit `\\?\` (for example on a path near `MAX_PATH`, or under a specific volume or mount configuration) | A **legitimate drive-letter project root is refused at config parse** with `CONFIG_INVALID`, and every publication on that host fails before any I/O. This is a false refusal, an availability defect. The fix would be to strip a leading `\\?\` on the drive-letter form before the two-separator test, keeping the UNC and device-namespace refusals intact. Note S-3 already flags the docstring's over-generalisation for this exact form (`docs/review/…:162`). |

**How TEST settles it during the real run.** Print `os.path.realpath` and
`Path(...).resolve()` of the project root on the Windows host, including a
deliberately long path, and assert the result does not open on two separators.
This costs one line and needs no container.

---

## 7. Test landscape

### 7.1 Files on the activation and publication path

| File | tests | Gating |
|---|---|---|
| `tests/synaptic_host/test_docker_training.py` | 14 | none; module-scope autouse import-isolation fixture at `:48-124` |
| `tests/synaptic_host/test_docker_prepared_composition.py` | 17 | none; Windows factory tested by injection at `:271-318` |
| `tests/synaptic_host/test_docker_execution.py` | 16 | none; one inline `pytest.skip` at `:355` |
| `tests/synaptic_host/test_publication_local_posix.py` | 4 | all four `skipif(os.name != "posix")` at `:173, :209, :286, :318` |
| `tests/synaptic_host/test_publication_local_windows.py` | 8 | **Windows-host-only**, `skipif(os.name != "nt")` alias at `:84-86`; inline volume skip at `:470` |
| `tests/synaptic_host/local_io_v1/test_windows_port_contract.py` | 32 | none; written to run **on Linux**, driving the Windows branch by injection (`:225`); two inline `if os.name == "nt"` skips at `:217`, `:423` |
| `tests/synaptic_host/local_io_v1/test_filesystem.py` | 101 | none at all; platform-neutral |
| `tests/synaptic_host/test_docker_staging.py` | 25 | eight `skipif(os.name != "nt", reason="Windows cleanup policy")` at `:47, 72, 95, 129, 162, 196, 215, 251` |
| `tests/synaptic_host/test_docker_publication.py` | 7 | none |
| `tests/synaptic_host/docker_v1/test_real_docker_wsl.py` | 1 | POSIX + `WSL_INTEROP` + docker.exe present (`:339-344`) — the legacy Alpine test |

Also gated: `tests/synaptic_host/local_io_v1/test_posix_spool_admission.py:24-27`
(Linux only); `tests/synaptic_host/test_cold_bootstrap.py:963-966`
(env-var opt-in).

### 7.2 The Windows test recipe

`scratch/test-phase/winpy.sh`, in full:

```bash
#!/usr/bin/env bash
# Canonical Windows-host pytest invocation from WSL for this worktree.
# Usage: scratch/test-phase/winpy.sh <windows-form test path> [pytest args...]
WINROOT='F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host-clean'
PY312='/mnt/c/Users/Joseph/AppData/Local/Programs/Python/Python312/python.exe'
export WSLENV=PYTHONPATH
export PYTHONPATH="$WINROOT;$WINROOT\\synaptic-tuner"
exec "$PY312" -m pytest "$@"
```

It runs pytest on **Windows CPython 3.12 invoked from WSL**, so `os.name == "nt"`
and the Windows-only suites actually execute. `PYTHONPATH` is two Windows-form
paths joined by `;`, forwarded verbatim by `WSLENV=PYTHONPATH` (no `/p`, because
the value is already in Windows form). The test path argument must also be in
Windows form.

`scratch/test-phase/winpy2.sh` is identical except that it adds
`WSLENV='PYTHONPATH:GIT_CONFIG_GLOBAL/p'` and points `GIT_CONFIG_GLOBAL` at
`scratch/test-phase/gitconfig_win` for git long-path support. **Use `winpy2.sh`
for anything that shells out to git**, which the activation path does.

### 7.3 Known environmental failures on Linux

The stable baseline is **12 failed, 11 skipped** in three families: 4 Windows
drive path, 3 absolute Windows docker executable, 5 locked Git object
(`docs/architecture/native-windows-publication-closure.md:1161-1176`). The pass
count is informational and rises with test additions.

Two facts that repeatedly cost time:

- **No environment variable fixes the 5 locked-Git-object failures.**
  `_git_environment()` (`docker_staging.py:1012-1029`) does not inherit the
  ambient environment and pins `GIT_CONFIG_GLOBAL=os.devnull`. The failures
  surface as `ValueError("exact locked Git object is unavailable")`
  (`docker_staging.py:1046`), which swallows git's own message with `from None`.
- **A `git clone` destination under `/mnt/f` fails** on `chmod .git/config.lock`
  (DrvFs). Clone destinations and pytest basetemps for cloning fixtures belong
  on ext4 (`docs/review/native-windows-publication-closure.md:115`).

Also: use explicit file paths, never a directory glob — the rtk proxy reports
"No tests collected" for globs and reformats output
(`docs/architecture/native-windows-publication-closure.md:1222-1227`). And
`test_docker_training.py` cannot be collected under Python 3.10
(`dataclass(weakref_slot=True)`); use an explicit 3.11+ interpreter
(`docs/review/native-windows-publication-closure.md:123`).

---

## 8. Open questions for ARCHITECT

Each is a decision with the options visible from the code.

### D1 — What does "the same prepared path" mean, given that the container argv is locked?

This is the gating decision; D2 through D7 are downstream of it.

| Option | What it costs | What it preserves |
|---|---|---|
| **A. Run the real SFT entrypoint on CPU with the tiny SmolLM2 model already pinned in the smoke** (`training/smokes/docker-sft.json:5-7`, `max_steps: 1`) | Needs a CPU-capable image with `/opt/conda/bin/python3` and torch; not Alpine, and not small. Slow. | Everything. Zero code change to staging, verification or publication. Genuinely the production path. |
| **B. Add a second locked closure to the engine submodule** naming a tiny diagnostic entrypoint | Modifies `synaptic-tuner` at `aec998ee`. **Explicitly forbidden by the task.** | The staging equality check, unweakened. |
| **C. Introduce a Host-side diagnostic stage builder** that bypasses `_verify_worker_closure_binding` for an explicitly opted-in run | A second staging path. Risks becoming the "compatibility layer" the constraints forbid. The check it bypasses is the strongest guarantee in `docker_staging.py`. | The image, mount, network and publication halves exactly. |
| **D. Scope the diagnostic to activation only** — real container, real create/start/observe, and accept that verification fails with a known diagnostic, so publication is proven separately on the POSIX or fake-port path | Does not exercise publication end to end on Windows, which is the stated point. | Everything else, with no code change at all. |
| **E. Split into two diagnostics**: a container-activation diagnostic (option D) plus a Host-side publication diagnostic that injects a genuine `ARTIFACTS_VERIFIED` aggregate | Two artefacts. The second needs an integrity-sealed aggregate, which the architecture doc says must not be forged (`docs/architecture/…:1276-1287`). | Honest about what each half proves. |

My reading: A is the only option that changes no code and is not forbidden, and
its cost is an image, not a design compromise. It is also the option the
architecture doc's own section 9.3 acceptance sequence already assumes. But it
is not an *Alpine* diagnostic, and the feature is named for one — so this
decision belongs to ARCHITECT, not to me.

### D2 — If a stand-in workload is chosen, who writes the five artifacts?

Options: a stdlib-only Python writer inside the container (feasible — see §2.5,
`tarfile`, `json` and a hand-built safetensors header are all standard library);
hand-authored fixture tarballs staged in and copied by a shell script (fails on
`workload_record` and the lineage document, both of which are run-specific);
or a Host-side writer that populates the artifact root before verification
(no longer "the container produced them").

### D3 — Where does the accelerator kind come from?

`docker_training.py:825` is a literal `AcceleratorDeviceRequestV1("nvidia", (0,), ("gpu",))`,
while `plan.resources.accelerator` at `:526` already reads
`profile.accelerators[0]`. Options: make line 825 profile-driven and widen
`training/providers/docker.json:24-26` to allow `cpu`; or add a second committed
provider profile for the diagnostic. The first is a two-line change that also
removes a latent inconsistency; the second avoids touching the production
profile at all.

### D4 — Where does the opt-in attach?

Options: a fourth CLI option (needs `cli.py:497` and the `range(2, 8, 2)` loop
at `:500` to change, and the fixed-arity parser is deliberate); an environment
variable following the `SYNAPTIC_RUN_WSL_LAUNCHER_INTEGRATION` precedent
(`tests/synaptic_host/test_cold_bootstrap.py:963-966`); a distinct
`--provider` value; or a distinct committed config path under
`project://training/` selected by `--config`, which needs **no code change at
all** because the config ref is already free-form within that prefix
(`cli.py:512-537`). The last option is the only one that adds no surface.

### D5 — Is the diagnostic a test or a command?

If it is a pytest module it inherits the Windows recipe (§7.2) and the existing
`skipif` conventions, and it cannot be run by an operator. If it is a command it
needs D4 and becomes a supported surface. The two queued host probes (§6) argue
for a test, because TEST owns settling them.

### D6 — Does the diagnostic get its own destination and spool root?

Recommendation: **no**. Adding a Windows-specific destination would break the
provider-neutrality ruling (§3.3). If isolation is wanted, a distinct
`project://.synaptic/` storage root reusing `adapter_ref` `host.local/v1` costs
one entry in `training/storage.json` and no code.

### D7 — How many reconcile calls does the diagnostic make, and what does it assert?

The verify cut and the publish cut are different calls (§1.5). The diagnostic
must call reconcile **at least twice** before asserting anything about
publication, and should assert the M-8/A-2 behaviour positively: a publish cut
with no publication returns `RECONCILE_REQUIRED` carrying
`PUBLICATION_COMPOSITION_ABSENT`, and `SUBMITTED` now requires
`not outcome.reconcile_required`.

---

## 9. Files the diagnostic is expected to touch

Contingent on D1; this is the union across the live options.

| Path | Expected change | Trigger |
|---|---|---|
| `training/providers/docker.json` or a sibling profile under `training/providers/` | image, interpreter, accelerator, cpu/memory for the diagnostic | D1, D3 |
| `training/smokes/` — a new committed input | the diagnostic's training input | D1, D4 |
| `training/storage.json` | at most one new root, if D6 chooses isolation | D6 |
| `synaptic_host/docker_training.py` | `:825` accelerator literal becomes profile-driven | D3 |
| `synaptic_host/docker_provider.py` | `:24-26` allowed accelerators, if the production profile is widened | D3 |
| `tests/synaptic_host/` — one new test module | the diagnostic itself, if D5 chooses a test | D5 |
| `scratch/test-phase/` | run records only | always |
| `docs/architecture/prepared-path-alpine-diagnostic.md` | ARCHITECT's output | always |

## 10. Files the diagnostic must not touch

| Path | Why |
|---|---|
| `synaptic-tuner/` — the entire submodule at `aec998ee` | Pinned. Forbidden by the task. Includes the locked closure manifest, `tuner/runtime/verification.py` and `tuner/training/methods/sft.py`. |
| `synaptic_host/docker_v1/composition.py` | Legacy same-process facade; production must not reach it (§4.1). |
| `tests/synaptic_host/docker_v1/test_real_docker_wsl.py` | The legacy Alpine test. Not an acceptance gate; leave it as the historical record it is. |
| `synaptic_host/docker_staging.py:1533-1588` | `_verify_worker_closure_binding`. Weakening the argv equality check removes the strongest guarantee on the path. |
| `synaptic_host/local_io_v1/posix.py` | Ruled untouched by the closure (`docs/architecture/…:651`). |
| `synaptic_host/artifact_destinations.py`, `local_artifact_destination.py`, `artifact_spool.py` | Ruled untouched; provider neutrality depends on the registry not learning that a platform exists. |
| `synaptic_host/publication_store.py` | No new database table. |
| `training/artifacts.json` | Adding a Windows destination breaks provider neutrality (§3.3). |
| `CLAUDE.md` anywhere | Gitignored in worktrees; orchestrator-managed. |

---

## 11. Where the code and the architecture doc disagree

Three places, all minor, all recorded rather than silently reconciled.

1. **Line numbers.** The architecture doc pins citations to `85b922fc` and says
   so (`docs/architecture/…:18-40`). Every number in this document is against
   the working tree at head. Notable drifts: the port factory is at
   `publication_composition.py:394-413` with the `LocalFilesystemV1`
   construction at `:454`, not `:433`; the lazy publication branch is at
   `docker_training.py:927-949`, not `:846-871`; `reconcile` runs
   `:1135-1218`, not `:1103-1129`.

2. **`_docker_command_result_v1` line.** The architecture doc cites
   `docker_training.py:682` (`docs/architecture/…:584`) and the review cites
   `:906-912` for the pre-fix mapping
   (`docs/review/…:103`). At head the function is at `:682` and the `submitted`
   expression at `:715-719`. The doc's by-name citation survived the shift; the
   review's by-line one did not.

3. **`stat_at` docstring cites `posix.py:321-328`** as the POSIX contract
   (`windows.py:1057-1058`), which is the same citation B-1 used. That one is
   still accurate and is noted only because it is the sole cross-module line
   citation embedded in shipped source rather than in a document, so it will go
   stale silently.

No disagreement of substance was found. The architecture doc's rulings (a)
through (g) all match the landed code.
