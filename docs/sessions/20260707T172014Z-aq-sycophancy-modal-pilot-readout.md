---
schema_version: research-session/v1
session_id: 20260707T172014Z-aq-sycophancy-modal-pilot-readout
title: AQ sycophancy Modal pilot readout
status: active
created_at: '2026-07-07T17:20:14Z'
updated_at: '2026-07-07T20:59:02Z'
phase: phase1
question: Can the AQ answer-sycophancy pilot produce a separable activation readout
  on official Qwen3-4B, and is the row pool sufficient to license steering?
tags:
- aq
- sycophancy
- modal
- mechinterp
run_ids:
- ap-JqoCvvgwbGHSKqkCux9CcM
- fc-01KWYMPM3A5P5QFPZD29AGXS9M
- ap-0gq6CSDwbQSV12mwChhlSe
- fc-01KWYT9RT4M79C0CWGXYGGPKMS
- ap-AhHmUkNR7ruGzGW66vikmM
- fc-01KWYTYS8F050TK9E072C14JAZ
- ap-Gk0B98l6fRfLflfcF3L2LQ
- fc-01KWZ2YK61JG04RER3QJV9ZM9B
- ap-AvZVf2c46omIDNKsFO1Rv3
- fc-01KWZ4AA48QFEFS073MX91VWGD
trajectory:
  anchor: docs/research-trajectory.md
  current_position: AQ is an exploratory sycophancy read-vs-write cell, separate from
    the locked Phase 1 headline matrix.
  changed_by_session: R1 found an underpowered readout lead; r2 cleared AQ-G0 and
    recovered a larger-pool readout direction. Local recovered-artifact diagnostics
    pass AQ-G1 but show a strong anchor prompt-condition confound. A readout-only
    hydra/isolation panel found that paired deltas survive, broad condition removal
    alone does not kill the signal, but behavior/correctness residualization largely
    attenuates it. The first Modal actuator launch exposed a smoke-row ordering issue;
    the corrected launch passed smoke and ran full arms, but AQ-G2 specificity failed
    against the permuted control, supporting a read/write decoupling null with a regenerated-baseline
    caveat.
checkpoints:
- id: 001-launch
  at: '2026-07-07T17:20:14Z'
  kind: launch
  title: Modal smoke and readout launched
  summary: User authorized the AQ Modal smoke/readout path on official base Qwen3-4B,
    not a Synaptic-trained variant; the final readout run used repo commit d5f26f4cb
    on Modal A10G.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  - experiments/aq-sycophancy-activation-actuator/AMENDMENT.md
  run_ids:
  - ap-JqoCvvgwbGHSKqkCux9CcM
  commands:
  - modal run --detach experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
    --readout --repo-commit=d5f26f4cb
  decisions:
  - Use official Qwen/Qwen3-4B at revision 1cfa9a7208912126459214e8b04321603b3df60c.
  next_steps: []
  signals: {}
- id: 002-result
  at: '2026-07-07T17:20:14Z'
  kind: result
  title: Readout completed with separable pilot direction
  summary: Extraction captured 32/32 answered rows; probe-fit selected a normalized
    layer-20 direction with AUROC 1.00 on 9 positive and 7 negative pilot labels.
    Other AUROCs were L12=0.70, L16=0.80, L17=0.90, and L24=0.90.
  evidence:
  - professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json
  - professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/extraction/manifest.json
  run_ids:
  - fc-01KWYMPM3A5P5QFPZD29AGXS9M
  commands: []
  decisions: []
  next_steps: []
  signals:
    selected_layer: 20
    auroc: 1.0
    n_positive: 9
    n_negative: 7
- id: 003-interpretation
  at: '2026-07-07T17:20:14Z'
  kind: interpretation
  title: AQ-G0 failed; no actuator verdict
  summary: The pilot supports the user's expectation that an answer-sycophancy readout
    exists, but AQ-G0 requires at least 20 positive and 20 negative incorrect-hint
    labels and this run produced only 9/7. Therefore the registered gate is underpowered/void
    and the actuator stage should wait for a scaled or revised row-pool plan.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/gates.yaml
  - experiments/aq-sycophancy-activation-actuator/row_pool.yaml
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  run_ids: []
  commands: []
  decisions:
  - Do not treat the layer-20 AUROC as AQ-G1 pass under the registered gate because
    AQ-G0 did not pass.
  next_steps:
  - Scale or revise the row-pool construction to satisfy AQ-G0 before any actuator
    launch.
  - Re-run readout on the scaled pool and then ask for explicit actuator launch approval.
  signals: {}
- id: 004-decision
  at: '2026-07-07T17:20:14Z'
  kind: decision
  title: Scale next AQ pass to 512 source rows
  summary: User requested a larger dataset, closer to 500 rows. The next AQ eval config
    was updated from limit 64 to limit 512, with Modal staging tags moved to r2 to
    keep scaled artifacts separate from the r1 pilot.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/eval_16bit_sycophancy_answer.yaml
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  - experiments/aq-sycophancy-activation-actuator/row_pool.yaml
  run_ids: []
  commands: []
  decisions:
  - Use `limit: 512` for the next AQ row-pool smoke/readout pass.
  - Keep actuator launch blocked until r2 scored rows clear AQ-G0.
  next_steps:
  - Validate and dry-run the r2 wrapper.
  - After user approval, launch r2 smoke/readout on Modal.
  signals: {}
- id: 005-r2-smoke
  at: '2026-07-07T18:26:29Z'
  kind: result
  title: R2 smoke cleared AQ-G0
  summary: 'Scaled r2 smoke at limit 512 completed on Modal A10G against official
    Qwen3-4B at repo commit 9f661c015. It produced 512 scored rows and a 256-row pool
    with 128 probe labels: 68 positive and 60 negative, clearing the 20/20 AQ-G0 minimum.'
  evidence:
  - professorsynapse/eh-al-prep-staging:aq-sycophancy-actuator-smoke-r2/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/row_pool_summary.json
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  run_ids:
  - ap-0gq6CSDwbQSV12mwChhlSe
  - fc-01KWYT9RT4M79C0CWGXYGGPKMS
  commands:
  - modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --repo-commit=9f661c015 --cost-cap-usd=10
  decisions:
  - AQ-G0 is no longer the blocker for the scaled r2 pool.
  next_steps:
  - Compare r2 readout against r1.
  signals:
    paired_question_count: 128
    row_pool_count: 256
    label_count: 128
    n_positive: 68
    n_negative: 60
- id: 006-r2-readout-partial
  at: '2026-07-07T18:26:29Z'
  kind: result
  title: R2 readout direction recovered; publish failed
  summary: R2 readout extracted and fit a direction, recovered from the Modal volume
    after HF artifact publication failed with 429 Too Many Requests from the dataset
    repo commit limit. The selected direction moved from r1 L20 to r2 L24; AUROC is
    0.846 on 68/60 labels, preserving signal but removing the r1 tiny-n perfect AUROC.
  evidence:
  - /ckpt/aq-sycophancy-readout-r2/data/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  run_ids:
  - ap-AhHmUkNR7ruGzGW66vikmM
  - fc-01KWYTYS8F050TK9E072C14JAZ
  commands:
  - modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --readout --repo-commit=9f661c015 --cost-cap-usd=10
  - modal app stop --yes ap-AhHmUkNR7ruGzGW66vikmM
  decisions:
  - Treat r2 as a computed readout with incomplete artifact publication, not as a
    clean DONE-marked run.
  - Do not launch actuator without fresh explicit approval.
  next_steps:
  - Retry publication only after the HF commit-rate window clears and the batch-upload
    wrapper commit is pushed.
  signals:
    selected_layer: 24
    auroc: 0.8458791208791208
    n_positive: 68
    n_negative: 60
    separation: 7.6320638677996335
    sigma: 4.152135594300958
- id: 007-wrapper-fix
  at: '2026-07-07T18:26:29Z'
  kind: decision
  title: Batch HF readout uploads
  summary: The AQ Modal wrapper now uploads directory artifacts with Hugging Face
    upload_folder instead of committing every extracted tensor individually, avoiding
    the 256-commits-per-hour failure mode on scaled readouts.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  run_ids: []
  commands:
  - python -m py_compile experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
  decisions:
  - Stop the stale Modal app that was retrying the old per-file uploader.
  next_steps:
  - Commit and push the wrapper fix plus r2 documentation.
  signals: {}
- id: 008-local-diagnostics
  at: '2026-07-07T19:06:07Z'
  kind: observation
  title: R2 local diagnostics pass AQ-G1 with confounds
  summary: Local CPU diagnostics over recovered r2 artifacts recomputed the selected
    layer-24 anchor readout with OOF AUROC 0.819 and bootstrap 95% CI [0.742, 0.886],
    so AQ-G1 passes as a readout screen. The same score almost perfectly separates
    incorrect-hint from neutral prompts at the anchor position (AUROC 0.988), while
    answer_end loses both label signal and prompt condition separation. Inside baseline-incorrect
    rows only, OOF AUROC 0.723 for wrong-hint-followed vs other wrong answers suggests
    some sycophancy-specific signal beyond generic wrongness, but the readout is not
    clean enough to treat as causal evidence.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py
  - experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  run_ids: []
  commands:
  - py -3.12 experiments\aq-sycophancy-activation-actuator\analyze_aq_readout.py
  decisions:
  - Treat AQ-G1 as passed for the r2 readout screen, not as causal evidence.
  - Keep actuator launch blocked pending explicit approval.
  next_steps:
  - If launching an actuator, carry strict neutral/correctness guardrails and a manual
    audit because the anchor readout is prompt-condition confounded.
  signals:
    selected_layer: 24
    oof_auroc: 0.8186274509803921
    bootstrap_ci_lo: 0.7421499970470116
    bootstrap_ci_hi: 0.8859277708592778
    condition_anchor_auroc: 0.98773193359375
    condition_answer_end_auroc: 0.45294189453125
    incorrect_only_oof_auroc: 0.7225935828877005
- id: 009-hydra-isolation-plan
  at: '2026-07-07T19:17:52Z'
  kind: planning
  title: Plan readout-only hydra isolation panel
  summary: Before any actuator launch, run a local readout-only panel to separate
    the current L24 answer-sycophancy signal from prompt-condition, correctness, refusal,
    and generic wrongness confounds. The panel should compare raw anchor readout,
    paired incorrect-minus-neutral delta readout, condition-axis residualized readout,
    condition+correctness+refusal/length residualized readout, an incorrect-only matched/sliced
    readout, and a small one-vs-rest component map for wrong-hint-following, correction/resistance,
    refusal/avoidance, generic wrongness, and correct answering.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py
  - experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json
  run_ids: []
  commands: []
  decisions:
  - Treat this as local screening/localization only, not actuator or causal evidence.
  - Prefer paired/residualized controls over adding more rows before interpreting
    the L24 signal.
  next_steps:
  - Extend `analyze_aq_readout.py` with paired-delta, residualized, incorrect-only,
    and hydra component diagnostics.
  - Run the CPU-only analysis on the recovered r2 artifacts.
  signals: {}
- id: 010-hydra-isolation-result
  at: '2026-07-07T19:23:11Z'
  kind: observation
  title: Hydra isolation panel run locally
  summary: The readout-only isolation panel ran on the recovered r2 artifacts. Raw
    L24 anchor OOF AUROC stayed 0.819. Matched incorrect-minus-neutral paired deltas
    survived at AUROC 0.778, and projecting out the broad incorrect-hint-vs-neutral
    condition axis left AUROC 0.815. Adding fold-local residualization for correctness,
    refusal, answer length, prompt length, and parsed confidence attenuated the readout
    to AUROC 0.600. Incorrect-only refits were weaker (raw 0.626, condition-residualized
    0.614), while length/confidence-matched incorrect-only 22/22 slices were stronger
    but small (raw 0.729, condition-residualized 0.725). The component map says the
    residualized signal is cleaner for hint resistance/correction (`hint_resisted_correct`
    AUROC 0.784) than for hint following (`hint_followed` AUROC 0.691); generic hinted
    wrongness collapses below chance (0.435).
  evidence:
  - experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py
  - experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json
  - experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/hydra_component_map.csv
  run_ids: []
  commands:
  - py -3.12 experiments\aq-sycophancy-activation-actuator\analyze_aq_readout.py
  decisions:
  - Interpret the L24 AQ readout as a mixed prompt-conflict/correctness-resistance
    structure, not a clean standalone sycophancy actuator.
  - Keep actuator launch blocked pending explicit approval and use strict guardrails
    if it is later launched.
  next_steps:
  - Consider token-timeline or richer label panels before actuator launch if the goal
    is mechanism mapping rather than fast steering.
  signals:
    raw_anchor_oof_auroc: 0.8186274509803921
    paired_delta_oof_auroc: 0.7781862745098039
    condition_residualized_oof_auroc: 0.8154411764705882
    condition_behavior_residualized_oof_auroc: 0.5997549019607843
    incorrect_only_raw_oof_auroc: 0.6263368983957219
    incorrect_only_condition_residualized_oof_auroc: 0.6143048128342246
    incorrect_only_matched_raw_oof_auroc: 0.7293388429752066
    incorrect_only_matched_condition_residualized_oof_auroc: 0.7252066115702479
    hydra_hint_followed_residualized_oof_auroc: 0.690863579474343
    hydra_hint_resisted_correct_residualized_oof_auroc: 0.7839208112023177
    hydra_hint_other_wrong_residualized_oof_auroc: 0.4349261849261849
- id: 011-actuator-prep
  at: '2026-07-07T19:37:00Z'
  kind: infrastructure
  title: Modal actuator path prepared
  summary: Shifted from cross-axis analysis toward actuation. Added an actuator row
    materializer that enriches the frozen r2 row pool with selector metadata from
    readout diagnostics, moved the steer cell to consume `analysis/actuator_rows.jsonl`,
    removed the stale readout-floor gate from post-steering gates because AQ-G1 is
    already adjudicated offline, and added a Modal `--actuator` path. The actuator
    function restores the r2 readout checkpoint from the Modal volume, re-runs readout
    diagnostics if needed, prepares actuator rows, runs `mechinterp steer`, scores
    gates, checkpoints outputs, and uploads actuator artifacts under `aq-sycophancy-actuator-r2/artifacts`.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/prepare_aq_actuator_rows.py
  - experiments/aq-sycophancy-activation-actuator/cell.yaml
  - experiments/aq-sycophancy-activation-actuator/gates.yaml
  - experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py
  run_ids: []
  commands:
  - py -3.12 experiments\aq-sycophancy-activation-actuator\prepare_aq_actuator_rows.py
  - py -3.12 -c "from MechInterp.config import load_steer_config; c=load_steer_config('../experiments/aq-sycophancy-activation-actuator/cell.yaml');
    print('cell ok', c.surface.rows_path, len(c.arms))"
  - py -3.12 -c "from MechInterp.stats.evaluator import load_gates_config; g=load_gates_config('../experiments/aq-sycophancy-activation-actuator/gates.yaml');
    print('gates ok', len(g['gates']), [x['name'] for x in g['gates']])"
  - py -3.12 experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --dry-run --actuator --repo-commit=3041c5dab --cost-cap-usd=10
  - modal run experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --dry-run --actuator --repo-commit=e108f15f4 --cost-cap-usd=10
  decisions:
  - Keep AQ-G1/readout-floor adjudication in the readout diagnostics rather than in
    post-steering `gates.yaml`.
  - Do not launch the live Modal actuator until the user gives explicit approval naming
    AQ, Modal A10G, official Qwen/Qwen3-4B, and the cost cap.
  next_steps:
  - Commit and push the actuator-prep changes.
  - Request explicit live launch approval.
  signals:
    actuator_rows: 256
    actuator_probe_rows: 128
    actuator_rows_with_selector_scores: 128
    gate_count: 3
    actuator_run_tag: aq-sycophancy-actuator-r2
    modal_dry_run_app: ap-34vtwn4UfC8VAH01CqgdKN
- id: 012-actuator-smoke-fail
  at: '2026-07-07T20:19:23Z'
  kind: gate
  title: Modal actuator launch stopped at smoke gate
  summary: User-approved live actuator launch ran on Modal A10G against official Qwen/Qwen3-4B
    at repo commit 440b88ab6, but `mechinterp steer` refused the full arms during
    smoke. The write target was reached within tolerance, but parity/offtarget isolation
    failed (`offtarget_abs_max=7.2005`, `gen_stream_fired=null`), so no full `rows_out.jsonl`,
    AQ-G2, or AQ-G3 behavioral result exists.
  evidence:
  - experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  - experiments/aq-sycophancy-activation-actuator/AMENDMENT.md
  run_ids:
  - ap-Gk0B98l6fRfLflfcF3L2LQ
  - fc-01KWZ2YK61JG04RER3QJV9ZM9B
  commands:
  - modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --actuator --repo-commit=440b88ab6 --cost-cap-usd=10
  - modal volume get eh-aq-sycophancy-smoke-logs /ckpt/aq-sycophancy-actuator-r2/data/experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json
    experiments\aq-sycophancy-activation-actuator\analysis\rows_out.jsonl.smoke_ok.json
    --force
  decisions:
  - Treat this as a smoke/instrument isolation failure, not as evidence for or against
    AQ-G2/AQ-G3.
  - Do not use `--force-full-run`; debug the smoke readback first.
  next_steps:
  - Run a smoke-level diagnostic for the Qwen3-4B `anchor_onward` + `gen_stream` intervention
    path, likely comparing narrower position targeting and additive-vs-erase/write
    laws before any full actuator relaunch.
  signals:
    smoke_passed: false
    write_ok: true
    parity_ok: false
    max_write_error: 0.010230378732117629
    offtarget_abs_max: 7.2005182495340705
    gen_stream_fired: null
- id: 013-actuator-r2-result
  at: '2026-07-07T20:59:02Z'
  kind: result
  title: Corrected Modal actuator completed; AQ-G2 failed
  summary: 'The smoke-row ordering fix was committed as a42b64a42 and relaunched on
    Modal A10G. Smoke passed with gen_stream_fired=true and offtarget_abs_max=0, the
    full six-arm run completed 1536 rows, and artifacts uploaded under aq-sycophancy-actuator-r2.
    Score-gates returned 5: reach and neutral guardrail passed, but anti-sycophancy
    versus permuted control failed with diff 0.0 and CI [-5, 5]. Regenerated no-op
    baseline drifted materially, with only 30/68 source-followed rows still wrong-hint-matching.'
  evidence:
  - experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl
  - experiments/aq-sycophancy-activation-actuator/analysis/gates_report.json
  - experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json
  - experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md
  - experiments/aq-sycophancy-activation-actuator/AMENDMENT.md
  run_ids:
  - ap-AvZVf2c46omIDNKsFO1Rv3
  - fc-01KWZ4AA48QFEFS073MX91VWGD
  commands:
  - modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py
    --actuator --repo-commit=a42b64a42 --cost-cap-usd=10
  - modal volume get eh-aq-sycophancy-smoke-logs /ckpt/aq-sycophancy-actuator-r2/data/experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl
    experiments\aq-sycophancy-activation-actuator\analysis\rows_out.jsonl --force
  decisions:
  - Treat the actuator result as AQ-G2 failure / exploratory decoupling null, not
    as a clean behavioral success.
  - Preserve the regenerated-baseline drift caveat before any formal resolution.
  next_steps:
  - Decide whether AQ should resolve as an exploratory null or whether a redesigned
    actuator surface should first align baseline regeneration with the source eval.
  signals:
    smoke_passed: true
    gen_stream_fired: true
    offtarget_abs_max: 0.0
    rows_out: 1536
    score_gates_returncode: 5
    overall_pass: false
    subtract_high_reach_count: 36
    anti_sycophancy_control_diff: 0.0
    anti_sycophancy_control_ci_lo: -5.0
    anti_sycophancy_control_ci_hi: 5.0
    regenerated_baseline_wrong_hint_matches: 30
    source_followed_rows: 68
legacy_session:
  id: '0043'
  path: docs/sessions/0043 - aq-sycophancy-modal-pilot-readout.md
---
# AQ sycophancy Modal pilot readout

## Question

Can the AQ answer-sycophancy pilot produce a separable activation readout on
official Qwen3-4B, and is the row pool sufficient to license steering?

## Trajectory Position

AQ is a tier-2 exploratory sycophancy read-vs-write cell, separate from the
locked Phase 1 headline matrix. This session records a pilot/smoke readout, not
a resolved amendment verdict.

## Summary

The r1 Modal pilot found a strong but underpowered activation readout: layer 20
AUROC 1.00 over 9 positive and 7 negative labels. The scaled r2 pass fixed the
AQ-G0 row-count problem, producing 68 positive and 60 negative labels, and still
found a separable readout: selected layer 24, AUROC 0.846, separation 7.63,
sigma 4.15. Local recovered-artifact diagnostics pass AQ-G1 on OOF scores
(AUROC 0.819, 95% CI [0.742, 0.886]) but show a strong anchor prompt-condition
confound (`incorrect_hint` vs neutral AUROC 0.988). The direction is available
locally from the Modal volume. The readout-only hydra isolation panel found
that paired deltas survive (AUROC 0.778) and broad hint-vs-neutral condition
removal alone does not kill the signal (AUROC 0.815), but residualizing
correctness/refusal/length/confidence attenuates it (AUROC 0.600). The
remaining structure looks more like prompt conflict plus correction/resistance
than a clean standalone sycophancy actuator. The first actuator launch exposed a
smoke-row ordering issue; after fixing that, the corrected Modal run passed
smoke and completed full arms, but AQ-G2 specificity failed against the permuted
control. The current actuator result is therefore an exploratory decoupling null
with a regenerated-baseline caveat, not a clean behavioral success.

## Checkpoints

### 001-launch - Modal smoke and readout launched

- at: `2026-07-07T17:20:14Z`
- kind: `launch`
- summary: User authorized the AQ Modal smoke/readout path on official base Qwen3-4B, not a Synaptic-trained variant; the final readout run used repo commit d5f26f4cb on Modal A10G.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
  - `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md`
- run ids:
  - `ap-JqoCvvgwbGHSKqkCux9CcM`
- commands:
  - `modal run --detach experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py --readout --repo-commit=d5f26f4cb`
- decisions:
  - Use official `Qwen/Qwen3-4B` at revision `1cfa9a7208912126459214e8b04321603b3df60c`.

### 002-result - Readout completed with separable pilot direction

- at: `2026-07-07T17:20:14Z`
- kind: `result`
- summary: Extraction captured 32/32 answered rows; probe-fit selected a normalized layer-20 direction with AUROC 1.00 on 9 positive and 7 negative pilot labels. Other AUROCs were L12=0.70, L16=0.80, L17=0.90, and L24=0.90.
- evidence:
  - `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json`
  - `professorsynapse/eh-al-prep-staging:aq-sycophancy-readout-r1/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/extraction/manifest.json`
- run ids:
  - `fc-01KWYMPM3A5P5QFPZD29AGXS9M`

### 003-interpretation - AQ-G0 failed; no actuator verdict

- at: `2026-07-07T17:20:14Z`
- kind: `interpretation`
- summary: The pilot supports the user's expectation that an answer-sycophancy readout exists, but AQ-G0 requires at least 20 positive and 20 negative incorrect-hint labels and this run produced only 9/7. Therefore the registered gate is underpowered/void and the actuator stage should wait for a scaled or revised row-pool plan.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/gates.yaml`
  - `experiments/aq-sycophancy-activation-actuator/row_pool.yaml`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
- decisions:
  - Do not treat the layer-20 AUROC as AQ-G1 pass under the registered gate because AQ-G0 did not pass.
- next steps:
  - Scale or revise the row-pool construction to satisfy AQ-G0 before any actuator launch.
  - Re-run readout on the scaled pool and then ask for explicit actuator launch approval.

### 004-decision - Scale next AQ pass to 512 source rows

- at: `2026-07-07T17:20:14Z`
- kind: `decision`
- summary: User requested a larger dataset, closer to 500 rows. The next AQ eval config was updated from `limit: 64` to `limit: 512`, with Modal staging tags moved to r2 to keep scaled artifacts separate from the r1 pilot.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/eval_16bit_sycophancy_answer.yaml`
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
  - `experiments/aq-sycophancy-activation-actuator/row_pool.yaml`
- decisions:
  - Use `limit: 512` for the next AQ row-pool smoke/readout pass.
  - Keep actuator launch blocked until r2 scored rows clear AQ-G0.
- next steps:
  - Validate and dry-run the r2 wrapper.
  - After user approval, launch r2 smoke/readout on Modal.

### 005-r2-smoke - R2 smoke cleared AQ-G0

- at: `2026-07-07T18:26:29Z`
- kind: `result`
- summary: Scaled r2 smoke at `limit: 512` completed on Modal A10G against official Qwen3-4B at repo commit `9f661c015`. It produced 512 scored rows and a 256-row pool with 128 probe labels: 68 positive and 60 negative, clearing the 20/20 AQ-G0 minimum.
- evidence:
  - `professorsynapse/eh-al-prep-staging:aq-sycophancy-actuator-smoke-r2/artifacts/experiments/aq-sycophancy-activation-actuator/analysis/row_pool_summary.json`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
- run ids:
  - `ap-0gq6CSDwbQSV12mwChhlSe`
  - `fc-01KWYT9RT4M79C0CWGXYGGPKMS`
- decisions:
  - AQ-G0 is no longer the blocker for the scaled r2 pool.

### 006-r2-readout-partial - R2 readout direction recovered; publish failed

- at: `2026-07-07T18:26:29Z`
- kind: `result`
- summary: R2 readout extracted and fit a direction, recovered from the Modal volume after HF artifact publication failed with `429 Too Many Requests` from the dataset repo commit limit. The selected direction moved from r1 L20 to r2 L24; AUROC is 0.846 on 68/60 labels, preserving signal but removing the r1 tiny-n perfect AUROC.
- evidence:
  - `/ckpt/aq-sycophancy-readout-r2/data/experiments/aq-sycophancy-activation-actuator/directions/sycophancy_answer_direction.json`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
- run ids:
  - `ap-AhHmUkNR7ruGzGW66vikmM`
  - `fc-01KWYTYS8F050TK9E072C14JAZ`
- decisions:
  - Treat r2 as a computed readout with incomplete artifact publication, not as a clean DONE-marked run.
  - Do not launch actuator without fresh explicit approval.

### 007-wrapper-fix - Batch HF readout uploads

- at: `2026-07-07T18:26:29Z`
- kind: `decision`
- summary: The AQ Modal wrapper now uploads directory artifacts with Hugging Face `upload_folder` instead of committing every extracted tensor individually, avoiding the 256-commits-per-hour failure mode on scaled readouts.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
- decisions:
  - Stop the stale Modal app that was retrying the old per-file uploader.

### 008-local-diagnostics - R2 local diagnostics pass AQ-G1 with confounds

- at: `2026-07-07T19:06:07Z`
- kind: `observation`
- summary: Local CPU diagnostics over recovered r2 artifacts recomputed the selected layer-24 anchor readout with OOF AUROC 0.819 and bootstrap 95% CI [0.742, 0.886], so AQ-G1 passes as a readout screen. The same score almost perfectly separates incorrect-hint from neutral prompts at the anchor position (AUROC 0.988), while `answer_end` loses both label signal and prompt condition separation. Inside baseline-incorrect rows only, OOF AUROC 0.723 for wrong-hint-followed vs other wrong answers suggests some sycophancy-specific signal beyond generic wrongness, but the readout is not clean enough to treat as causal evidence.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py`
  - `experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
- commands:
  - `py -3.12 experiments\aq-sycophancy-activation-actuator\analyze_aq_readout.py`
- decisions:
  - Treat AQ-G1 as passed for the r2 readout screen, not as causal evidence.
  - Keep actuator launch blocked pending explicit approval.

### 009-hydra-isolation-plan - Plan readout-only hydra isolation panel

- at: `2026-07-07T19:17:52Z`
- kind: `planning`
- summary: Before any actuator launch, run a local readout-only panel to separate the current L24 answer-sycophancy signal from prompt-condition, correctness, refusal, and generic wrongness confounds. The panel should compare raw anchor readout, paired incorrect-minus-neutral delta readout, condition-axis residualized readout, condition+correctness+refusal/length residualized readout, an incorrect-only matched/sliced readout, and a small one-vs-rest component map for wrong-hint-following, correction/resistance, refusal/avoidance, generic wrongness, and correct answering.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py`
  - `experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json`
- decisions:
  - Treat this as local screening/localization only, not actuator or causal evidence.
  - Prefer paired/residualized controls over adding more rows before interpreting the L24 signal.
  - Keep actuator launch blocked pending explicit approval.

### 010-hydra-isolation-result - Hydra isolation panel run locally

- at: `2026-07-07T19:23:11Z`
- kind: `observation`
- summary: The readout-only isolation panel ran on the recovered r2 artifacts. Raw L24 anchor OOF AUROC stayed 0.819. Matched incorrect-minus-neutral paired deltas survived at AUROC 0.778, and projecting out the broad incorrect-hint-vs-neutral condition axis left AUROC 0.815. Adding fold-local residualization for correctness, refusal, answer length, prompt length, and parsed confidence attenuated the readout to AUROC 0.600. Incorrect-only refits were weaker (raw 0.626, condition-residualized 0.614), while length/confidence-matched incorrect-only 22/22 slices were stronger but small (raw 0.729, condition-residualized 0.725). The component map says the residualized signal is cleaner for hint resistance/correction (`hint_resisted_correct` AUROC 0.784) than for hint following (`hint_followed` AUROC 0.691); generic hinted wrongness collapses below chance (0.435).
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/analyze_aq_readout.py`
  - `experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/summary.json`
  - `experiments/aq-sycophancy-activation-actuator/analysis/readout_diagnostics/hydra_component_map.csv`
- commands:
  - `py -3.12 experiments\aq-sycophancy-activation-actuator\analyze_aq_readout.py`
- decisions:
  - Interpret the L24 AQ readout as a mixed prompt-conflict/correctness-resistance structure, not a clean standalone sycophancy actuator.
  - Keep actuator launch blocked pending explicit approval and use strict guardrails if it is later launched.

### 011-actuator-prep - Modal actuator path prepared

- at: `2026-07-07T19:37:00Z`
- kind: `infrastructure`
- summary: Shifted from cross-axis analysis toward actuation. Added an actuator row materializer that enriches the frozen r2 row pool with selector metadata from readout diagnostics, moved the steer cell to consume `analysis/actuator_rows.jsonl`, removed the stale readout-floor gate from post-steering gates because AQ-G1 is already adjudicated offline, and added a Modal `--actuator` path. The actuator function restores the r2 readout checkpoint from the Modal volume, re-runs readout diagnostics if needed, prepares actuator rows, runs `mechinterp steer`, scores gates, checkpoints outputs, and uploads actuator artifacts under `aq-sycophancy-actuator-r2/artifacts`.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/prepare_aq_actuator_rows.py`
  - `experiments/aq-sycophancy-activation-actuator/cell.yaml`
  - `experiments/aq-sycophancy-activation-actuator/gates.yaml`
  - `experiments/aq-sycophancy-activation-actuator/cloud/modal_aq_sycophancy_activation_actuator.py`
- commands:
  - `py -3.12 experiments\aq-sycophancy-activation-actuator\prepare_aq_actuator_rows.py`
  - `py -3.12 experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py --dry-run --actuator --repo-commit=3041c5dab --cost-cap-usd=10`
  - `modal run experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py --dry-run --actuator --repo-commit=e108f15f4 --cost-cap-usd=10`
- decisions:
  - Keep AQ-G1/readout-floor adjudication in the readout diagnostics rather than in post-steering `gates.yaml`.
  - Do not launch the live Modal actuator until the user gives explicit approval naming AQ, Modal A10G, official Qwen/Qwen3-4B, and the cost cap.
- note: The first Modal CLI dry-run attempt failed on Windows console encoding (`charmap` could not print a checkmark). Rerunning with `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` succeeded, initialized dry-run app `ap-34vtwn4UfC8VAH01CqgdKN`, printed the actuator spec, and exited without spawning GPU work.

### 012-actuator-smoke-fail - Modal actuator launch stopped at smoke gate

- at: `2026-07-07T20:19:23Z`
- kind: `gate`
- summary: User-approved live actuator launch ran on Modal A10G against official Qwen3-4B at repo commit `440b88ab6`, but `mechinterp steer` refused the full arms during smoke. The write target was reached within tolerance, but parity/offtarget isolation failed (`offtarget_abs_max=7.2005`, `gen_stream_fired=null`), so no full `rows_out.jsonl`, AQ-G2, or AQ-G3 behavioral result exists.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
  - `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md`
- run ids:
  - `ap-Gk0B98l6fRfLflfcF3L2LQ`
  - `fc-01KWZ2YK61JG04RER3QJV9ZM9B`
- commands:
  - `modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py --actuator --repo-commit=440b88ab6 --cost-cap-usd=10`
  - `modal volume get eh-aq-sycophancy-smoke-logs /ckpt/aq-sycophancy-actuator-r2/data/experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json experiments\aq-sycophancy-activation-actuator\analysis\rows_out.jsonl.smoke_ok.json --force`
- decisions:
  - Treat this as a smoke/instrument isolation failure, not as evidence for or against AQ-G2/AQ-G3.
  - Do not use `--force-full-run`; debug the smoke readback first.
- next steps:
  - Run a smoke-level diagnostic for the Qwen3-4B `anchor_onward` + `gen_stream` intervention path, likely comparing narrower position targeting and additive-vs-erase/write laws before any full actuator relaunch.

### 013-actuator-r2-result - Corrected Modal actuator completed; AQ-G2 failed

- at: `2026-07-07T20:59:02Z`
- kind: `result`
- summary: The smoke-row ordering fix was committed as `a42b64a42` and relaunched on Modal A10G. Smoke passed with `gen_stream_fired=true` and `offtarget_abs_max=0`, the full six-arm run completed 1536 rows, and artifacts uploaded under `aq-sycophancy-actuator-r2`. Score-gates returned 5: reach and neutral guardrail passed, but anti-sycophancy versus permuted control failed with diff 0.0 and CI [-5, 5]. Regenerated no-op baseline drifted materially, with only 30/68 source-followed rows still wrong-hint-matching.
- evidence:
  - `experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl`
  - `experiments/aq-sycophancy-activation-actuator/analysis/gates_report.json`
  - `experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl.smoke_ok.json`
  - `experiments/aq-sycophancy-activation-actuator/NOTEBOOK.md`
  - `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md`
- run ids:
  - `ap-AvZVf2c46omIDNKsFO1Rv3`
  - `fc-01KWZ4AA48QFEFS073MX91VWGD`
- commands:
  - `modal run --detach experiments\aq-sycophancy-activation-actuator\cloud\modal_aq_sycophancy_activation_actuator.py --actuator --repo-commit=a42b64a42 --cost-cap-usd=10`
  - `modal volume get eh-aq-sycophancy-smoke-logs /ckpt/aq-sycophancy-actuator-r2/data/experiments/aq-sycophancy-activation-actuator/analysis/rows_out.jsonl experiments\aq-sycophancy-activation-actuator\analysis\rows_out.jsonl --force`
- decisions:
  - Treat the actuator result as AQ-G2 failure / exploratory decoupling null, not as a clean behavioral success.
  - Preserve the regenerated-baseline drift caveat before any formal resolution.
- next steps:
  - Decide whether AQ should resolve as an exploratory null or whether a redesigned actuator surface should first align baseline regeneration with the source eval.
