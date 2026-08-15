---
aliases:
- Superficial Alignment Hypothesis
- SAH
tags:
- kg/term
- concept
- term
kg:
  id: term:superficial-alignment-hypothesis
  type: term
  status: canonical
area: terms
related:
- '[[2305.11206--lima-less-more-alignment]]'
- '[[lima]]'
- '[[instruction-tuning]]'
relationships:
- type: proposed_by
  target: '[[2305.11206--lima-less-more-alignment]]'
  target_id: paper:2305.11206
  confidence: high
- type: related_to
  target: '[[lima]]'
  target_id: dataset:lima
  confidence: high
- type: related_to
  target: '[[instruction-tuning]]'
  target_id: method:instruction-tuning
  confidence: high
---

The hypothesis, stated by Zhou et al. (2023), that a model's knowledge and capabilities are learned almost entirely during pretraining, while alignment (instruction tuning, RLHF) teaches only which subdistribution of formats and styles to use when interacting with users. A corollary: a pretrained model can be sufficiently aligned with a small, stylistically-consistent set of examples, since the underlying capability is already present.

**Why it matters here:** this hypothesis is the theoretical anchor for the paper-2 related-work reframe: if alignment is mostly format-teaching rather than capability-teaching, then abstention behavior induced by prompting versus by training should be closely related surface phenomena, and divergences between them (e.g. [[prompt-cannot-override-rlvr-abstention-deficit]]) are informative about where training does more than reshuffle a format distribution already reachable by the base model.

**Lineage:** motivates [[lima]] and is empirically probed (and partially complicated) by later token-distribution-shift work such as URIAL (arXiv:2312.01552).
