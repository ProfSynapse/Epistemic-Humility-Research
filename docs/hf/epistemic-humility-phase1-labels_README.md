---
license: mit
pretty_name: Epistemic Humility Phase 1 Knowledge Labels
tags:
- epistemic-humility
- knowledge-boundary
- abstention
- qwen3
- labels
---

# Epistemic Humility Phase 1 Knowledge Labels

This dataset repository publishes compact, reproducible label/probe artifacts
for the Qwen3 4B Phase 1 knowledge-boundary split.

Source repository:
https://github.com/ProfSynapse/Epistemic-Humility-Research

Local provenance:

- Frozen question split: `experiment/phase1/data/qwen3-4b-instruct/questions_frozen.json`
- Probe manifest: `experiment/phase1/probe/qwen3-4b-instruct/probe_manifest.json`
- Sensitivity grid: `experiment/phase1/probe/qwen3-4b-instruct/sensitivity_grid.json`
- Public artifact manifest: `docs/public-artifacts.md`

## Contents

```text
qwen3-4b-instruct/questions_frozen.json
qwen3-4b-instruct/probe_manifest.json
qwen3-4b-instruct/sensitivity_grid.json
```

These files are enough to inspect the frozen train/dev knowledge-boundary split
and the probing setup without downloading local cache dumps.

## Scope And Caveats

The large local `probe_results.jsonl` cache is not included in this release.
It is treated as a reproducible intermediate cache, not a compact public label
artifact. Restricted bridge/OpenMOSS/Cheng raw data is also excluded.

## Citation

If you use these labels, cite the GitHub repository and the exact Hugging Face
revision shown on this dataset page.
