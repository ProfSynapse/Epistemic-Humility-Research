---
title: jlens-trained-checkpoint-midband-ablation
aliases:
- J-lens on a trained checkpoint plus rule-selected mid-band refusal-axis ablation
- jlens-trained-checkpoint-midband-ablation (FALSIFIED)
tags:
- kg/experiment
- experiment
- j-space
- abstention
kg:
  id: experiment:jlens-trained-checkpoint-midband-ablation
  type: experiment
  status: canonical
related:
- '[[j-space-localization-qwen3-4b]]'
- '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
- '[[caution-ablation-rederivation]]'
- '[[refusal-axis-ablation-confirmatory]]'
- '[[jacobian-lens]]'
- '[[directional-ablation]]'
- '[[j-space-mediated-actuation-fragility]]'
- '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
- '[[caution-encoding-read-actuate-dissociation-across-families]]'
- '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
- '[[training-flattens-and-deepens-jlens-workspace-band]]'
relationships:
- type: builds_on
  target: '[[j-space-localization-qwen3-4b]]'
  target_id: experiment:j-space-localization-qwen3-4b
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md Design stage 3 (identical J-lens settings to the raw-base profile for comparability: same corpus manifest, seed 20260707, 5 random directions, same 13-point depth grid)"
- type: builds_on
  target: '[[j-space-calibrated-layer-contrast-qwen3-4b]]'
  target_id: experiment:j-space-calibrated-layer-contrast-qwen3-4b
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md Motivation and posture (the calibrated layer contrast showed mid-band hs23 beats the inherited late write site hs34 by 22.7 points on raw-base; this cell tests whether that mid-band advantage carries to a trained checkpoint and a different behavior, refusal-axis ablation)"
- type: builds_on
  target: '[[caution-ablation-rederivation]]'
  target_id: experiment:caution-ablation-rederivation
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md Motivation and posture (the governed full refusal-axis ablation on clean_sft_grpo_v2_seed1, 0.994 to 0.0298, sits at the probe-chosen late site L35, selected before the J-lens or the read/actuate depth-dissociation doctrine existed; this cell reruns the same intervention engine and row set at a rule-selected mid-band site on the same checkpoint)"
- type: uses
  target: '[[jacobian-lens]]'
  target_id: method:jacobian-lens
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md Design (adapted per-cell copy of the pinned raw-base J-lens driver, extended with --model/--adapter arguments, run on the trained substrate)"
- type: uses
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md Design stage 5 (four-arm intervention: baseline, ablate, shift_minus2, shift_plus2, at the rule-selected site, under the parity-locked legacy residual intervention runner)"
- type: tests
  target: '[[j-space-mediated-actuation-fragility]]'
  target_id: mechanism:j-space-mediated-actuation-fragility
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome (first test of the write/read-site-mismatch account on a TRAINED checkpoint and a full refusal-axis ablation rather than a raw-base steering write; falsifier fired on both clauses)"
- type: supports
  target: '[[refusal-axis-readable-but-not-ablatable-at-midband]]'
  target_id: mechanism:refusal-axis-readable-but-not-ablatable-at-midband
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome (JT-G1: ablation at hs17 releases 0/168 known-item over-refusals vs L35's 163/168, and induces refusal on 47.99% of previously answered knowns, while hs17 construction AUROC 0.8645 sits near L35's 0.8688)"
- type: supports
  target: '[[training-flattens-and-deepens-jlens-workspace-band]]'
  target_id: mechanism:training-flattens-and-deepens-jlens-workspace-band
  confidence: high
  evidence:
  - "experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md#outcome (profile P1: interior band present but narrowly, raw-base hs26 peak 0.01057 suppressed to 0.00694 post-training, band flattens and its peak moves to hs29 at 0.00735)"
- type: related_to
  target: '[[refusal-axis-ablation-confirmatory]]'
  target_id: experiment:refusal-axis-ablation-confirmatory
  confidence: medium
  evidence:
  - "both cells probe how far the seed-1 L35 refusal-axis collapse (0.994 to 0.0298) generalizes: refusal-axis-ablation-confirmatory across a fresh seed at the same L35 site (falsified, 0.5528), this cell across a rule-selected mid-band site on the same seed-1 checkpoint (falsified, 1.000)"
- type: related_to
  target: '[[full-refusal-axis-ablation-collapse-is-seed1-specific]]'
  target_id: mechanism:full-refusal-axis-ablation-collapse-is-seed1-specific
  confidence: medium
  evidence:
  - "companion falsified generalization test of the same governed L35 collapse: that mechanism shows the magnitude does not transfer across seeds at the fixed late site, this cell shows it does not transfer across depth at the fixed seed"
- type: related_to
  target: '[[caution-encoding-read-actuate-dissociation-across-families]]'
  target_id: mechanism:caution-encoding-read-actuate-dissociation-across-families
  confidence: medium
  evidence:
  - "same-checkpoint, same-axis instance of the program's read/actuate depth-dissociation doctrine, complementing that mechanism's cross-family late-site dissociation with a single-checkpoint cross-depth dissociation"
---

Registered exploratory tier-2 cell, PI-approved in-conversation 2026-08-16,
resolved 2026-08-16. **Verdict: FALSIFIED on both clauses.** First J-lens
characterization run on a trained checkpoint in the program (every prior
J-lens result is raw-base Qwen3-4B only), paired with a rule-selected
mid-band full refusal-axis ablation on the same checkpoint that carries the
governed [[caution-ablation-rederivation]] collapse.

JT-G0 (integrity) passed: smoke cosine 0.9811 / top-10 overlap 0.82 against
the raw-base J-lens (>= 0.95 / 0.7 gate); archived extraction and behavior
rows verified (1233 rows, cells 168/373); binding refusal-axis fit at the
rule-selected site carried construction AUROC 0.8645; intervention baseline
reproduced the archived 0.994 floor exactly (0.9940).

Profile question (band presence): the interior J-lens effective-dimensionality
band survives training but only narrowly, and is reshaped. Interior max
effective_dim_frac_mean is 0.00735 at hs29, just above the 1.5x-early-median
presence threshold (0.00675). Raw-base's hs26 peak (0.01057) is suppressed
about 35% at the same index (0.00694) and the band flattens and shifts
deeper, with a new peak at hs29 instead of hs26
([[training-flattens-and-deepens-jlens-workspace-band]]).

Site-selection rule (fixed at signing) selected **hs17**, the shallowest
interior grid point clearing 0.5x the interior maximum.

Ablation question: full refusal-axis ablation at hs17 releases **none** of
the known-item over-refusal (1.0000, far past the 0.30 falsifier line) and
induces refusal on 47.99% of the 373 previously answered known items
(correct-rate collapses to 0.5013), a catastrophic specificity break. Row-paired
against the governed L35 rederivation on the identical 541 rows: L35 releases
163 of 168 formerly refused knowns and hs17 releases zero, with zero overlap
between the two sites' released rows; hs17 additionally newly refuses 179 of
the 373 answered knowns that L35 leaves intact. A descriptive wrinkle: a -2 SD
shift at hs17 releases more of the collapse (0.7143) than full ablation
(1.0000 refused), suggesting the axis at this depth is entangled with the
model's answering computation rather than acting as a clean refusal toggle
([[refusal-axis-readable-but-not-ablatable-at-midband]]).

**Why it matters here:** hs17 reads the refusal axis nearly as well as L35
(construction AUROC 0.8645 vs 0.8688) yet the causal handle does not transfer
there at all. This is the strongest same-checkpoint, same-axis demonstration
of the read/actuate depth-dissociation doctrine
([[caution-encoding-read-actuate-dissociation-across-families]]) in the
program to date: J-lens read-side localization does not license a write site
on this trained checkpoint, and paper 3's late-site ablation stands validated
as the site where the handle actually works, not a naive legacy choice.

**Scope:** registered exploratory tier; per pre-stated posture the governed
paper-3 numbers and the seed-2 confirmatory cell
([[refusal-axis-ablation-confirmatory]]) are untouched by this result. Source
of truth: `experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md`,
Outcome section, resolved 2026-08-16.
