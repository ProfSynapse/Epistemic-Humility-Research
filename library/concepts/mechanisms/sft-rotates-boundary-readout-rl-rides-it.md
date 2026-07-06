---
aliases:
- SFT Rotates the Answerability Readout Once, RL Rides It
- one-time SFT rotation of the boundary direction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:sft-rotates-boundary-readout-rl-rides-it
  type: mechanism
  status: canonical
cause: "Instruction supervised fine-tuning applied to a base model whose answerability (known-vs-unknown) readout is already present at full strength."
effect: "The linearly decodable answerability direction is rotated once into a near-orthogonal orientation (shared-basis cosine 0.06-0.25 across mid and late layers) with no gain in separability, and subsequent reinforcement learning rides that SFT-installed direction with negligible further rotation (cleansft to grpov2 cosine 0.91-0.997) and no AUROC change."
polarity: mediates
related:
- '[[internal--diag-item9-caution-assembly-timeline]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[answerability-probe-transfers-across-qa-datasets]]'
- '[[known-unknown-direction]]'
- '[[linear-probe]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[internal--diag-item9-caution-assembly-timeline]]'
  target_id: paper:internal-diag-item9
  confidence: high
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: high
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: high
- type: related_to
  target: '[[answerability-probe-transfers-across-qa-datasets]]'
  target_id: mechanism:answerability-probe-transfers-across-qa-datasets
  confidence: medium
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
---

Internal lab-notebook diagnostics (item 9) tracked the answerability readout across
four training stages (raw base, clean-SFT, GRPO-v2, GRPO-par-true) in a shared PCA-128
basis. The readout is present at full strength in the raw base (mid-to-late CV AUROC
mean 0.951) and no stage improves it (clean-SFT 0.922, GRPO-v2 0.923, GRPO-par-true
0.926). SFT rotates the direction once to a near-orthogonal orientation (raw to
clean-SFT cosine dropping to 0.06-0.25 from L8 onward) while both GRPO variants ride
that installed direction almost unchanged (0.91-0.997), with only a late-layer drift
into GRPO-par-true (0.736 at L35). This mechanizes the observed refit-per-checkpoint
drift and the low caution-direction cosine reported elsewhere in the program: the
rotation is a single SFT event, not gradual accumulation across training.
