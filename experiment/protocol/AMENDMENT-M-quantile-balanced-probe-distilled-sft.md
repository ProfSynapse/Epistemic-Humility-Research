# Protocol Amendment M: Quantile-Balanced Probe-Distilled Stated Confidence (SFT)

**Status:** Revision 1 SIGNED — user-authorized 2026-06-27 ("Yes approve"), with
recommended defaults: global quantile, band [0.10, 0.90], SFT-only clean completions
first. **Revision 2 — SIGNED, user-authorized 2026-06-29 ("1" → sign R2 as-is).**
Revision 1 was parked
as Amendment N's fallback; N has now completed and its result (the structural
action/knowledge decoupling) materially extends this cell. Revision 2 revives M as
the primary calibration route and adds an action-conditioning endpoint and a
pre-registered threshold-policy follow-on. **The Revision-1 §4.1/§4.2 gates are
unchanged and remain in force; Revision 2 only ADDS endpoints — but because it adds
a pre-registered measurement and a follow-on with its own decision rule, it requires
a fresh signature before running.**

**Revision history:**
- **R1 (2026-06-27, signed):** quantile-balanced probe-distilled `response_confidence`
  SFT on clean-SFT completions; calibration gate (with discrimination) + behavior
  gate; channel/loss falsifier.
- **R2 (2026-06-29, pending re-sign):** integrates Amendment N's finding that stated
  calibration and knowledge-conditioned *action* are separable and that the action
  decoupling is structural under RL (β re-run falsifier fired). Adds: (a) §1 fact 4 +
  the RETAIN-behavior/REPAIR-calibration mirror framing; (b) §2 relationship to N;
  (c) §3.4 the action-conditioning question and why M's scalar-only loss leaves it
  untouched by design; (d) §4 the action-margin SECONDARY endpoint + an inference-time
  threshold-policy sweep (no retraining); (e) §4.3 a "says-but-doesn't-act" branch
  that is EXPECTED, not a failure, and triggers the threshold follow-on. No change to
  the R1 gates, the builder target spec, the recipe, or the data scope.

**Short name:** Amendment M / probe-distilled calibration SFT

**Scope:** Authorize one new local SFT cell, `schema_probe_distilled_sft_seed1`
(seed 1, local 4B lane): clean-SFT behavior completions whose `response_confidence`
target is the model's own internal doubt-axis estimate (`appropriateness_p`), passed
through a **monotone quantile transform** so the target is simultaneously
*per-question grounded* (it tracks internal appropriateness) and
*distribution-balanced* (its marginal is spread, not mode-heavy). The objective is
to install stated-confidence **discrimination** by distilling the calibrated
internal axis into the verbalized channel — the cell neither Amendment K nor L could
be. It does NOT modify PROTOCOL v0.3, Amendment E (clean-SFT), Amendment J
(GRPO v3), or the K/L artifacts. Reported separately as an alternative base.

---

## 1. Rationale

The calibration-gap thread (Paper 3, `experiment/paper/paper3-knows-but-doesnt-say-draft-v0.md`)
established three facts that jointly motivate this amendment:

1. **The model has the signal internally.** A 1-D doubt-axis readout is calibrated
   to ECE ≈ 0.004 and separates known/unknown at AUROC ≈ 0.997, surviving all
   training [calibration: docs/sessions/0026 cp004; probe: _latent_knowledge_controls/].
2. **The stated channel does not report it, and outcome/preference training does not
   fix it.** DPO, KTO, GRPO v1/v2/v3 all leave emitted confidence collapsed
   (v3: std 0.027, AUROC→appropriateness 0.522) even though the v3 proper-score
   target was verified to have per-prompt dynamic range
   [calibration_gap_clean_sft_grpo_v3_seed1.json; computed-confidence-alignment-regimen.md].
3. **Contrastive SFT can install stated calibration only by supervising the wrong
   answer (K), which breaks behavior; masking the answer (L) recovers behavior but
   destroys calibration** — a clean dissociation
   [calibration_gap_contrastive_sft_seed1.json; calibration_gap_contrastive_masked_sft_seed1.json].
4. **(R2) RL on the calibrated base retains calibration but cannot repair behavior,
   and the answer/abstain ACTION is decoupled from knowledge — structurally.**
   Amendment N (GRPO v3 on the K base) RETAINED K's stated calibration (4/4) but
   FAILED behavior repair (2/4): greedy decode stayed pinned to K's over-refusing
   argmax. The deeper finding is that the action margin
   `P(answer|known) − P(answer|unknown)` is only ≈ +3 pts (it would need ≈ +14.5 to
   clear the behavior gate), and the pre-registered β 0.05 re-run — which demonstrably
   loosened the KL anchor (train KL ≈0.97 → ≈1.91) — moved that margin by +0.17 pts.
   The falsifier fired: the action/knowledge decoupling is **structural**, not a KL
   artifact. So "knows but doesn't say" has a sibling: "says but doesn't act"
   [AMENDMENT-N §7/§7.1; paper3 §7].

The untried route is to supervise the stated channel **toward the calibrated
internal estimate directly**. One naive form of this was already run and failed:
probe-scaled SFT with `response_confidence = 0.1 + 0.8·appropriateness_p` collapsed
to a single emitted value (0.8765) because the *target distribution* is imbalanced —
most knowns are answerable, so ~82% of targets land in one high band, and
cross-entropy is minimized by emitting that mode regardless of the input
[computed-confidence-alignment-regimen.md §004]. The audited diagnosis names the
exact fix: a target that is **per-question grounded AND distribution-balanced**
(quantile-map the probe estimate onto a spread band), so emitting any constant is
penalized and the model must use the question to predict the target — which is what
installs discrimination.

**Hypothesis.** A monotone quantile transform of `appropriateness_p` onto a spread
band, used as the SFT `response_confidence` target on clean-SFT behavior rows,
yields emitted confidence that is both spread (std ≥ 0.10) and **discriminating**
(AUROC → appropriateness ≥ 0.62), while preserving clean-SFT behavior (because the
answer/abstention completions are unchanged from clean SFT). Because the transform
is monotone, it preserves the per-question ordering of the calibrated internal
estimate (so the discrimination of the target is retained); because it equalizes the
marginal, it removes the §004 mode-collapse.

**(R2) The mirror of Amendment N.** N was **RETAIN calibration / REPAIR behavior** and
failed the repair (the resistant target was *behavior*, induced sideways from a
sub-dominant reward term against a KL anchor). M is the exact mirror — **RETAIN
behavior / REPAIR calibration** — and the bet is the mirror succeeds, because the
resistant channel (the stated scalar) is finally given a *direct, dense, per-item,
monotone-calibrated* target (the internal axis), instead of being induced from
outcomes (DPO/KTO/GRPO) or entangled with answer text (K). Behavior is held by
construction: the loss touches only the `response_confidence` token; the
answer/abstention completions are clean-SFT-identical (§3.1).

## 2. Relationship To Existing Protocols

- PROTOCOL v0.3 — locked plain-answer headline matrix. Untouched.
- Amendment E — clean-SFT base/cell. Untouched; this cell reuses its behavior
  completions and differs ONLY in the `response_confidence` target.
- Amendment J — GRPO v3. Untouched; this is an SFT-side cell, complementary to the
  reward-side fix that did not close the gap.
- **(R2) Amendment N — GRPO v3 on the K base.** Completed; PARTIAL (calibration
  retained, behavior not repaired) and the action decoupling shown structural by the
  pre-registered β 0.05 re-run. N's R1 note listed M as "on hold / fallback if N's
  falsifier triggers." N's result is the trigger: M is now the **revived primary
  route** to coherent calibration+behavior. M does not consume any N artifact; it is
  an SFT-side cell from the clean-SFT completions. N taught M two things, folded into
  R2: stated calibration ≠ knowledge-conditioned action (measure both, §4), and the
  action is best made a *readout* of the calibrated scalar rather than a separately
  trained policy (the threshold follow-on, §4).
- Amendments K / L — the contrastive cells and their dispositions stay on record.
  This cell is reported separately; do not pool with the clean-SFT base or the v0.3
  headline matrix.
- Supersedes (in practice) the naive probe-scaled SFT (`A1`, §004 of
  computed-confidence-alignment-regimen.md): same intent, distribution-balanced
  target that defeats the documented collapse.

## 3. Design Change

### 3.1 Builder change (epistemic) — quantile-balanced probe target

`build_schema_response_confidence_datasets.py` gains a new target formula,
`PROBE_DISTILLED_QUANTILE_FORMULA`, and a new output dataset
`sft_probe_distilled` built on the SAME behavior completions as the clean-SFT cell
(`SFT_CLEAN_FORMULA` rows: gold-correct answers and gold abstentions; NO
wrong-answer rows), replacing only the `response_confidence` value:

1. For each row, compute `appropriateness_p` exactly as the existing probe-scaled
   path does (answer rows: `factual_p`; abstention rows: `1 − factual_p`), from the
   `--probe-results` Laplace-smoothed 32-sample probe outputs (deterministic,
   GPU-free given probe JSONL).
2. Compute the **empirical quantile** of each row's `appropriateness_p` within the
   full training set: `q_i = rank(appropriateness_p_i) / (N + 1)` (average-rank for
   ties; deterministic given a fixed sort key).
3. Map to a spread target band: `response_confidence_i = lo + (hi − lo)·q_i`, with
   band `[lo, hi] = [0.10, 0.90]` (matches the contrastive/clean usable range;
   endpoints avoided to keep JSON/logit targets non-degenerate).
4. Quantize to the dataset's confidence precision (existing rounding) and emit.

Properties to assert in tests:
- **Monotone:** `appropriateness_p_i < appropriateness_p_j ⇒ confidence_i ≤
  confidence_j` (preserves internal ordering → preserves discrimination of the
  target).
- **Balanced:** the emitted target marginal is approximately uniform across the band
  — no single quantized value exceeds a cap (e.g. ≤ 15% of rows), directly
  preventing the §004 mode (which was 81.79%).
- **Behavior-identical to clean SFT:** the `messages` (answer/abstention text) are
  byte-identical to the clean-SFT dataset; only `response_confidence` differs.
- Manifest records the formula, band, quantile method, tie handling, and the
  resulting target histogram.

DESIGN DECISION (for sign-off): quantile computed **globally** (over all rows) so the
target still orders appropriate above inappropriate AND grades within each. A
per-stratum (per-role) quantile is the alternative; global is recommended because it
preserves the cross-role ordering the calibration gate's cell-means check rewards.

### 3.2 Training cell

- Cell name: `schema_probe_distilled_sft_seed1`. Seed 1, local 4B lane.
- Base model: `unsloth/Qwen3-4B-bnb-4bit` (same as clean-SFT / K / L).
- Recipe mirrors clean-SFT EXACTLY (LoRA r32/α64/dropout 0.05 all-linear; batch 10;
  LR 2e-4; 1 epoch; warmup 0.03; linear; adamw_8bit; bf16; seed 1;
  `completion_only_loss: true`). The ONLY difference from the clean-SFT cell is the
  `response_confidence` target column (quantile-balanced probe-distilled vs clean
  role-band). No sub-span masking is needed (no wrong-answer rows).
- Configs (YAML):
  - `experiment/phase1/grpo/configs/sft_schema_probe_distilled_response_confidence_seed1_smoke.yaml`
  - `experiment/phase1/grpo/configs/sft_schema_probe_distilled_response_confidence_seed1_full.yaml`

### 3.3 Why this is expected to beat the prior attempts

- vs naive probe-scaled (§004): same per-question grounding, but the quantile
  transform balances the marginal → emitting the mode is no longer loss-optimal.
- vs K: the discrimination signal lives in the *target value*, not in supervising
  the wrong-answer text → no behavior trade (completions are clean-SFT).
- vs L: L removed answer supervision and lost the calibration carrier; here the
  carrier is the per-question target itself, which is present on every (clean) row.
- vs GRPO v3: a dense, per-item, monotone-calibrated SFT target instead of a
  proper-score term that must stay sub-dominant to the behavior reward.

### 3.4 (R2) What M fixes, what it does not, and the threshold bridge

M supervises only the `response_confidence` scalar. It therefore targets the "says"
channel — the verbalized number — and **by construction does not change the native
answer/abstain action**, which is whatever the clean-SFT base does. Amendment N
proved these are separable (fact 4, §1): a model can emit calibrated confidence and
still take a knowledge-blind action. So M must NOT be read as automatically fixing
the action, and §4 measures the action margin as a distinct endpoint rather than
assuming it.

The bridge is a consequence of M's own success, and needs **no retraining**: if M's
emitted scalar is calibrated to appropriateness (the §4.1 gate), then an
inference-time decision rule — *surface the answer iff `response_confidence ≥ τ`,
otherwise abstain* — converts the calibrated scalar into knowledge-conditioned
action by construction (thresholding a calibrated appropriateness estimate is exactly
a knowledge-conditioned decision). This is the coherence that N's RL route could not
reach structurally: there the action was an independently-learned global propensity;
here it is a readout of the calibrated confidence. R2 pre-registers this threshold
sweep (§4, step 7) as a SECONDARY analysis on M's eval outputs — it is cheap, it does
not alter the M cell, and it is the natural test of whether installing calibration
*also* buys coherent action.

A note on the operating point. To make the threshold the *sole* action lever (so the
sweep cleanly isolates "calibration → action"), the threshold-policy eval re-prompts
the model to attempt an answer on every item and emit its calibrated confidence; the
abstain/answer decision is then the `τ` rule applied post-hoc, not the model's native
abstention. The native-abstention eval (the §4.1/§4.2 gates) is unchanged and remains
the primary surface.

## 4. Launch Sequence And Gates

1. **Builder unit tests (CPU):** monotonicity, balance (no value > 15% of rows),
   behavior-identity to clean SFT, manifest histogram. GREEN required.
2. **CPU preflight (data):** confirm the emitted target marginal is spread (report
   the histogram + max-bin share) and that ordering vs `appropriateness_p` is
   preserved (Spearman ≈ 1.0). GREEN required.
3. **Smoke** (`..._smoke.yaml`, max_steps ~32): exit 0; lineage records the
   probe-distilled dataset; loss decreasing.
4. **Full** (`..._full.yaml`, 1 epoch): exit 0; adapter + lineage. (OOM contingency:
   resume from latest checkpoint with `--run-timestamp` pin, as for K/L.)
5. **Merge** the adapter to 16-bit (same as clean-SFT / K / L).
6. **Eval** on SelfAware (mirror the K/L eval config) + `calibration_gap_report.py`.
7. **(R2) Action endpoint + threshold sweep (secondary, no retraining).** On the
   native eval scored rows, run `action_conditioning_report.py` to record the action
   margin `P(answer|known) − P(answer|unknown)` and the confidence/action AUROCs —
   the same instrument used for N, so M and N are comparable. Then run the
   threshold-policy eval (force-answer prompt + calibrated confidence) and sweep `τ`,
   reporting, per `τ`, the induced behavior gate (truthful / over_refusal /
   correct_on_known / refusal_recall) and the induced action margin. Report the
   τ-frontier; pick the operating point on a held-out split, never on the test set.

### 4.1 Calibration gate (the objective — must PASS, with discrimination)

- emitted AUROC → appropriateness ≥ **0.62** (this is discrimination, the thing L
  failed at despite having spread);
- emitted std ≥ **0.10** (spread; expected, by construction);
- ECE → appropriateness < **0.30**;
- behavior-conditional cell means ordered correctly: known_correct_answered >
  known_answered_wrong AND unknown_refused > unknown_answered_wrong (L inverted the
  second; this must hold).

### 4.2 Behavior gate (must PASS — preserve clean-SFT behavior)

Same bar as Amendment L (baseline = clean-SFT merged base):
- truthful_pct ≥ **35.6**; correct_on_known_pct ≥ **42.2**;
  over_refusal_pct ≤ **67.5**; refusal_recall_pct ≥ **82.0**.

Because the completions are clean-SFT-identical, behavior is expected to pass
comfortably; the risk is entirely on the calibration side.

### 4.3 Success condition and falsifier

- **SUCCESS:** both gates PASS → the first cell in the thread to achieve coherent
  stated-confidence calibration AND behavior. Then (optional, separate amendment)
  re-probe to confirm emitted confidence now tracks the internal doubt projection
  (internal→stated coherence), and consider a GRPO-v3 arm on top.
- **FALSIFIER:** if calibration still fails (AUROC < 0.62) despite a balanced,
  discriminating target, the conclusion is that SFT cross-entropy on a single
  confidence token cannot install discrimination even from a clean target — i.e. the
  bottleneck is the *channel/loss*, not the target distribution — which would
  redirect the program toward a dedicated confidence head / regression loss (an
  engine change) rather than another dataset.
- **(R2) "Says but doesn't act" branch — EXPECTED, not a failure.** The native
  action margin (§4 step 7) staying flat (≈ N's +3 pts) while the §4.1 calibration
  gate PASSES is the *predicted* outcome, given N: M fixes the scalar, not the native
  action. This is not a falsifier — it is the trigger for the pre-registered
  threshold-policy bridge (§3.4). Pre-registered prediction for the bridge: with M's
  calibrated scalar, a τ-thresholded action recovers a margin ≥ ~14.5 pts AND a
  behavior operating point on or above the §4.2 gate at some τ. If the τ-frontier
  CANNOT reach both at once — i.e. calibration is genuine yet thresholding it still
  fails to produce knowledge-conditioned action above the behavior gate — then the
  decoupling is deeper than the verbalized scalar (the internal axis itself does not
  support a clean operating point on this eval), which redirects to revisiting the
  probe/operating definition rather than to more SFT or RL. The calibration result
  (§4.1) stands on its own regardless of the bridge outcome.

## 5. Implementation Boundary

In scope: the builder quantile-balanced target + its tests + the new dataset; the
two SFT YAML configs; one eval config; merge + eval + calibration_gap reporting;
session-note checkpoints. **(R2)** also in scope: reusing the existing
`action_conditioning_report.py` on M's scored rows, and a threshold-policy eval
(force-answer prompt variant of the eval config) + a stdlib τ-sweep analysis script
— all reporting-only, no retraining, no new training cell. No change to PROTOCOL
v0.3, Amendment E artifacts, the clean-SFT base, Amendment J, the K/L artifacts, or
the Amendment N artifacts. No `synaptic-tuner` engine change is required for the
recommended (clean-completions) cell or the R2 endpoints.

## 6. Sign-Off Checklist

- approval date: 2026-06-27
- approved scope: one local seed-1 SFT cell `schema_probe_distilled_sft_seed1`,
  trained to completion, local 4B lane; one builder target formula + tests + dataset
- approved dataset: `sft_probe_distilled` (deterministic builder output; quantile-
  balanced probe-distilled `response_confidence`; behavior completions identical to
  clean SFT)
- excluded: any change to PROTOCOL v0.3 headline matrix, Amendment E artifacts, the
  clean-SFT base, Amendment J, or the K/L artifacts
- gates frozen: yes (§4.1 calibration gate WITH discrimination + §4.2 behavior gate)
- open decision for sign-off: global vs per-stratum quantile (recommended: global);
  target band [0.10, 0.90] (recommended); SFT-only first vs add masked-answer
  inappropriate rows (recommended: SFT-only clean completions first — cleanest test
  of the target-distribution hypothesis)
- risk acknowledged: yes (falsifier = channel/loss bottleneck → would motivate a
  confidence-head engine change under a further amendment)
- authorization: user, 2026-06-27 — "Yes approve"

**(R2) re-sign checklist — 2026-06-29, SIGNED:**
- what changed: added §1 fact 4 (N's structural action decoupling) + the
  RETAIN-behavior/REPAIR-calibration mirror framing; §2 relationship to N (M revived
  as primary route); §3.4 (action separable; threshold bridge); §4 step 7 (action
  margin + τ-sweep, reporting-only); §4.3 says-but-doesn't-act branch + the
  pre-registered bridge prediction; §5 R2 in-scope endpoints.
- what did NOT change: §4.1 calibration gate, §4.2 behavior gate, the builder target
  spec (§3.1), the recipe (§3.2), the data scope (clean-SFT completions, SFT-only).
- new pre-registered endpoint: action margin (secondary); bridge prediction: a τ on
  M's calibrated scalar reaches margin ≥ ~14.5 pts AND a behavior point ≥ §4.2 gate.
- still-open R1 decisions carried forward (recommended defaults unchanged): global
  quantile; band [0.10, 0.90]; SFT-only clean completions first.
- authorization: user, 2026-06-29 — "1" (sign R2 as-is).
