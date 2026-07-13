---
aliases:
- base-model propensity direction certified at held-out AUROC 0.82 with zero training
- untrained Qwen3-4B carries a readable confab-propensity signal
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:base-confab-propensity-direction-reads-held-out-without-training
  type: mechanism
  status: canonical
cause: "Fitting the AL confabulation-propensity recipe (L24 PCA-128 randomized seed 20260705, standardize, L35-caution-residualize, mean-diff confab-vs-unanswerable-refused, z-scale) fresh on untrained base Qwen/Qwen3-4B's own generation grades over a 1,662-row fit surface, with zero fine-tuning, DPO, KTO, or RL applied to the base model."
effect: "The frozen base-fit direction separates held-out confabulations from honest unanswerable refusals on a disjoint 750-row draw at AUROC 0.8179 (95% bootstrap CI [0.7190, 0.9042], 1,000 resamples, read once), clearing both BB-P1-G1 pass lines (>=0.62 and CI lower bound >0.55) decisively. The caution positive control reads AUROC 0.9820 on the gradeable-only population (n=732), certifying the extraction, generation, and scoring pipeline. This is the program's first certified held-out propensity reading anywhere, obtained without any training step."
polarity: enables
related:
- '[[internal-bb-base-propensity-fit-read--qwen3-4b-base]]'
- '[[confabulation-propensity-direction]]'
- '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
- '[[internal-h9-reading-gate-inconclusive-by-power--true-checkpoint]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[internal-bb-base-propensity-fit-read--qwen3-4b-base]]'
  target_id: paper:internal-bb-base-propensity-fit-read
  confidence: high
- type: related_to
  target: '[[confabulation-propensity-direction]]'
  target_id: term:confabulation-propensity-direction
  confidence: high
- type: related_to
  target: '[[propensity-direction-reads-but-does-not-actuate-fabrication]]'
  target_id: mechanism:propensity-direction-reads-but-does-not-actuate-fabrication
  confidence: medium
- type: related_to
  target: '[[internal-h9-reading-gate-inconclusive-by-power--true-checkpoint]]'
  target_id: paper:internal-h9-reading-gate-inconclusive-by-power
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
---

Amendment BB (experiments/bb-base-propensity-fit-read/AMENDMENT.md, resolved
2026-07-11) fits AL's exact confab-propensity recipe fresh on untrained base
Qwen/Qwen3-4B rather than transferring the AI-TRUE-fit direction (which AL's own
provenance shows transfers across checkpoints at only cosine 0.17). The base-fit
direction reads held-out confabulation at AUROC 0.8179, clearing both pass lines
decisively, with the caution control confirming pipeline health at 0.9820. This
is the before-training bookend to Amendment H9, which asked the identical
held-out reading question on the AI-TRUE checkpoint and could not adjudicate it:
H9's evaluability gate never cleared (4 confabs vs a 20-row floor, on both the
original and the one registered enlargement), so the AI-TRUE direction's
held-out reading claim remains untested at power on that checkpoint. BB shows
the untrained substrate carries enough of both behavior classes (32 confabs, 558
honest unanswerable refusals over the same 750-row pool H9 drew from) to power
the read, and the direction fit on that substrate generalizes cleanly.
