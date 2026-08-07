---
aliases:
- post-GRPO DPO recovers over-refusal
- G2 (grpo-three-seed-confirmatory)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:post-grpo-preference-stage-recovers-over-refusal-without-reopening-unknown
  type: mechanism
  status: canonical
cause: "a DPO preference-tuning stage applied after GRPO (clean_sft_grpo_dpo), evaluated against its own same-seed pre-DPO GRPO base"
effect: "over-refusal decreases by a small, direction-only margin (-0.77 pp and -1.84 pp across two fresh seeds, 18 and 43 rows respectively) while answer-on-unknown does not materially reopen (-0.39 pp, +0.29 pp, both within a pre-registered +2.0 pp cap), replicating a same-direction seed-1 effect"
polarity: enables
related:
- '[[grpo-three-seed-confirmatory]]'
- '[[grpo-centered-stacking]]'
- '[[grpo-abstention-shift-replicates-across-seeds]]'
relationships:
- type: supported_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/gates.yaml g2_post_grpo_preference_recovery_replicates (PASS both seeds, no magnitude floor by design)"
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md G2 ADJUDICATED PASS entry (seed 2 over_refusal -0.77 pp / answer_on_unknown -0.39 pp; seed 3 -1.84 pp / +0.29 pp)"
- type: related_to
  target: '[[grpo-centered-stacking]]'
  target_id: experiment:grpo-centered-stacking
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Effect 2 (the seed-1 recovery this mechanism replicates: over-refusal 66.62 to 63.63 pp, unknown answering steady at +0.10 pp)"
- type: related_to
  target: '[[grpo-abstention-shift-replicates-across-seeds]]'
  target_id: mechanism:grpo-abstention-shift-replicates-across-seeds
  confidence: medium
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Interpretation rules (a post-GRPO preference stage is useful only if it recovers known answers without materially reopening the unknown-answering gain GRPO itself produced)"
---

Registered as the second primary gate of `grpo-three-seed-confirmatory` (G2,
non-falsifier). The pass is real but thin: the red-team pass at resolve time
flagged that the comparison rests on one uncontrolled LoRA-merge round-trip
(the denominator is base plus GRPO adapter attached; the numerator is a
16-bit merge of that combination plus a further DPO adapter), and the DPO
numerator's LoRA initialization is frozen at the trainer baseline (3407)
across seeds rather than mirrored to the seed number, so seeds 2 and 3 are
partial rather than full replicates of the seed-1 finding. No magnitude
floor was set on the over-refusal decrease by design, because the seed-1
effect (-2.99 pp) was judged too small for a two-seed block to bound; report
with row counts, never percentages alone.
