---
aliases:
- workspace-band mismatch account of actuation fragility
- J-space actuation bridge
- write-to-workspace hypothesis
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:j-space-mediated-actuation-fragility
  type: mechanism
  status: canonical
cause: "Epistemic residual directions are read from or written at sites outside the model's workspace-like J-space band; in Qwen3-4B, L34/hs34 sits after the hs=23-29 J-lens effective-dimensionality peak."
effect: "Readout directions remain portable while late-layer residual-stream actuation is fragile, null, or collapse-prone because the write may miss the broadcast workspace channel."
polarity: explains
related:
- '[[j-space-localization-qwen3-4b]]'
- '[[j-space-midband-dose-calibration-qwen3-4b]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[j-space-token-targeted-refusal-qwen3-4b]]'
- '[[jspace-family-atlas]]'
- '[[qwen3-4b-family-atlas]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
- '[[global-workspace]]'
- '[[jacobian-lens]]'
- '[[activation-addition]]'
- '[[steering-vector]]'
- '[[residual-stream]]'
relationships:
- type: supported_by
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: medium
  evidence:
  - experiments/j-space-localization-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/profile_full.json
- type: tested_by
  target: '[[jspace-family-atlas]]'
  target_id: experiment:jspace-family-atlas
  confidence: low
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
- type: tested_by
  target: '[[qwen3-4b-family-atlas]]'
  target_id: experiment:qwen3-4b-family-atlas
  confidence: low
  evidence:
  - experiments/qwen3-4b-family-atlas/AMENDMENT.md#outcome
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: medium
  evidence:
  - experiments/jspace-family-atlas/AMENDMENT.md#outcome
- type: supported_by
  target: '[[j-space-midband-dose-calibration-qwen3-4b]]'
  target_id: experiment:j-space-midband-dose-calibration-qwen3-4b
  confidence: medium
  evidence:
  - experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json
- type: supported_by
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: medium
  evidence:
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-calibrated-layer-contrast-qwen3-4b/analysis-committed/full_summary.json
- type: supported_by
  target: '[[j-space-token-targeted-refusal-qwen3-4b]]'
  target_id: experiment:j-space-token-targeted-refusal-qwen3-4b
  confidence: low
  evidence:
  - experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md#outcome
  - experiments/j-space-token-targeted-refusal-qwen3-4b/analysis-committed/full_summary.json
- type: supported_by
  target: '[[tc-2026-workspace--verbalizable-representations-global-workspace]]'
  target_id: paper:tc-2026-workspace
  confidence: medium
  evidence:
  - library/notes/tc-2026-workspace--verbalizable-representations-global-workspace.md#summary
- type: related_to
  target: '[[global-workspace]]'
  target_id: term:global-workspace
  confidence: high
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
- type: related_to
  target: '[[activation-addition]]'
  target_id: method:activation-addition
  confidence: medium
- type: related_to
  target: '[[steering-vector]]'
  target_id: term:steering-vector
  confidence: medium
- type: related_to
  target: '[[residual-stream]]'
  target_id: term:residual-stream
  confidence: medium
---

The J-space mediated actuation-fragility mechanism is a proposed explanation
for this project line's repeated split between strong epistemic readouts and
fragile behavior writes. The external workspace result argues that only the
J-space component of a concept is privileged for report and downstream use. The
local Qwen3-4B J-lens characterization then found that this project's existing
L34 write site maps to hs=34, just after the hs=23-29 workspace-like
effective-dimensionality band and its hs=26 peak.

Under this mechanism, a direction can be linearly readable from the residual
stream without being a good causal write vector at the chosen layer. The
direction may be downstream of the broadcast workspace, outside the reportable
component of the concept, or mixed with late output-preparation features. That
would make late residual writes narrow, brittle, or collapse-prone even when the
same vector is a strong readout.

This is still a surface-local exploratory mechanism, not a cross-family
confirmatory claim. The local evidence now has three pieces: the J-lens smoke
passed, caution directions verbalized as self/absence/error/impossibility, and
L34 localized after the workspace-like peak; FIT-only dose calibration showed
that hs23/hs26 collapse at dose 200 is recoverable with lower layer-specific
setpoints; and the held-out calibrated contrast found hs23 beating hs34
clean_tighten by 22.7 percentage points with only +0.78 percentage points
known-correct cost. That is the first causal support for the layer-site account
on raw-base Qwen3-4B bf16.

The first token-targeted successor constrains the mechanism rather than
overturning it: a J-lens backward direction aimed at observed refusal/absence
tokens wrote accurately and was non-inert by itself, but it added only +0.54
percentage points over the already strong hs23 `c_hat` snap. Natural token-target
composition is therefore not enough, on this surface, to improve the actuator
once the workspace-band caution write is active.

The first cross-family test of the depth-fraction picture, `jspace-family-atlas`,
complicated rather than confirmed it: on Llama-3.2-3B-Instruct and
Mistral-7B-Instruct-v0.3, a representation-variance effective-dimension
profile peaks early-exterior (0.09-0.14 depth) rather than at an interior
band, so the workspace-like peak itself does not sit at a shared portable
depth fraction across families ([[workspace-band-peak-location-is-family-relative]]).
The read panel still found an interior band where doubt, caution, and raw
refusal all clear 0.80 held-out AUROC together (llama layers 15-23, mistral
7-27), so a family-relative layer map exists even though the profile's own
shape does not match the Qwen3-4B picture. The mechanism still needs
replication beyond raw-base Qwen3-4B before it should be treated as general.

`qwen3-4b-family-atlas` closes that replication gap directly, by running the
same representation-variance `eff_dim_frac` profile on this mechanism's own
founding substrate, raw-base Qwen3-4B. The profile peaks early-exterior at
hs5 (0.139 depth), not at the hs23-29 J-lens band this mechanism was built
from; the interior read band it does find (hs22-36, all three axes) sits on
top of the J-lens peak instead. That keeps the write/read-site-mismatch
account intact (L34/hs34 still sits after the readable interior band) while
adding a second, independent confirmation that the J-lens's effective-
dimensionality peak and this participation-ratio profile's peak are not the
same signal on this substrate: readability and this profile's notion of
dimensionality dissociate even when measured on the identical checkpoint.
