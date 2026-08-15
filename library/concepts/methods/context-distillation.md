---
aliases:
- Prompt distillation
- Distilling a prompt into weights
tags:
- kg/method
- concept
- method
kg:
  id: method:context-distillation
  type: method
  status: canonical
area: methods
related:
- '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
- '[[kl-divergence]]'
- '[[hhh-helpful-honest-harmless]]'
- '[[in-context-learning]]'
relationships:
- type: proposed_by
  target: '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
  target_id: paper:2112.00861
  confidence: high
- type: related_to
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
  confidence: high
- type: related_to
  target: '[[hhh-helpful-honest-harmless]]'
  target_id: term:hhh-helpful-honest-harmless
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
---

Given a prompt context C that conditions a language model's output distribution P(X | C), context distillation trains a fresh copy of the model to reproduce that conditioned distribution without the prompt present at inference time, by fine-tuning with a loss equal to the KL divergence between P(X | C) (the prompted teacher) and the student model's own predictions P(X). The effect is to internalize the behavior a prompt induces directly into the weights, freeing up context-window budget and removing the runtime dependency on the prompt string.

**Why it matters here:** context distillation is the original weights-vs-prompt equivalence experiment: it directly tests whether a trained model can reproduce prompted behavior, and by how much performance changes when the same behavioral target is reached by gradient descent on a KL objective rather than by conditioning at inference time. It is the closest historical precedent to asking whether trained abstention behavior differs from prompted abstention behavior for a principled (not merely correlational) reason.

**Lineage:** related to knowledge distillation generally, but distills a specific prompt's conditional distribution rather than a teacher model's overall behavior; contrast with [[in-context-learning]] and [[urial]], which keep the prompt at inference time instead of internalizing it via a training step.
