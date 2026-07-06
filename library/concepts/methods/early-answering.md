---
aliases:
- CoT truncation test
- early answering test
- Early Answering (CoT Truncation Test)
tags:
- kg/method
- concept
- method
kg:
  id: method:early-answering
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

Early answering is a CoT faithfulness test that progressively truncates a
chain-of-thought at each intermediate step, prompts the model with only the
partial reasoning, and records whether it produces the same final answer as the
full-CoT version. The proportion of matching answers across all truncation points
is summarized as the Area Over the Curve (AOC): a high AOC means the final
answer is stable from the earliest steps, indicating that subsequent reasoning
steps are likely [[post-hoc-reasoning]] elaboration rather than genuine
inference. Low AOC, by contrast, indicates the answer continues to depend on
later reasoning steps.

**Why it matters here:** The test provides a behavioral signature for
distinguishing genuine deliberative reasoning from rationalization, which is
central to whether chain-of-thought expressed uncertainty or confidence can be
trusted as an epistemic signal.

**Lineage:** derives from [[chain-of-thought-prompting]]; proposed alongside
[[adding-mistakes]] and [[filler-tokens-test]] as part of a three-test battery
for measuring CoT faithfulness.
