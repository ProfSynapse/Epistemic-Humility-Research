---
aliases:
- HALO
- HALOs
- human-aware losses
- Human-Aware Loss Functions (HALOs)
tags:
- kg/term
- concept
- term
kg:
  id: term:human-aware-loss-functions
  type: term
  status: canonical
area: methods
related:
- '[[2402.01306--kto-prospect-theoretic]]'
relationships:
- type: proposed_by
  target: '[[2402.01306--kto-prospect-theoretic]]'
  target_id: paper:2402.01306
  confidence: high
---

Human-Aware Loss Functions (HALOs) are alignment objectives that implicitly encode [[prospect-theory]] biases (particularly loss aversion) about how humans perceive and evaluate random outcomes. The KTO paper demonstrates that PPO, [[direct-preference-optimization]], and SLiC all belong to this family, and that membership in the HALO class correlates with stronger alignment performance, especially at scale.

**Why it matters here:** The HALO framing provides a unifying lens for comparing the three training arms in the abstention study: understanding whether a method is a HALO (and what inductive bias it encodes) helps predict when loss-aversion asymmetry aids or harms abstention calibration.

**Lineage:** introduced alongside [[kahneman-tversky-optimization]]; [[direct-preference-optimization]] and proximal-policy-optimization are retrospectively classified as HALOs.
