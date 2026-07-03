---
amendment: L
slug: answer-subspan-masked-contrastive-sft
question: >-
  Does masking the wrong-answer sub-span in contrastive SFT recover behavior
  while retaining Amendment K's calibration win?
predictions:
  orchestrator:
    call: masking retains calibration and recovers behavior gate
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  Per Amendment N table, behavior PASSED but calibration went to chance
  (AUROC 0.552) with inverted cell ordering — masking recovered behavior
  but destroyed the calibration carrier.
scoreboard: null
---

# Protocol Amendment L: Answer-Sub-Span-Masked Contrastive Schema-SFT

**Status:** SIGNED — user-authorized 2026-06-27 ("Approve")

**Short name:** Amendment L / masked-contrastive-SFT calibration base

**Scope:** Authorize one new local SFT cell, `schema_contrastive_masked_sft_seed1`
(seed 1, local 4B lane), identical to the Amendment K contrastive cell EXCEPT that
the wrong-answer text on inappropriate rows is excluded from the training loss via
a new, generic `synaptic-tuner` engine feature (per-row sub-span loss masking).
This directly attacks the §3.2 root cause that caused Amendment K to fail its
behavior gate, while preserving the calibration signal that Amendment K proved
works at the SFT stage. It does NOT modify PROTOCOL v0.3, Amendment E
(clean-SFT mainline), Amendment J (GRPO v3), or the Amendment K artifact (which
stays on record as the unmasked result). Reported separately as an alternative
base.

**Session note:** `docs/sessions/0026 - caution-vs-doubt-knowledge-gate.md`

---

## 1. Rationale

Amendment K (full contrastive schema-SFT) was the first objective in the whole
calibration-gap thread to **install behavior-conditional response confidence** at
the SFT stage. Its §4.1 calibration gate PASSED all four metrics decisively:

| metric | gate | Amendment K | clean-SFT / GRPO v3 |
|---|---|---|---|
| emitted AUROC→appropriateness | ≥0.62 | **0.684** | ≈0.52 |
| emitted std | ≥0.10 | **0.309** | 0.047 / 0.027 |
| ECE-vs-appropriateness | <0.30 | **0.183** | 0.40–0.44 |
| known_correct > known_wrong (mean) | — | 0.670 > 0.306 | fails |
| unknown_refused > unknown_answered_wrong (mean) | — | 0.581 > 0.156 | fails |
| (bonus) correct-vs-wrong AUROC, answered-known | — | 0.789 | 0.600 (v3) |

But its §4.2 behavior gate FAILED 3 of 4 (truthful 30.93<35.6, correct_on_known
36.63<42.2, over_refusal 79.2>67.5; refusal_recall 83.72 OK) and the cell was
REJECTED. The cause is the documented Amendment K §3.2 PRIMARY RISK: the SFT loss
mask (`completion_only_loss` / `assistant_only`) masks only the *prompt*, so on the
14,395 inappropriate rows the model is trained on the **wrong-answer text** carried
inside the assistant JSON, not only on the low confidence. Behavior degraded
(over-refusal up, correctness down) exactly as predicted.

**Diagnosis confirmed in the engine.** `shared/sft_preprocessing.py ::
materialize_sft_example` builds `labels = list(input_ids)` and, for
`assistant_only`, masks only the matching prompt prefix
(`labels[idx] = -100` for the prompt tokens). The entire assistant content —
`{"answer": "<wrong answer>","response_confidence": <low>}` — is therefore
supervised, including the wrong-answer value.

**This amendment** finishes the experiment correctly: keep the contrastive
high/low confidence contrast (the part that worked), but stop supervising the
wrong-answer text (the part that broke behavior), by masking the answer *value*
sub-span on inappropriate rows. Hypothesis: with the wrong-answer supervision
removed, the calibration win of Amendment K is retained while the behavior gate
recovers toward the clean-SFT base.

## 2. Relationship To Existing Protocols

- PROTOCOL v0.3 — locked plain-answer headline matrix. Untouched.
- Amendment E — clean-SFT base and clean cell. Untouched, remain canonical.
- Amendment J — GRPO v3 proper-scoring negative result. Untouched.
- Amendment K — the unmasked contrastive cell + its REJECTED disposition stay on
  record. This cell is the masked successor, reported separately. Do not pool
  with the clean-SFT base or the v0.3 headline matrix.

## 3. Design Change

### 3.1 Generic engine feature (synaptic-tuner) — per-row sub-span loss masking

Add an optional, backward-compatible capability to the canonical SFT
preprocessing primitive so a dataset row may declare literal text spans within the
rendered sequence to **exclude from the loss** (labels set to `-100`). This is a
generic engine feature (any research project can use it to supervise a sub-span of
an assistant message); it is NOT epistemic-specific.

- `shared/sft_preprocessing.py :: materialize_sft_example` gains a
  `loss_mask_spans: list[str] | None = None` parameter. When provided and
  non-empty, it encodes `full_str` with `return_offsets_mapping=True`, finds each
  span string's character range in the rendered text, and sets `labels = -100`
  for every token overlapping that range (applied AFTER the existing prompt /
  assistant_only masking). When `None`/empty, behavior is **byte-identical** to
  today (default path unchanged; no offsets call).
- The directive is threaded through `Trainers/sft/src/preprocessing.py`
  (`materialize_sft_features`, `prepare_sft_dataset`) and read from the dataset
  row key `loss_mask_text` (a list of literal strings). Rows without the key are
  unaffected.
- Fast-tokenizer requirement: offset mapping requires a fast tokenizer (Qwen3 is
  fast). If offsets are unavailable, raise a clear error rather than silently
  training the span.
- `loss_mask_mode` provenance string gains a suffix when spans were applied
  (e.g. `assistant_only+subspan_masked`) so `training_lineage.json` records it.

### 3.2 Builder change (epistemic) — emit the answer-value mask directive

`build_schema_response_confidence_datasets.py :: build_contrastive_sft_rows`
emits `loss_mask_text` on **inappropriate** rows only, containing the exact
rendered answer-value substring (the escaped inner content of the `answer` field
as produced by `_schema_payload` → `json.dumps`). Appropriate rows (gold-correct
answers and gold abstentions) and ambiguous_answer rows (gold answers) are
UNCHANGED — their answer text remains supervised, exactly as in Amendment K.

Net effect per row type:

| role | answer value | response_confidence | other JSON structure |
|---|---|---|---|
| appropriate | supervised | supervised | supervised |
| inappropriate | **masked (−100)** | supervised | supervised |
| ambiguous_answer | supervised | supervised | supervised |

The model still learns to emit a valid JSON envelope and the low confidence on
inappropriate rows; it no longer learns to emit the wrong answer text.

The masked dataset is written to a NEW file
`scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive_masked.jsonl`
so the Amendment K artifact is left untouched. The only difference from the K
dataset is the additive `loss_mask_text` column on inappropriate rows; messages
and confidence values are identical (verified by diff of the shared columns).

### 3.3 Training cell

- Cell name: `schema_contrastive_masked_sft_seed1`. Seed 1, local 4B lane.
- Base model: `unsloth/Qwen3-4B-bnb-4bit` (same as clean-SFT / Amendment K).
- Recipe mirrors clean-SFT / Amendment K EXACTLY (LoRA r32/α64/dropout 0.05
  all-linear; batch 10; LR 2e-4; 1 epoch; warmup 0.03; linear; adamw_8bit; bf16;
  seed 1; `completion_only_loss: true`). The ONLY differences from Amendment K
  are (a) the engine honors `loss_mask_text`, and (b) the dataset carries it. So
  any behavior recovery is attributable to removing wrong-answer supervision.
- Configs (YAML, like the GRPO trainer):
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_masked_response_confidence_seed1_smoke.yaml`
  - `experiment/phase1/grpo/configs/sft_schema_contrastive_masked_response_confidence_seed1_full.yaml`

## 4. Launch Sequence And Gates

1. **Engine unit test (CPU):** a `synaptic-tuner` test proves that with
   `loss_mask_text` set to the answer value, the answer-value tokens are `-100`
   and the `response_confidence` tokens remain supervised; and that with no
   directive the labels are byte-identical to the prior path. GREEN required.
2. **CPU preflight (data):** confirm the masked dataset carries `loss_mask_text`
   on exactly the inappropriate rows (n=14,395), absent on appropriate/ambiguous,
   and that each span is found in the rendered sequence. GREEN required.
3. **Smoke** (`..._smoke.yaml`, max_steps ~32): exit 0; training_lineage reports
   `loss_mask_mode: assistant_only+subspan_masked` and the masked dataset; loss
   decreasing.
4. **Full** (`..._full.yaml`, 1 epoch ≈ 2,934 steps): exit 0; adapter + lineage.
5. **Merge** the adapter to a 16-bit base (same as clean-SFT / Amendment K).
6. **Eval** on SelfAware (mirror the Amendment K eval config) + run
   `calibration_gap_report.py` on its scored_rows.

### 4.1 Calibration gate (must hold to call the cell a calibration success)

Reuse Amendment K §4.1 (the bar the mechanism already cleared):

- emitted AUROC→appropriateness ≥ **0.62**;
- behavior-conditional cell means: known_correct_answered > known_answered_wrong
  AND unknown_refused > unknown_answered_wrong;
- emitted std ≥ **0.10**;
- ECE-vs-appropriateness < **0.30**.

Expectation: calibration should be RETAINED at roughly Amendment K levels (masking
removes answer-text gradient, not the confidence contrast).

### 4.2 Behavior gate (the objective of this amendment — must PASS)

Baseline = clean-SFT merged base (SelfAware full): over_refusal 57.51%,
truthful 40.58%, correct_on_known 47.23%, refusal_recall 87.02%.

- truthful_pct ≥ **35.6**;
- correct_on_known_pct ≥ **42.2**;
- over_refusal_pct ≤ **67.5**;
- refusal_recall_pct ≥ **82.0**.

This is the gate Amendment K failed (3/4). PASSING it here — with calibration
retained — is the success condition for the whole contrastive-SFT line.

If behavior STILL fails with calibration retained, the conclusion is that the
contrastive low-confidence rows degrade behavior through a channel other than
wrong-answer supervision (e.g. the abstention/over-refusal answer text itself, or
distributional shift), and the fall-back is the §3.2-of-K probe-scaled approach
(appropriate rows + a small ~15% contrastive low tail) under a further amendment.

## 5. Implementation Boundary

In scope: the generic engine sub-span-masking feature + its unit test in
`synaptic-tuner` (authorized generic engine improvement); the builder
`loss_mask_text` emission + tests; the new masked dataset file; the two SFT YAML
configs; the merge + eval + calibration_gap reporting; session-note checkpoints.
No change to PROTOCOL v0.3, Amendment E artifacts, the clean-SFT base, Amendment
J, or the Amendment K artifact.

## 6. Sign-Off Checklist

- approval date: 2026-06-27
- approved scope: one local seed-1 SFT cell `schema_contrastive_masked_sft_seed1`,
  trained to completion, local 4B lane; one generic engine feature (per-row
  sub-span loss masking) + tests
- approved dataset: `sft_response_confidence_train_contrastive_masked.jsonl`
  (deterministic builder output; additive `loss_mask_text` column vs the K dataset)
- excluded: any change to PROTOCOL v0.3 headline matrix, Amendment E artifacts,
  the clean-SFT base, Amendment J, or the Amendment K artifact
- gates frozen: yes (§4 calibration gate reused from K + behavior gate)
- risk acknowledged: yes (offsets require a fast tokenizer; masking is additive
  and byte-identical when absent; behavior-via-other-channel fallback documented)
- authorization: user, 2026-06-27 — "Approve"
