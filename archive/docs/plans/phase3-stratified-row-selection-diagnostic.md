# Phase 3 Stratified Row-Selection Diagnostic Plan

Status: planning artifact, no live run
Created: 2026-06-19
Scope: Phase 3 exploratory mechanism prep only

## Purpose

Stable correct-refusal rows may be higher signal than changed rows for finding
abstention or humility controls. This plan records which current artifacts can
support exact row strata and what is still missing before a larger runner-ready
diagnostic.

This is not Phase 1 headline evidence, arm ranking, training feedback, or
reward-loop input.

## Artifact Feasibility

### Runner-Ready Probe-Key Artifacts

The Phase 3 local causal-pilot generation sweep has row-level outputs with
`probe_pool_row_key`, `label`, `refused`, `correct`, and `truthful`.

Usable source:

- `experiment/phase1/probe/qwen3-4b-instruct/causal_pilots/phase3_local_mech_interp_sweep/*/generation/*/scored_rows.jsonl`

Limits:

- It covers only the 16-row Phase 3 smoke slice.
- Baselines repeat across coefficient grid arms; deduplicate by
  `(candidate_label, probe_pool_row_key)`.
- This source can directly populate `selection.row_keys_by_candidate` in the
  current Phase 3 runner.

### Broader Eval Row-Level Artifacts

The Amendment A and Amendment B SelfAware evals have row-level `scored_rows.jsonl`
with exact `eval_set + row_index` identity and behavior fields.

Examples inspected:

- `experiment/phase1/eval/results_amendment_a_selfaware_full_local_4b`
- `experiment/phase1/eval/results_amendment_a_broader_ood_local_4b`
- `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seed*_all_arms_4b`
- `experiment/phase1/eval/results_amendment_b_stated_confidence_neutral_concise_schema_answer_confidence_selfaware_seq_seed*_4b`

Limits:

- These rows do not carry `probe_pool_row_key`.
- They are exact for behavioral transition analysis, but they do not directly
  join to current Phase 3 hidden-state extraction rows.
- Do not infer runner row strata from aggregate-only metrics.

## Candidate Row Strata

Definitions use row-level outputs only.

- `stable_unknown_refusal`: `label == unknown`, `refused == true`, and
  `truthful == true` across the selected comparator arms.
- `stable_known_correct`: `label == known`, `refused == false`,
  `correct == true`, and `truthful == true` across the selected comparator arms.
- `unknown_refusal_loss_transition`: an unknown row where an SFT or
  SFT-merged comparator correctly refuses, while a downstream arm answers.
- `known_recovery_transition`: a known row where SFT or SFT-merged refuses, but
  a downstream arm answers correctly.
- `known_corruption_transition`: a known row where SFT answers correctly, but a
  downstream arm is not truthful.

## Current Counts

### Phase 3 Runner-Ready Smoke Slice

From the 16 complete `probe_pool_row_key` rows across eight executable Phase 3
candidate contexts:

- Stable unknown refusal across SFT family (`sft_h_lora_l36`,
  `sft_delta_l35`): 7 rows.
- Stable unknown refusal across sequential SFT+DPO/KTO family: 2 rows.
- Stable unknown refusal across all eight executable contexts: 0 rows.
- Stable known correct across SFT family: 5 rows.
- Stable known correct across sequential SFT+DPO/KTO family: 4 rows.
- Stable known correct across all eight executable contexts: 3 rows.
- Unknown rows where SFT family refused but at least one sequential arm
  answered: 5 rows.
- Known rows where SFT family refused and at least one sequential arm answered
  correctly: 1 row.
- Known rows where SFT family was correct and at least one sequential arm was
  not truthful: 1 row.

Useful runner-ready row keys:

- Stable unknown refusal, sequential family:
  - `000000004662|qz_5914`
  - `000000008054|qb_4259`
- Stable known correct, all executable contexts:
  - `000000000913|tc_1521`
  - `000000001603|tc_2527`
  - `000000011725|qb_9320`
- Unknown SFT-refusal to sequential-answer transitions:
  - `000000000289|tc_555`
  - `000000001478|tc_2356`
  - `000000001480|tc_2358`
  - `000000003930|qz_3988`
  - `000000007238|qb_3139`
- Known SFT-refusal to sequential-correct transition:
  - `000000010637|qb_7795`
- Known SFT-correct to sequential-bad transition:
  - `000000005914|qb_1307`

### Broader SelfAware Eval Strata

Amendment A SelfAware seed-1 sequential row-level eval
(`sft_merged`, `sft_dpo`, `sft_kto`):

- Complete rows: 3,369 = 2,337 known / 1,032 unknown.
- Stable unknown refusal across all three arms: 476 rows.
- Stable known correct across all three arms: 387 rows.
- Unknown `sft_merged` correct refusal -> `sft_dpo` answer: 377 rows.
- Unknown `sft_merged` correct refusal -> `sft_kto` answer: 91 rows.
- Known `sft_merged` refusal -> `sft_dpo` correct answer: 95 rows.
- Known `sft_merged` refusal -> `sft_kto` correct answer: 37 rows.

Amendment B SelfAware sequential seeds 1-3, neutral concise schema answer
confidence rows:

- Complete rows per arm: 3,369 = 2,337 known / 1,032 unknown.
- Stable unknown refusal across all nine sequential seed arms: 227 rows.
- Stable known correct across all nine sequential seed arms: 368 rows.
- Per-seed unknown SFT-merged refusal -> DPO answer: 375, 289, 498.
- Per-seed unknown SFT-merged refusal -> KTO answer: 100, 121, 155.
- Per-seed known SFT-merged refusal -> DPO correct answer: 41, 63, 63.
- Per-seed known SFT-merged refusal -> KTO correct answer: 21, 37, 31.

These broader strata are behaviorally useful, but not currently runner-ready
because they lack `probe_pool_row_key` and hidden-state extraction rows.

## Proposed Diagnostic Design

### First Runner-Ready Smoke

Use the Phase 3 smoke-slice row keys above only as a small proof of the
stratified selection path. Do not generalize from it.

Candidate directions to test first:

- `sft_h_lora_l36`
- `sft_delta_l35`
- `sft_dpo_delta_l35`
- `sft_kto_h_lora_l35`

Controls:

- `no_vector_baseline`
- source sign control: `activation_addition` and/or `activation_subtraction`
- sign-matched wrong-layer control:
  - `wrong_layer` for addition effects
  - `wrong_layer_subtraction` for subtraction effects
- `random_matched_norm`
- no shuffled-label label unless a real shuffled-label artifact exists

Config shape:

```yaml
selection:
  row_keys_by_candidate:
    sft_h_lora_l36:
      - ... stable_unknown_refusal keys ...
      - ... stable_known_correct keys ...
      - ... transition keys ...
logit_diagnostic:
  top_k: 10
control_settings:
  wrong_layer:
    layer_offset: -1
controls:
  required:
    - no_vector_baseline
    - activation_addition
    - activation_subtraction
    - wrong_layer
    - wrong_layer_subtraction
    - random_matched_norm
```

Run as logit diagnostic only before any generation replay.

### Broader High-Signal Diagnostic

For a real stratified diagnostic, first materialize a bridge from broad
SelfAware eval rows to Phase 3 hidden-state/probe rows. Acceptable paths:

1. Add the selected SelfAware row strata to a probe pool that emits
   `probe_pool_row_key`, then rerun hidden-state extraction for those frozen
   rows.
2. Add an explicit, validated mapping from `(eval_set, row_index, id)` to
   `probe_pool_row_key` only if the underlying questions and aliases are
   confirmed identical.

Preferred initial broad strata:

- 8-16 stable unknown-refusal rows from the Amendment B all-seed sequential
  intersection.
- 8-16 stable known-correct rows from the same intersection.
- 8-16 unknown refusal-loss transition rows, sampled separately for DPO and KTO.
- 4-8 known recovery transition rows, sampled separately for DPO and KTO.

## Blockers

- Current broad SelfAware row-level artifacts do not include `probe_pool_row_key`.
- Current Phase 3 runner selection is keyed by hidden-state extraction rows, not
  eval-local `(eval_set, row_index)`.
- Aggregate-only metrics cannot support exact row strata.
- The runner still needs real shuffled-label direction artifacts before
  shuffled-label controls can be claimed.

## Recommendation

Do not create a broad runnable config yet. The immediate safe next step is a
small runner-ready smoke config using the 16-row Phase 3 generation-sweep keys,
or a stronger prep task that builds a validated SelfAware-to-probe row bridge
and hidden-state extraction for the broader high-signal strata.
