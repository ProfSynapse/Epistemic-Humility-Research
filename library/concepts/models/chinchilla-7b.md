---
aliases:
- Chinchilla 7B
- 7B Chinchilla
tags:
- kg/model
- concept
- model
kg:
  id: model:chinchilla-7b
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
- '[[hydra-effect]]'
relationships:
- type: related_to
  target: '[[2307.15771--hydra-effect-emergent-self-repair-language-model]]'
  target_id: paper:2307.15771
  confidence: high
- type: related_to
  target: '[[hydra-effect]]'
  target_id: term:hydra-effect
  confidence: high
---

Chinchilla 7B is the 7-billion-parameter member of DeepMind's compute-optimal
Chinchilla model family (Hoffmann et al., 2022), trained with a token-to-
parameter ratio tuned for compute-optimal scaling and, notably, with no
dropout, stochastic depth, or layer dropout at any point in training.

**Why it matters here:** McGrath et al. (2023) use Chinchilla 7B (32 attention
layers) as the analysis subject for their causal study of the
[[hydra-effect]] and erasure-MLP motifs. Its dropout-free training regimen is
load-bearing for the paper's argument: because the Hydra effect still occurs
in this model, training-time dropout cannot be the sole explanation for
layer-ablation self-repair.

**Lineage:** a member of the Chinchilla compute-optimal scaling family;
serves as the primary evaluation model for [[causal-effect-decomposition]]
studies of self-repair on [[counterfact]] factual-recall prompts.
