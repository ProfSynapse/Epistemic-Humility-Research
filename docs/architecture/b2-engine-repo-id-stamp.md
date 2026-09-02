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
