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
cause: "At the final-prompt-token anchor position, the refused-vs-known (doubt) contrast is not cleanly axis-specific: in jspace-family-atlas's post-hoc random-direction diagnostic, a FIXED random direction reaches up to 0.97 best-orientation AUROC on this contrast at some layers in both Llama-3.2-3B-Instruct and Mistral-7B-Instruct-v0.3, replicating the elevated reading the doubt-snap-cross-family-confirmatory fleet audit found on the same contrast (0.997-1.000 raw AUROC at the ported late layer) across every family in that panel. gemma-4-e4b-family-atlas re-ran the same diagnostic over all 43 layers on Gemma-4-E4B-it and found the confound is not confined to the doubt contrast there: the random-direction control, scored max-over-contrasts (doubt, caution, and raw refusal together), is elevated and spiky through much of the mid-band (0.83-0.97 at hs_index 10-12, 24, and 28-34, 0.89 at hs_index 42) while staying near chance at hs_index 0-8, 14-18, and 36-40. qwen3-4b-family-atlas found the same doubt-axis confound a fourth time, back in an axis-specific shape: its `ref_vs_known` control spikes to 0.87-0.98 at hs 21/24/32/36 while the caution (`ref_vs_confab`, <= 0.79 everywhere) and raw_refusal (`ref_vs_answered`, mostly <= 0.72, one spike to 0.829 at hs24) controls stay clean."
effect: "Held-out AUROC on the known-vs-refused doubt axis at this anchor must be read against its own layer's random-direction control value, not against the 0.5 chance baseline, because a large share of its apparent separability is a norm/position artifact rather than a doubt-specific direction. On Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3, and raw-base Qwen3-4B the caution (refused-vs-confab) and raw-refusal (refused-vs-answered) axes did not show this confound in the same diagnostic (random-direction control stayed near chance at almost every layer), so on those three families the confound was specific to the refused-vs-known contrast, not anchor-wide. On Gemma-4-E4B-it the confound generalizes across axes but stays layer-patchy: it does not track one contrast, it tracks specific layers (elevated at hs10-12/24/28-34/42, near chance at hs0-8/14-18/36-40), so any AUROC reported at this anchor on ANY axis should carry its own layer's random-direction control, and actuation-layer choice should prefer layers where the control is near chance for all axes simultaneously (hs14-18, hs36-40 on gemma-4-e4b) over the naive best-AUROC layer."
polarity: complicates
related:
- '[[jspace-family-atlas]]'
- '[[gemma-4-e4b-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
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
- type: supported_by
  target: '[[gemma-4-e4b-family-atlas]]'
  target_id: experiment:gemma-4-e4b-family-atlas
  confidence: medium
  evidence:
  - experiments/gemma-4-e4b-family-atlas/AMENDMENT.md#outcome (random-direction control re-derivation)
- type: supported_by
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: medium
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome (doubt-axis ref_vs_known control)
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

`gemma-4-e4b-family-atlas` re-ran the same control over the full 43-layer
depth on a third, structurally distinct family and found the confound
persists but changes shape: rather than singling out the refused-vs-known
contrast, the elevated control on Gemma-4-E4B-it moves with layer, spiking
across several axes at once in patches of the mid-band (hs10-12, hs24,
hs28-34, hs42) while sitting near chance elsewhere (hs0-8, hs14-18, hs36-40).
That makes the naive best-per-axis layers on this family (the ones with the
single highest raw AUROC per axis) exactly the ones where the control is also
elevated, so the diagnostic's practical use generalizes from "check the
doubt axis's own layer" to "check every axis's own layer, and prefer a layer
where the control is near chance for all of them at once."

`qwen3-4b-family-atlas` then ran the same control on raw-base Qwen3-4B and
found the confound back in its original, axis-specific shape: the doubt
axis's `ref_vs_known` control spikes to 0.87-0.98 at hs 21/24/32/36, while
caution's `ref_vs_confab` control stays <= 0.79 everywhere and raw_refusal's
`ref_vs_answered` control stays mostly <= 0.72 (one spike to 0.829 at hs24).
Four of four mapped families now show this confound on the doubt axis; three
of the four (llama, mistral, qwen3-4b) confine it to that one contrast, and
one (gemma-4-e4b) generalizes it across axes by layer, so the confound
itself is robust but its scope (single-axis versus cross-axis) still varies
by family.
