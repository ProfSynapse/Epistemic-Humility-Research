---
aliases:
- Training reshapes the J-lens interior workspace band
- trained-checkpoint J-lens profile suppresses and deepens the raw-base peak
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:training-flattens-and-deepens-jlens-workspace-band
  type: mechanism
  status: canonical
cause: "SFT + GRPO-v2 training (clean_sft_grpo_v2_seed1 lineage) applied on top of raw-base Qwen3-4B, measured by re-running the identical J-lens effective-dimensionality profile protocol (same corpus manifest, seed 20260707, 5 random directions, the same 13-point depth grid hs[2,5,8,11,14,17,20,23,26,29,32,35,36]) used for the raw-base characterization in j-space-localization-qwen3-4b."
effect: "The interior workspace-like band survives training but only narrowly and reshaped: interior max effective_dim_frac_mean is 0.00735 at hs29, just above the 1.5x-early-median presence threshold of 0.00675. Raw-base's hs26 peak (0.01057) is suppressed about 35% at the same index post-training (0.00694), and the band flattens and shifts deeper, with the new peak at hs29 instead of hs26. Full per-point profile: hs2 0.00448, hs5 0.00471, hs8 0.00350, hs11 0.00451, hs14 0.00348, hs17 0.00443, hs20 0.00512, hs23 0.00662, hs26 0.00694, hs29 0.00735, hs32 0.00611, hs35 0.00234, hs36 0.00100. First J-lens measurement taken on any trained checkpoint in the program."
polarity: modulates
related:
- '[[jlens-trained-checkpoint-midband-ablation]]'
- '[[j-space-localization-qwen3-4b]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[workspace-band-peak-location-is-family-relative]]'
- '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
- '[[jacobian-lens]]'
relationships:
- type: supported_by
  target: '[[jlens-trained-checkpoint-midband-ablation]]'
  target_id: experiment:jlens-trained-checkpoint-midband-ablation
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome (profile P1: interior band present but narrowly, hs26 peak suppressed ~35%, band flattened and deepened, new peak hs29)"
- type: related_to
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: high
  evidence:
  - "the raw-base source profile this mechanism's comparison is anchored to (hs23-29 band, hs26 peak 0.01057)"
- type: related_to
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: medium
  evidence:
  - "the workspace-band account this profile change qualifies: the band this mechanism was built from is not fixed by architecture alone, it also moves under training"
- type: related_to
  target: '[[workspace-band-peak-location-is-family-relative]]'
  target_id: mechanism:workspace-band-peak-location-is-family-relative
  confidence: medium
  evidence:
  - "parallel non-portability finding along a different axis: that mechanism shows the band's depth is not portable across model families, this mechanism shows it is not even stable across training on the SAME family and checkpoint lineage"
- type: related_to
  target: '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
  target_id: mechanism:refusal-axis-readable-but-not-ablatable-at-midband
  confidence: medium
  evidence:
  - "same cell's companion finding: the rule-selected ablation site sits inside this reshaped band"
- type: related_to
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
---

Registered exploratory finding, resolved 2026-08-16, and the first J-lens
effective-dimensionality profile ever run on a trained checkpoint in this
program (every prior J-lens result is raw-base Qwen3-4B only). Training
(`clean_sft_grpo_v2_seed1`, SFT + GRPO-v2 seed 1) does not remove the interior
workspace-like band [[j-space-localization-qwen3-4b]] found on raw-base
Qwen3-4B, but it narrows and reshapes it: the interior maximum
(effective_dim_frac_mean 0.00735 at hs29) clears the pre-registered presence
threshold only narrowly, the raw-base hs26 peak (0.01057) is suppressed about
35% at the same index (0.00694), and the band's peak itself moves three grid
points deeper, from hs26 to hs29.

**Why it matters here:** this is a same-family, same-checkpoint-lineage
instance of the band's depth and magnitude proving unstable, not just
non-portable across families ([[workspace-band-peak-location-is-family-relative]]
established the cross-family version). It means a J-lens band characterized
once on a raw-base checkpoint cannot be assumed to hold, in either magnitude
or exact depth, after the checkpoint is trained. The rule-selected ablation
site in this cell's companion finding
([[refusal-axis-readable-but-not-ablatable-at-midband]]) sits inside this
reshaped band.

**Scope:** registered exploratory tier; a single checkpoint and training
recipe. Whether the direction of the shift (suppression, deepening) is a
general training effect or specific to this SFT+GRPO recipe is an open,
unregistered question for a future cell. Source of truth:
`experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md`, Outcome
section, resolved 2026-08-16.
