---
aliases:
- Full refusal-axis ablation collapse is seed-1-specific
- the refusal axis stays load-bearing at seed 2 but does not fully collapse
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:full-refusal-axis-ablation-collapse-is-seed1-specific
  type: mechanism
  status: canonical
cause: "Full refusal-axis ablation (freshly fit raw mass-mean direction at L35, same registered recipe as the seed-1 rederivation) on known-item rows of clean_sft_grpo_v2_seed2's own per-seed lineage (published seed-2 GRPO-v2 LoRA on the published seed-2 merged SFT base), under the byte-mirrored archived intervention pipeline, registered confirmatory of the seed-1 result."
polarity: decreases
effect: "Known-item over-refusal falls only from a 1.0000 baseline to 0.5528 (releasing 45.7 percentage points, specificity intact: induced refusal on known_correct_answered 0.0133, correct-rate drop 7.2pp), far above both the registered 0.10 confirmation bound and the 0.30 falsifier line, so RC-G1 fires the falsifier. The axis remains causally load-bearing at seed 2: ablation lifts formerly-refused known items from 0% to 29.2% correct, and shift_minus2 (0.5590) tracks the ablate arm almost exactly, while shift_plus2 saturates known-item refusal back to 1.0000. But the seed-1 near-total collapse (0.994 to 0.0298) does not transfer to a fresh seed: the 0.030-class full-ablation figure is seed-1-specific and is not promoted as a general (cross-seed) result. The seed-2 ablate value (0.5528) sits close to seed-1's separately-governed known-unknown-orthogonalized component result (0.5238) and to the constant-ablate control in the KU-readout-coupling lineage (0.536); whether the refusal axis decomposes differently across seeds is a candidate follow-up question, not a claim of this cell."
related:
- '[[refusal-axis-ablation-confirmatory]]'
- '[[caution-ablation-rederivation]]'
- '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
- '[[ku-readout-coupling-actuates-selective-refusal-release]]'
- '[[directional-ablation]]'
- '[[refusal-direction]]'
relationships:
- type: supported_by
  target: '[[refusal-axis-ablation-confirmatory]]'
  target_id: experiment:refusal-axis-ablation-confirmatory
  confidence: high
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md#outcome (RC-G0 PASS, RC-G1 falsifier fired: post-ablation known-item over-refusal 0.5528 >= 0.30; arm table and descriptive observations)"
- type: different_from
  target: '[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]'
  target_id: mechanism:raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse
  confidence: high
  evidence:
  - "experiments/caution-ablation-rederivation/AMENDMENT.md#outcome (seed-1: 0.994 to 0.0298, near-total collapse) versus experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md#outcome (seed-2: 1.0000 to 0.5528, partial release only); same registered recipe, different seed, non-replicating magnitude"
- type: related_to
  target: '[[caution-ablation-rederivation]]'
  target_id: experiment:caution-ablation-rederivation
  confidence: high
  evidence:
  - "seed-1 analog of this cell's registered recipe; this mechanism records the fresh-seed outcome of that recipe rather than a re-derivation on the same substrate"
- type: related_to
  target: '[[ku-readout-coupling-actuates-selective-refusal-release]]'
  target_id: mechanism:ku-readout-coupling-actuates-selective-refusal-release
  confidence: medium
  evidence:
  - "experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md#outcome (seed-2 full-axis ablate value 0.5528 sits near that mechanism's seed-1 constant-ablate control, 0.536; flagged as a descriptive observation, not a claim)"
- type: related_to
  target: '[[directional-ablation]]'
  target_id: method:directional-ablation
  confidence: high
- type: related_to
  target: '[[refusal-direction]]'
  target_id: term:refusal-direction
  confidence: medium
---

Registered confirmatory finding, resolved 2026-08-16: the near-total,
ceiling-to-floor known-item over-refusal collapse that
[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]
reproduced on `clean_sft_grpo_v2_seed1` (0.994 to 0.0298) does **not**
transfer to a fresh seed under the identical registered recipe. On
`clean_sft_grpo_v2_seed2`'s own per-seed lineage, full refusal-axis ablation
releases only 45.7 percentage points of known-item refusal (1.0000 to
0.5528), with specificity intact but far short of both the 0.10 confirmation
bound and the 0.30 falsifier line: RC-G1 fires the falsifier as registered.

**Why it matters here:** the finding is not that the refusal axis is inert
at seed 2. Ablation still lifts formerly-refused known items from 0% to
29.2% correct and shift_minus2 tracks the ablate arm almost exactly, so the
axis remains causally load-bearing. What fails to generalize is the
*magnitude* of the seed-1 collapse specifically: seed 1's near-complete
release is seed-1-specific, not a property of the refusal axis construct in
general. This blocks promotion of the 0.030-class figure into paper 3
section 6 and paper 5 section 6.6 as a cross-seed result.

**Scope:** this mechanism does not retract or contradict the seed-1 finding,
which stands on its own governed source
([[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]]).
It records a distinct, seed-2-scoped outcome under the same registered
recipe. The proximity of the seed-2 ablate value (0.5528) to seed-1's
known-unknown-orthogonalized component result (0.5238,
[[raw-theta-refusal-axis-ablation-rederives-archived-overrefusal-collapse]])
and to the KU-readout-coupling constant-ablate control (0.536,
[[ku-readout-coupling-actuates-selective-refusal-release]]) is recorded as a
descriptive observation only; whether the axis decomposes differently across
seeds is an open, unregistered question for a future cell.

Source of truth: `experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md`,
Outcome section, resolved 2026-08-16.
