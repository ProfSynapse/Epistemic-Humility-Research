---
aliases:
- text surface form predicts boundary elevation
- question surface features carry part of the reads-as-known elevation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:text-surface-form-predicts-boundary-elevation
  type: mechanism
  status: canonical
cause: "Regressing the confab cloud's knowledge-boundary projection on raw text-surface features of the question (rare-word fraction, corpus log-frequency, proper-noun count, length)."
effect: "A substantial part of the confab-vs-refused boundary elevation is linearly predictable from surface form (AUROC 0.84 drops to 0.68-0.70 after residualization), while the internal familiarity direction explains none of it (0.84 to 0.83) and familiarity alone is at chance unmatched (0.51). Surface form shapes where a question lands on the boundary axis, but familiarity per se is not the confabulation pusher on this checkpoint."
polarity: mediates
related:
- '[[internal-al-prep-confab-cloud--true-checkpoint]]'
- '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
- '[[confab-cloud]]'
- '[[entity-recognition-direction]]'
relationships:
- type: supported_by
  target: '[[internal-al-prep-confab-cloud--true-checkpoint]]'
  target_id: paper:internal-al-prep-confab-cloud
  confidence: high
- type: related_to
  target: '[[question-familiarity-draws-confabulation-at-matched-doubt]]'
  target_id: mechanism:question-familiarity-draws-confabulation-at-matched-doubt
  confidence: high
- type: related_to
  target: '[[confab-cloud]]'
  target_id: term:confab-cloud
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction]]'
  target_id: term:entity-recognition-direction
  confidence: medium
---

Session-0038 refinement (analysis/amendment_al_prep/familiarity_vs_knowing_report.json,
TRUE A0 surface) of the session-0037 familiarity finding. The 0037 result
(familiarity proxies 0.682 at matched doubt on the raw base surface) survives
as a graded contributor, but on the abstention-trained TRUE checkpoint,
unmatched, familiarity alone does not separate confabs from refusals at all,
and the internal familiarity axis carries none of the boundary elevation.
What remains predictive is broader surface form. Design differences from 0037
(matched vs unmatched, raw base vs trained checkpoint, proxy sets) mean this
refines rather than contradicts the earlier mechanism. Single surface, single
seed, readout-not-causal.
