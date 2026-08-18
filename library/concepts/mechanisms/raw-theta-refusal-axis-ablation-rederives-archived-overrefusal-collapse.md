---
aliases:
- Full refusal-axis ablation re-derives the 0.994-to-0.030 over-refusal collapse
- the 0.030/0.524 divergence is variant identity, not error
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  type: mechanism
  status: canonical
cause: "Ablating the full refusal axis (raw-theta direction, legacy artifact name caution_direction_L35) versus its known-unknown-orthogonalized component (legacy artifact name caution_perp_direction_L35) from the L35 residual stream on known-item rows of the clean_sft_grpo_v2_seed1 checkpoint, under the archived phase-1 intervention pipeline re-run byte-faithfully (direction files pinned by sha256, archived config bytes verified unmodified)."
effect: "Raw-theta ablation collapses known-item over-refusal from a reproduced 0.994 baseline to 0.0298 (correct-on-derefusal 57.14%, specificity 0.9786 intact), re-deriving the archived 0.994-to-0.030 figure near-exactly and giving it a governed source for the first time. The known-unknown-orthogonalized (caution_perp) ablation instead lands at 0.5238 (specificity 0.9732), reproducing its own separately-governed 0.524 rather than the 0.030 figure. Step-0 attribution, recorded before results existed, traces the archived 0.030 citation specifically to the raw-theta variant, not caution_perp. The 0.030-vs-0.524 divergence between the two governed cells is variant identity (which component was ablated), not instrument drift or error."
polarity: decreases
related:
- '[[caution-ablation-rederivation]]'
- '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
- '[[ku-readout-coupling-actuates-selective-refusal-release]]'
- '[[write-direction-naming-battery]]'
- '[[directional-ablation]]'
- '[[refusal-direction]]'
- '[[contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis]]'
relationships:
- type: supported_by
  target: '[[caution-ablation-rederivation]]'
  target_id: experiment:caution-ablation-rederivation
  confidence: high
  evidence:
  - "experiments/caution-ablation-rederivation/AMENDMENT.md#outcome (CA-G0 PASS all three configs; CA-G1 raw-theta reproduced <= 0.10; caution_perp not the 0.030 source, >= 0.30; falsifier NOT fired)"
- type: related_to
  target: '[[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]'
  target_id: mechanism:caution-residual-ablation-relaxes-overrefusal-asymmetrically
  confidence: high
  evidence:
  - "this cell gives that mechanism's cited 0.994-to-0.030 number a freshly generated, governed source (previously un-re-derivable per write-direction-naming-battery)"
- type: related_to
  target: '[[ku-readout-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:ku-readout-coupling-actuates-selective-refusal-release
  confidence: high
  evidence:
  - "resolves why that mechanism's constant-ablate control (0.536 known_refused release) sits close to this cell's caution_perp ablation (0.5238) while raw-theta (0.0298) sits far away: different ablated component, not error"
- type: related_to
  target: '[[write-direction-naming-battery]]'
  target_id: experiment:write-direction-naming-battery
  confidence: high
  evidence:
  - "experiments/write-direction-naming-battery/AMENDMENT.md (that amendment found the archived 0.030 figure's only sources were paper-3 prose and archived configs whose declared output paths no longer existed; this cell repairs the provenance)"
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
- type: related_to
  target: '[[contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis]]'
  target_id: mechanism:contract-elicited-base-refusal-direction-is-distinct-from-trained-refusal-axis
  confidence: medium
  evidence:
  - "this mechanism's clean_sft_grpo_v2_seed1 L35 raw-theta refusal axis is
    one of the three trained reference directions the base-under-contract
    comparison uses; that cell finds the base-under-contract direction far
    from it in cosine (|cos| 0.0436 against the SFT-GRPO-v2 arm), a
    geometric-distinctness complement to this mechanism's causal-ablation
    validation of the same direction"
---

Provenance-repair cell, resolved 2026-08-16: re-runs the archived phase-1 intervention pipeline byte-faithfully (frozen legacy mech-interp machinery, no modernization) to either recover a governed source for paper 3's cited 0.994-to-0.030 known-item over-refusal collapse, or formally retire it. The falsifier did not fire: the raw-theta variant (full refusal-axis ablation) reproduces the archived collapse near-exactly, while the known-unknown-orthogonalized (caution_perp) variant reproduces its own separately-governed 0.524, not the 0.030 figure. Both no-intervention baselines reproduce 0.994 within the +/-0.02 integrity gate, and every row set is at full declared coverage, lead-verified by independent recompute on every arm.

**Why it matters here:** resolves a standing ambiguity in the [[ku-readout-coupling-actuates-selective-refusal-release]] lineage. The 0.030 (full refusal-axis ablation) and 0.524 (known-unknown-orthogonalized component) numbers were never in tension; they are two different variants' numbers, both now reproduced under governed re-derivation.

**Scope:** provenance repair only. This cell does not by itself re-promote 0.030 into any paper; paper 3 keeps the governed [[ku-readout-coupling-actuates-selective-refusal-release]] numbers (0.994 -> 0.524, replication 0.536) unless a further registered confirmatory step promotes the re-derived figure.

**Lineage:** re-derives the archived instrument behind [[caution-residual-ablation-relaxes-overrefusal-asymmetrically]]; resolves the divergence from [[ku-readout-coupling-actuates-selective-refusal-release]] (renamed 2026-08-16 from the retired "doubt-regulated caution coupling" construct name, per `papers/common/terminology.md`); repairs the un-re-derivable citation flagged by [[write-direction-naming-battery]]. Source of truth: `experiments/caution-ablation-rederivation/AMENDMENT.md`, Outcome section, resolved 2026-08-16.
