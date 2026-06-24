---
aliases:
- ablation study
- causal ablation
- zero ablation
tags:
- kg/method
- concept
- method
kg:
  id: method:neuron-ablation
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[causal-intervention]]'
- '[[activation-patching]]'
- '[[knowledge-neurons]]'
relationships:
- type: related_to
  target: '[[causal-intervention]]'
  target_id: method:causal-intervention
- type: related_to
  target: '[[activation-patching]]'
  target_id: method:activation-patching
- type: related_to
  target: '[[knowledge-neurons]]'
  target_id: term:knowledge-neurons
---

Neuron ablation is an interpretability validation technique in which an identified neuron is fixed to zero (or to its mean activation) across all tokens and sequences, and the resulting change in language modeling loss is measured per context. It distinguishes causal contributors from mere correlates: a neuron that truly mediates a feature will produce measurable loss increase when zeroed, whereas one that is correlated but not causal will not. Ablation is commonly paired with probing to close the correlational gap.

**Why it matters here:** Ablating neurons that carry known-unknown signals can directly test whether those neurons causally govern abstention behavior, providing mechanistic grounding for any epistemic-humility training intervention.

**Lineage:** a form of [[causal-intervention]]; closely related to [[activation-patching]] (which replaces rather than zeros activations); used to validate [[knowledge-neurons]] localization claims.
