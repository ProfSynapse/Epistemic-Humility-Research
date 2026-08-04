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
- kto
---

# Epistemic Humility: Qwen3-4B headline KTO adapter (seed 1)

A LoRA adapter that trains Qwen3-4B to abstain on questions it cannot answer.
This is the Kahneman-Tversky optimization (KTO) arm at seed 1 of a three-seed pre-registered
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
- **Method**: Kahneman-Tversky optimization (KTO), cold-start from the base model (no SFT warm-up stage).
- **Seed**: 1.
- **LoRA**: rank 32, alpha 64, dropout 0.05, applied to `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`.
- **Optimization**: learning rate 1e-6, 1 epoch, per-device batch 2, gradient accumulation 4.
  The materialized recipe carries no explicit `beta` override, so the
  run took the trainer default; PROTOCOL v0.3 section 3.1a registers
  beta 0.1 as the pre-registered default for this arm.
- **Training file**: `kto_congruence_train.jsonl`, SHA-256 `4d79fa505f5ae424e1fbd92f9fa5092b1006fc72858cca98579aa33e790f766e` as
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
| Refusal recall | 0.00% |
| Over-refusal | 0.17% |
| Correct-on-known | 27.05% |
| Truthful | 18.73% |
| Answer-on-unknown | 100.00% |

Source: [`selfaware_seed_metrics.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/analysis/selfaware_seed_metrics.csv), row `seed=1, arm=kto`.

### The three-seed headline for this arm

Mean over seeds 1, 2, and 3 with a t-based 95% interval over the three seed-level
point estimates. With three seeds these intervals are descriptive.

| Metric | Mean | 95% interval |
|---|---:|---|
| Refusal recall | 0.00% | 0.00 to 0.00 |
| Over-refusal | 0.14% | 0.03 to 0.26 |
| Correct-on-known | 26.95% | 26.22 to 27.69 |
| Truthful | 18.67% | 18.13 to 19.21 |

Source: [`selfaware_seed_summary.csv`](https://github.com/ProfSynapse/Epistemic-Humility-Research/blob/main/papers/paper-2-training-regimen/analysis/selfaware_seed_summary.csv), rows `arm=kto`.

### Data provenance across the three seeds

The three seeds did not all consume the same training file. Seed 1 ran on the
dataset build that predates the dev-split fix of 2026-06-14 (commit `3dc58e9b`),
which changed the builder to group the train and dev split by normalized
question text and in doing so re-randomized where the boundary falls. Seeds 2
and 3 ran on the corrected build and are identical to each other.

Both builds draw on the same question universe. The budget of 15,995 distinct
questions is unchanged, and so are the known set and the unknown set, so the fix
added and removed no questions. What moved is the train and dev boundary: 1,460
of the 14,395 train questions, 10.1% of them, were replaced by an equal number
that had been on the dev side, and the dev split itself keeps only 140 of its
1,600 questions.

This qualifies the interval in the table above. The three-seed interval for this
arm spans one pre-fix run and two post-fix runs, so part of its spread may
reflect the dataset version rather than training-seed variation alone. Read it as
a descriptive range over three runs, not as a clean estimate of seed noise. The
Training section of every card in this arm records the SHA-256 of the exact file
its run consumed, so the two groups can be told apart.

This adapter is the pre-fix run of the three. The build it trained on carried the
defect the fix cured: an audit on 2026-06-14 found 188 normalized prompt texts
present on both the train and the dev side under different source row keys,
because the source corpus carries duplicate rows with identical prompt text. All
188 carried the same known or unknown label on both sides, and the re-audit after
the rebuild found zero overlaps. This run consumed the train file only; its
materialized recipe names no dev split.

## How to load

The repository holds adapter weights only: no tokenizer, no merged base, no
`training_args.bin`. Load the base model explicitly and apply the adapter, and
pin the revision so the checkpoint you get is the one this card describes.

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = "unsloth/Qwen3-4B-bnb-4bit"
ADAPTER = "professorsynapse/eh-qwen3-4b-headline-kto-seed1-lora"
REVISION = "ebfa75363afe9a92c97b7032acd608359b2026f6"

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

- **Revision this card describes**: `ebfa75363afe9a92c97b7032acd608359b2026f6`
- **Local source run directory**: `synaptic-tuner/toolset-training-artifacts/runs/local/4b/kto__4b__headline__seed1/20260613_151337_logging_patch/final_model`
- **Run record**: [`kto__4b__headline__seed1.json`](https://github.com/ProfSynapse/Epistemic-Humility-Research/tree/main/archive/experiment/phase1/run_records)
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
