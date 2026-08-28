---
aliases:
- Consensus masks model-private correctness information
- Shared success patterns inflate peer correctness probes
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:inter-model-agreement-masks-privileged-correctness-signal
  type: mechanism
  status: canonical
cause: "Target and peer models answer most of the same questions correctly or incorrectly, so their correctness labels are strongly correlated."
effect: "A peer probe can predict target correctness from shared difficulty and its own success signal, reducing the full-set premium gap even if target-private information exists."
polarity: decreases
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[self-vs-peer-correctness-probing]]'
- '[[premium-gap]]'
relationships:
- type: supported_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: related_to
  target: '[[self-vs-peer-correctness-probing]]'
  target_id: method:self-vs-peer-correctness-probing
  confidence: high
- type: related_to
  target: '[[premium-gap]]'
  target_id: metric:premium-gap
  confidence: high
---

The tested model pairs agreed on correctness for roughly 72 to 83 percent of questions. Full-set self and peer probes were often comparable, but factual self advantage appeared consistently after evaluation was restricted to disagreements without retraining the probes.
