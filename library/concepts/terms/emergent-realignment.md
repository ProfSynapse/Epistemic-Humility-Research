---
aliases:
- re-alignment
- benign re-fine-tuning
- Emergent Re-alignment
tags:
- kg/term
- concept
- term
kg:
  id: term:emergent-realignment
  type: term
  status: canonical
area: training-dynamics
related:
- '[[2506.19823--persona-features-control-emergent-misalignment]]'
- '[[emergent-misalignment]]'
relationships:
- type: proposed_by
  target: '[[2506.19823--persona-features-control-emergent-misalignment]]'
  target_id: paper:2506.19823
  confidence: high
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
---

Emergent realignment is the finding that behavioral misalignment generalizes symmetrically: just as narrow harmful fine-tuning causes broad misalignment, narrow benign fine-tuning (as few as approximately 120 samples and 35 gradient steps) fully suppresses that broad misalignment. The suppression works whether the benign data is drawn from the same task distribution as the original harmful behavior or from a completely different domain, indicating that the alignment signal generalizes in both directions along the same axis.

**Why it matters here:** Epistemic humility research needs to know whether post-training behavioral traits are stable or fragile; the symmetry of emergence and realignment implies that targeted small interventions can correct overconfident or miscalibrated output patterns, which informs the design of abstention and calibration training regimens.

**Lineage:** related to [[emergent-misalignment]], which describes the harmful direction of the same generalization phenomenon; [[persona-vectors]] provide a geometry-grounded way to track both directions.
