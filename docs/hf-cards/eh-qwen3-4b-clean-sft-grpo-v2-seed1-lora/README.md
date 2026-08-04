---
license: apache-2.0
base_model:
- unsloth/Qwen3-4B-bnb-4bit
- professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit
base_model_relation: adapter
library_name: peft
pipeline_tag: text-generation
tags:
- epistemic-humility
- abstention
- calibration
- hallucination
- qwen3
- lora
- peft
- grpo
- rlvr
---

# Epistemic Humility: Qwen3-4B clean-SFT then GRPO-v2 adapter (seed 1)

A LoRA adapter for the reinforcement-learning stage of a response-confidence
training track. The model is trained to emit an answer together with a numeric
confidence in [0, 1], and this stage applies group-relative policy optimization
(GRPO) under the second version of the reward, which rebalanced the first
version's behavior terms.

This is the checkpoint the project's downstream mechanistic-interpretability work
loads, which is why it is released alongside the paper's adapter set.

## Status

Exploratory, seed 1, with a confirmatory replication in progress.

Every GRPO number in this track currently comes from a single seed. A three-seed
confirmatory block that rebuilds the entire GRPO-touching lineage at two fresh
seeds is registered at
[`experiments/grpo-three-seed-confirmatory`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md); its manifest
[`experiment.yaml`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/experiment.yaml) records status `signed`, registered
2026-07-31. Until that block resolves, the numbers below are exploratory
single-seed evidence.

The registration is explicit about the reporting rule: this is a tier-2
amendment whose numbers are exploratory response-confidence-track evidence,
reported separately from and never pooled with the pre-registered plain-answer
headline matrix.

## Training

- **Foundation model**: [`unsloth/Qwen3-4B-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-4B-bnb-4bit),
  loaded in 4-bit, maximum sequence length 2048.
- **Stage 1**: clean schema-SFT under the response-confidence output contract,
  merged to 16-bit and published as
  [`professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit),
  revision `ac361232c001af0ed5b0386b06dafc35d5cd31ea`.
- **Stage 2 (this adapter)**: GRPO with reward variant v2, per-device train batch
  size 32, 4 generations per prompt, 1 epoch.
- **Seed**: 1.
- **LoRA**: rank 32, alpha 64, dropout 0.05, applied to `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.

The reward variant is named in section 3 of
[the GRPO-centered stacking amendment](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-centered-stacking/AMENDMENT.md), which fixes GRPO v2 as the
accepted reward variant for this lineage; the stage hyperparameters are recorded
in `cell.yaml` of [the confirmatory block](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md) and in
[the clean-mainline runbook](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md).

## Output contract

This track uses a response-confidence contract rather than the plain-answer
contract of the headline arms: the model returns an answer plus a numeric
confidence.

```json
{"answer": "...", "response_confidence": 0.73}
```

The contract is itself an intervention, so every comparison in this track is made
against a clean-SFT baseline re-evaluated under the same contract, not against a
plain-answer arm.

## Evaluation

### How to read these numbers

The behavioral surface is SelfAware (Yin et al., 2023), a question set built to
separate questions that have an answer from questions that do not: 3,369 rows
per seed, 1,032 unknown-labeled and 2,337 known-labeled. Four metrics carry the
result, all defined in section 3.4 of the manuscript:

- **Refusal recall**: percentage of unknown rows the model refused. Higher is better.
- **Over-refusal**: percentage of known rows the model refused. Lower is better.
- **Correct-on-known**: among known rows the model chose to answer, the percentage
  answered correctly. Its denominator is the answered subset, not all known rows.
- **Truthful**: percentage of all rows either correctly answered (known) or
  correctly refused (unknown).

Both rows below are scored under the response-confidence contract on the full
3,369-row SelfAware surface at seed 1.

| Arm | Truthful | Refusal recall | Answer-on-unknown | Over-refusal | Correct-on-known | Mean confidence | Brier |
|---|---:|---:|---:|---:|---:|---:|---:|
| Clean SFT (same-seed baseline) | 40.58% | 87.02% | 12.98% | 57.51% | 47.23% | 0.748 | 0.364 |
| **This adapter (SFT then GRPO-v2)** | **41.08%** | **93.41%** | **6.59%** | **66.62%** | **53.85%** | **0.813** | **0.403** |

Source: [`selfaware_full_run_comparison_grouped.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv), rows
`Amendment E clean response-confidence / clean_sft_merged` and
`Amendment E clean response-confidence / clean_sft_grpo_v2`.

Read against its own same-seed baseline, GRPO moves answer-on-unknown from 12.98%
to 6.59% and refusal recall from 87.02% to 93.41%, at a cost of over-refusal
rising from 57.51% to 66.62%. That is the effect the confirmatory block is
registered to replicate.

### The confidence channel does not track behavior

The emitted confidence is nearly constant and close to uninformative: standard
deviation 0.0126 across all 3,369 rows, and an AUROC of 0.520 for separating
correct from wrong answers on answered known rows. A held-out linear probe on the
same rows separates known from unknown at AUROC 0.972 where the emitted
confidence reaches 0.637. Source:
[`calibration_gap_clean_sft_grpo_v2_seed1.json`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json).

Treat the numeric confidence this model emits as a formatting artifact, not as a
calibrated signal.

## How to load

This adapter was trained on the merged 16-bit clean-SFT model, not on the 4-bit
foundation model. Load the published merged base and apply the adapter to it.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit"
BASE_REVISION = "ac361232c001af0ed5b0386b06dafc35d5cd31ea"
ADAPTER = "professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora"
REVISION = "8914081dfcec4f1f025f2dbe4195d4f7aa8d210e"

tokenizer = AutoTokenizer.from_pretrained(BASE, revision=BASE_REVISION)
model = AutoModelForCausalLM.from_pretrained(BASE, revision=BASE_REVISION, device_map="auto")
model = PeftModel.from_pretrained(model, ADAPTER, revision=REVISION)
```

## Intended use and limits

A research artifact for studying abstention, calibration, and the behavior of
reinforcement learning on an abstention reward.

- Single seed. The three-seed confirmatory block has not resolved.
- One model family at one scale (Qwen3-4B), one primary evaluation surface.
- The emitted confidence scalar is collapsed and should not be read as calibrated.
- The abstention gain comes with a real over-refusal cost, quantified above.

## Provenance

- **Revision this card describes**: `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e`
- **Local source run directory**: `scratch/schema_response_confidence/runs/schema_clean_sft_grpo_v2_seed1_full/20260624_095831/final_model`
- **Registered confirmatory replication**: [`experiments/grpo-three-seed-confirmatory`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md)
- **Reward variant fixed in**: [the GRPO-centered stacking amendment](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-centered-stacking/AMENDMENT.md)
- **Staging registry**: [`docs/checkpoint-staging.md`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/docs/checkpoint-staging.md)
- **Release record**: [`docs/public-artifacts.md`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/docs/public-artifacts.md)
- **Paper**: [Training regimen manuscript](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/manuscript.md)
- **Project repository**: https://github.com/ProfSynapse/Epistemic-Humility-Research

## License

Apache-2.0, matching the `unsloth/Qwen3-4B-bnb-4bit` base model license recorded in
[the staging registry](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/docs/checkpoint-staging.md).

## Citation

Cite the paper and the exact Hugging Face revision shown on this page.

```bibtex
@misc{rosenbaum2026abstention,
  title  = {Teaching Small Language Models to Say I Don't Know: A Controlled
            Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data},
  author = {Rosenbaum, Joseph},
  year   = {2026},
  note   = {Synaptic Labs},
  howpublished = {\url{https://github.com/ProfSynapse/Epistemic-Humility-Research}}
}
```
