---
aliases:
- Retain loss preserves benign representations during rerouting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:retain-loss-preserves-benign-representations-during-rerouting
  type: mechanism
  status: canonical
cause: "Representation Rerouting jointly minimizes a retain loss on benign and refusal examples while disrupting targeted harmful representations."
effect: "The adapted model preserves most benchmark capability and its existing refusal behavior."
polarity: prevents
related:
- '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
- '[[representation-rerouting]]'
- '[[circuit-breaker-set]]'
relationships:
- type: supported_by
  target: '[[2406.04313--improving-alignment-robustness-circuit-breakers]]'
  target_id: paper:2406.04313
  confidence: high
- type: related_to
  target: '[[representation-rerouting]]'
  target_id: method:representation-rerouting
  confidence: high
- type: related_to
  target: '[[circuit-breaker-set]]'
  target_id: dataset:circuit-breaker-set
  confidence: high
---

The paper reports less than a 1% decrease on its capability evaluations for RR, while a refusal-retain ablation degraded capabilities. This evidence supports preservation within the evaluated domains rather than universal utility retention.
