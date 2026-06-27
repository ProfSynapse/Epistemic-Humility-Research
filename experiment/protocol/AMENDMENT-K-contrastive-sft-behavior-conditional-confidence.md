# Protocol Amendment K: Full Contrastive Schema-SFT for Behavior-Conditional Response Confidence

**Status:** SIGNED — user-authorized 2026-06-27 ("Proceed")

**Short name:** Amendment K / contrastive-SFT calibration base

**Scope:** Authorize one new local SFT cell, `schema_contrastive_sft_seed1`
(seed 1, local 4B lane), trained to completion. This is a NEW supervised base
that installs behavior-conditional response-confidence at the SFT stage. It does
NOT modify PROTOCOL v0.3, Amendment E (clean-SFT mainline / clean cell), or
Amendment J (GRPO v3). It is reported separately as an alternative base, not a
replacement for the clean-SFT base that E/J build on.

**Session note:** `docs/sessions/0026 - caution-vs-doubt-knowledge-gate.md`

---

## 1. Rationale

The calibration-gap thread has now falsified the "SFT teaches format, RL teaches
calibration" division of labor end to end. Five downstream objectives on the
clean-SFT base (DPO, KTO, GRPO v1, GRPO v2, GRPO v3) all failed to install
calibrated, behavior-conditional response confidence:

- The clean-SFT base emits near-constant confidence (eval std 0.047, AUROC≈0.52
  on appropriateness).
- GRPO v3 (Amendment J, proper-scoring Brier reward) did not fix it: emitted std
  0.013→0.027 (still collapsed), AUROC→appropriateness 0.520→0.522 (chance),
  ECE-vs-appropriateness 0.403→0.440 (worse). Only correct-vs-wrong AUROC among
  answered-known rows moved (0.521→0.600).

**Mechanistic diagnosis (GRPO v3 reward trace, full run).** The GRPO reward is a
single summed scalar (behavior ±2.0 + proper_score ±1.2) that GRPO assigns to
every token via shared advantage. Decomposing the within-group reward variance
that the advantage is computed from: the proper-score (calibration) term owns
only **3.2%**; behavior reinforcement owns ~89%. So ~97% of the gradient shaping
the policy — including the confidence tokens — is behavior, which reinforces the
model's habitual high-confidence committal completions and drags the confidence
mode *up*. Inline RL is structurally signal-starved for a 3-token readout
embedded in a ~26-token completion.

**Root cause of the collapse is upstream, at SFT.** `build_clean_sft_rows`
supervises ONLY appropriate completions (known→gold-correct answer, unknown→
abstention), all in the high band [0.70, 0.90], with the within-band spread being
deterministic hash noise uncorrelated with anything. The model is never shown a
single training example warranting low confidence, so it cannot learn to emit it.
The constant-confidence habit is installed at SFT; no downstream objective tried
so far has had a strong enough, well-credited signal to overcome it.

**Positive existence proof.** The exploratory contrastive SFT (session 0018,
Amendment E branch), even half-trained (checkpoint-1500 of 2934, interrupted by a
host restart), produced behavior-conditional confidence — the one thing no
downstream RL achieved:

| cell | mean emitted confidence (ckpt-1500) |
|---|---|
| known_correct_answer | 0.444 |
| known_wrong_answer | 0.280 |
| known_over_refusal | 0.465 |
| unknown_refusal | 0.668 |
| unknown_answer | 0.246 |

It was abandoned only because its *behavior* was poor (half-trained; supervised
on rejected wrong/over-refusal completions). The calibration mechanism worked.

**This amendment** finishes that experiment cleanly: train the contrastive
schema-SFT to completion and gate hard on behavior. Hypothesis: supervised
high/low contrast installs behavior-conditional confidence at the SFT stage
(shaping the *greedy mode* that eval reads), at far lower cost and with far
cleaner credit assignment than inline RL.

## 2. Relationship To Existing Protocols

- PROTOCOL v0.3 remains the locked plain-answer headline matrix. Untouched.
- Amendment E remains the schema target-construction track. Its clean-SFT base
  and clean cell are untouched and remain canonical for the E/J runs.
- Amendment J (GRPO v3) is untouched and remains valid as the proper-scoring
  negative result.
- This cell is a NEW supervised base. Do not pool it with the clean-SFT base or
  report its numbers under the v0.3 headline matrix. Report as
  "contrastive-SFT / behavior-conditional confidence base."

## 3. Design Change

### 3.1 Training cell

- Cell name: `schema_contrastive_sft_seed1`. Seed 1, local 4B lane.
- Base model: `unsloth/Qwen3-4B-bnb-4bit` (identical to the clean-SFT base — the
  ONLY difference from the clean-SFT cell is the training dataset).
- Dataset: `scratch/schema_response_confidence/qwen3-4b-instruct/sft_response_confidence_train_contrastive.jsonl`
  (deterministic output of the committed builder
  `build_schema_response_confidence_datasets.py :: build_contrastive_sft_rows`).
  29,338 rows, bimodal by appropriateness role:
  - appropriate (n=14,395): mean 0.801, band [0.70, 0.90];
  - inappropriate (n=14,395): mean 0.226, band [0.10, 0.35];
  - ambiguous_answer (n=548): mean 0.473, band [0.35, 0.60].
- Recipe mirrors the clean-SFT cell EXACTLY (LoRA r32/α64/dropout 0.05 all-linear;
  per-device batch 10; LR 2e-4; 1 epoch; warmup 0.03; linear; adamw_8bit; bf16;
  seed 1; `completion_only_loss: true` / `assistant_only` mask). Only the dataset
  differs, so any calibration/behavior delta is attributable to the data.

### 3.2 Known risk and mitigation (PRIMARY THREAT)

The trainer's `completion_only_loss` / `assistant_only` mask masks the *prompt*,
not the answer sub-span inside the assistant message. The schema output is one
JSON object (`{"answer": ..., "response_confidence": ...}`), so on the
inappropriate (rejected) rows the model is trained on the *wrong-answer text*,
not only the low confidence. This is the behavior risk that degraded the
half-trained contrastive run. Answer-sub-span masking would require editing the
`synaptic-tuner` submodule, which is out of bounds. **Mitigation = the hard
behavior gate in §4.** If the gate fails, this cell is REJECTED and the
documented fallback is "probe-scaled appropriate rows + a small (~15%)
contrastive low-confidence tail," to be proposed as a revised amendment.

### 3.3 Config files

The SFT trainer (`synaptic-tuner/Trainers/sft/train_sft.py --config <file>`) consumes
a **Python config module** exporting a `Config()` function (it `exec`s the file and
calls `Config()`), NOT a YAML — unlike the GRPO trainer. The proven contrastive
configs already exist from session 0018 and mirror the clean-SFT recipe exactly
(`completion_only_loss=True`, `assistant_only_loss=False` → lineage reports
`loss_mask_mode: assistant_only`; batch 10; LR 2e-4; LoRA r32/α64; seed 1); only the
dataset and `output_dir` differ from the clean-SFT cell:

- `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_smoke_config.py`
- `experiment/phase1/grpo/configs/sft_schema_contrastive_response_confidence_seed1_full_config.py`

## 4. Launch Sequence And Gates

1. **CPU preflight (data):** confirm the contrastive dataset distribution
   (bimodal appropriate/inappropriate, full range, JSON-valid). GREEN required.
2. **Smoke** (`..._smoke.yaml`, max_steps ~32): exit 0; training_lineage reports
   `loss_mask_mode: assistant_only` and the contrastive dataset; loss decreasing.
3. **Full** (`..._full.yaml`, 1 epoch ≈ 2,934 steps): exit 0; final adapter +
   lineage written.
4. **Merge** the adapter to a 16-bit base (same as the clean-SFT base merge).
5. **Eval** the merged model on SelfAware (mirror the clean-SFT merged eval
   config) and run `calibration_gap_report.py` on its scored_rows.

### 4.1 Calibration gate (the objective — must PASS to call the cell a success)

- emitted AUROC→appropriateness ≥ **0.62** (clean-SFT / v3 ≈ 0.52; aspirational ≥0.70);
- behavior-conditional cell means: known_correct_answered > known_answered_wrong
  AND unknown_refused > unknown_answered_wrong;
- emitted std ≥ **0.10** (clean-SFT 0.047, v3 0.027);
- ECE-vs-appropriateness < **0.30** (clean-SFT/v3 ≈ 0.40–0.44).

### 4.2 Behavior gate (the guard — must PASS or the cell is REJECTED)

Baseline = clean-SFT merged base (SelfAware full): over_refusal 57.51%,
truthful 40.58%, correct_on_known 47.23%, refusal_recall 87.02%.

- truthful_pct ≥ **35.6** (within 5 pts of clean-SFT);
- correct_on_known_pct ≥ **42.2** (within 5 pts);
- over_refusal_pct ≤ **67.5** (within 10 pts, not worse);
- refusal_recall_pct ≥ **82.0** (within 5 pts — keep unknown abstention).

If the behavior gate fails, the cell is REJECTED regardless of calibration; fall
back to §3.2.

## 5. Implementation Boundary

In scope (this amendment): the two SFT config files in §3.3, the merge + eval +
calibration_gap reporting, and session-note checkpoints. Reuses the committed,
unchanged builder and the generic `synaptic-tuner/Trainers/sft/train_sft.py`. No
submodule edits. No change to PROTOCOL v0.3, Amendment E artifacts, the clean-SFT
base, or Amendment J.

## 6. Sign-Off Checklist

- approval date: 2026-06-27
- approved scope: one local seed-1 SFT cell `schema_contrastive_sft_seed1`,
  trained to completion, local 4B lane
- approved dataset: `sft_response_confidence_train_contrastive.jsonl` (committed
  deterministic builder output)
- excluded: any change to PROTOCOL v0.3 headline matrix, Amendment E artifacts,
  the clean-SFT base, or Amendment J
- gates frozen: yes (§4 calibration gate + behavior gate)
- known risk acknowledged: yes (§3.2 wrong-answer supervision; behavior gate is
  the mitigation; documented fallback on gate failure)
- authorization: user, 2026-06-27 — "Proceed"
