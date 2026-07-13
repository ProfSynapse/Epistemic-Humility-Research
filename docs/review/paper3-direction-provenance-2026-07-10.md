# Paper 3 internal-direction provenance census

Date: 2026-07-10. Repo HEAD: 0d28ecbf (main). Author: provenance-census subagent.
Purpose: before moving the program's discovered internal epistemic directions into
`papers/paper-3-knows-but-doesnt-say/manuscript.md`, record each direction's exact
discovery provenance so paper 3's scope statement stays honest.

Rules honored: every experimental fact below is cited to the governed doc
(`experiments/<slug>/AMENDMENT.md`, section) or the pinned artifact/script I read it
from. Library term notes and the registry were used as navigation only and are
flagged wherever a number lives only there. Facts stated "at prep/sim level" are NOT
from a governed reading-gate amendment and are marked as such.

Directions covered: DOUBT axis, CAUTION axis (+ `caution_perp`), CONFAB-PROPENSITY
direction. Also cross-referenced: the ANSWERABILITY gate and CORRECTNESS dial (the
lead states these are already placed) because DOUBT collides with ANSWERABILITY (see
Ambiguity A1).

---

## 1. DOUBT axis (a.k.a. knowledge-boundary / known-vs-unknown readout)

**Defining experiment / doc.** The governed home is
`experiments/selfaware-latent-knowledge-controls/AMENDMENT.md` (status: historical
lab-notebook diagnostic, "not a governed amendment and not a confirmatory claim").
It delegates all definitional detail to its pinned scripts. The fit is defined in
`experiments/selfaware-latent-knowledge-controls/latent_knowledge_probe.py`
(docstring + `analyze`): a per-layer 5-fold cross-validated **L2 logistic probe** of
the residual-stream activation at the **final prompt token** predicting ground-truth
**known vs unknown** (SelfAware label). Best layer **L35**, known/unknown **AUROC
0.997**. The paper-3 geometry uses the mass-mean cousin of this direction at L35
(`archive/experiment/phase1/probe/paper3_section5_geometry.py`, cited in
`papers/paper-3-knows-but-doesnt-say/manuscript.md` Section 5).

**Model / checkpoint.** Two extraction sources appear in
`experiments/selfaware-latent-knowledge-controls/experiment.yaml` inputs:
- `a1a2_h_lora.json` / geometry (`h_lora`) = the active-adapter stream of the
  **trained** checkpoint (clean-SFT to GRPO-v2, seed 1). Paper-3 Section 5 geometry
  is computed on this (`L35 h_lora`).
- `a3_h_base_probe.json` (`h_base`) = the base residual stream captured in the SAME
  extraction pass; reads **0.997 @ L35** (I read the per-layer array directly from
  the artifact). This is the base pathway of the trained-checkpoint forward pass, not
  a separately-run raw base model.

**Reading-side claims (established, with citations).**
- Known/unknown AUROC 0.997 @ L35 (`a3_h_base_probe.json`; `a1a2_h_lora.json` L35
  0.9971). Lexical (question-text TF-IDF) control margin +0.033 over lexical 0.9641
  (`a1a2_h_lora.json` A1). Over-refusals sit at the KNOWN pole
  (`latent_knowledge_probe.py` over-refusal gap; selfaware AMENDMENT §Result).
- On the deployed checkpoint the same axis reads known/unknown at AUROC 0.972 while
  the emitted confidence scalar sits at ~0.52
  (`experiments/doubt-regulated-caution/AMENDMENT.md` §1, citing session-0026
  `calibration_gap_clean_sft_grpo_v2_seed1.json`). This is the paper-3 headline gap.

**Base / pretrain validation of the READING (yes, strong).** This is the same
known/unknown separation the program elsewhere governs as the ANSWERABILITY gate,
and that signal is base- and pretrain-validated by GOVERNED amendments:
- `experiments/base-model-training-free-mechanism/AMENDMENT.md` (Amendment W) §7:
  gate (known vs unknown, pre-gen anchor) **AUROC 0.997 @ L18, CI [0.995, 0.999]** on
  the RAW `unsloth/Qwen3-4B-bnb-4bit` Instruct base, NO adapter, NO program training.
- `experiments/pretrain-only-base-readout/AMENDMENT.md` (Amendment Y) §9: gate
  **0.997+** on four PRETRAIN-ONLY bases (Qwen3.5-4B-Base, Gemma-4-E4B pt,
  Llama-3.2-3B base, Olmo-3-7B base); H_B1 (pretraining origin) SUPPORTED 4/4;
  falsifier fired 0/4.
- A raw-base doubt-gate reading also appears in the (unsigned, worktree) tighten
  diagnostic: `neg_z_d` separates confab from known-correct at AUC 0.976 on raw-base
  `unsloth/Qwen3-4B` bf16
  (`experiments/doubt-gated-caution-tighten/AMENDMENT.md` Motivation).

**Actuation claims (paper 5, NOT paper 3).** Doubt-coupled caution write AC-G1 PASS
+8.7pt (`experiments/doubt-regulated-caution/AMENDMENT.md` outcome); doubt-gated
caution snap G1/G2/G3 (`experiments/doubt-gated-caution-tighten`). These are writes
and stay in the actuation paper.

**Verdict: SAFE for paper 3** (it is already in Sections 5-6). Reading side is the
best-validated of the three: base- and pretrain-origin confirmed by governed
amendments W and Y.

**Proposed scope sentence.** "The internal doubt axis is the model's linear
known-versus-unknown readout (5-fold logistic probe on the final-prompt-token
residual, best layer L35, AUROC 0.997); we recover it on the trained checkpoint but
the same separation is present untrained on the raw Qwen3-4B base (0.997) and on four
pretrain-only base models (0.99+), so the reading is a pretraining-origin property,
not a product of our training."

---

## 2. CAUTION axis (over-refusal / refuse-vs-answer gate) and `caution_perp`

**Defining experiment / doc.** Same governed home
(`experiments/selfaware-latent-knowledge-controls/AMENDMENT.md`, historical
lab-notebook). Fit defined in `latent_knowledge_controls.py` `a2_within_known`:
restrict to KNOWN rows only, then an L2 logistic residual probe predicting
**known_refused (over-refused) vs answered** — a contrast orthogonal to known/unknown.
`caution_perp` is this direction with the doubt direction projected out (perp
fraction 0.558; `paper3_section5_geometry.py`, cited in manuscript Section 5 and in
`experiments/doubt-regulated-caution/AMENDMENT.md` §1). Layer L35.

**Model / checkpoint.** TRAINED checkpoints only. The transfer panel
(`caution_axis_transfer.json`, read directly) fits caution on three arms: **sft,
grpo_dpo, grpo_v2** (mean cross-regimen |cos| 0.701, random floor 0.014,
SHARED-AXIS). Paper-3 geometry is L35 `h_lora` (clean-SFT to GRPO-v2). There is no
raw-base or instruct-base arm in the transfer panel.

**Reading-side claims (established, with citations).**
- Refuse-vs-answer among knowns: full caution AUROC 0.885; `caution_perp` (doubt-
  orthogonalized) 0.798 held-out; doubt axis alone 0.866; raw cosine to doubt -0.83,
  whitened -0.61 (`paper3_section5_geometry.py`, manuscript Section 5 table).
- Certified linear erasure of the answerability concept (LEACE) costs caution only
  5.4 +/- 0.6 of 91 points, leaving refuse/answer at 0.858
  (`experiments/knowledge-subspace-erasure/AMENDMENT.md`, Amendment AJ) — caution's
  separability is not carried by the knowledge readout.
- Caution is a single shared knowledge-orthogonal mechanism across SFT/DPO/GRPO-v2
  (`caution_axis_transfer.json`, |cos| to knowledge ~0.04-0.09).

**Base validation of the READING: NO, and it is not obtainable.** Caution is defined
by a refuse-vs-answer contrast among KNOWN items; that contrast only exists once the
model over-refuses. The raw base does not abstain: Amendment W ran 1,233 SelfAware
questions and recorded **0 refused** ("the base is pre-abstention and answered every
question", `experiments/base-model-training-free-mechanism/AMENDMENT.md` §7). So no
known-refused cell exists on the raw base and no base caution READING can be fit. The
raw-base caution work that does exist is ACTUATION only (a fixed write/"snap"
setpoint, `experiments/doubt-gated-caution-tighten/AMENDMENT.md`), where the direction
is used as a write axis and is explicitly described as a one-way "say-I-don't-know"
axis, not a fitted base reading.

**Actuation claims (paper 5, NOT paper 3).** Ablating `caution_perp` cuts
known-item over-refusal 0.994 to 0.030/0.524 with specificity
(`experiments/doubt-regulated-caution/AMENDMENT.md` §1); the caution snap tighten
instrument (`doubt-gated-caution-tighten`). Writes; stay in the actuation paper.
(Manuscript Section 6 already reports the 0.994 to 0.030 ablation as a paper-3
steering result — see Ambiguity A3.)

**Verdict: SAFE for paper 3 as a READING claim, with a required checkpoint caveat.**
Caution reading is genuine and knowledge-orthogonal, but it is intrinsically a
trained-checkpoint construct; the scope statement must not imply a base-model caution
reading exists.

**Proposed scope sentence.** "The caution gate (the refuse-versus-answer decision
among items the model knows) is a separable, knowledge-orthogonal internal axis that
recovers consistently across our SFT, DPO, and GRPO-v2 checkpoints; unlike the doubt
axis it is defined only where the model over-refuses, so it is a property of the
trained (post-abstention) model and we make no base-model claim for it."

---

## 3. CONFAB-PROPENSITY direction

**Defining experiment / doc.** The only GOVERNED doc that defines the direction is
`experiments/radial-anti-propensity-steering/AMENDMENT.md` (Amendment AL) §3.2: an
**L24 PCA-128** (randomized, seed 20260705), standardized, **caution-residualized**,
**mean-diff of confab vs unanswerable-refused**, fit on the full baseline surface and
frozen; the steering vector is the raw-2560-dim preimage. AL §Depends-on and §1
attribute the direction's origin to "the session-0037 commitment-signal line ... that
the scope check renamed confabulation propensity" and the session-0038 AL-prep
instruments. `experiments/confab-mechanics-cpu-fleet/AMENDMENT.md` is a thin
historical banking record of the phenotype/signature/familiarity scripts on the "AH
raw-base surface" and defines no reading gate.

**Model / checkpoint.** The **AI-TRUE** checkpoint: clean-SFT to GRPO with a
probe-as-reward TRUE arm (a deeply program-trained checkpoint), on the session-0038
TRUE A0 surface (`radial-anti-propensity-steering/AMENDMENT.md` §1, §3.1). AL §7
states the direction "needs refit per checkpoint (reference axes transferred at
**cosine 0.17**)" — it is checkpoint-specific and does not port.

**Reading-side claims (weak governance).** AL §1 (as motivation) states, at
"readout-plus-simulation" level: the residual confabs form a compact cloud that reads
boundary-elevated without an actually-knowing signal; the propensity direction is
confabulation-specific, not generic answer commitment (**cosine -0.35** against the
answer-vs-refuse direction; chance transfer at matched caution); the anti-propensity
push is the only channel with statistically real simulated reach (permutation
p=0.005). The frequently-quoted separation numbers (AUROC 0.834 caliper-matched,
session 0037; 0.67-0.68 caution-residualized on the session-0038 TRUE surface) appear
ONLY in the library term note
`library/concepts/terms/confabulation-propensity-direction.md` and the session-0037/
0038 prep, NOT in a governed reading-gate amendment. Per the read-before-cite rule I
do not treat those two numbers as established results.

**Base / instruct validation: NO.** The direction is defined and only ever validated
on the AI-TRUE deeply-trained checkpoint; it is caution-residualized by construction,
refit per checkpoint, and transfers at cosine 0.17. There is no base or instruct
reading claim.

**Actuation claims (paper 5, NOT paper 3) — and they are NULL.** AL is the governed
causal test: **USE-THE-SIGNAL NULL** — AL-G1 PASS (collateral 0/3), AL-G2 MISS (0 of
116 baseline confabs killed), AL-G3 MISS (primary-minus-control 0, CI [0.00, 0.00]);
smoke readback confirms the write landed on-axis, so the null is causal not
instrumental (`radial-anti-propensity-steering/AMENDMENT.md` outcome). Two follow-on
governed causal tests are also NULL: selected-setpoint regulator (Amendment AN,
`experiments/selected-setpoint-regulator/AMENDMENT.md`, registry: NULL, confounded)
and ao-propensity-regulated-caution (registry: NULL, Stage-1 knob validation fail).

**Verdict: NOT safe to report in paper 3 as an established internal reading
direction.** Its reading numbers are prep/sim-level (ungoverned), it is
checkpoint-specific to a deeply-trained checkpoint with no base validation, and its
only governed causal outcome is a null. Reporting it inside paper 3's
internal-vs-stated-confidence scope would overstate its status. If paper 3 references
it at all, it should be a one-line forward pointer to the actuation paper (paper 5),
framed as a checkpoint-specific correlate whose causal test came back null, not as a
paper-3 result.

**Proposed scope sentence (only if a pointer is wanted).** "A separate
confabulation-propensity direction (a caution-residualized read of which unanswerable
items draw a fabricated answer) is checkpoint-specific to our most-trained checkpoint
and is examined in the companion actuation paper, where writing along it does not
causally convert confabulations into refusals; we therefore do not include it among
this paper's internal-confidence signals."

---

## 4. Directions the lead noted as already placed (for framing only)

- **ANSWERABILITY gate / subspace** — governed by Amendment O (in-distribution
  ceiling AUROC 0.9967) and Amendment P `experiments/xdataset-probe-transfer`
  (cold KUQ-to-SelfAware transfer 0.9834). Base/pretrain-validated by W and Y.
  This is the SAME known/unknown separation paper 3 calls the doubt axis (see A1).
- **CORRECTNESS dial** — governed by Amendment S
  `experiments/correctness-confidence-probe` (per-attempt correctness, post-gen
  AUROC 0.834, self-eval gain +0.065). Base-validated: raw-base dial 0.834 (W §1),
  pretrain-only bases 0.79-0.87 (Y §9). Also the hallucination-veto leg (dial flags
  confabulations lowest-trust) is base-present 0.754 and training-sharpened to 0.980
  (W §7; `unified-two-signal-dial-veto` Amendment U).

I found no other program-fit internal direction beyond these; the remaining
direction-like entries under `library/concepts/terms/` (refusal-direction,
entity-recognition-direction, truth-direction, known-unknown-direction,
answerability-subspace, etc.) are ingested-literature concepts, not directions this
program fit.

---

## 5. Ambiguities and gaps (do not paper over)

**A1 — DOUBT and ANSWERABILITY are the same signal under two names.** Paper 3's
"doubt axis" (§5, known/unknown logistic/mass-mean probe, AUROC 0.997 @ L35) and the
program's "answerability gate / subspace" (Amendments O/P/W/Y, known/unknown AUROC
0.99+) are the same known-versus-unknown separation. Treating "answerability already
placed" and "doubt to be moved" as two distinct directions would double-count one
signal. Recommendation: paper 3 should state explicitly that its doubt axis is the
answerability/knowledge-boundary readout viewed as graded confidence.

**A2 — the governed home for doubt/caution is thin and delegates.**
`selfaware-latent-knowledge-controls/AMENDMENT.md` is an imported historical
lab-notebook that is explicitly "not a governed amendment and not a confirmatory
claim"; the fit lives in its pinned scripts, and paper 3 Section 5's precise geometry
numbers (cosine -0.83/-0.61, caution_perp 0.798, perp fraction 0.558) trace to a
legacy script `archive/experiment/phase1/probe/paper3_section5_geometry.py`, not to a
signed amendment. The reading claims are governed indirectly (via AC §1 for the
deployed-checkpoint numbers, AJ for erasure, W/Y for base validation). This is
adequate for an exploratory within-model paper but the manuscript should keep citing
the legacy script + AJ/W/Y rather than implying a single governed doubt/caution
amendment exists.

**A3 — caution actuation is already inside paper 3.** Manuscript Section 6 reports
the caution-ablation steering result (over-refusal 0.994 to 0.030). The lead's brief
places actuation in paper 5. Either paper 3's scope must be widened to own that one
steering result explicitly (it currently does), or it should be moved to paper 5 for
consistency. Flagging because it affects the "reading in paper 3, actuation in paper
5" split the census assumes.

**A4 — confab-propensity reading numbers are ungoverned.** The 0.834 / 0.67-0.68
separation figures exist only in the term note and session-0037/0038 prep, not in a
governed reading-gate amendment. Any paper-3 sentence must not cite them as
established results.

**A5 — checkpoint heterogeneity across the three directions.** Doubt is validated on
raw base + pretrain-only bases + trained checkpoint; caution only on trained
SFT/DPO/GRPO-v2; confab-propensity only on the AI-TRUE probe-as-reward checkpoint.
A single sentence like "we read three internal directions on the same model" would be
misleading: they live on different checkpoints and only doubt has a base reading.

---

## 6. Summary table

| Direction | Defining experiment (doc) | Model / checkpoint | Base-validated reading? | Safe for paper 3? | Proposed scope sentence (short form) |
|---|---|---|---|---|---|
| DOUBT axis | selfaware-latent-knowledge-controls (historical lab-notebook; fit in latent_knowledge_probe.py); base reading via W and Y | Trained clean-SFT to GRPO-v2 (h_lora) for geometry; also raw Qwen3-4B base + 4 pretrain-only bases | YES (raw base 0.997, W; pretrain-only 0.99+ 4/4, Y) | YES (already in) | Known/unknown logistic probe, L35, 0.997; pretraining-origin, present untrained. |
| CAUTION axis (+ caution_perp) | selfaware-latent-knowledge-controls (fit in latent_knowledge_controls.py a2_within_known); geometry paper3_section5_geometry.py; erasure AJ | Trained SFT / DPO / GRPO-v2 only (h_lora) | NO — not obtainable (base does not over-refuse, W §7: 0 refused) | YES as a reading claim, with trained-checkpoint caveat | Refuse-vs-answer gate among knowns, knowledge-orthogonal, shared across trained regimens; a post-abstention property, no base claim. |
| CONFAB-PROPENSITY | radial-anti-propensity-steering AL §3.2 (origin session 0037/0038 prep) | AI-TRUE (clean-SFT to GRPO probe-as-reward TRUE); checkpoint-specific (transfer cos 0.17) | NO | NO — reading ungoverned, checkpoint-specific, only governed causal test is null | If referenced, a forward pointer to paper 5: checkpoint-specific correlate, causal test null; excluded from paper 3's confidence signals. |
| ANSWERABILITY (already placed) | O / xdataset-probe-transfer (P); base via W, Y | Trained + raw base + pretrain-only | YES | already placed | (= doubt axis, see A1) |
| CORRECTNESS dial (already placed) | correctness-confidence-probe (S) | Raw Qwen3-4B base + pretrain-only + trained | YES (W §1, Y §9) | already placed | Per-attempt correctness read post-generation, training-free. |
