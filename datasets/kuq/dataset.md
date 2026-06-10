---
name: KUQ (Known-Unknown Questions)
source: https://huggingface.co/datasets/amayuelas/KUQ
paper: "2305.13712"
paper_title: "Knowledge of Knowledge: Exploring Known-Unknowns Uncertainty with Large Language Models"
license: MIT
files: [knowns_unknowns.jsonl, unknowns_all.jsonl]
size: "6,884 known/unknown-labeled questions + 6,363 unknowns with category labels"
role: eval (unanswerable-question detection)
fetched: 2026-06-10
fetched_from: "HF hub raw files via datasets/fetch_datasets.py (datasets builder rejects the source JSONL — inconsistent columns across rows; files copied verbatim instead)"
tags: [dataset, epistemic-humility, knowledge-boundary, abstention-eval]
---

## What it is

Questions labeled known vs unknown, with unknowns categorized
(future events, unsolved problems, controversial, ambiguous, etc.).
Like SelfAware, "unknown" here means unknown-to-anyone — a different
construct from model-specific unknowns.

## Role in our experiment

Held-out eval for abstention on epistemically unanswerable questions,
with the category labels enabling a breakdown of *which kinds* of
unanswerability the trained behavior transfers to.
