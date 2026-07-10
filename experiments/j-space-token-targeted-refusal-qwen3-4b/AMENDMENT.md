# j-space-token-targeted-refusal-qwen3-4b

Status: resolved falsified (exploratory, not confirmatory).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

The resolved calibrated layer contrast showed that the regulated caution snap
works substantially better inside/near the J-space band than at the inherited
late write site: hs23 reached 165/185 = 89.2% clean_tighten with 9/258 = 3.5%
known-correct cost, while hs34 reached 123/185 = 66.5% with 7/258 = 2.7% cost.
That result supports the layer-site account, but it leaves a mechanistic
optimization question open: can the J-lens token readout be run "backward" to
construct an internal write direction that nudges the same hs23 workspace state
toward refusal tokens and away from answer-continuation tokens?

This experiment follows option 2 from the 2026-07-08 brainstorm: internal
J-space token-targeted writing. It explicitly does **not** use an external
decode-time logit bias. Any token targeting happens as a hidden-state direction
inserted at hs23/hs29 under the same doubt gate as the resolved caution snap.

Posture: exploratory Tier-2 steer cell, raw-base `unsloth/Qwen3-4B` bf16 only,
local RTX 3090 lane. It is not a headline claim and is not a cross-family
result. The implemented runner and frozen inputs were pinned by `bin/exp sign`
before the held-out run.

## Design

Substrate: raw-base `unsloth/Qwen3-4B`, bf16, no adapter, no 4-bit
quantization.

Inputs:

- Resolved hs23/hs29/hs34 layer contrast result and FIT-selected setpoints from
  `j-space-calibrated-layer-contrast-qwen3-4b`.
- Per-layer fitted doubt gates and `c_hat` directions from
  `j-space-midband-write-sweep-qwen3-4b`.
- J-lens implementation and H1/profile artifacts from
  `j-space-localization-qwen3-4b`.
- Local gitignored held-out row text inherited from the predecessor materialized
  row pool. No question text, aliases, raw generations, or row-level outputs are
  committed.

Primary layer: hs23, because it won the resolved held-out layer contrast.
Secondary descriptive layer: hs29, because it was close behind hs23 and remains
inside the broader hs23-29 workspace-like band.

Internal token-target direction construction:

1. Choose a fixed, audited token bundle before running the held-out evaluation.
   The draft primary bundle is `concrete_refusal_surface` in
   `token_bundle.yaml`: positive targets are clean refusal surface pieces such
   as `"I`, ` I`, ` know`, ` cannot`, ` unable`, ` impossible`, ` unknown`,
   ` insufficient`, and ` null`; negative targets are answer/reply
   continuation pieces including ` answer`, `answer`, ` reply`, `reply`, and
   the observed Chinese answer-axis tokens `答案`, `回答`, `的答案`, and `的回答`.
   This first run deliberately leans into tokens that naturally appeared in the
   model's J-lens readouts. Abstract labels such as ` doubt`, ` caution`,
   ` uncertain`, and ` unsure`, plus multilingual compact refusal-token bundles,
   are deferred to a separate follow-up rather than screened inside this
   amendment.
2. Use the J-lens at a candidate layer to derive a hidden-state direction that
   raises the positive target bundle and lowers the negative target bundle.
   The planned primitive is a normalized target-minus-anti-target gradient under
   the layer's J-lens map, not a decode-time logit bias.
3. Orthogonalize the token-target direction against the layer's `c_hat` only for
   the diagnostic "independent token write" arm; the hybrid arm may use both
   components.
4. Calibrate token-target dose on FIT rows only. Held-out rows are untouched
   until the signed full run.

Arms, all under the same frozen doubt gate:

- `c_hat_only_hs23`: resolved best-layer caution snap baseline, hs23 setpoint
  25.
- `j_token_only_hs23`: token-target direction only, dose selected on FIT rows.
- `c_hat_plus_j_token_hs23`: hs23 caution snap plus token-target direction.
- `c_hat_plus_random_j_hs23`: hs23 caution snap plus a random J-space control
  direction at matched token-target norm.
- `c_hat_plus_j_token_hs29`: descriptive secondary hybrid arm at hs29.

Generation and scoring mirror the resolved layer contrast: EOS-enabled greedy
JSON generation, `min_new_tokens=1`, `max_new_tokens=200`,
`enable_thinking=False`; clean_tighten requires a natural-stop single-object
JSON refusal; known-correct cost is `not_well_formed_correct`.

Instrument files to pin at sign: `cell.yaml`, `gates.yaml`,
`token_bundle.yaml`, `token_bundle_audit.py`, and `run_token_target.py`. The
runner writes fsync-backed private JSONL checkpoints for resume, strips prompt,
alias, question, raw-output, and decoded-answer fields at the checkpoint append
boundary, and commits only aggregate summaries or fitted directions.

FIT calibration is complete and fixes the held-out token-target dose at **5.0**.
The committed aggregate summary is
`analysis-committed/fit_calibration_summary.json`; private row-level
checkpoints remain under gitignored `analysis/`. At the selected dose, hs23
`c_hat_plus_j_token` reached 119/124 = 96.0% FIT confab clean_tighten versus
118/124 = 95.2% for `c_hat_only` (+0.8 percentage points), with no
known-correct cost increase (3/172 for both) and 0 malformed / forced /
non-target-language rows. This is coherent enough to freeze the held-out
instrument, but it is a weak FIT signal relative to the pre-stated >=4pp
prediction; higher token-target doses collapsed into malformed outputs and are
not carried forward.

## Prediction

On raw-base Qwen3-4B bf16, an hs23 hybrid of the resolved doubt-gated `c_hat`
snap plus an internal J-lens token-target refusal direction will improve
held-out confab clean_tighten over hs23 `c_hat_only` by at least 4 percentage
points without increasing known-correct cost by more than 2 percentage points,
and the matched random J-space control will not reproduce the improvement.

## Falsifier

The option-2 line is falsified on this surface if the hs23 hybrid improves
clean_tighten over hs23 `c_hat_only` by less than 4 percentage points, or if it
increases known-correct cost by more than 2 percentage points, or if a matched
random J-space control reproduces the improvement within 3 percentage points.

## Gates

- **G0 (instrument validity; stop, not outcome)**: runner is row-checkpointed
  and resumable; selected token bundle and anti-token bundle are fixed and
  tokenizer-audited before FIT dose calibration; token-target doses are selected
  on FIT rows only; local row text exists only under gitignored `analysis/`;
  private row checkpoints do not retain prompts, aliases, question text, raw
  generations, or decoded answer text; repeated `c_hat_only` FIT calibration
  uses a shared baseline checkpoint rather than re-generating the same arm per
  dose; gate-inactive no-op rows may be seeded across same-layer arms/doses
  because greedy generation receives no intervention when `fire=false`;
  smoke readback is within tolerance for every dosed smoke row; smoke collapse
  is 0 for every intervention arm; no question text, aliases, row-level outputs,
  or raw generations are committed.
- **G1 (hybrid improves clean refusal)**: hs23 `c_hat_plus_j_token` confab
  clean_tighten rate minus hs23 `c_hat_only` confab clean_tighten rate >= 4
  percentage points.
- **G2 (no selectivity regression)**: hs23 `c_hat_plus_j_token`
  known-correct cost minus hs23 `c_hat_only` known-correct cost <= 2 percentage
  points.
- **G3 (not just arbitrary extra J-space energy)**: hs23
  `c_hat_plus_j_token` clean_tighten improvement over `c_hat_only` exceeds the
  matched `c_hat_plus_random_j` improvement by at least 3 percentage points.
- **G4 (format/language guard)**: malformed JSON, forced-continuation, and
  non-target language-drift rates are not worse than hs23 `c_hat_only` by more
  than 2 percentage points.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Hybrid hs23 `c_hat + J-token refusal` beats hs23 `c_hat_only` modestly, mainly by converting residual malformed/continuing failures into clean natural-stop refusals; token-only helps less than the hybrid; random J-space control does not reproduce. |
| user | |

## Outcome

Resolved 2026-07-08 on the local RTX 3090. The full held-out run completed over
443 rows with private row-level checkpoints under gitignored `analysis/` and
aggregate-only committed output at
`analysis-committed/full_summary.json`. The checkpoint sanitizer scan found no
prompt, question, alias, raw-output, decoded-answer, or row text fields in the
private JSONL checkpoints.

Verdict: exploratory falsification of the option-2 strong claim. The internal
J-lens token-target write is controllable and safe at the selected dose, but it
does not materially improve the already strong doubt-gated `c_hat` snap on this
surface.

Held-out arms:

| Arm | Confab clean_tighten | Known-correct cost | Readback |
|-----|----------------------|--------------------|----------|
| `c_hat_only_hs23` | 165/185 = 89.2% | 9/258 = 3.5% | `c_hat` mean 24.999, 100% within tolerance |
| `c_hat_plus_j_token_hs23` | 166/185 = 89.7% | 10/258 = 3.9% | `c_hat` mean 24.998, `j_token` mean 4.998, 100% within tolerance |
| `c_hat_plus_random_j_hs23` | 165/185 = 89.2% | 10/258 = 3.9% | `c_hat` mean 25.000, `random_j` mean 5.003, 100% within tolerance |
| `j_token_only_hs23` | 88/185 = 47.6% | 7/258 = 2.7% | `j_token` mean 4.997, 100% within tolerance |
| `c_hat_plus_j_token_hs29` | 166/185 = 89.7% | 10/258 = 3.9% | `c_hat` mean 125.011, `j_token` mean 4.986, 100% within tolerance |

Gate results:

- **G0 passed**: token bundle was fixed and audited before FIT calibration;
  dose was selected on FIT rows only; smoke/readback passed; row text and raw
  generations stayed out of committed artifacts; checkpoint sanitization passed.
- **G1 failed**: hs23 hybrid improved clean_tighten by only +0.54 percentage
  points over `c_hat_only`, below the pre-stated +4pp threshold.
- **G2 passed**: known-correct cost increased by +0.39 percentage points, below
  the +2pp ceiling.
- **G3 failed**: the random-J control produced +0.0pp improvement, so the hybrid
  exceeded random by only +0.54pp, below the +3pp specificity threshold.
- **G4 passed**: malformed JSON, forced-continuation, and non-target language
  drift stayed within the +2pp guard. The hybrid had 2/443 malformed rows,
  1/443 forced continuations, and 1/443 non-target-language rows.

Interpretation: option 2 found a coherent token-target actuator but not a useful
additive controller at the natural-token dose. The token-only arm did move
behavior relative to no caution snap, reaching 47.6% clean_tighten, so the
J-lens backward direction is not inert. However, once the stronger `c_hat`
workspace-band snap is already active, the token-target write adds at most one
extra clean refusal on 185 confab rows and one extra known-correct cost event on
258 known rows. The hs29 descriptive hybrid exactly matches the hs23 hybrid
point estimate on clean_tighten and cost, which suggests this particular
token-target direction is not exposing a new layer-site advantage beyond the
resolved `c_hat` band effect.

Next step: do not copy this bespoke runner. Promote the reusable interface into
Synaptic Tuner only after settling the minimal schema for config-driven compound
multi-readout writes. For scientific follow-up, keep dense or multilingual token
packing as a separate item rather than moving this amendment's goalposts.
