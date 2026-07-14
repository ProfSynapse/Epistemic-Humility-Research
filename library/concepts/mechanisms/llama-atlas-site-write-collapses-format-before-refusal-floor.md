---
aliases:
- Llama-3.2-3B atlas-site write fails on format collapse (RR shape F)
- llama refusal/well-formed floors are disjoint on the dose axis
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:llama-atlas-site-write-collapses-format-before-refusal-floor
  type: mechanism
  status: canonical
cause: "The doubt-gated caution write applied at Llama-3.2-3B-Instruct's own atlas-located workspace-band sites (hidden states hs20/hs22/hs23, sigma-relative dose grid {2,4,6,8,12,16,20} x sigma_c), scored on FIT against the registered dose-viability floors (fired-confab refused >= 0.60 AND well-formed >= 0.80)."
effect: "No (layer, dose) rung in the bracketed grid clears both floors simultaneously: the best refused rung (hs20 dose 16) reaches 263/576 = 0.457 (Wilson [0.416, 0.497]) but well-formed collapses to 0.700 (below the 0.80 floor) and known-correct false-refusal rises to 0.252; the best rung with well-formed intact (hs20 dose 12) reaches only 0.333 refused (well-formed 0.939). The refused and well-formed floors trend in opposite directions with dose and their admissible regions are disjoint on the continuous dose axis, so llama lands FIT dose-viability shape F (no held-out leg runs). This F is robust to detector width: crediting every hand-found abstention idiom on top of the locked 3-phrase canonical detector still reaches only 0.457 < 0.60, so the failure is a genuine format-collapse-before-refusal-floor pattern rather than an artifact of narrow phrase matching."
polarity: prevents
related:
- '[[rr-cross-family-raw-refusal]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
relationships:
- type: supported_by
  target: '[[rr-cross-family-raw-refusal]]'
  target_id: experiment:rr-cross-family-raw-refusal
  confidence: high
  evidence:
  - experiments/rr-cross-family-raw-refusal/AMENDMENT.md#outcome (llama leg)
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: high
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: medium
- type: related_to
  target: '[[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]'
  target_id: mechanism:canonical-phrase-detector-undercounts-cross-family-abstention-idioms
  confidence: medium
---

`rr-cross-family-raw-refusal` moved the doubt-gated caution write off the
ported late site and onto Llama-3.2-3B-Instruct's own atlas-located
workspace band, to test whether siting (rather than family) explained the
confirmatory's late-site non-actuation. On llama the write does produce
dose-monotone abstention pressure, but the refusal floor and the
well-formed floor never clear together anywhere on the bracketed grid: the
dose at which refusal is high enough breaks JSON format, and the dose at
which format is intact does not refuse enough. Hand-crediting every
abstention idiom the locked canonical detector misses still leaves this
family under the refusal floor, so the failure is not a detector-width
artifact, unlike the sibling mistral leg
([[canonical-phrase-detector-undercounts-cross-family-abstention-idioms]]).
