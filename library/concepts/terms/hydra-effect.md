---
aliases:
- Hydra effect
- self-repair (language models)
- adaptive computation compensation
tags:
- kg/term
- concept
- term
kg:
  id: term:hydra-effect
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[causal-effect-decomposition]]'
- '[[refusal-hydra-effect]]'
relationships:
- type: proposed_by
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[causal-effect-decomposition]]'
  target_id: method:causal-effect-decomposition
- type: related_to
  target: '[[refusal-hydra-effect]]'
  target_id: term:refusal-hydra-effect
  confidence: high
---

The Hydra effect is a form of adaptive computation observed in autoregressive
transformers: ablating one attention layer causes another layer -- typically
the next one -- to substantially increase its own direct effect on the
max-likelihood-token logit, partially compensating for the ablation. McGrath
et al. (2023) coined the term and showed it holds even in models trained
without dropout, stochastic depth, or layer dropout, which rules out
training-time regularization as the sole explanation for the compensatory
redundancy.

**Why it matters here:** the Hydra effect means layers are not independent,
non-redundant computational units -- ablation studies and causal-attribution
claims about "what a layer does" can be confounded by downstream layers
silently picking up the slack, a concern that generalizes to safety-relevant
circuits such as the [[refusal-hydra-effect]] found in dormant SAE features.

**Lineage:** identified via [[causal-effect-decomposition]] (direct vs.
indirect effect analysis) on factual-recall prompts; [[refusal-hydra-effect]]
is a domain-specific instance of the same compensatory-redundancy pattern.
