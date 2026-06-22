---
aliases:
- Mover head failure drives factual hallucination
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:mover-head-failure-drives-hallucination
  type: mechanism
  status: canonical
cause: Mover head selects incorrect information from subject position in early-to-middle layers
effect: Model produces a factually incorrect object token (hallucination) at output
polarity: enables
related:
- '[[2405.17969--knowledge-circuits-pretrained-transformers]]'
- '[[mover-head]]'
- '[[hallucination]]'
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
  target: '[[hallucination]]'
  target_id: term:hallucination
- type: related_to
  target: '[[knowledge-circuits]]'
  target_id: term:knowledge-circuits
---

Within the knowledge circuit framework, [[mover-head]] attention heads are responsible for copying factual attribute information from the enriched subject representation to the prediction position (arXiv:2405.17969). When a mover head attends to an incorrect position or retrieves a wrong attribute, the downstream prediction reflects that error as a hallucination at the output token. Circuit-level activation patching confirms the causal role: replacing mover head outputs with corrupted values reliably degrades factual accuracy, while restoring them rescues correct predictions.
