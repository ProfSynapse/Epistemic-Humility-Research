# Phase 3 Causal-Pilot Smoke Results

Status: initial Tier 2 exploratory local smoke
Created: 2026-06-18
Scope: SFT `h_lora` layer-36 known/unknown direction on Qwen3-4B local artifacts

## What Ran

The first live causal-pilot runner was implemented as a separate explicit
generation path:

- runner: `experiment/phase1/probe/phase3_causal_pilot_runner.py`
- config: `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`
- tests: `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
- candidate direction: `direction__9c8c74f718038292`
- source extraction: `extraction__12fb10b1c8c8`
- role/layer: SFT `h_lora`, layer 36
- evidence tier: Tier 2 exploratory local diagnostic

Generation requires `--allow-generation` and a generation-enabled config. The
readiness-only dry-run remains no-generation.

The follow-on diagnostic path uses the same Phase 3 activation hook/model and
candidate direction machinery, but runs next-token logit comparison instead of
generation:

- mode: `--mode logit_diagnostic`
- gate: `--allow-logit-diagnostic`
- intent: distinguish a mechanically active but behaviorally stable greedy
  decode from a dead hook or wrong intervention path

## Guardrail Found And Fixed

The first two-row launch caught a live-control labeling bug before any larger
run: `control=sign_flip` was used with a positive coefficient. That artifact was
a valid hook/scoring smoke but misleading for interpretation.

Fixes applied:

- live controls now fail closed if unsupported;
- explicit controls are `activation_addition` and `activation_subtraction`;
- generated rows record `intervention_applied_count` and
  `intervention_delta_abs_sum`;
- logit diagnostic rows record `generation_executed: false` and
  `logit_diagnostic_executed: true`;
- coefficient/control grids now fail validation when empty;
- tests cover the gate, layer mapping, hook behavior, unsupported controls, and
  row-delta metrics;
- the experiment-runner skill records the gotcha.

## Runs

| Run | Rows | Coefficient | Controls | Result |
| --- | ---: | ---: | --- | --- |
| `run_20260618T202128Z` | 2 | +1 mislabeled as `sign_flip` | baseline + mislabeled intervention | Valid hook/scoring smoke, not interpretable as sign-flip evidence. |
| `run_20260618T202546Z` | 2 | +/-1 | baseline, addition, subtraction | No behavior/text movement. |
| `run_20260618T202903Z` | 16 | +/-1 | baseline, addition, subtraction | No behavior/text movement; 0 thinking contamination. |
| `run_20260618T203228Z` | 16 | +/-5 | baseline, addition, subtraction | No behavior/text movement; 0 thinking contamination. |
| `run_20260618T203542Z` | 16 | +/-50 | baseline, addition, subtraction | No behavior/text movement; 0 thinking contamination. |
| `run_20260618T203936Z` | 2 | +/-50 | baseline, addition, subtraction | Hook telemetry confirmed `applied_count=1`, `delta_abs_sum~1488`, no behavior/text movement. |
| `run_20260618T212414Z` | 2 | +/-50 | baseline, addition, subtraction | Logit diagnostic exited 0. |
| `run_20260618T212538Z` | 16 | +/-50 | baseline, addition, subtraction | Logit diagnostic exited 0; intervention changed logits but not greedy next-token top-1. |
| `run_20260618T213414Z` | 2 | +/-50 | baseline, addition, subtraction | Post-remediation logit diagnostic exited 0; row flags verified. |

For the 16-row runs, baseline behavior was:

- unknown refusal rate: `87.5%`
- answer-on-unknown rate: `12.5%`
- over-refusal on known: `25.0%`
- known-answer correctness: `62.5%`
- truthful rate: `75.0%`

Addition and subtraction matched those metrics exactly at coefficients 1, 5,
and 50, with `per_row_delta_vs_no_vector` showing zero refusal, correctness, or
truthfulness changes.

## Logit Diagnostic Result

CPU tests passed before the GPU diagnostic:

```bash
python -m pytest experiment\phase1\probe\tests\test_phase3_causal_pilot_runner.py experiment\phase1\probe\tests\test_phase3_causal_pilot_dry_run.py -q
```

Post-remediation result: `21 passed in 2.06s`.

Docker gotcha: the GPU smoke only reached the script after overriding the
Unsloth image entrypoint with `--entrypoint python`. Without that override,
`unsloth/unsloth:latest` ran studio setup and failed on mounted-repo `chmod`
permissions before invoking the runner.

The 2-row logit diagnostic output is:

`experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z`

It exited 0.

The 16-row logit diagnostic output is:

`experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z`

It exited 0 with:

| Control | Hook applied | `delta_abs_sum_mean` | `l2_logit_delta_mean` | `max_abs_logit_delta_max` | `top1_changed_rate` |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline | n/a | 0 | 0 | 0 | 0 |
| activation_addition | 16/16 | 1488.159424 | 145.364276 | 1.763671875 | 0.0 |
| activation_subtraction | 16/16 | 1488.159424 | 141.963216 | 1.734375 | 0.0 |

Post-remediation provenance smoke:

`experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z`

It exited 0. Metrics remained nonzero, and row-level metadata in
`logit_diagnostics.jsonl` now reports `generation_executed: false` and
`logit_diagnostic_executed: true`.

## Interpretation

This is a clean pipeline success and an initial null for this exact intervention
design. The hook fires and applies a large vector at the intended layer, but
greedy generation on the smoke slice is unchanged.

The logit diagnostic narrows that null. The intervention is mechanically active
and changes the next-token logit distribution, so the prior no-generation-change
result is not simply a dead hook. However, coefficient 50 on this SFT `h_lora`
layer-36 direction did not change greedy next-token top-1 on the 16-row smoke.

The result should not be overread as "no mechanism." Narrower interpretation:

- the SFT layer-36 `h_lora` known/unknown direction is a strong correlational
  readout on extracted final-prompt-token states;
- simple final-prompt-token activation addition/subtraction at that layer did
  not move greedy behavior or greedy next-token top-1 on the tested rows, even
  at high coefficient;
- the next causal step should use richer logit/probability diagnostics or an
  alternate intervention design, not broader row scaling.

## Next Diagnostic Step

Before scaling rows, extend the logit-level diagnostic beyond top-1 change. The
first diagnostic shows logits move while greedy top-1 does not, so the direction
may be behaviorally weak but real on this slice.

Candidate follow-ups:

- add richer logit targets and probability slices, especially refusal-token or
  answer-token probability movement;
- try the SFT `delta` layer-35 direction;
- run a layer/position sweep;
- intervene before or after final norm if the model architecture makes layer-36
  block-output addition ineffective;
- test these diagnostics before running more generated rows.
