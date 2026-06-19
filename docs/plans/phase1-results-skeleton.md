# Phase 1 Paper-2 Results Skeleton

Status: manuscript scaffold, not final claims
Created: 2026-06-15
Scope: capture current Phase 1 result shape while seed completion remains the
immediate priority

## Use Rule

This document is a drafting scaffold for paper 2. It must not be cited as the
final results source until the locked v0.3 headline matrix has the required
seed coverage and analysis outputs.

Claim tiers:

1. **v0.3 headline evidence**: only the signed 2026-06-10 matrix, default
   configs, required seeds, and pre-registered analysis rules. These are the
   only source for paper headline claims.
2. **Amendment A / v0.4 extension evidence**: sequential `SFT -> DPO` and
   `SFT -> KTO` evidence, signed 2026-06-14 as a prospective extension. Report
   separately from v0.3 unless a later signed revision supersedes the matrix.
3. **Exploratory mechanism evidence**: hidden-state and probe diagnostics.
   Useful for mechanism hypotheses, not for behavioral headline claims.

## Immediate Priority

Complete the remaining seeds before upgrading any current pattern into a claim.

Seed-first work to protect the paper:

- finish the v0.3 default-config seed set for SFT, DPO, and KTO
- keep 4B headline results separate from 8B confirm and sensitivity-panel cells
- avoid expanding Amendment A until the seed-completion path is explicit
- persist per-row scored outputs for future evals: `id`, stable row/order key,
  label, refused, correct, truthful, and arm

## Manuscript Results Shape

### Result 1 - Cold-Start SFT Learns Abstention, But Over-Refuses

Claim tier: bounded local evidence so far; v0.3 headline claim pending seeds.

Current local pattern:

- SFT from base reliably induces refusal on unknowns across SelfAware and KUQ.
- The same behavior over-generalizes to known questions.
- Grouped-split reruns preserve the qualitative pattern, so the main SFT result
  is not explained away by the earlier train/dev duplicate-prompt issue.

Representative local numbers:

| Surface | Arm | Truthful | Refusal recall | Over-refusal | Notes |
|---|---:|---:|---:|---:|---|
| SelfAware full | SFT | 39.51 | 89.73 | 66.07 | pre-grouped comparator |
| SelfAware full | grouped SFT | 37.99 | 83.82 | 64.18 | grouped-split rerun |
| KUQ balanced | grouped SFT | 51.82 | 97.92 | 82.29 | broader OOD slice |

Draft interpretation:

SFT appears to teach an abstention policy, but the induced boundary is too
wide. The paper should frame this as the baseline failure mode the preference
methods are meant to repair, not as a solved humility behavior.

### Result 2 - Cold-Start DPO/KTO Stay Base-Like On Refusal

Claim tier: bounded local evidence so far; v0.3 headline claim pending seeds.

Current local pattern:

- DPO from base stays close to base on refusal behavior in SelfAware/KUQ local
  evidence.
- KTO from base also did not learn abstention on full SelfAware in the audited
  local comparator.
- This makes cold preference optimization look weak as an abstention inducer on
  this sized Qwen3 setup.

Representative local numbers:

| Surface | Arm | Truthful | Refusal recall | Over-refusal | Notes |
|---|---:|---:|---:|---:|---|
| SelfAware full | base | 19.26 | 0.00 | 0.04 | local comparator |
| SelfAware full | DPO | 15.08 | 0.00 | 0.04 | local comparator |
| SelfAware full | KTO | 18.73 | 0.00 | 0.21 | local comparator |

Draft interpretation:

The cold-start result motivates the Amendment A question: preference objectives
may be better understood as boundary refinement after SFT, rather than as the
first-stage mechanism that creates abstention behavior.

### Result 3 - Sequential DPO Reduces Over-Refusal But Overshoots

Claim tier: Amendment A / v0.4 extension evidence only.

Current local pattern:

- `SFT -> DPO` sharply reduces known-question over-refusal.
- The improvement is mixed because it also loses much of SFT's unknown refusal
  and lowers known correctness.
- Row-level transitions show that the over-refusal reduction is not purely
  useful recovery; many recovered answers are not correct.

Representative local numbers:

| Surface | Arm | Truthful | Refusal recall | Over-refusal | Correct on known |
|---|---:|---:|---:|---:|---:|
| SelfAware full | `sft_merged` | 38.50 | 82.56 | 61.49 | 49.44 |
| SelfAware full | `sft_dpo` | 30.25 | 48.84 | 13.95 | 25.61 |
| KUQ balanced | `sft_merged` | 52.34 | 98.44 | 80.21 | TBD |
| KUQ balanced | `sft_dpo` | 40.10 | 69.79 | 20.31 | TBD |

Transition evidence:

- SelfAware full: `sft_dpo` answered on 377 unknown rows where `sft_merged`
  had correctly refused.
- SelfAware full: `sft_dpo` converted 1,113 known SFT refusals into answers,
  but only 95 of those became correct answers.
- KUQ: 54 of 57 exact `sft_merged`-truthful / `sft_dpo`-untruthful flips came
  from unknown rows where DPO answered after SFT refused.

Draft interpretation:

Sequential DPO is the first local evidence of a meaningful reduction in
over-refusal after SFT, but the current operating point is too aggressive. The
next DPO question is not "does it move the boundary?" but "can a lower-intensity
preference stage move it less destructively?"

### Result 4 - Sequential KTO Preserves More Abstention But Leaves Over-Refusal

Claim tier: Amendment A / v0.4 extension evidence only.

Current local pattern:

- `SFT -> KTO` stays closer to SFT than sequential DPO.
- It preserves more unknown-question refusal and truthful score.
- It only partially reduces over-refusal, leaving the known-question failure
  still large.

Representative local numbers:

| Surface | Arm | Truthful | Refusal recall | Over-refusal | Correct on known |
|---|---:|---:|---:|---:|---:|
| SelfAware full | `sft_merged` | 38.50 | 82.56 | 61.49 | 49.44 |
| SelfAware full | `sft_kto` | 36.92 | 75.68 | 48.31 | 38.33 |
| KUQ balanced | `sft_merged` | 52.34 | 98.44 | 80.21 | TBD |
| KUQ balanced | `sft_kto` | 48.70 | 90.62 | 72.92 | TBD |

Transition evidence:

- SelfAware full: `sft_kto` answered on 91 unknown rows where `sft_merged`
  had correctly refused, versus 377 for `sft_dpo`.
- SelfAware full: `sft_kto` converted 322 known SFT refusals into answers, with
  37 correct.
- The exact truthful loss against SFT was smaller for `sft_kto` than for
  `sft_dpo` on SelfAware full: 125 vs 429 SFT-truthful / sequential-untruthful
  rows.

Draft interpretation:

Sequential KTO may be the conservative refinement path: it better preserves the
abstention behavior SFT created, but it does not yet solve over-refusal. KTO
sensitivity should target stronger known-question recovery without collapsing
unknown refusal.

### Result 5 - Mechanism Diagnostics Track The Behavioral Split

Claim tier: exploratory mechanism evidence only.

Current local pattern:

- The hidden-state diagnostics separate SFT from cold-start DPO/KTO in the same
  broad direction as behavior.
- SFT adapter/delta representations show stronger known-vs-unknown separability
  than cold-start DPO/KTO.
- Sequential arms preserve or reshape the SFT separability, but their base is
  the merged SFT model, so these are preference-stage deltas over SFT.

Representative local numbers:

| Arm | Best `h_base` | Best `h_lora` | Best `delta` | Caveat |
|---|---:|---:|---:|---|
| SFT | 0.75390625 L25 | 0.86328125 L36 | 0.85546875 L35 | original Qwen base |
| DPO | 0.75390625 L25 | 0.7734375 L35 | 0.75 L35 | original Qwen base |
| KTO | 0.75390625 L25 | 0.765625 L36 | 0.75 L26 | original Qwen base |
| `sft_dpo` | 0.84375 L36 | 0.85546875 L34 | 0.859375 L35 | merged SFT base |
| `sft_kto` | 0.84375 L36 | 0.859375 L35 | 0.85546875 L36 | merged SFT base |

Draft interpretation:

These probes can motivate a mechanism section or future Phase 3 work, but they
should not be used to claim internalized epistemic humility. The cautious read
is that SFT creates stronger known/unknown separability, cold-start preference
training does not, and sequential preference training operates on the SFT-shaped
representation.

## Figure And Table Placeholders

Priority manuscript artifacts after seed completion:

- Table 1: v0.3 headline default-config metrics by arm, mean and CI across
  seeds, with within-run bootstrap CIs available in appendix.
- Figure 1: refusal recall vs over-refusal trade-off for base/SFT/DPO/KTO.
- Figure 2: seed-level variation for each headline arm.
- Figure 3: sensitivity panel, explicitly labeled robustness-only and not a
  headline-number source.
- Table 2: Amendment A sequential results, labeled prospective extension.
- Figure 4: transition counts for `SFT -> DPO` and `SFT -> KTO`.
- Appendix table: exploratory hidden-state diagnostic readout.

## Missing Before Manuscript Claims

- Required seed completion for v0.3 default-config headline cells.
- Clear separation between 4B headline, 8B confirm, bridge, and sensitivity
  cells.
- Per-row scored outputs retained for every future live eval.
- Final decision on whether Amendment A remains an extension section or becomes
  a later signed v0.4 track that supersedes the original matrix.

## Current Narrative Draft

The current evidence suggests a two-stage story, but only as a scaffold. SFT is
effective at inducing abstention on unknown questions, yet it over-refuses badly
on known questions. Cold-start DPO and KTO do not appear to induce abstention in
the same local evidence. Sequential preference training is more promising but
not solved: DPO substantially reduces over-refusal while losing too much unknown
refusal and known correctness, whereas KTO preserves more of SFT's abstention
behavior but leaves over-refusal high. The immediate scientific risk is
over-interpreting a compelling local pattern before the seed-complete v0.3
matrix can say whether it is stable.
