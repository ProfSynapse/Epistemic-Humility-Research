---
license: apache-2.0
base_model:
- unsloth/Qwen3-4B-bnb-4bit
- professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora
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
- dpo
- sequential-training
---

# Epistemic Humility: Qwen3-4B sequential SFT then DPO adapter (seed 1)

A LoRA adapter for the second stage of a two-stage abstention regimen: supervised
fine-tuning first to induce refusal behavior at all, then direct preference optimization (DPO) on top
of it to refine where the refusal boundary sits. This is seed 1 of three.

The cold-start comparison that this extends found that preference training alone
does not induce abstention on this model at this scale. The question this arm
answers is whether preference training helps once SFT has already installed the
behavior.

## Status

Pre-registered extension. This adapter belongs to the sequential extension signed
off on 2026-06-14 as a prospective addition to the locked matrix, recorded in
section "Amendment A / v0.4 status" of [the protocol](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/docs/protocols/phase1/PROTOCOL.md) and in
[the amendment governance note](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/common/amendment-governance.md).

Its numbers are reported separately from the headline matrix and are never pooled
with it. The protocol states the rule directly: mixed-stage results must be
labeled as extension results unless a later signed revision explicitly supersedes
the matrix.

## Training

- **Foundation model**: [`unsloth/Qwen3-4B-bnb-4bit`](https://huggingface.co/unsloth/Qwen3-4B-bnb-4bit),
  loaded in 4-bit, maximum sequence length 2048.
- **Stage 1**: the same-seed headline SFT adapter
  ([`professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora`](https://huggingface.co/professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora), revision
  `535dfabec0365b80663df618880ac2ad0976eb51`), merged into a 16-bit model.
- **Stage 2 (this adapter)**: direct preference optimization (DPO) trained on top of that merged
  16-bit model.
- **Seed**: 1.
- **LoRA**: rank 32, alpha 64, dropout 0.05, applied to `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- **Optimization**: learning rate 5e-6, 1 epoch, per-device batch 2, gradient accumulation 4.
  The materialized recipe carries no explicit `beta` override, so the
  run took the trainer default; PROTOCOL v0.3 section 3.1a registers
  beta 0.1 as the pre-registered default for this arm.
- **Training file**: `dpo_train.jsonl`, SHA-256 `39e2ba8c9bc1b41ef1b7e797f80637c276ba150c97055962bbc4e2b550bd17b5` as
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
| Refusal recall | 48.84% |
| Over-refusal | 13.99% |
| Correct-on-known | 25.47% |
| Truthful | 30.16% |

Source: [`amendment_a_selfaware_summary.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/analysis/amendment_a_selfaware_summary.csv), row `seed1_all / sft_dpo`.

Across the three seeds this arm averages refusal recall 52.81%, over-refusal 14.59%, truthfulness 31.18%
(section 4.2 of [the manuscript](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/manuscript.md)).

## How to load

The stage-1 model this adapter was trained on is a local 16-bit merge that is not
itself published. Rebuild it from the two published pieces, then apply this
adapter on top. Merging a 4-bit base with its LoRA into 16-bit reproduces the
training-time construction; it is not guaranteed to be bit-identical to the local
artifact.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

FOUNDATION = "unsloth/Qwen3-4B-bnb-4bit"
STAGE1 = "professorsynapse/eh-qwen3-4b-headline-sft-seed1-lora"
STAGE1_REVISION = "535dfabec0365b80663df618880ac2ad0976eb51"
ADAPTER = "professorsynapse/eh-qwen3-4b-seq-sft-dpo-seed1-lora"
REVISION = "45138e73be9d28fcf9537a9d2de49d90ebf8601b"

tokenizer = AutoTokenizer.from_pretrained(FOUNDATION)
base = AutoModelForCausalLM.from_pretrained(FOUNDATION, device_map="auto")

stage1 = PeftModel.from_pretrained(base, STAGE1, revision=STAGE1_REVISION)
stage1 = stage1.merge_and_unload()

model = PeftModel.from_pretrained(stage1, ADAPTER, revision=REVISION)
```

## Intended use and limits

This is a research artifact for studying abstention and the refusal-recall
against over-refusal trade-off. It is not a deployment-ready assistant.

- One model family at one scale (Qwen3-4B), one primary evaluation surface.
- Extension evidence, reported separately from the pre-registered headline
  matrix and not pooled with it.
- Loading requires reconstructing the stage-1 merge described above.

## Provenance

- **Revision this card describes**: `45138e73be9d28fcf9537a9d2de49d90ebf8601b`
- **Local source run directory**: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/sft_dpo__4b__amendment_a__seed1/20260614_074933/final_model`
- **Run record**: [`sft_dpo__4b__amendment_a__seed1.json`](https://github.com/ProfSynapse/Epistemic-Humility-Research/tree/main/archive/experiment/phase1/run_records)
- **Registered protocol and extension sign-off**: [PROTOCOL v0.3](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/archive/docs/protocols/phase1/PROTOCOL.md)
- **Amendment governance**: [`papers/common/amendment-governance.md`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/common/amendment-governance.md)
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
