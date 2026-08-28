---
aliases:
- category-held-out cross-validation
- held-out topic probing
- held-out category generalization test
tags:
- kg/method
- concept
- method
kg:
  id: method:category-held-out-probing
  type: method
  status: canonical
area: methods
related:
- '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2603.18280--detection-cheap-routing-learned-why-refusal-based]]'
  target_id: paper:2603.18280
  confidence: high
- type: variation_of
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Category-held-out probing excludes one semantic topic from classifier training and uses it only for testing. The protocol repeats across topics to test cross-category transfer instead of within-topic separability.

**Why it matters here:** It supplies a stronger test that a readout captures a general concept rather than corpus-specific lexical or topical structure.

**Lineage:** It is a cross-validation variant of [[linear-probe]] evaluation with the semantic category as the held-out unit.
