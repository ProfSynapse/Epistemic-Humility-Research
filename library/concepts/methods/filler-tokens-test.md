---
aliases:
- filler token ablation
- ellipsis token test
tags:
- kg/method
- concept
- method
kg:
  id: method:filler-tokens-test
  type: method
  status: canonical
area: verification
related:
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
- '[[chain-of-thought-prompting]]'
relationships:
- type: proposed_by
  target: '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
  target_id: paper:2307.13702
  confidence: high
- type: derived_from
  target: '[[chain-of-thought-prompting]]'
  target_id: method:chain-of-thought-prompting
---

The filler tokens test is a CoT faithfulness ablation that replaces the entire
chain-of-thought with a string of uninformative "..." tokens of equivalent length
before querying the model for a final answer. Comparing accuracy on this
filler-token condition against a no-CoT baseline and a full-CoT condition tests
whether CoT performance gains arise from the semantic content of the reasoning or
merely from increased test-time compute length, ruling out steganographic
explanations where useful information is encoded in token count or position rather
than in the reasoning text itself.

**Why it matters here:** By decoupling compute from content, the ablation helps
determine whether chain-of-thought improvements reflect genuine deliberative
inference (which would support using CoT uncertainty estimates as epistemic
signals) or are artifacts of sequential token generation independent of
reasoning substance.

**Lineage:** derives from [[chain-of-thought-prompting]]; forms the
compute-control arm of the three-test faithfulness battery alongside
[[early-answering]] and [[adding-mistakes]].
