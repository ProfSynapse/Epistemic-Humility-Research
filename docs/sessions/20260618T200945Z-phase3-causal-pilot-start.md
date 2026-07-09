---
schema_version: research-session/v1
session_id: 20260618T200945Z-phase3-causal-pilot-start
title: Phase 3 Causal Pilot Start
status: active
created_at: '2026-06-18T20:09:45Z'
updated_at: '2026-06-19T09:45:00Z'
phase: phase1
question: Track startup of the Phase 3 exploratory causal-pilot mechanistic-interpretability
  work from existing hidden-state directions.
tags:
- experiment-runner
- knowledge-graph
run_ids: []
trajectory:
  anchor: docs/research-trajectory.md
  current_position: Phase 3 exploratory mechanism work is moving from verified hidden-state
    direction readiness into a small causal-pilot design.
  changed_by_session: Starts the causal-pilot session, records the smoke-slice decision,
    and summarizes existing Tier 1 hidden-state diagnostics before Tier 2 intervention.
checkpoints:
- id: 001-planning
  at: '2026-06-18T20:10:56Z'
  kind: planning
  title: Causal Pilot Session Started
  summary: Started a fresh Phase 3 causal-pilot session after the Amendment B sequential
    results synthesis. Current target is a small Tier 2 exploratory local activation-addition/subtraction
    pilot from existing verified SFT hidden-state directions, with no claim promotion
    and no reward-loop use.
  evidence:
  - docs/plans/phase3-interpretability-direction.md
  - docs/plans/phase3-interpretability-research-process.md
  - experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml
  run_ids: []
  commands: []
  decisions:
  - Reduce the broad 112-arm dry-run plan to a smoke-slice before any live model intervention.
  next_steps:
  - Verify extraction/direction artifacts and design the smallest executable runner
    or diagnostic step.
  signals: {}
- id: 002-result
  at: '2026-06-18T20:40:48Z'
  kind: result
  title: Initial Activation-Addition Smoke Complete
  summary: Implemented and ran the first explicit Phase 3 activation-addition runner.
    The runner gate, CPU tests, Docker/GPU smoke path, and hook telemetry all worked.
    Coefficients 1, 5, and 50 on the SFT h_lora layer-36 known/unknown direction produced
    no behavior or text changes on the 16-row smoke slice; hook telemetry confirmed
    the coefficient-50 intervention applied.
  evidence:
  - docs/plans/phase3-causal-pilot-smoke-results.md
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203542Z/metrics.json
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203936Z/scored_rows.jsonl
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 1 --max-rows
    16 --allow-generation
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 5 --max-rows
    16 --allow-generation
  - docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 50 --max-rows
    16 --allow-generation
  decisions:
  - Do not scale row count yet; next add a logit-level diagnostic to distinguish a
    behaviorally stable greedy decode from a hook/layer placement issue.
  next_steps:
  - Implement or run a next-token logit/refusal-token diagnostic for baseline/add/subtract
    before trying other directions or larger slices.
  signals: {}
- id: 003-result
  at: '2026-06-18T21:30:00Z'
  kind: result
  title: Logit Diagnostic Smoke Complete
  summary: Added and ran the explicit Phase 3 logit diagnostic mode through the existing
    activation-hook/model/candidate path. CPU tests passed, and 2-row plus 16-row
    GPU smokes exited 0 after overriding the Unsloth Docker image entrypoint; a post-remediation
    2-row smoke then verified corrected row-level diagnostic metadata. The diagnostic
    showed activation addition/subtraction changed the next-token logit distribution
    on all 16 rows, but coefficient 50 did not change greedy next-token top-1 on this
    smoke slice.
  evidence:
  - docs/plans/phase3-causal-pilot-smoke-results.md
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode
    logit_diagnostic --allow-logit-diagnostic --max-rows 2
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode
    logit_diagnostic --allow-logit-diagnostic --max-rows 16
  - docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode
    logit_diagnostic --allow-logit-diagnostic --max-rows 2
  decisions:
  - Treat the prior no-generation-change result as not simply a dead hook; the intervention
    is mechanically active and changes logits.
  - Do not scale generation rows yet from this direction/coefficient alone, because
    coefficient 50 on SFT h_lora layer 36 did not change greedy next-token top-1 on
    the 16-row smoke.
  next_steps:
  - Prefer richer logit targets/probability slices, the alternate SFT delta layer-35
    direction, a layer/position sweep, or a final-norm intervention before broader
    generation scaling.
  signals:
    cpu_tests: 21 passed in 2.06s
    post_remediation_smoke: run_20260618T213414Z exited 0
    row_metadata: generation_executed false; logit_diagnostic_executed true
    activation_addition_hook_applied: 16/16
    activation_subtraction_hook_applied: 16/16
    top1_changed_rate: 0.0
- id: 004-infrastructure
  at: '2026-06-18T22:52:00Z'
  kind: infrastructure
  title: Reusable Full-Sweep Runner Fixed
  summary: Added reusable Phase 3 sweep orchestration for the full local candidate
    inventory, including Docker materialized-config path rewriting, per-job execution
    logs, execution_results.jsonl, mode filtering, host aggregation of Docker manifest
    paths, and a new mech-interp-runner skill. A malformed first sweep exposed the
    gotcha that Docker YAML must not contain Windows absolute output roots.
  evidence:
  - .skills/mech-interp-runner/SKILL.md
  - experiment/phase1/probe/phase3_causal_pilot_sweep.py
  - experiment/phase1/probe/phase3_causal_pilot_aggregate.py
  - experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml
  - experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml
  run_ids: []
  commands:
  - python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_sweep.py
    experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py
    -q
  - python -m py_compile experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py experiment\\phase1\\probe\\phase3_causal_pilot_aggregate.py
  - python sync_skills.py --check --skill mech-interp-runner
  decisions:
  - Keep base-original h_base skipped until the live runner supports adapterless base
    execution; current generator requires an adapter and wraps the base in PeftModel.
  next_steps:
  - Use the reusable sweep wrapper for future Phase 3 local runs rather than hand-written
    Docker loops.
  signals:
    focused_tests: 34 passed in 3.21s
    skill_sync: in sync for mech-interp-runner
- id: 005-result
  at: '2026-06-18T23:45:00Z'
  kind: result
  title: Full Local Causal-Pilot Sweep Complete
  summary: Ran the full executable local Phase 3 causal-pilot sweep across 8 trained-model
    candidate directions, excluding only the adapterless base direction. Both logit_diagnostic
    and generation modes completed with return code 0. Aggregation produced 144 rows,
    exactly 8 candidates x 9 arms x 2 modes. Logit interventions moved distributions,
    but generation effects were sparse and mostly harmful at coefficient 50 rather
    than clean humility control.
  evidence:
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/_execution_logs/execution_results.jsonl
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/sft_dpo_delta_l35/generation/run_20260618T233308Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/sft_kto_h_lora_l35/generation/run_20260618T233700Z
  run_ids: []
  commands:
  - python experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_local_sweep.yaml
    --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic
  - python experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_local_sweep.yaml
    --mode-filter generation --write-plan --materialize-configs --execute --allow-generation
  - python experiment\\phase1\\probe\\phase3_causal_pilot_aggregate.py --root experiment\\phase1\\probe\\qwen3-4b-instruct\\causal_pilots\\phase3_local_mech_interp_sweep
    --out experiment\\phase1\\probe\\qwen3-4b-instruct\\causal_pilots\\phase3_local_mech_interp_sweep\\summary.csv
  decisions:
  - Treat the full sweep as Tier 2 exploratory local evidence only; do not promote
    it into headline Phase 1 claims or reward design without a later governed revision.
  - Interpret current directions as mechanically active but not yet a reliable behavioral
    control knob.
  next_steps:
  - Inspect richer logit/probability targets around refusal-related tokens and consider
    layer/position/final-norm variants before scaling row count.
  - If pursuing behavioral steering, prioritize targeted SFT-KTO/SFT-DPO follow-up
    around the few changed rows rather than broadening all arms immediately.
  signals:
    executed_jobs: 16
    aggregate_rows: 144
    logit_top1_changes: sparse; strongest 4/16 on SFT-DPO coefficient-50 arms
    generation_behavior_changes: three intervention arms changed refusal/truthfulness;
      changed rows mostly removed abstention or corrupted correct answers
- id: 009-result
  at: '2026-06-19T01:12:00Z'
  kind: result
  title: Changed-Row Probability-Slice Replay Complete
  summary: Ran a bounded logit/probability replay for the two prior changed-row candidates,
    using coefficient 50 and the implemented no-vector, activation-addition, and activation-subtraction
    controls. The replay stayed logit-only on the existing 16-row slice and did not
    run generation.
  evidence:
  - experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T010135Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T010351Z
  run_ids: []
  commands:
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic
  decisions:
  - Treat this as Tier 2 exploratory local mechanism evidence only; no Phase 1 headline,
    arm-ranking, or reward-loop use.
  - Do not broaden generation from this result alone; probability movement is diagnostic
    and not yet a clean humility-control signal.
  next_steps:
  - If continuing, add or use an implemented exact row selector before claiming changed-row-only
    replay; the current runner replays the existing balanced 16-row slice that contains
    the changed rows.
  - Consider implementing explicit top-k reporting and wrong-layer/random or shuffled
    controls before any broader behavioral sweep.
  signals:
    docker_safety_gate: GPU idle, no compute processes, old Unsloth containers were
      sleep-only
    sft_dpo_delta_l35: addition reduced unknown refusal-opener probability on average
      and changed four top-1 next tokens; subtraction increased unknown refusal-opener
      probability but changed no top-1 tokens
    sft_kto_h_lora_l35: addition increased refusal-opener probability without top-1
      changes; subtraction reduced refusal-opener probability and changed two unknown-row
      top-1 tokens
- id: 010-result
  at: '2026-06-19T01:28:00Z'
  kind: result
  title: Exact-Row Top-K Replay Complete
  summary: Added exact row-key selection and top-k logit reporting to the Phase 3
    causal-pilot runner, then reran the changed-row probability diagnostic on only
    the prior changed rows. The final reruns also preserve skipped answer-alias tokenization
    metadata when all aliases are multi-token.
  evidence:
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
  - experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T011956Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T012206Z
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
    experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
  - python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py
    experiment/phase1/probe/phase3_causal_pilot_aggregate.py
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic
  decisions:
  - Preserve default balanced max_rows selection unless selection.row_keys or selection.row_keys_by_candidate
    is configured.
  - Keep this result Tier 2 exploratory local mechanism evidence only.
  next_steps:
  - Add wrong-layer/random/shuffled controls before broader behavioral sweeps.
  - Consider fixing the tokenizer regex warning in the model load path before treating
    fine-grained tokenization as fully settled.
  signals:
    exact_rows: sft_dpo_delta_l35 used 4 row keys; sft_kto_h_lora_l35 used 2 row keys
    top_k: top_k=10 recorded per row for baseline and intervention
    sft_dpo_delta_l35: addition changed 4/4 top-1 tokens; subtraction changed 0/4
    sft_kto_h_lora_l35: addition changed 0/2 top-1 tokens; subtraction changed 2/2
- id: 011-result
  at: '2026-06-19T01:40:00Z'
  kind: result
  title: Wrong-Layer And Random Controls Complete
  summary: Added two scientifically valid logit-diagnostic controls to the Phase 3
    runner, wrong-layer with configured offset -1 and deterministic random matched-norm
    with seed 20260619. Shuffled-label remained skipped because there is no shuffled-label
    direction artifact or valid derivation in the current checked-in runner path.
    Exact-row logit diagnostics reran with no generation.
  evidence:
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
  - experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T013022Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T013300Z
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
    experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
  - python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py
    experiment/phase1/probe/phase3_causal_pilot_aggregate.py
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm
    --max-rows 16 --allow-logit-diagnostic
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm
    --max-rows 16 --allow-logit-diagnostic
  decisions:
  - Keep wrong-layer and random matched-norm scoped to logit diagnostics for this
    checkpoint.
  - Do not implement shuffled-label without an actual shuffled-label direction artifact
    or valid checked-in derivation.
  next_steps:
  - Treat DPO-delta real-direction effects as weakened by a strong wrong-layer control
    until a layer/nearby-layer panel separates them.
  - Continue to defer generation scaling; controls do not yet support a clean humility-control
    interpretation.
  signals:
    sft_dpo_delta_l35: real addition changed 4/4 top-1 rows; wrong-layer changed 3/4;
      random matched-norm changed 0/4
    sft_kto_h_lora_l35: real subtraction changed 2/2 top-1 rows; wrong-layer changed
      0/2; random matched-norm changed 0/2
    random_seed: 20260619
    wrong_layer_offset: -1
- id: 012-result
  at: '2026-06-19T09:32:00Z'
  kind: result
  title: DPO-Delta Nearby-Layer Logit Panel Complete
  summary: Ran a bounded logit-only nearby-layer panel for `sft_dpo_delta_l35` on
    the configured exact rows, coefficient 50, comparing source-layer activation addition
    at layer 35 with wrong-layer application at nearby layers 33, 34, and 36. Offset
    +2 was attempted but failed closed because it would apply to layer 37, beyond
    the model's 36 decoder blocks.
  evidence:
  - experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m2.yaml
  - experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m1.yaml
  - experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p1.yaml
  - experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p2.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_m2/run_20260619T091724Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_m1/run_20260619T091933Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_p1/run_20260619T092130Z
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
    experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
  - python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py
    experiment/phase1/probe/phase3_causal_pilot_aggregate.py
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls
    no_vector_baseline,activation_addition,wrong_layer --allow-logit-diagnostic
  decisions:
  - Keep the result Tier 2 exploratory local mechanism evidence only; no Phase 1 headline,
    arm-ranking, generation-sweep, cloud, or reward-loop use.
  - Treat `sft_dpo_delta_l35` source-layer specificity as weakened, not supported,
    because nearby wrong-layer applications matched 3/4 top-1 changes at each executable
    offset.
  next_steps:
  - Do not launch generation from this DPO-delta result alone.
  - If pursuing this candidate, prioritize non-layer-local explanations or stronger
    controls before behavioral scaling.
  signals:
    docker_safety_gate: old Unsloth containers were sleep-only; GPU was idle with
      no compute processes before launch
    exact_rows: 4
    source_layer: 35
    executable_wrong_layers:
    - 33
    - 34
    - 36
    invalid_offset: +2 -> layer 37 exceeds 36 decoder blocks
    source_activation_addition_top1: 4/4
    wrong_layer_offset_m2_top1: 3/4
    wrong_layer_offset_m1_top1: 3/4
    wrong_layer_offset_p1_top1: 3/4
- id: 013-result
  at: '2026-06-19T09:45:00Z'
  kind: result
  title: KTO H-Lora Sign-Matched Nearby-Layer Panel Complete
  summary: Added a minimal logit-diagnostic-only `wrong_layer_subtraction` control
    so KTO h_lora source-layer subtraction could be compared against sign-matched
    nearby wrong-layer controls. Ran the bounded exact-row KTO panel at coefficient
    50 for offsets -2, -1, and +1 with no generation and no cloud.
  evidence:
  - experiment/phase1/probe/phase3_causal_pilot_runner.py
  - experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
  - experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m2.yaml
  - experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m1.yaml
  - experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_p1.yaml
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_m2/run_20260619T093626Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_m1/run_20260619T093834Z
  - experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_p1/run_20260619T094047Z
  run_ids: []
  commands:
  - python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py
    experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q
  - python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py
    experiment/phase1/probe/phase3_causal_pilot_aggregate.py
  - docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py
    --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls
    no_vector_baseline,activation_subtraction,wrong_layer_subtraction --allow-logit-diagnostic
  decisions:
  - Preserve existing positive `wrong_layer` semantics for prior DPO results; use
    explicit `wrong_layer_subtraction` only for sign-matched subtraction controls.
  - Treat KTO h_lora source-layer specificity as weakened by sign-matched nearby-layer
    controls.
  next_steps:
  - Do not launch generation from this KTO h_lora result alone.
  - If continuing, investigate why these high-layer directions behave as non-local
    answer-token steering before testing behavior.
  signals:
    focused_tests: 50 passed
    exact_rows: 2
    source_layer: 35
    executable_wrong_layers:
    - 33
    - 34
    - 36
    source_activation_subtraction_top1: 2/2
    wrong_layer_subtraction_offset_m2_top1: 2/2
    wrong_layer_subtraction_offset_m1_top1: 2/2
    wrong_layer_subtraction_offset_p1_top1: 1/2
legacy_session:
  id: phase3-causal-pilot-start
  path: docs/sessions/0006 - phase3-causal-pilot-start.md
---
# Phase 3 Causal Pilot Start

## Question

Track startup of the Phase 3 exploratory causal-pilot mechanistic-interpretability work from existing hidden-state directions.

## Trajectory Position

This session follows the completed Amendment B sequential SelfAware reruns and
the initial Phase 3 dry-run readiness materialization. It is not a protocol
change and does not alter Phase 1 headline evidence. The immediate aim is to
test whether existing known/unknown hidden-state directions are merely
correlational readouts or have controlled behavioral leverage under a small
local activation-addition/subtraction pilot.

## Summary

The broad dry-run plan contains 112 planned arms/controls. Before any live model
intervention, this session narrows the first causal pilot to a smoke slice and
records the existing Tier 1 diagnostic baseline. Existing verified 128 known /
128 unknown extractions show SFT has stronger active-adapter and delta
known/unknown separability than cold-start DPO/KTO, while sequential DPO/KTO
preserve or reshape high SFT separability over the merged-SFT base. This remains
correlational until a controlled intervention changes behavior.

## Checkpoints
### 001-planning - Causal Pilot Session Started

- at: `2026-06-18T20:10:56Z`
- kind: `planning`
- summary: Started a fresh Phase 3 causal-pilot session after the Amendment B sequential results synthesis. Current target is a small Tier 2 exploratory local activation-addition/subtraction pilot from existing verified SFT hidden-state directions, with no claim promotion and no reward-loop use.
- evidence:
  - `docs/plans/phase3-interpretability-direction.md`
  - `docs/plans/phase3-interpretability-research-process.md`
  - `experiment/phase1/probe/config/phase3_causal_pilot_smoke.yaml`
- decisions:
  - Reduce the broad 112-arm dry-run plan to a smoke-slice before any live model intervention.
- next steps:
  - Verify extraction/direction artifacts and design the smallest executable runner or diagnostic step.

### 002-observation - Tier 1 Diagnostic Baseline

- at: `2026-06-18T20:24:00Z`
- kind: `observation`
- summary: Existing hidden-state diagnostic artifacts show a stable Tier 1
  pattern: SFT has higher active-adapter/delta known-vs-unknown separability
  than cold-start DPO/KTO, and sequential DPO/KTO retain high separability over
  the merged-SFT base. This does not establish causal control.
- evidence:
  - `docs/plans/phase3-hidden-state-diagnostic-summary.md`
  - `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8/manifest.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/hidden_states/extraction__12fb10b1c8c8/hidden_state_linear_probe_kfold5_diagnostic.csv`
- commands:
  - `python - <<summary script over hidden-state manifests and diagnostic CSVs>>`
- decisions:
  - Treat the first causal pilot as a test of behavioral leverage, not a repeat of the linear-probe result.
- next steps:
  - Wait for the implementation-feasibility handoff, then decide whether to add a minimal activation-addition runner or another readiness layer.
### 002-result - Initial Activation-Addition Smoke Complete

- at: `2026-06-18T20:40:48Z`
- kind: `result`
- summary: Implemented and ran the first explicit Phase 3 activation-addition runner. The runner gate, CPU tests, Docker/GPU smoke path, and hook telemetry all worked. Coefficients 1, 5, and 50 on the SFT h_lora layer-36 known/unknown direction produced no behavior or text changes on the 16-row smoke slice; hook telemetry confirmed the coefficient-50 intervention applied.
- evidence:
  - `docs/plans/phase3-causal-pilot-smoke-results.md`
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203542Z/metrics.json`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T203936Z/scored_rows.jsonl`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 1 --max-rows 16 --allow-generation`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 5 --max-rows 16 --allow-generation`
  - `docker run --gpus all ... phase3_causal_pilot_runner.py --coefficients 50 --max-rows 16 --allow-generation`
- decisions:
  - Do not scale row count yet; next add a logit-level diagnostic to distinguish a behaviorally stable greedy decode from a hook/layer placement issue.
- next steps:
  - Implement or run a next-token logit/refusal-token diagnostic for baseline/add/subtract before trying other directions or larger slices.

### 003-result - Logit Diagnostic Smoke Complete

- at: `2026-06-18T21:30:00Z`
- kind: `result`
- summary: Added and ran the explicit Phase 3 logit diagnostic mode through the existing activation-hook/model/candidate path. CPU tests passed, and 2-row plus 16-row GPU smokes exited 0 after overriding the Unsloth Docker image entrypoint; a post-remediation 2-row smoke then verified corrected row-level diagnostic metadata. The diagnostic showed activation addition/subtraction changed the next-token logit distribution on all 16 rows, but coefficient 50 did not change greedy next-token top-1 on this smoke slice.
- evidence:
  - `docs/plans/phase3-causal-pilot-smoke-results.md`
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 16`
  - `docker run --gpus all --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --allow-logit-diagnostic --max-rows 2`
- result:
  - Post-remediation CPU tests: `21 passed in 2.06s`.
  - 2-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212414Z`, exit 0.
  - 16-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T212538Z`, exit 0.
  - Post-remediation 2-row output: `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260618T213414Z`, exit 0.
  - Row-level diagnostic metadata now reports `generation_executed: false` and `logit_diagnostic_executed: true`; metrics remained nonzero.
  - The runner now validates non-empty coefficient/control grids.
  - Activation addition applied hooks on `16/16` rows; `delta_abs_sum_mean=1488.159424`, `l2_logit_delta_mean=145.364276`, `max_abs_logit_delta_max=1.763671875`, `top1_changed_rate=0.0`.
  - Activation subtraction applied hooks on `16/16` rows; `delta_abs_sum_mean=1488.159424`, `l2_logit_delta_mean=141.963216`, `max_abs_logit_delta_max=1.734375`, `top1_changed_rate=0.0`.
  - Baseline deltas were zero.
- interpretation:
  - The intervention is mechanically active and changes the logit distribution, so the prior no-generation-change result is not simply a dead hook.
  - Coefficient 50 on this SFT `h_lora` layer-36 direction did not change greedy next-token top-1 on the 16-row smoke.
- next steps:
  - Prefer richer logit targets/probability slices, the alternate SFT `delta` layer-35 direction, a layer/position sweep, or a final-norm intervention before broader generation scaling.

### 004-infrastructure - Reusable Full-Sweep Runner Fixed

- at: `2026-06-18T22:52:00Z`
- kind: `infrastructure`
- summary: Added reusable Phase 3 sweep orchestration for the full local candidate inventory, including Docker materialized-config path rewriting, per-job execution logs, `execution_results.jsonl`, mode filtering, host aggregation of Docker manifest paths, and a new `mech-interp-runner` skill. A malformed first sweep exposed the gotcha that Docker YAML must not contain Windows absolute output roots.
- evidence:
  - `.skills/mech-interp-runner/SKILL.md`
  - `experiment/phase1/probe/phase3_causal_pilot_sweep.py`
  - `experiment/phase1/probe/phase3_causal_pilot_aggregate.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_full_candidates.yaml`
  - `experiment/phase1/probe/config/phase3_causal_pilot_local_sweep.yaml`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_sweep.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py experiment\\phase1\\probe\\phase3_causal_pilot_aggregate.py`
  - `python sync_skills.py --check --skill mech-interp-runner`
- result:
  - Focused tests passed: `34 passed in 3.21s`.
  - Skill mirrors are in sync for `mech-interp-runner`.
- decisions:
  - Keep base-original `h_base` skipped until the live runner supports adapterless base execution; current generator requires an adapter and wraps the base in `PeftModel`.
- next steps:
  - Use the reusable sweep wrapper for future Phase 3 local runs rather than hand-written Docker loops.

### 005-result - Full Local Causal-Pilot Sweep Complete

- at: `2026-06-18T23:45:00Z`
- kind: `result`
- summary: Ran the full executable local Phase 3 causal-pilot sweep across 8 trained-model candidate directions, excluding only the adapterless base direction. Both `logit_diagnostic` and `generation` modes completed with return code 0. Aggregation produced 144 rows, exactly 8 candidates x 9 arms x 2 modes. Logit interventions moved distributions, but generation effects were sparse and mostly harmful at coefficient 50 rather than clean humility control.
- evidence:
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/_execution_logs/execution_results.jsonl`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/sft_dpo_delta_l35/generation/run_20260618T233308Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/sft_kto_h_lora_l35/generation/run_20260618T233700Z`
- commands:
  - `python experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_local_sweep.yaml --mode-filter logit_diagnostic --write-plan --materialize-configs --execute --allow-logit-diagnostic`
  - `python experiment\\phase1\\probe\\phase3_causal_pilot_sweep.py --config experiment\\phase1\\probe\\config\\phase3_causal_pilot_local_sweep.yaml --mode-filter generation --write-plan --materialize-configs --execute --allow-generation`
  - `python experiment\\phase1\\probe\\phase3_causal_pilot_aggregate.py --root experiment\\phase1\\probe\\qwen3-4b-instruct\\causal_pilots\\phase3_local_mech_interp_sweep --out experiment\\phase1\\probe\\qwen3-4b-instruct\\causal_pilots\\phase3_local_mech_interp_sweep\\summary.csv`
- result:
  - Executed jobs: 16 total, all return code 0.
  - Aggregated rows: 144.
  - Logit diagnostic: all executable directions produced nonzero logit movement. Top-1 next-token changes were sparse; strongest arms were `sft_dpo_delta_l35` coefficient-50 activation-addition and `sft_dpo_h_lora_l34` coefficient-50 activation-subtraction at `4/16`.
  - Generation: only three intervention arms changed refusal/truthfulness relative to no-vector baseline. The changed examples mostly removed abstention on unknown rows or changed a correct known answer to an incorrect one.
  - Baseline generation on the 16-row slice tracked prior behavior qualitatively: cold DPO/KTO answered all unknowns; SFT refused most unknowns; sequential arms were intermediate.
- interpretation:
  - These directions are mechanically active, but current activation addition/subtraction is not yet a reliable behavioral humility-control knob.
  - The best current evidence is negative/diagnostic: simple hidden-state direction steering can move logits without producing clean abstention improvements, and high-coefficient behavioral movement can degrade answers.
- next steps:
  - Inspect richer logit/probability targets around refusal-related tokens and consider layer/position/final-norm variants before scaling row count.
  - If pursuing behavioral steering, prioritize targeted SFT-KTO/SFT-DPO follow-up around the few changed rows rather than broadening all arms immediately.

### 006-observation - External Gap-Fill And Next Diagnostic Gate

- at: `2026-06-19T00:45:00Z`
- kind: `observation`
- summary: After the full local causal-pilot sweep, internal KG search and an
  external arXiv gap-fill agree that the next useful Phase 3 step is richer
  diagnostic instrumentation, not another broad generation sweep. The current
  directions are mechanically active but not clean humility-control knobs; newer
  refusal literature weakens the single-direction assumption and SAE-refusal
  work adds capability-entanglement risk.
- evidence:
  - `docs/plans/phase3-mechanism-source-map.md`
  - `docs/plans/phase3-interpretability-research-process.md`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/summary.csv`
  - `https://arxiv.org/abs/2602.02132`
  - `https://arxiv.org/abs/2512.16602`
  - `https://arxiv.org/abs/2411.11296`
  - `https://arxiv.org/abs/2505.23556`
- commands:
  - `python .agents\\skills\\knowledge-graph\\scripts\\kg_search.py "refusal direction activation steering" --root library --limit 12`
  - `python .agents\\skills\\knowledge-graph\\scripts\\kg_search.py "activation patching metric corruption steering" --root library --db .tmp\\kg-search\\phase3_patch.sqlite --limit 12`
  - `$env:PYTHONIOENCODING='utf-8'; python .agents\\skills\\knowledge-graph\\scripts\\kg_search.py "more than single refusal direction distributed refusal steering" --root library --db .tmp\\kg-search\\phase3_refusal_multi_utf8.sqlite --limit 12`
- result:
  - Local KG already has activation addition, CAA, activation patching, truth
    direction, representation engineering, and the 2024 single-refusal-direction
    paper represented.
  - Added source-ready notes and arXiv HTML sources for `2602.02132`,
    `2512.16602`, `2411.11296`, and `2505.23556`.
  - Added conservative KG atoms for sparse autoencoders, correlational probes,
    causal interventions, known/unknown directions, multi-direction refusal, and
    SAE-refusal capability tradeoffs.
  - KG search itself exposed Windows gotchas: repo-wide indexing can fall into
    inaccessible local HF cache files, stale default `.kg` state can cause
    SQLite constraint errors, and cp1252 stdout can fail on Unicode. Use scoped
    `--root library`, scratch `--db .tmp/kg-search/*.sqlite`, and
    `PYTHONIOENCODING=utf-8` when needed.
- decisions:
  - Next implementation should add refusal/answer token probability slices and
    targeted changed-row replay.
  - Defer broader generation sweeps, SAE/encoder training, and manuscript-level
    mechanism claims until the source-map gaps are filled and the probability
    diagnostics clarify whether interventions move refusal tokens, answer
    tokens, or unrelated logits.
- next steps:
  - Implement probability-slice diagnostics in the Phase 3 runner.
  - Add a targeted replay config for changed rows plus matched stable rows.
  - Run full `kg-ingest` extraction for the newer refusal and SAE-refusal papers
    before treating their detailed claims as validated KG evidence.

### 007-result - Probability-Slice Diagnostic Smoke Running

- at: `2026-06-19T00:25:00Z`
- kind: `result`
- summary: Added config-driven next-token probability/logit target slices to the
  Phase 3 logit diagnostic path and verified them with a 2-row Docker/GPU smoke.
  The diagnostic now reports static refusal-opener probability mass and dynamic
  row-specific answer-alias probability mass. A first live smoke exposed a
  tokenization gotcha: multi-token answer aliases can resolve to a first token
  like `I`, colliding with refusal openers. The runner now skips multi-token
  answer aliases by default and records them as skipped targets.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_gpu_smoke.yaml`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260619T002325Z/logit_diagnostics.jsonl`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_sft_activation_addition_gpu_smoke/run_20260619T002325Z/run_manifest.json`
- commands:
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py -q`
  - `python -m pytest experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_sweep.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_runner.py experiment\\phase1\\probe\\tests\\test_phase3_causal_pilot_dry_run.py -q`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --coefficients 50 --max-rows 2 --allow-logit-diagnostic`
- result:
  - Focused runner tests after the tokenization fix: `34 passed`.
  - Broader focused probe subset before the tokenization fix: `49 passed`; rerun
    after final patch pending in this session.
  - Live 2-row smoke output: `run_20260619T002325Z`, exit 0, 3 arms, 2 rows.
  - On the smoke rows, activation addition increased refusal-opener probability
    by about `+0.0280` on the unknown row and `+0.0195` on the known row, while
    answer-alias movement was near zero on the unknown row and about `+0.0012`
    on the known row. Activation subtraction reduced refusal-opener probability
    by about `-0.0312` and `-0.0295`.
- interpretation:
  - The SFT layer-36 direction is not dead: it changes a meaningful refusal
    opener slice even when greedy top-1 does not change.
  - This tiny smoke still does not show a clean humility-control knob, because
    the answer slice barely moves and the top token stays `I`.
  - Probability slices are more informative than the previous top-1-only
    diagnostic and should be run on the changed-row replay next.
- next steps:
  - Rerun the broader focused CPU probe tests after the tokenization fix.
  - Run the probability-slice diagnostic on the targeted changed-row replay
    before any broader generation sweep.

### 008-governance - Phase 3 Control-System Protocol Drafted

- at: `2026-06-19T00:55:00Z`
- kind: `governance`
- summary: Added a standalone Phase 3 control-system protocol draft for
  exploratory mechanism evidence. It keeps Phase 3 separate from signed Phase 1
  protocol authority and records that Tier 1/Tier 2 mechanism outputs are not
  headline evidence, arm ranking, or reward-loop input.
- evidence:
  - `docs/protocols/phase3/control-system-protocol.md`
  - `docs/research-trajectory.md`
  - `docs/plans/phase3-interpretability-research-process.md`
- decisions:
  - Treat the new protocol as the current Phase 3 exploratory governance
    pointer unless a later signed revision promotes specific claims.
- next steps:
  - Source-gate the pending literature queue before using those papers as
    claim-bearing mechanism evidence.

### 009-result - Changed-Row Probability-Slice Replay Complete

- at: `2026-06-19T01:12:00Z`
- kind: `result`
- summary: Ran a bounded logit/probability replay for the two prior changed-row
  candidates, using coefficient 50 and the implemented no-vector,
  activation-addition, and activation-subtraction controls. The replay stayed
  logit-only on the existing 16-row slice and did not run generation.
- evidence:
  - `experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T010135Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T010351Z`
- commands:
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic`
- result:
  - Docker/GPU gate passed: old Unsloth containers were sleep-only, `nvidia-smi`
    reported no compute processes, and GPU memory/utilization were idle before
    launch.
  - `sft_dpo_delta_l35`: coefficient-50 activation addition changed `4/16`
    top-1 next tokens. On unknown rows, refusal-opener probability moved down
    on average (`-0.032731`); on known rows, answer-alias probability moved down
    on average (`-0.012526`, driven by the Henley/July row). Subtraction changed
    no top-1 tokens and moved unknown refusal-opener probability up on average
    (`+0.070166`).
  - `sft_kto_h_lora_l35`: coefficient-50 activation subtraction changed `2/16`
    top-1 next tokens, including the prior Miss World changed row (`I` to
    `England`). Subtraction moved unknown refusal-opener probability down on
    average (`-0.037008`). Addition moved refusal-opener probability up on both
    unknown (`+0.024658`) and known (`+0.016293`) rows but changed no top-1
    tokens.
  - Answer-alias slices were available only for rows with exact single-token
    aliases under the current guard. Multi-token answer rows such as Wookey
    Hole, Lost In Space, Ann Summers, and the Copernicus answer had no
    answer-alias probability group in these row metrics.
- interpretation:
  - Probability slices clarify that the prior behavioral changes are not clean
    humility-control moves. `sft_dpo_delta_l35` addition changed top-1 tokens
    while reducing refusal-opener mass on unknown rows and suppressing at least
    one known answer alias. `sft_kto_h_lora_l35` subtraction reduced refusal
    mass and pushed an unknown row toward an answer token.
  - Current evidence remains Tier 2 exploratory local mechanism evidence only,
    not Phase 1 headline evidence, arm ranking, or reward-loop input.
- limitations:
  - The checked-in runner has no exact row-id selector, so this replay used the
    existing balanced 16-row slice that contains the changed rows rather than a
    changed-row-only slice.
  - The runner reports top-1 movement but not top-k movement.
  - Wrong-layer, random-direction, and shuffled-label controls are not
    implemented for this runner path; only no-vector, addition, and subtraction
    were run.
- next steps:
  - Add an exact row selector and explicit top-k reporting before making a
    narrower changed-row-only claim.
  - Add wrong-layer/random/shuffled controls before broader behavioral sweeps.

### 010-result - Exact-Row Top-K Replay Complete

- at: `2026-06-19T01:28:00Z`
- kind: `result`
- summary: Added exact row-key selection and top-k logit reporting to the Phase
  3 causal-pilot runner, then reran the changed-row probability diagnostic on
  only the prior changed rows. The final reruns also preserve skipped
  answer-alias tokenization metadata when all aliases are multi-token.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T011956Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T012206Z`
- commands:
  - `python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py experiment/phase1/probe/phase3_causal_pilot_aggregate.py`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction --max-rows 16 --allow-logit-diagnostic`
- result:
  - Exact row selection worked: `sft_dpo_delta_l35` replayed 4 configured row
    keys, and `sft_kto_h_lora_l35` replayed 2 configured row keys. The runner
    still defaults to balanced `max_rows` selection when exact row keys are not
    configured.
  - Top-k reporting worked: each logit diagnostic row now records
    `baseline_top_k` and `intervention_top_k` with rank, token id/text, logit,
    and probability; this run used `top_k: 10`.
  - `sft_dpo_delta_l35`: activation addition changed `4/4` top-1 tokens, while
    subtraction changed `0/4`. The Wookey/Stone row moved `That -> Stone`, the
    Ann Summers/Span row moved `I -> Span`, and the Henley row moved
    `July -> August`.
  - `sft_kto_h_lora_l35`: activation subtraction changed `2/2` top-1 tokens,
    moving Miss World `I -> England` and Copernicus `Earth -> The`; addition
    changed `0/2`.
  - Answer-alias skipped-target metadata is now visible. Multi-token-only rows
    report zero answer-alias probability mass with skipped target counts rather
    than dropping the answer-alias group.
- interpretation:
  - Exact-row replay confirms the prior top-1 changes were concentrated in the
    intended rows, but the movement still does not look like a useful humility
    control. The strongest changes push toward answer-like tokens or corrupt a
    known answer rather than increasing appropriate unknown abstention while
    preserving known correctness.
  - The top-k traces make the mechanism clearer: on Miss World, subtraction
    promotes `England` over `I` while the correct answer alias `Sweden` is not
    in top-k; on Henley, addition shifts mass from `July` toward `August`.
- limitations:
  - No generation was run in this checkpoint.
  - Wrong-layer, random-direction, and shuffled-label controls remain
    unimplemented in this runner path.
  - Docker emitted the existing tokenizer regex warning; token-level conclusions
    should keep that caveat until the model-load path is fixed or verified.

### 011-result - Wrong-Layer And Random Controls Complete

- at: `2026-06-19T01:40:00Z`
- kind: `result`
- summary: Added two scientifically valid logit-diagnostic controls to the
  Phase 3 runner: wrong-layer with configured offset `-1` and deterministic
  random matched-norm with seed `20260619`. Shuffled-label remained skipped
  because there is no shuffled-label direction artifact or valid derivation in
  the current checked-in runner path. Exact-row logit diagnostics reran with no
  generation.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_causal_pilot_changed_row_probability_slice.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T013022Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_changed_row_probability_slice/run_20260619T013300Z`
- commands:
  - `python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py experiment/phase1/probe/phase3_causal_pilot_aggregate.py`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm --max-rows 16 --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,activation_subtraction,wrong_layer,random_matched_norm --max-rows 16 --allow-logit-diagnostic`
- result:
  - `sft_dpo_delta_l35`: real activation addition changed `4/4` top-1 rows;
    wrong-layer changed `3/4`; random matched-norm changed `0/4`. This weakens
    any layer-specific interpretation for the DPO-delta candidate until a
    nearby-layer panel separates source-layer from adjacent-layer behavior.
  - `sft_kto_h_lora_l35`: real activation subtraction changed `2/2` top-1
    rows; wrong-layer changed `0/2`; random matched-norm changed `0/2`. This is
    a cleaner control separation than the DPO-delta case, though the direction
    still moves toward answer tokens rather than appropriate abstention.
  - Random matched-norm rows and manifests record seed `20260619`. Wrong-layer
    rows record source layer `35` and applied layer `34`.
- interpretation:
  - Random matched-norm did not match the real-direction top-1 effects on this
    exact row slice, so the effects are not explained by arbitrary same-norm
    vector injection alone.
  - Wrong-layer partly matches DPO-delta addition, so the DPO-delta effect is
    not yet source-layer-specific. Wrong-layer does not match KTO-h_lora
    subtraction on this slice.
  - This remains Tier 2 exploratory local evidence only; it is not Phase 1
    headline evidence, arm ranking, or reward-loop input.
- limitations:
  - No generation was run.
  - Shuffled-label was not implemented; no real shuffled-label artifact or
    valid checked-in derivation was found in this runner path.
  - The existing tokenizer regex warning still applies to fine-grained
    tokenization interpretation.

### 012-result - DPO-Delta Nearby-Layer Logit Panel Complete

- at: `2026-06-19T09:32:00Z`
- kind: `result`
- summary: Ran a bounded, logit-only nearby-layer panel for
  `sft_dpo_delta_l35` on the configured exact rows, coefficient `50`, with no
  generation and no cloud. The panel compared source-layer activation addition
  at layer `35` against wrong-layer applications at layers `33`, `34`, and
  `36`. Offset `+2` was attempted but failed closed because it maps to layer
  `37`, beyond the model's `36` decoder blocks.
- evidence:
  - `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m2.yaml`
  - `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_m1.yaml`
  - `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p1.yaml`
  - `experiment/phase1/probe/config/phase3_dpo_delta_l35_nearby_layer_offset_p2.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_m2/run_20260619T091724Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_m1/run_20260619T091933Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_dpo_delta_l35_nearby_layer_panel/offset_p1/run_20260619T092130Z`
- commands:
  - `python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py experiment/phase1/probe/phase3_causal_pilot_aggregate.py`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_m2.yaml --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,wrong_layer --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_m1.yaml --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,wrong_layer --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_p1.yaml --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,wrong_layer --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_p2.yaml --candidate sft_dpo_delta_l35 --coefficients 50 --controls no_vector_baseline,activation_addition,wrong_layer --allow-logit-diagnostic`
- result:
  - CPU gate passed: focused runner/dry-run tests reported `49 passed`, compile
    passed, and config validation found offsets `[-2, -1, 1, 2]`.
  - Docker/GPU gate passed before launch: old Unsloth containers were
    `sleep infinity`, GPU memory/utilization were idle, and `nvidia-smi` showed
    no compute processes.
  - Source-layer activation addition reproduced `4/4` top-1 changes in each
    completed run. Nearby wrong-layer controls changed `3/4` top-1 rows at
    offset `-2` (applied layer `33`), `3/4` at offset `-1` (applied layer
    `34`), and `3/4` at offset `+1` (applied layer `36`).
  - Qualitatively, wrong-layer controls often moved the same row-level tokens:
    `I -> Span` appeared at all three nearby layers; `That -> Stone` appeared
    at layers `34` and `36`; `July/August` remained a near-tie with small
    ordering changes; the Dr/Doctor/A row moved within the same local top-k
    cluster.
  - Probability slices were also similar rather than source-layer-specific.
    Mean refusal-opener probability deltas were source addition `-0.049596`,
    wrong-layer `-0.044377` at layer `33`, `-0.045936` at layer `34`, and
    `-0.057769` at layer `36`. Answer-alias movement was driven by the
    single-token Henley row under the current tokenization guard.
- interpretation:
  - This weakens a source-layer-specific interpretation for
    `sft_dpo_delta_l35`. The effect is not explained by the earlier random
    matched-norm control, but it is also not localized cleanly to layer `35`:
    nearby wrong-layer applications repeatedly reproduce most top-1 movement
    and comparable refusal-probability movement.
  - The movement still does not look like a useful humility-control signal:
    it tends to push answer-like tokens or corrupt a known answer, while
    reducing refusal-opener mass on these exact rows.
  - This remains Tier 2 exploratory local mechanism evidence only; it is not
    Phase 1 headline evidence, arm ranking, generation-sweep justification, or
    reward-loop input.
- limitations:
  - No generation was run.
  - Offset `+2` did not complete because layer `37` is invalid for this model.
  - Docker emitted the existing tokenizer regex warning; token-level
    interpretation keeps that caveat.

### 013-result - KTO H-Lora Sign-Matched Nearby-Layer Panel Complete

- at: `2026-06-19T09:45:00Z`
- kind: `result`
- summary: Added the minimal logit-diagnostic-only
  `wrong_layer_subtraction` control, preserving the existing positive
  `wrong_layer` semantics, then ran a bounded sign-matched nearby-layer panel
  for `sft_kto_h_lora_l35`. The panel used exact configured changed rows,
  coefficient `50`, no generation, and no cloud.
- evidence:
  - `experiment/phase1/probe/phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py`
  - `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m2.yaml`
  - `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_m1.yaml`
  - `experiment/phase1/probe/config/phase3_kto_h_lora_l35_nearby_layer_offset_p1.yaml`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_m2/run_20260619T093626Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_m1/run_20260619T093834Z`
  - `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_kto_h_lora_l35_nearby_layer_panel/offset_p1/run_20260619T094047Z`
- commands:
  - `python -m pytest experiment/phase1/probe/tests/test_phase3_causal_pilot_runner.py experiment/phase1/probe/tests/test_phase3_causal_pilot_dry_run.py -q`
  - `python -m py_compile experiment/phase1/probe/phase3_causal_pilot_runner.py experiment/phase1/probe/phase3_causal_pilot_sweep.py experiment/phase1/probe/phase3_causal_pilot_aggregate.py`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_m2.yaml --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_subtraction,wrong_layer_subtraction --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_m1.yaml --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_subtraction,wrong_layer_subtraction --allow-logit-diagnostic`
  - `docker run --rm --gpus all --ipc=host --entrypoint python ... phase3_causal_pilot_runner.py --mode logit_diagnostic --config ...offset_p1.yaml --candidate sft_kto_h_lora_l35 --coefficients 50 --controls no_vector_baseline,activation_subtraction,wrong_layer_subtraction --allow-logit-diagnostic`
- result:
  - Implementation validation passed: focused runner/dry-run tests reported
    `50 passed`, compile passed, and config validation found offsets
    `[-2, -1, 1]` with negative `wrong_layer_subtraction` coefficients.
  - Docker/GPU gate passed before launch: old Unsloth containers were
    `sleep infinity`, GPU memory/utilization were idle, and `nvidia-smi` showed
    no compute processes. GPU was idle again after the runs.
  - Source-layer activation subtraction at layer `35` changed `2/2` top-1
    rows, reproducing `I -> England` and `Earth -> The`.
  - Sign-matched wrong-layer subtraction changed `2/2` rows at offset `-2`
    (applied layer `33`), `2/2` rows at offset `-1` (applied layer `34`), and
    `1/2` rows at offset `+1` (applied layer `36`).
  - Top-k movement was qualitatively similar at offsets `-2` and `-1`:
    `England` overtook `I` on the Miss World row, and `The` overtook `Earth`
    on the Copernicus row. At offset `+1`, `England` overtook `I`, while
    `Earth` remained top-1 on the Copernicus row.
  - Refusal-opener probability moved down for both source and nearby-layer
    subtraction. Mean deltas were source `-0.043785`, wrong-layer layer `33`
    `-0.069618`, wrong-layer layer `34` `-0.060726`, and wrong-layer layer
    `36` `-0.061368`. Answer-alias deltas were effectively zero under the
    current single-token alias guard.
- interpretation:
  - With sign-matched controls, `sft_kto_h_lora_l35` no longer remains cleanly
    separated from nearby wrong-layer controls. The earlier apparent separation
    was at least partly a sign-mismatch artifact.
  - The movement remains answer-like and not abstention-aligned: subtraction
    reduces refusal-opener mass and pushes answer-like top tokens on these
    exact rows.
  - This remains Tier 2 exploratory local mechanism evidence only; it is not
    Phase 1 headline evidence, arm ranking, generation-sweep justification, or
    reward-loop input.
- limitations:
  - No generation was run.
  - The panel did not test offset `+2`, because prior work established layer
    `37` is invalid for this model.
  - Docker emitted the existing tokenizer regex warning; token-level
    interpretation keeps that caveat.
