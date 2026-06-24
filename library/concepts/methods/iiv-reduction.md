---
aliases:
- Is-It-Valid reduction
- IIV classification reduction
- generation-to-classification reduction
tags:
- kg/method
- concept
- method
kg:
  id: method:iiv-reduction
  type: method
  status: canonical
area: methods
related:
- '[[2509.04664--why-language-models-hallucinate]]'
- '[[hallucination]]'
- '[[calibration]]'
- '[[generation-discrimination-gap]]'
- '[[overconfidence]]'
relationships:
- type: proposed_by
  target: '[[2509.04664--why-language-models-hallucinate]]'
  target_id: paper:2509.04664
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
---

A formal reduction from generative language modeling to binary classification: a base model is used as an Is-It-Valid (IIV) classifier by thresholding its output probability at 1/|error set|, and lower bounds on the IIV misclassification rate translate into lower bounds on the generation error rate via the inequality error_rate >= 2 * IIV_misclassification - max_error_set / min_valid_set - delta.

**Why it matters here:** Demystifies hallucination as a consequence of natural statistical pressures in density estimation rather than a model-specific failure mode, and connects decades of binary-classification theory to generative error analysis.

**Lineage:** Extends Kalai and Vempala (2024) which covered a special case without prompts or abstentions; generalizes to prompted settings in Theorem 1 (Section 3.2) of this paper.
