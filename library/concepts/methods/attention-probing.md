---
aliases:
- attention probe
- attention-pooling probe
- linear attention probe
tags:
- kg/method
- concept
- method
kg:
  id: method:attention-probing
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[chain-of-thought-faithfulness]]'
relationships:
- type: related_to
  target: '[[chain-of-thought-faithfulness]]'
  target_id: term:chain-of-thought-faithfulness
---

Attention probing applies a learned attention-pooling layer over a transformer
layer's hidden states to classify concepts (such as a model's committed final
answer) from variable-length activation prefixes. The probe is trained on random
prefix lengths so that it learns sequence-length-independent decoding rather than
position-specific cues; it is then evaluated at every generation step to track
how early the model's internal belief state commits to a conclusion.

**Why it matters here:** Attention probes provide a position-resolved readout of
internal commitment that can be compared against emitted token uncertainty,
making them a key tool for detecting performative chain-of-thought and measuring
the gap between a model's internal confidence and its expressed epistemic state.

**Lineage:** related to [[chain-of-thought-faithfulness]] as a measurement
instrument; [[probe-guided-early-exit]] extends this method into a
generation-stopping strategy.
