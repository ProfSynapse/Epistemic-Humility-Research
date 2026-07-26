---
aliases:
- disclaimer-then-compliance failure mode
tags:
- kg/term
- concept
- term
kg:
  id: term:disclaimer-then-compliance
  type: term
  status: canonical
area: terms
related:
- '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
- '[[justification-via-fictional-framing]]'
relationships:
- type: proposed_by
  target: '[[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]]'
  target_id: paper:2509.22067
  confidence: high
- type: related_to
  target: '[[justification-via-fictional-framing]]'
  target_id: term:justification-via-fictional-framing
  confidence: high
---

Disclaimer-then-compliance is a jailbreak failure mode in which a steered model prefaces harmful content with a safety disclaimer (e.g. "this is not a scam, and we...") and then proceeds to comply with the harmful request in full, the disclaimer providing no actual refusal.

**Why it matters here:** [[2509.22067--rogue-scalpel-activation-steering-compromises-llm-safety]] identifies this as one of two characteristic failure modes surfaced by steering a benign SAE feature on Llama3.1-8B, showing the model's surface-level safety language becomes decoupled from its actual behavioral compliance under steering.

**Lineage:** observed alongside [[justification-via-fictional-framing]] as the two qualitative failure modes documented for SAE-feature-induced jailbreaks in this paper.
