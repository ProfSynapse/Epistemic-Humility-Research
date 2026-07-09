---
license: mit
pretty_name: Epistemic Humility Phase 1 Evaluation Artifacts
tags:
- epistemic-humility
- abstention
- calibration
- evaluation
- qwen3
---

# Epistemic Humility Phase 1 Evaluation Artifacts

This dataset repository publishes the release-safe Phase 1 evaluation analysis
artifacts for the Epistemic Humility research program.

Source repository:
https://github.com/ProfSynapse/Epistemic-Humility-Research

Local provenance:

- Eval analysis scripts/root: `experiment/phase1/eval/analysis/`
- Paper 2 row-pattern artifacts: `papers/paper-2-training-regimen/analysis/row-pattern/`
- Results provenance inventory: `archive/papers/retired/results-provenance-inventory.md`
- Public artifact manifest: `docs/public-artifacts.md`

## Contents

The `analysis/` folder contains aggregate CSV/JSON/Markdown outputs and the
analysis scripts used to produce them, including:

- SelfAware full-run comparison tables.
- Amendment A and Amendment B transition reports.
- Paper 2 row-pattern summaries and representative examples.
- Thinking-vs-nonthinking comparison summaries.
- Sycophancy answer summaries.
- Unknown-question label analyses tied to the Paper 2 row-pattern artifacts.

## Scope And Caveats

This repository intentionally does not publish every raw local eval result
directory or scratch cache. It publishes the compact analysis layer that is most
useful for replication and review while preserving the local provenance trail in
the GitHub repository.

The results provenance inventory remains the authority for which evidence blocks
are publication-grade, amendment-scoped, exploratory, or pending reconciliation.
Do not treat all rows here as v0.3 headline evidence without checking that file.

## Citation

If you use these artifacts, cite the GitHub repository and the exact Hugging
Face revision shown on this dataset page.
