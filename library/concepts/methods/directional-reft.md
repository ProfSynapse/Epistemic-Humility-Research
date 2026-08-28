---
aliases:
- DiReFT
- Directional ReFT
tags:
- kg/method
- concept
- method
kg:
  id: method:directional-reft
  type: method
  status: canonical
area: methods
related:
- '[[2404.03592--reft-representation-finetuning-language-models]]'
- '[[representation-finetuning]]'
- '[[low-rank-linear-subspace-reft]]'
- '[[low-rank-adaptation]]'
relationships:
- type: proposed_by
  target: '[[2404.03592--reft-representation-finetuning-language-models]]'
  target_id: paper:2404.03592
  confidence: high
- type: variation_of
  target: '[[representation-finetuning]]'
  target_id: method:representation-finetuning
  confidence: high
- type: related_to
  target: '[[low-rank-linear-subspace-reft]]'
  target_id: method:low-rank-linear-subspace-reft
  confidence: high
- type: related_to
  target: '[[low-rank-adaptation]]'
  target_id: method:low-rank-adaptation
  confidence: high
---

Directional ReFT is an ablation of LoReFT that removes the orthogonality
constraint and difference operation. It applies a pair of learned low-rank
projections directly to selected hidden representations.

**Why it matters here:** DiReFT tests whether a simpler and faster hidden-state
adapter retains the behavioral control of the fuller LoReFT formulation.

**Lineage:** DiReFT is a variation of [[representation-finetuning]] and
resembles [[low-rank-adaptation]] applied to selected hidden representations.
