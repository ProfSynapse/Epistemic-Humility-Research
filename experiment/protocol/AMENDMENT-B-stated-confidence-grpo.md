# Protocol Amendment B: Stated Confidence and GRPO Calibration Reward

**Status:** SIGNED OFF for stated-confidence measurement and reporting
(user approval, 2026-06-19). This amendment is accepted as an additive
measurement extension to the signed Phase 1 protocol. It does not silently
replace the signed PROTOCOL v0.3 plain-answer headline matrix or Amendment A
plain-answer sequential results.

**GRPO/RLVR status:** prospective only. This sign-off accepts the
answer/confidence output contract, stated-confidence reruns, and confidence
scoring/reporting rules. It does not authorize new GRPO/RLVR training runs
without a separate launch decision.

**Short name:** Amendment B / stated-confidence GRPO

**Scope:** Add a structured stated-confidence output contract to Phase 1 evals,
rerun existing evals under that contract to establish baselines across training
regimens and seeds, and define the prospective GRPO/RLVR arm with a
calibration-aware reward.

**Session note:** `docs/sessions/0003 - grpo-stated-confidence.md`

---

## 1. Rationale

The signed v0.3 experiment measures answer/refusal behavior, self-consistency
confidence, token-level ECE, and hidden-state coherence. Those measurements
answer whether a model abstains appropriately and whether token/logprob or
sampling-derived confidence changes after training, but they do not require the
model to state its own confidence in ordinary QA responses.

Amendment B adds that missing layer. The goal is to measure whether a model's
stated confidence tracks:

1. the model-specific known/unknown boundary from the probe split, and
2. whether the generated factual answer content is actually correct.

This is also the measurement baseline needed before evaluating any GRPO/RLVR
training objective that rewards calibrated uncertainty.

## 2. Relationship To Existing Protocols

This amendment is additive.

- v0.3 remains the locked headline SFT/DPO/KTO comparison.
- Amendment A remains the prospective sequential-refinement extension
  (`SFT -> DPO`, `SFT -> KTO`).
- Amendment B results must be labeled separately as stated-confidence rerun
  evidence unless and until a later signed protocol revision supersedes the
  headline matrix.
- Old eval outputs without the Amendment B JSON fields remain valid for their
  original answer/refusal, self-consistency, token-ECE, and hidden-state
  analyses, but cannot be retrofitted into stated-confidence metrics.

## 3. Output Contract

Every Amendment B evaluation generation, and every Amendment B GRPO-training
completion, must return only a JSON object with exactly these two keys:

```json
{"answer": "Paris.", "confidence": 0.73}
```

Field semantics:

- `answer`: the model's factual answer or abstention text.
- `confidence`: a number from 0 to 1 representing the model's probability that
  its factual answer content is correct.

For a clean abstention, calibrated `confidence` should be low because the model
is not asserting a factual answer. This definition intentionally separates
"confidence that the answer text is factually correct" from "confidence that
abstaining was the right policy."

Malformed JSON, missing keys, non-string `answer`, or non-numeric `confidence`
are scorer-visible failures. The scorer may still use raw text for ordinary
answer/refusal metrics, but stated-confidence coverage for that row is missing.

## 4. Eval Rerun Requirement

Amendment B is not only a GRPO training change. It adds a stated-confidence
measurement layer to the whole Phase 1 comparison.

Before comparing GRPO stated-confidence behavior against prior methods, the
existing eval suite must be rerun under the JSON output contract for every
baseline/regimen whose stated-confidence behavior will be compared:

| Block | Arms / regimens | Seed treatment | Purpose |
|---|---|---|---|
| Base | base model | deterministic eval seed(s) as configured | stated-confidence reference point |
| v0.3 headline | SFT, DPO, KTO | all relevant completed/reportable seeds | baseline across the signed training methods |
| v0.3 panels | LR/beta panel cells if cited in stated-confidence analysis | matching panel seeds | robustness-only, never headline replacement |
| Amendment A | `SFT -> DPO`, `SFT -> KTO` where included | all relevant completed/reportable seeds | stated-confidence readout for sequential refinement |
| Amendment B | GRPO/RLVR stated-confidence cells | predeclared seeds before launch | new method comparison |

All reruns used in the same table or figure must use the same JSON prompt,
same parser, same eval set definition, and same stated-confidence metrics.

## 5. Metrics

Eval parsing preserves:

- `generated_answer`: raw model output
- `answer_text`: parsed `answer` field when JSON is valid, otherwise raw text
- `stated_confidence`: parsed float or null

Stated-confidence summary metrics:

- `coverage_pct`: fraction of rows with parseable stated confidence
- `mae_vs_known_label`: mean absolute distance from the probe-label target,
  where known = 1 and unknown = 0
- `brier_vs_known_label`: mean squared distance from the same known/unknown
  target
- `mae_vs_answer_correctness`: mean absolute distance from factual answer
  correctness, where correct answer content = 1 and incorrect/non-answer content
  = 0
- `brier_vs_answer_correctness`: mean squared distance from factual answer
  correctness

Interpretation:

- `*_vs_known_label` asks whether stated confidence tracks the model-specific
  knowledge boundary.
- `*_vs_answer_correctness` asks whether stated confidence tracks the truth of
  the produced factual answer content.
- Brier metrics penalize confident wrong answers quadratically and should be
  reported with coverage because a model can otherwise dodge calibration
  measurement by failing the output contract.

## 6. Prospective GRPO Reward

Use a verifiable reward over the same model-specific known/unknown split:

- known + correct answer + high stated confidence: high reward
- known + abstention: over-refusal penalty
- known + wrong answer: wrong-answer penalty, larger when confidence is high
- unknown + explicit abstention + low confidence: positive abstention reward
- unknown + answer/guess: wrong-answer penalty, larger when confidence is high
- generic hedging on known-correct answers: small penalty

The initial implementation lives in:

- `experiment/phase1/grpo/humility_reward.py`
- `experiment/phase1/grpo/build_grpo_dataset.py`

This code must remain outside `synaptic-tuner/`. The tuner should receive it
through its existing custom GRPO reward and dataset interfaces; project-specific
experiment logic must not be committed into the submodule.

### Prospective GRPO Candidate Cells

The current requested GRPO candidate set is:

| Model size | Lane | Seed scope | Arm | Definition | Recipe status |
|---|---|---|---|---|---|
| 4B | local or approved lane | seeds 1, 2, and 3 | `grpo` | GRPO/RLVR from the Qwen3-4B base model using the Amendment B answer/confidence reward contract. | Checklist only; no runnable Phase 1 recipe until dataset projection, reward wiring, and tuner dispatch are confirmed. |
| 4B | local or approved lane | seeds 1, 2, and 3 | `sft_grpo` | Merge/use the matched SFT seed as the starting model, then train GRPO/RLVR with the Amendment B reward contract. | Checklist only; additionally requires exact seed-specific SFT merged model paths and base/reference semantics. |

These cells are prospective and do not authorize launch. They are not part of
the signed v0.3 matrix/count assertions, and they must not be represented as
runnable YAML until the generic tuner route can truthfully express the intended
GRPO base model, reward function, dataset projection, and artifact output path.

## 7. Launch And Reporting Rules

No training or eval reruns are authorized by this amendment text alone. Each
local or cloud launch still requires explicit approval for the exact cells,
seeds, and lane.

Before running Amendment B cells:

1. Enumerate the exact arms, seeds, eval configs, and output directories.
2. Confirm whether v0.3 panel cells and Amendment A cells are included in the
   stated-confidence analysis.
3. Ensure outputs are labeled as Amendment B stated-confidence reruns.
4. Preserve old v0.3 and Amendment A result artifacts; do not overwrite them.
5. Write run/session records that point back to this amendment and the session
   note.

Reporting language must distinguish:

- original v0.3 headline answer/refusal results
- Amendment A sequential-refinement results
- Amendment B stated-confidence rerun evidence
- prospective Amendment B GRPO/RLVR training results

## 8. Sign-Off Record

- Approval date: 2026-06-19
- Approved rerun/reporting scope: accepted stated-confidence reruns using the
  answer/confidence-only JSON contract, including completed SelfAware sequential
  Amendment A cells where available.
- Supersession: no silent supersession of v0.3 plain-answer headline results or
  Amendment A plain-answer sequential results. Stated-confidence runs are a
  separate measurement layer.
- GRPO authorization: not approved by this sign-off. Future GRPO/RLVR cells
  require separate explicit launch approval.
- Output schema: strict JSON with `answer` and `confidence`.
- Metrics: coverage, mean stated confidence, MAE and Brier against the
  model-specific known/unknown label, and MAE and Brier against factual answer
  correctness.
