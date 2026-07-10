---
license: mit
pretty_name: Epistemic Humility locked training-regimen Training Data
tags:
- epistemic-humility
- abstention
- calibration
- qwen3
- fine-tuning
---

# Epistemic Humility locked training-regimen Training Data

This dataset contains the redistributable Qwen3 4B locked training-regimen training/dev
artifacts for the Epistemic Humility research program.

The files are generated from the local repository:

- GitHub project: https://github.com/ProfSynapse/Epistemic-Humility-Research
- Local provenance root: `archive/experiment/phase1/data/qwen3-4b-instruct/`
- Public artifact manifest: `docs/public-artifacts.md`
- Protocol: `archive/docs/protocols/phase1/PROTOCOL.md`

## Contents

```text
qwen3-4b-instruct/sft_train.jsonl
qwen3-4b-instruct/sft_dev.jsonl
qwen3-4b-instruct/dpo_train.jsonl
qwen3-4b-instruct/dpo_dev.jsonl
qwen3-4b-instruct/kto_congruence_train.jsonl
qwen3-4b-instruct/kto_congruence_dev.jsonl
qwen3-4b-instruct/kto_correctness_safe_train.jsonl
qwen3-4b-instruct/kto_correctness_safe_dev.jsonl
qwen3-4b-instruct/build_manifest.json
qwen3-4b-instruct/questions_frozen.json
```

`questions_frozen.json` records the frozen known/unknown budget and train/dev
question-key split used by the locked training-regimen build. `build_manifest.json` records the
local build parameters and count assertions.

## Scope

This release is limited to redistributable Qwen3 4B locked training-regimen artifacts. It does
not include restricted bridge data, OpenMOSS/Cheng raw data, local cache dumps,
or model checkpoints.

## Citation

If you use this data, cite the repository and the exact Hugging Face revision
shown on the dataset page.
