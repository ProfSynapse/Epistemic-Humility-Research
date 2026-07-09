---
aliases:
- The hallucination veto is already saturated at the first visible token
- veto does not crystallize across the answer window on trained checkpoints
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:veto-saturates-by-first-visible-token
  type: mechanism
  status: canonical
cause: "Reading the post-generation correctness/veto axis at token granularity across the answer window (first visible token through answer end, veto axis refit per position out-of-fold) on the deployed clean-SFT to GRPO-v2 checkpoint."
effect: "The veto is already near-saturated at the first visible token (AUROC 0.9424) and does not rise across the answer window, drifting slightly down to 0.9248 by answer-end (delta -0.0175 against a pre-registered +0.10 crystallization bar, AK-G1 MISS; random-direction guards clean at 0.486/0.529). On trained checkpoints the fabricate-anyway commitment is legible by the first emitted token rather than assembled across the fabrication; the descriptive raw base still rises (+0.0341 to a ~0.997 ceiling) but far below the bar."
polarity: enables
related:
- '[[internal-ak-commitment-point-stage1--grpo-v2]]'
- '[[post-generation-veto-is-rederived-not-carried]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[task-training-sharpens-not-creates-hallucination-veto]]'
- '[[known-unknown-direction]]'
relationships:
- type: supported_by
  target: '[[internal-ak-commitment-point-stage1--grpo-v2]]'
  target_id: paper:internal-ak-commitment-point-stage1
  confidence: high
- type: related_to
  target: '[[post-generation-veto-is-rederived-not-carried]]'
  target_id: mechanism:post-generation-veto-is-rederived-not-carried
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[task-training-sharpens-not-creates-hallucination-veto]]'
  target_id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  confidence: high
---

Amendment AK Stage 1 (branch amendment-ak-commitment-point, analysis commit
069427dd; committed record experiments/commitment-point/artifacts/stage1/ak_stage1_gate_verdicts.md) traced
the veto axis token-by-token across the answer window. On the gated grpo-v2 arm the
veto is already near its ceiling at the first visible token (AUROC 0.9424) and does
not crystallize as the fabrication is written, drifting to 0.9248 by answer-end
(delta -0.0175 vs the +0.10 gate, AK-G1 MISS). The commitment is legible up front
rather than assembled across the answer, which reframes the re-derived veto (see
[[post-generation-veto-is-rederived-not-carried]]) as re-derived by the first
emitted token, not gradually over the fabrication.
</content>
