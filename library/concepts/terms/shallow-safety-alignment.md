---
aliases:
- Shallow safety alignment
- A few tokens deep alignment
tags:
- kg/term
- concept
- term
kg:
  id: term:shallow-safety-alignment
  type: term
  status: canonical
area: terms
related:
- '[[2406.05946--safety-alignment-should-be-made-more-than]]'
- '[[safety-alignment-concentrates-on-first-output-tokens]]'
relationships:
- type: proposed_by
  target: '[[2406.05946--safety-alignment-should-be-made-more-than]]'
  target_id: paper:2406.05946
  confidence: high
- type: related_to
  target: '[[safety-alignment-concentrates-on-first-output-tokens]]'
  target_id: mechanism:safety-alignment-concentrates-on-first-output-tokens
  confidence: high
---

Qi et al. (2024) name "shallow safety alignment" the failure mode where an aligned model's generative distribution is adapted from its unaligned base mostly over the first few output tokens (typically the refusal prefix, e.g. "I cannot", "I apologize"), rather than throughout the full response. Once a generation is forced past this initial refusal window (by adversarial suffixes, prefilling attacks, decoding-parameter manipulation, or a few steps of fine-tuning), the model's behavior reverts toward the unaligned base distribution.

**Why it matters here:** shallow safety alignment is a training-side analogue of the token-distribution-shift finding in URIAL (arXiv:2312.01552): both show alignment concentrating its effect on a small number of tokens rather than reshaping the whole response distribution, but here the mechanism is a training vulnerability rather than a prompting equivalence result.
