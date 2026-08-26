---
title: prompt-crossing-heldout-confirmatory
aliases:
- 'Prompt-crossing held-out confirmatory: promoting the paper-2 prompt-condition claims on out-of-distribution surfaces'
- held-out confirmatory promotion of C1/C2/C3
- AmbigQA confirmatory prompt-crossing
tags:
- kg/experiment
- experiment
- abstention
kg:
  id: experiment:prompt-crossing-heldout-confirmatory
  type: experiment
  status: canonical
related:
- '[[prompt-vs-training-panel]]'
- '[[prompt-crossing-completion]]'
- '[[ood-breadth-beyond-selfaware]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[only-sft-installs-abstention-in-weights]]'
- '[[preference-stage-after-sft-partially-erodes-internalized-abstention]]'
- '[[context-invariance]]'
- '[[stated-confidence-under-pstruct]]'
relationships:
- type: built_on_by
  target: '[[stated-confidence-under-pstruct]]'
  target_id: experiment:stated-confidence-under-pstruct
  confidence: high
  evidence:
  - "experiments/stated-confidence-under-pstruct/AMENDMENT.md Motivation and
    posture (CPU-only re-analysis of this cell's existing 18 P-struct-bearing
    arms x 1,832 AmbigQA rows, scoring the stated_confidence field this cell
    captured but did not analyze; no new generation)"
- type: builds_on
  target: '[[prompt-vs-training-panel]]'
  target_id: experiment:prompt-vs-training-panel
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/AMENDMENT.md Motivation and posture (the panel and its fresh-seed replication ran on the same SelfAware rows and the same Qwen3-4B checkpoints; this cell is the registered confirmatory promotion route, same model, held-out data)"
- type: builds_on
  target: '[[prompt-crossing-completion]]'
  target_id: experiment:prompt-crossing-completion
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/AMENDMENT.md Motivation and posture (cites the panel's registered fresh-seed replication, resolved 2026-08-16, falsifier not fired, as the second SelfAware-tier predecessor the three claims come from)"
- type: builds_on
  target: '[[ood-breadth-beyond-selfaware]]'
  target_id: experiment:ood-breadth-beyond-selfaware
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/AMENDMENT.md Motivation and posture (reuses the screened out-of-distribution surfaces, AmbigQA/KUQ/BIG-bench known-unknowns, built and adjudicated by ood-breadth-beyond-selfaware, including its KUQ leakage screen)"
- type: supports
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/experiment.yaml (verdict: C1 confirmed and promoted at exploratory-companion strength, instruction gap 70.26pp on held-out AmbigQA, base P-rc 70.26 vs P-plain 0.00, inside the registered 50-90pp band; F1 <15pp not fired)"
- type: supports
  target: '[[only-sft-installs-abstention-in-weights]]'
  target_id: mechanism:only-sft-installs-abstention-in-weights
  confidence: high
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/experiment.yaml (verdict: C2 confirmed and promoted, cold SFT seeds 56.39/63.47/61.58 inside the registered 40-80 band, base P-struct 0.00, all six cold DPO/KTO seeds at or below 0.10; F2 not fired)"
- type: supports
  target: '[[preference-stage-after-sft-partially-erodes-internalized-abstention]]'
  target_id: mechanism:preference-stage-after-sft-partially-erodes-internalized-abstention
  confidence: medium
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/experiment.yaml (verdict: C3 partial, no promotion, F3 not fired; seq SFT-KTO retains 90.1/83.8/78.6 percent of same-seed cold-SFT parent recall, inside the 40-100 promotion band; seq SFT-DPO retains 28.9/32.6/28.4 percent, below the 40 percent promotion band and above the 25 percent erasure floor, confirming the DPO-erodes-more-than-KTO asymmetry on a held-out surface without clearing promotion)"
- type: related_to
  target: '[[context-invariance]]'
  target_id: term:context-invariance
  confidence: medium
  evidence:
  - "experiments/prompt-crossing-heldout-confirmatory/AMENDMENT.md (the three claims under promotion are paper 2 Section 4.2's prompt-condition findings; this cell is their registered held-out confirmatory test)"
---

Tier-2 confirmatory eval-only cell, resolved 2026-08-17/18 (signed 2026-08-17;
verdict recorded in `experiment.yaml` as of merge e85bef8d). Promotes three
paper 2 Section 4.2 prompt-condition claims from exploratory to
"exploratory-companion" tier on a held-out surface: same Qwen3-4B checkpoints
as the panel and `prompt-crossing-completion`, but AmbigQA validation
(primary gate, 1,832 rows) plus KUQ and BIG-bench known-unknowns
(secondary, descriptive) instead of SelfAware. Twenty primary arms crossing
base/cold-SFT/cold-DPO/cold-KTO/clean-SFT/SFT-GRPO/sequential preference
checkpoints against P-rc, P-plain, and P-struct prompt contracts.

C1 (instruction gap at base) and C2 (SFT internalization signature under
P-struct) both confirmed and promoted at exploratory-companion strength: C1's
gap is 70.26 percentage points on held-out AmbigQA (base P-rc 70.26 vs
P-plain 0.00), inside the registered 50-90pp band. C2's cold SFT seeds read
56.39/63.47/61.58, inside the 40-80 band, with base P-struct at 0.00 and all
six cold DPO/KTO seeds at or below 0.10. C3 (erosion, not erasure, after a
preference stage) stays partial with no promotion, though its falsifier does
not fire: seq SFT-KTO retains 90.1/83.8/78.6 percent of its same-seed
cold-SFT parent's recall, inside the 40-100 promotion band, while seq
SFT-DPO retains only 28.9/32.6/28.4 percent, below the 40 percent promotion
band but above the 25 percent erasure floor. The held-out surface reproduces
the same DPO-erodes-more-than-KTO asymmetry the SelfAware-tier
`prompt-crossing-completion` cell found, without clearing the promotion
threshold on this surface. PH-G0 passed on all 20 primary arms: full 1,832-row
coverage, config shas matching pinned bytes, lead recompute matching exactly.
Secondary descriptive readings show internalization generalizing to KUQ
(88.34) and BIG-bench (100.0), both with base at 0.00.

**Why it matters here:** this is the program's first confirmatory-route
promotion of paper 2's prompt-condition claims off the single dataset
(SelfAware) and single-replication tier they were resolved on. C1 and C2 now
carry the confirmatory companion designation reported alongside, and never
pooled with, the Section 4.2 exploratory table or the locked headline matrix.
C3's partial outcome keeps the erosion asymmetry between DPO and KTO
exploratory-tier but confirms it is not a SelfAware-specific artifact.

**Lineage:** builds on [[prompt-vs-training-panel]] (SelfAware exploratory
predecessor establishing C1 and C2) and [[prompt-crossing-completion]]
(SelfAware fresh-seed replication establishing C3's parent-relative form);
reuses the screened out-of-distribution surfaces from
[[ood-breadth-beyond-selfaware]]. Source of truth:
`experiments/prompt-crossing-heldout-confirmatory/AMENDMENT.md` and
`experiments/prompt-crossing-heldout-confirmatory/experiment.yaml` (verdict
field, as of merge e85bef8d).
