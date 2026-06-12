# Qwen3 4B Phase 1 Dataset Snapshot

This directory tracks the protocol budget anchor for the Qwen3 4B Phase 1
dataset build. The generated train/dev JSONL files are intentionally ignored by
git and published to Hugging Face instead.

Public HF dataset repo:
https://huggingface.co/datasets/professorsynapse/epistemic-humility-phase1

Published Qwen3 4B Phase 1 train/dev files:

- `qwen3-4b-instruct/sft_train.jsonl`
- `qwen3-4b-instruct/sft_dev.jsonl`
- `qwen3-4b-instruct/dpo_train.jsonl`
- `qwen3-4b-instruct/dpo_dev.jsonl`
- `qwen3-4b-instruct/kto_congruence_train.jsonl`
- `qwen3-4b-instruct/kto_congruence_dev.jsonl`
- `qwen3-4b-instruct/kto_correctness_safe_train.jsonl`
- `qwen3-4b-instruct/kto_correctness_safe_dev.jsonl`

The local `questions_frozen.json` file remains tracked here as the
protocol-required provenance artifact for the frozen known/unknown budget and
train/dev question-key split.
