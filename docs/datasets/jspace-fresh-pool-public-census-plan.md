# J-space Fresh-Pool Public Census Plan

Status: draft plan. This is not a dataset release.

## Purpose

The J-space layer-site replication mines a fresh behavioral pool from the AH
Stage-0 expansion universe. The same scan can become a reusable public index for
future epistemic-humility work: rows that a raw-base model answers despite
gold-unanswerability, and rows it answers correctly despite being answerable.

## Release Boundary

Safe first release:

- Row keys.
- Source dataset name and source-local identifier when available.
- Gold class (`unknown` / `known`).
- Behavioral role (`confab` / `known_correct_answered`).
- Source/category metadata.
- Text-free baseline behavior flags for generated candidates (`answered`,
  `refused`, `correct`, `degenerate`, natural-stop/token counts).
- Model, substrate, rendering, generation, grader, and script provenance.
- Aggregate counts and hashes for reproducibility.

Do not release without a separate license audit:

- Raw question text.
- Gold aliases.
- Model generations.
- Prompt-rendered strings.
- Row-level intervention outputs that include source text or generated text.

## Source Posture

Locally documented source status:

- KUQ: MIT in `datasets/kuq/dataset.md`.
- SelfAware: Apache-2.0 in `datasets/selfaware/dataset.md`.
- PopQA: public dataset and companion GitHub are visible, but local metadata
  does not establish raw-text redistribution terms for our derived release.
- TriviaQA: official release is public for research use, but local metadata does
  not establish raw-text redistribution terms for our derived release.

Default policy: publish a rebuildable manifest and loader first; publish raw
text only source-by-source after checking the upstream license and preserving
required notices.

## Build Path

1. Run the fresh-pool miner with `--scan-all-candidates`.
2. Keep private rows under the experiment's gitignored `analysis/` directory.
3. Rebuild the public-safe manifest with `--manifest-only` after the scan if the
   manifest schema changed.
4. Commit only `analysis-committed/fresh_eval_pool_manifest.json` or a sibling
   public manifest containing no text, aliases, or generation text.
5. Add a datasheet before any external HF release.
6. Require explicit release approval before uploading a public dataset.

## Current Consumer

The immediate consumer is
`experiments/j-space-layer-contrast-replication-qwen3-4b/`. Its signed evidence
gate remains a minimum fresh-pool floor, not a publication claim.
