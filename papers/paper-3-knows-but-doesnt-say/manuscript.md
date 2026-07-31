---
title: "Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v1
date: 2026-07-02
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
target: arXiv (cs.CL / cs.AI)
evidence_base: >
  locked-training-regimen/legacy-mech-interp artifacts under archive/experiment/phase1/. Internal-axis numbers:
  experiments/selfaware-latent-knowledge-controls/artifacts/latent_knowledge_controls/ (a3_h_base_probe.json,
  c2_*.json, a1a2_h_lora.json, caution_axis_transfer.json) and
  docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md checkpoints 002-004. Geometry:
  archive/experiment/phase1/probe/paper3_section5_geometry.py over extraction__55254a04aa1f;
  caution_direction_L35.json / caution_perp_direction_L35.json. Steering:
  archive/experiment/phase1/probe/analysis/current_clean_grpo_v2_* (caution_residual_intervention,
  caution_perp_residual_intervention, known_overrefusal_native_l26_coeff_sweep,
  l26_double_orthogonalized_panel_{a,b,c}_generation, knowledge_boundary_steer).
  Stated-confidence calibration: archive/experiment/phase1/eval/analysis/calibration_gap_*.json
  (clean_sft_grpo_v2_seed1, clean_sft_grpo_v3_seed1, contrastive_sft_seed1,
  contrastive_masked_sft_seed1). Behavior: archive/experiment/phase1/eval/results_amendment_*.
notes: >
  Numbers discipline: every quantitative claim in this draft traces to a named
  artifact above. All experiments are single-seed (seed 1), Qwen3-4B, evaluated on
  SelfAware (n=3369) unless stated otherwise; this is a within-model mechanistic
  study, not a multi-seed effect-size estimate. Figures marked "directional" rest
  on small wrong-answer cells (n=16 on the held-in TriviaQA known set) and are
  reported as such. Companion papers: the program's taxonomy and
  evidence-synthesis paper, [*The Depths of Ignorance: A Taxonomy, Systematic
  Evidence Synthesis, and Research Agenda for Epistemic Humility in Language
  Models*](../paper-1-taxonomy-framework/manuscript.md) (superseded source
  draft retained at archive/meta-analysis/paper/draft-v0.md), defines the
  coherence axis this paper
  measures; the SFT/DPO/KTO/GRPO regimen experiment, [*Teaching Small Language
  Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and
  GRPO on Model-Specific Abstention Data*](../paper-2-training-regimen/manuscript.md),
  supplies the DPO/KTO behavior results referenced in Section 7. This paper is
  the third in the series; the training-free two-signal readout it motivates is
  [*It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for
  Epistemic Humility in Small Language Models*](../paper-4-two-signal-readout/manuscript.md).
  draft-v1 (2026-07-02) absorbs the confidence-channel and probe-coda depth
  (old regimen-paper Sections 7-8): the RL-collapse incentive analysis, the
  Brier proper-scoring equation and its full negative, precise
  RL-on-calibrated-base numbers, the confidence-training synthesis, the
  five-arm and knows-vs-says figures, and a provenance appendix (Appendix A).
  Reader-facing prose no longer names internal amendment labels; the mapping
  lives in Appendix A.
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
appropriateness at AUROC ≈ 0.52–0.56 (barely above chance) and is collapsed
near a constant (≈ 0.82, std ≈ 0.01–0.03). The model represents what it does not know;
it does not report it. By "knows" we mean this internal recognition of which
questions are answerable, not verified self-knowledge that the model's own answer
is correct. We make four contributions. (1) We quantify this
representation–verbalization gap and show the relevant items are not internally
confused: questions the model over-refuses despite knowing them sit at an internal
"known" position. (2) We resolve the internal geometry into two correlated but
separable axes: a graded *known-unknown (answerability) axis* (how known an item
is; previously called the doubt axis) and a partially
independent *caution* gate (the refuse/answer decision); raw cosine overstates
their collinearity at −0.83, but held-out discriminability after orthogonalization
shows a genuine caution-specific component (refuse/answer AUROC ≈ 0.80 after
projecting out the known-unknown axis). (3) We place the two axes in the program's anatomy: the
known-unknown axis is the answerability separation itself, present untrained (0.997 on the
raw base, 0.997+ on four pretrain-only bases), while caution is a construct of the
trained model alone, unreadable on a base that never refuses; training does not
create the known-unknown axis, but it does create caution. A companion actuation study confirms the
caution gate is causally real and one-way (ablation collapses over-refusal on
known questions from 0.994 to 0.030, yet no intervention installs appropriate
abstention on genuine unknowns). (4) We show the stated
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
*act* humble: to abstain when it should, to hedge, to say "I don't know." The
taxonomy paper's review of the training literature
([*The Depths of Ignorance*](../paper-1-taxonomy-framework/manuscript.md)) shows that
almost all of this work is measured at a single depth (a scalar confidence or a
binary abstention) and that one axis is almost entirely unmeasured: *coherence*,
whether the model's stated epistemic signal, its token-level signal, and its
hidden-state signal actually agree.
[*The Depths of Ignorance*](../paper-1-taxonomy-framework/manuscript.md) names the
distinction with Plato's image from the *Meno*: a true opinion not tethered to
a reason is like one of the statues of Daedalus, apt to run away. A humility
behavior not anchored to the model's internal state is an untethered statue:
right today, a runaway under
distribution shift.

This paper measures that axis directly in one model and reports what we found: the
tether is missing, and ordinary training does not install it. Concretely, the model
already holds a calibrated internal estimate of what it knows, but the number it
states is decoupled from that estimate, and seven training interventions that move
its behavior or its stated number fail to couple the two.

Our contributions, each a section below:

- The gap (Section 4). A linear probe on hidden states separates known from
  unknown questions at AUROC ≈ 0.997 and is calibrated to ECE ≈ 0.004 by a 1-D
  readout; the model's *stated* confidence on the same items ranks appropriateness
  at ≈ 0.52–0.56 and is near-constant. The over-refused-but-known items are
  internally "known," so the failure is verbalization, not representation. The
  axis is not created by our training: the same separation reads at 0.997
  untrained on the raw base and at 0.997+ on four pretrain-only bases.
- The geometry (Section 5). The internal signal decomposes into a graded
  *known-unknown axis* and a separable *caution* gate. We show why the naive measurement
  (raw cosine = −0.83, "they're the same axis") is wrong and the held-out
  orthogonalization measurement (caution-specific refuse/answer AUROC ≈ 0.80) is
  right, a methodological caution about cosine in high-dimensional activation
  space. Caution, unlike the known-unknown axis, is a construct of the trained model alone: a base
  that never refuses offers no refuse/answer contrast to read.
- Causal status, imported (Section 6). A companion actuation study
  establishes that the caution gate is causally real but asymmetric: ablating the
  caution direction collapses over-refusal on known items (0.994 → 0.030) with
  clean specificity, while no intervention tried there installs abstention on
  true unknowns. Section 6 states that conclusion and what it licenses; the
  actuation program itself is the companion paper's subject.
- Training resistance and a localizing dissociation (Section 7). The stated-
  confidence gap survives DPO, KTO, GRPO v1/v2/v3, and contrastive SFT. A clean
  dissociation between answer-supervised and answer-masked contrastive SFT shows
  the calibration signal contrastive SFT installs is carried by supervising the
  wrong answer itself: keep it and behavior breaks; remove it and calibration
  breaks.

Two follow-on cells then close off the obvious repairs from both sides. Reinforcement
learning on the calibrated (answer-supervised) base retains stated calibration but
cannot install knowledge-conditioned action ("says but doesn't act"), and the result
survives halving the KL anchor: the decoupling is structural, not an anchor
artifact. Its mirror (distilling the model's own calibrated internal axis
directly into the stated confidence token by SFT) preserves the
knowledge-conditioned action but cannot
install stated calibration: the distilled scalar collapses onto the answer/abstain
action ("acts but doesn't say"). We then argue (Section 8) that two opposite training
pressures failing on the same channel localize the bottleneck to the channel
itself (a single confidence token emitted by the language head and trained by
next-token cross-entropy), and that the productive move is therefore an engine
change: a dedicated
confidence head supervised by a regression loss against the internal axis, not another
objective on the same token.

A scope note before the results: this is a deep within-model mechanistic study of a
single model (Qwen3-4B) at a single seed. We are explicit throughout about which
numbers are robust population reads (n ≈ 3369) and which are directional small-cell
estimates, and Section 9 collects the threats to validity. The claims we stand
behind are qualitative and large in magnitude (0.997 vs 0.52; the
answer-supervised → answer-masked direction flip); the claims we flag are the
precise effect sizes.

## 2. Related work and positioning

### The coherence axis

The taxonomy paper
([*The Depths of Ignorance*](../paper-1-taxonomy-framework/manuscript.md)) introduces
a "Depths of Ignorance" taxonomy (L1 calibration, L2 structured ignorance, L3
distributional signatures, L4 objective uncertainty) and a cross-cutting
coherence/faithfulness axis, and documents that
the training literature clusters at L1 and almost never measures coherence. The
first systematic framework for "faithful calibration" finds that token-probability,
hidden-state, and sampled-consistency estimators of internal confidence diverge on
the same traces [arXiv:2606.03969], and multiple groups find that more inference-
time reasoning impairs calibration rather than helping [arXiv:2508.15050,
arXiv:2506.18183]. This paper is the empirical instantiation of the coherence
axis of [*The Depths of Ignorance*](../paper-1-taxonomy-framework/manuscript.md) on
one model: we measure stated vs internal directly and ask whether training
couples them.

### Latent knowledge and probing

A line of work shows that a model's hidden states
linearly encode whether it is being truthful or whether it knows an answer
[arXiv:2304.13734, arXiv:2212.03827, arXiv:2310.06824, arXiv:2207.05221], with
theoretical grounding for why such directions are linear [arXiv:2403.03867] and
evidence that truth directions generalize across tasks [arXiv:2407.08582]; a
mechanistic literature localizes factual recall itself to identifiable components
[arXiv:2202.05262, arXiv:2104.08696, arXiv:2309.08600]. Two findings are directly
concurrent with ours: a linear probe reads answerability even while the output
hallucinates [arXiv:2310.11877], and internal truthfulness readouts exceed what
outputs express [arXiv:2410.02707]; a complementary result shows fine-tuning
*suppresses* rather than destroys the boundary-tracking structure
[arXiv:2511.12991]. Our internal axis is in this family (a logistic probe on
residual activations). Our question is downstream of probing: granting that the
knowledge is decodable, *why does the model not say it*, and can training make it
say it? The training-resistance depth (seven objectives on one model, with refit
probes held fixed) is the part this literature has not measured.

### Activation steering

Inference-time intervention along a learned direction can
change model behavior [arXiv:2306.03341, arXiv:2308.10248, arXiv:2312.06681], and
humility-adjacent behaviors such as
sycophancy live in steerable internal subspaces [arXiv:2604.03147]. Closest to our
result, refusal itself is mediated by a single causally steerable direction
[arXiv:2406.11717] (though single-direction framings deserve caution
[arXiv:2602.02132], and intervention conclusions are sensitive to methodological
choices [arXiv:2309.16042]). The program uses steering as a causal probe of our
two-axis decomposition in the companion actuation paper; Section 6 imports its
conclusion, a clean asymmetry that, to our knowledge, has not been isolated for
the abstention behavior specifically.

### Abstention and preference training

The program's training-regimen
experiment
([*Teaching Small Language Models to Say I Don't Know*](../paper-2-training-regimen/manuscript.md))
establishes, on the same model and data, that cold-start SFT induces abstention
(and over-refusal), and that DPO and KTO reposition the abstention boundary
rather than inducing the behavior. The broader literature agrees that training moves
*abstention behavior*: IDK-labeled fine-tuning and honesty alignment install
refusal (with over-refusal as the standard side effect) [arXiv:2312.07000,
arXiv:2401.13275, arXiv:2603.17504], while reasoning-focused post-training
degrades it [arXiv:2506.09038]; surveys catalogue the design space
[arXiv:2407.18418]. A separate line trains models to *verbalize* confidence
[arXiv:2205.14334, arXiv:2306.13063, arXiv:2405.20974, arXiv:2405.21028,
arXiv:2406.08391], typically reporting improved calibration on the trained
distribution without testing whether the emitted scalar tracks the model's
internal state (the coherence question this paper measures). Two newer RL
variants sharpen the contrast: Rewarding Doubt optimizes a logarithmic scoring
rule for direct confidence expression [arXiv:2503.02623], while RLMF uses
metacognitive self-judgment to improve faithful uncertainty expression over
standard RL [arXiv:2606.32032]. We treat these as positive controls for what
output-policy training can move, not as evidence that the emitted channel is
coupled to a hidden-state answerability or correctness signal. Consistent with our
RL nulls, ternary abstention rewards under GRPO also fail to couple abstention to
confidence [arXiv:2511.11500], and there are structural reasons to expect the
output channel to resist: calibrated models must hallucinate at a floor set by
their miscalibration [arXiv:2311.14648], alignment stages degrade calibration
[arXiv:2311.13240], and fine-tuning perturbs overlapping representations rather
than writing new signal [arXiv:2604.15574].
This paper builds on
[*Teaching Small Language Models to Say I Don't Know*](../paper-2-training-regimen/manuscript.md)
by asking what happens to the *confidence* channel under those and further
objectives, and by adding the GRPO and contrastive-SFT cells.

## 3. Setup

### Model and data

All experiments use `unsloth/Qwen3-4B-bnb-4bit` with LoRA
adapters (r = 32, α = 64, dropout = 0.05, all-linear targets). Training data for the
abstention/confidence cells is built from TriviaQA-RC (no-context)
[arXiv:1705.03551] following the
Cheng recipe (reusing the data-construction recipe, not released labels). The
out-of-distribution evaluation is SelfAware [arXiv:2305.18153] (n = 3369; 1032
unknown-labeled, 2337
known-labeled), scored with the locked-training-regimen eval harness. Probe and geometry work
uses hidden-state extractions from the merged models, best layer L35 unless
noted (Appendix A pins the harness, extraction, and artifacts).

### Three readouts on the same questions

- *Internal confidence (known-unknown axis).* A logistic probe fit on residual-stream
  activations to separate known-answerable from unknown questions, read at the
  generation position. Reported as known/unknown AUROC and as the calibration (ECE)
  of a 1-D readout along the axis.
- *Stated confidence.* The model is prompted to return JSON with an `answer` and a
  `response_confidence` ∈ [0,1] (its stated probability that its response is
  appropriate). We read the emitted scalar directly from scored rows.
- *Behavior.* Whether the model answered or abstained, and whether the answer was
  correct, summarized as truthful_rate, correct_on_known, over_refusal (refusal on
  known), and refusal_recall (refusal on unknown).

### Calibration metrics

For the stated channel we report: AUROC of the emitted
scalar at ranking *response appropriateness* (the headline coherence number), the
standard deviation of the emitted scalar (a collapse detector), expected
calibration error against appropriateness (ECE), and the per-behavior-cell mean of
the emitted scalar (does the model state higher confidence when it is actually
right/appropriate?). For the internal channel we report known/unknown AUROC and the
1-D readout's ECE.

### Scope

Single seed (seed 1), single model. We treat large qualitative contrasts
as the findings and flag precise effect sizes as single-seed estimates (Section 9).

## 4. Result 1: The model represents what it does not know, and does not report it

The headline contrast is between two readouts of the same model on the same
questions.

### The internal readout

The known-unknown-axis probe separates known from unknown questions at
**AUROC ≈ 0.997** at the best layer (L35), and this is a property of the internal
state rather than surface vocabulary: the residual probe beats a lexical baseline
(≈ 0.964) by +0.033. A one-dimensional logistic
readout along the known-unknown axis (fit without correct/wrong leakage, 5-fold CV) is
**near-perfectly calibrated in aggregate, ECE ≈ 0.004**, and its projection is
monotone across behavior cells (correct > wrong > refused > unknown). This monotone
ordering, like the answerability identity below, is a single-model/single-population
reading (Qwen3-4B, SelfAware); a methodologically parallel evidence-responsiveness
test on a different Qwen lineage and a different error class (confident wrongness on
answerable, world-known questions, rather than KUQ ignorance) found the analogous
KUQ-fit direction's projection reverses in sign instead of ordering monotonically
there, and a constructive search for a portable evidence-responsive axis on that
population recovered only generic retrieval-family geometry, not a specific evidence
axis, so this ordering should not be assumed to transfer before it is tested directly
(`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`, Outcome;
`experiments/evidence-response-direction-search/AMENDMENT.md`, Outcome).

### The stated readout

The same model's emitted `response_confidence` is collapsed near a
constant (on the held-in known set, mean ≈ 0.821 with std ≈ 0.015) and ranks its
own correct vs wrong answers at **AUROC ≈ 0.559 with ECE ≈ 0.142**. On the full SelfAware evaluation the trained models' emitted scalar
ranks appropriateness at **AUROC ≈ 0.52–0.56** (Section 7). Per behavior
cell the emitted number is nearly flat (≈ 0.81 whether the model was right, wrong,
or refused), whereas the internal projection is monotone.

So the discriminating signal exists internally and the verbalized number is a
collapsed near-constant. The model *knows* but does not *say*.

![[figures/fig-p2-01-internal-vs-stated-gap.png]]

**Figure 1. The internal–stated confidence gap.** Two readouts of the same model
on the same SelfAware questions (n=3369). *Left:* the internal known-unknown-axis probe
(L35) separates known from unknown questions at AUROC ≈ 0.997, while the emitted
`response_confidence` scalar ranks appropriateness barely above chance
(AUROC ≈ 0.52). *Right:* the internal axis is near-perfectly calibrated
(ECE ≈ 0.004) where the stated scalar is badly miscalibrated (ECE ≈ 0.142). The
discriminating signal exists internally; the verbalized number is a collapsed
near-constant.

### The gap is like-for-like, not a scoring artifact

A skeptic could object
that Figure 1 scores the two channels against different labels (the probe
against known/unknown, the stated scalar against appropriateness). On the
deployed GRPO-trained checkpoint (Section 7, intervention 4), both channels can
be scored against the *same* known/unknown label on the *same* joined rows
(n = 1233): the L35 probe reads the boundary at AUROC 0.972 while the same
checkpoint's own emitted confidence reads it at 0.637. The
calibration side of the contrast is equally stark: a linear readout along the
internal axis is near-calibrated (ECE ≈ 0.004, above), while the emitted
channel's ECE against appropriateness on the full evaluation is 0.403. The
emitted scalar does carry *some* boundary information when scored against the
label it is best at (0.637 > chance): the gap is not that the stated channel
is empty, but that it says a fraction of what the states contain.

![[figures/fig-p1-09-knows-vs-says.png]]

**Figure 2. The model knows more than it says: like-for-like on one
checkpoint.** On the same GRPO-trained checkpoint and the same evaluation rows,
a held-out linear probe of layer-35 hidden states reads the known/unknown
boundary at AUROC 0.972 while the model's own emitted confidence reads it at
0.637. The knowledge is in there; training never wired it to the output.

### The gap is not internal confusion

A natural objection is that the model
over-refuses items it is genuinely unsure of. It does not: the known-but-refused
items sit at an internal "known" position. On the 0 (known) to 1 (unknown)
known-unknown scale, known-answered items sit at ≈ 0.001 and unknown-refused at ≈ 0.999, while
known-*refused* items sit at ≈ 0.25–0.28, far from the unknown pole. Over-refusal is a behavioral-threshold
phenomenon over items the model internally recognizes as known, not suppression of
a genuine internal "I don't know."

### The internal signal survives training

Re-fitting the probe on each fine-tuned
model's own activations gives essentially identical separation: clean SFT 0.9968,
SFT→GRPO-DPO 0.9972, SFT→GRPO-v2 0.9971, all vs base 0.997. Training does not damage or move the internal
representation; it leaves the gap intact.

### The known-unknown axis is the answerability readout, and it predates our training

One
identity, stated explicitly so the research program does not count a single signal
twice: the known-unknown axis is the same known-versus-unknown separation that the
two-signal readout paper
([*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md))
deploys as its answerability gate, read here as graded confidence rather than as a
binary gate. And the separation is not something our training created. The same
known/unknown probe reads at 0.997 untrained on the raw Qwen3-4B base (no
instruction tuning, no adapter) and at 0.997 or higher on four pretrain-only base
models spanning families and eras, a registered pretraining-origin test whose
falsifier fired on none of the four bases (Appendix A). We fit the axis on trained
checkpoints because that is where this paper's questions live; the signal itself is
a pretraining-origin property.

## 5. Result 2: The internal signal is two axes, a graded known-unknown axis and a separable caution gate

Reading "how known is this item" and "did the model refuse" as one axis would be
the parsimonious story, and the first measurement appears to support it: the raw
mass-mean cosine between the caution direction (refuse vs answer among knowns) and
the knowledge/known-unknown direction is **−0.83**, i.e. nearly collinear, opposite sign.
Under that reading,
refusal is simply the low-known tail of a single graded known-unknown axis.

That reading is an artifact of the instrument. Raw cosine in high-dimensional
activation space is dominated by a few shared high-variance dimensions and
overstates collinearity. Whitening the covariance (shrinkage λ = 0.1) drops the
cosine to **−0.61** on the full sample (subsampling to 300/300 for the AUROC
protocol gives −0.56 to −0.61 depending on subsample seed), and the caution
direction retains a substantial component off the known-unknown axis: its **residual
fraction is 0.557** (≈ 55.7% of the caution direction's length, ≈ 31% of its
variance, is known-unknown-orthogonal; subsample-invariant). Full cells for the geometry
are 168 known-refused, 373 known-answered, and 676 unknown-refused, with the two
large cells subsampled to 300/300 for the AUROC protocol; the covariance is
pooled within-class and shrinkage-whitened; all discriminability numbers are
5-fold held-out.

The decisive test is held-out discriminability after orthogonalization. Predicting
refuse (1) vs answer (0) among known items:

| direction | held-out refuse/answer AUROC, mean (range over 4 fold seeds) |
|---|---|
| knowledge/known-unknown axis alone | 0.866 (0.861–0.872) (strong: refuse = less-known) |
| caution orthogonalized to the known-unknown axis (`caution_perp`) | **0.798 (0.788–0.826)** |
| full caution | 0.885 (0.881–0.892) |

Removing the *entire* rank-1 known-unknown direction barely dents refuse/answer
separability (0.885 → 0.798, means over fold seeds), so the refuse/answer decision
is not confined to the known-unknown axis: a genuine caution-specific gate exists (an
independent reconstruction reproduces the pipeline and supplies the fold-seed
spread). The two are correlated
(both are elevated on the low-known tail) but separable.

### Method lesson

Raw cosine said "one axis" (−0.83); held-out discriminability
after orthogonalization says "two axes." The reliable instrument for "is direction
B reducible to direction A" is not cosine but whether B still discriminates its
target after A is projected out. Stronger whitening monotonically pushes the cosine
−0.83 → −0.61 → toward 0, re-validating an independent near-orthogonality estimate
(≈ 0.02) from a separate analysis. The stronger reducibility test, certified
linear erasure of the full answerability concept (LEACE), confirms this: erasing
everything a linear probe can use to read known/unknown (probe AUROC 0.996 to
0.496 post-erasure) costs the caution readout 5.4 ± 0.6 points of 91, leaving
refuse/answer discrimination at 0.858 held-out. Caution's linear separability is not carried
by the knowledge readout, which contributes only a small quantified share.

### The caution axis is shared across training regimens

The caution direction
recovered independently from SFT, GRPO-DPO, and GRPO-v2 models points the same way
(mean cross-regimen |cos| = 0.701 vs a random floor of 0.014; GRPO-DPO ↔ GRPO-v2 =
0.857) and is approximately orthogonal to the knowledge axis within each model
(|cos| ≈ 0.04–0.09). Caution is a single,
stable, knowledge-orthogonal internal mechanism, not an artifact of one training
run. Each of those readings is fit on its own checkpoint's activations; no single
common checkpoint carries all of them.

### Caution is a trained-checkpoint construct, and cannot be anything else

The
caution direction is defined by a refuse-versus-answer contrast among items the
model knows, and that contrast only exists once a model over-refuses. The raw base
never does: on the 1,233-question known/unknown surface of the base-model readout,
it refused zero questions, so there is no base-model caution direction to fit, for
this model or for any model that never abstains (Appendix A). The asymmetry
between the two axes is therefore itself a finding about what abstention training
adds. Training does not create the known-unknown axis (the answerability separation is already at
ceiling in the raw base and in pretrain-only bases, Section 4); it does create
caution. Every caution number in this paper is a property of the trained,
post-abstention checkpoints, and we make no base-model claim for the caution gate.

The program has also examined a third candidate direction, a
confabulation-propensity read (which unanswerable items draw a fabricated answer
rather than a refusal, residualized against caution). It is checkpoint-specific to
the program's most-trained checkpoint and is examined in the companion actuation
paper ([*Readable Is Not Writable*](../paper-5-actuation/manuscript.md)), where
writing along it does not causally convert confabulations into refusals; we
therefore do not include it among this paper's internal-confidence signals.

## 6. Result 3: The caution gate is causally real, and the leverage is one-way

The two-axis decomposition makes a causal prediction: intervening on the caution
gate should change the refuse/answer decision without changing what the model
knows. Testing that prediction by steering is actuation work, and it belongs to
the companion actuation paper
([*Readable Is Not Writable*](../paper-5-actuation/manuscript.md)), which
establishes the result this paper's argument needs: ablating the caution direction
collapses over-refusal on known items from 0.994 to 0.030 with clean specificity,
the known-unknown-orthogonalized component alone carries a large share of that effect, and
no intervention tried there (including steering the knowledge axis directly)
installs appropriate abstention on genuine unknowns. The leverage is one-way:
excess caution can be relaxed; missing caution cannot be written in.

Two consequences carry forward here. The causal dissociation confirms that the
caution gate is a mechanism of its own and not a re-reading of the known-unknown axis, closing
Section 5's reading-side case from the intervention side. And the asymmetry frames
Section 7: if inference-time control can relax over-caution but cannot install the
abstention humility actually needs on novel unknowns, the remaining lever is
training, and Section 7 reports what training does and does not deliver.

## 7. Result 4: Training does not close the stated-confidence gap, and a dissociation shows why

If behavior is steerable and the internal signal is calibrated, the open question is
whether *training* can make the model's *stated* confidence track appropriateness.
We ran seven interventions. None closes the gap, and the last two close it from
opposite sides in a way that localizes the mechanism.

### The seven interventions

#### Interventions 1–2: DPO and KTO

The training-regimen
paper ([*Teaching Small Language Models to Say I Don't Know*](../paper-2-training-regimen/manuscript.md))
shows that DPO [arXiv:2305.18290] and KTO [arXiv:2402.01306] reposition the abstention boundary rather than inducing abstention;
on the confidence channel the emitted scalar remains a flat high value across
outcome cells (e.g. known-wrong ≈ 0.83): repositioned behavior, unchanged
stated confidence.

#### Interventions 3–4: GRPO v1 and v2

Reward shaping over the behavior (GRPO [arXiv:2402.03300]) leaves the stated scalar
collapsed: on the full evaluation GRPO-v2 emits mean ≈ 0.813 with std ≈ 0.013
(a near-constant ~0.8 regardless of input), ranks appropriateness at
AUROC ≈ 0.520 with ECE ≈ 0.403, and ranks its own correct vs wrong among
answered knowns at AUROC ≈ 0.521 (chance). The diagnosis is an
incentive analysis, and it generalizes beyond this particular reward. The
reward's confidence term shaped confidence toward fixed per-cell targets (high
when answering correctly, low when wrong), but the model cannot observe its own
correctness at generation time, and on the held-in distribution it is trained
against, roughly 96% of its answered known rows are correct (373/388 in the
behavior subset of the same artifact); emitting the majority-cell constant is
therefore reward-optimal. Collapse is not a training accident. It is the
optimum of the objective as specified.

#### Intervention 5: GRPO v3, proper scoring

If the fixed-target confidence term makes a
constant reward-optimal, the obvious repair (and the one the verifiable-RL
literature reaches for [arXiv:2507.16806, arXiv:2503.02623]) is to make
calibration itself the optimum: replace the fixed targets with a Brier proper score of emitted
confidence against realized appropriateness,

$$r_{\text{conf}} = 1 - (c - a)^2, \qquad c \in [0, 1],\; a \in \{0, 1\},$$

where $c$ is the emitted confidence and $a$ is the realized appropriateness of
the completion. The expected reward $\mathbb{E}[r_{\text{conf}}]$ is uniquely
maximized at $c = p(a = 1 \mid x)$: emitting the true probability of being
appropriate is not merely encouraged but is the optimum, so a near-constant is
provably sub-optimal. v3 adds exactly this term; by design it is sub-dominant
to the behavior reward (confidence
weight 1.2, explicitly kept below the behavior magnitudes so behavior is not traded
away). Importantly, the
failure here is not a degenerate target: a CPU preflight re-scoring 19,904 real
rollouts confirmed the per-prompt targets have real dynamic range (group-target
std 0.320 over 4211 prompts, 65.6% in [0.2,0.8]) and that emitting the calibrated
target strictly beats a flat 0.82 on 4211/4211 prompts (mean Brier gain +0.394).
Yet after training,
behavior is fine (truthful 40.99, correct_on_known 52.52, over_refusal 65.13,
refusal_recall 92.34) while the stated scalar stays high and flat (mean ≈ 0.849,
std ≈ 0.027) and still ranks appropriateness at AUROC ≈ 0.522 with ECE 0.440.
A proper score with verified
per-prompt dynamic range, kept sub-dominant to the behavior reward to preserve
behavior, still does not move the three-token confidence readout: the
proper-scoring optimum exists in theory, but gradient ascent from a collapsed
initialization does not find it: the policy stays in the constant-confidence
basin, and the behavior terms it is also earning give it no reason to leave.
This is the cleanest form of the negative result: **even a reward for which
calibrated confidence is the mathematical optimum fails to elicit it through RL
from this initialization.**

#### Interventions 6–7: contrastive SFT, answer-supervised and answer-masked

These two variants are the
dissociation, treated in full below.

### The answer-supervision dissociation (the localizing result)

Contrastive SFT
supervises matched high-confidence appropriate completions and low-confidence
inappropriate completions. The *answer-supervised* variant supervises the entire
assistant turn on inappropriate rows, including the wrong-answer text. The
*answer-masked* variant is identical except a generic per-row sub-span loss mask
removes the wrong-answer text from the loss, so inappropriate rows supervise only the
low confidence, not the wrong answer. This is a clean single-variable comparison: the
only difference is whether the wrong answer is in the loss.

Table 1. The answer-supervision dissociation (SelfAware, n = 3369; gates fixed
in the pre-registered design).

| metric | gate | clean-SFT base | **answer-supervised** | **answer-masked** |
|---|---|---|---|---|
| emitted AUROC → appropriateness | ≥ 0.62 | ≈ 0.52 | **0.684 ✓** | **0.552 ✗** |
| emitted std (collapse detector) | ≥ 0.10 | ≈ 0.05 | 0.309 | 0.180 |
| ECE → appropriateness | < 0.30 | 0.40–0.44 | 0.183 | 0.277 |
| known_correct mean > known_wrong mean | (none) | fails | 0.670 > 0.306 ✓ | 0.756 > 0.742 ✓ (barely) |
| unknown_refused mean > unknown_wrong mean | (none) | fails | 0.581 > 0.156 ✓ | **0.666 < 0.696 ✗ (inverted)** |
| truthful_pct | ≥ 35.6 | 40.58 | **30.93 ✗** | **41.59 ✓** |
| correct_on_known_pct | ≥ 42.2 | 47.23 | **36.63 ✗** | **50.06 ✓** |
| over_refusal_pct | ≤ 67.5 | 57.51 | **79.2 ✗** | **62.73 ✓** |
| refusal_recall_pct | ≥ 82.0 | 87.02 | 83.72 ✓ | 93.51 ✓ |


The answer-supervised variant installs stated calibration (AUROC 0.684, large cell
separations, the only arm to beat chance at ranking correct vs wrong among answered
knowns at AUROC 0.789) but breaks behavior (over-refuses, correctness falls). The
answer-masked variant recovers behavior fully (it matches or exceeds the
clean-SFT base on every behavior metric) but the stated calibration collapses
back toward
baseline (AUROC 0.552; the unknown cell-mean ordering inverts, the model stating
*higher* confidence when it answers an unknown wrong, 0.696, than when it correctly
refuses, 0.666). Note that the answer-masked variant is not collapsed to a constant
(std 0.180 ≫ base 0.05): it emits *spread* confidence that does not *discriminate*.
Variance is not calibration.

### Mechanistic reading

The wrong-answer supervision carried the
stated calibration, not merely a behavior-breaking side effect. When the
answer-supervised variant supervises "{wrong answer} + low confidence" jointly, the
low-confidence token is bound to the act of producing that (wrong) answer, and that
binding is what makes the stated scalar track appropriateness. Remove the answer from
the loss (the answer-masked variant) and behavior heals, but the confidence token
loses the thing it was conditioned on, so discrimination returns to baseline. Under a
single SFT lever, stated calibration and behavior are in tension: you can buy one or
the other, not both. This is why we report the answer-masked variant as a successful
behavior cell and a failed calibration cell rather than a success: calibration over
sycophancy.

![[figures/fig-p2-02-answer-supervision-dissociation.png]]

**Figure 3. The answer-supervision dissociation: a single SFT lever cannot buy
calibration and behavior together.** *Left:* the calibration–behavior trade-off.
Each arm is one point: x = stated calibration (emitted AUROC → appropriateness,
gate 0.62), y = behavior (truthful %, gate 35.6). The answer-supervised variant
sits bottom-right (good calibration, broken behavior); the answer-masked variant
sits top-left (good behavior, calibration back at baseline); base is bad on both.
The quadrant lines are the protocol gates; no arm reaches the pass quadrant
(top-right). *Right:* the four behavior metrics by arm, showing the answer-supervised
over-refusal spike and correctness drop that masking the answer recovers. Data:
Table 1.

### The SFT→RL follow-on: a second dissociation, confidence vs action

The
answer-supervision result says a single SFT lever cannot buy calibration and
behavior together. The obvious next move is a *division of labour*: keep the
answer-supervised calibration and repair its behavior with reinforcement learning,
which is built for behavior shaping. We ran GRPO v3 (the same proper-scoring reward
as intervention 5) on the answer-supervised base rather than the clean-SFT base, so
that the KL anchor now references a *calibrated* policy and the dominant behavior
reward attacks its over-refusal. This is an
exploratory single-seed cell, reported separately from the locked matrix.

The calibration half of the bet pays: training on the answer-supervised base *retains* stated
calibration even as the policy moves well off its reference (final KL ≈ 0.97).
The emitted scalar keeps AUROC → appropriateness 0.646, std 0.311, ECE 0.214, and
the full cell ordering, including the very ordering the answer-masked variant
inverted: unknown-refused (0.542) > unknown-answered-wrong (0.138). RL on a calibrated base preserves
calibration where RL on the flat base (intervention 5) could not manufacture it;
the base, not the reward, was the binding constraint for the confidence channel.
This is the first direct evidence in this study that RL does not intrinsically
*destroy* a calibrated stated-confidence channel: it fails only to create one.

![[figures/fig-p2-03-answer-supervised-cell-confidence.png]]

**Figure 4. GRPO on the answer-supervised base retains stated calibration: the
emitted scalar tracks outcome.** Mean emitted `response_confidence` per behavior
cell (greedy). The full ordering is preserved (high for known-correct, low for
unknown-wrong), including the exact ordering the answer-masked variant inverted:
unknown-refused (0.54, an appropriate abstention) sits *above* unknown-wrong (0.14,
a confident error). RL on a calibrated base preserves the confidence channel that
RL on the flat base could not manufacture.

But behavior does not repair, and *why* it does not is the result. Over-refusal
gets *worse*, not better (90.76%, vs the answer-supervised arm's 79.2%; truthful 31.9, below the 35.6
gate). Decomposing the answer/abstain decision from the confidence scalar (Table
2) shows the two channels have come apart. The confidence channel discriminates:
among refusals, the stated scalar separates a correct refusal (an unknown) from a
mistaken one (a known the model should have answered) at AUROC 0.62, and among
answers it separates correct from wrong at AUROC 0.84. The *action* channel barely
conditions on knowledge at all: the model answers knowns only 2.85 points more
often than unknowns (9.2% vs 6.4%; p = 0.006, statistically real but practically
negligible). The decision is ~97% a single knowledge-independent propensity and
~3% knowledge.

Table 2. GRPO-v3 on the answer-supervised base: calibrated confidence,
uncalibrated action (SelfAware, n = 3369; greedy unless noted).

| channel | measurement | value |
|---|---|---|
| confidence | refusal-appropriateness AUROC (unknown-refused vs known-refused) | **0.62** |
| confidence | answer-correctness AUROC (correct vs wrong, among answers) | **0.84** |
| action | answer-rate margin, P(answer\|known) − P(answer\|unknown) | **+2.85 pts** (p = 0.006) |
| action | same margin at temperature 1.35 (training temperature) | +6.5 pts |
| action | same margin over training (1861 steps, binned) | +2.5 → ~+7 pts, never opens |
| action | same margin, lower-KL re-run (β 0.05, greedy); pre-reg. falsifier ≥ ~14.5 | **+3.02 pts** (p = 0.004), falsifier fired → structural |

![[figures/fig-p2-04-confidence-vs-action.png]]

**Figure 5. Calibrated confidence, uncalibrated action.** The two channels of the
policy from GRPO on the answer-supervised base have come apart. *Left:* the confidence channel discriminates:
the emitted scalar separates appropriate from mistaken refusals (AUROC 0.62) and
correct from wrong answers (AUROC 0.84), both above chance. *Right:* the action
channel barely conditions on knowledge: the answer-rate margin between knowns and
unknowns is only +2.85 pts greedy and +6.5 pts at the training temperature 1.35.
The decision is ~97% a single knowledge-independent propensity. "Knows but doesn't
say" becomes "says but doesn't act."

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

![[figures/fig-p2-05-action-margin-trajectory.png]]

**Figure 6. The action margin never opens during training.** Answer rate for
known vs unknown rollouts (temperature 1.35) binned across the 1861-step run of
GRPO on the answer-supervised base. Both bands drift down together as the global answer rate falls; the knowledge
margin between them (shaded) stays at ≈ +5–8 points throughout and never widens.
A policy that passes the behavior gate would need the margin to open to ≈ +14.5
points and the bands to separate; neither happens. The reward differential
between refusing a known and refusing an unknown moved the *global* propensity,
not the knowledge conditioning.

The reading extends this paper's thesis by one layer. The model knows internally
(Section 4) and, after answer-supervised SFT, *says* it: the confidence scalar tracks
knowledge. But it does not *act* on it: the answer/abstain decision is decoupled
from the very signal the model is now able to verbalize. "Knows but doesn't say"
becomes, here, "says but doesn't act." Whether this last gap is structural or an
artifact of the KL anchor pinning the action to the answer-supervised over-refusing mode is a
question we pre-registered a falsifier for and then tested with a lower-KL
(β 0.05) re-run: the action margin must open to ≥ ~14.5 points (the separation
the behavior gate implies) or we record the decoupling as structural.

### The falsifier fired: the decoupling is structural

Halving the KL anchor
(β 0.1 → 0.05) demonstrably loosened the policy: train-time KL roughly doubled
(≈ 0.97 → ≈ 1.91), so the policy moved markedly further from the
answer-supervised base. Yet the greedy eval is a near-exact overlay of the β 0.1 run: truthful 31.9%
(unchanged), over-refusal 90.59% (vs 90.76%), and the confidence channel still
calibrated (AUROC 0.648 vs 0.646, ECE 0.212 vs 0.214, cells ordered). The action margin moved by **0.17
points**, from +2.85 to **+3.02 pts** (z = 2.90, p = 0.004), against the ~14.5
it would need to clear the behavior gate, and the training-trajectory margin
stayed in
the same +5–9 pt band throughout, never trending toward opening. The β knob was the
one lever that could have explained the action decoupling as a KL artifact; it moved
the policy and did not move the conditioning. We therefore record "says but doesn't
act" as a **structural** property of the objective-and-decode, not of the KL anchor.
The implication is the experiment Section 8 sets out: the action and the stated
scalar must be supervised against the model's own internal known-unknown axis directly,
which no outcome or preference reward does. Tuning the RL knob is closed.

### Where this leaves confidence training

Across the five confidence-channel
arms so far (GRPO-v2, proper-scoring GRPO, the two contrastive variants, and
RL on the answer-supervised base), no combination produced a checkpoint that
both behaves well and states calibrated confidence, and the pattern is
internally consistent: supervision can install a calibrated channel
(the answer-supervised variant), RL preserves an installed channel (the
follow-on above), RL cannot install one (interventions 3–5), and behavior and
stated confidence move on separate channels throughout. The stated channel is
never coupled to the epistemic state in the first place unless supervision
explicitly constructs the coupling, and the one supervision that constructs it
does so by a binding (the wrong-answer text) that breaks behavior.
This is a local claim about coupling in this model and channel: it does not deny
that RLMF-style objectives can improve faithful uncertainty metrics, but it says
that output-level improvement is not yet the same thing as wiring the model's
internal signal to both action and stated confidence.

![[figures/fig-p1-08-confidence-channel.png]]

**Figure 7. The confidence channel and behavior fail in opposite arms.**
Emitted-confidence spread (left), calibration against response appropriateness
(center), and over-refusal (right) for the five confidence-channel arms
(seed 1, exploratory). The RL arms (red) sit below the collapse gate and at
chance calibration with moderate over-refusal; the contrastive arms (green)
calibrate the channel at behavioral cost; RL on the answer-supervised base
(purple) keeps the calibration and worsens the behavior. No arm gets both halves
right.

### The SFT-distillation mirror: a third dissociation, action vs stated confidence

The RL follow-on gives "says but doesn't act." Its mirror is the obvious
SFT route to the same goal from the other side: instead of installing the scalar
and repairing behavior, *preserve* the clean-SFT behavior and install the scalar by
distilling the model's own calibrated internal axis into it directly. We supervised
the stated `response_confidence` on clean-SFT data with a scalar-only loss whose
target is the probe's factual confidence $P(\text{answer correct})$ per row
(AUROC ≈ 0.997 internally), clamped to $[0.02, 0.98]$; no balancing, no abstention
inversion. The assistant *answer* text is byte-identical to clean SFT, so the
knowledge-conditioned action is preserved by construction; only the confidence token
is retargeted. This too
is an exploratory single-seed cell, reported separately from the locked matrix, with
the gate pre-registered: success = emitted AUROC → correctness ≥ 0.70, falsifier
< 0.60.

The behavior half holds trivially and the calibration half fails: the falsifier
fired (Table 3). Because the answer text is untouched, the action channel conditions
on knowledge *strongly*: the answer-rate margin is **+31.2 pts** (known 37.7% vs
unknown 6.5%; z = 18.6), the widest in this paper and a full behavior pass 4/4. But
the distilled scalar did not learn correctness. It collapsed onto the **action**:
across 3369 rows it emits essentially two values (0.9706 whenever it answers,
0.0294 whenever it abstains) regardless of whether the answer is right. Ranking answered
knowns correct-vs-wrong gives AUROC 0.504 (means 0.9706 vs 0.9651); refusal
appropriateness 0.501; emitted → appropriateness 0.526; ECE 0.408. The emitted std
is large (0.42) precisely *because* it splits on the answer/abstain action, not
because it discriminates correctness: the same "variance is not calibration" caution
as the answer-masked variant, in its sharpest form. A scalar-only SFT loss with a
genuinely calibrated, per-row-varying target (the source axis ranks correctness at
AUROC 0.997) still installs only a re-description of the action the model already
takes, not the correctness the target encodes.

Table 3. Probe-axis distillation: distilling the calibrated internal axis into
the stated scalar by SFT (SelfAware, n = 3369; greedy).

| channel | measurement | value |
|---|---|---|
| action | answer-rate margin, P(answer\|known) − P(answer\|unknown) | **+31.2 pts** (z = 18.6); behavior 4/4 ✓ |
| confidence | emitted AUROC → correctness (pre-reg. success ≥ 0.70, falsifier < 0.60) | **0.504**; falsifier fired ✗ |
| confidence | distinct emitted values across 3369 rows | **3** (0.9706 answer / 0.0294 abstain, correctness-blind) |
| confidence | ECE → appropriateness | 0.408 |

### The symmetry, and what it localizes

The two follow-ons are mirror images.
RL on the calibrated base keeps the *stated* calibration and cannot
install knowledge-conditioned *action*: "says but doesn't act." SFT distillation
into the scalar keeps the knowledge-conditioned *action* and cannot
install *stated* calibration: "acts but doesn't say." Neither the RL route nor the
scalar-SFT route succeeds in routing the calibrated internal known-unknown axis (AUROC 0.997)
into the verbalized single-token confidence readout. That the same channel resists
two opposite training pressures (an outcome-aligned proper-scoring reward and a
direct distillation of the very axis that is calibrated) localizes the bottleneck to
the channel itself: a single confidence token trained by next-token cross-entropy
collapses onto the lowest-entropy correlate available (the answer/abstain action),
not the higher-entropy correctness signal. This is the motivation for Section 8's
engine change: a dedicated confidence head supervised by a regression (proper-score)
loss against the internal axis, rather than a token emitted by the language head.

## 8. Discussion

### Possessed vs performed humility, measured

The taxonomy paper
([*The Depths of Ignorance*](../paper-1-taxonomy-framework/manuscript.md)) framed the
distinction between humility a model possesses (tethered to its internal state)
and humility it merely performs (untethered behavior). Section 4 makes the distinction concrete: the
internal tether exists and is calibrated (ECE 0.004), the performed behavior can be
shaped (Sections 6–7), and the *stated* confidence (the channel a user actually
reads) is tied to neither. The model is, in the precise sense of the *Meno*, giving
true opinions without the tether; our seven interventions are attempts to install
the tether, and they fail.

### Why the stated channel is the stubborn one

The internal axis survives training
untouched (Section 4) and behavior is cheaply steerable (Section 6, established in
the companion actuation paper), yet the stated
scalar resists every objective we tried. The dissociation explains why: outcome and
preference rewards (DPO/KTO/GRPO) move behavior and leave the scalar collapsed
because the scalar is a tiny part of the supervised signal; the one objective that
moved the scalar (contrastive SFT) did so by entangling it with answer text, which
trades behavior. No objective we tried supervises the stated scalar *against the
right target directly*.

### The implied experiment, run and resolved: probe distillation does not route the axis into the scalar

The model already contains a calibrated estimate of
appropriateness: the internal known-unknown axis (ECE 0.004). The natural objective is
therefore not to induce calibration from outcomes, but to *distill the internal axis
into the stated channel*: supervise the emitted `response_confidence` toward the
model's own known-unknown-axis readout, so the model learns to *say* what it already
*represents*. This decouples the confidence target from the answer text (avoiding the
answer-supervised trade) and supplies a dense, per-item, calibrated target (avoiding
GRPO's out-competed confidence term). We ran it (Section 7, Table 3), and it
failed in an informative way. This framing treats the known-unknown axis's
calibrated appropriateness estimate as a stand-in for factual confidence,
$P(\text{answer correct})$; that identification, like the axis's monotonicity in
Section 4, is a single-model/single-population reading on Qwen3-4B/SelfAware, and a
methodologically parallel constructive search for a portable evidence-responsive
axis on a different model and error-class population found only generic
retrieval-family geometry rather than a specific evidence/correctness axis, so the
identification should not be assumed to hold outside this population without a
direct test (`experiments/evidence-response-direction-search/AMENDMENT.md`, Outcome).

The design needed two corrections on the way, both instructive. First, a *naive*
probe-scaled target (response_confidence = 0.1 + 0.8·appropriateness_p) collapses to
a single emitted value (0.8765) because the target *distribution* is imbalanced: most
known items are answerable, so most targets land in a high band, and cross-entropy is
minimized by emitting that mode. The intended fix was to quantile-balance the target onto a spread band so that
emitting a constant is penalized; but a CPU preflight on the real pool showed the
*source* axis it balanced (appropriateness on all-appropriate clean-SFT
completions) is itself near-degenerate (85% of rows at one ceiling value), so balancing fabricates
knowledge-uncorrelated variance. The signed design therefore distills the
probe's factual-correctness axis $P(\text{answer correct})$ *directly*: a genuinely
per-row-varying, internally calibrated target (AUROC 0.997), no balancing.

That target is exactly what the objection above asks for, and the model still did not
learn to say it. With the answer text held byte-identical to clean SFT, behavior
passed 4/4 and the action conditioned on knowledge strongly (+31.2 pts), but the
distilled scalar collapsed onto the *action*: two values, answer↔0.97 / abstain↔0.03,
correctness AUROC 0.504 (Section 7, Table 3). Distilling a calibrated target into the
single confidence token does not install calibration; it installs a re-description of
the answer/abstain decision. Combined with the RL mirror, this is what
moves the conclusion past "we have not yet found the right objective": two opposite
training pressures on the same channel both fail, which points at the *channel*, not
the objective.

### The next experiment: an engine change, not another loss on the same token

If a single confidence token trained by next-token cross-entropy collapses
onto the lowest-entropy correlate available regardless of the target, the remedy is to
stop emitting confidence from the language head: add a dedicated confidence head that
reads the same hidden state the internal axis is fit on and is supervised by a
regression (proper-score) loss against that axis, so the calibrated representation is
routed to the readout directly rather than relayed through a token the LM objective
keeps collapsing. Like all training cells here this requires a new pre-registered protocol
revision and inherits this paper's measurement: success means the stated channel
finally clears both the calibration gate (AUROC → appropriateness ≥ 0.62, with
discrimination, not just spread) and the behavior gate at once, the cell none of the
seven interventions could be.

### Three readings of the gap, in increasing strength

First, as *measurement*:
any evaluation of "does the model know what it knows" that reads only output
channels understates what the model knows, badly: the same checkpoint scores
0.637 or 0.972 on the same rows depending on whether one reads its statements
or its states (Section 4, Figure 2). Second, as *mechanism*: the training arms
decompose as *policy over a fixed epistemic signal*. SFT installs a refusal
routine gated on the signal; preference and reward objectives re-gate the
routine ([*Teaching Small Language Models to Say I Don't Know*](../paper-2-training-regimen/manuscript.md));
none of them touches the signal, which is why the refit
probes are identical across arms (Section 4) while refusal rates move by tens
of points. Third, as *strategy*: the expensive part of epistemic humility (the
internal knowledge-boundary signal) is already paid for by pretraining:
the same answerability readout is present in pretrain-only base weights, before
any instruction tuning or preference training, replicated across four bases
spanning families and eras (Appendix A).
The unsolved part is the *readout*: coupling stated confidence and action to a
signal that is linearly available inside. Training the readout failed here in
seven variants; reading it directly with a probe trivially succeeds. The
two-signal readout paper
([*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md))
pursues that readout line directly (whether a training-free probe readout can
supply the calibrated gate and dial that output training could not) and takes
on the transfer questions (across datasets, model sizes, and families) that
this single-model study leaves open; the standard probing cautions (a probe can
read recall rather than truth-tracking [arXiv:2510.09033]; transfer must be
tested, not assumed)
carry over to it.

### Implications beyond this model

If the pattern generalizes (Section 9 is honest
that we have not shown this), it reframes a common assumption in abstention training:
that teaching better behavior will produce better-calibrated confidence. Here the two
are dissociable, and the confidence channel needs its own, internally-anchored
supervision. It also tempers the "steer in humility at inference" hope: the easy
steering direction (less over-caution) is the opposite of what novel unknowns
require (more caution), and the companion actuation study could not install the
hard direction.

## 9. Limitations

- Single seed, single model. Every number is seed 1 on Qwen3-4B. The large
  qualitative contrasts (0.997 vs 0.52; the answer-supervised →
  answer-masked direction flip) are
  unlikely to be seed noise, but the precise effect sizes are single-seed estimates
  and the whole pattern needs replication across seeds and at least one other model
  family/size before any claim of generality.
- Small wrong-answer cells. Some internal-vs-stated discrimination numbers rest
  on few wrong-answered items (n = 16 on the held-in known set); these are reported
  as directional. The full-eval AUROC numbers (n ≈ 3369) are not affected.
- SelfAware-only OOD surface. Behavior and stated-calibration numbers are on one
  OOD benchmark. Generalization to other known/unknown surfaces is untested.
- Knowledge erasure is linear-only. The stronger reducibility test is now
  done: certified linear erasure (LEACE) of the full answerability concept
  leaves the caution readout at 0.858 held-out (baseline 0.912), with the
  knowledge subspace contributing a small quantified share (5.4 ± 0.6 points
  across 24 fold assignments). The
  remaining caveat is that the erasure certificate is linear: a nonlinear
  probe could still read answerability from the erased states, so the
  independence claim is about linear readouts, matching the linear
  instruments used throughout.
- Probe could read outcome leakage. The internal axis is fit on activations; we
  control for lexical baselines and fit the readout without correct/wrong leakage,
  but probe-based "knowledge" claims always carry the risk that the probe reads a
  correlate. The causal steering results summarized in Section 6 (from the
  companion actuation paper) partly mitigate this for the
  caution axis but not for the known-unknown axis.
- The imported steering evidence is single-site / few-layer. The causal
  results Section 6 summarizes come from the companion actuation paper and rest
  on interventions at a small number of sites and layers, so "cannot install
  caution" is a statement about the interventions tried there, not a proof of
  impossibility.
- The SFT→RL confidence/action result is single-seed and exploratory. The
  GRPO-v3-on-answer-supervised cell (Section 7, Table 2) is one seed of one
  exploratory pre-registered cell, reported separately from the locked matrix; the confidence/action decoupling
  should be read as a lead, not an established claim, until replicated. Its central
  open question (whether the decoupling is structural or an artifact of the KL
  anchor) was settled within the cell by a pre-registered lower-KL (β 0.05) re-run:
  the falsifier (action margin ≥ ~14.5 points), fixed in advance, fired: the margin
  moved only +0.17 pts (to +3.02) while the policy demonstrably loosened, so the
  decoupling is recorded as structural. This resolves the artifact-vs-structural
  question for this single-seed cell but does not lift the single-seed caveat: the
  structural reading itself still wants replication across seeds and a larger model.
- The probe-distillation cell is single-seed and exploratory. The
  probe-distillation result (Section 7, Table 3) is one seed of one exploratory
  pre-registered cell, reported separately from the locked matrix; "acts but doesn't say" and the channel-bottleneck
  reading it supports should be read as a lead, not an established claim, until
  replicated. The pre-registered calibration falsifier (AUROC → correctness < 0.60)
  fired, so the negative is on the record, but the *interpretation* (that the
  collapse is a property of the single-token-via-CE channel rather than of this
  particular target or recipe) is what the proposed confidence-head experiment is
  designed to test, and is not yet established.
- Naming caution from a different lineage. A dedicated naming-earnability test on a
  different model and direction lineage (Qwen3.5-4B, hs20, not this paper's
  Qwen3-4B L35 known-unknown axis) found the mentalistic "doubt" name not earned on
  evidence-responsiveness: the transfer test voided on population reversal (the
  KUQ-fit direction reads reversed on a world-known confident-wrong error class),
  and the natively refit direction passed specificity but failed the
  projection-collapse leg, with the margin channel instrument-void
  (`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`, Outcome).
  A follow-on constructive search for a direction built to maximize the evidence
  contrast fired at baseline but was indistinguishable from covariance-shaped
  random directions and recovered generic retrieval-family geometry rather than a
  specific evidence axis (`experiments/evidence-response-direction-search/AMENDMENT.md`,
  Outcome). Neither result is a direct test of this paper's known-unknown axis;
  they transfer as a naming caution by methodology, not as a falsification of the
  identity or monotonicity claims made here.

## 10. Conclusion

In one small instruction-tuned model, epistemic humility is three things that do not
agree: a calibrated internal estimate of what the model knows, a behavior that a
companion actuation study shows can
be cheaply steered down (but not up) along a separable caution gate, and a stated
confidence number that tracks neither and resists every training objective we tried
to fix it with. The decisive evidence is a single-variable dissociation: contrastive
SFT can install stated calibration only by supervising the wrong-answer text, which
breaks behavior, and masking that text restores behavior while destroying the
calibration. The model knows but does not say, and current objectives move what it
says or what it does without coupling them. Two mirror follow-ons sharpen rather than
close the gap: reinforcement learning on a calibrated base keeps the stated signal but
not knowledge-conditioned action, and distilling the calibrated internal axis directly
into the stated confidence token keeps the action but collapses the scalar onto
it: two opposite pressures, the same channel, the same failure. Because the calibrated
signal already exists inside the model and the obstruction is now localized to the
single-token confidence channel, the route this paper motivates is not another
objective on that token but an engine change: a dedicated confidence head, reading the
hidden state the internal axis is fit on, supervised by a regression loss against it.

## Data and code availability

All training configs, eval configs, reward definitions, probe/geometry/steering
scripts, governed protocol amendments, and per-cell calibration reports are in the
repository [https://github.com/ProfSynapse/Epistemic-Humility-Research] under
`archive/experiment/phase1/`, `docs/protocols/`, and `experiments/<slug>/`. The per-cell stated-confidence
calibration reports are at `archive/experiment/phase1/eval/analysis/calibration_gap_*.json`;
the internal-axis and steering artifacts are under
`archive/experiment/phase1/probe/analysis/`.

Published dataset releases on Hugging Face (the repo-side manifest with pinned
revisions is `docs/public-artifacts.md`):
`professorsynapse/epistemic-humility-phase1` (training/dev data),
`professorsynapse/epistemic-humility-phase1-labels` (frozen question split and
knowledge labels), `professorsynapse/epistemic-humility-phase1-evals` (eval
analysis layer), `professorsynapse/eh-probe-directions` (per-layer probe
directions with fit metadata; replicate the internal-axis readout without GPU
extraction), and `professorsynapse/eh-readout-rows` (per-question
question/answer/grade rows behind the readout results).

Restricted or gitignored datasets (e.g. bridge
sets) are not redistributed. This is draft-v1; numbers are current as of 2026-07-02.

## References

(Compiled 2026-07-04 from the program's knowledge-graph library; every entry
has an ingested note under `library/notes/`. Cited inline as [arXiv:id].)

- Arditi et al. (2024). Refusal in Language Models Is Mediated by a Single Direction. arXiv:2406.11717.
- Azaria et al. (2023). The Internal State of an LLM Knows When It's Lying. arXiv:2304.13734.
- Bani-Harouni et al. (2025). Rewarding Doubt: A Reinforcement Learning Approach to Calibrated Confidence Expression of Large Language Models. arXiv:2503.02623.
- Burns et al. (2022). Discovering Latent Knowledge in Language Models Without Supervision. arXiv:2212.03827.
- Cheang et al. (2025). Do LLMs Really Know What They Don't Know? Internal States Mainly Reflect Knowledge Recall Rather Than Truthfulness. arXiv:2510.09033.
- Cheng et al. (2024). Can AI Assistants Know What They Don't Know?. arXiv:2401.13275.
- Cunningham et al. (2023). Sparse Autoencoders Find Highly Interpretable Features in Language Models. arXiv:2309.08600.
- Dai et al. (2021). Knowledge Neurons in Pretrained Transformers. arXiv:2104.08696.
- Damani et al. (2025). Beyond Binary Rewards: Training LMs to Reason About Their Uncertainty. arXiv:2507.16806.
- Ethayarajh et al. (2024). KTO: Model Alignment as Prospect Theoretic Optimization. arXiv:2402.01306.
- Gani et al. (2026). Quantifying Faithful Confidence Expression in Large Reasoning Models. arXiv:2606.03969.
- Jiang et al. (2024). On the Origins of Linear Representations in Large Language Models. arXiv:2403.03867.
- Joad et al. (2026). There Is More to Refusal in Large Language Models than a Single Direction. arXiv:2602.02132.
- Joshi et al. (2017). TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension. arXiv:1705.03551.
- Kadavath et al. (2022). Language Models (Mostly) Know What They Know. arXiv:2207.05221.
- Kalai and Vempala (2023). Calibrated Language Models Must Hallucinate. arXiv:2311.14648.
- Kaplan et al. (2026). Why Fine-Tuning Encourages Hallucinations and How to Fix It. arXiv:2604.15574.
- Kapoor et al. (2024). Large Language Models Must Be Taught to Know What They Don't Know. arXiv:2406.08391.
- Kirichenko et al. (2025). AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions. arXiv:2506.09038.
- Lacombe et al. (2025). Don't Think Twice! Over-Reasoning Impairs Confidence Calibration. arXiv:2508.15050.
- Li et al. (2023). Inference-Time Intervention: Eliciting Truthful Answers from a Language Model. arXiv:2306.03341.
- Lin et al. (2022). Teaching Models to Express Their Uncertainty in Words. arXiv:2205.14334.
- Liu et al. (2026). Reinforcement Learning with Metacognitive Feedback Elicits Faithful Uncertainty Expression in LLMs. arXiv:2606.32032.
- Liu et al. (2024). On the Universal Truthfulness Hyperplane Inside LLMs. arXiv:2407.08582.
- Marks et al. (2023). The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets. arXiv:2310.06824.
- Mei et al. (2025). Reasoning about Uncertainty: Do Reasoning Models Know When They Don't Know?. arXiv:2506.18183.
- Meng et al. (2022). Locating and Editing Factual Associations in GPT. arXiv:2202.05262.
- Mohamadi et al. (2025). Honesty over Accuracy: Trustworthy Language Models through Reinforced Hesitation. arXiv:2511.11500.
- Orgad et al. (2024). LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations. arXiv:2410.02707.
- Panickssery et al. (2023). Steering Llama 2 via Contrastive Activation Addition. arXiv:2312.06681.
- Rafailov et al. (2023). Direct Preference Optimization: Your Language Model is Secretly a Reward Model. arXiv:2305.18290.
- Rosenbaum (2026). It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models. Companion draft, this repository: [papers/paper-4-two-signal-readout/manuscript.md](../paper-4-two-signal-readout/manuscript.md).
- Rosenbaum (2026). The Depths of Ignorance: A Taxonomy, Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in Language Models. Companion draft, this repository: [papers/paper-1-taxonomy-framework/manuscript.md](../paper-1-taxonomy-framework/manuscript.md).
- Rosenbaum (2026). Teaching Small Language Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data. Companion draft, this repository: [papers/paper-2-training-regimen/manuscript.md](../paper-2-training-regimen/manuscript.md).
- Shao et al. (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300.
- Shi et al. (2025). Fine-Tuned LLMs Know They Don't Know: A Parameter-Efficient Approach to Recovering Honesty. arXiv:2511.12991.
- Slobodkin et al. (2023). The Curious Case of Hallucinatory (Un)answerability: Finding Truths in the Hidden States of Over-Confident Large Language Models. arXiv:2310.11877.
- Stengel-Eskin et al. (2024). LACIE: Listener-Aware Finetuning for Confidence Calibration in Large Language Models. arXiv:2405.21028.
- Sun et al. (2026). Valence-Arousal Subspace in LLMs: Circular Emotion Geometry and Multi-Behavioral Control. arXiv:2604.03147.
- Turner et al. (2023). Steering Language Models With Activation Engineering. arXiv:2308.10248.
- Uluoglakci et al. (2026). Inducing Epistemological Humility in Large Language Models: A Targeted SFT Approach to Reducing Hallucination. arXiv:2603.17504.
- Wen et al. (2024). Know Your Limits: A Survey of Abstention in Large Language Models. arXiv:2407.18418.
- Xiong et al. (2023). Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs. arXiv:2306.13063.
- Xu et al. (2024). SaySelf: Teaching LLMs to Express Confidence with Self-Reflective Rationales. arXiv:2405.20974.
- Yang et al. (2023). Alignment for Honesty. arXiv:2312.07000.
- Yin et al. (2023). Do Large Language Models Know What They Don't Know?. arXiv:2305.18153.
- Zhang et al. (2023). Towards Best Practices of Activation Patching in Language Models: Metrics and Methods. arXiv:2309.16042.
- Zhu et al. (2023). On the Calibration of Large Language Models and Alignment. arXiv:2311.13240.

## Appendix A: Provenance (internal labels to artifacts)

Reader-facing prose above uses no internal amendment labels. For
reproducibility, the mapping from each training-cell claim to its governing
protocol document and scored artifact:

| Paper section | Internal label | Protocol / notes | Primary artifacts |
|---|---|---|---|
| §3 setup (locked eval harness; stated-scalar readout; hidden-state extraction `55254a04aa1f`) | probe program / locked eval harness | `archive/experiment/phase1/eval/run_eval.py`; `archive/experiment/phase1/eval/analysis/calibration_gap_report.py` | `experiments/selfaware-latent-knowledge-controls/artifacts/latent_knowledge_controls/` |
| §4 internal-vs-stated gap; like-for-like on the GRPO-v2 checkpoint (Fig. 2) | probe program (Amendments L/M lineage; caution-vs-known-unknown note); session 20260627T093723Z | `archive/notes/experiments/caution-vs-doubt-knowledge-gate.md`; `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md` checkpoints 002–004 | `experiments/selfaware-latent-knowledge-controls/artifacts/latent_knowledge_controls/` (`a3_h_base_probe.json`, `c2_*.json`, `a1a2_h_lora.json`); `archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json` (`B_internal_vs_emitted`: internal AUROC 0.972 vs emitted 0.637) |
| §5–6 geometry; §6 imported steering summary (companion actuation paper) | probe program | `archive/experiment/phase1/probe/paper3_section5_geometry.py`; independent reconstruction `papers/paper-3-knows-but-doesnt-say/analysis/provenance/p3_section5_provenance_20260704/reconstruct_section5_geometry.py`; `caution_direction_L35.json`; `caution_perp_direction_L35.json`; `caution_axis_transfer.json` | `archive/experiment/phase1/probe/analysis/current_clean_grpo_v2_*` (interventions, coefficient sweeps, generation panels; reported as results of the companion actuation paper) |
| §4 known-unknown-axis origin (raw base 0.997); §5 caution unreadable on base (0 refusals in 1,233) | Amendment W | `experiments/base-model-training-free-mechanism/AMENDMENT.md` §7 | `papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/amendment_w_base_model_result.json` |
| §5 knowledge-subspace erasure (LEACE) | Amendment AJ | `experiments/knowledge-subspace-erasure/AMENDMENT.md`; `archive/experiment/phase1/probe/amendments/amendment_aj_subspace_erasure.py`; `amendment_aj_addendum_gap_distribution.py` | `archive/experiment/phase1/probe/analysis/amendment_aj_subspace_erasure/` (`result.json`, `addendum_a1_gap_distribution.json`) |
| §7 interventions 1–2 (DPO/KTO stated-confidence contract) | Amendment B | `experiments/stated-confidence-grpo/AMENDMENT.md` | `papers/paper-2-training-regimen/analysis/amendment_b_confidence_alignment_by_outcome.csv` |
| §7 interventions 3–4 (GRPO v1/v2 collapse + incentive analysis) | Amendment E cells; Amendment J diagnostics / session 0026 | `experiments/grpo-v3-proper-scoring-confidence/RUNBOOK.md` | `archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json` |
| §7 intervention 5 (proper-scoring GRPO) | Amendment J (GRPO-v3) | `experiments/grpo-v3-proper-scoring-confidence/RUNBOOK.md`; reward `archive/experiment/phase1/grpo/humility_reward_v3.py`; preflight `archive/notes/experiments/computed-confidence-alignment-regimen.md` | `archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v3_seed1.json`; `results_amendment_j_*` |
| §7 interventions 6–7 (contrastive SFT, answer-supervised / answer-masked) | Amendments K and L | `experiments/contrastive-sft-behavior-conditional-confidence/AMENDMENT.md`; `experiments/answer-subspan-masked-contrastive-sft/AMENDMENT.md` | `calibration_gap_contrastive_sft_seed1.json`; `calibration_gap_contrastive_masked_sft_seed1.json`; `results_amendment_k_*`; `results_amendment_l_*` |
| §7 RL-on-calibrated-base follow-on, incl. the β 0.10 → 0.05 falsifier re-run (Table 2, Figs. 4–6; Fig. 7 spans arms) | Amendment N (incl. β 0.05 arm) | `experiments/grpo-v3-on-contrastive-sft-base/AMENDMENT.md` (results tables §7) | result tables embedded in the amendment document; `results_amendment_n_*`; `action_conditioning_report.py`; run records under `archive/experiment/phase1/run_records/` |
| §7 probe-axis distillation mirror (Table 3) | Amendment M, Revision 3 | `experiments/quantile-balanced-probe-distilled-sft/AMENDMENT.md` | `results_amendment_m_*_probe_factual_sft_seed1_merged_full_4b` |
| §4 pretraining-origin test (four pretrain-only bases at 0.997+); §8 "paid for by pretraining" | Amendment Y | `experiments/pretrain-only-base-readout/AMENDMENT.md` (SUPPORTED 4/4) | `archive/experiment/phase1/probe/amendment_y_results/` |

Vocabulary note: reader-facing prose in this paper follows the program-wide rename
in `papers/common/terminology.md`, the canonical mapping from the prior
"doubt"-family names (doubt axis, doubt direction, doubt readout) to the
known-unknown vocabulary used throughout. Governed filenames, artifact names, and
internal labels in the table above keep their original names verbatim per that
file's usage rule 1.

Governance notes: Amendments B/E/J/K/L/M/N are exploratory single-seed evidence
cells with pre-stated predictions and falsifiers, reported here as exploratory
and never pooled with the pre-registered headline matrix (PROTOCOL v0.3, signed
2026-06-10), whose confirmatory surface belongs to the training-regimen paper
([*Teaching Small Language Models to Say I Don't Know*](../paper-2-training-regimen/manuscript.md)).
The Section 8 references to
[*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md)
correspond to the training-free two-signal readout program, maintained in the
same repository.
