---
aliases:
- slow thinking behaviors
- extended chain-of-thought reasoning
- non-linear reasoning
tags:
- kg/term
- concept
- term
kg:
  id: term:slow-thinking
  type: term
  status: canonical
area: calibration
related:
- '[[verbalized-confidence]]'
relationships:
- type: derived_from
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
---

Slow thinking refers to the set of deliberative, non-linear behaviors that reasoning LLMs exhibit during chain-of-thought generation: exploring alternative approaches, verifying intermediate conclusions, and backtracking from errors before committing to a final answer. It contrasts with direct step-by-step linear generation in standard instruction-tuned models, which produce each token in a single forward pass without explicit self-revision. The mechanism is typically implemented through extended reasoning traces trained with reinforcement learning or distillation from a teacher model that rewards arriving at correct final answers via exploratory paths.

**Why it matters here:** Slow thinking changes the relationship between a model's internal deliberation and its expressed confidence, raising the question of whether more exploration produces better-calibrated outputs or merely more verbose ones that can still systematically diverge from the model's actual uncertainty.

**Lineage:** extends [[verbalized-confidence]] as a richer behavioral context for uncertainty expression.
