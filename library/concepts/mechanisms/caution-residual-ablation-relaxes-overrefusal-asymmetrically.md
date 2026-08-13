---
aliases:
- Caution-residual ablation relaxes over-refusal asymmetrically
- Caution is relaxable but not installable by steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  type: mechanism
  status: canonical
cause: "Ablating the caution residual direction (activation steering at inference) in a small instruction-tuned model that over-refuses known questions."
effect: "Over-refusal on known questions drops from 0.994 to 0.030 with clean specificity, but no steering intervention installs abstention on genuine unknowns - caution is causally relaxable but not installable, an asymmetry specific to the abstention behavior."
polarity: decreases
related:
- '[[internal-paper3--knows-but-doesnt-say]]'
- '[[answerability-subspace-erasure-degrades-answerability-behavior]]'
- '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
- '[[refusal-direction]]'
- '[[residual-stream]]'
- '[[caution-install-bounded-site-sweep]]'
- '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
relationships:
- type: supported_by
  target: '[[internal-paper3--knows-but-doesnt-say]]'
  target_id: paper:internal-paper3
  confidence: high
- type: related_to
  target: '[[caution-install-bounded-site-sweep]]'
  target_id: experiment:caution-install-bounded-site-sweep
  confidence: high
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome
    (falsifier does not fire on the trained clean-SFT-to-GRPO-v2 lineage;
    this asymmetry survives the bounded search as an exploratory lead, see
    [[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]])
- type: related_to
  target: '[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]'
  target_id: mechanism:caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b
  confidence: medium
  evidence:
  - experiments/caution-install-bounded-site-sweep/AMENDMENT.md#outcome (G1
    actuation clears broadly while G3 specificity and G2 selectivity remain
    unresolved, complicating rather than settling the raw-base asymmetry)
- type: related_to
  target: '[[answerability-subspace-erasure-degrades-answerability-behavior]]'
  target_id: mechanism:answerability-subspace-erasure-degrades-answerability-behavior
  confidence: medium
- type: related_to
  target: '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
  target_id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: high
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

Paper 3 Result 3 uses activation steering as a causal probe of the doubt/caution
decomposition. Ablating the caution residual cuts over-refusal on known questions
0.994 to 0.030 with clean specificity (correct-on-known preserved), but no
intervention tried induces appropriate abstention on true unknowns. The control is
asymmetric: excess caution can be relaxed, missing caution cannot be installed by
steering. This mirrors the behavioral asymmetry that motivates reading (not steering)
the internal axes as the deployment route.

**Bounded search status (2026-08-13):** [[caution-install-bounded-site-sweep]]
gave this claim its first pre-registered bounded test on the trained
clean-SFT-to-GRPO-v2 lineage: seven write sites, two write positions, an
eight-rung dose ladder, and three magnitude-matched two-site pairs. The
falsifier did not fire, so the asymmetry survives as stated here. It
survives with a complication, not a clean reproduction: G1 actuation
cleared at every dose-viable site (five of five, held-out confab
clean_tighten 0.870-0.955), so raw refusal-inducing actuation is not scarce
on this lineage; the falsifier stayed silent because G3 direction
specificity passed at only one of those sites and G2 selectivity could not
be adjudicated at any of them (see
[[caution-install-actuates-but-specificity-unresolved-on-trained-qwen3-4b]]).
Tier 2, exploratory; a lead, not a claim.
