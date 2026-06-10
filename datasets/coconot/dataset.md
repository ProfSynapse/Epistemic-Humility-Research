---
name: CoCoNot (Contextual Noncompliance)
source: https://huggingface.co/datasets/allenai/coconot
paper: "2407.12043"
paper_title: "The Art of Saying No: Contextual Noncompliance in Language Models"
license: "not tagged on HF; see repo README (AI2 release)"
files: [original_test.jsonl, original_train.jsonl, contrast_test.jsonl]
size: "1,001 original test + 11,477 original train + 379 contrast test"
role: eval (noncompliance + over-refusal)
fetched: 2026-06-10
fetched_from: "HF hub via datasets/fetch_datasets.py (datasets 4.4.1)"
tags: [dataset, epistemic-humility, noncompliance, over-refusal]
---

## What it is

Taxonomy-driven noncompliance benchmark (incomplete, unsupported,
indeterminate, humanizing, unsafe requests...). The **contrast** set
contains superficially similar requests that SHOULD be complied with —
the over-refusal probe. `pref` split (preference pairs) not downloaded;
add to fetch_datasets.py if the KTO arm wants it.

## Role in our experiment

Eval for the over-refusal axis: IDK training must not inflate refusals
on compliant-looking requests. Contrast set is the headline metric here;
original test gives the noncompliance-recall side. Train split kept
because its (prompt, noncompliant-response) pairs are a candidate
KTO-negative source.
