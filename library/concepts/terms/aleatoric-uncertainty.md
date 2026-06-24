---
aliases:
- irreducible uncertainty
- data uncertainty
- task-inherent ambiguity
tags:
- kg/term
- concept
- term
kg:
  id: term:aleatoric-uncertainty
  type: term
  status: canonical
area: terms
related:
- '[[2509.20088--causal-understanding-uncertainty]]'
- '[[calibration]]'
- '[[overconfidence]]'
- '[[knowledge-boundary]]'
- '[[mcqa-causal]]'
- '[[verbatim-memorization-probing]]'
relationships:
- type: proposed_by
  target: '[[2509.20088--causal-understanding-uncertainty]]'
  target_id: paper:2509.20088
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[knowledge-boundary]]'
  target_id: term:knowledge-boundary
  confidence: medium
- type: related_to
  target: '[[mcqa-causal]]'
  target_id: dataset:mcqa-causal
  confidence: medium
- type: related_to
  target: '[[verbatim-memorization-probing]]'
  target_id: method:verbatim-memorization-probing
  confidence: medium
---

Uncertainty that arises from intrinsic randomness or ambiguity in the data-generating process rather than from model ignorance. Aleatoric uncertainty cannot be reduced by providing the model with more training data or a larger model, because it reflects genuine ambiguity in the task itself (e.g., hedging language in causal statements, polysemous constructions). Contrasted with epistemic uncertainty, which reflects a knowledge gap the model could in principle close with more or better information.

**Why it matters here:** Distinguishing aleatoric from epistemic uncertainty is critical for diagnosing model failures: if a model is consistently wrong on a subset of inputs across paraphrase variants, that points to task-inherent ambiguity rather than a training gap, and adding data will not help. This distinction guides whether calibration training, data augmentation, or architectural changes are the right intervention.

**Lineage:** Conceptual distinction from Hullermeier and Waegeman (2021); operationalized via paraphrase consistency analysis in Lithgow-Serrano et al. (2025).
