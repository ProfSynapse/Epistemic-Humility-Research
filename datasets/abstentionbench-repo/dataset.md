---
name: AbstentionBench (repo snapshot)
source: https://huggingface.co/datasets/facebook/AbstentionBench
paper: "2506.09038"
paper_title: "AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions"
license: CC-BY-NC-4.0
files: [AbstentionBench.py, data.py, subsampling-indices.json, UMWP_indices_answerable.json, kuq_new_categories.csv]
size: "repo snapshot only — benchmark composes 20 constituent datasets at load time (~35k prompts when materialized)"
role: eval (holistic abstention, OOD) — NOT YET MATERIALIZED
fetched: 2026-06-10
fetched_from: "huggingface_hub snapshot_download via datasets/fetch_datasets.py"
tags: [dataset, epistemic-humility, abstention-eval, ood-eval, needs-materialization]
---

## What it is

Holistic abstention benchmark: 20 datasets x 6 abstention scenarios
(underspecified context, stale data, ill-posed, etc.), with
human-validated judges. The HF repo contains **no data** — just a
legacy `datasets` loading script (rejected by datasets >= 3.x) that
downloads and subsamples the constituents (GPQA, KUQ, FalseQA, UMWP,
SQuAD2, ...) using `subsampling-indices.json`.

## Materialization plan (deferred)

To actually run it: use the official GitHub
(facebookresearch/abstentionbench) pipeline, or port `AbstentionBench.py`
+ `subsampling-indices.json` to a plain downloader for the scenario
subsets we need. Note some constituents (e.g. GPQA) are gated on HF.

## Role in our experiment

Headline OOD abstention eval for paper 2; also the source of the "24%
abstention" figure flagged for PDF verification in `effects.csv` (that
verification needs only the paper PDF — `library/pdfs/2506.09038.pdf` —
not the data).
