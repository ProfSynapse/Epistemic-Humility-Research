---
amendment: J
slug: grpo-v3-proper-scoring-confidence
question: >-
  Does a proper-scoring (Brier) GRPO reward install calibrated,
  behavior-conditional emitted response confidence on the clean-SFT base?
predictions:
  orchestrator:
    call: emitted scalar moves toward calibrated internal doubt axis
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  NEGATIVE — emitted confidence stayed collapsed (std 0.027, AUROC to
  appropriateness 0.522, ECE worse); only answered-known correct-vs-wrong
  AUROC moved 0.521 to 0.600.
scoreboard: null
---

# Protocol Amendment J: Proper-Scoring (Brier) GRPO Reward for Response Confidence

**Status:** SIGNED — user-authorized 2026-06-27 ("Let's finish b1 first since it
won't take very long. Then amend and get training going.")

**Short name:** Amendment J / GRPO v3 proper-scoring confidence reward

**Scope:** Authorize one new local GRPO cell, `schema_clean_sft_grpo_v3`
(arm **B0**), that retrains the merged clean schema-SFT seed-1 checkpoint with a
proper-scoring reward (`humility_reward_v3.py`) instead of the v2
behavior-bonus reward. The clean-SFT base, the GRPO dataset, and every GRPO
hyperparameter are held identical to the existing `schema_clean_sft_grpo_v2`
cell so that the **reward function is the only changed variable**. This amendment
adds a cell; it does not relabel, overwrite, or re-interpret the v2 cell or any
PROTOCOL v0.3 / Amendment E artifact.

**Session note:** `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md`

**Design note (non-governed):**
`experiments/grpo-v3-proper-scoring-confidence/RUNBOOK.md`,
`archive/notes/experiments/computed-confidence-alignment-regimen.md`

---

## 1. Rationale

Amendment E established that clean schema-SFT emits a genuine confidence spread
(2,489 unique targets in `[0.3508, 0.90]`), but the seed-0018 audit showed the
scalar collapse is **GRPO-driven, not SFT-driven**:

- clean SFT emits spread;
- `schema_clean_sft_grpo_v1` collapsed it (known/unknown confidence means
  0.746 / 0.747, audit §023);
- `schema_clean_sft_grpo_v2` collapsed it further (eval confidence std 0.015,
  ECE 0.142, correct-vs-wrong AUROC 0.56, session 0026).

Meanwhile the L35 doubt-axis probe on the same v2 model is near-calibrated
(ECE 0.004): the model **internally separates known from unknown but does not say
so** in the emitted scalar. The lever is therefore the GRPO reward, not the SFT
data.

The v2 reward pays a fixed behavior bonus per cell (known_correct +2.0,
known_over_refusal −2.0, unknown_abstain +1.2) but does **not** reward the
emitted scalar for being well-calibrated. A constant confidence is a stationary
point of that reward. v3 fixes this by adding a strictly proper scoring term:

- a **Brier** penalty between the emitted `response_confidence` and a
  per-question appropriateness target makes any constant scalar provably
  suboptimal (a proper scoring rule is uniquely minimized by reporting the true
  per-question appropriateness probability);
- the behavior magnitudes from v2 are preserved so behavior incentives are
  unchanged and the contrast with v2 is clean.

External grounding is the same as Amendment E §1: per-sample sequence-probability
is not a reliable confidence lever (arXiv:2606.27359), so the appropriateness
target is built from sampled correctness, not log-probability.

## 2. Relationship To Existing Protocols

This amendment is additive and is the GRPO-reward analogue of the Amendment E
data work.

- PROTOCOL v0.3 remains the locked plain-answer headline matrix. Untouched.
- Amendment E remains the schema target-construction track and supplies the
  clean-SFT base this cell builds on. Untouched.
- The `schema_clean_sft_grpo_v2` cell remains valid as the behavior-bonus
  baseline and as the attribution control for this cell. **v3 must not overwrite
  v2 outputs**; it writes to a distinct `..._grpo_v3_seed1_*` run directory.
- Reported separately as "GRPO v3 / proper-scoring confidence" runs. Do not pool
  with v1/v2 collapse results except as explicit controls.

## 3. Design Change

### 3.1 Reward

`experiment/phase1/grpo/humility_reward_v3.py`, default closure
`epistemic_humility_reward = make_reward()`:

- proper-scoring term: `−confidence_weight * Brier(conf, appropriateness)` with
  `confidence_weight = 1.2`;
- `appropriateness` is the per-question target probability that the emitted
  response is the appropriate one, computed in `target_mode="group"` (default):
  the target is estimated per (label, gold-answer) group over the rollout batch,
  so a question answered correctly by most samples gets a high answer-target and
  a true-unknown gets a high abstention-target;
- behavior term: the v2 magnitudes are preserved (known_correct +2.0,
  known_over_refusal −2.0, unknown_abstain +1.2);
- malformed-JSON / missing-scalar rows fail closed to the v2 malformed penalty.

### 3.2 CPU preflight (completed, GREEN)

Before any GPU spend the v3 reward was re-scored on 19,904 real v2 rollouts
(`experiment/phase1/grpo/v3_reward_preflight.py`):

- **Q1 spread:** group appropriateness targets std 0.320 over 4,211 prompts,
  65.6% in `[0.2, 0.8]` — no degenerate single-target collapse;
- **Q2 ordering:** behavior cell ordering preserved (known_correct >
  unknown_abstain > known_over_refusal);
- **Q3 Brier gain:** a calibrated emitter beats a flat-0.82 emitter on
  4,211 / 4,211 prompts (mean Brier gain +0.394).

This empirically rules out the main degenerate risk (uniform group targets that
would make the proper-scoring term inert) before training.

### 3.3 Cell definition

| Cell | Base | Dataset | Reward | Output dir |
|---|---|---|---|---|
| `schema_clean_sft_grpo_v3` (B0) | merged clean schema-SFT seed-1 | same GRPO `grpo_train.jsonl` as v2 | `humility_reward_v3.py` `epistemic_humility_reward` | `runs/schema_clean_sft_grpo_v3_seed1_{smoke,full}` |

All GRPO hyperparameters (LoRA r32/α64, batch 32, num_generations 4,
max_completion 128, temp 1.35, LR 5e-6, beta 0.1, 1 epoch) are copied verbatim
from `grpo_schema_clean_sft_merged_seed1_v2_full.yaml`.

Config files:

- `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v3_smoke.yaml`
- `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v3_full.yaml`

## 4. Launch Sequence

| Order | Step | Gate |
|---|---|---|
| 1 | v3 smoke (12 steps, logging every step, reward-debug on) | reward variance > 0 across steps; reward-debug rows show non-constant per-row reward and sane appropriateness targets |
| 2 | v3 full (1 epoch) | smoke GREEN |
| 3 | eval | calibration (confidence std, ECE, correct-vs-wrong AUROC) + behavior cells vs `schema_clean_sft_grpo_v2`; re-probe L35 doubt-axis coherence |

A red smoke (constant reward, or degenerate appropriateness targets) blocks the
full run and reopens the reward design.

## 5. Metrics And Interpretation

Use the Amendment E §5 metrics plus the calibration triple that v2 failed:

- `response_confidence` std and unique count (must exceed v2's 0.015 / collapse);
- ECE against response appropriateness (target: well below v2's 0.142);
- correct-vs-wrong **answer** AUROC on the emitted scalar (target: above v2's
  0.56, toward the L35 probe's internal separability);
- known over-refusal and unknown answering held at or better than v2 — a
  calibration gain bought by regressing behavior is not a success.

Success = the emitted scalar moves toward the model's already-calibrated internal
doubt axis ("model says what it knows"), with behavior preserved.

## 6. Implementation Boundary

Project-local files only:

- `experiment/phase1/grpo/humility_reward_v3.py`
- `experiment/phase1/grpo/v3_reward_preflight.py`
- `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v3_smoke.yaml`
- `experiment/phase1/grpo/configs/grpo_schema_clean_sft_merged_seed1_v3_full.yaml`

Generated scratch datasets and model artifacts remain uncommitted. The
`synaptic-tuner/` submodule remains generic; no Epistemic-specific reward logic
is added inside the submodule.

## 7. Sign-Off Checklist

- approval date: 2026-06-27
- approved scope: one local seed-1 GRPO cell `schema_clean_sft_grpo_v3` (arm B0),
  smoke then full, reward = `humility_reward_v3.py`
- approved cells/seeds/lane: `schema_clean_sft_grpo_v3` seed 1, local 4B lane
- excluded: any change to PROTOCOL v0.3 headline matrix, Amendment E artifacts, or
  the `schema_clean_sft_grpo_v2` outputs; additional seeds (deferred until seed-1
  v3 is interpreted)
- schema/metric definitions frozen: yes (§5)
- authorization: user, 2026-06-27 — "amend and get training going"
