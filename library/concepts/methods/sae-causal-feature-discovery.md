---
aliases:
- three-stage refusal pipeline
- jailbreak-critical feature pipeline
- SAE Causal Feature Discovery Pipeline
tags:
- kg/method
- concept
- method
kg:
  id: method:sae-causal-feature-discovery
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
- '[[refusal-direction]]'
- '[[sparse-autoencoder]]'
relationships:
- type: proposed_by
  target: '[[2509.09708--beyond-i-m-sorry-i-can-t]]'
  target_id: paper:2509.09708
  confidence: high
- type: derived_from
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
- type: derived_from
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

SAE Causal Feature Discovery is a three-stage pipeline that identifies a minimal
causal set of sparse-autoencoder features whose ablation flips a model from
refusal to compliance. Stage one selects the top-K SAE features by cosine
similarity to the refusal direction; stage two greedily prunes to a minimal
faithful subset using the 'I'-token logit as a surrogate for refusal strength;
stage three fits a [[factorization-machine]] to the remaining active features to
surface additional causally interacting feature pairs that a linear filter misses.
The method distinguishes primary active causal features from dormant compensatory
ones, revealing the [[refusal-hydra-effect]].

**Why it matters here:** Understanding which internal features mediate the
refusal-versus-answer decision is directly relevant to the epistemic-humility
programme's goal of reading and steering the known-unknown signal: the same causal
localization logic applies to answerability features.

**Lineage:** derived from [[refusal-direction]] (provides the seed similarity
ranking) and extends [[sparse-autoencoder]] (provides the feature dictionary);
depends on [[factorization-machine]] for pairwise interaction discovery.
