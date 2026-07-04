---
aliases:
- Internal doubt degrades fabrication specificity
- doubt that fails to trigger refusal still shortens and blurs the confabulation
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:internal-doubt-degrades-fabrication-specificity
  type: mechanism
  status: canonical
cause: "Higher pre-generation doubt-trunk projection on questions where the model nevertheless commits to answering an unanswerable question."
effect: "The resulting fabrication is shorter and less specific (within-flavor Spearman rho -0.21 to -0.24 for specificity, permutation p=0.001, and -0.27 for length): the doubt that failed to stop the answer still degrades it. Hedging, by contrast, is question-driven, not state-driven (activation probe 0.674 fails its TF-IDF question guard at 0.642)."
polarity: decreases
related:
- '[[internal-confab-mechanics--cpu-fleet]]'
- '[[pre-generation-commitment-signal-predicts-confabulation]]'
- '[[known-unknown-direction]]'
- '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
relationships:
- type: supported_by
  target: '[[internal-confab-mechanics--cpu-fleet]]'
  target_id: paper:internal-confab-mechanics
  confidence: high
- type: related_to
  target: '[[pre-generation-commitment-signal-predicts-confabulation]]'
  target_id: mechanism:pre-generation-commitment-signal-predicts-confabulation
  confidence: high
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
- type: related_to
  target: '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
  target_id: mechanism:hidden-state-linearly-encodes-unanswerability-despite-hallucination
  confidence: medium
---

Session-0037 arm A (analysis/mi_confab_phenotypes_20260704/), on 309 baseline
confabulations with a 100 percent activation-cache join. Confabulations are long and
generic (about 50 words, low fact density) where correct answers are terse and dense
(about 11 words); within that phenotype, the graded doubt reading predicts how
specific the fabrication dares to be. Supporting behavioral contrast: a doubt prime
produced 0 confabulations in 324 generations while a certainty prime raised the
confab count (459 vs 309 baseline) and their length but not per-confab texture.
Instrument caveat: the raw trunk projection and the frozen probe score disagree on
the sign of the length coupling, so the two readouts are not interchangeable. Regex
phenotype labels; single surface; correlational.
