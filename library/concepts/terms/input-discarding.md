---
aliases:
- input token discarding
- immediate input transformation
tags:
- kg/term
- concept
- term
kg:
  id: term:input-discarding
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[ll2020--interpreting-gpt-the-logit-lens]]'
- '[[2012.14913--transformer-ff-layers-key-value-memories]]'
- '[[logit-lens]]'
- '[[residual-stream]]'
- '[[gpt-2]]'
- '[[kl-divergence]]'
- '[[iterative-refinement-transformers]]'
relationships:
- type: proposed_by
  target: '[[ll2020--interpreting-gpt-the-logit-lens]]'
  target_id: paper:ll2020
  confidence: high
- type: related_to
  target: '[[logit-lens]]'
  target_id: method:logit-lens
- type: related_to
  target: '[[gpt-2]]'
  target_id: model:gpt-2
- type: related_to
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
- type: related_to
  target: '[[iterative-refinement-transformers]]'
  target_id: term:iterative-refinement-transformers
---

Input discarding is the empirical observation that GPT-style transformers
immediately convert input token representations into something close to
predicted-output space after the very first layer, rather than maintaining
an input-centric representation that gradually shifts toward output. The
phenomenon is measured by computing the KL divergence between the input
distribution and each intermediate layer's decoded distribution: a large
discontinuous jump after layer 0 signals that the model has already
discarded the raw input identity and is operating in predictive space
from the second layer onward.

**Why it matters here:** Input discarding constrains where and how factual
associations and uncertainty signals are processed: because the model
moves to predictive space immediately, intermediate representations cannot
be read as "copies of input tokens with edits" but must be interpreted as
evolving output predictions, which changes how probing and editing
interventions should be designed.

**Lineage:** discovered via [[logit-lens]] applied to [[gpt-2]];
motivates the [[iterative-refinement-transformers]] view of forward-pass
computation.
