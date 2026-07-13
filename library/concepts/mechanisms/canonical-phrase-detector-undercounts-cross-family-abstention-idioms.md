---
aliases:
- exact-phrase refusal detector undercounts cross-family abstention idioms
- detector narrowness as a validity threat in cross-family abstention measurement
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  type: mechanism
  status: canonical
cause: "A canonical refusal/abstention detector whose phrase vocabulary was calibrated on one model family (here, a locked 3-phrase set: \"i do not know\", \"i don't know\", \"^abstain\") is applied unchanged to a different family's generations to grade fired-confab abstention rate."
effect: "On Mistral-7B-Instruct-v0.3, hand-reading 366 non-refused fired-confab generations at the peak dose rung found 97 well-formed clear-abstention idioms phrased entirely outside the locked 3-phrase set (e.g. \"it is impossible to predict...\", \"it is uncertain whether...\", \"I cannot determine...\"), enough that crediting them moves the family's gate reading from a 2.1-point miss (0.5793 vs the 0.60 floor) to a pass (0.679-0.701). The same locked detector, held fixed, produced a failure on Llama-3.2-3B-Instruct that stayed robust to the same width-crediting exercise (credited peak still only 0.457 < 0.60), showing the undercount is family-specific rather than a uniform correction that would apply everywhere the detector is used."
polarity: decreases
related:
- '[[rr-cross-family-raw-refusal]]'
- '[[mistral-atlas-site-write-abstains-below-canonical-detector-floor]]'
- '[[llama-atlas-site-write-collapses-format-before-refusal-floor]]'
- '[[abstention]]'
relationships:
- type: supported_by
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (mistral leg binding caveat)
- type: related_to
  target: '[[mistral-atlas-site-write-abstains-below-canonical-detector-floor]]'
  target_id: mechanism:mistral-atlas-site-write-abstains-below-canonical-detector-floor
  confidence: high
- type: related_to
  target: '[[llama-atlas-site-write-collapses-format-before-refusal-floor]]'
  target_id: mechanism:llama-atlas-site-write-collapses-format-before-refusal-floor
  confidence: medium
- type: related_to
  target: '[[abstention]]'
  target_id: term:abstention
  confidence: medium
---

A durable methods finding from `rr-cross-family-raw-refusal`: an
exact-phrase refusal/abstention detector calibrated on one model family's
idiom does not generalize its coverage to another family, and the miss is
large enough to flip a gate verdict. The finding is established by contrast
across the experiment's two legs, both instrument-verified: mistral's
FIT dose-viability miss is substantially a canonical-phrase-coverage gap
(hand-crediting idioms clears the floor), while llama's miss on the same
locked detector is robust to the same width-crediting exercise (format
collapses before the refusal floor regardless of phrase coverage). This
shows the undercount is a family-specific validity threat to be checked per
family, not evidence that widening the detector would rescue every
cross-family non-actuation result.
