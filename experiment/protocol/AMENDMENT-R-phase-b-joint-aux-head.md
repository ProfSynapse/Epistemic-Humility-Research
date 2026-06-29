# Amendment R — Phase B: Joint Co-Training of the aux_head (Native Behavior Change)

**Status:** DRAFT (NOT signed). Pre-registration scope locked on the primary
framing (user 2026-06-29: "native behavior change (B1)"); gates/falsifier finalize
on sign-off, which is gated on the engine build + a green smoke. Tier-2 exploratory
cell (new TRAINING evidence, falsifier pre-stated; reported separately from the
locked PROTOCOL v0.3 matrix). No goalpost-moving after sign-off.
**Instrument rationale:** Tier-2 per
`experiment-runner/reference/amendment-vs-lab-notebook.md` — a new training-evidence
cell with a real falsifier. Successor to [[amendment-q-aux-head-trainable-readout]]:
O/P/Q proved the answerability signal is latent and *readable* by a bolted-on head;
R asks whether co-training that head *into* the base changes the model's OWN behavior.
**Compute:** Local GPU training — joint multi-task SFT (`freeze_base=false`,
`lm_loss_weight>0`), 4B, single-seed first. A few short LoRA runs. Launch requires
explicit user approval (NOT yet given; this is a draft).
**Model/surface:** Qwen3-4B clean-SFT lineage (seed 1). Single-model, single-seed,
exploratory.
**Engine:** `synaptic-tuner` `aux_head` — requires the Phase-B engine build below
(the joint-loss path is currently STUBBED; see §2). Generic, reusable.

## Revision history
- **R1 (2026-06-29, DRAFT):** scope + primary framing locked (B1 native behavior
  change). Engine prerequisites enumerated. Gates pending engine build + smoke;
  signature pending.
- **R1.1 (2026-06-29, DRAFT):** §4 made concrete pre-smoke — named the existing
  scorer (`calibration_gap_report.py` Analysis A) as the primary-metric instrument,
  anchored the A0-analog baseline from the committed `clean_sft_grpo_v2_seed1`
  report (emitted→appropriateness AUROC 0.561, flat scalar std 0.0129), and recorded
  a candidate falsifier effect size (≥ +0.05 AUROC, A1>A2). Threshold still locks
  post-smoke; no goalpost moved (made stricter/more concrete, never loosened).

## 1. Facts this builds on

1. The three-channel dissociation: internal axis calibrated (probe 0.997); the
   stated-confidence scalar collapses ([[amendment-m-r3-factual-axis-retarget]]
   correctness-AUROC 0.504, base 0.559); RL can't install knowledge-conditioned
   action ([[amendment-n-beta005-structural-decoupling]]).
2. The signal is latent and READABLE: [[amendment-o-probe-as-oracle-ceiling]] (+95
   oracle policy), [[amendment-p-xdataset-transfer]] (transfers cold 0.983),
   [[amendment-q-aux-head-trainable-readout]] (a TRAINED head reproduces it, 0.983).
3. Open after Q: every result so far is a *readout* bolted onto a frozen base — none
   changes the model's behavior. The deployment payoff is untested: does the
   auxiliary objective, backpropagating into the shared base during real SFT,
   install the calibrated behavior M/N could not?

## 2. Engine prerequisites (generic synaptic-tuner build — MUST land before any run)

The joint-loss path is currently stubbed (`aux_head_trainer.py:186`:
`# Phase B seam (do NOT enable here): loss = outputs.loss + cfg.lm_loss_weight * head_loss`).
Four reusable features, plus a gotcha:

1. **Joint loss.** Implement the seam: `loss = outputs.loss + lm_loss_weight *
   head_loss` (wire `outputs.loss` from the LM `labels`; currently head-loss is the
   entire loss). `aux_head_trainer.py:154-188`.
2. **`freeze_base=false` path.** Optimizer must include base/LoRA params, not just
   the head; skip `_freeze_base_keep_head()` when false. `aux_head_trainer.py:76-77,
   106-150`.
3. **End-of-prompt token position** (Q finding #1). Read answerability *before* the
   answer on prompt+completion rows. The prompt/completion boundary is recoverable
   from `labels` (-100 mask): end-of-prompt index = `(labels != -100).float().argmax(1)
   - 1` per row, computed in `compute_loss` and passed to a `reduce_hidden_states`
   variant. Add `token_position="end_of_prompt"`. `aux_head.py:137-181`.
4. **Input normalization** (Q finding #2). Add an optional `nn.LayerNorm(input_dim)`
   before the linear in `AuxHead` (trainable, portable — no fitted scaler to ship),
   so the head trains at a sane LR (raw saturates; Q used lr=1e-5 / standardization).
   `aux_head.py:66-98`.
5. **Gotcha to verify:** `output_hidden_states=True` + gradient checkpointing + LoRA
   co-training can break gradient flow — the build must assert gradients reach both
   the head and the LoRA params.

A focused builder handoff (parallel to docs/sessions/0027, Phase A) will spec these
with acceptance tests. Phase B does not run until this lands + smokes green.

## 3. Method (joint training; one treatment + two controls)

4B, single-seed, local. Same abstention SFT data the clean-SFT arm used (known→answer
rows, unknown→IDK rows; the known/unknown split IS the `target_field`). **Confirmed
(R1.1):** the KUQ extraction rows carry `label ∈ {known: 600, unknown: 400}` — a
binary answerability column ready to map to a 0/1 `aux_head.target_field`; A2 shuffles
this column. aux_head reads `end_of_prompt`, L35, BCE, LayerNorm input.

- **A0 — LM-only SFT baseline** (aux_head off): the model's native abstention behavior
  + a post-hoc (frozen-base, Q-style) head readout for reference.
- **A1 — joint** (`freeze_base=false`, `lm_loss_weight=1`, real answerability targets,
  λ = head-loss weight): the treatment.
- **A2 — joint placebo** (identical to A1 but answerability targets SHUFFLED): isolates
  whether the answerability *signal* drives any change vs merely adding a regularizing
  loss term. A positive A1 is only believable if A1 > A2.

## 4. Gates and falsifier (PRIMARY = native behavior change; finalize on sign-off)

**PRIMARY (locked framing — B1 native behavior change):** joint co-training with the
real answerability signal (A1) must improve the MODEL'S OWN calibration/abstention
over BOTH the LM-only baseline (A0) and the placebo (A2). Operationalized on
NON-CIRCULAR metrics (avoiding O caveat 2): the model's **emitted** stated-confidence
correctness/appropriateness-AUROC, and native answer/abstain behavior margin —
measured from the model's own generations, NOT the head's readout.
- **Falsifier:** A1's emitted-scalar calibration (and native margin) does NOT exceed
  A2 (placebo) by a pre-set effect size → the auxiliary answerability objective buys
  no behavioral change; the bottleneck is the expression channel, not the
  representation. (Exact effect-size threshold locked on sign-off, after the smoke
  fixes baseline variance.)

**Primary-metric instrument & A0-analog baseline (pre-smoke anchor, not yet locked).**
The non-circular primary is already computed by the existing GPU-free scorer
`experiment/phase1/eval/analysis/calibration_gap_report.py` (Analysis A), so A0/A1/A2
are scored with the same instrument as every prior arm — no new measurement code. The
two locked metric fields it emits, on the SelfAware **behavior subset** (n=1233):
- `auroc_emitted_to_appropriateness` — emitted stated-confidence as a forecast of
  response appropriateness. Its docstring establishes this read is non-circular (the
  axis is a known/unknown contrast over two *appropriate* cells, not trained to
  separate appropriate from inappropriate), which is exactly the property §4 needs to
  avoid O's circularity caveat.
- `auroc_emitted_correct_vs_wrong_answered_known` + `ece_vs_appropriateness` (secondary
  reads on the same generations).

**A0 analog = the `clean_sft_grpo_v2_seed1` calibration-gap report already committed**
(`experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json`): on
the behavior subset, `auroc_emitted_to_appropriateness = 0.561`,
`auroc_emitted_correct_vs_wrong = 0.532`, emitted std `0.0129` (a flat, chance-level
scalar). Arm-to-arm spread on the same field: the abstention/GRPO arms sit ~0.52–0.56
(grpo-v3 emitted std 0.027); only the contrastive-SFT arms ever moved the scalar
(Amendment K emitted std 0.309; L 0.180) — i.e. a real shift in this metric is large
and visible, not a fraction of a point.

**Candidate effect size (to confirm or revise post-smoke, NOT yet locked):** A1's
behavior-subset `auroc_emitted_to_appropriateness` exceeds A2's by **≥ +0.05** AND
clears the ~0.56 flat-scalar floor. The smoke fixes A0/A2 run-to-run variance under the
actual Phase B harness; the final threshold is set to max(this candidate,
2×observed-baseline-SD) at sign-off. Recording the candidate now prevents a
hindsight-fit threshold — it can be made stricter or its variance basis corrected, but
not loosened to manufacture a pass.

**SECONDARY (de-risk gate, descriptive):** head answerability-AUROC after A1 ≥ 0.90 —
the head stays calibrated as the base moves (the deployed-artifact preservation
number; rides along, not the primary claim).

**Pre-stated prediction (recorded to avoid hindsight):** PARTIAL / likely-negative —
the head stays calibrated (secondary passes) but native emitted-scalar calibration
barely moves over placebo, because the prior evidence locates the bottleneck at the
single-token expression channel, not the latent representation. A clean negative would
sharpen the thesis to "it's the channel, not the data or the signal." A positive A1 >
A2 on emitted calibration would be the program's headline win.

**Ambiguity rule:** report the A1/A0/A2 numbers with the explicit effect size; do not
retune λ, layer, token position, or LR after the result to manufacture a verdict.

## 5. Reporting and promotion

Exploratory, single-model/single-seed; reported separately from the locked matrix into
Paper 3 §8/§9 as the readout→behavior step. A positive result is a LEAD; promotion to
a claim requires replication (fresh seeds / 8B / held-out reporting surface) registered
before running. Carries O/P/Q caveats: answerability not per-attempt correctness; the
correctness gap (O's 0.64) and generic-train-distribution transfer remain separate.

## 6. Sign-off checklist
- [x] Primary framing locked (B1 native behavior change; user 2026-06-29).
- [x] Engine build (§2) landed in synaptic-tuner + unit tests green (PR #119,
  squash `e95dbde` on submodule main; all 5 items + §2.5 grad-flow test; local
  `pytest` 62 passed 2026-06-29). Root submodule-pointer bump to `e95dbde` pending.
- [ ] Pre-flight smoke green (joint loss runs; gradients reach head + LoRA;
  end_of_prompt token reproduces the Q axis; head calibration baseline measured).
- [x] Primary-metric instrument identified + A0-analog baseline anchored (R1.1).
- [ ] Final effect-size falsifier threshold locked (post-smoke; candidate ≥ +0.05).
- [ ] User sign-off recorded + training launch authorized.

## 7. Result

_(pending engine build, smoke, sign-off, and run)_
