---
aliases:
- Freezing most weights protects coherence even when the updated mask is random.
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:fixed-update-budget-protects-coherence-independent-of-circuit-selection
  type: mechanism
  status: canonical
cause: "Selective fine-tuning freezes 70 percent of model weights and updates only a matched 30 percent mask."
effect: "General language-modeling coherence is preserved regardless of whether the mask is circuit-derived or random, while unrestricted fine-tuning degrades perplexity."
polarity: prevents
related:
- '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
- '[[perplexity]]'
- '[[boolq]]'
relationships:
- type: supported_by
  target: '[[2607.19317--circuitkit-circuit-discovery-evaluation-application-toolkit-mechanistic]]'
  target_id: paper:2607.19317
  confidence: high
- type: related_to
  target: '[[perplexity]]'
  target_id: metric:perplexity
  confidence: high
- type: related_to
  target: '[[boolq]]'
  target_id: dataset:boolq
  confidence: high
---

In the Llama-3.2-3B-Instruct BoolQ fine-tuning study, circuit masks and equal-budget random masks both keep WikiText-2 perplexity near the unmodified model while full-parameter training degrades it. Across the broader 16-cell audit, mean circuit-minus-random accuracy change is -0.001, so the evidence supports the budget constraint rather than mask identity as the protective factor (Section 11.7; Table 9).
