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

External evidence supports deriving the target from sampled correctness rather
than from sequence log-probability. Zenn & Geiping (arXiv:2606.27359) find that
per-sample sequence-probability/correctness rank correlations are distributed
symmetrically around zero, so log-probability is not a reliable lever for
ranking repeated responses to the same prompt. The probe-scaled target below
uses empirical `p_correct` over 32 samples, an accuracy estimate rather than a
probability lever, which is the better-grounded signal under that finding.

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

Important semantic constraint: high `response_confidence` is not the same thing
as high factual-answer confidence. It means the emitted response is appropriate.
Therefore, saying "I don't know" on a true unknown should receive high
`response_confidence`, because the abstention is correct. Conversely,
model-ambiguous rows should not be forced into abstention by default; they can
remain answerable, but the answer should carry low-to-middle confidence to
express uncertainty.

Final training target:

```text
response_confidence = 0.1 + 0.8 * response_appropriateness_p
```

This maps responses into non-endpoint `[0.1, 0.9]` space. For example, a
question the base model got wrong on all 32 samples gives an abstention target
near `0.8765` and a factual-answer target near `0.1235`; a 16/32 question maps
near `0.5`.

### 3.1 Seed-1 v1 Result: Probe Scaling Alone Was Insufficient

The first local seed-1 probe-scaled schema-SFT run completed successfully, but
the scalar still collapsed:

- SFT run:
  `scratch/schema_response_confidence/runs/sft_schema_probe_scaled_seed1_full/20260623_095638`
- mixed SelfAware smoke config:
  `experiment/phase1/eval/config/eval_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_local_4b.yaml`
- eval result:
  `experiment/phase1/eval/results_amendment_e_response_confidence_selfaware_probe_scaled_sft_seed1_smoke_4b`

The eval had 100% JSON/response-confidence coverage over 192 rows, but every
row emitted `response_confidence: 0.8765`. The training target histogram explains
the failure: the SFT dataset had 20 target values, but `0.8765` still accounted
for 12,222 / 14,943 rows (81.79%). This result is therefore a target-imbalance
failure, not evidence that calibrated scalar expression is impossible.

Follow-up Amendment E revisions must prevent SFT from solving the scalar loss by
emitting the modal value.

### 3.2 Seed-1 v2 Exploratory Branch: Full-Size Contrastive Target Shaping

Rather than dropping rows to balance target values, v2 adds a full-size
contrastive SFT projection derived from the DPO chosen/rejected pairs:

| Source row | SFT target role | Confidence target |
|---|---|---|
| chosen response | appropriate | deterministic spread in `[0.70, 0.90]` |
| rejected response | inappropriate | deterministic spread in `[0.10, 0.35]` |
| ambiguous/discard answer row | ambiguous_answer | deterministic spread in `[0.35, 0.60]` |

The deterministic spread is keyed by role, probe row key, and answer text:

```text
response_confidence = band_low + (band_high - band_low) * stable_hash(role, key, answer)
```

This is an UaIT-style contrastive supervision revision: SFT sees high-confidence
appropriate behavior and low-confidence inappropriate behavior instead of only
high-confidence successful rows. It preserves the semantic constraint that a
correct "I don't know" on a true unknown is high-confidence, while a known
question over-refusal is low-confidence.

Regenerated local dataset audit:

- contrastive SFT rows: 29,338
- appropriate rows: 14,395
- inappropriate rows: 14,395
- ambiguous-answer rows: 548
- unique response-confidence targets: 4,986
- target range: `[0.10, 0.90]`
- mean target: `0.512539`
- largest exact target count: 20 rows

This v2 dataset is an exploratory diagnostic branch, not the preferred mainline.
It directly tests whether supervised low/high contrast can make the scalar move,
but because it supervises rejected completions in SFT, it blurs the intended
boundary between format/style learning and preference/accuracy tuning.

### 3.3 Seed-1 v3 Mainline Revision: Clean SFT, Preference Contrast Later

The preferred mainline separates the stages:

- SFT teaches the JSON format, appropriate answer/abstention style, and broad
  confidence bands.
- DPO/KTO/GRPO carry the bad-response contrast and accuracy/calibration tuning.

The clean SFT projection contains only appropriate completions:

| Source row | SFT target role | Rows | Confidence target |
|---|---|---:|---|
| known SFT answer | appropriate | 7,981 | deterministic spread in `[0.70, 0.90]` |
| unknown SFT abstention | appropriate | 6,414 | deterministic spread in `[0.70, 0.90]` |
| ambiguous/discard answer row | ambiguous_answer | 548 | deterministic spread in `[0.35, 0.60]` |

Local dataset audit:

- clean SFT rows: 14,943
- appropriate known rows: 7,981
- appropriate unknown rows: 6,414
- ambiguous-answer rows: 548
- unique response-confidence targets: 2,489
- target range: `[0.3508, 0.90]`
- mean target: `0.788340`
- largest exact target count: 17 rows

Rejected completions, wrong answers, and known-question over-refusals are
excluded from clean SFT and reserved for DPO/KTO/GRPO.

## 4. Rerun / Launch Requirement

The prior Amendment D schema-SFT, schema-SFT->DPO, schema-SFT->KTO, and
schema-SFT->GRPO artifacts cannot answer the probe-scaled target question.
They remain useful as evidence for the constant-target failure mode.

Required rerun sequence:

| Order | Cell | Base | Dataset contract |
|---|---|---|---|
| 1 | `schema_clean_sft` | Qwen3-4B base | clean SFT JSON |
| 2 | `schema_clean_sft_dpo` | merged clean SFT | schema DPO JSON |
| 3 | `schema_clean_sft_kto` | merged clean SFT | schema KTO JSON |
| 4 | `schema_clean_sft_grpo` | merged clean SFT | GRPO over same schema/reward family |

The `schema_contrastive_sft` branch is allowed as an exploratory scalar-movement
diagnostic, but downstream DPO/KTO/GRPO should not use it as the default base
unless its eval is explicitly being interpreted as contrastive-SFT evidence.

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
- `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_smoke_config.py`
- `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_full_config.py`
- `experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_smoke_config.py`
- `experiment/phase1/grpo/configs/sft_schema_clean_response_confidence_seed1_full_config.py`
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
