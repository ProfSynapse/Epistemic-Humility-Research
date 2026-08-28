---
id: task-56c61a
title: HF data-exhaust backfill
status: in-progress
assignee:
- '@claude'
tier: P
priority: low
experiment: ''
component: ''
depends_on: []
files:
- docs/public-artifacts.md
new_files: []
blocker: PI approval per dataset
created_date: '2026-08-27'
updated_date: '2026-08-27'
---
## Description
Terminal experiments without published exhaust (order tens of cells). Run
through the `data-exhaust` skill; every upload needs the dry-run card shown
plus explicit PI approval, and the revision recorded in the experiment's
NOTEBOOK plus `docs/public-artifacts.md`. Migrated from the TODO.md audited
backlog table (row EX, audited 2026-08-27).

## Acceptance Criteria
- [ ] Terminal experiments without published exhaust enumerated
- [ ] Dry-run card shown and PI approval obtained per dataset before upload
- [ ] Each published revision recorded in its experiment's NOTEBOOK.md and `docs/public-artifacts.md`

## Work Log
- 2026-08-27 @claude: seeded from TODO.md row EX during the task-backlog harness build.

## Enumeration (2026-08-27, registry cross-referenced against docs/public-artifacts.md)

Terminal experiments: 80. Aggregate exhaust already published: 8. UNPUBLISHED: 72 (63 with analysis-committed artifacts ready for aggregate-shape builds; 9 with zero committed artifacts, nothing to package without further decisions).

| files | status | slug |
|---|---|---|
| 83 | resolved | gemma4-e4b-kv-seam-quarantine |
| 44 | resolved | j-space-cross-family-layer-contrast |
| 24 | null-result | j-space-midband-write-sweep-qwen3-4b |
| 24 | null-result | margin-evidence-responsiveness-worldknown |
| 21 | resolved | caution-install-bounded-site-sweep |
| 21 | resolved | gemma4-e4b-pocket-ladder |
| 16 | resolved | qwen35-4b-midband-doubt-snap |
| 14 | resolved | placebo-seed-distribution-census |
| 13 | resolved | j-space-localization-qwen3-4b |
| 13 | falsified | rr3-corrected-placebo-replication |
| 12 | falsified | rr-cross-family-raw-refusal |
| 11 | resolved | doubt-gated-caution-tighten |
| 11 | falsified | gate-contribution-factorial |
| 11 | resolved | prompt-crossing-completion |
| 11 | resolved | prompt-vs-training-panel |
| 10 | null-result | family-atlas-surface-matched-json-completion-control |
| 9 | resolved | gemma-4-e4b-family-atlas |
| 9 | resolved | ood-breadth-beyond-selfaware |
| 8 | resolved | form-judge-axis-g-rescore |
| 8 | resolved | h9-propensity-reading-gate |
| 7 | resolved | bb-base-propensity-fit-read |
| 7 | null-result | evidence-response-direction-search |
| 7 | resolved | jspace-family-atlas |
| 7 | falsified | margin-mapping |
| 7 | falsified | write-direction-naming-battery |
| 6 | null-result | correctness-direction-rotation |
| 6 | null-result | family-atlas-surface-matched-vllm-control |
| 6 | falsified | j-space-token-targeted-refusal-qwen3-4b |
| 6 | resolved | pstruct-internalization-seed-robustness |
| 5 | resolved | abstention-wide-instrument-calibration |
| 5 | falsified | rr2-mistral-adjudicated-refusal-confirm |
| 4 | resolved | grpo-three-seed-confirmatory |
| 4 | null-result | margin-separation-fine-ladder |
| 3 | resolved | caution-ablation-rederivation |
| 3 | resolved | correctness-geometry-scale-ladder |
| 3 | null-result | dark-actuator-screen |
| 3 | null-result | family-atlas-surface-matched-pool-control |
| 3 | falsified | grpo-cold-start-induction |
| 3 | resolved | h6-genstream-hook-firing-check |
| 3 | resolved | j-space-layer-contrast-rep2-multisource |
| 3 | resolved | qwen3-4b-family-atlas |
| 3 | null-result | qwen35-4b-family-atlas |
| 2 | null-result | correctness-subspace-overlap |
| 2 | resolved | dial-logprob-baseline |
| 2 | resolved | dial-logprob-baseline-v2 |
| 2 | resolved | dial-logprob-baseline-v3 |
| 2 | resolved | idk-switch-naming-confirmatory |
| 2 | null-result | j-space-layer-contrast-replication-qwen3-4b |
| 2 | resolved | j-space-midband-dose-calibration-qwen3-4b |
| 2 | resolved | placebo-signflip-question-type-analysis |
| 2 | resolved | qwen35-4b-midband-heldout |
| 2 | falsified | wrong-answer-cell-power-fix |
| 1 | resolved | dial-logprob-t-deployed-confirmatory |
| 1 | null-result | family-atlas-surface-diversity-control |
| 1 | resolved | family-atlas-surface-residualization-control |
| 1 | resolved | flavor-atlas-rawbase |
| 1 | resolved | flavor-atlas-surface-control-confirmatory |
| 1 | resolved | fusion-nonredundance-redo |
| 1 | resolved | j-space-calibrated-layer-contrast-qwen3-4b |
| 1 | null-result | qualify-mode-separability-base-readout |
| 1 | resolved | rawbase-ambigqa-boundary-readout |
| 1 | resolved | snap-seed-sampled-decode-replication |
| 1 | resolved | ungated-vs-gated-dose-matched |
| 0 | null-result | ao-propensity-regulated-caution |
| 0 | resolved | ap-veto-length-balanced-confirmatory |
| 0 | falsified | base-refusal-direction-under-contract |
| 0 | falsified | fresh-sft-epistemic-mode-token-grpo |
| 0 | resolved | headline-seed1-postfix-rerun |
| 0 | resolved | prompt-crossing-heldout-confirmatory |
| 0 | resolved | readout-under-contract-crossing |
| 0 | resolved | stated-confidence-under-pstruct |
| 0 | falsified | susceptibility-as-probe |
- 2026-08-27 @claude: batch 1 uploaded (10 aggregate datasets, PI-approved in-conversation); revisions recorded in each NOTEBOOK and docs/public-artifacts.md. 53 buildable cells remain.
- 2026-08-27 @claude: batch 2 uploaded (10 aggregate datasets, PI-approved in-conversation); revisions recorded. 43 buildable cells remain.
- 2026-08-27 @claude: batch 3 uploaded (15 aggregate datasets, PI-approved in-conversation); revisions recorded. 28 buildable cells remain.
