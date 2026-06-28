---
title: "Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v0
date: 2026-06-27
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
target: arXiv (cs.CL / cs.AI)
evidence_base: >
  Phase-1/Phase-3 artifacts under experiment/phase1/. Internal-axis numbers:
  experiment/phase1/probe/analysis/_latent_knowledge_controls/ (a3_h_base_probe.json,
  c2_*.json, a1a2_h_lora.json, caution_axis_transfer.json) and
  docs/sessions/0026 checkpoints 002-004. Geometry: scratchpad/caution_residual_geometry.py
  over extraction__55254a04aa1f; caution_direction_L35.json. Steering:
  experiment/phase1/probe/analysis/current_clean_grpo_v2_* (caution_residual_intervention,
  caution_perp_residual_intervention, known_overrefusal_native_l26_coeff_sweep,
  l26_double_orthogonalized_panel_{a,b,c}_generation, knowledge_boundary_steer).
  Stated-confidence calibration: experiment/phase1/eval/analysis/calibration_gap_*.json
  (clean_sft_grpo_v2_seed1, clean_sft_grpo_v3_seed1, contrastive_sft_seed1,
  contrastive_masked_sft_seed1). Behavior: experiment/phase1/eval/results_amendment_*.
notes: >
  Numbers discipline: every quantitative claim in this draft traces to a named
  artifact above. All experiments are single-seed (seed 1), Qwen3-4B, evaluated on
  SelfAware (n=3369) unless stated otherwise; this is a within-model mechanistic
  study, not a multi-seed effect-size estimate. Figures marked "directional" rest
  on small wrong-answer cells (n=16 on the held-in TriviaQA known set) and are
  reported as such. Companion papers: the systematic evidence synthesis
  (meta-analysis/paper/draft-v0.md, "Paper 1") that defines the coherence axis this
  paper measures, and the three-way abstention-training comparison
  (experiment/paper/draft-v1.md, "Paper 2") that supplies the DPO/KTO behavior
  results referenced in Section 7.
---

# Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model

## Abstract

A model that says "I don't know" appropriately may still be performing humility
rather than possessing it. We separate the two in a small instruction-tuned model
(Qwen3-4B) by reading three signals on the same questions: an *internal* confidence
axis recovered by a linear probe on hidden states, the *stated* confidence the
model verbalizes as a number, and the *behavior* it commits to (answer or abstain).
On a known/unknown question split (SelfAware, n=3369), the internal axis separates
known from unknown items at AUROC ≈ 0.997 and is well-calibrated by a one-dimensional
readout (ECE ≈ 0.004), while the stated confidence the same model emits ranks
appropriateness at AUROC ≈ 0.52–0.56 — barely above chance — and is collapsed near
a constant (≈ 0.82, std ≈ 0.01–0.03). The model represents what it does not know;
it does not report it. We make four contributions. **(1)** We quantify this
representation–verbalization gap and show the relevant items are not internally
confused: questions the model over-refuses despite knowing them sit at an internal
"known" position. **(2)** We resolve the internal geometry into two correlated but
separable axes — a graded *doubt* axis (how known an item is) and a partially
independent *caution* gate (the refuse/answer decision); raw cosine overstates
their collinearity at −0.83, but held-out discriminability after orthogonalization
shows a genuine caution-specific component (refuse/answer AUROC 0.825 after
projecting out doubt). **(3)** We show behavior is *causally* steerable but
*asymmetrically*: ablating the caution residual cuts over-refusal on known
questions from 0.994 to 0.030 with clean specificity, yet no intervention we tried
induces appropriate abstention on genuine unknowns. **(4)** We show the stated
confidence gap survives seven training interventions (DPO, KTO, GRPO v1/v2/v3, and
two contrastive-SFT variants), and we localize the mechanism with a clean
single-variable dissociation: contrastive SFT installs stated calibration only when
it also supervises the wrong-answer text (which degrades behavior), and masking
that text recovers behavior but destroys the calibration. The verbalized
confidence channel is decoupled from the internal one, and current training
objectives move behavior or stated confidence but do not couple them. We argue the
remaining route is to supervise the stated channel *toward the model's own
calibrated internal axis*, and we frame that experiment.

## 1. Introduction

The dominant way to teach a language model epistemic humility is to teach it to
*act* humble: to abstain when it should, to hedge, to say "I don't know." Paper 1's
synthesis of the training literature [meta-analysis/paper/draft-v0.md] shows that
almost all of this work is measured at a single depth — a scalar confidence or a
binary abstention — and that one axis is almost entirely unmeasured: *coherence*,
whether the model's stated epistemic signal, its token-level signal, and its
hidden-state signal actually agree. Paper 1 names the distinction with Plato's
image from the *Meno*: a true opinion not tethered to a reason is like one of the
statues of Daedalus, apt to run away. A humility behavior not anchored to the
model's internal state is an untethered statue — right today, a runaway under
distribution shift.

This paper measures that axis directly in one model and reports what we found: the
tether is missing, and ordinary training does not install it. Concretely, the model
already holds a calibrated internal estimate of what it knows, but the number it
states is decoupled from that estimate, and seven training interventions that move
its behavior or its stated number fail to couple the two.

Our contributions, each a section below:

- **The gap (Section 4).** A linear probe on hidden states separates known from
  unknown questions at AUROC ≈ 0.997 and is calibrated to ECE ≈ 0.004 by a 1-D
  readout; the model's *stated* confidence on the same items ranks appropriateness
  at ≈ 0.52–0.56 and is near-constant. The over-refused-but-known items are
  internally "known," so the failure is verbalization, not representation.
- **The geometry (Section 5).** The internal signal decomposes into a graded
  *doubt* axis and a separable *caution* gate. We show why the naive measurement
  (raw cosine = −0.83, "they're the same axis") is wrong and the held-out
  orthogonalization measurement (caution-specific refuse/answer AUROC = 0.825) is
  right — a methodological caution about cosine in high-dimensional activation
  space.
- **Steerability (Section 6).** Behavior is causally controllable along the
  caution axis — ablation cuts over-refusal on known items 0.994 → 0.030 with clean
  specificity — but the control is asymmetric: we can relax excess caution, we
  cannot install missing caution (no intervention induces abstention on true
  unknowns).
- **Training resistance and a localizing dissociation (Section 7).** The stated-
  confidence gap survives DPO, KTO, GRPO v1/v2/v3, and contrastive SFT. A clean
  K↔L dissociation shows the calibration signal contrastive SFT installs is carried
  by supervising the wrong answer itself: keep it and behavior breaks; remove it
  and calibration breaks.

We then argue (Section 8) that because the model already *has* a calibrated
internal axis, the productive move is to supervise the *stated* channel toward that
internal axis — probe distillation — rather than to keep trying to induce
calibration from outcome rewards or answer-bound supervision.

A scope note before the results: this is a deep within-model mechanistic study of a
single model (Qwen3-4B) at a single seed. We are explicit throughout about which
numbers are robust population reads (n ≈ 3369) and which are directional small-cell
estimates, and Section 9 collects the threats to validity. The claims we stand
behind are qualitative and large in magnitude (0.997 vs 0.52; 0.994 → 0.030); the
claims we flag are the precise effect sizes.

## 2. Related work and positioning

**The coherence axis.** Paper 1 introduces a "Depths of Ignorance" taxonomy (L1
calibration, L2 structured ignorance, L3 distributional signatures, L4 objective
uncertainty) and a cross-cutting coherence/faithfulness axis, and documents that
the training literature clusters at L1 and almost never measures coherence. The
first systematic framework for "faithful calibration" finds that token-probability,
hidden-state, and sampled-consistency estimators of internal confidence diverge on
the same traces [arXiv:2606.03969], and multiple groups find that more inference-
time reasoning impairs calibration rather than helping [arXiv:2508.15050,
arXiv:2506.18183]. This paper is the empirical instantiation of Paper 1's coherence
axis on one model: we measure stated vs internal directly and ask whether training
couples them.

**Latent knowledge and probing.** A line of work shows that a model's hidden states
linearly encode whether it is being truthful or whether it knows an answer
[arXiv:2304.13734, arXiv:2212.03827, arXiv:2310.06824, arXiv:2207.05221]. Our
internal axis is in this family (a logistic probe on residual activations). Our
question is downstream of probing: granting that the knowledge is decodable, *why
does the model not say it*, and can training make it say it.

**Activation steering.** Inference-time intervention along a learned direction can
change model behavior [arXiv:2306.03341], and humility-adjacent behaviors such as
sycophancy live in steerable internal subspaces [arXiv:2604.03147]. We use steering
as a causal probe of our two-axis decomposition and report a clean asymmetry that,
to our knowledge, has not been isolated for the abstention behavior specifically.

**Abstention and preference training.** Paper 2 [experiment/paper/draft-v1.md]
establishes, on the same model and data, that cold-start SFT induces abstention (and
over-refusal), and that DPO and KTO reposition the abstention boundary rather than
inducing the behavior. This paper builds on Paper 2 by asking what happens to the
*confidence* channel under those and further objectives, and by adding the GRPO and
contrastive-SFT cells.

## 3. Setup

**Model and data.** All experiments use `unsloth/Qwen3-4B-bnb-4bit` with LoRA
adapters (r = 32, α = 64, dropout = 0.05, all-linear targets). Training data for the
abstention/confidence cells is built from TriviaQA-RC (no-context) following the
Cheng recipe (reusing the data-construction recipe, not released labels). The
out-of-distribution evaluation is SelfAware (n = 3369; 1032 unknown-labeled, 2337
known-labeled), scored with the Phase-1 eval harness
[experiment/phase1/eval/run_eval.py]. Probe and geometry work uses hidden-state
extractions from the merged models (extraction `55254a04aa1f`), best layer L35
unless noted.

**Three readouts on the same questions.**

- *Internal confidence (doubt axis).* A logistic probe fit on residual-stream
  activations to separate known-answerable from unknown questions, read at the
  generation position. Reported as known/unknown AUROC and as the calibration (ECE)
  of a 1-D readout along the axis [experiment/phase1/probe/analysis/_latent_knowledge_controls/].
- *Stated confidence.* The model is prompted to return JSON with an `answer` and a
  `response_confidence` ∈ [0,1] (its stated probability that its response is
  appropriate). We read the emitted scalar directly from scored rows
  [experiment/phase1/eval/analysis/calibration_gap_report.py].
- *Behavior.* Whether the model answered or abstained, and whether the answer was
  correct, summarized as truthful_rate, correct_on_known, over_refusal (refusal on
  known), and refusal_recall (refusal on unknown).

**Calibration metrics.** For the stated channel we report: AUROC of the emitted
scalar at ranking *response appropriateness* (the headline coherence number), the
standard deviation of the emitted scalar (a collapse detector), expected
calibration error against appropriateness (ECE), and the per-behavior-cell mean of
the emitted scalar (does the model state higher confidence when it is actually
right/appropriate?). For the internal channel we report known/unknown AUROC and the
1-D readout's ECE.

**Scope.** Single seed (seed 1), single model. We treat large qualitative contrasts
as the findings and flag precise effect sizes as single-seed estimates (Section 9).

## 4. Result 1 — The model represents what it does not know, and does not report it

The headline contrast is between two readouts of the same model on the same
questions.

**Internal.** The doubt-axis probe separates known from unknown questions at
**AUROC ≈ 0.997** at the best layer (L35), and this is a property of the internal
state rather than surface vocabulary: the residual probe beats a lexical baseline
(≈ 0.964) by +0.033 [a3_h_base_probe.json, c2_sft.json]. A one-dimensional logistic
readout along the doubt axis (fit without correct/wrong leakage, 5-fold CV) is
**near-perfectly calibrated in aggregate, ECE ≈ 0.004**, and its projection is
monotone across behavior cells (correct > wrong > refused > unknown) [docs/sessions/0026,
checkpoint 004-result].

**Stated.** The same model's emitted `response_confidence` is collapsed near a
constant — on the held-in known set, mean ≈ 0.821 with std ≈ 0.015 — and ranks its
own correct vs wrong answers at **AUROC ≈ 0.559 with ECE ≈ 0.142** [checkpoint
004-result]. On the full SelfAware evaluation the trained models' emitted scalar
ranks appropriateness at **AUROC ≈ 0.52–0.56** (Section 7, Table 2). Per behavior
cell the emitted number is nearly flat (≈ 0.81 whether the model was right, wrong,
or refused), whereas the internal projection is monotone.

So the discriminating signal exists internally and the verbalized number is a
collapsed near-constant. The model *knows* but does not *say*.

**The gap is not internal confusion.** A natural objection is that the model
over-refuses items it is genuinely unsure of. It does not: the known-but-refused
items sit at an internal "known" position. On the 0 (known) to 1 (unknown) doubt
scale, known-answered items sit at ≈ 0.001 and unknown-refused at ≈ 0.999, while
known-*refused* items sit at ≈ 0.25–0.28 — far from the unknown pole [c2_gap_sft.json,
c2_gap_grpo_dpo.json, a3_h_base_probe.json]. Over-refusal is a behavioral-threshold
phenomenon over items the model internally recognizes as known, not suppression of
a genuine internal "I don't know."

**The internal signal survives training.** Re-fitting the probe on each fine-tuned
model's own activations gives essentially identical separation: clean SFT 0.9968,
SFT→GRPO-DPO 0.9972, SFT→GRPO-v2 0.9971, all vs base 0.997 [c2_sft.json,
c2_grpo_dpo.json, a1a2_h_lora.json]. Training does not damage or move the internal
representation; it leaves the gap intact.

## 5. Result 2 — The internal signal is two axes: graded doubt and a separable caution gate

Reading "how known is this item" and "did the model refuse" as one axis would be
the parsimonious story, and the first measurement appears to support it: the raw
mass-mean cosine between the caution direction (refuse vs answer among knowns) and
the knowledge/doubt direction is **−0.83**, i.e. nearly collinear, opposite sign
[scratchpad/confidence_vs_axes.py; caution_direction_L35.json]. Under that reading,
refusal is simply the low-known tail of a single graded doubt axis.

That reading is an artifact of the instrument. Raw cosine in high-dimensional
activation space is dominated by a few shared high-variance dimensions and
overstates collinearity. Whitening the covariance (shrinkage λ = 0.1) drops the
cosine to **−0.565**, and the caution direction retains a substantial component off
the doubt axis: its **residual fraction is 0.557** (≈ 55.7% of the caution
direction's length, ≈ 31% of its variance, is doubt-orthogonal)
[scratchpad/caution_residual_geometry.py; L35 h_lora; kr = 168, ka = 300, ur = 300;
5-fold held-out].

The decisive test is held-out discriminability after orthogonalization. Predicting
refuse (1) vs answer (0) among known items:

| direction | held-out refuse/answer AUROC |
|---|---|
| knowledge/doubt axis alone | 0.875 (strong: refuse = less-known) |
| caution orthogonalized to doubt (`caution_perp`) | **0.825** |
| full caution | 0.894 |

Removing the *entire* rank-1 doubt direction barely dents refuse/answer
separability (0.894 → 0.825), so the refuse/answer decision is not confined to the
doubt axis: a genuine caution-specific gate exists [caution_residual_geometry.py].
The two are correlated — both are elevated on the low-known tail — but separable.

**Method lesson.** Raw cosine said "one axis" (−0.83); held-out discriminability
after orthogonalization says "two axes." The reliable instrument for "is direction
B reducible to direction A" is not cosine but whether B still discriminates its
target after A is projected out. Stronger whitening monotonically pushes the cosine
−0.83 → −0.56 → toward 0, re-validating an independent near-orthogonality estimate
(≈ 0.02) from a separate analysis. (Caveat carried to Section 9: we projected out
only the rank-1 mass-mean doubt direction; removing a full multi-dimensional
knowledge-probe subspace is the stronger reducibility test and is not yet done.)

**The caution axis is shared across training regimens.** The caution direction
recovered independently from SFT, GRPO-DPO, and GRPO-v2 models points the same way
(mean cross-regimen |cos| = 0.701 vs a random floor of 0.014; GRPO-DPO ↔ GRPO-v2 =
0.857) and is approximately orthogonal to the knowledge axis within each model
(|cos| ≈ 0.04–0.09) [caution_axis_transfer.json, c2_*.json]. Caution is a single,
stable, knowledge-orthogonal internal mechanism, not an artifact of one training
run.

## 6. Result 3 — Behavior is causally steerable, but asymmetrically

The two-axis decomposition makes a causal prediction: intervening on the caution
gate should change the refuse/answer decision without changing what the model knows.
It does — in one direction.

**Relaxing excess caution works, with clean specificity.** Ablating the caution
residual at L35 on known items (n = 541: 373 known-answered + 168 known-refused)
drops refusal on the known-refused group from **0.994 to 0.030** and recovers 0.57
correctness on those previously-refused items, while leaving known-answered behavior
essentially untouched (refusal stays 0.0; correctness 1.0 → 0.979)
[current_clean_grpo_v2_caution_residual_intervention/summary.json]. The doubt-
orthogonalized component is *independently* load-bearing: ablating `caution_perp`
alone drops known-refused refusal 0.994 → 0.524 and recovers 0.33 correctness, again
with clean known-answered specificity
[current_clean_grpo_v2_caution_perp_residual_intervention/summary.json]. The gate is
not merely a re-reading of doubt.

**It works during real generation, and it is directional.** A repair direction
applied at L26 during generation (orthogonalized to both unknown-refusal and
known-wrong directions; 96 pairs) reduces over-refusal-on-known monotonically with
coefficient — e.g. 75% → 54.7% at coefficient 20 — while leaving unknown-refusal at
≈ 100% and inducing essentially no new wrong answers on knowns
[current_clean_grpo_v2_l26_double_orthogonalized_panel_a_generation]. The effect is
layer-specific (applying the same direction at L24/L25 repairs less) and signed:
*subtracting* the direction reduces over-refusal (75% → 56.25%, truthful 48.96% →
60.42% at coefficient 15) while *adding* it makes over-refusal worse (→ 85.94%)
[current_clean_grpo_v2_known_overrefusal_generation_replay_96_coeff_sweep]. The cost
at high coefficient is a few hallucinated answers on knowns.

**Installing missing caution does not work.** Every intervention we tried leaves
unknown-refusal pinned at ≈ 100% and answer-on-unknown ≈ 0%: we can dial caution
down but not up where it is absent. Steering the *knowledge* axis directly (ITI over
11 heads, n = 256) barely moves behavior at all — over-refusal-on-known only 33.6% →
23.4% at the strongest setting, and answer-on-unknown stays ≈ 0% (max 0.78%)
[current_clean_grpo_v2_knowledge_boundary_steer/summary.json]. The causal leverage
on abstention lives on the caution axis, not the knowledge axis, and it is
one-directional.

**Reading.** The model's over-refusal is a mis-set threshold on a gate we can
relax, which is why steering fixes it cheaply. Appropriate abstention on a true
unknown would require *raising* the gate in the right place, which the same
machinery does not deliver. This asymmetry matters for any deployment story that
hopes to "steer in humility": the easy direction is reducing over-caution; the hard
direction — the one humility actually needs on novel unknowns — is unsolved.

## 7. Result 4 — Training does not close the stated-confidence gap, and a dissociation shows why

If behavior is steerable and the internal signal is calibrated, the open question is
whether *training* can make the model's *stated* confidence track appropriateness.
We ran seven interventions. None closes the gap, and the last two close it from
opposite sides in a way that localizes the mechanism.

**The seven interventions.**

1–2. **DPO, KTO.** Paper 2 shows these reposition the abstention boundary rather
than inducing abstention; on the confidence channel the emitted scalar remains a
flat high value across outcome cells (e.g. known-wrong ≈ 0.83) — repositioned
behavior, unchanged stated confidence [experiment/paper/analysis/amendment_b_confidence_alignment_by_outcome.csv].

3–4. **GRPO v1/v2.** Reward shaping over the behavior leaves the stated scalar
collapsed: GRPO-v2 emits mean ≈ 0.811 with std ≈ 0.013, ranks appropriateness at
AUROC ≈ 0.561, and ranks its own correct vs wrong at AUROC ≈ 0.532 (chance)
[calibration_gap_clean_sft_grpo_v2_seed1.json].

5. **GRPO v3 (proper scoring).** v3 adds a Brier proper-score confidence term under
which a near-constant is provably sub-optimal and the true per-question probability
is optimal; by design the term is sub-dominant to the behavior reward (confidence
weight 1.2, explicitly kept below the behavior magnitudes so behavior is not traded
away) [experiment/notes/grpo-v3-proper-scoring-confidence.md]. Importantly, the
failure here is not a degenerate target: a CPU preflight re-scoring 19,904 real
rollouts confirmed the per-prompt targets have real dynamic range (group-target
std 0.320 over 4211 prompts, 65.6% in [0.2,0.8]) and that emitting the calibrated
target strictly beats a flat 0.82 on 4211/4211 prompts (mean Brier gain +0.394)
[experiment/notes/computed-confidence-alignment-regimen.md]. Yet after training,
behavior is fine (truthful 40.99, correct_on_known 52.52, over_refusal 65.13,
refusal_recall 92.34) while the stated scalar stays high and flat (mean ≈ 0.849,
std ≈ 0.027) and still ranks appropriateness at AUROC ≈ 0.522
[calibration_gap_clean_sft_grpo_v3_seed1.json;
results_amendment_j_..._grpo_v3_seed1_full_4b]. A proper score with verified
per-prompt dynamic range, kept sub-dominant to the behavior reward to preserve
behavior, still does not move the three-token confidence readout: the confidence
term is out-competed by the behavior term it must stay below. This is the cleanest
form of the negative result — the objective was provably aligned with calibration
and still did not install it.

6–7. **Contrastive SFT (K) and answer-masked contrastive SFT (L).** These are the
dissociation, below.

**The K↔L dissociation (the localizing result).** Contrastive SFT supervises matched
high-confidence appropriate completions and low-confidence inappropriate completions.
Cell K supervises the entire assistant turn on inappropriate rows, including the
wrong-answer text. Cell L is identical except a generic per-row sub-span loss mask
removes the wrong-answer text from the loss, so inappropriate rows supervise only the
low confidence, not the wrong answer. This is a clean single-variable comparison: the
only difference is whether the wrong answer is in the loss.

Table 1. K↔L dissociation (SelfAware, n = 3369; gates from
experiment/protocol/AMENDMENT-L-...md).

| metric | gate | clean-SFT base | **K (answer supervised)** | **L (answer masked)** |
|---|---|---|---|---|
| emitted AUROC → appropriateness | ≥ 0.62 | ≈ 0.52 | **0.684 ✓** | **0.552 ✗** |
| emitted std (collapse detector) | ≥ 0.10 | ≈ 0.05 | 0.309 | 0.180 |
| ECE → appropriateness | < 0.30 | 0.40–0.44 | 0.183 | 0.277 |
| known_correct mean > known_wrong mean | — | fails | 0.670 > 0.306 ✓ | 0.756 > 0.742 ✓ (barely) |
| unknown_refused mean > unknown_wrong mean | — | fails | 0.581 > 0.156 ✓ | **0.666 < 0.696 ✗ (inverted)** |
| truthful_pct | ≥ 35.6 | 40.58 | **30.93 ✗** | **41.59 ✓** |
| correct_on_known_pct | ≥ 42.2 | 47.23 | **36.63 ✗** | **50.06 ✓** |
| over_refusal_pct | ≤ 67.5 | 57.51 | **79.2 ✗** | **62.73 ✓** |
| refusal_recall_pct | ≥ 82.0 | 87.02 | 83.72 ✓ | 93.51 ✓ |

[calibration_gap_contrastive_sft_seed1.json; calibration_gap_contrastive_masked_sft_seed1.json;
results_amendment_k_...; results_amendment_l_...]

K installs stated calibration (AUROC 0.684, large cell separations, the only cell to
beat chance at ranking correct vs wrong among answered knowns at AUROC 0.789) but
breaks behavior (over-refuses, correctness falls). L recovers behavior fully — it
matches or exceeds the clean-SFT base on every behavior metric — but the stated
calibration collapses back toward baseline (AUROC 0.552; the unknown cell-mean
ordering inverts, the model stating *higher* confidence when it answers an unknown
wrong, 0.696, than when it correctly refuses, 0.666). Note that L is not collapsed
to a constant (std 0.180 ≫ base 0.05): it emits *spread* confidence that does not
*discriminate*. Variance is not calibration.

**Mechanistic reading.** The wrong-answer supervision in K was load-bearing for the
stated calibration, not merely a behavior-breaking side effect. When K supervises
"{wrong answer} + low confidence" jointly, the low-confidence token is bound to the
act of producing that (wrong) answer, and that binding is what makes the stated
scalar track appropriateness. Remove the answer from the loss (L) and behavior
heals, but the confidence token loses the thing it was conditioned on, so
discrimination returns to baseline. Under a single SFT lever, stated calibration and
behavior are in tension: you can buy one or the other, not both. This is why we
report L as a successful behavior cell and a failed calibration cell rather than a
success — calibration over sycophancy.

**The K→RL follow-on: a second dissociation, confidence vs action.** The K↔L
result says a single SFT lever cannot buy calibration and behavior together. The
obvious next move is a *division of labour*: keep K's calibration and repair K's
behavior with reinforcement learning, which is built for behavior shaping. We ran
GRPO v3 (the same proper-scoring reward as intervention 5) on the K base rather
than the clean-SFT base — so that the KL anchor now references a *calibrated*
policy and the dominant behavior reward attacks K's over-refusal [Amendment N;
experiment/protocol/AMENDMENT-N-grpo-v3-on-contrastive-sft-base.md]. This is an
exploratory single-seed cell, reported separately from the locked matrix.

The calibration half of the bet pays: training on the K base *retains* stated
calibration even as the policy moves well off its reference (final KL ≈ 0.97).
The emitted scalar keeps AUROC → appropriateness 0.646, std 0.311, ECE 0.214, and
the full cell ordering — including the very ordering L inverted, unknown-refused
(0.542) > unknown-answered-wrong (0.138). RL on a calibrated base preserves
calibration where RL on the flat base (intervention 5) could not manufacture it;
the base, not the reward, was the binding constraint for the confidence channel.

But behavior does not repair — and *why* it does not is the result. Over-refusal
gets *worse*, not better (90.8%, vs K's 79.2%; truthful 31.9, below the 35.6
gate). Decomposing the answer/abstain decision from the confidence scalar (Table
2) shows the two channels have come apart. The confidence channel discriminates:
among refusals, the stated scalar separates a correct refusal (an unknown) from a
mistaken one (a known the model should have answered) at AUROC 0.62, and among
answers it separates correct from wrong at AUROC 0.84. The *action* channel barely
conditions on knowledge at all: the model answers knowns only 2.85 points more
often than unknowns (9.2% vs 6.4%; p = 0.006 — statistically real, practically
negligible). The decision is ~97% a single knowledge-independent propensity and
~3% knowledge.

Table 2. GRPO-v3-on-K — calibrated confidence, uncalibrated action (SelfAware,
n = 3369; greedy unless noted) [results_amendment_n_...; action_conditioning_report.py].

| channel | measurement | value |
|---|---|---|
| confidence | refusal-appropriateness AUROC (unknown-refused vs known-refused) | **0.62** |
| confidence | answer-correctness AUROC (correct vs wrong, among answers) | **0.84** |
| action | answer-rate margin, P(answer\|known) − P(answer\|unknown) | **+2.85 pts** (p = 0.006) |
| action | same margin at temperature 1.35 (training temperature) | +6.5 pts |
| action | same margin over training (1861 steps, binned) | +2.5 → ~+7 pts, never opens |

Temperature confirms this is not a decoding artifact. Greedy decoding refuses
almost everything (over-refusal 91%); sampling at the training temperature 1.35
answers almost everything (refusal 8%, and it now answers 87% of *unknowns* too);
at neither operating point does the decision discriminate known from unknown, and
at the high temperature even the confidence channel breaks (refusal-appropriateness
AUROC falls to 0.33, below chance). Temperature slides a single global
answer/refuse propensity; it does not create knowledge-conditioned action that
isn't there. And across all 1861 training steps the action margin never opened
(Table 2, row 5): the strong reward differential between refusing a known
(−1.28 mean reward) and refusing an unknown (+2.10) moved the *global* answer rate,
not the conditioning.

The reading extends this paper's thesis by one layer. The model knows internally
(Section 4) and, after K-style SFT, *says* it — the confidence scalar tracks
knowledge. But it does not *act* on it: the answer/abstain decision is decoupled
from the very signal the model is now able to verbalize. "Knows but doesn't say"
becomes, here, "says but doesn't act." Whether this last gap is structural or an
artifact of the KL anchor pinning the action to K's over-refusing mode is a live
question we are testing with a lower-KL (β 0.05) re-run, pre-registering the
falsifier before the result: the action margin must open to ≥ ~14.5 points (the
separation the behavior gate implies) or we record the decoupling as structural.

## 8. Discussion

**Possessed vs performed humility, measured.** Paper 1 framed the distinction
between humility a model possesses (tethered to its internal state) and humility it
merely performs (untethered behavior). Section 4 makes the distinction concrete: the
internal tether exists and is calibrated (ECE 0.004), the performed behavior can be
shaped (Sections 6–7), and the *stated* confidence — the channel a user actually
reads — is tied to neither. The model is, in the precise sense of the *Meno*, giving
true opinions without the tether; our seven interventions are attempts to install
the tether, and they fail.

**Why the stated channel is the stubborn one.** The internal axis survives training
untouched (Section 4) and behavior is cheaply steerable (Section 6), yet the stated
scalar resists every objective we tried. The dissociation explains why: outcome and
preference rewards (DPO/KTO/GRPO) move behavior and leave the scalar collapsed
because the scalar is a tiny part of the supervised signal; the one objective that
moved the scalar (contrastive SFT) did so by entangling it with answer text, which
trades behavior. No objective we tried supervises the stated scalar *against the
right target directly*.

**The implied experiment: quantile-balanced probe distillation.** The model already
contains a calibrated estimate of appropriateness — the internal doubt axis (ECE
0.004). The natural objective is therefore not to induce calibration from outcomes,
but to *distill the internal axis into the stated channel*: supervise the emitted
`response_confidence` toward the model's own doubt-axis readout, so the model learns
to *say* what it already *represents*. This decouples the confidence target from the
answer text (avoiding K's trade) and supplies a dense, per-item, calibrated target
(avoiding GRPO's out-competed confidence term).

One caution is already on record and shapes the design. A *naive* probe-scaled SFT
target (response_confidence = 0.1 + 0.8·appropriateness_p) was run earlier and
collapsed: it emitted a single value (0.8765) on every row, because the target
*distribution* is imbalanced — most known items are answerable, so most targets land
in a high band, and cross-entropy is minimized by emitting that mode regardless of
the input [experiment/notes/computed-confidence-alignment-regimen.md, §004]. The
fix is to make the target *per-question grounded and distribution-balanced* at once:
quantile-map the probe estimate onto a spread band so that emitting any constant is
penalized, forcing the model to use the question to predict the target — which is
exactly what installs discrimination. This is the experiment we take up next; like
all training cells here it requires a new governed protocol amendment, and it
inherits this paper's measurement: success means the stated channel finally clears
both the calibration gate (AUROC → appropriateness ≥ 0.62, with discrimination, not
just spread) and the behavior gate at once — the cell neither K nor L could be.

**Implications beyond this model.** If the pattern generalizes (Section 9 is honest
that we have not shown this), it reframes a common assumption in abstention training:
that teaching better behavior will produce better-calibrated confidence. Here the two
are dissociable, and the confidence channel needs its own, internally-anchored
supervision. It also tempers the "steer in humility at inference" hope: the easy
steering direction (less over-caution) is the opposite of what novel unknowns
require (more caution), and we could not install the hard direction.

## 9. Limitations

- **Single seed, single model.** Every number is seed 1 on Qwen3-4B. The large
  qualitative contrasts (0.997 vs 0.52; 0.994 → 0.030; the K↔L direction flip) are
  unlikely to be seed noise, but the precise effect sizes are single-seed estimates
  and the whole pattern needs replication across seeds and at least one other model
  family/size before any claim of generality.
- **Small wrong-answer cells.** Some internal-vs-stated discrimination numbers rest
  on few wrong-answered items (n = 16 on the held-in known set); these are reported
  as directional. The full-eval AUROC numbers (n ≈ 3369) are not affected.
- **SelfAware-only OOD surface.** Behavior and stated-calibration numbers are on one
  OOD benchmark. Generalization to other known/unknown surfaces is untested.
- **Rank-1 doubt projection.** The two-axis separability (Section 5) projects out
  only the rank-1 mass-mean doubt direction. The stronger test — removing a full
  multi-dimensional knowledge-probe subspace and re-checking `caution_perp` — is not
  yet done; it could shrink the caution-specific residual.
- **Probe could read outcome leakage.** The internal axis is fit on activations; we
  control for lexical baselines and fit the readout without correct/wrong leakage,
  but probe-based "knowledge" claims always carry the risk that the probe reads a
  correlate. The causal steering results (Section 6) partly mitigate this for the
  caution axis but not for the doubt axis.
- **Steering is single-site / few-layer.** The interventions are at L35 (ablation)
  and L26 (generation); we did not exhaustively search layers or multi-site
  combinations, so "cannot install caution" is a statement about the interventions
  tried, not a proof of impossibility.
- **The K→RL confidence/action result is single-seed and exploratory.** The
  GRPO-v3-on-K cell (Section 7, Table 2) is one seed of one exploratory amendment,
  reported separately from the locked matrix; the confidence/action decoupling
  should be read as a lead, not an established claim, until replicated. Its central
  open question — whether the decoupling is structural or an artifact of the KL
  anchor — is the subject of a pre-registered lower-KL (β 0.05) re-run that was not
  yet complete at the time of writing; the falsifier (action margin ≥ ~14.5 points)
  was fixed in advance.

## 10. Conclusion

In one small instruction-tuned model, epistemic humility is three things that do not
agree: a calibrated internal estimate of what the model knows, a behavior that can
be cheaply steered down (but not up) along a separable caution gate, and a stated
confidence number that tracks neither and resists every training objective we tried
to fix it with. The decisive evidence is a single-variable dissociation: contrastive
SFT can install stated calibration only by supervising the wrong-answer text, which
breaks behavior, and masking that text restores behavior while destroying the
calibration. The model knows but does not say, and current objectives move what it
says or what it does without coupling them. Because the calibrated signal already
exists inside the model, the route we have not yet tried — and the one this paper
motivates — is to supervise the stated channel toward the model's own internal axis.

## Data and code availability

All training configs, eval configs, reward definitions, probe/geometry/steering
scripts, governed protocol amendments, and per-cell calibration reports are in the
repository [https://github.com/ProfSynapse/Epistemic-Humility-Research] under
`experiment/phase1/` and `experiment/protocol/`. The per-cell stated-confidence
calibration reports are at `experiment/phase1/eval/analysis/calibration_gap_*.json`;
the internal-axis and steering artifacts are under
`experiment/phase1/probe/analysis/`. Restricted or gitignored datasets (e.g. bridge
sets) are not redistributed. This is draft-v0; numbers are current as of 2026-06-27.

## References

(Shared bibliography with Paper 1; arXiv identifiers are cited inline. To be
compiled for submission.)
