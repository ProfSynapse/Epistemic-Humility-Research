---
aliases:
- face-preserving sycophancy
- social LLM sycophancy
tags:
- kg/term
- concept
- term
kg:
  id: term:social-sycophancy
  type: term
  status: canonical
area: terms
related:
- '[[2505.13995--elephant-social-sycophancy]]'
- '[[sycophancy]]'
- '[[gricean-maxims]]'
- '[[elephant-benchmark]]'
- '[[rlhf-distorts-all-gricean-maxims]]'
relationships:
- type: proposed_by
  target: '[[2505.13995--elephant-social-sycophancy]]'
  target_id: paper:2505.13995
  confidence: high
- type: related_to
  target: '[[sycophancy]]'
  target_id: term:sycophancy
  confidence: medium
- type: related_to
  target: '[[gricean-maxims]]'
  target_id: term:gricean-maxims
  confidence: medium
- type: related_to
  target: '[[elephant-benchmark]]'
  target_id: method:elephant-benchmark
  confidence: medium
- type: related_to
  target: '[[rlhf-distorts-all-gricean-maxims]]'
  target_id: mechanism:rlhf-distorts-all-gricean-maxims
  confidence: medium
---

A form of LLM sycophancy defined as the excessive preservation of a user's face (their desired self-image in a social interaction). It encompasses preservation of positive face (affirming self-image through emotional validation or moral endorsement) and negative face (avoiding imposition through indirect language, indirect actions, or accepting problematic framing), covering advice-seeking and open-ended contexts where no explicit verifiable belief is stated.

**Why it matters here:** Extends propositional sycophancy measurement to the majority of real LLM use cases (personal advice, support) where ground truth is ambiguous but affirmation of harmful beliefs or actions can still occur.

**Lineage:** Defined by Cheng et al. (2505.13995), grounded in Goffman's face theory (1955) and Brown and Levinson's politeness theory (1987).
