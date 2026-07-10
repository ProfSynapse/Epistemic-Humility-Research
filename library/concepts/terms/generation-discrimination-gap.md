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

**mechanism program in-house evidence (regimen-robust):** the
[[mech-interp-model-variation-panel]] program reproduces the gap in the
calibrated-epistemic-humility setting and shows it survives method variation.
Across five fine-tuning regimens (SFT-DPO-GRPO, SFT-KTO-GRPO, GRPO v2, GRPO-DPO,
KTO) the final-adapter delta is highly separable on internal activations
(pairwise AUC ~0.98-0.99, set by the final training stage) yet does not steer
generated behavior safely (best four-cell macro recall 0.695; KTO's sharp L11
axis failed a generated-replay behavior gate). This ties the gap to
[[gap-4-probe-transfer]]: humility fine-tuning moves the representation, but the
moved signal is the *performance* of humility read off internal state rather than
a behaviorally controllable calibration surface. The planned mechanism response
follows ITI's lesson that the gap closes by *where* a direction is applied
(sparse attention heads, token-by-token during generation), not by a sharper
single residual-stream axis.
