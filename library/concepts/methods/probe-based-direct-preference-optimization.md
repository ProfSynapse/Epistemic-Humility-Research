---
aliases:
- Probe-based DPO
- Probe-scored direct preference optimization
tags:
- kg/method
- concept
- method
kg:
  id: method:probe-based-direct-preference-optimization
  type: method
  status: canonical
area: methods
related:
- '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
- '[[direct-preference-optimization]]'
- '[[linear-probe]]'
relationships:
- type: proposed_by
  target: '[[2510.21531--probe-based-fine-tuning-reducing-toxicity]]'
  target_id: paper:2510.21531
  confidence: high
- type: derived_from
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Probe-based direct preference optimization scores sampled responses with a
frozen activation probe. It labels the lowest-scoring response as chosen and
the highest-scoring response as rejected, then applies standard DPO to the
resulting preference pairs.

**Why it matters here:** The method converts an internal representation
readout into a training signal that changes model weights.

**Lineage:** It modifies [[direct-preference-optimization]] by replacing an
output classifier with a [[linear-probe]] during preference-pair construction.
