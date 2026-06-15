---
aliases:
- default hedged prediction
- blind guess
- default prediction
tags:
- kg/term
- concept
- term
kg:
  id: term:hedged-prediction
  type: term
  status: canonical
area: terms
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
- '[[unfamiliar-finetuning-examples]]'
- '[[hallucination]]'
relationships:
- type: proposed_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
- type: related_to
  target: '[[unfamiliar-finetuning-examples]]'
  target_id: term:unfamiliar-finetuning-examples
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

A hedged prediction is the loss-minimizing default output that a finetuned LLM
reverts to when a test input is highly unfamiliar. It mirrors the response
distribution associated with unfamiliar finetuning examples in the training set,
meaning the content and character of hallucinated outputs are shaped by what the
model learned to predict on those low-likelihood training instances.

**Why it matters here:** Understanding the hedged prediction mechanism explains
why filtering or re-labeling [[unfamiliar-finetuning-examples]] can change not
just hallucination rate but the specific form of incorrect outputs, which is
relevant to designing [[abstention]] training that produces genuine "I don't
know" responses rather than plausible-sounding wrong answers.

**Lineage:** introduced alongside [[unfamiliar-finetuning-examples]] in
[[2403.05612--unfamiliar-finetuning-examples]]; related to [[hallucination]]
and [[knowledge-boundary]].
