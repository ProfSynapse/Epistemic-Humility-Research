---
amendment: F
slug: grpo-centered-stacking
question: >-
  Can a GRPO-centered third stage (before or after a preference pass) beat
  the two-stage arms on the refusal/known-answer tradeoff?
predictions:
  orchestrator:
    call: a third GRPO-centered stage may combine effects better than two-stage
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  SIGNED OFF (2026-06-24) for exploratory local seed-1 three-stage stacking
  over the clean Amendment E lineage.
scoreboard: null
---

# Protocol Amendment F: GRPO-Centered Three-Stage Stacking

**Status:** SIGNED OFF

**Short name:** Amendment F / GRPO-centered stacking

**Scope:** Add an exploratory three-stage training extension over the latest
clean response-confidence lineage. The proposed arms test whether GRPO can
serve as either the final calibration/refusal boundary stage after SFT-warmed
preference training, or as the intermediate stage before a final DPO/KTO
preference pass.

**Session note:** `docs/sessions/20260624T183052Z-grpo-centered-stacking-plan.md`

---

## 1. Rationale

The accumulated local evidence suggests that single downstream stages after SFT
are not enough:

- cold-start DPO and KTO mostly answer unknown rows and fail the humility target;
- SFT alone remains competitive but over-refuses many known rows;
- SFT->DPO lowers over-refusal but often gives up too much unknown abstention;
- SFT->KTO is less destructive than DPO but does not clearly beat SFT overall;
- SFT->GRPO is the only downstream path that materially shifts unknown
  abstention in the desired direction, but it can raise known over-refusal and
  has not solved response-confidence calibration.

Amendment F asks whether a third stage can combine these effects better than the
two-stage arms. The core question is whether GRPO should be applied after
preference tuning, or whether GRPO should be followed by a lighter preference
stage to recover known answers and reduce over-refusal.

## 2. Relationship To Existing Protocols

This amendment is additive and exploratory.

- PROTOCOL v0.3 remains the locked plain-answer headline protocol.
- Amendment A remains the plain-answer SFT-warmed sequential extension.
- Amendment B remains the prompt-elicited stated-confidence measurement track.
- Amendment C covers DPO/KTO cross-over stacking without GRPO.
- Amendment D records the first schema response-confidence track.
- Amendment E remains the clean/probe-scaled response-confidence retrain track
  and supplies the current base lineage for this amendment.
- Amendment F does not supersede prior results and must be reported separately.

## 3. Design Change

Use the latest clean Amendment E response-confidence family as the source
lineage unless a later signed amendment replaces it.

Candidate arms:

| Arm | Definition | Purpose |
|---|---|---|
| `clean_sft_dpo_grpo` | `clean SFT -> DPO -> GRPO` | Test whether GRPO can restore unknown abstention after DPO reduces over-refusal. |
| `clean_sft_kto_grpo` | `clean SFT -> KTO -> GRPO` | Test whether GRPO improves a less destructive KTO-warmed policy. |
| `clean_sft_grpo_dpo` | `clean SFT -> GRPO -> DPO` | Test whether DPO can recover known answers after GRPO shifts refusal upward. |
| `clean_sft_grpo_kto` | `clean SFT -> GRPO -> KTO` | Test whether KTO can soften GRPO over-refusal while preserving unknown abstention. |

Default GRPO source should be the latest accepted GRPO reward variant, currently
GRPO v2 from Amendment E. If a newer GRPO reward is adopted before launch, the
source variant must be named in the run record and config.

## 4. Rerun / Launch Requirement

Existing two-stage artifacts can be reused only as source checkpoints after
lineage validation:

1. verify the source arm completed training cleanly;
2. merge the source adapter when the next stage requires a merged base;
3. run a bounded sanity eval of the merged source model before using it as the
   next-stage base;
4. confirm the next-stage config points at the merged source base and not the
   original foundation model;
5. record source metrics and artifact paths in the session note/run record.

Proposed local seed-1 launch order:

| Order | Cell | Gate |
|---:|---|---|
| 1 | `clean_sft_dpo_grpo` | DPO corrected-base full eval exists and merged-source sanity passes. |
| 2 | `clean_sft_kto_grpo` | KTO corrected-base full eval exists and merged-source sanity passes. |
| 3 | `clean_sft_grpo_dpo` | GRPO v2 full eval exists and merged-source sanity passes. |
| 4 | `clean_sft_grpo_kto` | GRPO v2 full eval exists and merged-source sanity passes. |

Seeds 2/3 and 8B are deferred until seed 1 shows that the three-stage pipeline
is interpretable and not merely compounding known failure modes.

## 5. Metrics And Interpretation

Use the full SelfAware eval as the first comparison point and preserve the same
core metrics:

- truthful percentage;
- unknown refusal recall;
- unknown answer rate;
- known over-refusal rate;
- correct-on-known among answered known rows;
- refusal rate;
- response-confidence coverage, mean, unique-value count, and Brier/MAE versus
  response appropriateness when available;
- row-level transitions against clean SFT, the immediate source arm, and GRPO v2
  where relevant.

The simple balanced behavior score used in
`experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv` is
an exploratory summary only. It is not a registered headline metric unless a
later signed protocol freezes it.

Interpretation rules:

- A win must improve the refusal/known-answer tradeoff against its immediate
  source, not only against cold-start DPO/KTO.
- Higher stated confidence is not an improvement unless calibration metrics
  improve.
- GRPO reducing unknown answers by over-refusing known rows is not sufficient.
- A preference stage after GRPO is useful only if it recovers known answers
  without materially reopening unknown answering.

## 6. Implementation Boundary

Project-local artifacts may include:

- seed-specific YAML configs under `experiment/phase1/grpo/configs/`;
- eval configs under `experiment/phase1/eval/config/`;
- run records, session notes, and analysis CSVs;
- generic tuner fixes in `synaptic-tuner/` only when they are reusable outside
  this project.

Do not commit model weights, large generated result rows, cache files, or
restricted data. The `synaptic-tuner/` submodule must remain generic.

## 7. Launch And Reporting Rules

This draft does not authorize launch by itself. A launch decision must name the
exact cell, source checkpoint, merge path, destination run path, eval config,
seed, and lane.

Every result must be labeled as Amendment F / GRPO-centered stacking and must
not be pooled into v0.3, Amendment A, or Amendment E headline claims.

## 8. Sign-Off Checklist

- approval date: 2026-06-24
- approved scope: exploratory local seed-1 three-stage stacking over the clean
  Amendment E response-confidence lineage
- approved cells/seeds/lane: seed 1 local for `clean_sft_dpo_grpo`,
  `clean_sft_kto_grpo`, `clean_sft_grpo_dpo`, and `clean_sft_grpo_kto`
- exact GRPO source variant: GRPO v2 from Amendment E unless a later signed
  amendment supersedes it before a specific cell launches
- exact source checkpoints: clean SFT merged seed 1, clean SFT->DPO seed 1,
  clean SFT->KTO seed 1, and clean SFT->GRPO v2 seed 1 as recorded in the
  Amendment E session note and corrected-base eval configs
- merge/sanity-eval requirements frozen: each source adapter must be merged onto
  its immediate clean lineage before the next stage; a bounded SelfAware sanity
  eval must pass before a full next-stage launch
- schema/metric definitions frozen: use the existing response-confidence JSON
  output contract and the metrics listed in section 5
- excluded cells/seeds: seeds 2/3, 8B, cloud lanes, bridge cells, and any merged
  model publication are deferred until seed-1 local results are interpretable
