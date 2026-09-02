# B-2 — where the locked repo id can be stamped into `adapter_config.json`

**Task** #107 (PREPARE #102, nested cycle #101, feature #73), agent `preparer-engine`, 2026-09-02.
**Engine** `synaptic-tuner` at `aec998ee8d6a2e58d86e19e8132bc59aa21ebd53`, branch
`feat/submodule-cloud-api-v1`, working tree clean. Every `synaptic-tuner/…`
citation below is a line number at that commit.
**Host** worktree `F:\Code\Toolset-Training\_worktrees\ehr-submodule-cloud-api-v1-host-clean`.
**Upstream** test report `docs/testing/prepared-path-alpine-diagnostic.md` §6 (B-2, CONFIRMED by
measurement), blocker task #85, user ruling 2026-09-02.

This is a research document. It lists candidate stamp points and their
trade-offs. **It recommends nothing.** ARCHITECT (#103) decides. No `.py` file
was edited. No container was started and no image was pulled.

---

## 0. Headline, in the order ARCHITECT needs it

1. **The locked repo id already reaches the trainer process.** It arrives as the
   `--model-name` argv value and lands in `config.model.model_name`, which is
   **in scope at the LoRA attach point**. Question (2) resolves to *reaches*,
   not to *degraded* and not to *never reaches*. No new host-to-container
   plumbing is needed for any candidate below.
2. **Adding a CLI flag would be expensive.** The trainer argv is compared for
   equality against an independently constructed expected argv on the host
   (`tuner/runtime/verification.py:609-621`). A new flag must be added in two
   places in lockstep or the run fails verification.
3. **Three downstream consumers already want a repo id, and one of them raises
   today on exactly the path value B-2 produces.** The stamp is a net
   improvement for them, not a regression.
4. **Prior art exists for the mutation idiom, inside unsloth itself**, and the
   engine already has a helper that rewrites `adapter_config.json` on disk.
5. **The engine's test suite cannot import the SFT trainer or its model loader**
   — both import unsloth at module scope — so a stamp in either is covered only
   by source-text assertions. Testability does not separate the two in-process
   candidates. The existing fake runner writes an already-correct adapter
   config, which is why a green suite never caught B-2.

---

## 1. What the "locked repo id" literally is

### 1.1 The field

The locked repo id is the `model.ref` field of the **compiled workload's
configuration document**. Both verifiers read it from the same path:

```
tuner/runtime/verification.py:253
    locked_model_ref=workload.document["configuration"]["document"]["model"]["ref"],

Trainers/sft/runtime_v1.py:1459-1461
    locked_model_ref=workload.document["configuration"]["document"]["model"][
        "ref"
    ],
```

### 1.2 Its value for the SmolLM2 smoke

From the Host's committed smoke config `training/smokes/docker-sft.json`:

| Key | Value |
|---|---|
| `model.ref` | `HuggingFaceTB/SmolLM2-135M-Instruct` |
| `model.revision` | `12fd25f77366fa6b3b4b768ec3050bf629380bac` |
| `model.tokenizer_revision` | `12fd25f77366fa6b3b4b768ec3050bf629380bac` |
| `hyperparameters.lora_rank` | `8` |
| `hyperparameters.lora_target_modules` | `k_proj`, `o_proj`, `q_proj`, `v_proj` |

So the string the verifier demands is exactly `HuggingFaceTB/SmolLM2-135M-Instruct`,
matching what the test report measured (`docs/testing/prepared-path-alpine-diagnostic.md` §6).

The smoke sets a LoRA rank, and `apply_lora_adapters` is called unconditionally
(§3.1), so there is no workload on this path that avoids the LoRA branch.

---

## 2. How the value reaches the trainer under the prepared path

**Answer: it reaches, in full, as an explicit argv value.** This is the
*reaches* branch of the three-way shape, and it is the single most consequential
finding in this document.

### 2.1 The in-container supervisor builds the trainer argv

`Trainers/sft/runtime_v1.py` runs **inside** the container. It holds the whole
compiled workload document and constructs the trainer argv at `:1164-1194`:

```
Trainers/sft/runtime_v1.py:1164-1180
    argv = [
        str(Path(python_executable).resolve()),
        "-I",
        str(worker_path),
        "--",
        "--model-name",
        str(model["ref"]),          # <-- the locked repo id, verbatim
        "--model-revision",
        str(model_revision),
        "--anonymous-model",
        "--model-cache-dir",
        str(roots.cache / "model"),
        "--model-snapshot",
        str(model_snapshot),
        ...
    ]
```

`model` here is the same `configuration.document.model` mapping the verifier
reads, so `--model-name` and `locked_model_ref` are **the same string by
construction**, not merely equal by coincidence.

The snapshot path travels beside it, separately, as `--model-snapshot` and as
the `SYNAPTIC_MODEL_SNAPSHOT` environment variable (`:1211`). Identity and load
location are therefore already two distinct channels on this path. B-2 is that
`peft` overwrites the identity with the location.

### 2.2 It lands in `config.model.model_name`

`train_sft.py` assigns the argv value onto the config object during override
application:

```
Trainers/sft/train_sft.py:893-894
    if args.model_name:
        config.model.model_name = args.model_name
```

`model_name: str` is a declared field of the model config
(`Trainers/sft/configs/config_loader.py:35`).

### 2.3 The argv is equality-checked from the host

The host reconstructs the expected trainer argv independently and compares it
element-wise:

```
tuner/runtime/verification.py:614-621
    expected_argv = _expected_trainer_argv(
        executable, normalized, dataset_path, config, workload
    )
    if (
        [_normalized_path(item) for item in evidence["argv"]] != [
        _normalized_path(item) for item in expected_argv
        ]
    ):
        return False
```

and `_expected_trainer_argv` (`:660-685`) hard-codes the same flag sequence,
including `"--model-name", str(model["ref"])` at `:674`.

**Consequence for ARCHITECT.** Any candidate that introduces a *new* trainer CLI
flag must edit `Trainers/sft/runtime_v1.py:1164` **and**
`tuner/runtime/verification.py:660` together, and any drift between them fails
the run at verification rather than at the trainer. Every candidate in §5
avoids this by reusing the `--model-name` value that is already present.

---

## 3. The LoRA attach point, the save path, and what unsloth does first

### 3.1 What is in scope at `train_sft.py:1159`

```
Trainers/sft/train_sft.py:1159-1171
    model = apply_lora_adapters(
        model,
        r=config.lora.r,
        ...
    )
```

In scope at that statement:

| Name | Carries |
|---|---|
| `model` | the freshly wrapped PEFT model, with `model.peft_config` populated |
| `config.model.model_name` | **the locked repo id** (§2.2) |
| `config.model.model_revision` | the locked revision |
| `args.model_snapshot` | the snapshot directory |
| `runtime_v1_requested` | bool, set at `:728`; true only for prepared runs |
| `tokenizer`, `train_dataset`, `eval_dataset`, `run_metadata` | not relevant here |

`runtime_v1_requested` is worth noting: `:728-737` already gates strict
offline-snapshot behaviour on it, so it is an available discriminator if
ARCHITECT wants the stamp to apply only to prepared runs rather than to every
local SFT run.

### 3.2 `apply_lora_adapters` is a thin wrapper

`Trainers/sft/src/model_loader.py:272-353`. It prints, defaults
`target_modules`, builds `peft_kwargs`, and calls
`FastLanguageModel.get_peft_model(model, **peft_kwargs)` at `:338-341`, then
returns the model at `:353`. It does not touch any name field. It is shared in
shape (not in code) with the DPO, GRPO and KTO trainers, which each define their
own `apply_lora_adapters` (`Trainers/dpo/src/model_loader.py:156`,
`Trainers/grpo/src/model_loader.py:113`, `Trainers/kto/src/model_loader.py:154`).

### 3.3 Where the adapter is saved

There is exactly one model-save call in the SFT trainer:

```
Trainers/sft/train_sft.py:1451-1452
    trainer.save_model(str(final_model_path))
    if args.protected_smoke_evidence or runtime_v1_requested:
        tokenizer.save_pretrained(str(final_model_path))
```

`trainer.save_model` on a PEFT-wrapped model reaches
`PeftModel.save_pretrained`, which writes `adapter_config.json` **from the live
`peft_config` object**. The only defaulting is a `None` fallback:

```
peft/peft_model.py (installed 0.18.1), save_pretrained
    # save the config and change the inference mode to `True`
    if peft_config.base_model_name_or_path is None:
        peft_config.base_model_name_or_path = (
            self.base_model.__dict__.get("name_or_path", None)
            if peft_config.is_prompt_learning
            else self.base_model.model.__dict__.get("name_or_path", None)
        )
```

**This is the load-bearing mechanism for candidates A and B**: a non-`None`
value already on `peft_config` is written through unchanged. Mutating
`model.peft_config[adapter].base_model_name_or_path` after the attach therefore
propagates to the saved file.

**No post-save rewrite exists.** `grep` over `Trainers/sft/` finds no other
`save_pretrained` and no `adapter_config` write. The supervisor's
`_archive_artifact` streams files into the tar without editing them, which the
test report also concluded independently (§6, "Honest limits", item 3).

### 3.4 Does the unsloth path alter the name before peft sees it

The trainer **requires** `config._name_or_path` to be the snapshot path, and
asserts it:

```
Trainers/sft/src/model_loader.py:230-236
    if require_resolved_revision or require_local_snapshot:
        assert protected_snapshot is not None
        model_source = getattr(getattr(model, "config", None), "_name_or_path", None)
        tokenizer_source = getattr(tokenizer, "name_or_path", None)
        if not isinstance(model_source, str) or Path(model_source).resolve() != protected_snapshot:
            raise RuntimeError("Loaded model snapshot does not match the protected revision")
```

with the reason stated in the comment at `:175-179`: unsloth may otherwise
rewrite a Hub model name to an optimized mirror whose commit identity differs
from the approved source. The engine also passes `use_exact_model_name=True`
(`:217`) to suppress that rewrite.

So the snapshot path in `_name_or_path` is **deliberate and asserted**, not
accidental. Any stamp must therefore leave `model.config._name_or_path` alone,
and must not run before `:236`. All candidates in §5 satisfy this because they
act at or after the LoRA attach, which is far later.

Reading the locally installed unsloth for the mutation question:

```
unsloth/models/llama.py:3293-3302   (installed 2026.4.2)
    # Fix up config for transformers uploading PEFT
    for active_adapter in model.peft_config.keys():
        # Not necessary since we requires transformers >= 4.37
        if False:
            name = model.peft_config[active_adapter].base_model_name_or_path
            ...
            model.peft_config[active_adapter].base_model_name_or_path = name
```

The block is dead (`if False:`), so unsloth at this version does **not** alter
the field. See §6 for why this is nonetheless the most useful prior art in the
document, and §7 open question O-1 for the version caveat.

---

## 4. What the verifier compares, and who else reads the field

### 4.1 The check itself

Two independent implementations of the same rule, both keyed on the artifact
file `adapter_config.json` inside the archived `final_model` artifact:

```
tuner/runtime/verification.py:940-953        (host-side, post-run)
def _valid_model_config(name: str, content: bytes, *, locked_model_ref: str | None) -> bool:
    ...
    if name == "adapter_config.json":
        return (
            document.get("peft_type") == "LORA"
            and isinstance(document.get("base_model_name_or_path"), str)
            and document["base_model_name_or_path"] == locked_model_ref
        )
```

```
Trainers/sft/runtime_v1.py:1803-1815         (in-container twin, raises first)
def _validate_model_config(path: Path, name: str, *, locked_model_ref: str | None) -> None:
    ...
    if name == "adapter_config.json":
        if (
            document.get("peft_type") != "LORA"
            or not isinstance(document.get("base_model_name_or_path"), str)
            or document["base_model_name_or_path"] != locked_model_ref
        ):
            raise RuntimeV1Error("trainer adapter config is not recognizable LoRA")
```

Three predicates: the key exists, it is a `str`, and it is **exactly** equal to
`model.ref`. No normalisation, no prefix match, no path resolution. One stamp of
the correct string satisfies both, because both derive `locked_model_ref` from
the same workload field (§1.1).

### 4.2 Other consumers of `base_model_name_or_path`

Every non-test reference in the engine, classified by what a repo id would do
to it:

| Consumer | Line | Uses it as | Effect of a repo id |
|---|---|---|---|
| `Evaluator/cloud_hf_job.py` | `:106-115` | hub id; **raises** if it starts with `/` or `.` | **Fixed.** Rejects the path value today |
| `Evaluator/cloud_hf_job_vllm.py` | `:151-158` | same | **Fixed.** Same rejection |
| `shared/experiment_tracking/transformers_loss_loader.py` | `:39-42` | model source to load | Improved for cloud; see O-3 |
| `shared/model_loading/merge.py` | `:40-43` | naming only; `split("/")[-1]` | **Improved.** A path yields a bad name |
| `shared/llm/providers/unsloth.py` | `:92-94` | model source to load | See O-3 |
| `Evaluator/vllm_setup.py` | `:315-318` | substring size sniff (`"3b"`, `"7b"`…) | Improved; a repo id usually carries the size |
| `shared/model_loading/unsloth_loader.py` | `:111-112` | lowercase substring VL sniff | Neutral |
| `shared/upload/converters/{gguf,gguf_reliable,webgpu}.py` | `:293`, `:308`, `:361` | lowercase substring sniff | Neutral |
| `tuner/backends/evaluation/unsloth_backend.py` | `:150` | display, default `"unknown"` | Neutral |
| `tuner/handlers/inference_handler.py` | `:171` | display | Neutral |
| `tuner/handlers/list_handler.py` | `:378` | display | Neutral |
| `Tools/convert_to_webllm.py` | `:79` | reads the name | Neutral |

**Nothing in the engine requires this key to be a filesystem path.** The two
consumers that constrain it at all (`cloud_hf_job.py`, `cloud_hf_job_vllm.py`)
constrain it to be a **hub id**, which is what the stamp would write. The
`merge.py:266` comment "Always use absolute paths (PEFT saves
base_model_name_or_path as-is)" refers to the *adapter path argument* passed in
by the caller, not to the value of this key; the same idiom appears at
`Trainers/grpo/train_grpo.py:214-216`. It is not a counter-example.

The residual risk is O-3 in §7: the two loaders that treat the string as a model
source would, given a repo id, try to resolve it from the hub. They are not on
the prepared path, but they are on other lanes.

---

## 5. Candidate stamp points

Presented with trade-offs only. **No recommendation.**

### Candidate A — mutate `peft_config` in `train_sft.py`, right after the attach

Immediately after `train_sft.py:1171`, set
`model.peft_config[<adapter>].base_model_name_or_path = config.model.model_name`.

- **For.** Smallest possible diff, in the file the user's ruling names. The
  value is already in scope. Honoured by `save_pretrained` (§3.3). Matches the
  idiom unsloth itself uses (§6). No argv change, so §2.3 does not bite.
- **Against.** SFT only; the DPO, GRPO and KTO trainers keep the defect.
  `train_sft.py` cannot be imported by the test suite (§5.5), so this is
  testable only by source assertion. Needs a decision on which adapter key(s)
  to write when `peft_config` holds more than one.

### Candidate B — mutate inside `apply_lora_adapters`

In `Trainers/sft/src/model_loader.py`, after `:341`, taking the id as a new
keyword argument passed from `train_sft.py:1159`.

- **For.** The stamp sits next to the attach it corrects. Extends cleanly to the
  other three trainers, which have parallel functions.
- **Against.** Changes a shared function signature. Four call sites diverge
  unless all four are updated, which widens the diff beyond the SFT lane the
  ruling scoped. **It buys no testability over Candidate A**:
  `Trainers/sft/src/model_loader.py:5` imports unsloth at module scope
  (`from unsloth import FastLanguageModel, is_bfloat16_supported`), so this
  module is no more importable in the suite than `train_sft.py` is. Both A and B
  are source-assertion-only at the unit level.

### Candidate C — rewrite `adapter_config.json` on disk after `trainer.save_model`

After `train_sft.py:1451`, re-read the written file, set the key, write it back.

- **For.** Acts on the exact artifact the verifier reads, so it is immune to any
  future change in how `peft` derives the value, and immune to O-1 (the unsloth
  version question) entirely. **The engine already has this helper**:
  `shared/evolutionary/surgery/utils.py:43` `load_adapter_config` and `:52`
  `save_adapter_config`, used by `alpha_sweep.py:56` and
  `svd_rank_reduction.py:118`.
- **Against.** Rewrites a file that `peft` just wrote, which is a repair rather
  than a correction, and re-serialising can perturb key order or formatting. It
  is also the furthest point from the cause.

### Candidate D — stamp in the supervisor, `runtime_v1.py`, before archiving

Rejected on sight, recorded so ARCHITECT need not re-derive it: the supervisor
is the same component that runs `_validate_model_config`
(`runtime_v1.py:1803`). A stamp there would write the value it then checks,
collapsing the artifact contract into a tautology and destroying exactly the
auditability the user's ruling preserved.

### 5.5 Testing surface, which constrains A versus B

`Trainers/sft/train_sft.py` imports unsloth at module load, so the suite tests
it by reading its **source text**:

```
tests/trainers/sft/test_train_sft_source.py:19-20
    # train_sft imports unsloth at module load, so verify the --seed flag and its
    # is-not-None override (honoring seed=0) at the source level.
```

That file already contains an assertion group for the protected/offline
plumbing (`:69-84`), which is the natural home for a source assertion on a
Candidate A stamp.

The behavioural surface lives in `tests/trainers/sft/test_runtime_v1.py` and
`tests/runtime/test_artifact_verification.py`. A `FakeRunner` writes a
compliant adapter config (`test_runtime_v1.py:672-675`):

```
(model / "adapter_config.json").write_text(
    '{"base_model_name_or_path":"example/model","peft_type":"LORA"}',
    encoding="utf-8",
)
```

and a `base-drift` attack case asserts the check rejects `attacker/model`
(`test_runtime_v1.py:672-675` in the hostile subclass at `:660-676`).

**This is why B-2 was invisible to a green suite**: the fake runner writes the
*already-correct* value, so the suite has never exercised the real `peft` stamp.
Any new test should make the fake write a snapshot-shaped path and assert the
run is rejected, which is the missing negative case.

**How the suite is run.** `pytest.ini` sets `testpaths = tests`,
`addopts = -v --tb=short`, and one marker, `integration`. The test extra is
`pytest>=8,<9` (`pyproject.toml`). Plain `python -m pytest` from the engine root
is the invocation; no host conda environment is involved. The tests cited above
are pure-Python (source reads, `tmp_path`, JSON, fake runners) and do **not**
need the training image. Only a test that actually attaches a real LoRA would
need the image, and no such test exists today.

---

## 6. Prior art for overriding `base_model_name_or_path`

**In unsloth.** `unsloth/models/llama.py:3293-3302` iterates
`model.peft_config.keys()` and assigns
`model.peft_config[active_adapter].base_model_name_or_path = name` after the
adapter is attached. The body is disabled (`if False:`, with the comment "Not
necessary since we requires transformers >= 4.37"), so it does not run. Its
value here is that it establishes the **exact mutation idiom** Candidate A would
use, in the library that owns the object, including the multi-adapter loop.

**In unsloth_zoo.** `unsloth_zoo/hf_utils.py:151-156` reads the field, coerces
it with `str()`, raises if it is `None`, and lowercases it into
`os.environ["UNSLOTH_MODEL_NAME"]`. `unsloth_zoo/saving_utils.py:2653-2654`
reads it back out of a config dict. Both are readers, not writers.

**In the engine.** Two pieces:

- `shared/evolutionary/surgery/utils.py:43,52` — `load_adapter_config` /
  `save_adapter_config`, a checked-in read-modify-write of
  `adapter_config.json`, already used to mutate `lora_alpha`
  (`alpha_sweep.py:56`) and rank (`svd_rank_reduction.py:118`). This is the
  ready-made mechanism for Candidate C.
- `Trainers/sft/src/model_loader.py:217` — `load_kwargs["use_exact_model_name"] = True`,
  the engine already suppressing an unsloth-side name rewrite for identity
  reasons. It is the closest existing statement of intent that identity must
  not drift, and it is covered by `tests/trainers/sft/test_model_revision.py:54,95`.

---

## 7. Open questions I could not settle from source

**O-1 — the unsloth version gap is not closed.** The image measured by
`test-host` carries `peft 0.18.0`, `unsloth 2026.1.2`, `unsloth_zoo 2026.1.2`,
`transformers 4.57.1`. The libraries I read are the ones installed in this WSL
environment: `peft 0.18.1`, `unsloth 2026.4.2`, `unsloth_zoo 2026.4.2`,
`transformers 5.5.0`. I used the local installs, not a PyPI sdist and not a
GitHub tag, and I state that plainly. `peft` differs by one patch and the
`save_pretrained` fallback and `mapping_func` assignment both match what
`test-host` read from inside the image, so §3.3 is corroborated across two
versions. **unsloth differs by three minor versions and is NOT corroborated.**
I cannot rule out that `unsloth 2026.1.2` mutates the field where `2026.4.2`
does not, or vice versa. Settling this needs a read from inside the image, which
this task forbids. This is the residual of the teachback's
`least_confident_item`, and it is an argument in favour of a candidate that does
not depend on `peft_config` state at all (Candidate C).

**O-2 — multi-adapter key selection.** `peft_config` is a dict. Every candidate
that mutates it must decide whether to write the active adapter, or loop all
keys as unsloth's dead block does. Nothing in the prepared path creates a second
adapter today, so this is a robustness choice rather than a live requirement.

**O-3 — the two loader consumers.** `shared/llm/providers/unsloth.py:92` and
`shared/experiment_tracking/transformers_loss_loader.py:39` treat the string as
a **model source to load from**. With a repo id they would resolve it against
the hub. Neither runs on the prepared path, and `cloud_hf_job.py:110` proves the
cloud lane already assumes a hub id, so the balance of evidence says a repo id
is the intended value engine-wide. I could not find a local-offline caller of
either that would break, but I did not exhaustively trace their callers.

**O-4 — SETTLED, not open.** I asked whether `model_loader.py` is importable in
the suite, which would have made Candidate B behaviourally testable where
Candidate A is not. It is not: `Trainers/sft/src/model_loader.py:5` is
`from unsloth import FastLanguageModel, is_bfloat16_supported`, at module scope.
Both candidates are therefore source-assertion-only at the unit level, and
testability does not separate them. §5 has been corrected. The one behavioural
lever available to either is the negative case in `test_runtime_v1.py` described
in §5.5, which tests the *verifier* against a path-shaped value rather than
testing the stamp itself.

**O-5 — the other three trainers.** DPO, GRPO and KTO have parallel
`apply_lora_adapters` functions and presumably the same defect, but no verifier
enforces the contract for them today, and the user's ruling named the SFT lane.
Whether to fix them is a scope question for ARCHITECT, not a finding.

**O-6 — checkpoint adapter configs.** The smoke sets `save_steps: 1` and
`save_total_limit: 1`, so intermediate checkpoints are written and carry their
own `adapter_config.json`. `artifacts.retain_checkpoints` is `false` and the
verifier reads the `final_model` archive, so checkpoints appear to be out of
scope, but I did not trace the checkpoint archive path to be certain.
