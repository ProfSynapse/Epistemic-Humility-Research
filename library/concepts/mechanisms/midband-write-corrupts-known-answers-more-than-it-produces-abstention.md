---
aliases:
- override O-1 fires on a fresh pool (6.37:1)
- silent-wrongness dissociation generalizes beyond the M1 rows
- answer-corrupting override condition
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:midband-write-corrupts-known-answers-more-than-it-produces-abstention
  type: mechanism
  status: canonical
cause: "Positive dosing at the registered 1.0x reference-dose setpoint (dose_abs 12.608, hs20, erase_write) is applied to P-KNOWN, the same 600-row never-dosed known-correct PopQA pool used to resolve axis K, and known-row loss of correctness is compared against known-row abstention on the same rows."
effect: "Known-row loss of correctness at 1.0x is 0.403 against known-row abstention of 0.063, a ratio of 6.37, well above the cell's registered factor-3 override-O-1 threshold. This generalizes a previously disclosed exploratory dissociation (disclosure D-2, measured on the M1 ladder's already-dosed rows, where ungated dosing at the 1.0x rung destroyed about 31 points of known-correct accuracy while converting under 7 points to abstention) to a fresh, never-dosed, larger population: at this operating point the write's dominant cost on known-correct rows is silent wrongness, unmarked substitutions and confident false detail, not conversion to a marked refusal. Per the cell's registered rule, any naming-table row assembled with 'abstention' in its name would require an 'answer-corrupting' prefix; because axis G is separately instrument-void and axis K separately resolves KNOWLEDGE-STATE rather than the predicted DIFFICULTY-TRACKING, no naming-table row is in fact assembled from this cell, so O-1 fires as a standalone, generalized finding with no name left to prefix."
polarity: decouples
related:
- '[[write-direction-naming-battery]]'
- '[[margin-mapping]]'
- '[[ungated-vs-gated-dose-matched]]'
relationships:
- type: supported_by
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md#outcome (O-1's numeric condition fires; known-row loss of correctness 0.403 vs known-row abstention 0.063, ratio 6.37)
- type: related_to
  target: '[[margin-mapping]]'
  target_id: experiment:margin-mapping
  confidence: high
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Prior reads that broke blinding, Disclosure D-2; the M1 row-log source of the exploratory dissociation this arm confirms on a fresh pool)
- type: related_to
  target: '[[ungated-vs-gated-dose-matched]]'
  target_id: experiment:ungated-vs-gated-dose-matched
  confidence: medium
  evidence:
  - experiments/write-direction-naming-battery/AMENDMENT.md (Prior reads that broke blinding, Disclosure D-2; contrasts this dissociation with the opposite decomposition ungated-vs-gated-dose-matched found at the Qwen3-4B/L34 overdrive operating point, 55.8pp false refusal versus 3.9pp answered-wrong)
---

At the Qwen3.5-4B hs20 mid-band operating point, dosing a known-correct row
along the frozen c_hat direction is roughly six times more likely to leave a
silently wrong answer than to produce a marked abstention. This was first
noticed as an unregistered, blinding-breaking observation on the M1 ladder's
own already-dosed rows (disclosure D-2) and is confirmed here as a genuine
property of the write, not an artifact of that particular row set: on a
fresh, never-dosed, larger pool the ratio is 6.37:1, comfortably above the
cell's pre-registered factor-3 override threshold.

This is the opposite decomposition from what `ungated-vs-gated-dose-matched`
found at the Qwen3-4B raw-base, late-site (L34), dose-200 overdrive operating
point, where ungated dosing produced 55.8 points of false refusal against
only 3.9 points of answered-wrong. The two results are not in tension; they
show the write's cost profile on knowns, like its content-selectivity
([[caution-write-selectivity-is-content-dependent-not-gate-created]]), is
operating-point-dependent. At the mid-band setpoint that carries this
program's held-out abstention claim, the write's dominant failure mode on
knowledge it should have left alone is silent corruption of the answer, not
over-refusal, a fact that constrains any future name for this write and rules
out describing it as safely conservative on knowns at this dose.
