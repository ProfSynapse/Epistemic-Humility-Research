---
aliases:
- ROME editing shifts mover head from copying to extracting
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rome-editing-shifts-mover-head-behavior
  type: mechanism
  status: canonical
cause: ROME inserts new factual association at a specific MLP layer
effect: Mover heads shift behavior from copying the original subject token to extracting the newly edited information; edited knowledge dominates multi-hop reasoning circuits
polarity: enables
related:
- '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
- '[[mover-head]]'
- '[[rank-one-model-editing]]'
- '[[knowledge-circuits]]'
relationships:
- type: supported_by
  target: '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
  target_id: paper:2405.17969
  confidence: high
- type: related_to
  target: '[[mover-head]]'
  target_id: term:mover-head
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
---

After [[rank-one-model-editing]] (ROME) inserts a new fact into an MLP layer, circuit-level analysis reveals that [[mover-head]] attention heads reorganize their information-routing behavior: rather than copying original subject-token content, they shift to extracting the newly stored attribute from the edited weight (arXiv:2405.17969). This behavioral shift propagates through multi-hop reasoning circuits, so downstream reasoning that depends on the edited fact also updates consistently. The finding demonstrates that targeted weight edits do not merely override output probabilities but reorganize the functional roles of circuit components.
