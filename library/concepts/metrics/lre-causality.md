---
aliases:
- causality score
- Hard Causality
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:lre-causality
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[lre-faithfulness]]'
relationships:
- type: related_to
  target: '[[lre-faithfulness]]'
  target_id: metric:lre-faithfulness
---

LRE causality (also called the causality score or Hard Causality) measures the proportion of test cases in which applying a linear relational embedding (LRE) transformation to a subject's hidden state causes the model to produce the correct object token at the output. Unlike correlation-based probing metrics, causality scoring requires that the linear structure be actively interventional: patching in the LRE-transformed vector must flip the model's prediction to the correct relation target, confirming that the representation encodes the relation in a way the model actually uses during forward inference. Scores above 0.9 in the LRE literature indicate a nearly perfect, causally active linear relational representation.

**Why it matters here:** The distinction between correlational and causal readout is central to interpreting whether answerability probes merely correlate with abstention behaviour or whether the internal axis causally mediates it, which is the core interpretive question for Papers 3 and 4 of this project.

**Lineage:** companion metric to [[lre-faithfulness]], which measures how well the LRE reconstructs the target representation rather than how often it causes the correct output token.
