---
name: sycophancy-eval
source: https://github.com/meg-tong/sycophancy-eval
paper: "2310.13548"
paper_title: "Towards Understanding Sycophancy in Language Models"
license: "MIT per HF mirror; no LICENSE file in source repo — verify before redistribution"
files: [answer.jsonl, are_you_sure.jsonl, feedback.jsonl]
size: "~34 MB across 3 task files"
role: eval
fetched: 2026-06-09
tags: [dataset, epistemic-humility, sycophancy, eval]
---

## What it is

Sharma et al. (Anthropic) free-form sycophancy evaluation: answer sycophancy,
"are you sure?" capitulation, and feedback sycophancy tasks.

## Verification note (2026-06-10)

Re-checked upstream with a fresh shallow clone: the repo contains ONLY these
three eval prompt datasets plus `example.ipynb`/`utils.py` — **no released
model outputs** (the paper's per-model results were never published as data).
Still no LICENSE file upstream. The prompt records do carry graded metadata
enabling output-free analyses: `base.correct_answer`, `base.incorrect_answer`,
gold alias lists (TriviaQA/MS-MARCO-derived), and `metadata.prompt_template`
distinguishing neutral vs. "I think the answer is {correct}" vs. "I don't
think the answer is {correct}" vs. "I think the answer is {incorrect}"
framings of the same question. Row counts re-verified (wc -l):
answer.jsonl 7,268 (file lacks trailing newline, so wc -l undercounts by 1); are_you_sure.jsonl 4,887; feedback.jsonl 8,500.
Any sycophancy-output analysis therefore requires generating outputs
ourselves (the planned experiment's third eval axis), not reanalysis.

## Role in our experiment

Optional third eval axis: does abstention/humility training reduce capitulation
under "are you sure?" pressure (the inverted-humility failure mode)?
