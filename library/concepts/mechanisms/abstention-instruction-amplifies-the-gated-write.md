---
title: abstention-instruction-amplifies-the-gated-write
aliases:
- the abstention instruction amplifies but does not enable the gated write
- gated write survives without the abstention instruction, attenuated
- instruction-amplified actuation
tags:
- kg/mechanism
- concept
- mechanism
- actuation
kg:
  id: mechanism:abstention-instruction-amplifies-the-gated-write
  type: mechanism
  status: canonical
cause: "An abstention-permitting system-prompt sentence (which also seeds the literal refusal string the narrow grader matches) is present in context alongside the doubt-gated mid-band activation write, versus the identical write under a prompt carrying only the JSON output contract (experiments/no-abstention-prompt-gated-replication, all five registered families at their frozen operating points, two-stage wide-instrument grading with the detector threshold refit under the new prompt)."
effect: "The write produces a real, direction-specific two-stage abstention lift with no abstention instruction in context in every family (qwen3-4b +11.4pp 95% CI [7.0, 16.7]; llama +9.3pp [6.7, 12.0]; mistral +18.8pp [15.8, 21.8]; qwen3.5-4b +45.6pp [42.4, 48.6]; gemma +47.0pp [37.1, 55.5]; known-correct cost near zero everywhere; random-direction controls at or below no_op), and the instruction amplifies it: qwen3-4b reaches only 12.7% of its with-prompt lift magnitude, llama roughly 13% of its own, while gemma and qwen3.5-4b retain most of theirs. The amplification is family-dependent and does not track the with-prompt effect ordering. Two corollaries: without the seeded phrase, qwen3-4b's abstentions are invisible to the string detector (0 of 21 judged abstentions caught) while qwen3.5-4b emits overt refusal strings unprompted (516/1332 at the string stage); and the write installs a measurable internal doubt state even where no abstention text appears, collapsing stated response_confidence direction-specifically in every family."
polarity: increases
related:
- '[[no-abstention-prompt-gated-replication]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[known-unknown-direction]]'
- '[[detector-v2-overfires-on-random-arm-text]]'
relationships:
- type: supported_by
  target: '[[no-abstention-prompt-gated-replication]]'
  target_id: experiment:no-abstention-prompt-gated-replication
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md#outcome
    (Verdict, Gates G1/G1b/G3/G4, Descriptive findings 1-2 and 4)
- type: related_to
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: high
  evidence:
  - experiments/prompt-vs-training-panel/AMENDMENT.md#outcome (the
    instruction alone is a near-ceiling actuator on the untrained base,
    90.89% vs 0.00%; this mechanism and that one jointly bound the
    instruction's and the write's separate contributions)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: high
  evidence:
  - experiments/no-abstention-prompt-gated-replication/AMENDMENT.md (Design;
    the gate is the frozen doubt-direction detector, threshold refit under
    the new prompt on the FIT split only)
---

# The abstention instruction amplifies, but does not enable, the gated write

The sharpest reading of the no-abstention-prompt replication: the mid-band
doubt-gated write is a genuine actuator on its own, in every family tested,
and the abstention instruction is an amplifier whose gain varies strongly by
family. Neither the write-only nor the instruction-only channel accounts for
the combined with-prompt effect; they share the work.

Alongside [[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]
(instruction alone: 90.89% on the untrained base), this brackets the
actuation picture for paper 5: presence of the instruction is a near-ceiling
actuator by itself, the write is a real but family-heterogeneous actuator by
itself, and the with-prompt gated numbers reported in the confirmatory
surfaces measure their combination, now disclosed as such.
