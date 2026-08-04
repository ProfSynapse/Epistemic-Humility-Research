---
license: apache-2.0
base_model: unsloth/Qwen3-4B-bnb-4bit
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
- sft
---

# Epistemic Humility: Qwen3-4B headline SFT adapter (seed 1)

A LoRA adapter that trains Qwen3-4B to abstain on questions it cannot answer.
This is the supervised fine-tuning (SFT) arm at seed 1 of a three-seed pre-registered
comparison of three training objectives, all trained cold-start from the base
model on the same frozen question budget.

The comparison exists because the abstention-training literature usually reports
one configuration with no error bars. Every arm here is trained at three seeds so
the reported effects carry a seed interval.

## Status

Pre-registered headline result. This adapter is one cell of the locked run matrix
in [PROTOCOL v0.3](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/docs/protocols/phase1/PROTOCOL.md), signed 2026-06-10 before any of these runs
launched, at the pre-registered default configuration. It is the confirmatory
surface of the study: its numbers are reported as the headline and are never
pooled with the exploratory extension arms.

## Training

- **Base model**: [`unsloth/Qwen3-4B-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-4B-bnb-4bit), loaded in
  4-bit, maximum sequence length 2048.
- **Method**: supervised fine-tuning (SFT), cold-start from the base model (no SFT warm-up stage).
- **Seed**: 1.
- **LoRA**: rank 32, alpha 64, dropout 0.05, applied to `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- **Optimization**: learning rate 2e-4, 1 epoch, per-device batch 2, gradient accumulation 4, chat template applied with `enable_thinking: false`.
- **Training file**: `sft_train.jsonl`, SHA-256 `714577a8ce6d32ace422df519690b0a96adde3985f36cab0a24404e0a92d558b` as
  recorded in the run record.

## Training data

The training files are released as a public dataset at
[`professorsynapse/epistemic-humility-phase1`](https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1). All arms are built
from one frozen question set: a known set and an unknown set of distinct source
questions, split so that train and dev question keys are disjoint after
normalizing question text. The per-method row expansion (one row per question for
SFT, one chosen/rejected pair per question for DPO, several labeled rows per
question for KTO) follows from each format rather than from a different budget.

Targets are constructed as registered in section 4 of
[the protocol](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/docs/protocols/phase1/PROTOCOL.md): known questions take the gold short answer in a fixed
template, unknown questions take a style-varied abstention phrasing drawn from a
bank in which every phrasing contains one of the evaluation refusal markers.

The public dataset excludes restricted source data; see
[the public-artifacts manifest](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/docs/public-artifacts.md) for the redistribution boundary.

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

### This adapter (seed 1)

| Metric | Value |
|---|---:|
| Refusal recall | 83.91% |
| Over-refusal | 64.31% |
| Correct-on-known | 50.00% |
| Truthful | 38.08% |
| Answer-on-unknown | 16.09% |

Source: [`selfaware_seed_metrics.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/analysis/selfaware_seed_metrics.csv), row `seed=1, arm=sft`.

### The three-seed headline for this arm

Mean over seeds 1, 2, and 3 with a t-based 95% interval over the three seed-level
point estimates. With three seeds these intervals are descriptive.

| Metric | Mean | 95% interval |
|---|---:|---|
| Refusal recall | 87.88% | 77.36 to 98.41 |
| Over-refusal | 64.77% | 63.60 to 65.94 |
| Correct-on-known | 50.21% | 49.05 to 51.36 |
| Truthful | 39.19% | 36.12 to 42.26 |

Source: [`selfaware_seed_summary.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/analysis/selfaware_seed_summary.csv), rows `arm=sft`.

## How to load

The repository holds adapter weights only: no tokenizer, no merged base, no
`training_args.bin`. Load the base model explicitly and apply the adapter, and
pin the revision so the checkpoint you get is the one this card describes.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "unsloth/Qwen3-4B-bnb-4bit"
ADAPTER = "professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora"
REVISION = "535dfabec0365b80663df618880ac2ad0976eb51"

tokenizer = AutoTokenizer.from_pretrained(BASE)
model = AutoModelForCausalLM.from_pretrained(BASE, device_map="auto")
model = PeftModel.from_pretrained(model, ADAPTER, revision=REVISION)
```

## Intended use and limits

This is a research artifact for studying abstention, calibration, and the
refusal-recall against over-refusal trade-off. It is not a deployment-ready
assistant. Three limits are worth stating plainly:

- One model family at one scale (Qwen3-4B), one primary evaluation surface.
- The headline numbers describe behavior on SelfAware. Transfer to other
  question distributions is measured separately in the paper and is not
  summarized here.
- The seed intervals come from three seeds. They are descriptive, not a
  precise uncertainty estimate.

## Provenance

- **Revision this card describes**: `535dfabec0365b80663df618880ac2ad0976eb51`
- **Local source run directory**: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft__4b__headline__seed1/20260614_053221/final_model`
- **Run record**: [`sft__4b__headline__seed1.json`](https://github.com/ProfSynapse/Epistemic-Humility-Research/tree/main/archive/experiment/phase1/run_records)
- **Registered protocol**: [PROTOCOL v0.3](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/docs/protocols/phase1/PROTOCOL.md), signed 2026-06-10
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
