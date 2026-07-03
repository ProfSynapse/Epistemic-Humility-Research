---
aliases:
- CAA
- contrastive activation addition
- steering vectors
- representation engineering steering
- Activation Steering
- representation steering
- inference-time steering
- activation-level intervention
- SAE latent steering
- representation engineering
- latent steering
- causal steering
- linear behavioral control
- residual stream addition
tags:
- kg/method
- concept
- method
kg:
  id: method:activation-steering
  type: method
  status: canonical
area: steering
related:
- '[[persona-vectors]]'
relationships:
- type: derived_from
  target: '[[persona-vectors]]'
  target_id: method:persona-vectors
---

Approach to LLM behavioral control that adds learned steering vectors to intermediate
hidden states during inference while keeping all model weights frozen. Steering vectors
are obtained by contrasting residual-stream activations under exhibited versus
suppressed behavior conditions, typically via mean-difference or linear probing.
Effective for single-behavior interventions; does not extend gracefully to
multi-behavior compositional scenarios where independently derived vectors may
interfere with one another.

**Why it matters here:** Activation steering is the primary experimental tool for
testing whether epistemic-humility behaviors (truthfulness, calibrated uncertainty,
refusal propensity) have identifiable geometric structure in the residual stream that
can be causally intervened upon, connecting directly to the [[answerability-subspace]]
and [[known-unknown-direction]] work in this research program.

**Lineage:** derived from [[persona-vectors]] (character-trait activation patterns);
contrasted with [[compositional-steering-tokens]] (input-embedding space) and
[[lora-dare]] (parameter merging) in multi-behavior steering evaluations.
