---
aliases:
- format preference uncertainty
- MCQ response-format uncertainty
tags:
- kg/term
- concept
- term
kg:
  id: term:format-uncertainty
  type: term
  status: canonical
area: terms
related:
- '[[2310.11732--calibration-aligned-multiple-choice]]'
- '[[answer-uncertainty]]'
- '[[overconfidence]]'
- '[[in-context-learning]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
relationships:
- type: proposed_by
  target: '[[2310.11732--calibration-aligned-multiple-choice]]'
  target_id: paper:2310.11732
  confidence: high
- type: related_to
  target: '[[answer-uncertainty]]'
  target_id: term:answer-uncertainty
  confidence: medium
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: medium
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: medium
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: medium
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: medium
---

In the MCQ setting, the component of a language model's predictive probability that reflects uncertainty about whether to begin the response with a choice letter at all, as opposed to uncertainty about which choice is correct. Formally, it is the model's marginal probability over the direct-answer format F_c (Equation 2-3 in He et al. 2023). Pre-trained models have high format uncertainty in zero-shot settings; ICL reduces it by demonstrating the expected format.

**Why it matters here:** Disentangling format uncertainty from answer uncertainty explains why ICL calibrates pretrained models but not aligned ones: ICL collapses format uncertainty but cannot repair answer uncertainty that alignment has corrupted.

**Lineage:** Introduced in He et al. 2023 (arXiv:2310.11732) as a formal decomposition of the MCQ predictive probability.
