---
aliases:
- axis K resolves KNOWLEDGE-STATE, not difficulty-tracking
- disclosed D-3 difficulty gradient does not replicate on a fresh pool
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:midband-write-on-knowns-is-difficulty-blind
  type: mechanism
  status: canonical
cause: "Positive dosing at the registered 1.0x reference dose (dose_abs 12.608, hs20, erase_write) is applied to P-KNOWN, 600 never-dosed known-correct PopQA rows drawn from the qwen35_4b worldknown census and stratified 300/300 by a pre-frozen median split on PopQA retrieval-difficulty score s_pop into a rare half and a popular half."
effect: "Rare-minus-popular loss of correctness at 1.0x is -0.06 (bootstrap 95% CI [-0.137, 0.017]), short of the registered +0.10-absolute-with-CI-excluding-zero requirement for DIFFICULTY-TRACKING, so axis K resolves KNOWLEDGE-STATE: the write moves known rows at a rate independent of how hard they are to retrieve, rather than preferentially against harder-to-retrieve knowledge. This is a registered non-replication of a previously disclosed exploratory read on the M1 ladder's 133 already-dosed PopQA known rows, which showed rare-half now-wrong 0.388 versus popular-half now-wrong 0.258 at the same 1.0x rung; the same contrast on a fresh, never-dosed, roughly five-times-larger pool does not reproduce. The rare-minus-popular contrast on abstention rate runs the other direction, +0.06 (CI [0.020, 0.100]); this is reported alongside the correctness contrast but is never rounded into the axis-K verdict, per the cell's registered separation of the two readouts."
polarity: complicates
related:
- '[[write-direction-naming-battery]]'
- '[[margin-mapping]]'
relationships:
- type: supported_by
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (Axis K, KNOWLEDGE-STATE)
- type: related_to
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Prior reads that broke blinding, Disclosure D-3; the M1 row-log source of the exploratory difficulty read this arm re-tests on a fresh pool)
---

Disclosure D-3, computed before sign on the M1 ladder's already-dosed PopQA
known rows, suggested the mid-band write might preferentially corrupt harder
(rarer) known facts, a "retrieval-suppression" reading consistent with the
cell's own registered prediction (naming-table row 4, "retrieval-suppression
gradient"). Registering Arm C on a fresh, never-dosed, larger, stratified
PopQA pool was the confirmatory test of that disclosed read, and the read did
not survive: the rare/popular gap in loss-of-correctness collapses to
approximately zero (and points slightly the wrong way) with a CI that
comfortably includes zero.

This closes axis K at KNOWLEDGE-STATE rather than DIFFICULTY-TRACKING, which
independently excludes the cell's registered prediction (naming-table row 4)
regardless of what axis G or axis B resolve to. It also means the mid-band
write's cost on known-correct rows should not be described as
difficulty-indexed or retrieval-suppressing without a fresh confirmatory
result; the only fact this pool establishes about *what* the write corrupts
on knowns is the separate O-1 dissociation
([[midband-write-corrupts-known-answers-more-than-it-produces-abstention]]),
not a difficulty gradient.
