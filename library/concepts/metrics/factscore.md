---
aliases:
- Factuality Score
- atomic factuality score
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:factscore
  type: metric
  status: canonical
area: metrics
---

FActScore decomposes a long-form generated response into its atomic constituent
facts and then labels each fact as supported or unsupported by querying a
retrieval-augmented external knowledge source (typically Wikipedia or a search
index). The final score is the fraction of atomic facts that are verified as
true, giving a fine-grained factuality signal that aggregates across all claims
in the response rather than producing a single holistic judgment.

**Why it matters here:** FActScore provides the primary factuality evaluation
signal for the [[conservative-reward-model]] approach in
[[2403.05612--unfamiliar-finetuning-examples]], measuring whether RL training
with a conservative reward model actually reduces hallucinated atomic claims
relative to SFT and answer-relabeling baselines.

**Lineage:** no formal lineage edges; used as an evaluation metric by
[[conservative-reward-model]].
