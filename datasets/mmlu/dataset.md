---
name: MMLU (all, test + validation)
source: https://huggingface.co/datasets/cais/mmlu
paper: "2009.03300"
paper_title: "Measuring Massive Multitask Language Understanding"
license: MIT
files: [test.jsonl, validation.jsonl]
size: "14,042 test + 1,531 validation MCQs across 57 subjects"
role: eval (OOD transfer)
fetched: 2026-06-10
fetched_from: "HF hub via datasets/fetch_datasets.py (datasets 4.4.1)"
tags: [dataset, epistemic-humility, mcq, ood-eval]
---

## What it is

57-subject multiple-choice knowledge benchmark (Hendrycks et al.).
Fields: question, subject, choices (4), answer (index).

## Role in our experiment

**OOD transfer eval** for abstention behavior trained on TriviaQA-style
free-form QA: does IDK training generalize to MCQ knowledge probes?
Cheng et al. used MMLU as one of their OOD sets, so this also supports
verifying their OOD numbers in `effects.csv`.
