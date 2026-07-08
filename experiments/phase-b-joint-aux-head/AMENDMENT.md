---
amendment: R
slug: phase-b-joint-aux-head
question: >-
  Does jointly co-training the aux_head into an unfrozen base change the
  model's OWN emitted calibration/abstention behavior?
predictions:
  orchestrator:
    call: >-
      partial/likely-negative; head stays calibrated, emitted scalar barely moves
  user:
    call: null
    note: >-
      Predates the dual-prediction practice (adopted 2026-07-03 at AH
      signing); no separately recorded user prediction.
outcome: >-
  FALSIFIED — A1-A2 +0.043 below the +0.05 bar and A1 below A0;
  co-training shifts the action policy, not the emitted channel.
scoreboard: null
---

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

A focused builder handoff (parallel to docs/sessions/20260629T000000Z-aux-scalar-head-build-handoff.md, Phase A) will spec these
with acceptance tests. Phase B does not run until this lands + smokes green.

**Status (2026-06-29):** items 1–4 LANDED in PR #119 (submodule `e95dbde`, 62
aux_head tests green). Two prerequisites remain before the scored A0/A1/A2 run, both
generic engine/runner work (NOT epistemic-humility specifics):

6. **`prompt_render="prompt_completion"` mode** (`train_sft.py` preprocessing;
   builder spec `docs/sessions/20260629T000000Z-phase-b-token-faithfulness-fix-handoff.md`). The default full-conversation render diverges
   from `add_generation_prompt=True` at the `</think>` newlines, so item 3's
   `end_of_prompt` lands one token short of the validated gen-prompt axis (smoke:
   cos 0.54 / AUROC 0.85 vs the 0.96 axis). The verified fix renders rows
   prompt/completion-style so the *existing* `end_of_prompt` helper lands on the
   faithful token (400/400 rows, cos 0.9998). Default unchanged ⇒ backward-compatible.
7. **Runner forwarding of the `aux_head` block.** `train_sft.py` reads `aux_head`
   from its config file only — there is **no argparse** for it — and the tuner's
   `local_run_handler._build_trainer_command` forwards recipe keys as `--flags` but
   does **not** forward any `aux_head` block (verified: `aux_head` appears nowhere in
   `tuner/`). So a recipe's `aux_head:` is **inert on the standard local-run lane**
   until aux_head argparse is added to `train_sft.py` and forwarded in
   `_build_trainer_command` (alongside the existing `--chat-template-kwargs` / lora
   forwarding). This belongs in the submodule's **own** `fine-tuning` skill + the
   builder PR — it is generic engine knowledge, not installed from the root project.

Root-side prep for the run is DONE and staged (lab-notebook): the aux-dataset builder
(`amendment_r_build_phase_b_aux_dataset.py`, real + seeded-shuffled placebo, gitignored
scratch), the A0/A1/A2 recipes (`eh_phase1_qwen3_4b_amendment_r_*.yaml`), and the
run records (`aux_a{0,1,2}__4b__amendment_r__seed1.json`, A0 launchable today, A1/A2
`blocked_on` items 6+7). The reusable runbook is
`experiment-runner/reference/aux-head-cotraining-arms.md`.

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
  **Faithfulness sub-gate RESOLVED (2026-06-29): the fix is verified — prompt/completion
  tokenization restores cos 0.9998 / AUROC 0.938 (see §7). Pending: the engine
  preprocessing render-mode build (handoff `docs/sessions/20260629T000000Z-phase-b-token-faithfulness-fix-handoff.md`), then the
  joint-loss-runs + baseline parts of the smoke.**
- [x] Primary-metric instrument identified + A0-analog baseline anchored (R1.1).
- [x] Final effect-size falsifier threshold locked (+0.05, 2026-06-29 after the
  faithful-token gate went GREEN; not moved at scoring).
- [x] User sign-off recorded + training launch authorized; scored run complete
  2026-06-30 (see §7 — FALSIFIED).

## 7. Result

### Verdict (2026-06-30): FALSIFIED

Scored run complete. All three arms trained (1800 steps, seed 1, identical LM data),
merged to 16-bit, evaluated on full SelfAware response-confidence (n=3369/arm), and
scored via `calibration_gap_report.py` Analysis A. Verdict by the locked falsifier
(`amendment_r_falsifier_check.py`; margin +0.05 unchanged):

| Arm | `auroc_emitted_to_appropriateness` | refusals | answered-known-wrong | combined train_loss |
|---|---|---|---|---|
| A0 (reference, head off) | **0.513** | 2256 | 544 | 0.505 (pure LM) |
| A1 (treatment, real targets) | **0.466** | 1912 | 795 | 4.557 (LM+aux) |
| A2 (placebo, shuffled) | **0.422** | 1394 | 1120 | 5.530 (LM+aux) |

- **PRIMARY gate A1 − A2 ≥ +0.05: FAIL** (got **+0.043**; real-target arm beats placebo
  only directionally, below the pre-locked bar).
- **SECONDARY A1 > A0: FAIL** (A1 is **−0.047 below** the head-off reference).

**Interpretation.** The emitted stated-confidence is a near-deterministic function of the
answer/abstain ACTION in every arm (conf|answered ≈ 0.88–0.95, conf|refused ≈ 0.00), not
an appropriateness estimate; the model answers many known-wrong questions at ~0.9
confidence, so emitted confidence does not rank appropriateness (AUROC ≈ chance). The
aux head DID fit its target internally (A1 combined loss 4.557 < A2 5.530, real beats
placebo), but that internal readout did not propagate to the emitted channel. What the
co-training changed was the action policy: it reduced abstention (refusals A0 2256 > A1
1912 > A2 1394) and raised confident-wrong answers, which lowered appropriateness-AUROC
below the head-off reference. The placebo perturbed the policy most, so the shift tracks
the act of attaching+optimizing a head, not the target information.

This is a clean negative consistent with the project's internal-vs-emitted three-channel
dissociation (the internal axis reads at AUROC ~0.997 but the emitted scalar collapses
onto the action): jointly co-training an auxiliary readout on an unfrozen base does not
open the internal→emitted channel. Non-locked footnote (not the gate): on
`auroc_emitted_correct_vs_wrong | answered_known` the order flips and all are >chance
(A0 0.581 < A1 0.607 < A2 0.651) — among answers it gives, emitted confidence ranks
correct-vs-wrong somewhat, and slightly more so with the head — but that does not rescue
the appropriateness falsifier.

Artifacts: `experiment/phase1/eval/analysis/{calibration_gap_amendment_r_a0,a1,a2,
amendment_r_falsifier_verdict}.json`; per-arm `scored_result` blocks in the three
`run_records/aux_a{0,1,2}__4b__amendment_r__seed1.json`. Not promoted (it is a negative);
no replication registered.

### Pre-flight smoke finding (2026-06-29, lab-notebook — NOT verdict-bearing)

Engine landed (PR #119, submodule `e95dbde`, 62 aux_head tests green). The pre-flight
faithfulness smoke (`experiment/phase1/probe/amendment_r_phase_b_{smoke,offset_diag}.py`)
routes real KUQ rows through the exact trainer preprocessing and reads L35 via the
engine reduce path. It caught a **token-position confound before any scored run**
(falsifier untouched — faithfulness clause):

| position | CV AUROC | cos→cached |
|---|---|---|
| cached faithful axis | 0.964 | — |
| gen-prompt token (Q's, `add_generation_prompt=True`) | 0.938 | **0.9998** |
| engine `end_of_prompt + 0` | 0.850 | **0.544** |
| `end_of_prompt + {1,2,3}` | 0.948 / 0.867 / 0.929 | 0.910 / 0.628 / 0.936 |

**The engine's `end_of_prompt` does NOT reproduce the validated answerability axis**
(cos 0.55 — the weak-token signature). Root cause: the full-sequence assistant-turn
render emits `</think>\n{content}` (one newline) while `add_generation_prompt=True`
emits `</think>\n\n`; the labels-derived boundary lands one token short of the
validated gen-prompt position, and no integer offset into the completion reproduces it
(best +1 = cos 0.91, still under the 0.95 bar). `aux_target` threading verified OK.

**Blocker + fix paths (user/builder decision):** scored A0/A1/A2 is blocked until the
SFT prompt segment ends exactly at the gen-prompt token. (1) **Rendering alignment**
(preferred, generic engine fix): align the `</think>\n\n` scaffold + mask so
`end_of_prompt` == gen-prompt token. (2) **Separate gen-prompt forward** for the head
input (messier for joint training). See [[amendment-r-phase-b-token-faithfulness-gap]].

**FIX VERIFIED (2026-06-29, prototype `amendment_r_phase_b_promptcompletion_proto.py`).**
Path (1) confirmed. Tokenizing rows **prompt/completion-style** — prompt =
`render(system+user, add_generation_prompt=True)`, then `++ completion ++ <|im_end|>`,
with `labels = [-100]*len(prompt) ++ completion` — makes the engine's *existing*
`prompt_end_indices`/`reduce_hidden_states(token_position="end_of_prompt")` land on the
gen-prompt token for **400/400** rows: **CV AUROC 0.9380 (cached 0.9389), cos 0.9998,
mse 0.04.** No change to the engine's token-position code; the fix is a preprocessing
**render mode** (the current full-conversation render diverges from
`add_generation_prompt=True` at the `</think>` newlines, so the faithful token has no
clean in-row position). Builder spec: `docs/sessions/20260629T000000Z-phase-b-token-faithfulness-fix-handoff.md`. The real run uses the real
abstention completion (known→answer, unknown→IDK); the fixed completion here only
isolates the read position (which is before the completion).
