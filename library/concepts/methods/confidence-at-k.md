---
aliases:
- Confidence@k
- confidence at k
- top-k confidence selection
tags:
- kg/method
- concept
- method
kg:
  id: method:confidence-at-k
  type: method
  status: canonical
area: methods
related:
- '[[2601.23096--catto-per-token-calibration]]'
- '[[catto]]'
- '[[self-consistency]]'
- '[[direct-preference-optimization]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2601.23096--catto-per-token-calibration]]'
  target_id: paper:2601.23096
  confidence: high
- type: related_to
  target: '[[catto]]'
  target_id: method:catto
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

An inference-time selection rule that generates k candidate outputs per input and selects the one with the highest token-level calibrated confidence, where confidence is computed from the model's predicted probabilities over label tokens. The selection is proved Bayes-optimal under well-calibrated confidence. No additional training is required.

**Why it matters here:** Converts well-calibrated token probabilities into measurable accuracy gains at inference time. Reverses DPO-induced accuracy degradation on hard benchmarks when applied on top of CATTO. Directly usable as a read-out procedure for locked training-regimen checkpoints without any additional training or annotation.

**Lineage:** Proposed in arXiv:2601.23096 Section 3.3; Bayes-optimality proved in Appendix A.3. Related to self-consistency (which aggregates by voting) but uses calibrated token probability rather than answer agreement as the selection criterion.
