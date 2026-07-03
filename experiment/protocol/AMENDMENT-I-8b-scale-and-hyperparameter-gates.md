---
amendment: I
slug: 8b-scale-and-hyperparameter-gates
question: >-
  Which 8B response-confidence/thinking variants are worth preparing, and
  should hyperparameter sweeps run before a pre-run audit?
predictions:
  orchestrator:
    call: tiered 8B gates plus mandatory pre-sweep hyperparameter audit
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  DRAFT / NOT SIGNED; defines 8B variant tiers and a hyperparameter gate,
  authorizes no training.
scoreboard: null
---

# Protocol Amendment I: 8B Scale And Hyperparameter Gates

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment I / 8B scale and hyperparameter gates

**Scope:** Define a governed planning layer for Qwen3-8B response-confidence and
thinking-enabled variants, plus a pre-run hyperparameter audit that must happen
before learning-rate, beta, KL, reward-shaping, or LoRA-rank sweeps are launched.

**Session note:** `docs/sessions/0022 - 8b-scale-and-hyperparameter-planning.md`

---

## 1. Rationale

The current local Qwen3-4B evidence is useful for process development, but the
model may be too small for several expected epistemic-humility effects:

- cold-start DPO and KTO remained close to base-like answering;
- SFT learned the abstention behavior but over-refused known rows;
- GRPO and three-stage stacks improved the refusal/known-answer tradeoff only
  modestly;
- response confidence remained largely behavior-insensitive across the clean
  seed-1 stacks.

Before spending more local or HF Jobs compute, this amendment separates two
decisions:

1. which 8B variants are scientifically worth preparing; and
2. whether hyperparameter changes are likely to move behavior, or whether the
   limiting factor is data quality, source labels, reward design, or model scale.

## 2. Relationship To Existing Protocols

This amendment is additive and exploratory.

- PROTOCOL v0.3 already includes a locked plain-answer 8B confirm for SFT, DPO,
  and KTO. Amendment I does not change those headline requirements.
- Amendment E supplies the clean response-confidence output contract and clean
  seed-1 lineage.
- Amendment F supplies the seed-1 GRPO-centered stack screen.
- Amendment G proposes best-stack replication and a narrow 8B scale gate for
  `clean SFT -> GRPO v2 -> DPO`.
- Amendment H defines the thinking-enabled parallel arm.
- Amendment I does not authorize training. It defines variant tiers and gates so
  later launches are explicit rather than improvised.

## 3. 8B Variant Tiers

### Tier 0: Locked v0.3 8B Confirm

Existing PROTOCOL v0.3 scope:

| Arm | Seeds | Status |
|---|---:|---|
| 8B SFT | 1, 2, 3 | locked but not completed locally |
| 8B DPO | 1, 2, 3 | locked but not completed locally |
| 8B KTO | 1, 2, 3 | locked but not completed locally |

These remain plain-answer headline confirm cells. They are not response-confidence
or thinking-arm substitutes.

### Tier 1: Minimal Clean Response-Confidence 8B Screen

Prepare these first if scale-up is approved:

| Arm | Purpose |
|---|---|
| `8b_clean_sft` | Test whether 8B SFT learns the response-confidence schema and abstention boundary with less over-refusal. |
| `8b_clean_sft_grpo_v2` | Test whether GRPO v2 has stronger behavioral leverage at 8B. |
| `8b_clean_sft_grpo_dpo` | Test whether the current best 4B stack scales. |

Tier 1 is the lowest-cost scale answer: if these do not improve the tradeoff or
confidence calibration, a full 8B matrix is probably not justified yet.

### Tier 2: Full Clean Response-Confidence 8B Seed-1 Matrix

Run only after Tier 1 is interpretable:

| Arm | Mirrors 4B evidence |
|---|---|
| `8b_clean_sft_dpo` | Amendment E two-stage preference comparator |
| `8b_clean_sft_kto` | Amendment E two-stage preference comparator |
| `8b_clean_sft_dpo_grpo` | Amendment F preference -> RL |
| `8b_clean_sft_kto_grpo` | Amendment F preference -> RL |
| `8b_clean_sft_grpo_kto` | Amendment F RL -> preference |

`8b_clean_sft_grpo_dpo` is already in Tier 1 and should be reused as the Tier 2
RL -> preference comparator.

### Tier 3: Thinking-Enabled 8B Parallel Arm

Thinking-enabled 8B training must not reuse 4B source labels. It needs:

1. Qwen3-8B non-thinking TriviaQA source probe;
2. Qwen3-8B thinking-enabled TriviaQA source probe;
3. acceptance gate on extraction quality and row-level label transitions;
4. thinking-derived SFT/DPO/KTO/GRPO datasets;
5. response-confidence evals with thinking enabled and final-answer extraction
   after `</think>`.

Candidate training arms mirror Tier 1 first:

| Arm | Purpose |
|---|---|
| `8b_thinking_clean_sft` | Test 8B source-label and schema behavior under thinking. |
| `8b_thinking_clean_sft_grpo_v2` | Test reward shaping on thinking-derived labels. |
| `8b_thinking_clean_sft_grpo_dpo` | Test whether the best non-thinking stack survives the thinking branch. |

Full thinking 8B matrix is deferred until the Tier 3 source probe shows thinking
materially changes the 8B knowledge boundary and extraction is reliable.

## 4. Hyperparameter Gate Before New Sweeps

Do not launch LR/beta/KL/reward/LoRA sweeps only because compute is available.
Before any new sweep, produce an audit that answers:

- Did prior runs saturate, plateau, diverge, or remain undertrained?
- Did DPO/KTO show objective separation without behavior movement?
- Did GRPO reward components move independently, or did one component dominate?
- Did confidence collapse because the reward/data gave no usable gradient?
- Did larger batch size alter stability or only throughput?
- Are LoRA rank/alpha likely capacity bottlenecks, or are data/reward labels the
  tighter constraint?

The locked v0.3 LR/beta panel remains valid as a robustness plan, but Amendment I
requires using local training exhaust and literature before adding new
non-registered knobs such as LoRA rank, KL schedule, reward weights, or epochs.

## 5. Rerun / Launch Requirement

No launch is authorized by this draft.

Every 8B launch must name:

- model family and exact checkpoint;
- source-label artifact and whether thinking is enabled;
- dataset version;
- training stage lineage;
- seed;
- local or HF Jobs lane;
- expected output path;
- eval config and thinking mode;
- whether the run is Tier 0, Tier 1, Tier 2, or Tier 3.

Every hyperparameter run must name:

- the observed failure mode it tests;
- the prior exhaust evidence motivating the knob;
- why the chosen value is theoretically meaningful;
- what result would cause us to stop rather than expand the sweep.

## 6. Metrics And Interpretation

Use the same response-confidence metrics as Amendments E/F/H when the output
contract is in scope:

- truthful percentage;
- unknown refusal recall;
- unknown answer rate;
- known over-refusal;
- correct-on-known among answered known rows;
- response-confidence coverage and unique-value distribution;
- Brier/MAE versus response appropriateness;
- row-level transitions against matched 4B and same-size source arms.

Interpretation rules:

- Do not compare 4B labels to 8B labels as if they share a knowledge boundary.
- Do not treat higher confidence as improvement unless calibration improves.
- Do not call a hyperparameter useful if it only improves training loss while
  SelfAware behavior remains unchanged.
- Do not advance to Tier 2 or Tier 3 training until Tier 1 and the source-probe
  gates are interpretable.

## 7. Sign-Off Checklist

- approval date:
- approved tier(s):
- approved arms/seeds:
- approved lane(s):
- source-label artifact(s):
- hyperparameter audit completed:
- excluded cells:
- stop conditions:
