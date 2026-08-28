---
aliases:
- Probe-based DPO preserves probe-detectable toxicity features
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:probe-based-dpo-preserves-detectable-toxicity-representations
  type: mechanism
  status: canonical
cause: "[[probe-based-direct-preference-optimization]] constructs chosen and rejected responses from differences in frozen probe scores."
effect: "Preference training retains toxicity representations that remain detectable by training, held-out, and retrained probes."
polarity: enables
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[probe-based-direct-preference-optimization]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: related_to
  target: '[[probe-based-direct-preference-optimization]]'
  target_id: method:probe-based-direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Single-probe DPO retained held-out and retrained probe AUCs of 0.938 and
0.926. Ten-probe DPO retained 0.994 and 0.992, while classifier-scored DPO
reached 0.866 and 0.770. The paper presents the causal explanation as a
hypothesis rather than a demonstrated mechanism.
