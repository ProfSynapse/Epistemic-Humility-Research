---
aliases:
- doubt-axis norm/position confound at the final-prompt-token anchor
- random-direction control on the refused-vs-known contrast
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:refused-vs-known-contrast-carries-norm-position-confound
  type: mechanism
  status: canonical
cause: "At the final-prompt-token anchor position, the refused-vs-known (doubt) contrast is not cleanly axis-specific: in jspace-family-atlas's post-hoc random-direction diagnostic, a FIXED random direction reaches up to 0.97 best-orientation AUROC on this contrast at some layers in both Llama-3.2-3B-Instruct and Mistral-7B-Instruct-v0.3, replicating the elevated reading the doubt-snap-cross-family-confirmatory fleet audit found on the same contrast (0.997-1.000 raw AUROC at the ported late layer) across every family in that panel."
effect: "Held-out AUROC on the known-vs-refused doubt axis at this anchor must be read against its own layer's random-direction control value, not against the 0.5 chance baseline, because a large share of its apparent separability is a norm/position artifact rather than a doubt-specific direction. The caution (refused-vs-confab) and raw-refusal (refused-vs-answered) axes did not show this confound in the same diagnostic (random-direction control stayed ~0.5-0.75 at every layer), so the confound is specific to the refused-vs-known contrast, not anchor-wide."
polarity: complicates
related:
- '[[jspace-family-atlas]]'
- '[[doubt-snap-cross-family-confirmatory]]'
- '[[known-unknown-direction]]'
- '[[refusal-direction]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
  - experiments/jspace-family-atlas/analysis-committed/random_direction_control.json
- type: related_to
  target: '[[doubt-snap-cross-family-confirmatory]]'
  target_id: experiment:doubt-snap-cross-family-confirmatory
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md (Motivation and posture, fleet audit finding)
- type: related_to
  target: '[[known-unknown-direction]]'
  target_id: term:known-unknown-direction
  confidence: medium
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

A post-hoc audit of the doubt-snap fleet's committed captures had already
flagged that the refusal-vs-answering axis reads near-ceiling (0.997-1.000)
in every family at the ported layer, well above what a doubt-specific
direction alone should produce. `jspace-family-atlas` ran a fixed
random-direction control at every layer of its own capture and found the same
pattern on the refused-vs-known contrast specifically: a random direction,
oriented for best separation, reaches up to 0.97 AUROC at some layers in both
mapped families. The caution and raw-refusal axes, scored against the same
control, stayed near chance (~0.5-0.75), so the confound does not generalize
to every contrast at this anchor, only to the one comparing refused rows
against known-correct rows.

The practical read: this project's doubt-axis AUROC numbers at the
final-prompt-token anchor overstate how much of their separability is a
doubt-specific readout versus activation norm or token-position artifacts
shared by the two populations. Any future report of a doubt-axis AUROC at
this anchor should carry its own layer's random-direction control alongside
it rather than compare to 0.5, and any actuation design that treats a strong
doubt-axis AUROC as license to write on that direction should first check
whether the same layer's control is also elevated.
