---
aliases:
- hydra effect in refusal
- dormant redundant features
- compensatory dormant features
tags:
- kg/term
- concept
- term
kg:
  id: term:refusal-hydra-effect
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
- '[[caution-readout-is-low-rank-on-collinear-carriers]]'
relationships:
- type: proposed_by
  target: '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
  target_id: paper:2509.09708
  confidence: high
- type: related_to
  target: '[[caution-readout-is-low-rank-on-collinear-carriers]]'
  target_id: mechanism:caution-readout-is-low-rank-on-collinear-carriers
  confidence: high
---

The refusal hydra effect is the phenomenon in which SAE features that show zero
activation on a harmful prompt (dormant or silent features) nonetheless play a
causally necessary role in maintaining refusal behavior. When the primary active
causal features are ablated, the previously dormant features switch on and
partially compensate, preserving refusal even though they were invisible to
activation-based feature selection. The name is borrowed from the circuits
literature on the hydra effect, which describes analogous compensatory redundancy
in factual recall.

**Why it matters here:** Compensatory dormant features mean that naive ablation
experiments underestimate the true circuit size for any safety-relevant behavior,
including the known-unknown gate: a probe that captures only active features at
prompt time may miss the full set of features the model recruits when the primary
ones are suppressed.

**Lineage:** a domain-specific instance of the broader hydra effect concept in
mechanistic interpretability; discovered via [[sae-causal-feature-discovery]].
