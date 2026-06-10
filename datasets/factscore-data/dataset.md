---
name: factscore-data
source: https://github.com/shmsw25/FActScore (data hosted on Google Drive folder 1kFey69z8hGXScln01mVxrOhrqgM62X7I, fetched via gdown per repo README)
paper: "2305.14251"
paper_title: "FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation"
license: "MIT License (repo LICENSE file; Drive data released through the repo README under the same project)"
files: [labeled/{InstructGPT,ChatGPT,PerplexityAI}.jsonl + prompt_entities.txt, unlabeled/{12 models}.jsonl + prompt_entities.txt, unlabeled-predictions/{12 models}.jsonl, prompt_entities.txt]
size: "~19 MB"
role: meta-analysis-reanalysis (factual precision vs. abstention/response-rate trade-off)
fetched: 2026-06-10
tags: [dataset, epistemic-humility, factuality, hallucination, abstention, reanalysis]
---

## What it is

Released data from Min et al. (EMNLP 2023), the FActScore paper. Biography
generations ("Tell me a bio of {entity}") with atomic-fact decomposition and
factuality labels. Three components:

1. **`labeled/`** — Section 3 human-annotation data: 183 generations each from
   InstructGPT, ChatGPT, PerplexityAI (549 rows; 16,040 human-labeled atomic
   facts total: 4,726 / 5,426 / 5,888 respectively). Each record:
   `input` (prompt), `output` (full generation), `topic` (Wikipedia entity),
   `cat` (entity rarity tier + region, e.g. `["very rare", "North America"]`),
   `annotations[]` per sentence with `is-relevant`, `model-atomic-facts[]`,
   and `human-atomic-facts[]` each carrying `label` ∈ {S, NS, IR}
   (Supported / Not Supported / Irrelevant).
2. **`unlabeled/`** — raw generations for 12 LMs x 500 prompts (6,000 rows;
   GPT-4, ChatGPT, InstructGPT, Alpaca-7B/13B/65B, Vicuna-7B/13B, MPT-Chat-7B,
   Dolly-12B, Pythia-12B, Stablelm-alpha-7B). Record: `input`, `output`,
   `topic`, `cat`. Includes abstaining responses.
3. **`unlabeled-predictions/`** — Section 4.3 automated scoring of the same 12
   LMs: per-response `facts[]` (atomic facts), `ChatGPT_Labels[]` and/or
   `LLAMA+NP_Labels[]` (S/NS per fact), `prompt`. Abstentions are EXCLUDED
   from these files, so row counts vary (333–500; total 5,476); response
   ratio = rows/500 (e.g. ChatGPT 421/500 = 84.2%, GPT-4 441/500 = 88.2%,
   all Alpacas 500/500 = 100% responding).

`prompt_entities.txt` (top level, 500 entities) is the unlabeled prompt list;
`labeled/prompt_entities.txt` (183) is the human-annotation subset.

## What was skipped

From the same Drive folder: `enwiki-20230401.db` (18 GB Wikipedia knowledge
source — refetch with `python -m factscore.download_data` if rerunning the
scorer), `demos.zip` (few-shot demos for the atomic-fact generator), and
`original_generation.zip` (2.3 MB earlier-version generation dumps,
superseded by `unlabeled/`). Refetch any of these with
`python3 -m gdown <file-id>`; IDs are in `factscore/download_data.py` or by
listing Drive folder `1kFey69z8hGXScln01mVxrOhrqgM62X7I`.

## Why it matters for the meta-analysis

Per-response factuality labels JOINED with per-model response/abstention
behavior across an RLHF ladder (InstructGPT vs. ChatGPT vs. GPT-4) and
SFT-only models (Alpaca/Vicuna/Dolly — all ~100% responding) — the
respond-rate vs. precision operating-point data that C3 (over-refusal
trade-offs) and C1/C4 need, with entity-rarity tiers (`cat`) as a
knowledge-frontier proxy.
