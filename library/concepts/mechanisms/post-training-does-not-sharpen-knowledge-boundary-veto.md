---
title: post-training-does-not-sharpen-knowledge-boundary-veto
aliases:
- Amendment Y H_B3 not supported
- vendor post-training does not sharpen, and can dull, the hallucination veto
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:post-training-does-not-sharpen-knowledge-boundary-veto
  type: mechanism
  status: canonical
cause: "Comparing the hallucination-veto AUROC on four pretrain-only base models against their vendor-post-trained instruct siblings (Qwen3.5-4B, gemma-4-E4B, Llama-3.2-3B, Olmo-3-7B), with the clean within-run comparison being the Olmo-3 pair (same seed and scorer, base k-shot render vs instruct chat-template render); the other three pairs are cross-run and additionally confounded by render surface."
effect: "Instruct-minus-base veto delta is <= 0 on every one of the four pairs. The clean Olmo-3 pair moves veto 0.803 -> 0.731 and within-SelfAware control 0.791 -> 0.674. The Z-anchored instruct siblings (greedy) sit at or below their Amendment Y bases too (Qwen3.5 0.666 vs 0.666; Gemma 0.871 vs 0.874; Llama-3.2 0.633 vs 0.835, though this pair is render-confounded). H_B3 (post-training sharpens the veto, predicted, report-only) is NOT SUPPORTED: vendor post-training does not sharpen the internal hallucination veto, and can dull it, consistent with Amendment X's prior finding of non-monotonicity across training."
polarity: decreases
related:
- '[[pretrain-only-base-readout]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[rawbase-ambigqa-boundary-readout]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[pretrain-only-base-readout]]'
  target_id: experiment:pretrain-only-base-readout
  confidence: high
  evidence:
  - "AMENDMENT.md sec 9 (H_B3 not-supported adjudication and per-pair veto
    deltas)"
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: medium
  evidence:
  - "AMENDMENT.md sec 9 (that mechanism found OUR abstention-SFT plus GRPO
    sharpens the veto +0.226 AUROC on top of an ALREADY vendor-post-trained
    instruct base; this mechanism finds vendor post-training itself, the
    stage before that, does not sharpen and can dull the same veto - an
    apparent direction contrast that reflects two different training
    interventions at two different pipeline stages, not a contradiction of
    either result)"
- type: related_to
  target: '[[rawbase-ambigqa-boundary-readout]]'
  target_id: experiment:rawbase-ambigqa-boundary-readout
  confidence: high
  evidence:
  - "experiments/rawbase-ambigqa-boundary-readout/AMENDMENT.md sec 3
    Prediction (cites this finding directly as grounds: 'Amendment Y's H_B3
    found post-training does not sharpen the SelfAware readout, so training
    has not been shown to create or destroy this signal in either direction
    on any surface')"
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
  evidence:
  - "AMENDMENT.md sec 6 (veto AUROC as defined by X/Z/SR on this direction)"
---

Amendment Y's report-only H_B3 hypothesis predicted post-training would
sharpen the hallucination veto (an expected, not gated, direction). It did
not: the instruct-minus-base veto delta is non-positive on every one of the
four Arm A pairs, most cleanly on the within-run Olmo-3 pair where seed and
scorer are held fixed and only vendor post-training differs (0.803 -> 0.731).

**Why it matters here:** this is a direct dependency for a later cell.
`rawbase-ambigqa-boundary-readout`'s pre-registered prediction cites this
result by name as one of its two grounds for expecting a flavor-specific
(not training-warp) reading on AmbigQA: if post-training has not been shown
to create or destroy the knowledge-boundary signal in either direction on
any surface tested so far, there is no prior reason to expect it created the
AmbigQA-specific gap either.

**Lineage:** related to, and at an earlier training stage than,
[[task-training-sharpens-not-creates-hallucination-veto]] (Amendment W vs
U), which found OUR downstream task training sharpens the same veto by
+0.226 AUROC on top of an already-instruct base. Read together, the
program's two training interventions have opposite measured effects on
veto sharpness at their respective stages: vendor post-training (base ->
instruct) does not sharpen and can dull it, while the program's own
abstention-SFT + GRPO (instruct -> our checkpoint) does sharpen it. Known
confound: the Qwen3.5/Gemma/Llama-3.2 pairs are cross-run and differ in
prompt render (base k-shot vs instruct chat template) in addition to
training, so the Olmo-3 pair is the amendment's cleanest supported
statement. Source of truth:
`experiments/pretrain-only-base-readout/AMENDMENT.md` sec 9.
