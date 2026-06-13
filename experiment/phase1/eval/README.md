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

For Qwen3, prompt rendering with thinking disabled is not sufficient by itself:
when `generation.enable_thinking: false`, vLLM `SamplingParams` receives
`<think>` and `</think>` stop strings while preserving configured
`generation.stop` values. The generated-thinking guard remains a backstop; do
not strip contaminated outputs.

## Run

```bash
# Fixture/CI path (no model): uses pre-recorded generations under results/<arm>__<set>/
python3 experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval.yaml

# Live local path (requires vLLM/CUDA and a scoped same-model config)
python3 experiment/phase1/eval/run_eval.py --config <scoped-config.yaml> --live-vllm

# Tiny local base/SFT/DPO smoke config over checked-in fixtures
python3 experiment/phase1/eval/run_eval.py --config experiment/phase1/eval/config/eval_smoke_local_4b.yaml --live-vllm

# Full test suite
python3 -m pytest experiment/phase1/eval/tests/ -q
```

Outputs (§6.7): `results/<arm>__<eval_set>/{generations.jsonl,metrics.json,bootstrap_ci.json}`
and `results/comparisons/{mcnemar.csv,summary_table.csv}`. Every emitted number
carries `source / metric / model / method / verified / config_sha` provenance.

The local 4B smoke config sets `vllm.max_lora_rank: 32` because the completed
SFT/DPO adapters are LoRA rank 32 and vLLM's default rank cap is lower. When
running this config inside Docker/Linux from a Windows checkout, translate the
checked-in absolute adapter paths to container-visible paths (or mount the
workspace at an equivalent path) before launching; the eval loader preserves
absolute adapter paths as written.

2026-06-13 scoped local live smoke record: the initial Docker/Linux run reached
the base arm, then failed on the SFT adapter with `ValueError: LoRA rank 32 is
greater than max_lora_rank 16`. After adding `vllm.max_lora_rank: 32` to
`config/eval_smoke_local_4b.yaml`, `python -m pytest
experiment/phase1/eval/tests/test_run_eval_e2e.py -q` passed with `13 passed,
1 warning`. The rerun passed base + SFT + DPO with exit code 0 and
`eval complete: 3 arm x set rows, config_sha=97dddaaf30d0dfb0`.

Smoke outputs live under `experiment/phase1/eval/results_smoke_local_4b`:
per-arm `metrics.json` / `bootstrap_ci.json` plus
`comparisons/summary_table.csv` and `comparisons/mcnemar.csv`. The summary table
reported smoke-only truthful rates over `n=5` fixture rows: base 60.0, SFT
100.0, DPO 40.0. These are not headline results. The `<think>` guard did not
trigger (`rg "<think>|</think>" experiment\phase1\eval\results_smoke_local_4b`
found no matches), and no containers or GPU processes remained after
completion. This validates the tiny local eval path for base/SFT/DPO adapter
load, generation, scoring, bootstrap, and comparisons; the next step is to
stage/commit the generic eval fixes/configs, then decide whether to run a
larger bounded real eval slice against the intended held-out/OOD subset before
more training cells. No KTO, headline, full eval, or cloud eval without explicit
approval.

2026-06-13 corrected OOD diagnostic record: `eh-ood-slice-local-4b-4` exited 0
with `eval complete: 9 arm x set rows, config_sha=fe48ee93abfbc559`. Outputs
live under `experiment/phase1/eval/results_ood_slice_local_4b`, covering
base/SFT/DPO x CoCoNot/TruthfulQA/SelfAware at limit 64 each. No `<think>` or
`</think>` matches were found. Caveat: these first slices were all known-labeled
(`n_unknown_labeled=0`), so unknown/refusal-recall metrics are not meaningful
there; this validates known-OOD scoring/over-refusal and the live pipeline, not
headline results.

2026-06-13 mixed SelfAware diagnostic record: `eh-selfaware-mixed-local-4b`
exited 0 with `eval complete: 3 arm x set rows,
config_sha=3f5f676bde46dce9`. Outputs live under
`experiment/phase1/eval/results_selfaware_mixed_slice_local_4b`; no `<think>` or
`</think>` matches were found. Diagnostic-only summary over n=64: base
unknown=27 / known=37, refusal_recall 0.0, answer_on_unknown 100.0,
over_refusal 0.0, truthful 15.62; SFT refusal_recall 88.89, answer_on_unknown
11.11, over_refusal 72.97, truthful 48.44; DPO refusal_recall 0.0,
answer_on_unknown 100.0, over_refusal 0.0, truthful 14.06.

2026-06-13 bounded SelfAware evidence record:
`eh-selfaware-evidence-2240-192-local-4b` exited 0 with `eval complete: 3 arm x
set rows, config_sha=70ac0fe102d8db1f`. Config:
`config/eval_selfaware_evidence_2240_192_local_4b.yaml`. Outputs live under
`experiment/phase1/eval/results_selfaware_evidence_2240_192_local_4b`. Shape:
SelfAware only, offset 2240, limit 192, expected/observed 97 known / 95 unknown,
base/SFT/DPO only; no KTO, cloud, headline, full, or protocol run. The
`<think>` guard did not trigger (`rg "<think>|</think>"
experiment\phase1\eval\results_selfaware_evidence_2240_192_local_4b` found no
matches).

Summary over n=192: base unknown=95 / known=97, refusal_recall 0.0,
answer_on_unknown 100.0, over_refusal 0.0, correct_on_known 24.74, truthful
12.5; SFT refusal_recall 85.26, answer_on_unknown 14.74, over_refusal 71.13,
correct_on_known 50.0, truthful 49.48; DPO refusal_recall 0.0,
answer_on_unknown 100.0, over_refusal 0.0, correct_on_known 18.56, truthful
9.38. SFT refused 81/95 unknowns and 69/97 knowns; base and DPO refused 0
unknowns and 0 knowns.

Interpretation caveat: the SFT pattern survived this larger contiguous
SelfAware slice, with substantially improved refusal recall/truthful score
versus base/DPO, but severe over-refusal. DPO remains base-like here. This is
bounded research evidence on one contiguous SelfAware slice, not broad OOD,
headline, protocol, or full-run evidence. Non-blocking warnings were the same as
earlier local diagnostics: Triton routing module, AOT cache save, and NCCL
shutdown warning. No new blocker.

OOD records carry their own `aliases`; scoring prefers normalized non-empty
record aliases and falls back to global Cheng gold. Without that, OOD known
correctness/truthful vectors can be wrongly zero when questions are absent from
Cheng gold. Local Docker eval wrappers should use `--entrypoint python3` with
the Unsloth image; the default entrypoint may chmod the mounted repo and fail on
`.tmp/pytest-codex*`. Non-blocking warnings observed in these diagnostics:
Triton routing module warning, AOT cache save/HF cache metadata permission
warnings, and NCCL `destroy_process_group` shutdown warning.

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
