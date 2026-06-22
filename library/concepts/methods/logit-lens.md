---
aliases:
- vocabulary projection
- intermediate layer projection
- LogitLens
- nostalgebraist logit lens
tags:
- kg/method
- concept
- method
kg:
  id: method:logit-lens
  type: method
  status: canonical
area: mechanistic-interpretability
related:
- '[[tuned-lens]]'
- '[[prediction-trajectory]]'
- '[[residual-stream]]'
relationships:
- type: related_to
  target: '[[tuned-lens]]'
  target_id: method:tuned-lens
- type: related_to
  target: '[[prediction-trajectory]]'
  target_id: term:prediction-trajectory
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
---

The logit lens is an early-exiting technique (nostalgebraist, 2020) that decodes transformer hidden states at each layer directly into vocabulary space using the model's pretrained unembedding matrix, without any learned correction. It produces interpretable prediction trajectories on models whose residual stream evolves smoothly toward the final distribution, but is brittle, biased toward the last-token position, and fails to recover sensible distributions on architectures such as BLOOM and OPT. The [[tuned-lens]] remedies this by learning a per-layer affine correction that maps hidden states into a form the unembedding matrix can faithfully decode.

**Why it matters here:** Logit-lens trajectories reveal where in a network factual decisions crystallize, making it a foundational diagnostic for understanding knowledge localization and recall mechanisms relevant to calibration and epistemic behavior.

**Lineage:** foundational predecessor to [[tuned-lens]]; underlies [[prediction-trajectory]] analyses used for prompt-injection detection.
