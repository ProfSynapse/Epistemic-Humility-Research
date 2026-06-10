---
name: TriviaQA (rc.nocontext, validation)
source: https://huggingface.co/datasets/mandarjoshi/trivia_qa
paper: "1705.03551"
paper_title: "TriviaQA: A Large Scale Distant Supervision Challenge Dataset for Reading Comprehension"
license: "not tagged on HF (license:unknown); official release is free for research use — see http://nlp.cs.washington.edu/triviaqa/"
files: [validation.jsonl, cheng_test_gold.jsonl]
size: "17,944 questions (rc.nocontext validation) + 11,313 gold-alias rows for the Cheng et al. test set (unfiltered.nocontext validation); full corpus is GBs and deliberately not committed"
role: eval + truthful-rate recomputation
fetched: 2026-06-10
fetched_from: "HF hub via datasets/fetch_datasets.py (datasets 4.4.1)"
tags: [dataset, epistemic-humility, qa, gold-aliases]
---

## What it is

Trivia QA pairs with gold answers including `answer.aliases` and
`answer.normalized_aliases`. The rc.nocontext config drops evidence
documents — only question + answer fields, which is all we need.

## Role in our experiment

1. **Unlocked the exact truthful-rate recomputation** (done 2026-06-10) in
   `meta-analysis/analysis/reanalyze_idk_outputs.py`. Discovery: Cheng et
   al.'s (2401.13275) 11,313-question "test" set is exactly TriviaQA
   **unfiltered.nocontext/validation** (100% normalized-question match;
   their integer question_ids are a re-index). `cheng_test_gold.jsonl`
   carries the matched gold aliases; built by
   `scripts/fetch_datasets.py` (`build_cheng_gold`). Exact alias grading
   replaced the INTERIM token-F1 proxy.
2. In-domain train/eval source for the SFT-vs-KTO experiment's
   known/unknown splits (model-specific, via correctness probing).
