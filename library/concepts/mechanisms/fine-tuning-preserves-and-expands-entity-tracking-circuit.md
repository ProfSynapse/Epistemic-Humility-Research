---
aliases:
- Fine-tuning preserves and expands the entity-tracking circuit
- Base entity-tracking circuit persists after fine-tuning
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fine-tuning-preserves-and-expands-entity-tracking-circuit
  type: mechanism
  status: canonical
cause: "Conversational or arithmetic fine-tuning is applied to LLaMA-7B while preserving the architecture and component correspondence."
effect: "The base model's 72-head entity-tracking circuit remains highly faithful, while arithmetic fine-tuning recruits additional heads into a larger circuit with the same group functions."
polarity: modulates
related:
- '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
- '[[path-patching]]'
- '[[circuit-faithfulness]]'
relationships:
- type: supported_by
  target: '[[2402.14811--fine-tuning-enhances-existing-mechanisms-case-study]]'
  target_id: paper:2402.14811
  confidence: high
- type: related_to
  target: '[[path-patching]]'
  target_id: method:path-patching
  confidence: high
- type: related_to
  target: '[[circuit-faithfulness]]'
  target_id: metric:circuit-faithfulness
  confidence: high
---

The unchanged base circuit recovers 88% to 97% of the fine-tuned models' entity-tracking accuracy. Separately discovered circuits in the arithmetic-tuned models have 175 heads and approximately contain the base circuit.
