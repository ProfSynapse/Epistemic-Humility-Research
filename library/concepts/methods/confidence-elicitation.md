---
aliases:
- verbalized confidence
- black-box uncertainty estimation
- non-logit-based confidence
tags:
- kg/method
- concept
- method
kg:
  id: method:confidence-elicitation
  type: method
  status: canonical
area: methods
related:
- '[[verbalized-confidence]]'
- '[[consistency-based-confidence]]'
relationships:
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[consistency-based-confidence]]'
  target_id: method:consistency-based-confidence
---

Confidence elicitation is the process of estimating an LLM's confidence in its responses without access to model logits, fine-tuning, or proprietary internals. Instead of reading token probabilities directly, it relies on prompting the model to express uncertainty in words, sampling multiple responses and measuring their agreement, or using other black-box probing techniques. This makes it applicable to API-only deployments where internal model states are unavailable.

**Why it matters here:** Abstention research must work with models deployed behind APIs, so black-box elicitation methods are the practical path for measuring whether a model knows what it does not know without retraining or internal access.

**Lineage:** related to [[verbalized-confidence]] and [[consistency-based-confidence]], which are concrete instantiations of this general process.
