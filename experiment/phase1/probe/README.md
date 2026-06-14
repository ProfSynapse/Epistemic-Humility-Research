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
| `config/hidden_state_probe.yaml` | Pinned hidden-state extraction config (hashed SSOT) |
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

Outputs land in
`experiment/phase1/probe/<model_tag>/hidden_states/<extraction_id>/`:

- per-row `*_h_base.safetensors` / `*_h_lora.safetensors` / `*_delta.safetensors`
- `rows.jsonl` (per-row alignment + prompt hash + config sha)
- `manifest.json` (exhaustive provenance + crash-safe status/verified)

The whole `hidden_states/` tree is gitignored (large reproducible tensor
artifacts). The GPU-free deps (`pyyaml`/`numpy`/`safetensors`) are enough to run
the schema/config/selection/stub pipeline and its tests; `torch`/`transformers`/
`peft` are lazy-imported and needed only for the real forward.

## Tests

```
cd experiment/phase1/probe
python -m pytest tests/ -q
```
