---
aliases:
- URIAL
- Untuned LLMs with Restyled In-context ALignment
tags:
- kg/method
- concept
- method
kg:
  id: method:urial
  type: method
  status: canonical
area: methods
related:
- '[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]'
- '[[in-context-learning]]'
- '[[superficial-alignment-hypothesis]]'
- '[[lima]]'
relationships:
- type: proposed_by
  target: '[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]'
  target_id: paper:2312.01552
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
- type: related_to
  target: '[[superficial-alignment-hypothesis]]'
  target_id: term:superficial-alignment-hypothesis
  confidence: high
- type: related_to
  target: '[[lima]]'
  target_id: dataset:lima
  confidence: medium
---

A tuning-free alignment method: a base (untuned) LLM is given a fixed system prompt plus as few as K=3 constant, restyled in-context demonstrations that model the discourse style of a helpful AI assistant. No gradient update is performed; alignment is entirely a prompting-time effect. Lin et al. (2023) show this closes most of the gap to, and on strong base models exceeds, SFT- and RLHF-tuned counterparts on the just-eval-instruct benchmark.

**Why it matters here:** URIAL is the strongest available existence proof that surface-level alignment behavior, including at least part of what looks like trained refusal/caution style, can be reproduced with zero weight updates. It sharpens the prompt-vs-training question this related-work reframe is built around: if K=3 ICL examples close most of the SFT/RLHF gap on general instruction-following, any residual gap specific to abstention (see [[prompt-cannot-override-rlvr-abstention-deficit]]) is the more informative signal about what training adds that prompting cannot.

**Lineage:** builds directly on the [[superficial-alignment-hypothesis]] and [[lima]] (LIMA, arXiv:2305.11206), pushing the same claim from "1,000 SFT examples suffice" to "zero gradient updates suffice."
