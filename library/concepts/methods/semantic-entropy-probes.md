---
aliases:
- SEP
- semantic entropy probes
- SEPs
tags:
- kg/method
- concept
- method
kg:
  id: method:semantic-entropy-probes
  type: method
  status: canonical
area: methods
related:
- '[[2406.15927--semantic-entropy-probes]]'
- '[[linear-probe]]'
- '[[semantic-entropy]]'
- '[[consistency-based-confidence]]'
- '[[p-true]]'
- '[[hallucination]]'
- '[[auroc]]'
relationships:
- type: proposed_by
  target: '[[2406.15927--semantic-entropy-probes]]'
  target_id: paper:2406.15927
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[semantic-entropy]]'
  target_id: method:semantic-entropy
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[p-true]]'
  target_id: method:p-true
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

Linear logistic regression classifiers trained on the hidden states of a single LLM generation to predict binarized semantic entropy. At training time, SE labels are computed from N=10 high-temperature samples; at test time, only a single forward pass is required. Two probing positions are studied: the second-last-token (SLT) of the generated response and the token-before-generating (TBG), the last input token before any generation.

**Why it matters here:** SEPs reduce the computational overhead of semantic uncertainty quantification from 5-10x to near-zero at deployment, while outperforming accuracy probes on out-of-distribution task generalization. They bridge sampling-based SE and hidden-state probing, providing a cheap uncertainty signal that can attach to any model generation pipeline.

**Lineage:** Proposed in Kossen et al. 2406.15927; builds on semantic entropy (Farquhar et al. 2024) as the supervisory signal and on linear probe methodology for reading LLM hidden states.
