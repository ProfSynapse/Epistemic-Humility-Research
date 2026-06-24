---
aliases:
- exact token probing
- exact answer probe
- answer-span probing
tags:
- kg/method
- concept
- method
kg:
  id: method:exact-answer-token-probing
  type: method
  status: canonical
area: methods
related:
- '[[2410.02707--llms-know-more-than-they-show]]'
- '[[linear-probe]]'
- '[[generation-discrimination-gap]]'
- '[[truth-direction]]'
- '[[gradient-structure-encodes-output-correctness]]'
relationships:
- type: proposed_by
  target: '[[2410.02707--llms-know-more-than-they-show]]'
  target_id: paper:2410.02707
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: medium
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: medium
- type: related_to
  target: '[[gradient-structure-encodes-output-correctness]]'
  target_id: mechanism:gradient-structure-encodes-output-correctness
  confidence: medium
---

A linear probing classifier trained on the intermediate LLM activations extracted at the specific tokens that constitute the exact answer in a generated response (e.g., 'Hartford' in a long answer string), rather than at the last generated token, the end-of-question token, or a mean over all generated tokens.

**Why it matters here:** Concentrating probing at exact answer tokens reliably raises error-detection AUC by several points for probing classifiers (up to 0.85-0.95) because truthfulness signal is spatially concentrated at those positions. This is the primary methodological contribution of 2410.02707 and a complementary finding to gradient-space localization in Grad Detect.

**Lineage:** Extends the probing-classifier literature (Burns et al. 2022; Kadavath et al. 2022; Li et al. 2024) by changing the token selection strategy rather than the classifier or feature type. Self-extraction of exact answer spans uses a few-shot instruct-model call.
