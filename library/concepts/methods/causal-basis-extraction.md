---
aliases:
- CBE
- Causal Basis Extraction (CBE)
tags:
- kg/method
- concept
- method
kg:
  id: method:causal-basis-extraction
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
- '[[causal-intervention]]'
relationships:
- type: proposed_by
  target: '[[2303.08112--tuned-lens-eliciting-latent-predictions]]'
  target_id: paper:2303.08112
  confidence: high
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
---

Causal Basis Extraction (CBE) is an algorithm that identifies directions in the
residual stream with the highest causal influence on a lens (and by extension on
the model itself). It optimizes for directions that maximally shift the lens
output when ablated, then validates them by measuring the Spearman correlation
(rho = 0.89) between a direction's influence on the tuned lens and its influence
on the full model, confirming the lens is a reliable proxy for causal ranking.
The result is a compact, ranked basis of causally meaningful directions rather
than a flat enumeration of all residual-stream dimensions.

**Why it matters here:** CBE is directly relevant to epistemic humility research
because the same residual-stream basis that mediates factual predictions is a
candidate locus for known-unknown directions and steering vectors; methods that
locate causally influential directions inform where and how to intervene to
improve calibration or abstention.

**Lineage:** introduced in [[2303.08112--tuned-lens-eliciting-latent-predictions]];
conceptually a causal extension of linear-probe approaches, using
[[causal-intervention]] (ablation) to rank directions rather than passive
correlation.
