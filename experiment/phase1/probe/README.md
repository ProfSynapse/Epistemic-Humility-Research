# Phase 1 knowledge probe (Component A, WS-1)

Estimates, for every TriviaQA train-split question, this model's `P_correct`
under its own generation, and captures its wrong answers (the downstream
KTO/DPO negatives). Produces the `probe_results.jsonl` contract that the WS-2
dataset builders consume.

## Files

| File | Role |
|---|---|
| `probe.py` | Driver: load pool, checkpointed probe, score, label, write outputs |
| `backends.py` | vLLM (real GPU) and Stub (GPU-free, for tests) backends |
| `scoring.py` | Correctness primitives ported from the Cheng-validated scorer |
| `config/probe.yaml` | Pinned, pre-registered sampling config (N=32, T=1.0, thinking off) |
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

## Tests

```
cd experiment/phase1/probe
python -m pytest tests/ -q
```
