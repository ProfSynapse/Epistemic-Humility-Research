---
aliases:
- Factual recall exposes privileged correctness knowledge
- Model-private factual correctness emerges with depth
- Factual self-probe advantage appears on disagreement subsets and grows with depth
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:factual-retrieval-carries-model-private-correctness-signal
  type: mechanism
  status: canonical
cause: "A target model processes factual-recall questions on which its correctness differs from a peer model's correctness."
effect: "From early-to-middle layers onward, the target's own representations predict its correctness better than the tested peer representations."
polarity: increases
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[privileged-correctness-knowledge]]'
- '[[premium-gap]]'
- '[[triviaqa]]'
- '[[hotpotqa]]'
relationships:
- type: supported_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: related_to
  target: '[[privileged-correctness-knowledge]]'
  target_id: term:privileged-correctness-knowledge
  confidence: high
- type: related_to
  target: '[[premium-gap]]'
  target_id: metric:premium-gap
  confidence: high
- type: related_to
  target: '[[triviaqa]]'
  target_id: dataset:triviaqa
  confidence: high
- type: related_to
  target: '[[hotpotqa]]'
  target_id: dataset:hotpotqa
  confidence: high
---

All nine main factual disagreement comparisons had significant positive premium gaps for both linear and MLP probes. The gap was near zero in early layers, became reliably positive around normalized depth 0.25 to 0.40, and generally strengthened toward later layers. The retrieval explanation remains interpretive because the study did not intervene on the signal.
