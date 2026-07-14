---
aliases:
- Mistral-7B atlas-site write peaks just under the refusal floor (RR shape F)
- mistral 0.5793 vs 0.60 floor, format- and cost-clean
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:mistral-atlas-site-write-abstains-below-canonical-detector-floor
  type: mechanism
  status: canonical
cause: "The doubt-gated caution write applied at Mistral-7B-Instruct-v0.3's own atlas-located workspace-band sites (hidden states hs15/hs16/hs17, sigma-relative dose grid {2,4,6,8,12,16,20} x sigma_c), scored on FIT against the same dose-viability floors and graded with the locked 3-phrase canonical refusal detector (\"i do not know\", \"i don't know\", \"^abstain\")."
effect: "The peak rung (hs16 dose 12) reaches fired-confab refused 504/870 = 0.5793 (Wilson [0.546, 0.612]) against the 0.60 floor, a 2.1-point miss, with well-formed 850/870 = 0.977 and known-correct false-refusal 6/255 = 0.024 (Wilson upper bound 0.050) both clean; refused never reaches 0.60 anywhere on the 21-rung grid, with near-symmetric turnover either side of the peak, so no interpolation rescues a viable point and mistral lands FIT dose-viability shape F. Unlike llama, this miss is NOT robust to detector width: hand-reading all 366 non-refused fired confabs at the peak rung found 97 well-formed clear-abstention idioms phrased outside the locked detector's vocabulary (e.g. \"it is impossible to predict...\", \"it is uncertain whether...\"), and crediting them raises the peak to 0.679-0.701, clearing the 0.60 floor with JSON intact."
polarity: prevents
related:
- '[[rr-cross-family-raw-refusal]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
relationships:
- type: supported_by
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (mistral leg)
- type: related_to
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: high
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: medium
---

On Mistral-7B-Instruct-v0.3, the doubt-gated caution write at its own
atlas-located site produces dose-monotone, well-formed, cost-clean
abstention pressure that peaks just short of the registered refusal floor
(0.5793 against 0.60) and stays under it at every rung, so the gate verdict
is a clean shape F. The gap between the locked-detector reading and a
hand-verified reading is large: 97 well-formed abstention generations at
the peak rung are phrased entirely outside the locked canonical-phrase
detector's vocabulary, and crediting them would clear the floor. The gate
verdict is unchanged (the locked detector decides), but the miss is
recorded as substantially a canonical-phrase-coverage limitation of the
locked instrument's grader on this family, not an absence of abstention
pressure, unlike the format-collapse failure on llama
([[llama-atlas-site-write-collapses-format-before-refusal-floor]]).
