---
amendment: C
slug: crossover-preference-stacking
question: >-
  Can a cross-over second preference stage (SFT->DPO->KTO or SFT->KTO->DPO)
  combine complementary corrections better than either first-stage arm?
predictions:
  orchestrator:
    call: DPO and KTO may apply complementary corrections, better balance
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  DRAFT / NOT SIGNED / DEPRIORITIZED; reciprocal preference stacking not in
  active near-term matrix as of 2026-06-25.
scoreboard: null
---

# Protocol Amendment C: Cross-Over Preference Stacking

**Status:** DRAFT / NOT SIGNED / DEPRIORITIZED. This amendment is a proposed
exploratory extension. It does not authorize training, evaluation, artifact
publication, or changes to any signed protocol scope by itself. As of
2026-06-25, reciprocal DPO/KTO preference stacking is not part of the active
near-term matrix; preference -> RL and RL -> preference crossings are higher
priority.

**Short name:** Amendment C / crossover preference stacking

**Scope:** Add an exploratory cross-over sequential preference-stacking
extension that tests `SFT -> DPO -> KTO` and `SFT -> KTO -> DPO` after the
Amendment A first-stage sequential arms.

**Session note:** `docs/sessions/20260619T122000Z-amendment-c-crossover-preference-stacking.md`

---

## 1. Rationale

Current sequential evidence suggests the two first-stage preference follow-ons
repair different parts of the SFT behavior profile. `SFT -> DPO` reduces
known-row over-refusal strongly, but appears to overshoot by giving up many
unknown-row abstentions. `SFT -> KTO` preserves more of the SFT refusal behavior
and truthfulness profile, but leaves more over-refusal unresolved.

Amendment C asks whether a second, cross-over preference stage can combine those
corrections: DPO may reduce SFT's excessive refusal, while KTO may then pull the
policy back toward abstaining on genuinely unknown rows; conversely, KTO may
preserve abstention first, while DPO may then recover additional known answers.

The competing hypothesis is that stacking preference stages compounds
instability rather than balancing it. The second stage may wash out the first
stage, over-answer unknown rows, restore over-refusal, degrade known-answer
accuracy, or introduce schema and provenance failures that make the resulting
arms uninterpretable.

2026-06-25 literature check: `DPO Meets PPO: Reinforced Token Optimization for
RLHF` (arXiv:2404.18922) supports preference-derived signal feeding a later
RL-style policy optimizer, but does not provide a comparable reason to treat
DPO->KTO and KTO->DPO ordering as a distinct high-priority axis. This amendment
therefore remains a dormant draft unless later evidence revives it.

## 2. Relationship To Existing Protocols

This amendment is additive and exploratory.

- Signed PROTOCOL v0.3 remains the locked headline protocol.
- Amendment A remains the prospective sequential-refinement extension defining
  `SFT -> DPO` and `SFT -> KTO` with merge-first execution.
- Amendment B remains the separate stated-confidence / GRPO scope.
- Amendment C does not supersede v0.3, Amendment A, or Amendment B.
- If these arms are later run, every result, config, run record, artifact
  pointer, table, and figure must label the evidence as Amendment C.

## 3. Proposed Arms

Define two cross-over stacked arms:

| Arm | Definition | Execution sketch |
|---|---|---|
| `sft_dpo_kto` | `SFT -> DPO -> KTO` | Merge the completed `SFT -> DPO` model, then train a KTO stage from that merged prior sequential model. |
| `sft_kto_dpo` | `SFT -> KTO -> DPO` | Merge the completed `SFT -> KTO` model, then train a DPO stage from that merged prior sequential model. |

For the second preference stage, the base and reference model should be the
merged prior sequential model where the tuner supports that configuration. This
amendment does not require project-specific trainer changes. If the generic
tuner cannot express the intended base/reference relationship, the affected cell
must stop at planning until a generic tuner-supported route is approved.

## 4. Hypotheses

Primary hypothesis:

- DPO and KTO may apply complementary corrections and produce a better
  refusal/known-answer balance than either first-stage sequential arm alone.

Competing hypotheses:

- The second stage erases useful SFT-induced abstention.
- The second stage washes out the first preference stage rather than composing
  with it.
- `SFT -> DPO -> KTO` remains too answer-prone or becomes unstable.
- `SFT -> KTO -> DPO` reintroduces DPO-style over-answering.
- Either stacked arm compounds over-refusal, over-answering, schema instability,
  or capability regression.

## 5. Matrix And Gates

Candidate matrix:

| Model size | Lane | Seed scope | Arms | Gate |
|---|---|---|---|---|
| 4B | local smoke | seeds 1, 2, and 3 | `sft_dpo_kto`, `sft_kto_dpo` | Each seed requires explicit launch approval for exact configs, source artifacts, output paths, and lane. |
| 8B | deferred | not approved | none yet | Revisit only after 4B evidence justifies the added cost. |

Seeds 1, 2, and 3 are the requested 4B candidate scope, not a headline matrix.
They must still be launched deliberately, one exact approved batch at a time.
The earlier seed-1 smoke gate is retained as an execution recommendation, not a
restriction on the candidate matrix: if seed 1 exposes merge, sanity-eval,
schema, or provenance failures, seeds 2 and 3 should pause until the failure is
resolved.

Before any stacked seed is launched, the source plan must identify:

1. valid merge provenance,
2. a completed sanity eval,
3. public run records/configs/pointers sufficient to reproduce what was run,
4. no large artifacts committed, and
5. no unresolved schema, confidence, or artifact-lineage failures.

Recipe status: no runnable Amendment C recipe YAML is declared by this draft.
The two stacked arms need seed-specific merged prior-stage model paths from
`SFT -> DPO` or `SFT -> KTO`. Until those exact source artifacts and the
base/reference interpretation are named, recipe scaffolding should remain a
checklist item rather than a runnable config.

## 6. Metrics

Report the same core answer/refusal metrics used for the surrounding Phase 1 and
sequential analyses:

- unknown refusal recall
- known answer accuracy
- over-refusal rate
- row-level transition counts against the matched SFT baseline
- row-level transition counts against the matched `SFT -> DPO` first-stage arm
- row-level transition counts against the matched `SFT -> KTO` first-stage arm
- stated-confidence coverage and calibration metrics if the Amendment B eval
  contract is used
- capability and regression notes, including qualitative output failures,
  schema failures, merge warnings, and provenance anomalies

Transition summaries should distinguish at minimum:

- unknown rows where a prior arm refused and the stacked arm answers
- unknown rows where a prior arm answered and the stacked arm refuses
- known rows where a prior arm refused and the stacked arm answers
- known rows where a prior arm refused and the stacked arm answers correctly
- known rows where a prior arm answered correctly and the stacked arm loses that
  correct answer

## 7. Falsifiers

Amendment C should be treated as unsupported if any of the following hold:

- both stacked arms perform no better than the better first-stage arm on the
  refusal/known-answer tradeoff;
- the second stage erases SFT-induced abstention on unknown rows;
- known-answer accuracy degrades materially relative to the relevant first-stage
  sequential comparator;
- stacked outputs show schema or stated-confidence failures that make the eval
  contract unreliable;
- merge lineage, base/reference identity, or artifact provenance cannot be
  reconstructed from public records and pointers;
- capability/regression notes show a material qualitative degradation not
  captured by the aggregate metrics.

## 8. Implementation Boundary

This amendment text does not approve any launch. A later launch decision must
name the exact cells, seeds, configs, source artifacts, destination paths, and
execution lane.

No large model artifacts, adapters, generated eval rows, or restricted data may
be committed. Repository changes should be limited to public protocol text,
configs, scripts, tests, run records, and artifact pointers that preserve
provenance without redistributing large or restricted files.

Do not put project-specific Amendment C logic into `synaptic-tuner/`. Use the
existing generic tuner capabilities where possible, and stop for a separate
implementation decision if generic support is insufficient.

## 9. Sign-Off Checklist

This amendment becomes active only after explicit user approval. At sign-off,
record:

- approval date;
- approved arms;
- approved seeds;
- approved execution lane;
- exact first-stage artifacts to merge from;
- second-stage base/reference interpretation;
- eval contract, including whether Amendment B stated-confidence fields are in
  scope;
- artifact and run-record locations;
- any excluded cells or deferred model sizes.
