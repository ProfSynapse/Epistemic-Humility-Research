---
aliases:
- self versus external correctness probing
- disagreement-subset privileged-knowledge probing
- self-peer correctness probe comparison
tags:
- kg/method
- concept
- method
kg:
  id: method:self-vs-peer-correctness-probing
  type: method
  status: canonical
area: verification
related:
- '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
- '[[linear-probe]]'
- '[[privileged-correctness-knowledge]]'
- '[[premium-gap]]'
relationships:
- type: proposed_by
  target: '[[2604.12373--masked-consensus-disentangling-privileged-knowledge-llm-correctness]]'
  target_id: paper:2604.12373
  confidence: high
- type: variation_of
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[privileged-correctness-knowledge]]'
  target_id: term:privileged-correctness-knowledge
  confidence: high
- type: measured_by
  target: '[[premium-gap]]'
  target_id: metric:premium-gap
  confidence: high
---

Self-versus-peer correctness probing trains classifiers to predict one target model's answer correctness from either that model's own question representation or another model's representation of the same question. It trains on full data and separately evaluates target-source disagreement items so shared correctness patterns cannot act as a positive proxy.

**Why it matters here:** The comparison tests whether a target readout contains model-specific correctness information beyond question features available to peer models.

**Lineage:** The method is a controlled use of [[linear-probe]] evaluation. It summarizes self advantage with the [[premium-gap]] and treats disagreement filtering as an evaluation operation rather than a training set.
