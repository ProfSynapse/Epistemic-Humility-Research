---
amendment: H
slug: thinking-enabled-parallel-arm
question: >-
  Does Qwen3 thinking mode change the observable knowledge boundary enough
  to warrant a parallel thinking-derived training/eval branch?
predictions:
  orchestrator:
    call: thinking perturbs the boundary enough to justify a parallel arm
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  DRAFT / NOT SIGNED; bounded audit showed real perturbation, enough to define
  a parallel arm but not to overwrite non-thinking evidence.
scoreboard: null
---

# Protocol Amendment H: Thinking-Enabled Parallel Arm

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment H / thinking-enabled parallel arm

**Scope:** Add a separate thinking-enabled replication branch for the Phase 1
epistemic-humility pipeline: rerun the TriviaQA knowledge-boundary probe with
Qwen3 thinking enabled, rebuild the derived datasets from that source if the
probe is accepted, then repeat the same training/eval regimen family as a
parallel comparator against the current non-thinking branch.

**Session note:** `docs/sessions/20260625T122352Z-triviaqa-thinking-knowledge-audit.md`

---

## 1. Rationale

The locked Phase 1 source labels were derived with Qwen3 thinking disabled.
New literature and our local audit both raise the possibility that thinking mode
changes the observable knowledge boundary: the model may produce correct final
answers under a reasoning trace that it does not produce in the non-thinking
setting.

The 2026-06-25 bounded audit did not justify replacing the current labels, but
it did show a real perturbation. On 128 matched TriviaQA rows, thinking moved
16/47 base-unknown rows out of unknown, including 1 row into known, while also
moving 10 greedy-correct rows to greedy-wrong. This is enough to define a
parallel thinking arm, not enough to overwrite the non-thinking evidence.

## 2. Relationship To Existing Protocols

This amendment is additive and exploratory.

- PROTOCOL v0.3 remains locked as the non-thinking headline protocol.
- Amendments B-G remain non-thinking unless their configs explicitly say
  otherwise.
- Amendment H does not supersede any existing results. It creates a separately
  labeled thinking-enabled comparator branch.
- Current non-thinking artifacts remain valid for the non-thinking research
  question.

## 3. Design Change

Amendment H adds a two-stage parallel branch.

### Stage H1: Thinking-Aware TriviaQA Source Probe

Rerun the TriviaQA source probe with:

| Field | Value |
|---|---|
| model | same Qwen3 base family as the matched non-thinking branch |
| thinking | enabled |
| scoring | score final answer text after the last `</think>` |
| raw provenance | preserve raw generations and extraction statuses |
| invalid trace handling | score empty final answer when `<think>` is opened without `</think>` |
| comparison | join against non-thinking `probe_pool_row_key` |

The first acceptance gate is extraction quality. If unterminated traces dominate,
the run measures token-budget truncation, not knowledge.

### Stage H2: Thinking-Enabled Training/Eval Replication

If H1 is accepted, rebuild the derived known/unknown/ambiguous datasets from the
accepted thinking labels and repeat the same regimen family as the current local
4B evidence track:

| Regimen family | Thinking branch intent |
|---|---|
| SFT | Teach output schema/final-response behavior from thinking-derived labels. |
| SFT -> DPO | Test paired preference tuning after a thinking-derived SFT base. |
| SFT -> KTO | Test unpaired preference tuning after a thinking-derived SFT base. |
| SFT -> GRPO | Test reward tuning after a thinking-derived SFT base. |
| SFT -> DPO -> GRPO | Compare the current best non-thinking stack under thinking-derived labels. |
| SFT -> GRPO -> DPO | Compare the Amendment F best-stack direction under thinking-derived labels. |
| SFT -> KTO -> GRPO | Test KTO-first stacking under thinking-derived labels. |
| SFT -> GRPO -> KTO | Test KTO-after-GRPO stacking under thinking-derived labels. |

Reciprocal preference-family stacks such as `SFT -> DPO -> KTO` and
`SFT -> KTO -> DPO` are not part of the Amendment H default matrix. They remain
deferred unless later evidence or a specific failure mode makes DPO/KTO ordering
theoretically necessary. The active three-step contrast is preference -> RL
versus RL -> preference.

Seed policy should mirror the active non-thinking decision tree: seed 1 first
for plumbing and behavior, then seeds 2/3 only after the arm is interpretable or
when replicating the best observed stack.

## 4. Rerun / Launch Requirement

Existing non-thinking artifacts can be reused only as comparators. They cannot
answer the thinking-enabled question.

Required reruns:

1. thinking-enabled TriviaQA probe;
2. thinking-derived data build and leakage checks;
3. training for each approved thinking regimen/seed;
4. full SelfAware response-confidence eval with thinking enabled;
5. paired comparison against matched non-thinking runs.

This draft does not authorize any launch. A launch decision must name the exact
stage, config, seed, source checkpoint, lane, and output path.

## 5. Metrics And Interpretation

Report the same behavior and response-confidence metrics as the matched
non-thinking branch:

- truthful percentage;
- unknown refusal recall;
- unknown answer rate;
- known over-refusal;
- correct-on-known among answered known rows;
- response-confidence coverage and unique-value distribution;
- Brier/MAE versus response appropriateness;
- row-level transitions against the matched non-thinking model.

Additional H1 metrics:

- label-transition table from non-thinking to thinking;
- greedy correctness transition table;
- extraction-status counts;
- base-unknown-to-thinking-known and base-unknown-to-thinking-discard rates;
- scorer-sensitivity notes for semantically correct but alias-missed answers.

Interpretation rules:

- Do not call thinking better solely because it moves unknown rows into discard.
- Do not treat exact-alias scorer misses as new knowledge without row review.
- Keep behavior and confidence separated; higher confidence is not improvement
  unless calibration metrics improve.

## 6. Implementation Boundary

Project-local implementation may include:

- probe configs under `archive/experiment/phase1/probe/config/`;
- probe comparison scripts under `archive/experiment/phase1/probe/`;
- experiment-local runbooks/plans under `experiments/<slug>/`;
- protocol/session docs under `docs/protocols/`, `experiments/<slug>/`, and `docs/sessions/`;
- analysis summaries under `experiment/phase1/probe/analysis/` and
  `archive/experiment/phase1/eval/analysis/`.

Do not commit model weights, large raw run outputs, restricted data, or scratch
training directories. Generic training/eval fixes in `synaptic-tuner/` must
remain project-agnostic.

## 7. Launch And Reporting Rules

All results must be labeled as Amendment H / thinking-enabled parallel arm.

They must not be pooled into PROTOCOL v0.3, Amendment E/F/G non-thinking
headline comparisons, or public artifact claims unless a later signed amendment
explicitly says how to combine them.

Local GPU launches require exact current approval naming the cell/seed/lane.
Cloud launches and Hugging Face publication require separate exact approvals.

## 8. Sign-Off Checklist

- approval date:
- approved scope:
- approved cells/seeds/lane:
- excluded cells/seeds:
- schema/metric definitions frozen:
