---
amendment: G
slug: best-stack-replication-scale-gate
question: >-
  Does the best seed-1 stack (clean SFT->GRPO v2->DPO) reproduce across seeds
  and merit publication or 8B scaling?
predictions:
  orchestrator:
    call: best seed-1 stack worth testing for cross-seed reproducibility before scaling
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  DRAFT / NOT SIGNED; governs seed-2/3 replication and a narrow 8B/publication
  scale gate, pending explicit launch approval.
scoreboard: null
---

# Protocol Amendment G: Best-Stack Replication And Scale Gate

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment G / best-stack replication and scale gate

**Scope:** Add a governed follow-up to Amendment F that replicates the strongest
seed-1 response-confidence stack, `clean SFT -> GRPO v2 -> DPO`, across clean
local seeds before treating it as a public artifact candidate or scaling it to
8B.

**Session note:** `docs/sessions/0020 - best-stack-replication-and-scale-gate.md`

---

## 1. Rationale

Amendment F completed four local seed-1 three-stage stacks over the clean
response-confidence lineage. The strongest stack was `clean_sft_grpo_dpo`:
it preserved low unknown-answering like GRPO while modestly reducing GRPO's
known-row over-refusal. The gain was useful but small, and all Amendment F arms
still showed high, behavior-insensitive stated response confidence.

This means the next evidence question is not another one-off stack. It is
whether the best observed stack is reproducible across seeds and worth
publishing or scaling.

## 2. Relationship To Existing Protocols

This amendment is additive and exploratory.

- PROTOCOL v0.3 remains the locked plain-answer headline protocol.
- Amendment E remains the clean response-confidence retrain track and supplies
  the required output contract, dataset family, and clean seed lineage.
- Amendment F remains the seed-1 GRPO-centered stacking screen.
- Amendment G does not supersede prior results and must be reported separately.

## 3. Design Change

Replicate only the best Amendment F stack first:

| Arm | Definition | Purpose |
|---|---|---|
| `clean_sft_grpo_dpo_seed2` | clean response-confidence `SFT seed2 -> GRPO v2 seed2 -> DPO seed2` | Test whether the seed-1 `GRPO -> DPO` tradeoff reproduces. |
| `clean_sft_grpo_dpo_seed3` | clean response-confidence `SFT seed3 -> GRPO v2 seed3 -> DPO seed3` | Close the 3-seed local evidence gap before publication. |

Each seed must rebuild the clean response-confidence lineage for that seed. Do
not combine the seed-1 clean SFT or GRPO source with a different final-stage
seed and call it a seed replication.

Optional scale gate after local seed replication:

| Gate | Candidate | Condition |
|---|---|---|
| 8B seed-1 confirm | clean response-confidence `SFT -> GRPO v2 -> DPO` on Qwen3-8B-Instruct | Only after local seeds show that the behavior tradeoff is not a seed-1 artifact. |
| Hugging Face publication | adapters and selected merged models | Only after lineage, eval, license, model-card, and artifact-size gates pass. |

## 4. Rerun / Launch Requirement

Existing seed-1 Amendment E/F artifacts can be reused as comparators only.
They cannot answer the seed-replication question.

For each new seed:

1. train or locate a clean response-confidence SFT model for that seed;
2. merge and full-evaluate the clean SFT source;
3. train GRPO v2 from that clean SFT source;
4. merge the GRPO v2 source and run a bounded merged-source sanity eval;
5. train DPO from the merged GRPO v2 source;
6. run the full SelfAware response-confidence eval;
7. rebuild the comparison CSVs and record session/run provenance.

The launch is not authorized by this draft. A launch decision must name the
exact seed, source checkpoints, configs, destination run path, lane, and eval
plan.

## 5. Metrics And Interpretation

Use the full SelfAware metrics already used in Amendments E/F:

- truthful percentage;
- unknown refusal recall;
- unknown answer rate;
- known over-refusal rate;
- correct-on-known among answered known rows;
- response-confidence coverage, unique values, mean, and Brier/MAE versus
  response appropriateness;
- row-level transition notes against clean SFT, clean SFT->GRPO v2, and
  seed-1 `clean_sft_grpo_dpo`.

Interpretation rules:

- A reproducible win must improve or preserve the refusal/known-answer tradeoff
  against the same-seed GRPO v2 source, not only against the foundation model.
- Lower unknown answering caused only by increased known over-refusal is not a
  clean win.
- Higher stated response confidence is not an improvement unless calibration
  metrics improve.
- If confidence remains collapsed, report behavioral gains and confidence
  failure separately.

## 6. Implementation Boundary

Project-local artifacts may include:

- seed-specific training/eval configs under `experiment/phase1/`;
- run records under `experiment/phase1/run_records/`;
- session notes under `docs/sessions/`;
- experiment notes under `experiment/notes/`;
- analysis CSVs under `experiment/phase1/eval/analysis/`.

Do not commit model weights, scratch run products, restricted data, or large
generated row files. Generic tuner fixes may occur only in `synaptic-tuner/`
when they are reusable outside this project.

## 7. Launch And Reporting Rules

Results must be labeled as Amendment G / best-stack replication and must not be
pooled into v0.3, Amendment E, or Amendment F headline claims.

Local GPU launches require an exact current approval naming the seed/cell/lane.
Cloud launches and Hugging Face publication require separate exact approvals.

## 8. Sign-Off Checklist

- approval date:
- approved scope:
- approved cells/seeds/lane:
- excluded cells/seeds:
- schema/metric definitions frozen:
