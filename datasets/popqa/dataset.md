---
name: PopQA (test)
source: https://huggingface.co/datasets/akariasai/PopQA
paper: "2212.10511"
paper_title: "When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories"
license: "not tagged on HF; companion GitHub (AlexTMallen/adaptive-retrieval) is MIT"
files: [test.jsonl]
size: "14,267 entity-centric questions with Wikipedia popularity scores"
role: eval (long-tail knowledge boundary)
fetched: 2026-06-10
fetched_from: "HF hub via datasets/fetch_datasets.py (datasets 4.4.1)"
tags: [dataset, epistemic-humility, long-tail, knowledge-boundary]
---

## What it is

Entity-centric open-domain QA built from Wikidata triples, each question
annotated with subject-entity monthly Wikipedia page views (`s_pop`,
`o_pop`). Popularity stratifies questions by how likely a model is to
know the answer — a natural axis for knowledge-boundary analysis.

## Role in our experiment

OOD eval with a built-in difficulty gradient: abstention rate should
track (inverse) popularity if the trained model abstains on genuinely
unknown facts rather than on surface features. `possible_answers` gives
gold aliases for exact-match grading.
