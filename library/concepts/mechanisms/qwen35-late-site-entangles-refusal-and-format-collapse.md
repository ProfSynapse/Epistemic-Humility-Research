---
aliases:
- refusal induction entangled with JSON well-formedness collapse (Qwen3.5 late site)
- doubt-snap late-site no-window null on Qwen3.5
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:qwen35-late-site-entangles-refusal-and-format-collapse
  type: mechanism
  status: canonical
cause: "On Qwen/Qwen3.5-4B and Qwen/Qwen3.5-9B (bf16, hybrid linear-attention architecture), applying the doubt-gated caution erase-write snap at the registered late write site (model-local depth fraction round(0.94*(num_hidden_layers-1)), the hs30/hs34-equivalent site) at any dose on the FIT-only sweep."
effect: "Confab refusal/coherent-actuation content and JSON well-formedness move together rather than separately: on Qwen3.5-4B (recalibrated dose grid 10-75), coherent tighten rises 2.8% -> 9.0% -> 17.3% -> 32.6% across doses 10-40 while well-formedness stays high, then well-formedness collapses 90% -> 55% -> 3% across doses 40/50/60 and tighten falls to 10.8% / 0% / 0%, peaking at only ~33% far below the registered 60% bar; on Qwen3.5-9B (recalibrated grid 60-140) tighten rises only 0.4% -> 5.8% before the same well-formedness cliff already seen at 200/250 on the original grid. No dose on either the registered {100,150,200,250} grid or the recalibrated per-cell grids clears both the 60% refusal/clean_tighten bar and an 80% well-formed bar at once, so both cells fail the G0 dose-viability gate before held-out scoring."
polarity: prevents
related:
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[qwen35-4b-midband-doubt-snap]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
relationships:
- type: supported_by
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: high
  evidence:
  - experiments/doubt-snap-cross-family-confirmatory/NOTEBOOK.md (2026-07-09 and 2026-07-10 entries)
  - experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md (dose-recalibration note)
- type: tested_by
  target: '[[qwen35-4b-midband-doubt-snap]]'
  target_id: experiment:qwen35-4b-midband-doubt-snap
  confidence: medium
  evidence:
  - experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md#falsifier
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
- type: related_to
  target: '[[steering-dose-windows-are-absolute-not-sigma-transferable]]'
  target_id: mechanism:steering-dose-windows-are-absolute-not-sigma-transferable
  confidence: medium
---

At the registered late write site on Qwen3.5, refusal induction and output
well-formedness are not independently controllable by dose: every setpoint
that raises confab refusal content also degrades JSON structure, and the two
curves cross well below the thresholds the doubt-gated caution snap needs to
register a viable operating window. Both Qwen3.5 cells in
`doubt-snap-cross-family-confirmatory` failed dose viability (G0) on this
basis, not on an absence of gate discrimination (FIT AUC was high on both).

The open question this entanglement raises is whether it is a property of the
late write site specifically or of the caution direction and mechanism on
this substrate more broadly. `qwen35-4b-midband-doubt-snap` tests exactly
that, by moving the write to a J-space workspace-band layer on the same model
and checking whether refusal and well-formedness decouple there; as of this
writing that test has not resolved.
