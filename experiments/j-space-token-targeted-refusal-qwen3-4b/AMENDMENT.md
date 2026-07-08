# j-space-token-targeted-refusal-qwen3-4b

Status: draft (not signed; do not launch as confirmatory evidence).

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
result. The draft is not signed and must not be launched until the runner is
implemented, row-checkpointed, and pinned.

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

1. Choose a fixed, audited token bundle before running the held-out evaluation:
   refusal/abstention/unknown JSON-supporting tokens as positive targets, and
   answer/reply/continuation tokens as negative targets.
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

Instrument files to pin at sign: `cell.yaml`, `gates.yaml`, and the runner
module once implemented. The draft configs below describe the intended
instrument, but signing is blocked until the executable runner exists.

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
  and resumable; selected token bundle and anti-token bundle are fixed before
  FIT dose calibration; token-target doses are selected on FIT rows only; local
  row text exists only under gitignored `analysis/`; smoke readback is within
  tolerance for every dosed smoke row; smoke collapse is 0 for every intervention
  arm; no question text, aliases, row-level outputs, or raw generations are
  committed.
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

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
