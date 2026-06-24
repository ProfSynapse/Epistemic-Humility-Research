---
aliases:
- Generation-Discrimination Gap
- G-D gap
tags:
- kg/term
- concept
- term
kg:
  id: term:generation-discrimination-gap
  type: term
  status: canonical
area: terms
related:
- '[[2306.03341--inference-time-intervention]]'
- '[[truth-direction]]'
- '[[self-knowledge]]'
relationships:
- type: proposed_by
  target: '[[2306.03341--inference-time-intervention]]'
  target_id: paper:2306.03341
  confidence: medium
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[self-knowledge]]'
  target_id: term:self-knowledge
  confidence: medium
---

The generation-discrimination gap is the difference between how well a model can
discriminate true from false statements via a linear probe on its internal
activations (probe accuracy) and how truthfully it generates directly (generation
accuracy). The term was coined by Saunders et al. (2022) and operationalized by Li
et al. as a roughly 40-point gap on LLaMA-7B over TruthfulQA.

**Why it matters here:** the gap is the empirical case that a model "knows" more
than it "says", which implies the problem is eliciting latent knowledge rather
than acquiring it. For abstention and calibration work, an analogous gap can exist
between a model's internal uncertainty representation and its
[[verbalized-confidence]].

**Lineage:** introduced by Saunders et al. as the G-D gap and given a concrete
probe-versus-generation measurement by [[inference-time-intervention]].
