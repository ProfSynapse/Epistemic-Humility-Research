---
aliases:
- Qwen J-lens replication supports cross-model cognitive space
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen-j-lens-replication-supports-cross-model-cognitive-space
  type: mechanism
  status: canonical
cause: "Nanda, Blank, and Bhatia implemented J-lens on Qwen 3.6 27B using 25 Pile prompts and penultimate-layer Jacobians"
effect: "they report partial replication of verbal-report swaps, CKA workspace bands, directed modulation, multilingual and typo evaluations, plus failed or weak replications for harder multihop, poetry, and arithmetic cases, supporting the broad cognitive-space claim while warning that model ability and dataset design matter"
polarity: supports
related:
- '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
- '[[jacobian-lens]]'
- '[[cognitive-space]]'
- '[[qwen3]]'
relationships:
- type: supported_by
  target: '[[tc-2026-workspace-commentary-nanda--cognitive-space-j-lens-replication]]'
  target_id: paper:tc-2026-workspace-commentary-nanda
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[cognitive-space]]'
  target_id: term:cognitive-space
  confidence: high
- type: related_to
  target: '[[qwen3]]'
  target_id: model:qwen3
  confidence: medium
---

Nanda's commentary reports an independent, fast replication on Qwen 3.6 27B. The replication recovered some core phenomena, including verbal-report effects, workspace-like CKA bands, directed modulation, multilingual probing/causal effects, and typo results, but found weaker or failed replication on multihop, poetry, and arithmetic. The pattern supports J-lens as a cross-model tool while emphasizing that eval difficulty must match the model.
