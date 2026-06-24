---
aliases:
- lexical mediation
- VA lexical mediation
- token emission VA modulation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:lexical-mediation-links-va-steering-to-behavioral-control
  type: mechanism
  status: canonical
cause: "Shifting the VA coordinates of LLM residual stream activations via steering along the VA subspace."
effect: "The emission log-odds of refusal-associated tokens (e.g., 'I can't', 'Sorry') and compliance-associated tokens (e.g., 'Here', 'Sure') change proportionally, driving downstream refusal and sycophancy behavior."
polarity: mediates
related:
- '[[2604.03147--sycophancy-internal-representations]]'
- '[[arousal-axis-monotonically-controls-refusal-and-sycophancy]]'
- '[[valence-arousal-subspace]]'
- '[[va-subspace-extraction]]'
- '[[refusal-direction-mediates-refusal]]'
- '[[refusal-direction]]'
- '[[steering-vector]]'
- '[[sycophancy]]'
- '[[safety-refusal]]'
relationships:
- type: supported_by
  target: '[[2604.03147--sycophancy-internal-representations]]'
  target_id: paper:2604.03147
  confidence: high
- type: related_to
  target: '[[arousal-axis-monotonically-controls-refusal-and-sycophancy]]'
  target_id: mechanism:arousal-axis-monotonically-controls-refusal-and-sycophancy
  confidence: high
- type: related_to
  target: '[[valence-arousal-subspace]]'
  target_id: term:valence-arousal-subspace
  confidence: high
- type: related_to
  target: '[[va-subspace-extraction]]'
  target_id: method:va-subspace-extraction
  confidence: high
- type: related_to
  target: '[[refusal-direction-mediates-refusal]]'
  target_id: mechanism:refusal-direction-mediates-refusal
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: high
- type: related_to
  target: '[[safety-refusal]]'
  target_id: term:safety-refusal
  confidence: high
---

Refusal tokens cluster in the low-arousal, negative-valence region of the unembedding space (83.4% of refusals begin with 'I'; 'I can't' appears in 77.1% of refusals and 0% of compliances). Arousal steering at alpha=+0.30 shifts delta log-odds by -5.63 and reduces P(refusal tokens) from 89.6% to 65.4%. Clamping the logits of 21 refusal/compliance tokens to unsteered values collapses arousal-induced refusal from 86.5% to 26.0%, while clamping 21 random tokens leaves it at 86.5% (Table 14). Under alpha=-0.10, refusal/compliance clamping reduces steered refusal from 90.0% to 44.0% while random clamping has no effect. Emotional prefixes shift representations toward -V/-A, with the strongest prefix (delta-V=0.11, delta-A=0.07) increasing refusal by 30pp, further confirming the lexical pathway. The contrastive refusal direction lies 86.5 degrees from the VA plane, yet both paths achieve behavioral control via the same downstream token-emission mechanism.
