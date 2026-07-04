---
aliases:
- POS Scrubbing Raises LM Perplexity
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:pos-scrubbing-raises-perplexity
  type: mechanism
  status: canonical
cause: "Linearly erasing part-of-speech information from every transformer layer via [[concept-scrubbing]]."
effect: "Large increase in autoregressive language model perplexity (LEACE: 1.73-3.57 bits/byte vs. baseline 0.62-0.90; random erasure causes no change), demonstrating that LMs heavily rely on linearly encoded POS information."
polarity: increases
related:
- '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
- '[[leace]]'
- '[[concept-scrubbing]]'
- '[[universal-dependencies-pos]]'
relationships:
- type: supported_by
  target: '[[2306.03819--leace-perfect-linear-concept-erasure-closed-form]]'
  target_id: paper:2306.03819
  confidence: high
- type: related_to
  target: '[[leace]]'
  target_id: method:leace
- type: related_to
  target: '[[concept-scrubbing]]'
  target_id: method:concept-scrubbing
contradicted-by: []
---

When [[leace]] projections are applied at every layer of a transformer to erase [[universal-dependencies-pos]] tags, the language model's perplexity rises dramatically (from 0.62-0.90 to 1.73-3.57 bits/byte), while equivalent random projections cause no change. This demonstrates that LMs causally rely on linearly encoded part-of-speech information during generation, not merely correlating with it. The result is reported in arXiv:2306.03819 and corroborates the [[concept-scrubbing]] methodology as a causal diagnostic tool.
