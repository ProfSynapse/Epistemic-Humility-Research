---
schema_version: research-session/v1
session_id: 20260704T031355Z-ah-close-out-to-amendment-ai-sensor-refit-v1-v2-4-bit-serving-catch-pool-v2-1-arms-launch
title: 'AH close-out to Amendment AI: sensor refit v1/v2, 4-bit serving catch, pool
  v2.1, arms launch'
status: active
created_at: '2026-07-04T03:13:55Z'
updated_at: '2026-07-04T03:56:56Z'
phase: phase1
question: Can GRPO with a probe-agreement reward (frozen refit L24 sensor read from
  the policy's own pre-generation states) train the model to consult its own readout,
  where every text-channel attempt failed?
tags:
- experiment-runner
- amendment-ai
run_ids:
- amendment_ai_grpo_true_seed1_20260703_233256
- amendment_ai_grpo_true_seed1_20260703_234149
- amendment_ai_grpo_true_seed1_20260703_234933
trajectory:
  anchor: docs/research-trajectory.md
  current_position: ''
  changed_by_session: ''
checkpoints:
- id: 001-planning
  at: '2026-07-04T03:14:27Z'
  kind: planning
  title: Overnight authorization and scope
  summary: 'User pre-authorized (2026-07-03, AskUserQuestion): clean-SFT state extraction,
    sensor refit + constants derivation + D-over re-classification, and GRPO reward-plumbing
    smoke; full PAR arms conditional on smoke green + refit AUROC >= 0.9 + constants
    derived per pre-stated rules. Both parties recorded TRUE-wins predictions in the
    prereg frontmatter before launch.'
  evidence:
  - experiments/probe-as-reward/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 002-result
  at: '2026-07-04T03:14:28Z'
  kind: result
  title: Sensor refit v1 on merged-16bit states
  summary: 'Union-surface extraction (18,496 rows) plus mining extraction (9,397)
    completed on the 3090; AF-600-lineage refit on clean-SFT pre-gen states gives
    L24 held-out OOF AUROC 0.9947 vs gold, clearing the 0.9 floor. Mining + recalibration
    + refit v1 merged to main as PR #178.'
  evidence:
  - experiments/probe-as-reward/artifacts/par_sensor_refit.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 003-gate
  at: '2026-07-04T03:14:28Z'
  kind: gate
  title: 'Smoke v1 FAIL: 4-bit serving mismatch caught'
  summary: 'Smoke criterion 2 failed with in-loop p vs offline reference max_abs_diff
    0.97: the GRPO trainer loads the checkpoint 4-bit (QLoRA lineage) while sensor
    v1 was fit on merged-16bit states; in-loop integrity read 0.815. The honest FAIL
    record is retained in amendment_ai_smoke.json.'
  evidence:
  - experiments/probe-as-reward/artifacts/amendment_ai_smoke.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 004-infrastructure
  at: '2026-07-04T03:14:28Z'
  kind: infrastructure
  title: 'Sensor v2: refit-per-serving-configuration'
  summary: 'Extended Amendment T''s refit-per-checkpoint to refit-per-serving-configuration:
    union + mining states re-extracted through the 4-bit-loaded model and the sensor
    refit on those states, giving L24 OOF AUROC 0.9945 (quantization costs ~0.0002).
    Three-way byte identity verified: in-loop read = extractor read = persisted state,
    exact 0.0.'
  evidence:
  - experiments/probe-as-reward/artifacts/par_sensor_refit_v2.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 005-validation
  at: '2026-07-04T03:14:48Z'
  kind: validation
  title: 'TruthfulQA construct audit: EXCLUDE'
  summary: Stratified 82-row audit of the 407 TruthfulQA D-over candidates found 0/82
    genuinely unanswerable (58.5% misconception-loaded answerable, 28% plainly answerable,
    13.4% open-list with a true set); the D-over flag was the probe being correct.
    All 407 excluded from the training pool; audit memo committed.
  evidence:
  - experiments/probe-as-reward/artifacts/amendment_ai_truthfulqa_audit.md
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 006-gate
  at: '2026-07-04T03:14:48Z'
  kind: gate
  title: Smoke v2 all-green under sensor v2
  summary: Reward variance nonzero on 71.9% of steps (mean group std 0.417); in-loop
    p exact-zero diff vs persisted serving-aligned states; integrity audit 0.99 on
    the 500-row balanced set with both tripwire halts demonstrably firing (shuffled
    sensor 0.479, forced-invalid 1.0); checkpoint save/load clean (504 LoRA tensors).
  evidence:
  - experiments/probe-as-reward/artifacts/amendment_ai_smoke_v2.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 007-decision
  at: '2026-07-04T03:14:48Z'
  kind: decision
  title: Prereg SIGNED; constants locked
  summary: 'All three launch conditions verified and the prereg signed at bdc135ae:
    w_c = w_a = 0.50 (largest grid value with gold-unanswerable-stratum flip <= 2%;
    observed 1.3% at grid max), mixture 29.0% (smallest m with divergent advantage-mass
    share >= 25% on OOF margins). Gates AI-G0/G1/G2 locked as written; verdict adjudication
    reserved for the user.'
  evidence:
  - experiments/probe-as-reward/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 008-amendment
  at: '2026-07-04T03:14:48Z'
  kind: amendment
  title: 'Pool v2.1: membership under the in-loop sensor'
  summary: 'Pre-launch correction (before any arm step): the full-fit in-loop probe
    memorizes the union fit surface (train AUROC 1.0), under which 0/18,496 union
    rows are divergent, so the 320 union-origin rows in v2 train_divergent were inert;
    enforcing the recorded membership rule, union rows re-classified concordant and
    the 60% category cap re-applied on mining-only supply (a plain drop would leave
    ambiguous at 67%). Final pool: 2,102 divergent / 16,665 concordant / 400-row holdout
    pinned to the locked draw; committed at 67c08f92.'
  evidence:
  - experiments/probe-as-reward/artifacts/amendment_ai_pool_manifest.json
  run_ids: []
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 009-launch
  at: '2026-07-04T03:14:48Z'
  kind: launch
  title: 'Arms ordered: TRUE then PERMUTED'
  summary: 'Arms launch order sent to the runner under the user''s pre-authorization:
    clean-SFT to GRPO-probe TRUE, then PERMUTED (fixed within-gold-class row-key permutation,
    seed 0), GRPO-v2 lineage recipe with only the reward swapped, frozen v2 L24 sensor,
    tripwires per prereg 1.5. A HOLD/GO cycle interposed the pool v2.1 correction
    before any training step; runner confirms pull of 67c08f92 before launch.'
  evidence:
  - experiments/probe-as-reward/AMENDMENT.md
  run_ids: []
  commands: []
  decisions: []
  next_steps:
  - Verdict eval (AI-G0/G1/G2) with a fresh-refit eval probe when both arms complete;
    user adjudicates
  signals: {}
- id: 010-observation
  at: '2026-07-04T03:38:20Z'
  kind: observation
  title: TRUE arm live; scheduled steps 2,934; env provenance
  summary: 'Full TRUE arm running at runs/amendment_ai_grpo_true_seed1/20260703_233256
    after a 16-step launch verification (kept as provenance at 20260703_232457): ~16s/step,
    first steps sane (reward variance healthy, schema-valid 95.3%, p spans [0,1] tracking
    the live policy). Scheduled steps are 2,934 (recipe rule num_train_epochs=1 on
    the 23,472-row composed set), so AI-G0''s 90% floor means >= 2,641. Env provenance:
    trainer runs in conda unsloth_env; joblib/scipy/scikit-learn 1.8.0 installed --no-deps
    for the pickled sensor, verified bit-identical to the fitting env (max_abs_diff
    0.0 on 8 seeded vectors); relaunches must use the unsloth_env interpreter.'
  evidence:
  - experiment/phase1/grpo/amendment_ai_train_manifest.json
  run_ids:
  - amendment_ai_grpo_true_seed1_20260703_233256
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 011-recovery
  at: '2026-07-04T03:48:08Z'
  kind: recovery
  title: Stale-HOLD kill and TRUE relaunch; live run is 234149
  summary: A queued stale HOLD was executed by the runner one wake-cycle after its
    GO was already satisfied, killing the correctly-launched TRUE run (233256) at
    step 4; nothing was deleted and the pool/train data were already v2.1, so TRUE
    was relaunched fresh from step 0. The live run is runs/amendment_ai_grpo_true_seed1/20260703_234149
    (first steps sane; 232457 = 16-step launch verification and 233256 = step-4 kill
    are retained as provenance). Incident + mitigations recorded in the subagent-orchestration
    doctrine (SHA-stamped directives, self-invalidating destructive orders, world-state
    checks).
  evidence:
  - .skills/experiment-runner/reference/subagent-orchestration.md
  run_ids:
  - amendment_ai_grpo_true_seed1_20260703_234149
  commands: []
  decisions: []
  next_steps: []
  signals: {}
- id: 012-amendment
  at: '2026-07-04T03:56:56Z'
  kind: amendment
  title: 'Correction: live TRUE run is 234933'
  summary: 'The 234149 dir named in the recovery checkpoint was the runner''s 16-step
    v2.1 launch verification, not the full arm; the live full TRUE run is runs/amendment_ai_grpo_true_seed1/20260703_234933
    (PID confirmed, 19 steps sane at verification: reward_mean band 0.375-0.937, schema-valid
    94.2%, 2,934 scheduled steps). Runner re-prepped against pool v2.1 and re-drew
    the 500-row integrity audit set (250/gold-class, seed 0) at f8d26f95.'
  evidence: []
  run_ids:
  - amendment_ai_grpo_true_seed1_20260703_234933
  commands: []
  decisions: []
  next_steps: []
  signals: {}
legacy_session:
  id: amendment-ai-probe-as-reward-launch
  path: docs/sessions/0036 - ah-close-out-to-amendment-ai-sensor-refit-v1-v2-4-bit-serving-catch-pool-v2-1-arms-launch.md
---
# AH close-out to Amendment AI: sensor refit v1/v2, 4-bit serving catch, pool v2.1, arms launch

## Question

Can GRPO with a probe-agreement reward (frozen refit L24 sensor read from the policy's own pre-generation states) train the model to consult its own readout, where every text-channel attempt failed?

## Trajectory Position

RQ4 use-the-signal, reward-channel stage. AH (with Addendum A1) certified H-COMPLIANCE for the text channel: prime uptake does not consult the model's own readout. Amendment AI is the reward-channel counterpart: if GRPO paid directly on agreement with the model's own frozen readout also fails to couple behavior to the readout (TRUE vs PERMUTED flat), H-compliance generalizes across channels; if it succeeds, we have the first trained readout-consulting policy. Probe-as-reward is the fallback path after the prosthetic path was rejected as too fragile/gameable.

## Summary

Full overnight arc under the user's conditional pre-authorization: clean-SFT state extractions (union 18,496 + mining 9,397), sensor refit v1 (L24 OOF AUROC 0.9947, PR #178), smoke v1 honest FAIL that exposed a 4-bit serving-configuration mismatch, sensor v2 refit on 4-bit-served states (0.9945; three-way byte identity exact 0.0), constants derived per pre-stated rules (w_c = w_a = 0.50, mixture 29.0%), TruthfulQA construct audit (EXCLUDE all 407), smoke v2 all-green, prereg SIGNED, and a pre-launch pool v2.1 correction (union membership re-classified under the full-fit in-loop sensor: 0/18,496 union rows divergent; divergent supply mining-only 2,102 with the 60% cap re-applied; holdout pinned). Arms TRUE then PERMUTED ordered to the runner via a HOLD/GO cycle so the correction landed before any training step. Verdict eval and adjudication remain open: eval probe is fresh-refit per Amendment T, gates locked, user adjudicates in the morning.

## Checkpoints
### 001-planning - Overnight authorization and scope

- at: `2026-07-04T03:14:27Z`
- kind: `planning`
- summary: User pre-authorized (2026-07-03, AskUserQuestion): clean-SFT state extraction, sensor refit + constants derivation + D-over re-classification, and GRPO reward-plumbing smoke; full PAR arms conditional on smoke green + refit AUROC >= 0.9 + constants derived per pre-stated rules. Both parties recorded TRUE-wins predictions in the prereg frontmatter before launch.
- evidence:
  - `experiments/probe-as-reward/AMENDMENT.md`
### 002-result - Sensor refit v1 on merged-16bit states

- at: `2026-07-04T03:14:28Z`
- kind: `result`
- summary: Union-surface extraction (18,496 rows) plus mining extraction (9,397) completed on the 3090; AF-600-lineage refit on clean-SFT pre-gen states gives L24 held-out OOF AUROC 0.9947 vs gold, clearing the 0.9 floor. Mining + recalibration + refit v1 merged to main as PR #178.
- evidence:
  - `experiments/probe-as-reward/artifacts/par_sensor_refit.json`
### 003-gate - Smoke v1 FAIL: 4-bit serving mismatch caught

- at: `2026-07-04T03:14:28Z`
- kind: `gate`
- summary: Smoke criterion 2 failed with in-loop p vs offline reference max_abs_diff 0.97: the GRPO trainer loads the checkpoint 4-bit (QLoRA lineage) while sensor v1 was fit on merged-16bit states; in-loop integrity read 0.815. The honest FAIL record is retained in amendment_ai_smoke.json.
- evidence:
  - `experiments/probe-as-reward/artifacts/amendment_ai_smoke.json`
### 004-infrastructure - Sensor v2: refit-per-serving-configuration

- at: `2026-07-04T03:14:28Z`
- kind: `infrastructure`
- summary: Extended Amendment T's refit-per-checkpoint to refit-per-serving-configuration: union + mining states re-extracted through the 4-bit-loaded model and the sensor refit on those states, giving L24 OOF AUROC 0.9945 (quantization costs ~0.0002). Three-way byte identity verified: in-loop read = extractor read = persisted state, exact 0.0.
- evidence:
  - `experiments/probe-as-reward/artifacts/par_sensor_refit_v2.json`
### 005-validation - TruthfulQA construct audit: EXCLUDE

- at: `2026-07-04T03:14:48Z`
- kind: `validation`
- summary: Stratified 82-row audit of the 407 TruthfulQA D-over candidates found 0/82 genuinely unanswerable (58.5% misconception-loaded answerable, 28% plainly answerable, 13.4% open-list with a true set); the D-over flag was the probe being correct. All 407 excluded from the training pool; audit memo committed.
- evidence:
  - `experiments/probe-as-reward/artifacts/amendment_ai_truthfulqa_audit.md`
### 006-gate - Smoke v2 all-green under sensor v2

- at: `2026-07-04T03:14:48Z`
- kind: `gate`
- summary: Reward variance nonzero on 71.9% of steps (mean group std 0.417); in-loop p exact-zero diff vs persisted serving-aligned states; integrity audit 0.99 on the 500-row balanced set with both tripwire halts demonstrably firing (shuffled sensor 0.479, forced-invalid 1.0); checkpoint save/load clean (504 LoRA tensors).
- evidence:
  - `experiments/probe-as-reward/artifacts/amendment_ai_smoke_v2.json`
### 007-decision - Prereg SIGNED; constants locked

- at: `2026-07-04T03:14:48Z`
- kind: `decision`
- summary: All three launch conditions verified and the prereg signed at bdc135ae: w_c = w_a = 0.50 (largest grid value with gold-unanswerable-stratum flip <= 2%; observed 1.3% at grid max), mixture 29.0% (smallest m with divergent advantage-mass share >= 25% on OOF margins). Gates AI-G0/G1/G2 locked as written; verdict adjudication reserved for the user.
- evidence:
  - `experiments/probe-as-reward/AMENDMENT.md`
### 008-amendment - Pool v2.1: membership under the in-loop sensor

- at: `2026-07-04T03:14:48Z`
- kind: `amendment`
- summary: Pre-launch correction (before any arm step): the full-fit in-loop probe memorizes the union fit surface (train AUROC 1.0), under which 0/18,496 union rows are divergent, so the 320 union-origin rows in v2 train_divergent were inert; enforcing the recorded membership rule, union rows re-classified concordant and the 60% category cap re-applied on mining-only supply (a plain drop would leave ambiguous at 67%). Final pool: 2,102 divergent / 16,665 concordant / 400-row holdout pinned to the locked draw; committed at 67c08f92.
- evidence:
  - `experiments/probe-as-reward/artifacts/amendment_ai_pool_manifest.json`
### 009-launch - Arms ordered: TRUE then PERMUTED

- at: `2026-07-04T03:14:48Z`
- kind: `launch`
- summary: Arms launch order sent to the runner under the user's pre-authorization: clean-SFT to GRPO-probe TRUE, then PERMUTED (fixed within-gold-class row-key permutation, seed 0), GRPO-v2 lineage recipe with only the reward swapped, frozen v2 L24 sensor, tripwires per prereg 1.5. A HOLD/GO cycle interposed the pool v2.1 correction before any training step; runner confirms pull of 67c08f92 before launch.
- evidence:
  - `experiments/probe-as-reward/AMENDMENT.md`
- next steps:
  - Verdict eval (AI-G0/G1/G2) with a fresh-refit eval probe when both arms complete; user adjudicates
### 010-observation - TRUE arm live; scheduled steps 2,934; env provenance

- at: `2026-07-04T03:38:20Z`
- kind: `observation`
- summary: Full TRUE arm running at runs/amendment_ai_grpo_true_seed1/20260703_233256 after a 16-step launch verification (kept as provenance at 20260703_232457): ~16s/step, first steps sane (reward variance healthy, schema-valid 95.3%, p spans [0,1] tracking the live policy). Scheduled steps are 2,934 (recipe rule num_train_epochs=1 on the 23,472-row composed set), so AI-G0's 90% floor means >= 2,641. Env provenance: trainer runs in conda unsloth_env; joblib/scipy/scikit-learn 1.8.0 installed --no-deps for the pickled sensor, verified bit-identical to the fitting env (max_abs_diff 0.0 on 8 seeded vectors); relaunches must use the unsloth_env interpreter.
- run ids:
  - `amendment_ai_grpo_true_seed1_20260703_233256`
- evidence:
  - `experiment/phase1/grpo/amendment_ai_train_manifest.json`
### 011-recovery - Stale-HOLD kill and TRUE relaunch; live run is 234149

- at: `2026-07-04T03:48:08Z`
- kind: `recovery`
- summary: A queued stale HOLD was executed by the runner one wake-cycle after its GO was already satisfied, killing the correctly-launched TRUE run (233256) at step 4; nothing was deleted and the pool/train data were already v2.1, so TRUE was relaunched fresh from step 0. The live run is runs/amendment_ai_grpo_true_seed1/20260703_234149 (first steps sane; 232457 = 16-step launch verification and 233256 = step-4 kill are retained as provenance). Incident + mitigations recorded in the subagent-orchestration doctrine (SHA-stamped directives, self-invalidating destructive orders, world-state checks).
- run ids:
  - `amendment_ai_grpo_true_seed1_20260703_234149`
- evidence:
  - `.skills/experiment-runner/reference/subagent-orchestration.md`
### 012-amendment - Correction: live TRUE run is 234933

- at: `2026-07-04T03:56:56Z`
- kind: `amendment`
- summary: The 234149 dir named in the recovery checkpoint was the runner's 16-step v2.1 launch verification, not the full arm; the live full TRUE run is runs/amendment_ai_grpo_true_seed1/20260703_234933 (PID confirmed, 19 steps sane at verification: reward_mean band 0.375-0.937, schema-valid 94.2%, 2,934 scheduled steps). Runner re-prepped against pool v2.1 and re-drew the 500-row integrity audit set (250/gold-class, seed 0) at f8d26f95.
- run ids:
  - `amendment_ai_grpo_true_seed1_20260703_234933`
### 013-decision - Verdict-eval locked pre-outcome

- at: `2026-07-04T05:10:00Z`
- kind: `decision`
- summary: The full AI-G0/G1/G2 verdict-eval was written, self-tested, and committed while the TRUE arm was at steps ~30-80 of 2,934 (no outcome observed), making the analysis procedure effectively pre-registered. Scorer amendment_ai_verdict_score.py (fresh eval probe per arm refit on the FINAL checkpoint per Amendment T with holdout excluded from fit = G0 falsifier; G1 own-readout congruence differential on the locked 400-row holdout, 10,000-boot paired bootstrap seed 0, schema-invalid counts incongruent; descriptive strata labeled NOT gates) passed synthetic self-tests (bootstrap point/CI/determinism, G2 tolerance both sides, congruence truth table). The G2 no-regression reference was PINNED to the Amendment E corrected-base full SelfAware eval of GRPO-v2 (93.41/33.38/53.85, formulas + counts committed) so no verdict-time freedom remains in the comparison. Prereg gained §4 (operationalization only; no gate/floor/constant changes). Commits 1327f15c + 254380da. TRUE arm healthy at last disk check (80 steps, no HALT, reward_mean 0.656, group-std nonzero 75%).
- evidence:
  - `experiment/phase1/probe/amendment_ai_verdict_score.py`
  - `experiments/probe-as-reward/artifacts/amendment_ai_g2_reference_grpo_v2.json`
  - `experiments/probe-as-reward/AMENDMENT.md`
