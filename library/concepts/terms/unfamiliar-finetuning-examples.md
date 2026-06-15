---
aliases:
- unfamiliar examples
- long-tail finetuning examples
- out-of-scope finetuning data
tags:
- kg/term
- concept
- term
kg:
  id: term:unfamiliar-finetuning-examples
  type: term
  status: canonical
area: terms
related:
- '[[2403.05612--unfamiliar-finetuning-examples]]'
relationships:
- type: proposed_by
  target: '[[2403.05612--unfamiliar-finetuning-examples]]'
  target_id: paper:2403.05612
  confidence: high
---

Unfamiliar finetuning examples are SFT training instances whose correct answers
carry high negative log-likelihood under the pretrained model, indicating that
the concept falls outside the base model's scope of parametric knowledge.
Empirically, the proportion of such examples in the SFT corpus is the primary
driver of post-SFT hallucination, not SFT as a training procedure in general.

**Why it matters here:** The finding that unfamiliar examples (rather than SFT
volume or format) cause hallucination reframes the abstention training problem:
controlling the familiarity distribution of SFT data is a prerequisite to
reliably teaching a model to say "I don't know" without inducing spurious
refusals on known questions. This connects directly to [[sft-unknown-examples-drive-hallucination]].

**Lineage:** related to [[hallucination]], [[knowledge-boundary]], and
[[hedged-prediction]]; the mechanism is formalized in
[[unfamiliar-ft-examples-drive-hallucination-character]].
