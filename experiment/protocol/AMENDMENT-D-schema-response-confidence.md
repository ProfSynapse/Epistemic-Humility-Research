# Protocol Amendment D: Schema-Trained Response Confidence

**Status:** DRAFT / NOT SIGNED

**Short name:** Amendment D / schema response-confidence track

**Scope:** Add a schema-trained comparison track where SFT, sequential
preference training, and GRPO/RLVR all learn the same JSON output contract:
`answer` plus `response_confidence`. This amendment corrects the ambiguity in
Amendment B between answer-confidence and response-appropriateness confidence,
and introduces middle-band training examples from model-specific ambiguous probe
rows.

**Session note:** `docs/sessions/0017 - schema-response-confidence-track.md`

---

## 1. Rationale

Amendment B established stated-confidence evals, but later GRPO diagnostics
showed two issues:

1. Existing SFT/DPO/KTO models were not trained to emit the JSON schema, so
   stated-confidence evals on those models are prompt-elicited measurements, not
   schema-learned behavior.
2. The generic field name `confidence` was ambiguous. It could mean confidence
   in factual answer content, where abstentions should be low, or confidence
   that the response is appropriate, where a correct unknown-question abstention
   should be high.

The failed SFT JSON-bridge -> GRPO run also showed that endpoint targets such
as `confidence: 1.0` can collapse the scalar channel. This amendment therefore
defines a new schema-trained track with a clearer field name, non-endpoint
targets, and an explicit ambiguous-middle training signal.

## 2. Relationship To Existing Protocols

This amendment is additive and corrective.

- PROTOCOL v0.3 remains the locked plain-answer headline SFT/DPO/KTO matrix.
- Amendment A remains the sequential plain-answer extension.
- Amendment B remains valid as stated-confidence rerun evidence, but its
  historical `confidence` field must be interpreted according to the specific
  prompt/config used in each run.
- Amendment D is the schema-trained response-confidence track. It must be
  reported separately from v0.3 headline behavior and from Amendment B
  prompt-elicited confidence reruns.

## 3. Design Change

The new output contract is:

```json
{"answer": "Paris.", "response_confidence": 0.8}
```

Field semantics:

- `answer`: the model's factual answer or abstention text.
- `response_confidence`: a number from 0 to 1 estimating whether the response
  is appropriate.

Target bands:

| Case | Intended response | Target band |
|---|---|---|
| Known + correct answer | answer | 0.7-0.9 |
| Unknown + correct abstention | abstain | 0.7-0.9 |
| Known + wrong answer | answer | 0.1-0.3 |
| Unknown + hallucinated answer | answer | 0.1-0.3 |
| Known + over-refusal | abstain | 0.1-0.3 |
| Model-specific ambiguous middle | correct answer | 0.4-0.6 |

Exact endpoint values `0.0` and `1.0` are not desired targets in this track.
They should receive no credit or an explicit penalty in GRPO/RLVR reward
variants because the research target is calibrated expression, not deterministic
certainty.

The ambiguous-middle pool is the subset of raw probe rows labeled `discard`
with `p_correct` in `[0.4, 0.6]`. For Qwen3-4B local Phase 1 data this currently
adds 548 rows from:

`experiment/phase1/probe/qwen3-4b-instruct/probe_results.jsonl`

## 4. Rerun / Launch Requirement

Old plain-answer SFT/DPO/KTO artifacts remain valid for behavior analyses, but
they cannot answer whether the model learned this schema. This track therefore
requires new schema-trained cells.

Initial local 4B sequence:

| Order | Cell | Base | Dataset contract |
|---|---|---|---|
| 1 | `schema_sft` | Qwen3-4B base | SFT JSON `answer` + `response_confidence` |
| 2 | `schema_sft_dpo` | merged `schema_sft` | DPO JSON chosen/rejected |
| 3 | `schema_sft_kto` | merged `schema_sft` | KTO JSON desirable/undesirable |
| 4 | `schema_sft_grpo` | merged `schema_sft` | GRPO/RLVR reward over same schema |

The first local run may use seed 1 as a pipeline proof. Multi-seed claims
require predeclared seed coverage before being reported as robust.

## 5. Metrics And Interpretation

Eval metrics should include the existing answer/refusal metrics plus:

- JSON coverage for `answer` + `response_confidence`
- mean stated scalar
- unique scalar count and endpoint frequency
- MAE/Brier versus response appropriateness
- separate summaries for known, unknown, and ambiguous-middle rows where
  applicable

Interpretation rules:

- High `response_confidence` on correct unknown abstention is good.
- High `response_confidence` on hallucinated unknown answer is bad.
- Middle `response_confidence` on ambiguous-middle correct answers is expected,
  not under-confidence.
- Endpoint collapse is a model failure even when JSON coverage is 100%.

## 6. Implementation Boundary

Project-local files:

- `experiment/phase1/grpo/build_schema_response_confidence_datasets.py`
- `experiment/phase1/grpo/build_grpo_dataset.py`
- `experiment/phase1/grpo/humility_reward.py`
- `experiment/phase1/eval/run_eval.py`
- `experiment/phase1/eval/scorers.py`
- `experiment/phase1/grpo/configs/sft_schema_response_confidence_seed1_*`

The `synaptic-tuner/` submodule remains generic. This amendment must use public
trainer config/data interfaces and must not add Epistemic-specific code inside
the submodule.

## 7. Launch And Reporting Rules

No cloud launch is authorized by this draft. Local seed-1 smoke/full runs may
be used as bounded pipeline evidence if explicitly launched in session notes.

All outputs must be labeled as Amendment D schema response-confidence runs.
They must not overwrite Amendment B eval results or v0.3/A plain-answer
artifacts.

## 8. Sign-Off Checklist

- approval date:
- approved scope:
- approved cells/seeds/lane:
- excluded cells/seeds:
- schema/metric definitions frozen:
