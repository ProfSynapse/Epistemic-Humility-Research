---
name: abstentionbench-results
source: https://github.com/facebookresearch/AbstentionBench (analysis/abstention_performance.csv)
paper: "2506.09038"
paper_title: "AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions"
license: "Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0, repo LICENSE file)"
files: [abstention_performance.csv]
size: "65 KB, 624 rows"
role: meta-analysis-reanalysis (aggregated abstention operating points; second source for C3/C4)
fetched: 2026-06-10
fetched_from: "git clone --depth 1, repo snapshot also in ../repos-staging/AbstentionBench/"
tags: [dataset, epistemic-humility, abstention, over-refusal, reanalysis]
---

## What it is

The authors' released results table for AbstentionBench: abstention
**precision, recall, and F1** per (model x benchmark-subset), 624 rows.
Columns: `model_name_formatted`, `scenario_label` (6 scenarios: answer
unknown, false premise, stale, subjective, underspecified context,
underspecified intent), `dataset_name_formatted` (31 benchmark subsets, e.g.
KUQ/*, CoCoNot/*, FalseQA, GPQA-Diamond, SQuAD 2.0, UMWP, FreshQA),
`post_training_stage` (Base / Instruct / SFT / DPO / PPO RLVF for the Llama
3.1 Tulu-3 ladder; NaN for frontier models), `precision`, `recall`,
`f1_score`.

23 models: frontier (GPT-4o, Gemini 1.5 Pro, o1 + high/low reasoning, DeepSeek
R1 Distill Llama 70B, S1.1 32B), open families (Llama 3.1 8B/70B/405B Base +
Instruct, Llama 3.3 70B, Qwen2.5 32B, Mistral 7B v0.3, OLMo 7B, TinyLlamaChat),
and crucially the **Tulu 3 post-training ladder at both 8B and 70B**
(SFT → DPO → PPO RLVF; 184 rows). Most models have 30-31 rows; the o1
high/low-reasoning API variants have only 3-4 (subset runs).

Example row:
`DeepSeek R1 Distill Llama 70B, answer unknown, BB/Known unknowns, NaN, 0.9333, 0.6087, 0.7368`

## What is NOT released

Raw per-question model outputs (20 models x ~35k prompts) are **not public**:
the GitHub repo's `Results` loader (`analysis/load_results.py`) reads from a
local `base_results_dir` sweep directory, and the HF dataset
(`facebook/AbstentionBench`) contains only the benchmark loading script (see
`../abstentionbench-repo/dataset.md`). This CSV is the finest grain released.
Regenerating raw outputs requires running the pipeline (`main.py` sweeps).

## Why it matters for the meta-analysis

Precision and recall are reported SEPARATELY per model — precision on
abstention is exactly the over-refusal-adjacent quantity the literature
usually omits (false positives = abstaining on answerable items), and the
Tulu-3 ladder gives a clean Base→SFT→DPO→PPO within-family comparison at two
scales from a source independent of Cheng et al.
