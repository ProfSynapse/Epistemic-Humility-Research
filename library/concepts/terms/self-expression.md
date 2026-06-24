---
aliases:
- LLM self-expression
- faithful knowledge expression
- knowledge faithfulness
tags:
- kg/term
- concept
- term
kg:
  id: term:self-expression
  type: term
  status: canonical
area: terms
related:
- '[[2409.18786--survey-honesty-of-llms]]'
- '[[self-knowledge]]'
- '[[generation-discrimination-gap]]'
- '[[spurious-dishonesty]]'
- '[[hallucination]]'
- '[[sycophancy]]'
relationships:
- type: proposed_by
  target: '[[2409.18786--survey-honesty-of-llms]]'
  target_id: paper:2409.18786
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[spurious-dishonesty]]'
  target_id: term:spurious-dishonesty
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
---

Self-expression is the capacity of a language model to faithfully convey its internal knowledge (both parametric and in-context) in generated outputs, avoiding fabrication and sycophantic distortion. It is distinct from self-knowledge: a model may correctly identify what it knows while still failing to express it accurately due to training artifacts, prompt sensitivity, or decoding dynamics.

**Why it matters here:** Self-expression is the output-side complement to self-knowledge in the dual-lens honesty framework. Failures of self-expression (hallucination, sycophancy, context-ignoring) can occur even when the model's internal representations are well-calibrated, making it a separate target for evaluation and intervention.

**Lineage:** Formalized as the second axis of LLM honesty by Li et al. 2024 (2409.18786). Closely related to the generation-discrimination gap, which quantifies how much a model's output-level truthfulness lags behind its representational truthfulness.
