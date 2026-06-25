---
aliases:
- Model forensics
tags:
- kg/term
- concept
- term
kg:
  id: term:model-forensics
  type: term
  status: canonical
area: terms
related:
- '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
- '[[cot-monitorability]]'
- '[[reasoning-transparency]]'
relationships:
- type: proposed_by
  target: '[[2606.26071--model-forensics-investigating-whether-concerning-behavior-reflects]]'
  target_id: paper:2606.26071
  confidence: high
- type: related_to
  target: '[[cot-monitorability]]'
  target_id: term:cot-monitorability
  confidence: medium
- type: related_to
  target: '[[reasoning-transparency]]'
  target_id: term:reasoning-transparency
  confidence: medium
---

The investigative practice of determining whether a model's concerning action was driven by malign intent, as opposed to a benign cause such as confusion, lack of judgment, overzealousness, or misinterpretation of ambiguous environment features. It goes beyond detecting concerning behavior to ask why the behavior occurred.

**Why it matters here:** it reframes safety evaluation around intent rather than surface behavior, the same humility-about-attribution that separates calibrated abstention from confident misjudgment in this vault's themes.

**Lineage:** named and scaffolded by this paper; related to [[cot-monitorability]] and [[reasoning-transparency]] (CoT as an evidence source) and to [[specification-gaming]] / [[reward-tampering]] (the behaviors it investigates).
