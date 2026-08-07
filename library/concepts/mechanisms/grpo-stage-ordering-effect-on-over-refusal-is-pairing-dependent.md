---
aliases:
- GRPO-first vs GRPO-last ordering effect
- G5 (grpo-three-seed-confirmatory)
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:grpo-stage-ordering-effect-on-over-refusal-is-pairing-dependent
  type: mechanism
  status: canonical
cause: "training a GRPO stage before versus after a preference stage (DPO or KTO) in a three-stage response-confidence stacking lineage"
effect: "the over-refusal reduction from ordering GRPO first holds direction at all three seeds for the KTO pairing (-5.78, -3.13, -2.49 pp, attenuating) but SIGN-REVERSES across the two new seeds for the DPO pairing (-1.67, +0.17, +2.18 pp), so a general GRPO-first-beats-GRPO-last claim does not hold uniformly across preference-stage choice"
polarity: mediates
related:
- '[[grpo-three-seed-confirmatory]]'
- '[[grpo-centered-stacking]]'
relationships:
- type: supported_by
  target: '[[grpo-three-seed-confirmatory]]'
  target_id: experiment:grpo-three-seed-confirmatory
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/gates.yaml g5_stage_ordering_comparison (secondary, descriptive, non-gating)"
  - "experiments/grpo-three-seed-confirmatory/NOTEBOOK.md RED-TEAM PASS Finding 2 (G5 delivered; DPO pair mean +0.23 pp [min -1.67, max +2.18], KTO pair mean -3.80 pp [min -5.78, max -2.49], n=3 seed-level descriptive spread, not an inferential CI)"
- type: related_to
  target: '[[grpo-centered-stacking]]'
  target_id: experiment:grpo-centered-stacking
  confidence: high
  evidence:
  - "experiments/grpo-three-seed-confirmatory/AMENDMENT.md Effect 3 (the seed-1 observation this mechanism retests: both matched pairs pointed the same way at seed 1, DPO -1.67 pp, KTO -5.78 pp, registered as secondary/descriptive because the DPO margin was judged unadjudicable at two added seeds)"
---

This mechanism is explicitly non-gating and descriptive per the pre-registered
gate text: the seed-1 DPO-pair margin was judged too small for a two-seed
block to resolve, and G5 bars either pairing's delta from being reported as a
finding. Reported anyway because it corrects a specific prior claim: Amendment
F's Effect 3 prose ("both matched pairs point the same way") is **false at
three seeds for the DPO pair** and must not be recited in any write-up. The
KTO pairing is the more robust of the two, holding direction across all three
seeds while attenuating in magnitude; the DPO pairing crosses zero and its
sign is not interpretable as a stable ordering preference.
