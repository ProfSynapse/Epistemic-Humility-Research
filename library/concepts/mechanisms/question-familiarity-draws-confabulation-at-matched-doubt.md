---
aliases:
- Question familiarity draws confabulation at matched doubt
- familiar-looking unanswerable questions are the ones the model fabricates on
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:question-familiarity-draws-confabulation-at-matched-doubt
  type: mechanism
  status: canonical
cause: "Higher surface familiarity of an unanswerable question (corpus-internal token frequency and neighbor proxies), with internal doubt level held fixed by caution-distance matching."
effect: "The familiar-looking question is the one that draws a confabulation rather than a refusal (joint familiarity proxies predict confab-vs-refuse at 0.682, permutation p=0.0099, on caution-matched pairs): the entity-recognition account of hallucination gating reproduces on this surface as a graded pull toward answering."
polarity: increases
related:
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
- '[[entity-recognition-direction]]'
- '[[unfamiliar-ft-examples-drive-hallucination-character]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
relationships:
- type: supported_by
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction-gates-refusal-vs-hallucination]]'
  target_id: mechanism:entity-recognition-direction-gates-refusal-vs-hallucination
  confidence: high
- type: related_to
  target: '[[entity-recognition-direction]]'
  target_id: term:entity-recognition-direction
  confidence: high
- type: related_to
  target: '[[unfamiliar-ft-examples-drive-hallucination-character]]'
  target_id: mechanism:unfamiliar-ft-examples-drive-hallucination-character
  confidence: medium
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
---

Session-0037 arm B (analysis/mi_confab_signature_20260704/). At matched caution
distance and matched unanswerability flavor, text-level familiarity proxies alone
predict which of two equally-doubted questions gets a fabricated answer. The
familiarity features explain part but not all of the commitment signal (activation
probe 0.834 beats them by +0.152 on paired folds), so familiarity is a contributor
to the pre-generation commitment state rather than the whole of it. The frozen
knowledge probe was largely null on the same contrast, separating familiarity from
parametric knowledge. Proxies are corpus-internal, not web frequencies; single
surface; correlational.
