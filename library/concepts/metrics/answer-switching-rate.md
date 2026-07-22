---
aliases:
- ASR (Answer Switching Rate)
- answer flip rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:answer-switching-rate
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
- '[[attack-success-rate]]'
- '[[kl-divergence]]'
relationships:
- type: proposed_by
  target: '[[2505.21800--directions-cones-exploring-multidimensional-representations-propositional-facts]]'
  target_id: paper:2505.21800
  confidence: high
- type: related_to
  target: '[[attack-success-rate]]'
  target_id: metric:attack-success-rate
  confidence: low
- type: related_to
  target: '[[kl-divergence]]'
  target_id: metric:kl-divergence
  confidence: medium
---

Answer Switching Rate (ASR) is the fraction of prompts the model originally answered correctly that flip to an untruthful answer after a causal intervention (activation addition on false statements, or directional ablation on true statements) along a candidate truth direction or concept-cone basis vector. It is computed per direction or per Monte Carlo sample drawn from a cone, and is the primary success measure for truth-direction and truth-cone causal interventions.

**Why it matters here:** ASR is the intervention-strength readout that lets a paper claim a subspace, not just a single direction, causally mediates a behavior; it is the metric-side analogue of the Answer Switching Rate the correctness-direction-rotation cell would need if it moved from a cosine-only readout to a causal-intervention readout.

**Lineage:** shares its acronym with, but is conceptually distinct from, [[attack-success-rate]] (jailbreak-elicitation success on a safety-aligned model); ASR here measures truthfulness-flip success on factual propositions, not refusal bypass. Complements [[kl-divergence]] as the paired fidelity check (does the intervention preserve unrelated behavior).
