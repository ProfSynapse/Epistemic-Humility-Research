# Phase-1 eval harness (WS-4)

Research-repo-native eval harness for the Phase-1 abstention experiment
(SFT vs DPO vs KTO, plus the Cheng bridge arm). Scores each trained adapter (and
`base`) on the in-domain held-out set and the OOD sets, emits the full metric
decomposition with paired confidence intervals, deterministically and committed.

Design authority: `docs/architecture/phase1-pipeline.md` §6 (eval harness), §8
(schemas). Metric definitions: `experiment/protocol/PROTOCOL.md` v0.2 §3.5.

## Modules

| File | Responsibility |
|---|---|
| `scorers.py` | Refusal detection, word-bounded gold-alias correctness, 4-quadrant/truthful rate, refusal-recall + over-refusal, AP, token ECE (MMLU, 15 bins), accuracy retention. The Cheng primitives are a **verbatim-logic port** of the read-only `meta-analysis/analysis/reanalyze_idk_outputs.py`. |
| `stats.py` | Paired bootstrap percentile CIs + McNemar between arms on identical question sets. Seeded, deterministic. |
| `ood.py` | Loaders normalizing each OOD corpus (KUQ, CoCoNot, PopQA, SelfAware, TruthfulQA, MMLU, AbstentionBench) into the uniform eval-record contract. |
| `run_eval.py` | Config-driven driver: generate (fixture or vLLM) -> score -> stats -> provenance-stamped outputs. |
| `config/eval.yaml` | The single source of paths, sampling, bins, arms, and eval sets. No hardcoded paths/counts in code. |

## The keystone: Cheng reproduction

`tests/test_cheng_regression.py` asserts the ported scorer reproduces Cheng's
published over-refusal exactly from the on-disk outputs: **Idk-SFT 42.71%**,
**Idk-DPO 23.27%**, n=11,313, plus the full per-method reanalysis row set
(ground truth: `meta-analysis/evidence/idk-method-reanalysis.csv`). A failure
indicts a pipeline bug, not the metric. Run it first:

```bash
python3 -m pytest experiment/phase1/eval/tests/test_cheng_regression.py -q
```

## Two distinct normalizers (do not conflate)

- `normalize` — answers/aliases; keeps only `[a-z0-9]` tokens (correctness).
- `norm_question` — question-text keys; collapses whitespace, strips the HIR
  confidence prefix, **keeps punctuation**. This is the key space coder-data's
  leakage guard also uses. Conflating them silently breaks gold lookup and
  leakage detection.

## Inference boundary

Real generation (vLLM loading each adapter) is the explicit opt-in path:
`run_eval.py --live-vllm`. The default remains `FixtureGenerator`, so the
scoring + stats layers still run end to end without a model in CI.

`VLLMGenerator` builds one base model per run, supports `base` plus same-model
LoRA arms, requires an explicit loadable `model_name`, and keeps `model_tag` as
the reporting/provenance label. Use a scoped config for local GPU smoke that
contains only same-model arms such as `base`, `sft`, and `dpo`; do not include
KTO/bridge until those artifacts are ready. Qwen3 thinking is pinned off and
generated `<think>` tags fail the run instead of being stripped.

## Run

```bash
# Fixture/CI path (no model): uses pre-recorded generations under results/<arm>__<set>/
python3 experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval.yaml

# Live local path (requires vLLM/CUDA and a scoped same-model config)
python3 experiment/phase1/eval/run_eval.py --config <scoped-config.yaml> --live-vllm

# Full test suite
python3 -m pytest experiment/phase1/eval/tests/ -q
```

Outputs (§6.7): `results/<arm>__<eval_set>/{generations.jsonl,metrics.json,bootstrap_ci.json}`
and `results/comparisons/{mcnemar.csv,summary_table.csv}`. Every emitted number
carries `source / metric / model / method / verified / config_sha` provenance.

## AP confidence signal

AP (§6.4 item 3) ranks answers by a confidence signal that is **pluggable** via
`confidence.signal` in the config. The default is `self_consistency` (P_correct
agreement across N eval samples) — the architect's pinned default: it is the
more robust signal at the knowledge frontier and is directly R-Tuning-comparable.
`seq_logprob` is the swappable alternative. Each run records its
`confidence_source` and `confidence_n_samples` in `metrics.json` so AP numbers
are provenance-traceable and a later logprob run is distinguishable from a
self-consistency one.

`confidence.n_samples` is the AP-specific self-consistency budget, kept separate
from the probe's 32: AP only needs a ranking, not a fine P_correct estimate, so a
smaller N (default 8) keeps the OOD-sweep eval cost under the ceiling.
