# Phase 1 knowledge probe (Component A, WS-1)

Estimates, for every TriviaQA train-split question, this model's `P_correct`
under its own generation, and captures its wrong answers (the downstream
KTO/DPO negatives). Produces the `probe_results.jsonl` contract that the WS-2
dataset builders consume.

## Files

| File | Role |
|---|---|
| `probe.py` | Driver: load pool, checkpointed probe, score, label, write outputs |
| `backends.py` | vLLM (real GPU) and Stub (GPU-free) backends + the shared `render_probe_prompt` helper both tiers use |
| `scoring.py` | Correctness primitives ported from the Cheng-validated scorer |
| `config/probe.yaml` | Pinned, pre-registered sampling config (N=32, T=1.0, thinking off) |
| `hidden_state_probe.py` | Hidden-state extraction tier driver (HF+PEFT forward; base/LoRA/delta; exploratory) |
| `hidden_state_schema.py` | Model-free validation + manifest builder for the hidden-state tier (GPU-free keystone) |
| `hidden_state_linear_probe.py` | Diagnostic per-layer linear probes over extracted hidden states (smoke/analysis only) |
| `hidden_state_directions.py` | Candidate direction data layer for later intervention pilots; no steering/generation |
| `phase3_causal_pilot_sweep.py` | Non-GPU-by-default planner/executor for reusable local causal-pilot sweeps |
| `phase3_causal_pilot_aggregate.py` | Offline aggregation of completed causal-pilot run manifests and metrics |
| `config/hidden_state_probe.yaml` | Pinned hidden-state extraction config (hashed SSOT) |
| `config/phase3_causal_pilot_full_candidates.yaml` | Full local candidate inventory for comparable Phase 3 causal-pilot sweeps |
| `config/phase3_causal_pilot_local_sweep.yaml` | Reusable local mech-interp sweep plan across current candidate directions |
| `requirements-hidden-state.txt` | Inference deps for the hidden-state tier, decoupled from the trainer pins |
| `tests/` | GPU-free smoke tests on a fixture |

## Prerequisites

1. WS-0 fetch must have run (post sign-off):
   `python datasets/scripts/fetch_datasets.py --only triviaqa-rc-nocontext`
   produces `datasets/triviaqa-rc-nocontext/train.jsonl`.
2. `vllm` installed on a CUDA host (the RTX 3090 pilot). vLLM is imported
   lazily, so the module loads and tests run without it.

## Run (real probe, post sign-off)

```
cd experiment/phase1/probe
python probe.py --config config/probe.yaml
```

Outputs land in `experiment/phase1/probe/<model_tag>/`:

- `probe_results.jsonl` (one record per question, the A to B contract)
- `probe_manifest.json` (model, sampling config, prompt, split source, counts)
- `sensitivity_grid.json` (label-noise sensitivity analysis)

The probe is **resumable**: results are appended keyed by `question_id`, and a
restart skips ids already present. Per-question seeds are derived from the
master seed plus the `question_id`, so a resumed run reproduces skipped
questions exactly.

## enable_thinking=False

The Qwen3 thinking toggle is pinned OFF for all of Phase 1. The probe passes
`enable_thinking=False` through `apply_chat_template` / vLLM
`chat_template_kwargs`, AND runs a runtime self-check
(`assert_no_think_scaffolding`) that aborts loudly if `<think>` scaffolding
leaks into a rendered prompt, so a template that silently ignores the kwarg
fails on the first real run instead of contaminating probe outputs. See the
`backends.py` header for what was verified offline vs deferred to the first
GPU run.

## Hidden-state extraction (exploratory mechanism tier)

> **Separate from the stochastic knowledge probe above.** This tier is
> exploratory mechanism tooling. It stays OFF the locked PROTOCOL v0.3 headline
> path and the Amendment A / v0.4 track, writes to its own output subtree, and
> NEVER mutates `probe_results.jsonl` or any run record (it links them by id).

`hidden_state_probe.py` runs a deterministic base-vs-LoRA forward pass and
persists `h_base`, `h_lora`, and `delta = h_lora − h_base` at the final prompt
token across all layers, for a matched known/unknown slice of the **frozen**
split. The research question is whether abstention training changes the model's
internal knowledge state or only its surface refusal policy; this MVP is the
correlational extraction harness (linear probes and causal/patching work are a
deferred later phase).

### Why HF + PEFT, not vLLM

The harness uses a plain Hugging Face **Transformers + PEFT** forward path, not
vLLM. vLLM does not expose `output_hidden_states`, and **vLLM v0.18.0+
hidden-state extraction was evaluated and rejected** (it is disk / speculative-
decode oriented, has no adapter contrast, and its LoRA path merges-at-load — so
it cannot serve the in-process per-layer base-vs-LoRA contrast this tier needs).
Do not reopen that pivot.

### Design

- **Adapter-state confound guard (two-tier).** A GPU-free pre-flight
  (`hidden_state_schema.validate_arm_states`) rejects any config that does not
  pair exactly one disabled/unloaded base arm with exactly one active arm
  (catching the silent adapter-active-vs-adapter-active confound); a GPU-smoke
  `h_base != h_lora` assertion (built later) is the second tier.
- **Deterministic forward.** `model.eval()`, `use_cache=False`,
  `torch.no_grad()`, batch=1, fixed dtype/device — so the last prompt token is
  unambiguous (never a literal `-1` under left padding).
- **dtype policy.** Persist fp32 as an EXPLICIT conversion: the manifest records
  both `compute_dtype` (model native) and `persist_dtype` (fp32). No silent cast,
  no compression.
- **Crash-safe manifest.** The manifest is written with `status:"launched"`
  BEFORE the forward, then patched to `ok`/`failed`; `verified` is set True only
  after the emitted tensors are checked. A `launched` manifest left on disk is a
  self-evident crashed/partial extraction.
- **Shared render path.** Both this tier and `VLLMBackend` call
  `backends.render_probe_prompt`, so they render byte-identically and cannot
  drift in `enable_thinking=False` thinking-tag handling.
- **Leakage discipline.** The slice is selected from `questions_frozen.json`
  keys and aligned to `probe_results.jsonl` by `probe_pool_row_key` only (never
  loose question text); `probe_results.jsonl` is streamed, never whole-loaded.

### Install + run (real extraction, GPU)

```
pip install -r experiment/phase1/probe/requirements-hidden-state.txt
cd experiment/phase1/probe
python hidden_state_probe.py --config config/hidden_state_probe.yaml
```

On this Windows desktop, prefer the Docker/Unsloth path for real Qwen3-4B
4-bit extraction. Native Python can see CUDA, but the current `bitsandbytes`
stack fails the model load with `ModuleNotFoundError: triton.ops`. Use a temp
Docker config with container-native adapter paths (`/workspace/repo/...`) and
pass Git safe-directory env vars so manifest provenance can finalize:

```
docker run --rm --gpus all \
  -e GIT_CONFIG_COUNT=1 \
  -e GIT_CONFIG_KEY_0=safe.directory \
  -e GIT_CONFIG_VALUE_0=/workspace/repo \
  -v "F:\Code\Epistemic-Humility-Research:/workspace/repo" \
  -v hf-cache:/root/.cache/huggingface \
  -w /workspace/repo \
  --entrypoint python3 unsloth/unsloth:latest \
  experiment/phase1/probe/hidden_state_probe.py \
  --config .tmp/hidden_state_probe_sft_mvp_docker.yaml
```

The `hf-cache` Docker volume keeps model cache data out of the git workspace.
Without the Git safe-directory environment, Docker can write tensor rows but
fail the final manifest gate with missing `research_repo_commit` and
`submodule_commit`.

Local merged model directories are valid extraction bases. For those local
paths, `hidden_state_probe.py` records `base_model_revision` and
`base_model_hash` as `local-sha256:<digest>` in the manifest. This preserves the
strict finalize gate for populated provenance while leaving Hub commit behavior
unchanged for Hub-hosted model ids.

Outputs land in
`experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/`:

- per-row `*_h_base.safetensors` / `*_h_lora.safetensors` / `*_delta.safetensors`
- `rows.jsonl` (per-row alignment + prompt hash + config sha)
- `manifest.json` (exhaustive provenance + crash-safe status/verified)

The whole `hidden_states/` tree is gitignored (large reproducible tensor
artifacts). The GPU-free deps (`pyyaml`/`numpy`/`safetensors`) are enough to run
the schema/config/selection/stub pipeline and its tests; `torch`/`transformers`/
`peft` are lazy-imported and needed only for the real forward.

### Diagnostic linear probes

After extraction, `hidden_state_linear_probe.py` can run a small per-layer
known-vs-unknown diagnostic over `h_base`, `h_lora`, and `delta`:

```
python experiment/phase1/probe/hidden_state_linear_probe.py \
  experiment/phase1/probe/qwen3-4b-instruct/hidden_states/<extraction_id>
```

It writes `hidden_state_linear_probe_diagnostic.csv` and `.json` into the
extraction directory by default. The method is leave-one-out ridge linear
classification with fold-local standardization and an intercept, implemented
with only `numpy` and `safetensors`. Every output is stamped
`DIAGNOSTIC_SMOKE_ONLY`; this is pipeline validation and exploratory analysis,
not pre-registered headline evidence.

The default cross-validation remains leave-one-out. For larger local slices,
use stratified k-fold explicitly:

```
python experiment/phase1/probe/hidden_state_linear_probe.py \
  experiment/phase1/probe/qwen3-4b-instruct/hidden_states/<extraction_id> \
  --cv stratified_kfold --cv-folds 5 \
  --prefix hidden_state_linear_probe_kfold5_diagnostic
```

### Candidate directions

`hidden_state_directions.py` derives normalized candidate vectors from an
existing extraction directory for later causal intervention pilots:

```
python experiment/phase1/probe/hidden_state_directions.py \
  experiment/phase1/probe/qwen3-4b-instruct/hidden_states/<extraction_id>
```

It writes `hidden_state_candidate_directions.csv`,
`hidden_state_candidate_directions.manifest.json`, and per-direction
`directions/*.safetensors` shards. Current candidates are
`unknown_mean_minus_known_mean` over `h_base`/`h_lora`/`delta`, plus mean
`delta = h_lora - h_base` vectors for all/known/unknown rows. This is only the
reusable data/direction layer: it does not run steering, generation, SAE/SAELens,
or NNsight, and it is not headline or pre-registered evidence.

### Phase 3 causal-pilot sweep

`phase3_causal_pilot_sweep.py` wraps the live runner across candidate directions
and modes without touching model packages by default. It plans commands from a
checked-in sweep config and only invokes `phase3_causal_pilot_runner.py` when
`--execute` and the mode-specific allow flags are passed.

Plan the current local sweep without GPU/model loading:

```
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml
```

Write a durable plan and per-candidate runner configs, still without running
generation or diagnostics:

```
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --write-plan --materialize-configs
```

To plan or materialize only logit diagnostics from the full config without
including generation jobs:

```
python experiment/phase1/probe/phase3_causal_pilot_sweep.py \
  --config experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml \
  --mode-filter logit_diagnostic --write-plan --materialize-configs
```

After an explicitly approved local GPU run creates result folders, aggregate
completed manifests offline:

```
python experiment/phase1/probe/phase3_causal_pilot_aggregate.py \
  --root experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep \
  --out experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
```

The default sweep config uses the 9-candidate inventory in
`config/phase3_causal_pilot_full_candidates.yaml`, while materialized execution
configs inherit the generation-enabled guardrails from
`config/phase3_causal_pilot_gpu_smoke.yaml`. The checked-in sweep plans Docker
commands for live GPU execution with `/workspace/repo/...` runner/config paths,
not host Python commands. The base-original `h_base` candidate is inventoried
but skipped by default because the current live runner loads adapter-backed
models from extraction provenance and does not yet provide a safe adapterless
base intervention path.

Latest comparable local 128x128 diagnostics use the same 128 known / 128
unknown slice and 5-fold balanced-accuracy readout. All listed extractions
wrote 256 rows, 768 safetensors, manifest `status=ok` / `verified=true`, and
had no `<think>` / `</think>` / `reasoning_content` matches.

| Arm | Temp config | Extraction | Best `h_base` | Best `h_lora` | Best `delta` |
|---|---|---|---:|---:|---:|
| SFT | `.tmp/hidden_state_probe_sft_128x128_docker.yaml` | `qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8` | 0.75390625 L25 | 0.86328125 L36 | 0.85546875 L35 |
| DPO | `.tmp/hidden_state_probe_dpo_128x128_docker.yaml` | `qwen3-4b-instruct/hidden_states/extraction__f3dbd2c1754a` | 0.75390625 L25 | 0.7734375 L35 | 0.75 L35 |
| KTO | `.tmp/hidden_state_probe_kto_128x128_docker.yaml` | `qwen3-4b-instruct/hidden_states/extraction__0810aa2972e8` | 0.75390625 L25 | 0.765625 L36 | 0.75 L26 |

Plain read: the base pass is identical across arms, while the SFT adapter and
delta show stronger known-vs-unknown separability than cold-start DPO/KTO. This
is consistent with bounded behavioral evidence that preference-only DPO/KTO
runs stayed base-like. Treat these as exploratory mechanism/local diagnostics
only, not headline or pre-registered evidence.

Sequential Amendment A local diagnostics use the merged grouped-SFT model as
the base and then apply the sequential preference adapter as the active LoRA.
Both listed extractions used the same 128 known / 128 unknown slice, wrote 256
rows and 768 safetensors, finalized manifest `status=ok` / `verified=true`, had
no `<think>` / `</think>` / `reasoning_content` matches, and recorded
`base_model_revision` / `base_model_hash` as
`local-sha256:813a8a882a07871b2167948931791f69ad19add8b7c4e6cf2faef0a25e1fbdcd`.

| Sequential arm | Extraction | Best `h_base` | Best `h_lora` | Best `delta` |
|---|---|---:|---:|---:|
| `sft_dpo` | `qwen3-4b-instruct/hidden_states/extraction__0d58c201ab3e` | 0.84375 L36 | 0.85546875 L34 | 0.859375 L35 |
| `sft_kto` | `qwen3-4b-instruct/hidden_states/extraction__e1473df788a5` | 0.84375 L36 | 0.859375 L35 | 0.85546875 L36 |

Comparative caveat: in these sequential runs, `h_base` is the merged SFT model,
not original Qwen, so the base representation already includes SFT. `delta` is
therefore the preference-stage change over SFT. Plain read: SFT creates high
separability; cold-start DPO/KTO do not; sequential DPO/KTO preserve or reshape
the high SFT separability.

## Tests

```
cd experiment/phase1/probe
python -m pytest tests/ -q
```
