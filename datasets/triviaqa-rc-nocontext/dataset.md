---
name: TriviaQA (rc.nocontext, validation)
source: https://huggingface.co/datasets/mandarjoshi/trivia_qa
paper: "1705.03551"
paper_title: "TriviaQA: A Large Scale Distant Supervision Challenge Dataset for Reading Comprehension"
license: "not tagged on HF (license:unknown); official release is free for research use — see http://nlp.cs.washington.edu/triviaqa/"
files: [validation.jsonl, cheng_test_gold.jsonl, train.jsonl]
size: "17,944 questions (rc.nocontext validation) + 11,313 gold-alias rows for the Cheng et al. test set (unfiltered.nocontext validation) + rc.nocontext train split (Phase 1 probe/train pool, fetched on sign-off); full corpus is GBs and deliberately not committed"
role: eval + truthful-rate recomputation + Phase 1 probe/train pool
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

## train.jsonl (Phase 1 probe/train pool, WS-0)

`train.jsonl` is the **rc.nocontext train split**, the probe/train pool for
the Phase 1 abstention experiment (paper 2). It is the pool the Component A
knowledge probe samples (`experiment/phase1/probe/probe.py`) and the WS-2
builder turns into SFT/DPO/KTO training files.

Why the train split and not the on-disk `validation.jsonl`: the validation
pool is the exact source of Cheng's 11,313-question test set, so probing or
training on it would leak the held-out test set into training. We keep Cheng's
set as the disjoint bridge-comparable test set and probe/train on the train
split instead. The WS-2 builder enforces normalized-question disjointness with
a hard leakage-guard assertion
(`normalized(probe_questions) intersect normalized(cheng_test_questions)` must
be empty), using the same normalization as the eval scorer
(`re.sub(r"\s+", " ", s.strip().lower())`).

Schema: identical to `validation.jsonl` (`question`, `question_id`,
`answer.normalized_aliases`, ...). Train rows are self-describing, so the probe
reads gold aliases directly from this file; no separate gold build is needed
(unlike the Cheng re-index case that produced `cheng_test_gold.jsonl`).

Fetch (PENDING user sign-off, not yet executed): the spec row is registered in
`scripts/fetch_datasets.py:SPECS`; run with one idempotent, split-restricted
command once the protocol is signed off:

```
python datasets/scripts/fetch_datasets.py --only triviaqa-rc-nocontext
```

After the real fetch lands, replace this PENDING note with the actual row
count and fetch date to complete the provenance record.
