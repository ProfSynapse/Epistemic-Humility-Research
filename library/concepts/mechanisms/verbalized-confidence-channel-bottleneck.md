---
aliases:
- The verbalized confidence channel bottlenecks internal-to-stated coupling
- Stated confidence channel is the bottleneck, not knowledge
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:verbalized-confidence-channel-bottleneck
  type: mechanism
  status: canonical
cause: "Training a model to state confidence as a single scalar emitted by the language head under next-token cross-entropy (DPO, KTO, GRPO v1/v2/v3, contrastive-SFT), rather than via a dedicated head with a regression loss against the internal axis."
effect: "The stated confidence stays decoupled from the calibrated internal answerability axis across all seven interventions; two opposite training pressures - RL on the calibrated base (keeps stated calibration, cannot install knowledge-conditioned action) and distilling the internal axis into the emitted scalar (keeps action, collapses the scalar onto it) - each fail on the same channel, localizing the bottleneck to the emission channel itself."
polarity: prevents
related:
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[verbalized-confidence]]'
- '[[instruction-tuning-induces-calibration-collapse]]'
- '[[verbalized-confidence-imitation-overconfidence]]'
- '[[open-ended-generation-breaks-prompting-calibration]]'
- '[[faithful-calibration]]'
relationships:
- type: supported_by
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: high
- type: related_to
  target: '[[instruction-tuning-induces-calibration-collapse]]'
  target_id: mechanism:instruction-tuning-induces-calibration-collapse
  confidence: medium
- type: related_to
  target: '[[verbalized-confidence-imitation-overconfidence]]'
  target_id: mechanism:verbalized-confidence-imitation-overconfidence
  confidence: medium
- type: related_to
  target: '[[open-ended-generation-breaks-prompting-calibration]]'
  target_id: mechanism:open-ended-generation-breaks-prompting-calibration
  confidence: medium
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
---

Paper 3 ("Knows but Doesn't Say") shows the internal answerability axis is
calibrated (AUROC 0.997, readout ECE 0.004) while the model's stated confidence on
the same items ranks appropriateness at 0.52-0.56 and is near-constant, and that the
gap survives seven training interventions. Two opposite repairs (Amendments N and M)
each fail on the same channel - "says but doesn't act" and "acts but doesn't say" -
localizing the bottleneck to the single confidence scalar emitted by the LM head
under cross-entropy. This motivates an engine change: a dedicated confidence head
with a regression loss against the internal axis (the ceiling for which is shown by
Amendments O/Q in [[internal-twosignal-readout--training-free]]).
