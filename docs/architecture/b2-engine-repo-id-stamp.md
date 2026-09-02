# B-2 — stamping the locked repo id into `adapter_config.json`

ARCHITECT ruling for nested cycle #101 (task #112, nested ARCHITECT #103).
Date 2026-09-02. Upstream research: `docs/preparation/b2-engine-repo-id-stamp.md`
(preparer-engine, task #107). User ruling for this cycle: fix the engine, move
the pin, the verifier stays strict.

Every line citation below was re-verified against the engine working tree at
`aec998ee`. Section 13 records where I found the research off by a line.

---

## 0. The ruling in one paragraph

**Candidate C, gated on `runtime_v1_requested`.** After the SFT trainer saves
the final model, re-read `final_model/adapter_config.json`, set
`base_model_name_or_path` to `config.model.model_name`, and write it back.
Do it only when the run is a prepared runtime-v1 run. Do **not** mutate
`model.peft_config` (Candidates A and B), and do **not** import the engine's
existing surgery helper to do it. One engine file changes, plus two test files.

---

## 1. Why the stamped value is trustworthy

This is the finding that made the ruling easy, and the research did not state
it: **`config.model.model_name` is already proven equal to the locked model ref
on every prepared run, by a check that exists today.**

- The trainer's runtime projection publishes `"ref": config.model.model_name`
  (`Trainers/sft/train_sft.py:64`).
- The host rebuilds an expected projection whose model ref is
  `config["model"]["ref"]` (`tuner/runtime/verification.py:732`) — the same
  workload field the adapter-config check reads (`:253`) — and additionally
  requires the embedded lineage's `model.base_model` to equal it (`:766`).

So the value cannot be wrong without the run already failing for an unrelated,
pre-existing reason. The stamp therefore introduces **no new trust in a new
value**; it copies a value the run is already audited against into a second
artifact that is audited against the same source. That is what makes this a
correction rather than a workaround.

The plumbing is confirmed: `runtime_v1.py:1164-1173` builds the trainer argv
with `--model-name`, `str(model["ref"])` at `:1169-1170`, and
`train_sft.py:893-894` binds it into `config.model.model_name`.

---

## 2. Why not Candidates A and B

Both mutate `model.peft_config[...].base_model_name_or_path` after the LoRA
attach and rely on `peft`'s `save_pretrained` writing a non-`None` value
through unchanged.

**The blocking reason is O-1.** The research read `unsloth 2026.4.2` from the
WSL environment; the image runs `unsloth 2026.1.2`, three minor versions back.
In `2026.4.2` the block that rewrites this exact field
(`unsloth/models/llama.py:3293-3302`) is disabled behind `if False:`. Whether it
is live in `2026.1.2` is unknown and unknowable without reading inside the
image. If it is live, it rewrites the field the stamp just set, and the failure
appears **after a complete training run**, at verification.

I am not willing to spend a real run to find out, and I do not need to: the
whole question is an artifact of stamping an in-memory object that a third-party
library owns. Candidate C never touches that object.

Two further points, neither decisive alone:

- The research is right that A and B are equally untestable — both
  `train_sft.py` and `Trainers/sft/src/model_loader.py:5` import unsloth at
  module scope, so neither can be imported by the suite (research O-4).
- B additionally changes a function signature shared in shape with three other
  trainers, widening the diff past the SFT lane this cycle scoped.

**Candidate D stays rejected** for the reason the research gives: the supervisor
that would stamp is the same component that runs `_validate_model_config`
(`Trainers/sft/runtime_v1.py:1803-1815`), so it would check its own writing.

**C is not the same mistake.** The stamp lives in the trainer; the checks live
in the supervisor and, independently, on the host outside the container
(`tuner/runtime/verification.py:940-953`). Producer and verifier stay separate,
which is exactly the property D destroys.

### 2.1 The objection to C, answered

The research calls C "a repair rather than a correction, and the furthest point
from the cause". The cause cannot be fixed at its root. `peft` derives the
field from the loaded model's `_name_or_path`, and that value is **required** to
be the snapshot directory: `Trainers/sft/src/model_loader.py:230-236` asserts it
and raises otherwise, deliberately, so that unsloth cannot substitute an
optimized mirror. Any change that made `peft` derive the repo id would break the
identity assertion the engine went out of its way to add.

Once the root is closed, both A and C are downstream corrections. The right
tie-breaker is which one acts on the bytes the verifier reads. C does.

---

## 3. The exact change

One file: `Trainers/sft/train_sft.py`.

### 3.1 Early guard — the "raise before save" requirement

Insert immediately after the LoRA attach block ends at `:1171`, so a bad ref
fails in seconds instead of after a full training run:

```python
if runtime_v1_requested:
    locked_ref = config.model.model_name
    if not isinstance(locked_ref, str) or not locked_ref:
        raise RuntimeError(
            "runtime-v1 run has no usable model ref to stamp into adapter_config.json"
        )
```

`runtime_v1_requested` is already in scope, set at `:728`.

### 3.2 The stamp

Insert immediately after the save block at `:1450-1452`, before
`finalize_protected_evidence`:

```python
if runtime_v1_requested:
    locked_ref = config.model.model_name
    if not isinstance(locked_ref, str) or not locked_ref:
        raise RuntimeError(
            "runtime-v1 run has no usable model ref to stamp into adapter_config.json"
        )
    adapter_config_path = final_model_path / "adapter_config.json"
    if not adapter_config_path.is_file():
        raise RuntimeError("runtime-v1 run produced no adapter_config.json to stamp")
    document = json.loads(adapter_config_path.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise RuntimeError("adapter_config.json is not a JSON object")
    document["base_model_name_or_path"] = locked_ref
    adapter_config_path.write_text(
        json.dumps(document, indent=2), encoding="utf-8"
    )
```

The guard is repeated rather than hoisted because the two sites are 280 lines
apart and each must be independently fail-closed. **At no point is the snapshot
path written, and there is no fallback branch** — every failure raises.

Placement is immediately after the save so that every later step in the function
sees the stamped file. Nothing between the save and the archive rewrites it:
`build_runtime_v1_projection` (`:47-99`) digests only the dataset and records
paths, and the research confirmed the supervisor's archiver streams members
verbatim.

### 3.3 Do NOT import the surgery helper

The research proposes
`shared/evolutionary/surgery/utils.py:43,52`
(`load_adapter_config` / `save_adapter_config`) as the ready-made mechanism.
**Take the idiom, not the dependency.**

`train_sft.py:186-190` imports `shared.evolutionary` inside a
`try/except ImportError` and sets `EVOLUTIONARY_AVAILABLE`, i.e. the engine
already treats that package as **optional**. Importing
`shared.evolutionary.surgery.utils` executes both
`shared/evolutionary/__init__.py` and `shared/evolutionary/surgery/__init__.py`,
the latter re-exporting a block of config types. Taking a hard dependency on an
optional package, from the one code path that must not fail at the end of a
successful training run, trades a real risk for six lines of JSON I/O.

`json` and `pathlib.Path` are already imported by `train_sft.py`. Inline it.

---

## 4. O-1 — the unsloth version gap

**Closed by construction. No in-image probe is required.**

Candidate C reads and writes a file after `peft` has finished with it, so no
behaviour of `unsloth 2026.1.2`, `2026.4.2`, or any future version can change
the stamped result. The gap does not need to be measured because the ruling does
not depend on the answer.

This is a schedule saving as well as a correctness one: had I ruled A, TEST
would have had to run a probe, report, and wait for a second ruling before CODE
could start.

For the record, had the lead overridden to A, the single read-only command would
have been:

```
docker.exe --host <npipe> run --rm --network none --pull never \
  --entrypoint cat <image@sha256:…> \
  /opt/conda/lib/python3.11/site-packages/unsloth/models/llama.py
```

with the `if False:` guard around the `base_model_name_or_path` loop as the
thing to confirm. Note this depends on the B-4 fix (`--entrypoint`), since the
image's own entrypoint would otherwise discard the `cat`.

---

## 5. O-2 — multi-adapter key policy

**Stamp exactly one file: the top-level `final_model/adapter_config.json`.**

Under C the question largely dissolves. There is no dict of adapters to choose
from; there is one file, and it is the one both verifiers read
(`verification.py:947`, `runtime_v1.py:1807` — both keyed on the member name
`adapter_config.json`). If a future multi-adapter run wrote per-adapter
subdirectories, the top-level file is still what the artifact contract covers,
and such a run is out of scope: nothing on the prepared path creates a second
adapter today.

Candidates A and B would have had to choose between the active adapter and a
loop over `peft_config.keys()`. C does not.

---

## 6. O-3 — the consumers that load from this string

**Confirmed: none of the three is on the prepared path**, and I verified the
second one by two independent routes rather than by absence of an import.

| Consumer | On the prepared path? | Evidence |
|---|---|---|
| `Evaluator/cloud_hf_job.py:106-115` | No | Cloud lane only |
| `shared/llm/providers/unsloth.py:92` | No | Not imported by the trainer |
| `shared/experiment_tracking/transformers_loss_loader.py:33-42` | No | See below |

The loss loader deserves the detail because it is the one that would actually
bite. It reads `base_model_name_or_path` out of `adapter_config.json` and
returns it as **a model source to load from**
(`_load_adapter_base_model_name`, `:33-42`), reached from
`shared/experiment_tracking/per_example_loss.py:566,621`. Inside a
network-disabled container, handing it a hub id instead of a local path would
fail.

It cannot run on the prepared path, for two independent reasons:

1. Its entry point is gated on `compute_losses`
   (`train_sft.py:1513`), and the string `compute_losses` does not appear
   anywhere in `synaptic_host/`, so the Host never sets it in the workload
   document or the argv.
2. The trainer argv is compared for equality against an independently
   constructed expected argv (`verification.py:612-621`, built by
   `_expected_trainer_argv`), so a flag the Host does not construct cannot
   appear.

**This is also the reason for the gate.** An ungated stamp would be a net fix
for the cloud lane, which today *raises* on a path value, but it would change
what the loss loader receives on **local** runs with `compute_losses` enabled,
from a local path to a hub id. That is a regression on a lane this cycle cannot
test. Gating on `runtime_v1_requested` confines the change to the lane the
ruling names and leaves every other lane byte-identical.

The gate is not a compatibility layer. It is a scope boundary, and it reuses the
discriminator the trainer already uses at `:728-737` to gate strict
offline-snapshot behaviour.

---

## 7. O-5 — the DPO, GRPO and KTO lanes

**Out of scope for this cycle.** No verifier enforces the artifact contract for
them today, the user's ruling named the SFT lane, and the constraint is the
minimal change that unblocks the SFT smoke. Widening now would mean editing
three more trainers to fix a defect nothing currently detects.

Recorded as follow-ups, not silently dropped:

- `Trainers/dpo/src/model_loader.py:156`
- `Trainers/grpo/src/model_loader.py:113`
- `Trainers/kto/src/model_loader.py:154`

Each has a parallel `apply_lora_adapters` and presumably the same defect. If any
of those lanes later gains a locked-ref verifier, this ruling's shape transfers
directly.

---

## 8. O-6 — checkpoint adapter configs

**Out of scope, and settled rather than assumed.** The verifier reads exactly
one artifact role: `inventory.for_role("final_model")`
(`tuner/runtime/verification.py:210`). The Host archives five roles
(`synaptic_host/docker_training.py:47-50`): `final_model`, `tokenizer`,
`training_lineage`, `training_metrics`, `workload_record`. There is no
checkpoint role, so a checkpoint's `adapter_config.json` is never archived and
never verified.

Stamping checkpoints would add writes inside the training loop for no
contractual gain.

---

## 9. Test specification

Both tests are pure Python. Neither needs the training image, because neither
attaches a real LoRA.

**Test 1 — the missing negative case** in `tests/trainers/sft/test_runtime_v1.py`.

Add `"snapshot-path"` to the `attack` parametrize tuple at `:646-655`, and a
branch in `HostileModel.run` (`:660-676`) alongside `base-drift`:

```python
elif attack == "snapshot-path":
    (root / "adapter_config.json").write_text(
        '{"base_model_name_or_path":'
        '"/artifacts/cache/model/models--HuggingFaceTB--SmolLM2-135M-Instruct'
        '/snapshots/12fd25f77366fa6b3b4b768ec3050bf629380bac",'
        '"peft_type":"LORA"}',
        encoding="utf-8",
    )
```

This is the exact shape B-2 produces in the field. **It is the test whose
absence let a green suite ship the defect**: the `FakeRunner` writes an
already-correct `"example/model"` (`:284-287`), so the suite has never exercised
a path-shaped value. `base-drift` proves the check rejects a *different repo
id*; it does not prove it rejects a *path*.

**Test 2 — pin the stamped value.** A unit test asserting the written value
equals `config.model.model_name`. Since `train_sft.py` cannot be imported, this
is a source assertion in `tests/trainers/sft/test_train_sft_source.py`,
alongside the existing protected/offline group whose function opens at `:69`. It must assert all
three properties, not just the presence of the key:

1. the assigned value is `config.model.model_name`, not `args.model_snapshot`;
2. the write is gated on `runtime_v1_requested`;
3. a non-string or empty ref raises rather than falling back.

A test that only greps for `base_model_name_or_path` would pass against a
version that stamps the snapshot path, which is the bug.

**How the suite runs.** Plain `python -m pytest` from the engine root;
`pytest.ini` sets `testpaths = tests`. No host conda environment, no Docker, no
image. This is consistent with the standing rule that nothing model-related runs
outside a container: these tests run no model.

---

## 10. Files CODE touches

| File | Change |
|---|---|
| `Trainers/sft/train_sft.py` | early guard after `:1171`; stamp after `:1452`; no new module-scope import |
| `tests/trainers/sft/test_runtime_v1.py` | `snapshot-path` attack case (`:646-655`, `:660-676`) |
| `tests/trainers/sft/test_train_sft_source.py` | source assertions for the stamp |

**Must not be touched.** `Trainers/sft/src/model_loader.py` (in particular the
`_name_or_path` assertion at `:230-236` and `use_exact_model_name` at `:217`);
`Trainers/sft/runtime_v1.py:1803-1815`; `tuner/runtime/verification.py`
anywhere, and specifically `:940-953`, `:612-621` and `:732`; the DPO, GRPO and
KTO trainers; `shared/evolutionary/`; anything under `synaptic_host/`. The
verifier stays strict, and the trainer argv does not change, so `:612-621` is
never at risk.

---

## 11. Host pin-move steps

The submodule is at **detached HEAD `aec998ee`**, verified; there is no local
branch, and `remotes/origin/feat/submodule-cloud-api-v1` contains that commit.
Remote is `https://github.com/ProfSynapse/Synaptic-Tuner.git`. A coder who
commits without creating a branch first will strand the commit.

Reads and writes use Windows git:
`'/mnt/c/Program Files/Git/cmd/git.exe' -c safe.directory='*' -C <windows path>`.

1. In the submodule, create the local branch at the current HEAD:
   `git.exe -C <submodule> checkout -b feat/submodule-cloud-api-v1 aec998ee`.
   Confirm `git.exe -C <submodule> status -sb` no longer reports `HEAD (no branch)`.
2. Commit the engine change on that branch.
3. Push by explicit ref:
   `git.exe -C <submodule> push origin feat/submodule-cloud-api-v1:feat/submodule-cloud-api-v1`.
4. In the Host worktree, stage the moved submodule pointer and commit it on
   `feat/submodule-cloud-api-v1-host-clean`. This pointer commit is the pin move;
   it is the only Host-side change in this cycle.
5. Push the Host branch by explicit ref.
6. Produce a fresh released checkout for TEST. The prior ruling stands: it goes
   on a **Windows drive** (`F:`, NTFS) produced with `git.exe`, never on distro
   ext4 reached over a UNC, because `local_io_v1/config.py:113-119` refuses a UNC
   project root and `docker_v1/prepared.py:46-47` raises without a drive letter.

Nothing merges to `main`. The engine pin moves for the first time in this
feature; record the new commit id in the Host pin note so the next cycle does not
re-derive it.

---

## 12. Residuals

- **R-1.** The stamp is confined to prepared runs. The cloud lane
  (`Evaluator/cloud_hf_job.py:106-115`) still raises on a path value produced by
  a local run. Pre-existing, unchanged by this cycle, worth its own ticket.
- **R-2.** DPO, GRPO and KTO keep the defect (section 7).
- **R-3.** The suite still never exercises a real `peft` save. Test 1 tests the
  *verifier* against a path-shaped value; only the host run exercises the
  *stamp*. The smoke is that test.
- **R-4.** I did not read `unsloth 2026.1.2`. Under Candidate C that is
  deliberate and harmless, but it means the engine still has no recorded answer
  to what that version does to `peft_config`. If anyone later revisits Candidate
  A, the question reopens.

---

## 13. Citation drift found while verifying

| Research says | Actually |
|---|---|
| `train_sft.py:1451-1452` for `trainer.save_model` | `:1450` is `trainer.save_model`; `:1451-1452` is the tokenizer save |
| `test_runtime_v1.py:672-675` for the FakeRunner adapter config | that is the `base-drift` hostile write; the FakeRunner's own write is `:284-287` |

Both are single-line offsets in an otherwise accurate document, and neither
changes any conclusion. The research's substantive claims — the argv plumbing,
the `save_pretrained` fallback, the verifier predicates, the helper location,
the unsloth dead block, and the O-4 correction about importability — all held up
against the tree.

---

## 15. Amendment 2026-09-02 — ruling on B-5 (regenerating the worker closure manifest)

Blocker #116. The B-2 stamp edits `Trainers/sft/train_sft.py`, which is member 8
of the checked-in content-addressed worker closure
`tuner/runtime/manifests/offline-sft-worker-v1.json`. The manifest pins that
file by size and sha256, so the edit invalidates it and every prepared run
fails at staging until it is regenerated.

### 15.1 The measured state

Measured against the engine working tree on 2026-09-02, with the B-2 edit
already applied by CODE:

| Item | Manifest records | Working tree |
|---|---|---|
| `Trainers/sft/train_sft.py` size | 74 467 | 76 857 |
| `Trainers/sft/train_sft.py` sha256 | `412b4e33…f540aba` | `a2c4c8fd…` (moves again if CODE edits further) |
| `payload_bytes` | 683 234 | 685 624 |
| `closure_digest` | `eeba2f42…41d7d3` | recomputed |

I swept all 66 members against the working tree. **Exactly one member has
drifted** — `Trainers/sft/train_sft.py`. `Trainers/sft/runtime_v1.py` and
`Trainers/sft/src/model_loader.py` are also closure members and are also in the
B-2 blast radius, but neither has moved. `member_count` stays 66, the member set
and its order are unchanged, and every member is `git_mode` `100644` (there is
no `100755` member in this closure).

### 15.2 Ruling — option (a), a refresh-in-place generator

Adopt **(a)**: one checked-in script in the engine's `scripts/`, named
`regenerate_offline_sft_worker_closure.py`, mirroring the
`capture_*_lock.py` pattern. It **refreshes** the existing manifest; it never
rebuilds it.

**Why not (b), reviewed hand-regeneration.** Two of the four values are sha256
digests — one over a 76 KB source file, one over a 66-member canonical JSON
document. A person cannot compute them by inspection, so (b) is really "run an
ad hoc snippet and paste the output", which is (a) without review, without a
fail-closed contract, and without a checked-in artifact the next editor can
find. The operation also recurs: this is the first closure-member edit of the
branch, not the last. And the failure is not confined to a wrong digest —
a hand edit that reflows the JSON breaks the exact-bytes assertion in the
contract test, and a hand edit that updates `size_bytes` but not
`payload_bytes` passes casual review yet raises
`"worker closure totals or ordering are invalid"` inside the container
(`offline_sft_worker.py:344-356`), after staging, on the real run.

**Why not (c) in the shape it would naturally take.** The tempting third option
is a self-healing contract test that rewrites the manifest when it mismatches.
That is closed: the closure manifest is the artifact that decides which code
runs in the network-disabled container, and a test that repairs its own
expectation is not a pin. The check must be able to fail.

### 15.3 Member list source of truth

**The existing manifest's own `members[].path` list.** Not a filesystem walk,
not `pyproject.toml`, not the contract test.

- `pyproject.toml:57` carries only `"tuner.runtime" = ["manifests/offline-sft-worker-v1.json"]`
  — it declares the manifest as package data and lists no members. It is not a
  candidate.
- `tests/contract/test_offline_sft_worker_closure.py:21-88` holds `_MEMBERS`, a
  hard-coded tuple of all 66 paths. This is the **independent cross-check**, not
  the source. Tooling must not import a test module to learn what to produce;
  that would collapse the two independent copies into one and destroy the check.

**Why a filesystem walk is closed.** This is the load-bearing constraint.
`_iter_staged_files` (`offline_sft_worker.py:372`) enumerates the staged tree in
the container and the check at `:425-441` requires it to *exactly* equal the
member set, raising `"staged worker members do not exactly match closure"`. A
walk-based generator would make closure-widening the default behaviour of the
tool: add any file under an owned prefix, run the generator, and it silently
joins the set of code that executes in the container. The contract test's
`_MEMBERS` tuple would catch it — but late, and the path of least resistance
under time pressure is to paste the new list into `_MEMBERS` and move on.
Refresh-in-place makes widening structurally impossible from the tool, so
widening requires a deliberate two-file edit that a reviewer sees as a diff of
paths. Design against the failure mode, not the happy path.

### 15.4 The canonical serialization

Two different byte strings are involved and conflating them is the single
easiest way to produce a manifest that fails only at run time.

**File bytes** (pinned by the contract test at lines 110-117):

```python
json.dumps(
    document,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
    allow_nan=False,
).encode("utf-8") + b"\n"
```

**Digest input** (`offline_sft_worker.py:123-139`): the *same* `json.dumps`
call, over the document with `closure_digest` popped, and **without** the
trailing newline. `closure_digest` is `sha256` of that.

So: the newline is part of the file and not part of the digest. Top-level keys
land in alphabetical order and member keys in the order
`git_mode`, `path`, `sha256`, `size_bytes` as a consequence of `sort_keys`, not
as an independent rule. Members stay ordered by path in plain `str` sort
(`offline_sft_worker.py:342` requires `paths == sorted(paths)`); a refresh
preserves the input order and therefore satisfies this for free.

### 15.5 Exactly which fields change

Four values, and nothing else:

1. `members[<train_sft.py>].sha256`
2. `members[<train_sft.py>].size_bytes`
3. `payload_bytes` — the sum over all members
4. `closure_digest`

Unchanged: `schema_version`, `closure_ref`, `entrypoint`, `trainer_entrypoint`,
`owned_module_prefixes`, `optional_features`, `member_count`, every member path,
every `git_mode`, and the member ordering. The six identity fields are re-checked
verbatim against module constants at `offline_sft_worker.py:301-307`, so a
generator that touches any of them fails closed at parse.

The generator addresses the member **by path**, never by array index. "Member 8"
is an ordinal in this document only.

### 15.6 The generator's contract

Default mode is `--check`; `--write` must be explicit. A bare invocation never
mutates a checked-in artifact. This matches the drift-check idiom the Host repo
already uses (`bin/sync_skills.py`).

Exit codes, distinct so CI can tell a stale manifest from a broken tool:

| Code | Meaning |
|---|---|
| 0 | On-disk bytes already equal the regenerated bytes |
| 3 | Drift — prints the differing member paths and field names |
| 125 | Fault — prints a reason code, writes nothing |

Fail-closed conditions, all of which produce 125 and no write:

- Any member path is missing, is a symlink, or is not a regular file.
- The recomputed path list is not identical to the input list, or is not sorted,
  or contains a duplicate.
- A member's POSIX executable bit contradicts its recorded `git_mode`
  (the staged-tree check at `offline_sft_worker.py:437-441` enforces this in the
  container; catching it here turns a run-time failure into a tool-time one).
- Any member exceeds `_MAX_MEMBER_BYTES`, or the total exceeds
  `_MAX_CLOSURE_BYTES` (64 MiB each, `offline_sft_worker.py:61-62`).
- **Verify-after-write**: re-read the bytes just written, re-parse them through
  the production verifier, and confirm the recomputed digest matches. If it does
  not, restore the original bytes and exit 125. The generator must never leave a
  manifest on disk that the worker would reject.

The generator must not import the contract test, and must not write any file
other than the manifest.

### 15.7 Script shape and its two divergences from the capture-lock pattern

Mirror `scripts/capture_hf_training_image_lock.py`: an `_authenticated_repo_root()`
that refuses a symlinked script, checks `script.name` and
`script.parent.name == "scripts"`, verifies that anchor files resolve to
themselves, inserts the authenticated root on `sys.path`, and exits 125 with a
reason code on any fault. Anchors here: `tuner/runtime/offline_sft_worker.py`
and `tuner/runtime/manifests/offline-sft-worker-v1.json`.

Two deliberate divergences, both narrowing:

- **No delegation to a new `tuner/` module.** The capture-lock script is thin
  because `tuner/cloud/hf_training_image_lock.py` is also used by production
  verification. Here the production verifier already exists — the generator
  imports `closure_digest` and the identity constants from
  `tuner/runtime/offline_sft_worker.py` and adds no second implementation of
  them. A new module under `tuner/` would also sit inside an owned module prefix
  (`offline_sft_worker.py:34-44`), which is the namespace the worker's import
  guard governs (`:499`, `:551`); a non-member module there is precisely the
  shape that guard exists to reject. `scripts/` is outside every owned prefix.
- **No external inputs.** No `--docker`, no registry, no network. The tool reads
  the working tree and the manifest and writes the manifest.

### 15.8 How the contract test proves round-trip

`tests/contract/test_offline_sft_worker_closure.py` **already is** the
round-trip proof and needs no edit. Five assertions compose to it:

| Assertion | What it proves |
|---|---|
| `payload == json.dumps(document, …) + b"\n"` | The file is in canonical form, newline included — no reflow survives |
| `document["closure_digest"] == closure_digest(document)` | The digest is over the document actually written |
| per-member `size_bytes == len(content)` and `sha256 == sha256(content)` | Every content pin matches the working tree |
| `payload_bytes == sum(size_bytes)` | The total is consistent |
| `tuple(paths) == _MEMBERS` and `member_count == len(_MEMBERS) == 66` | The closure did not widen, checked against a copy the tool never reads |

Read together: parse the written bytes, re-derive every value, re-serialize, and
require byte equality with what is on disk. That is a round trip.

`_MEMBERS` and the literal `66` must **not** be touched by this work. If a future
change requires touching them, that is a closure-widening decision and needs its
own ruling, not a generator run.

**One new test is required**, in the same file, and it is the only test change:

```
test_regenerator_reports_no_drift_on_the_checked_in_manifest
```

It invokes the script as a subprocess with `sys.executable` in `--check` mode
and asserts exit 0. This pins the generator itself to the same exact-bytes
contract that pins the manifest, so a tool that drifts from the canonical form is
caught in CI rather than at the next regeneration. One function invoking one
script is not a framework.

### 15.9 The `docs/preparation` prose line

**Leave it unchanged.** `docs/preparation/prepared-path-alpine-diagnostic.md:117`
reads "Today: 66 members, 683 234 payload bytes, closure digest
`eeba2f42…41d7d3`". The word "Today" already scopes the claim to the
observation date, and the observation was true of engine `aec998ee`. Rewriting a
research document so it tracks a change it predates makes it stop describing the
commit it measured. The supersession is recorded here instead; section 15.1
carries the new state.

One citation drift found in that document while checking this: it cites
`docker_staging.py:32` for `_CLOSURE_MANIFEST_SOURCE_PATH`; the constant is at
`:33`. Recorded, not corrected, for the same reason.

### 15.10 Confirmation — no Host file pins the digest

**coder-engine's finding is correct, with one refinement worth stating so the
next person who greps does not misread what they find.**

The literal `eeba2f42` appears in the Host tree exactly twice:

1. `docs/preparation/prepared-path-alpine-diagnostic.md:117` — prose, handled in 15.9.
2. `scratch/test-phase/wintmp2/docker-admission0/project/synaptic-tuner/tuner/runtime/manifests/offline-sft-worker-v1.json`
   — a staged copy left by an earlier run. `scratch/` is gitignored
   (`.gitignore:9`), so this is a run artifact, not a pin. It will be
   regenerated on the next staging.

No Host **code** pins it, and the design makes pinning unnecessary:
`docker_staging.py:33` names the manifest by path, `:1180-1182` and `:1239`
recompute the digest from the locked git blob by popping `closure_digest`, and
`:1750`/`:1765` pass `worker_source_closure_digest=locked_closure.closure_digest`
— the expectation is *derived from the blob being verified*, never stored.
`_parse_manifest` then requires `recorded == observed == expected`
(`offline_sft_worker.py:308-320`), which is self-consistent by construction for
any correctly regenerated manifest.

The engine side is equally clean: **zero** occurrences of the digest literal
anywhere in the engine outside the manifest itself. No test embeds it;
`tests/runtime/test_offline_sft_worker.py:22` and
`tests/trainers/sft/test_runtime_v1.py:86` both read the manifest at run time.

**Therefore B-5 needs no Host change.** The submodule pointer move already
scheduled in section 11 carries the new digest.

### 15.11 Files

Engine (`synaptic-tuner`), all in the same commit as the B-2 trainer edit:

| File | Change |
|---|---|
| `scripts/regenerate_offline_sft_worker_closure.py` | New. The generator, per 15.6 and 15.7. |
| `tuner/runtime/manifests/offline-sft-worker-v1.json` | Regenerated. Four values, per 15.5. |
| `tests/contract/test_offline_sft_worker_closure.py` | One new test function, per 15.8. `_MEMBERS` untouched. |

Host: none.

**Ordering constraint for CODE.** Run `--write` *after* the trainer edit is
final. Any further edit to any of the 66 members re-stales the manifest, so run
`--check` as the last step before committing rather than assuming only
`train_sft.py` moved. The sweep in 15.1 is a snapshot, not a standing fact.

### 15.12 Residuals

- **R-3.** Nothing outside the contract test enforces that the generator was
  actually run. A closure-member edit committed without regeneration passes
  review and fails at the next prepared run. The new test in 15.8 closes this in
  CI; if this branch has no CI gate, the check is only as good as the person who
  remembers to run it. Flagging for the deferred ledger, not deciding it — a
  pre-commit hook is a repo-policy decision above my remit.
- **R-4.** `optional_features` is pinned to `[]` at
  `offline_sft_worker.py:306`. The generator writes it through unchanged, so it
  is inert here, but it is the field a future "add an optional member" request
  would reach for, and it has no generator support by design.

### 15.13 Correction 2026-09-02 — the 25 test failures are not the stale manifest

Recorded after the ruling above was accepted. I ran the engine suite to check the
blocker's attribution and it does not hold.

`tests/trainers/sft/test_runtime_v1.py` on this worktree: **34 failed, 42 passed.**
All 34 share one root cause, and it is neither the stale manifest nor B-2.

- 25 fail with `OfflineSFTWorkerError: staged worker member mode does not match`.
- 9 fail a `pytest.raises(match=...)` assertion whose observed message is
  `offline worker closure validation failed` — the same closure error preempting
  the specific error each negative test meant to provoke.

**Mechanism.** Every one of the 66 members is mode `0o777` on this
DrvFs/9p Windows-backed mount, so the POSIX executable bit is set on all of them.
The staged-tree check at `offline_sft_worker.py:438-441` requires
`executable == (git_mode == "100755")`, and every member is declared `100644`.
The fixture stages members with `shutil.copy2` (`test_runtime_v1.py:89-93`),
which preserves mode, so the check raises on **member 1**,
`Trainers/sft/configs/config.yaml` — a file B-2 never touches — before the
per-member content check ever reaches `train_sft.py`.

Git disagrees with the filesystem and git is right: this repo has
`core.filemode = false`, and the index records `100644` for the members.
The `0o777` is a mount artifact that git is explicitly configured to ignore.

**Three consequences.**

1. **Correction to blocker #116's attribution — itself corrected later the same
   day.** My first statement here, "regenerating the manifest fixes none of the
   34", was true of this worktree and wrong as a general claim. There are two
   independent causes, and the mode artifact *masks* the other one: the loop at
   `offline_sft_worker.py:430-441` checks content then mode per member, so on a
   `0o777` mount it raises on member 1, `config.yaml`, before member 8's genuine
   content mismatch is ever reached. On a mode-correct filesystem the stale
   manifest is a real and sufficient cause — which is what coder-engine measured
   on an ext4 git-archive harness, reporting `staged worker member does not
   match closure` and returning to baseline after regeneration. What stands from
   the original claim: on this mount the mode failure reproduces on a pristine
   checkout of `aec998ee` with no B-2 edit, and TEST (#105) therefore runs on an
   ext4 extraction by lead ruling.

   Verified independently after coder-engine regenerated the manifest: staging
   all 66 members to ext4 at `0o644` and calling
   `load_offline_sft_worker_closure` **passes**, while the identical stage at
   `0o777` still raises `staged worker member mode does not match`. The
   regenerated manifest is correct, and its `payload_bytes` landed at 685 624 —
   exactly the arithmetic specified in 15.5.

2. **Correction to 15.6, which is my own error.** The mode fail-closed condition
   as written consults `path.stat()`, so the generator would refuse on all 66
   members on this very mount and could never be run here. Amend the oracle:
   take `git_mode` from `git ls-files -s`, not from a filesystem stat. The field
   is named `git_mode`, git is its authority, and a stat is the wrong oracle
   anywhere `core.fileMode` is false. The condition stands, with git as the
   source: refuse if git's recorded mode disagrees with the manifest's.

3. **For TEST (#105), flagged not decided.** The closure-authenticating tests in
   this file cannot pass on a Windows-backed mount regardless of B-2 or B-5.
   Running them meaningfully needs a POSIX-faithful filesystem, so "green on this
   worktree" is not available for this file and should not be the acceptance
   gate. Which filesystem TEST uses is above my remit.
