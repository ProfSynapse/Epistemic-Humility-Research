# Protocol Amendment E: Probe-Scaled Response Confidence Targets

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment E / probe-scaled response-confidence retrain

**Scope:** Replace Amendment D's mostly constant schema response-confidence
targets with targets derived from the model's original 32-sample probe
performance. This amendment keeps the Amendment D JSON contract but changes the
training target construction before rerunning schema-SFT and downstream
SFT->DPO/KTO/GRPO cells.

**Session note:** `docs/sessions/0018 - probe-scaled-response-confidence-retrain.md`

---

## 1. Rationale

Amendment D established the `answer` + `response_confidence` schema, but the
first local seed-1 results showed scalar collapse:

- merged schema-SFT full SelfAware eval emitted `response_confidence: 0.8` on
  all 3,369 rows
- schema-SFT->KTO smoke also emitted constant `0.8`
- corrected schema-SFT->GRPO full SelfAware eval also emitted constant `0.8`

The dataset audit showed why this was likely: the SFT projection contained
14,395 ordinary rows with `response_confidence: 0.8`, 548 ambiguous-middle rows
in `[0.4, 0.6]`, and no ordinary low-confidence or varied high-confidence SFT
targets. The model learned the output envelope but had little reason to learn a
usable scalar.

## 2. Relationship To Existing Protocols

This amendment is additive and corrective relative to Amendment D.

- PROTOCOL v0.3 remains the locked plain-answer headline matrix.
- Amendment A remains the sequential plain-answer extension.
- Amendment B remains prompt-elicited stated-confidence evidence.
- Amendment D remains the first schema-trained response-confidence track and
  records the constant-target failure mode.
- Amendment E changes the schema target construction for a rerun track. It does
  not retroactively relabel Amendment D results.

## 3. Design Change

The JSON output contract is unchanged:

```json
{"answer": "...", "response_confidence": 0.73}
```

The target scalar is now derived from the original probe result for the same
question:

- source: `experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`
- signal: `sampled_correct` / `p_correct` from 32 stochastic samples
- factual confidence estimate:

```text
factual_p = (correct_samples + 1) / (n_samples + 2)
```

This Laplace-smoothed estimate avoids hard 0/1 endpoints while preserving the
observed 32-sample score.

Response-appropriateness probability:

| Target response type | response_appropriateness_p |
|---|---|
| factual answer | `factual_p` |
| abstention/refusal | `1 - factual_p` |

Final training target:

```text
response_confidence = 0.1 + 0.8 * response_appropriateness_p
```

This maps responses into non-endpoint `[0.1, 0.9]` space. For example, a
question the base model got wrong on all 32 samples gives an abstention target
near `0.8765` and a factual-answer target near `0.1235`; a 16/32 question maps
near `0.5`.

## 4. Rerun / Launch Requirement

The prior Amendment D schema-SFT, schema-SFT->DPO, schema-SFT->KTO, and
schema-SFT->GRPO artifacts cannot answer the probe-scaled target question.
They remain useful as evidence for the constant-target failure mode.

Required rerun sequence:

| Order | Cell | Base | Dataset contract |
|---|---|---|---|
| 1 | `schema_probe_scaled_sft` | Qwen3-4B base | probe-scaled SFT JSON |
| 2 | `schema_probe_scaled_sft_dpo` | merged probe-scaled SFT | probe-scaled DPO JSON |
| 3 | `schema_probe_scaled_sft_kto` | merged probe-scaled SFT | probe-scaled KTO JSON |
| 4 | `schema_probe_scaled_sft_grpo` | merged probe-scaled SFT | GRPO over same schema/reward family |

Start with seed 1 local smoke/full before scaling to additional seeds.

## 5. Metrics And Interpretation

Use the Amendment D eval metrics plus explicit scalar-distribution checks:

- JSON coverage for `answer` + `response_confidence`
- unique `response_confidence` count
- confidence histogram by known/unknown/refusal/correctness
- endpoint frequency
- MAE/Brier versus response appropriateness
- known over-refusal and unknown answering against nearest controls

Interpretation:

- Success requires scalar movement, not just JSON coverage.
- A model that still emits one scalar value on every row fails the confidence
  expression question even if refusal behavior improves.
- GRPO reward improvements must be interpreted jointly with known over-refusal;
  reducing unknown answering by over-refusing known questions is not sufficient.

## 6. Implementation Boundary

Project-local files:

- `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
- `experiment/phase1/grpo/tests/test_build_schema_response_confidence_datasets.py`
- `experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_smoke_config.py`
- `experiment/phase1/grpo/configs/sft_schema_probe_scaled_response_confidence_seed1_full_config.py`
- Amendment E eval configs to be added after a successful probe-scaled SFT
  checkpoint exists

Generated scratch datasets and model artifacts remain uncommitted.

The `synaptic-tuner/` submodule remains generic. No Epistemic-specific logic
should be added inside the submodule for this amendment.

## 7. Launch And Reporting Rules

No launch is authorized by this draft alone. The first local seed-1 smoke/full
launch should be recorded in the session note with dataset manifest evidence
and post-run eval checks.

Report these outputs separately as Amendment E / probe-scaled
response-confidence runs. Do not pool them with Amendment D constant-target
results except as explicit controls.

## 8. Sign-Off Checklist

- approval date:
- approved scope:
- approved cells/seeds/lane:
- excluded cells/seeds:
- schema/metric definitions frozen:
