---
name: reward-calibration (PPO-M released training data, sampled)
source: https://github.com/SeanLeng1/Reward-Calibration ; data on HF HINT-lab/calibration_preference_mixture_final-v0.1 and HINT-lab/prompt-collections-final-v0.3
paper: "2410.09724"
paper_title: "Taming Overconfidence in LLMs: Reward Calibration in RLHF"
license: "Apache License 2.0 (repo LICENSE file); both HF datasets carry no license tag — verify before redistribution"
files: [calibration_preference_mixture.sample2400.jsonl, prompt_collections.sample.jsonl]
size: "~32 MB (stratified samples; full sets are 25,524 and 20,480 rows, ~147 MB combined parquet)"
role: reference-train-data (calibrated reward modeling preference pairs)
fetched: 2026-06-10
fetched_from: "HF parquet API (datasets-server auto-converted shards), stratified head-sampled per source dataset"
tags: [dataset, epistemic-humility, calibration, preference-pairs, reward-model, reference]
---

## What it is

The released training data for PPO-M (calibrated reward modeling), Leng et
al. 2024. Two stratified samples:

1. **`calibration_preference_mixture.sample2400.jsonl`** — 2,400 of 25,524
   rows (head-200 per `dataset_name`; full mix: ultrafeedback 2,823, hh_rlhf
   2,500, simple_math 2,500, math_dpo 2,384, code_vulnerability 2,372, pku
   2,336, orca 2,271, shp 2,052, capybara 1,758, code_feedback 1,709,
   helpsteer2 1,534, helpsteer 1,285). Schema per row: `chosen` / `rejected`
   (message lists: {role, content}), `dataset_name`, plus four
   confidence-augmented variants `chosen_high`, `chosen_low`,
   `rejected_high`, `rejected_low` — the same chosen/rejected answers
   prefixed with a system prompt eliciting a 0-10 verbalized confidence.
   This is the CRM (calibrated reward model) training set: the RM is trained
   so reward(chosen_high) > reward(chosen_low) and reward(rejected_low) >
   reward(rejected_high).
2. **`prompt_collections.sample.jsonl`** — 1,020 of 20,480 rows (head-170 per
   `dataset`; full mix: UltraFeedback 7,990, UltraInteract 7,848, OpenOrca
   1,641, Capybara 1,428, HelpSteer 1,064, DIBT 509). Schema: `dataset`,
   `context`, `context_messages`, `id`, `prompt` (message list),
   `confidence_prompt` (same prompt + confidence-elicitation system prompt),
   `modified` (bool). These are the PPO rollout prompts.

Refetch full sets:
`curl -L https://huggingface.co/api/datasets/HINT-lab/calibration_preference_mixture_final-v0.1/parquet/default/train/0.parquet`
(96.9 MB) and `.../HINT-lab/prompt-collections-final-v0.3/parquet/default/train/0.parquet` (44.4 MB).

## What is NOT released

No per-question eval outputs or per-benchmark result files exist in the repo
or on HF — eval numbers live only in README tables (ECE/MT-Bench/Arena-Hard
per model) and the paper. The repo's `dataset/` folder is unmodified
third-party benchmark inputs (GSM8K, TruthfulQA, SciQ, BBH, CommonsenseQA,
MMLU professional). The trained models ARE released on HF (HINT-lab org):
llama3-8b-final-{ppo,ppo-m,ppo-c}-v0.3, mistral-7b-ppo{,-m,-c}-hermes,
llama3-8b-crm-final-v0.1 (calibrated RM), mistral-7b-hermes-{rm,crm}-skywork,
plus DPO/CDPO variants — so per-question outputs are regenerable locally.

## Why it matters for the meta-analysis

The only released preference-pair dataset purpose-built for confidence
calibration (C5 targeted interventions). Its high/low confidence-augmentation
construction is directly reusable as a KTO recipe template for our
experiment, and the chosen/rejected pairs can be re-labeled for an
abstention-aware KTO variant (gap: no KTO-for-calibration exists).
