---
aliases:
- surrogate model confidence
- cross-model confidence transfer
- surrogate confidence
- black-box surrogate confidence
tags:
- kg/method
- concept
- method
kg:
  id: method:surrogate-confidence-estimation
  type: method
  status: canonical
area: methods
related:
- '[[2311.08877--llamas-know-what-gpts-dont-show]]'
- '[[verbalized-confidence]]'
- '[[confidence-elicitation]]'
- '[[consistency-based-confidence]]'
- '[[self-consistency]]'
- '[[selective-classification-auc]]'
- '[[auroc]]'
- '[[question-difficulty-transfer]]'
relationships:
- type: proposed_by
  target: '[[2311.08877--llamas-know-what-gpts-dont-show]]'
  target_id: paper:2311.08877
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
  confidence: medium
- type: related_to
  target: '[[confidence-elicitation]]'
  target_id: method:confidence-elicitation
  confidence: medium
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
- type: related_to
  target: '[[selective-classification-auc]]'
  target_id: metric:selective-classification-auc
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
- type: related_to
  target: '[[question-difficulty-transfer]]'
  target_id: term:question-difficulty-transfer
  confidence: medium
---

A confidence estimation technique for closed-source LLMs that borrows the token-level probabilities of an accessible open-weight surrogate model and pairs them with the target model's generated answer. The surrogate is queried on the same question, and its probability for its own preferred answer is used as the confidence score for the target model's output. Linguistic confidences and surrogate probabilities can be linearly interpolated via a scalar mixture weight alpha.

**Why it matters here:** Provides a practical, post-hoc confidence signal for API-only models that expose no logits, without requiring fine-tuning or internal access. Even weak surrogates (half the target's accuracy) outperform the target's own verbalized confidence, making this method applicable to any closed-source or opaque checkpoint as long as a related open-weight model exists. Directly relevant to evaluating Phase 1 abstention checkpoints if token probabilities become unavailable.

**Lineage:** Proposed in 2311.08877 as an alternative to verbalized-confidence for closed-source models; extends confidence-elicitation to the cross-model setting; the mixture variant sits between verbalized-confidence and consistency-based-confidence in complexity.
