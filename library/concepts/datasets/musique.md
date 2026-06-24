---
aliases:
- MuSiQue
- Multistep Question Answering
tags:
- kg/dataset
- concept
- dataset
kg:
  id: dataset:musique
  type: dataset
  status: canonical
area: datasets
related:
- '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
- '[[truthrl]]'
- '[[crag]]'
- '[[hallucination]]'
- '[[knowledge-boundary]]'
relationships:
- type: proposed_by
  target: '[[2509.25760--truthrl-incentivizing-truthful-llms]]'
  target_id: paper:2509.25760
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: medium
- type: related_to
  target: '[[crag]]'
  target_id: dataset:crag
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
---

A multi-hop question-answering dataset with compositional reasoning requirements; used in TruthRL experiments as a held-out generalization benchmark alongside HotpotQA and NQ.

**Why it matters here:** The hardest generalization benchmark in TruthRL; MuSiQue consistently shows negative truthfulness scores for most baselines, making it a stress-test for multi-step uncertainty recognition.

**Lineage:** Trivedi et al. 2022; used as a held-out evaluation in TruthRL (Table 1).
