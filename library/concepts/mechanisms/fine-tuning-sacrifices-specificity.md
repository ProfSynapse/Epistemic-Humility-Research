---
aliases:
- Fine-tuning achieves high efficacy at the cost of specificity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fine-tuning-sacrifices-specificity
  type: mechanism
  status: canonical
cause: Applying standard fine-tuning (FT) to insert a new fact into an LLM
effect: Near-perfect efficacy (ES=100%) but severely degraded specificity -- roughly 60% of neighboring subjects are incorrectly updated (NS=40.4% on GPT-2 XL), indicating bleedover to unrelated facts
polarity: decreases
related:
- '[[2202.05262--rome-locating-editing-factual-associations]]'
- '[[model-editing]]'
- '[[rank-one-model-editing]]'
relationships:
- type: supported_by
  target: '[[2202.05262--rome-locating-editing-factual-associations]]'
  target_id: paper:2202.05262
  confidence: high
- type: related_to
  target: '[[model-editing]]'
  target_id: method:model-editing
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
---

Standard fine-tuning on a new fact achieves near-perfect efficacy -- the model reliably produces the updated answer -- but the gradient update spreads across many weights, causing neighboring subjects that share surface form or semantic proximity to be incorrectly updated as well (arXiv:2202.05262). On GPT-2 XL evaluated on CounterFact, fine-tuning achieves ES=100% while neighbor specificity drops to NS=40.4%, meaning roughly 60% of related but distinct facts are corrupted. This specificity collapse contrasts with [[rank-one-model-editing]] (ROME), which surgically targets the identified causal layer and preserves neighbor specificity.
