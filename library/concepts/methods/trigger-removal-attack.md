---
aliases:
- trigger token removal jailbreak
- trigger removal jailbreak
tags:
- kg/method
- concept
- method
kg:
  id: method:trigger-removal-attack
  type: method
  status: canonical
area: adversarial-robustness
related:
- '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
- '[[projection-layer-wise-relevance-propagation]]'
- '[[dominant-refusal-direction]]'
relationships:
- type: proposed_by
  target: '[[2502.09674--hidden-dimensions-llm-alignment-multi-dimensional-analysis]]'
  target_id: paper:2502.09674
  confidence: high
- type: derived_from
  target: '[[projection-layer-wise-relevance-propagation]]'
  target_id: method:projection-layer-wise-relevance-propagation
- type: related_to
  target: '[[dominant-refusal-direction]]'
  target_id: term:dominant-refusal-direction
---

The trigger-removal attack is a mechanistically-informed jailbreak procedure that first applies [[projection-layer-wise-relevance-propagation]] to the dominant refusal direction in the final transformer layers to identify the input tokens most responsible for activating refusal, then uses an LLM to iteratively rephrase the harmful prompt while avoiding those identified trigger tokens. Unlike surface-form jailbreaks, the rephrased prompts shift their projection on the dominant refusal direction toward the benign region of the safety residual space, achieving a pass rate of roughly 0.30 even after 160-shot safety fine-tuning exposure. The attack retains effectiveness because it targets the underlying geometric structure of refusal rather than surface-level pattern matching.

**Why it matters here:** This method demonstrates that internal refusal geometry (the [[dominant-refusal-direction]]) is mechanistically actionable: knowing which tokens activate the direction is sufficient to construct adversarial rephrases that bypass safety training, raising the cost of post-hoc refusal patching and motivating multi-directional safety approaches.

**Lineage:** derived from [[projection-layer-wise-relevance-propagation]]; targets the [[dominant-refusal-direction]] identified via the [[safety-residual-space]] decomposition.
