---
aliases:
- tokenizer round-trip residual
- flow instability
- inter-seed denoising variance
- u_r
- u_f
- u_s
- World Model Hallucination Predictors
tags:
- kg/method
- concept
- method
kg:
  id: method:hallucination-predictor-world-model
  type: method
  status: canonical
area: verification
related:
- '[[2606.27326--hallucination-world-models-predictable-preventable]]'
- '[[world-model-hallucination-modes]]'
relationships:
- type: proposed_by
  target: '[[2606.27326--hallucination-world-models-predictable-preventable]]'
  target_id: paper:2606.27326
  confidence: high
- type: derived_from
  target: '[[world-model-hallucination-modes]]'
  target_id: term:world-model-hallucination-modes
---

Three label-free, training-free runtime signals that predict hallucination before it manifests, each targeting one mode of the [[world-model-hallucination-modes]] taxonomy. Tokenizer round-trip residual (u_r) measures the latent-space norm of the encode-then-decode-then-re-encode round trip for the predicted next latent, targeting perceptual hallucination. Flow instability (u_f) measures the mean shift in the dynamics denoiser's clean-target prediction across successive Euler substeps, targeting action-marginalized hallucination. Inter-seed denoising variance (u_s) measures variance of the next-latent prediction across N independent denoising seeds at fixed context and action, targeting scene-diverging hallucination. All three signals are normalized by per-step latent RMS change to remove confound from high-activity transitions.

**Why it matters here:** These predictors are a concrete instance of uncertainty quantification for black-box generation processes, providing proxy confidence signals without access to ground-truth labels. The approach is directly relevant to hallucination detection under epistemic uncertainty: a model that cannot assess where its predictions are unreliable cannot exercise appropriate caution.

**Lineage:** derives from [[world-model-hallucination-modes]]; introduced by [[2606.27326--hallucination-world-models-predictable-preventable]].
