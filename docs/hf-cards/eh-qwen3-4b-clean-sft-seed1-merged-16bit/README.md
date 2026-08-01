---
license: apache-2.0
base_model: unsloth/Qwen3-4B-bnb-4bit
base_model_relation: finetune
library_name: transformers
pipeline_tag: text-generation
tags:
- epistemic-humility
- abstention
- calibration
- hallucination
- qwen3
- sft
- merged
---

# Epistemic Humility: Qwen3-4B clean schema-SFT, merged 16-bit (seed 1)

A merged 16-bit model: Qwen3-4B supervised fine-tuned to answer under a
response-confidence output contract, where every response carries an answer plus
a numeric confidence in [0, 1].

This is a base artifact rather than a result in its own right. It is the stage-1
model that the response-confidence track's reinforcement-learning stage trains on
top of, and it is the same-seed baseline every comparison in that track is
measured against. It is published so that
[`professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora)
can be loaded without reconstructing a local merge.

## Status

Exploratory, seed 1, with a confirmatory replication in progress.

This model is stage 1 of the response-confidence lineage. A three-seed
confirmatory block that rebuilds that lineage at two fresh seeds is registered at
[`experiments/grpo-three-seed-confirmatory`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md); its manifest
[`experiment.yaml`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/experiment.yaml) records status `signed`, registered
2026-07-31. The track's numbers are exploratory evidence, reported separately
from and never pooled with the pre-registered plain-answer headline matrix.

## Training

- **Base model**: [`unsloth/Qwen3-4B-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-4B-bnb-4bit),
  loaded in 4-bit, maximum sequence length 2048.
- **Method**: supervised fine-tuning under the response-confidence output
  contract, 1 epoch, then the LoRA adapter merged into a 16-bit model.
- **Seed**: 1.
- **LoRA (before merge)**: rank 32, alpha 64, dropout 0.05, applied to `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.

The confidence target for each question is derived from the base model's own
32-sample probe performance on that question rather than from sequence
log-probability. Stage settings are recorded in `cell.yaml` of
[the confirmatory block](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md) and in
[the clean-mainline runbook](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md).

## Output contract

```json
{"answer": "...", "response_confidence": 0.73}
```

The contract is itself an intervention, so this model is the baseline that the
downstream arms in this track are compared against, rather than being compared to
a plain-answer arm.

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

Scored under the response-confidence contract on the full 3,369-row SelfAware
surface at seed 1.

| Metric | Value |
|---|---:|
| Refusal recall | 87.02% |
| Over-refusal | 57.51% |
| Correct-on-known | 47.23% |
| Truthful | 40.58% |
| Answer-on-unknown | 12.98% |
| Mean emitted confidence | 0.748 |
| Brier against response appropriateness | 0.364 |

Source: [`selfaware_full_run_comparison_grouped.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv), row
`Amendment E clean response-confidence / clean_sft_merged`.

## How to load

This is a full merged model in 16-bit, not an adapter.

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit"
REVISION = "ac361232c001af0ed5b0386b06dafc35d5cd31ea"

tokenizer = AutoTokenizer.from_pretrained(MODEL, revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(MODEL, revision=REVISION, device_map="auto")
```

## Intended use and limits

A research artifact and a base for the reinforcement-learning stage of this
track. It is not a deployment-ready assistant.

- Single seed. The three-seed confirmatory block has not resolved.
- One model family at one scale (Qwen3-4B), one primary evaluation surface.
- The emitted confidence scalar is close to constant in this lineage; do not read
  it as calibrated.

## Provenance

- **Revision this card describes**: `ac361232c001af0ed5b0386b06dafc35d5cd31ea`
- **Local source run directory**: `scratch/schema_response_confidence/runs/sft_schema_clean_seed1_full/20260623_123624/Qwen3-4B-bnb-4bit/merged-16bit`
- **Registered confirmatory replication**: [`experiments/grpo-three-seed-confirmatory`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/experiments/grpo-three-seed-confirmatory/AMENDMENT.md)
- **Clean-mainline runbook**: [`amendment_e_clean_mainline_runbook.md`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/experiment/phase1/grpo/amendment_e_clean_mainline_runbook.md)
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
