---
title: "Look Before You Speak: Operating-Point-Dependent Selectivity in Actuating Known-Unknown State"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: Draft v1 (restructured)
date: 2026-08-17
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
target: arXiv (cs.CL / cs.AI / mechanistic interpretability)
evidence_base: >
  Exploratory Paper-5 actuation arc. Governed source docs include
  experiments/causal-confidence-steering/AMENDMENT.md,
  experiments/first-person-injection/AMENDMENT.md (legacy label AMENDMENT-AB),
  experiments/doubt-regulated-caution/AMENDMENT.md (legacy label AMENDMENT-AC),
  experiments/second-person-doubt-prime/AMENDMENT.md (legacy label AMENDMENT-AF),
  experiments/oracle-dissociation-prime/AMENDMENT.md (legacy label AMENDMENT-AG),
  experiments/divergent-pool-own-readout/AMENDMENT.md (legacy label AMENDMENT-AH),
  experiments/probe-as-reward/AMENDMENT.md (legacy label AMENDMENT-AI),
  experiments/doubt-gated-caution-tighten/AMENDMENT.md,
  experiments/j-space-localization-qwen3-4b/AMENDMENT.md,
  experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md,
  experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md,
  experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md,
  experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md,
  experiments/abstention-wide-instrument-calibration/AMENDMENT.md,
  experiments/rr-cross-family-raw-refusal/AMENDMENT.md,
  experiments/rr3-corrected-placebo-replication/AMENDMENT.md,
  experiments/gate-contribution-factorial/AMENDMENT.md,
  experiments/ungated-vs-gated-dose-matched/AMENDMENT.md,
  experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md,
  experiments/qwen35-4b-midband-heldout/AMENDMENT.md,
  experiments/snap-seed-sampled-decode-replication/AMENDMENT.md,
  experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md,
  experiments/jspace-family-atlas/AMENDMENT.md,
  experiments/placebo-seed-distribution-census/AMENDMENT.md,
  experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md,
  experiments/evidence-response-direction-search/AMENDMENT.md,
  experiments/placebo-signflip-question-type-analysis/AMENDMENT.md,
  experiments/correctness-direction-rotation/AMENDMENT.md,
  experiments/correctness-subspace-overlap/AMENDMENT.md,
  experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md,
  experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md,
  experiments/radial-anti-propensity-steering/AMENDMENT.md,
  experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md,
  experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md,
  experiments/h6-genstream-hook-firing-check/AMENDMENT.md,
  experiments/dark-actuator-screen/AMENDMENT.md,
  experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md,
  experiments/caution-ablation-rederivation/AMENDMENT.md,
  experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md, and
  `experiments/caution-install-bounded-site-sweep/AMENDMENT.md`.
notes: >
  Exploratory draft, not yet submission-ready. Every reader-facing claim maps
  to the governed experiment document that registered it in Appendix A; body
  prose names no internal experiment identifiers, filenames, or repository
  paths. Actuation results are single-model or surface-local unless the text
  says otherwise, and every positive controller result runs on a frozen,
  off-the-shelf checkpoint except where a trained checkpoint is named
  explicitly. Vocabulary follows papers/common/terminology.md: the readout is
  the known-unknown (KU) direction, the validated actuator at the frozen
  Qwen3.5-4B mid-band operating point is the IDK switch, and any other dosed
  write is a boundary push.
---

# Look Before You Speak: Operating-Point-Dependent Selectivity in Actuating Known-Unknown State

*Scope note on "epistemic state": throughout, the phrase names what a linear
readout of the hidden state reports about answerability and refusal, not a
claim that the model represents its own doubt as a mental state. Our earlier
work named these readouts mentalistically (the doubt direction, the doubt
gate, doubt-coupling); the vocabulary here is known-unknown (KU), which
describes how the readout was fit rather than what the model is supposed to
feel.*

---

> *"What I cannot create, I do not understand."*
>
> Richard Feynman

## Abstract

A frozen small language model carries a near-perfect answerability readout in
its hidden state before it generates, a separate correctness readout after, and
a veto signal that ranks confabulations (fluent, specific answers to questions
the model has no basis to answer) as low trust. Our earlier work established
all three by reading the model from outside. Reading is not writing. Can those
signals be written back into the model to make it act epistemically humble?

Across a sequence of pre-stated exploratory cells, the answer is mixed and
mechanistically sharp. First, naive "turn the probe around" strategies mostly
fail. Direct activation steering and within-generation text injection on the
trust axes produced no behavioral effect; stronger first-person
phrasing produced only a small gate-side trickle and no correctness-revision
effect. A second, purpose-built push against a direction fit specifically to
separate confabulations from honest refusals fared no better: calibrated to
move the readout by exactly the amount needed and verified by read-back to
have done so within 0.1%, it converted zero of 116 confabulations into
refusals, the cleanest case we have of a direction moving by the commanded
amount without the behavior following it. A
high-authority second-person system prompt did move behavior, but a
divergent-pool test showed the model was obeying the instruction rather than
consulting its own readout. Even a reward equal to the model's own probe score
failed to train readout consultation: the true-sensor arm was less congruent
with its final readout than a permuted-sensor control.

Second, hidden-state actuation does work when the problem is posed as a
KU-gated controller rather than as an unconditional write, and it needs no
training at all: every positive result below runs on a frozen, off-the-shelf
checkpoint. A KU-gated boundary
push (dosed write) on raw-base Qwen3-4B converted 136/185 held-out confabulations into
clean refusals (73.5%, Wilson 95% CI [66.7, 79.3]) while producing 8/258
false refusals on known-correct answers (3.1%, CI [1.6, 6.0]); random-direction
and permuted-gate controls did not reproduce the result. Which component
supplies that selectivity, however, is operating-point-dependent rather than a
universal property of the write. At this same overdrive dose (L34, dose 200),
a separate comparison shows an unconditional write damages 60.1%
of held-out known-correct rows versus 3.1% gated, a 57.0-point gap (McNemar's
paired test, p = 4.2e-43): here the gate is the sole source of selectivity. At
mid-band doses (qwen hs20, relative depth 0.625 of the stack, absolute dose
12.608; mistral hs16, relative depth 0.500, absolute dose 3.665), a controlled
factorial found the
write itself is already content-selective: a permuted-gate control reaches
confab abstention 0.550-0.600 against the true gate's 0.689-0.694, and the
KU-readout gate's own contribution to selectivity is real but sub-floor
(0.148 qwen, 0.129 mistral, against a 0.20 floor). At mid-band the
gate's role reduces to a modest selectivity increment plus cost governance,
not the source of selectivity. The lesson is regime-dependent, not universal:
overdrive makes the gate essential, mid-band lets the write self-sort with the
gate tightening the margins.

Third, write location matters. A Jacobian-lens diagnostic localized a
workspace-like band in Qwen3-4B around hs23 to hs29, peaking at hs26, while
the inherited L34 write site maps to hs34, just after that band. After
layer-specific dose calibration, held-out mid-band writing beat the late
reference: hs23 (relative depth 0.639) reached 165/185 clean refusals (89.2%)
versus hs34 (relative depth 0.944) 123/185
(66.5%), a +22.7 point gain with only +0.78 points known-correct cost. Using
the same lens backward to target natural refusal tokens was not enough to
improve the controller: a token-target direction was non-inert by itself
(88/185 = 47.6%) but added only one extra clean refusal on top of the mid-band
boundary push.

Fourth, what transfers across model families is measured rather than assumed,
and the measurement is itself a result. On Mistral-7B the same controller
clears its benefit and cost gates under a wide, blinded abstention instrument
(69.9% adjudicated refusal at 0.52% known-correct cost) and fails
direction-specificity at every operating point tested, because a
magnitude-matched random direction moves refusal behavior too. Fifteen fresh
random seeds per family show why that is not noise: matched-magnitude random
writes are sign-consistent within a family and opposite in sign across
families, suppressing hedging in Qwen (median -6.0 points) and Llama (-7.67)
while recruiting it in Mistral (+7.0). A raw increase in abstention rate
therefore cannot certify that an intervention is coupled to the model's
known-unknown state, and a placebo criterion has to be set against a
family's own measured null rather than against zero. On Gemma-4-E4B, a depth
ladder overturns that family's reputation for inertness: it clears the
behavioral gates at four sites in a shallow band, and fails
direction-specificity at every site tested above its key-value sharing seam.

Together these results support a practical distinction: epistemic state is
readable, externally usable, and sometimes writable, but not automatically
consulted by the model's own policy. Productive actuation requires the right
channel, the right gate, and the right write site, and none of it requires
training the model. Training does not remove the causal handle either: on a
trained checkpoint from a separate line, ablating a related refusal axis
releases 45.7 points of known-item over-refusal on a fresh seed of the same
recipe (Section 6.6).

---

## 1. Introduction

A small language model can represent what it knows internally while failing to
verbalize or act on that state. That gap is where this work started. It is a
failure of coherence between a model's stated signal and its hidden-state
signal, the cross-cutting axis of a taxonomy of epistemic humility we set out
separately, which runs from scalar calibration up to uncertainty over the
objective itself (Rosenbaum, 2026a).
Our diagnosis of the gap (Rosenbaum, 2026c) showed that answerability is linearly
readable from hidden states at near-ceiling accuracy while stated confidence
remains flat and training-resistant. The follow-up (Rosenbaum, 2026d) showed
that two readable signals, answerability before generation and answer
correctness after generation, compose into a training-free trust pipeline that
generalizes across sizes, families, and sampled-decode seeds.

Those results are about reading. Actuation runs the other direction. If a model
already contains a faithful epistemic signal, can we make its generation policy
consult that signal? Can we steer the residual stream, inject the signal in text, reward
agreement with it, or write into the workspace-like layer band where reportable
representations live (Gurnee et al., 2026)?

This is not a trivial extension of probing. A linear probe can be useful even if
the model's policy never uses the direction it reads. Conversely, a direction can
be behaviorally causal without being a faithful self-readout. Neither half is
peculiar to this work. Representation engineering treats reading a concept
direction and writing along it as one method (Zou et al., 2023), and a
controlled study across five models finds the two can come apart sharply: a
logistic probe above 93% accuracy at every layer produced near-zero steering
effect at its own best-accuracy layer, while alignment with the model's own
unembedding readout predicted steering success where probe accuracy did not
(Billa, 2026). The claim the evidence supports is correspondingly narrow:

> **A readable direction is not automatically a usable actuator, and what
> makes it usable is the operating point.** Epistemic directions can be
> strong, portable readouts while remaining weak, channel-dependent, or
> non-selective actuators; where selectivity comes from, when it appears at
> all, is a property of the dose and the write site rather than of the
> direction.

That thesis had an obvious way to be wrong. If writing a readable direction
back into the residual stream at the layer where it reads best had moved
behavior selectively, there would be no gap between reading and writing to
report. Five experiments tested exactly that, across two independent
activation-write attempts (one on the gate and dial directions themselves, one
on a direction purpose-built to separate confabulations from honest refusals
and verified by read-back to move by the commanded amount), text injection,
system prompts, and reward, and none of them produced it.

Four findings follow, and they are the argument of the paper. Reading a
direction is not writing it: five independent ways of routing the readout into
behavior fail on the same substrates where the readout itself is near-ceiling.
Direct activation writes do actuate, and there selectivity belongs to the
operating point rather than to the direction, which is what the gated versus
unconditional comparison, the dosed boundary push, and the one mid-band write
validated closely enough to earn a name of its own each show from a different
side. Where the write lands matters
as much as what is written: the workspace-band depth rule holds on the model
that produced it and gets its cross-family stress test on a fourth family's
depth ladder. And what transfers across families is measured rather than
assumed: benefit and cost gates replicate, direction-specificity does not
survive its strongest test on every family, and the random-direction null a
placebo control is supposed to sit against is itself family-signed, which
makes the cross-family scope of the recipe a result in its own right.

The practitioner's version of all four is a five-step recipe, and it is short
enough to state before the evidence for it:

1. read the model's epistemic state externally;
2. use that readout as a gate;
3. write a calibrated policy direction only where the gate fires;
4. choose a site where the write lands inside or near the workspace-like layer
   band;
5. keep random-direction, permuted-gate, and known-correct cost controls in
   the loop, with the random-direction tolerance set against that family's own
   measured null rather than against zero.

Three strands of evidence sit beside that argument rather than inside it, and
each is flagged where it lands. Two experiments of ours on the correctness
axis, one measuring its rotation across a model's own training checkpoints and
one asking whether a shared subspace explains its partial transfer between
them, are why we expect that axis to generalize worse than the answerability
axis this paper writes on (Section 6.5). An ablation of a refusal
axis on a trained checkpoint is why we do not think training removes the
causal handle (Section 6.6). And the per-family random-direction null
distributions that the cross-family results lean on were measured as an
instrument study in their own right rather than assumed (Section 4.8).

The evidence remains exploratory: most experiments are single-model,
single-seed, or surface-local. The pattern is stable enough to organize the
next study, a larger cross-model replication of the gated workspace-band
actuator plus sharper tests of whether denser token targets or different model
families change the write/read relationship.

---

## 2. Background: From Readout to Actuation

### 2.1 The prior readout result

Our diagnosis paper (Rosenbaum, 2026c)
separated three surfaces: the internal state, the stated confidence token, and
the generated behavior. On Qwen3-4B, an internal answerability axis separated
known from unknown items at about AUROC 0.997 (area under the receiver
operating characteristic curve, where 0.5 is chance and 1.0 is perfect
separation), while stated confidence was nearly flat. The readout paper
(Rosenbaum, 2026d)
then split the internal state into two deployable readouts: an answerability
**gate** before generation and a correctness **dial** after generation. The
gate/dial/veto pipeline is useful because it reads the model from outside
rather than asking the model to faithfully report itself. Both results sit
inside an established finding that hidden states carry knowledge and truth
structure the output channel does not express (Burns et al., 2022; Kadavath et
al., 2022; Marks et al., 2023; Orgad et al., 2024), including answerability
specifically, which is linearly readable even on items the model goes on to
hallucinate an answer for (Slobodkin et al., 2023), and entity-level knowledge
awareness, which is readable as a direction and causally gates whether the
model refuses or fabricates (Ferrando et al., 2024).

That distinction motivates the present study. External reading can support a
classifier, a monitor, or an abstention wrapper, but it does not prove the model's
own policy uses the signal. Abstention itself is also not a solved problem an
external controller would be redundant with: the design space is wide (Wen et
al., 2024), training a model to say "I don't know" is a substantial project in
its own right (Cheng et al., 2024), and reasoning post-training degrades
abstention rather than fixing it (Kirichenko et al., 2025). Actuation asks whether the internal state can be
made causal for behavior.

### 2.2 What would count as use?

We treat "use of an internal readout" as stronger than behavior change. A system
prompt that says "you do not know this" and causes refusal is an actuator, but it
does not show the model consulted its own state. Likewise, a reward that improves
abstention behavior may train surface heuristics rather than readout alignment.

The cleanest positive evidence would satisfy three conditions:

- alignment: the intervention is computed from the model's own state, not
  from gold labels;
- specificity: a permuted or random control does not reproduce the effect;
- selectivity: the intervention moves target failures without imposing the
  same action on rows where it is inappropriate.

The specificity condition is the one the external literature has found hardest
to satisfy, and the one that costs the cross-family results in Section 4.8
their strongest claim: a random unit vector orthogonal to a fitted
steering vector can produce behavioral effects statistically indistinguishable
from the fitted vector itself across several traits and models (Venkatesh and
Kurapath, 2026). Because intervention conclusions are also sensitive to metric
and corruption choices (Zhang et al., 2023), every control below was frozen
before outcome evaluation.

The successful cells below meet these conditions only when readout and write are
separated: the readout gates the intervention, and the write supplies a fixed
behavioral move.

---

## 3. Methods

Appendix A maps each claim below to the governed document behind it, and
Appendix B gives the checkpoint and pinned revision behind each one, separating
the substrates a multi-model cell declared from the ones it actually launched.

Write sites are named by their raw
hidden-state index (hs followed by the layer number) because that is how each
experiment's own instrument named them, but raw indices are not comparable across families
with different block counts, and several comparisons here are cross-family.
We therefore also give relative depth, the layer index divided by the model's
number of hidden layers, wherever a site is compared against a site in another
family. Block counts, each read from the checkpoint's own configuration file,
are: Llama-3.2-3B 28, Mistral-7B-Instruct-v0.3 32, Qwen3.5-4B 32, Qwen3-4B 36,
Gemma-4-E4B 42. The convention matters here rather than being bookkeeping:
llama's hs20 and Qwen3.5-4B's hs20 are the same integer and not the same depth
(relative depth 0.714 versus 0.625), and on present evidence they fall on
opposite sides of the band in which any family we tested has actuated.

### 3.1 Channels

We tested four ways to route an epistemic readout into behavior.

- Activation writes: interventions that modify the residual stream along a
  fitted direction at a specified layer and token scope, either by adding a
  scaled copy of the direction or, in the erase-write form used for most
  results here, by removing the state's existing component along that direction and
  writing a fixed setpoint in its place, following the activation-addition
  line (Turner et al., 2023) and its contrastive difference-of-means
  construction (Panickssery et al., 2023), within the broader read-and-write
  program of representation engineering (Zou et al., 2023). These are the
  closest analogue to turning the probe around, the strategy inference-time
  intervention makes explicit for a truthfulness probe (Li et al., 2023).
  Every activation write reported in this paper is
  timed to a fixed pre-generation position and persists through decode; a
  mid-generation write timed to the point where the model commits to an
  answer was also attempted, but is not reported as a result because an
  instrument-validity check found it uncertified (Section 6.4).
- Within-generation text injection: probe scores rendered into a thinking or
  revision trace as text, either as terse telemetry or as first-person prose
  with explicit action rules.
- High-authority system prompts: the same kind of state-derived label
  rendered as a second-person system instruction before generation.
- Reward coupling: a reinforcement-learning reward computed from a frozen
  probe score read from the policy's own pre-generation hidden state.

Two further operations on a fitted direction appear in the results on trained
checkpoints, and they are not the same intervention. **Ablation** removes the
state's component along the direction and leaves the rest of the residual
stream untouched, so the model runs without whatever that direction carries.
**Displacement** leaves that component in place and adds a fixed multiple of
the direction on top of it, the multiple counted in standard deviations of the
direction's own projection over the rows it was fit on, so a minus-two-sigma
displacement subtracts two such units without erasing anything. Ablation asks
what the model does when the direction is gone; displacement asks what it does
when the direction is moved. Both are reported on the same refusal axis in
Sections 6.3 and 6.6, and whether they agree turns out to depend on the site.

### 3.2 Readouts and directions

The core readouts are the known-unknown (KU) direction and a refusal
direction. In the gating experiments, the sensor is a standardized KU
projection: confabulation-prone rows project lower on it than known-correct
answered rows, so the gate fires when the negated projection exceeds a frozen
threshold. The actuator is a separate boundary-push direction, constructed by
orthogonalizing a raw refuse/control direction against the KU direction and
confab-propensity controls. The raw direction is built the way refusal
directions are built elsewhere (Arditi et al., 2024); the orthogonalization is
a guard against the gate and the actuator collapsing into one axis, and it is
worth saying plainly that it does not buy representational independence, since
ablating one orthogonal refusal direction measurably changes another
(Wollschläger et al., 2025), and refusal is not well captured by any single
direction (Joad et al., 2026). Later J-space experiments reuse per-layer
versions of these gates and write directions.

The J-space line adds the Jacobian lens (J-lens) of Gurnee et al. (2026). For a
hidden-state vector at a layer, the J-lens estimates the first-order causal
effect of that vector on the model's final output, a Jacobian rather than a
fixed or learned linear map, and applies the unembedding matrix to the result
to give a vocabulary readout of what the model is poised to verbalize at that
point. Gurnee et al. find that workspace-like properties, meaning
representations available for report and for flexible internal use, emerge in
an intermediate band of layers rather than uniformly. We use the lens in two
ways: first as a read-only localization diagnostic, and then backward as a
source of token-target write directions.

### 3.3 Fitting the directions

Rows enter a fit by what the model does with them at baseline, in three roles:
confabulation-prone rows (unanswerable questions it answers anyway),
known-correct rows (answerable questions it answers correctly), and
unknown-refused rows (unanswerable questions it declines). The
confabulation-prone and known-correct roles are split, stratified by question
category under a fixed seed, into a fit split of 40% and a held-out split of
60%. Unknown-refused rows are never themselves gated or graded, so the whole
role stays in the fit split as scaffolding. On the raw-base Qwen3-4B controller
that split is 124 fit and 185 held-out confabulation rows, and 172 fit and 258
held-out known-correct rows.

Every direction here is read at one layer and one token position: the anchor,
meaning the last prompt token, taken before the model has generated anything.
The anchor is a function of the prompt alone, so the same position is defined
identically in every arm.

The known-unknown direction is a mass-mean contrast, the difference of two
class means normalized to unit length: the mean anchor state over fit
known-correct rows minus the mean over unknown-refused rows. On the raw-base
Qwen3-4B controller it is fit at hidden state 34. The gate score is that
direction's projection, standardized by the fit pool's own mean and standard
deviation, clipped to plus or minus two, and negated, because
confabulation-prone rows sit lower on it. The firing threshold is the Youden-J
point of that score, the point maximizing true-positive minus false-positive
rate, chosen on the fit split alone and frozen before a single held-out row is
touched. Separating fit confabulation rows from fit known-correct rows, the
score reaches AUROC 0.9955; the selected threshold catches 120 of 124 fit
confabulations (96.8%) and flags 2 of 172 fit known-correct rows (1.2%). Every
number Section 4.5 reports is measured on the held-out split that neither the
direction fit nor the threshold choice ever saw.

The raw direction the boundary push is built from is a second mass-mean
contrast in the same anchor states, and it is not the same contrast: the mean
over unknown-refused rows minus the mean over fit confabulation rows, which
separates declining from confabulating among questions the model cannot
answer. A third direction, confabulation propensity, is a standardized logistic
classifier of the confabulation label over those same rows, with its solver
seed pinned so that refitting reproduces the vector exactly. The boundary-push
write direction is that raw refuse-versus-confabulate direction with its
components along the other two removed, by Gram-Schmidt against the plane the
two span. Propensity is carried only to define that plane; the gate does not
read it.

The refusal axis of Sections 6.3 and 6.6 is a different direction with a
different fit, and it is fit on answerable questions rather than unanswerable
ones: a mass-mean contrast between known items the model refuses and known
items it answers correctly, taken at hidden state 35 on the trained checkpoint
and unit-normalized. Its sigma, the scale a displacement is counted in, is the
standard deviation of its own projection over those same rows.

Directions are refit at each site rather than ported. The mid-band Qwen3.5-4B
operating point carries its own directions, standardization constants, and
threshold fit at hidden state 20; the Mistral-7B site at hidden state 16
carries its own, rebuilt byte-identically from that family's own fit record;
the layer sweeps of Section 4.6 carry one set per layer. No fitted vector
crosses a family boundary anywhere in this paper.

### 3.4 Dosing and operating points

Two write laws appear below, and they measure dose differently.

The erase-write law, which every gated controller result uses, removes the
state's existing component along the write direction and installs a fixed
setpoint in its place. The dose is therefore the realized projection onto the
write direction after the write, and it is read back on dosed rows to confirm
the write landed. That single quantity is expressed two ways. At the raw-base
Qwen3-4B late site it is stated as a raw projection value, dose 200, and
read back at mean 200.11 on the pre-run smoke and mean 200.018 across the
dose-matched comparison. At the mid-band sites it is stated as a multiple
of sigma, the standard deviation of that direction's projection over the fit
pool, which is what makes a setpoint comparable across layers and families
whose residual streams differ in scale: Qwen3.5-4B at hidden state 20 runs at
eight sigma, an absolute dose of 12.608, and Mistral-7B at hidden state 16 runs
at twelve sigma, an absolute dose of 3.665. The absolute figure and the sigma
multiple are one number written twice. The late-site dose has no sigma
expression, which is why it is quoted as the raw projection value throughout.

The additive law leaves the existing component alone and adds a fixed vector on
top of it. It is used by the push of Section 4.2, where the dose is the
raw-space projection gap between the confabulating mean and the refusing mean
along that direction, the amount that moves an average confabulating row's
reading onto the refusing population's mean; and by the displacements of
Sections 6.3 and 6.6, where the dose is a stated number of sigma.

Doses are chosen on the fit split, never on the rows a result is reported over,
under a single rule. A ladder of candidate setpoints, fixed before the run, is
applied to a small fit-split calibration subset at the candidate site. A rung
is usable only if the read-back lands within tolerance on every dosed row, no
dosed row degenerates, and fit-split confabulation clean tightening on the
subset clears its floor: 50% in the layer and depth ladders, and 60%
together with fit-split known-correct false refusal at or below 10% in the
cross-family fleet. Selection among usable rungs differs by design: the layer
and depth ladders take the highest fit-split clean tightening, breaking ties
on lower known-correct cost and then lower dose, while the cross-family fleet
takes the lowest qualifying dose. If
no rung on the ladder is usable, the arm stops there and is recorded
as having no viable dose, before any held-out row is generated or scored. That
stop is a pre-outcome rule rather than an outcome, and it is what ends the
cross-family fleet's arms in Section 6.5 and the two deepest Gemma sites in
Section 4.9.

### 3.5 Outcome measures

Different channels move different things, so no single outcome covers the
results below.

**Clean tightening** is the primary behavioral outcome of the write results: a
row that previously confabulated now produces a single well-formed JSON object
with exactly one answer field, that field's value is a refusal, generation
terminated naturally before the token cap, and nothing follows the JSON. It is
the strictest outcome in the paper, since a row that refuses in prose but
breaks the output contract does not count.

**Known-correct false refusal** is the matching cost outcome: a row that was a
well-formed answer matching a gold alias at baseline is no longer one after the
intervention. It counts refusals, wrong answers, and broken output alike, which
is why Section 4.5 decomposes it once into those three parts.

**Refusal**, where the text says refusal rather than clean tightening, is a
format-agnostic reading of the same behavior: the generation contains one of
three fixed English refusal forms, anywhere in the text and regardless of
whether the JSON parses, with degenerate text excluded. Well-formedness is then
reported as its own separate rate, which is what lets a result state that
refusal and output corruption came apart.

**Abstention** in Section 4.1 is the rate at which the model declines on
unanswerable questions, read off the final output after a revision pass rather
than the first pass, with accuracy on answerable questions carried alongside as
a no-regression floor. The dial cells in the same section score
appropriate-revision discrimination instead: the probability of revising given
an initially wrong answer minus the probability of revising given an initially
correct one.

**Release** is baseline refusal rate minus the arm's refusal rate on the same
population, the share of rows an intervention un-refuses. **Induced refusal**
is its mirror, the arm's refusal rate minus baseline on a population that
answered at baseline, the share an intervention muzzles.

**Selectivity gap** is release on known items the model refused despite being
able to answer them, minus release on unanswerable items it refused. A prompt
that frees the first group without freeing the second scores high. Section
4.3's headline is the true prompt's gap minus the permuted prompt's gap.

**Congruence** is per-row agreement between what the policy did and what a
fresh probe reads from that policy's own pre-generation state on that same row:
either the probe reads unanswerable, at probability above one half, and the
model refused, or the probe reads answerable and the model answered. An output
that violates the schema counts as incongruent. It is the primary outcome of
the reward experiment in Section 4.4, and it is deliberately not an accuracy
measure: a policy can abstain well and still score low on it.

**Contribution to selectivity** is the quantity that decides whether the gate
or the write supplies selectivity at a given operating point. For one arm,
selectivity is the magnitude of its effect on confabulation-prone rows minus
the magnitude of its effect on known-correct rows, each effect being that arm's
rate minus the undosed baseline rate on that population, taken in absolute
value. The gate's contribution is then that quantity under the true gate minus
the same quantity under a permuted gate, with the write held fixed.
Magnitudes rather than raw rates are used because a mid-band write can suppress
hedging rather than induce it, and a raw contrast flips sign in that regime
while the underlying concentration of the effect on unknowns does not.

**Hedged share** is the wide-instrument abstention rate on the
confabulation-prone pool. The census of Section 4.8 reports, per random seed,
the signed change in that share in percentage points against a shared undosed
baseline measured on the same rows.

**Over-refusal**, in Section 6.6, is the refusal rate on questions the model can
answer, so a collapse in over-refusal is a release of behavior rather than a
cost.

**Degenerate output** is text that is empty, contains no alphanumeric
character, is a single repeated n-gram, or whose parsed answer field is a
dominant repeated unit. Degenerate rows never count as refusals or abstentions
under any instrument here. A rise in the degeneracy rate above 5 points against
baseline is a guard in the text and prompt channels, and zero
degeneracy on dosed rows is a precondition for a dose to be usable at all.

### 3.6 Scoring instruments

Refusal is scored two ways across this paper, and which one a result rests on
changes what the number means.

The narrow instrument reads refusal from the model's own output and nothing
else: a refusal value in the parsed JSON answer field, or one of three fixed
English refusal forms in the text. It is what Sections 4.5, 4.6, 4.7 and 4.9
score under, including the random-direction and permuted-gate controls behind
the Section 4.5 headline and every clean-tightening rate in the layer and depth
ladders.

The wide instrument is a two-stage stack. First a frozen, deterministic pattern
detector, widened beyond those three forms with abstention vocabulary compiled
before launch from mined in-family idioms and published abstention phrase
inventories; its rates are reported but do not decide anything. Then the
primary lane: every row the detector marks non-refused is stripped of arm,
dose, role, and source labels, shuffled under a fixed permutation, and graded
as bare text by context-free adjudicators against a single rubric.
A text counts as an abstention only if it declines to give the queried answer,
or states unknowability or uncertainty as its answer, without also asserting a
specific answer value; a hedge followed by a committed answer is not an
abstention, and degenerate or empty text is not an abstention. The pool carries
clear-positive and clear-negative decoys to certify adjudicator calibration
before unblinding, and the graded manifest is hashed and committed before
anything is unblinded. The final rate per row is detector-refused or
adjudicated-abstention. The lane cannot widen the benefit vocabulary without
widening the cost vocabulary by the same rule, because the adjudicator cannot
tell a confabulation-prone row from a known-correct one. This stack is what
every number in Section 4.8 rests on, and what the mid-band gate factorial
reported in Sections 5 and 6.2 rests on.

Sections 4.1 through 4.4 score under neither: each of the text, prompt, and
reward channels uses the refusal grader defined in its own cell, applied to
that cell's own final output. The two stacks are not interchangeable, and the
size of the gap between them is itself measured in Section 4.8.

### 3.7 Populations and controls

Confabulation-prone rows come from the unanswerable split of
Known-Unknown Questions (Amayuelas et al., 2023), whose per-row subtype labels
(controversial, future-unknown, underspecified, and the rest) Section 4.8
uses for its subtype breakdown. Known-correct rows come from PopQA (Mallen et
al., 2022) and TriviaQA (Joshi et al., 2017), graded against gold answers.
Every experiment below draws its rows from these three sources unless the text
says otherwise.

Controls are matched to the mechanism, and each control's metric and
construction were declared before outcome evaluation, following the standard
caution that intervention conclusions are sensitive to exactly those choices
(Zhang et al., 2023):

- text-injection arms use placebo or permuted labels with the same prompt form;
- reward arms compare true-sensor and permuted-sensor rewards;
- hidden-state write arms use random-direction controls and permuted gates;
- J-space token-target arms use a matched random J-space direction.

A random-direction control writes a fixed random unit vector, drawn without
reference to any data, on the same rows the true gate fired, at a magnitude
matched to the realized projection the true write achieved. A permuted gate
holds the number of dosed rows fixed and permutes which rows they are,
assigning them uniformly at random across the combined confabulation-prone and
known-correct pool under a fixed seed, with the real write direction unchanged.
Permuting over the combined pool rather than over confabulation-prone rows
alone keeps the fired mix at deployment proportions; permuting within a
subsample would over-represent known-correct rows and flatter the gate.

### 3.8 Statistical analysis

Every binomial rate in this paper carries a Wilson 95% interval, and the
gates are stated against both the point estimate and the relevant
end of that interval, so a rate can clear its floor and still miss its gate.

Paired binary comparisons between two interventions on the same rows use
McNemar's test, evaluated as an exact two-sided binomial test on the discordant
pairs. It certifies the gated versus unconditional contrast of Section 4.5,
where 149 of 258 known-correct rows are discordant, and the mid-band versus
late write-site contrast on the multi-source pool in Section 4.6, where 42 rows
are discordant and all 42 break the same way. The latter carries a
second clause the test alone does not supply: late-only failures had to
outnumber mid-only failures at least three to one.

A confidence interval on the difference between two independent proportions
uses the Newcombe hybrid score interval, built from the two rates' own Wilson
bounds rather than from a normal approximation, which is what Section 4.9
reports for the well-formedness difference between the two key-value sharing
conditions.

Bootstrap intervals are percentile intervals, and the resampling unit follows
what the quantity is a distribution over rather than being uniform across the
paper:

- Section 4.2's primary-minus-control kill difference resamples rows, 1,000
  resamples;
- Section 4.3's quantities all resample rows within cell, at 10,000 resamples
  for the selectivity gap, the induced refusal, and the compliance asymmetry,
  and over rows for the divergent-pool release congruence;
- Section 4.4's congruence differential resamples rows in pairs matched across
  the two training arms, 10,000 resamples;
- Section 4.8's sign fractions resample seeds, not rows: each of the fifteen
  seeds contributes one signed delta, and 10,000 resamples of those fifteen
  signs give the interval. Each seed's own delta separately carries a row-level
  Wilson interval, and the two levels are never pooled.

### How this research was conducted with AI

This actuation program is run by a human principal investigator working with a
frontier language model acting as a research orchestrator, which dispatches
specialized AI agents for bounded tasks. We state the arrangement because it
is part of the method: an actuation claim is easy to get wrong in a way the
final numbers alone will not reveal, if the same process that builds an
intervention also grades it, and the division of labor below is built against
that risk specifically.

Every cell behind this paper is a governed unit of work. Before any row is
scored, a signed design fixes the channel, the write site, the dose law, the
controls, and the outcome gates, and every instrument file behind it is
pinned by content hash. After signing, thresholds do not move, and an outcome
cannot be reinterpreted to fit a different gate after the fact. The human
side holds everything with consequence: approving a cell's design before it
launches, authorizing the compute that runs it, adjudicating any outcome that
requires judgment rather than arithmetic, merging a result into the record,
and deciding what the paper claims. The AI side builds each channel's
harness, runs the dose calibration and control sweeps, computes every
statistic reported below, drafts this manuscript, and red-teams its own
results before a human is asked to trust them.

Two controls carry most of the weight. Adversarial review is mandatory
before any positive result is trusted, and it runs separately from the agent
that produced the result, looking specifically for the failure modes an
actuation claim is prone to: a control that can see what it is supposed to
be blind to, a direction fit and evaluated on the same rows, and a placebo
that looks clean only because it was measured against the wrong baseline.
And every claim traces to its governed design document rather than to a
memory of what an earlier cell showed. No agent, including the orchestrator,
may assert what a prior experiment found without opening its signed record,
because a plausible but wrong account of a prior result is the error that
compounds silently across a program with this many cells behind it.

Provenance is enforced by construction. Every checkpoint is pinned by
revision, every instrument file is content-hashed at signing, and Appendix A
traces each claim in this paper to the document that governs it while
Appendix B traces it to the exact checkpoint. None of this removes the need
for human scientific judgment about what a pattern of null and positive
results means across the cells above. It keeps the AI's share of that
judgment auditable: a reader can follow any number in this paper back to the
bytes that produced it and the document that fixed its gates before a single
row was scored.

---

## 4. Results

### 4.1 Directly writing or telling the model its readout mostly fails

Start with the most direct question the readout results raise: if the gate and
dial directions are readable, can we write them back into the model at the
positions where they read best? That premise, that the best read site is the best write
site, is one an independent study has since tested directly and rejected: probe
accuracy does not predict steering success, and the layer where a probe reads
best can produce no steering effect at all (Billa, 2026). Steerability also
tracks how separable the two activation clusters are along the fitted
difference direction rather than how accurately a classifier can be fit (Braun
et al., 2025).

On Qwen3.5-4B, an 8-cell steering grid crossed two signals (gate/dial), two
positions (anchor/end), and two channels (activation write/text injection). None
of the eight cells passed its effect gate. Gate-at-anchor activation steering was flat across
the alpha sweep; dial-at-end activation steering was flat; text-injection cells
were also flat under their own metrics. The signal is present and the
tested channels do not make the policy use it, which is the read/write split
in its simplest form.

A natural objection is that the text was phrased unnaturally. We therefore tested
stronger first-person phrasing: "I am X% sure..." plus an explicit action rule.
The result remained negative. The gate cell showed a small, real trickle of
rule-following (+2.0 points abstention, CI excluding zero) but missed the +10
point gate by a factor of five. Dial cells did not improve revision behavior:
the late-position metric was instrument-saturated, and the final-thought version
missed with a -2.7 point delta whose CI included zero. The strongest natural
language framing did not open the channel at useful magnitude.

The model can read the state, and an external system can read the state, but
placing a description of that state inside the generation trajectory does not
reliably make the model act on it.

### 4.2 A calibrated push against a purpose-built confabulation direction moves the readout but not the behavior

The same question has a sharper form. Rather than reusing the gate and dial
directions, which were fit to read, ask it of a direction built for exactly
this purpose: a direction fit
to separate confabulations (fluent, specific answers to questions the model
has no basis to answer) from honest refusals among questions the model
cannot answer, residualized against the refusal axis so that it is not a
restatement of the model's general tendency to refuse. Call it the
confabulation-push direction; it is
distinct from the known-unknown axis used everywhere else in this paper and
from the boundary-push write direction of Section 4.5. It was fit on a
checkpoint trained with reinforcement learning, the same checkpoint whose
reward-trained arm is evaluated in Section 4.4 below, where it produced 116
confabulations under the checkpoint's own generation policy on a fixed
question set.

If the direction is causally upstream of the fabricate-versus-refuse choice,
subtracting it from the residual stream at generation time, at a magnitude
calibrated to erase the average gap between confabulating and honestly
refusing rows, should convert some of those 116 into refusals. Ninety-eight
rows scored above the push threshold and were dosed from the first generated
token onward; a permuted-assignment control pushed the same number of rows,
chosen at random, at the same magnitude and direction. Collateral stayed
inside its floor: none of 90 baseline-correct rows flipped to
refusal, against a ceiling of 3. But the push converted zero of the 116
baseline confabulations, and a three-point dose ladder at half and double the
calibrated magnitude converted only one of 30 pushed confabulations at the
highest dose tested. The primary arm's kills minus the permuted control's
kills came to exactly zero, with a bootstrap 95% confidence interval of
[0.00, 0.00]. Both the reach and specificity gates missed, and the
falsifier fired.

The null is not an instrumentation failure. A read-back check on the pushed
rows found the confabulation-push projection moved by -2.7133 against a
commanded -2.7110, a ratio of 1.0008: the push landed almost exactly where it
was aimed. Unpushed rows showed a projection shift of exactly 0.0000, and
reproduced their unintervened grade on 1,564 of 1,564 rows. The direction
moves the readout by the commanded amount, and the behavior does not move at
all.

![FIG-P5-06: Confabulation kills under the primary push versus the permuted-assignment control, with the read-back verification of push magnitude](figures/fig-p5-06-propensity-null.png)
**Figure 6.** Confabulations converted to refusal under the calibrated
confabulation-push direction versus a permuted-assignment control at the
same magnitude, alongside the read-back check confirming the push landed
within 0.1% of the commanded amount on pushed rows and produced exactly zero
shift on unpushed rows.

The scope is deliberately narrow: one checkpoint, one seed, and the
confabulation-push direction itself does not transfer across checkpoints at
better than 0.17 cosine similarity to a reference axis on this substrate, so
the result licenses a claim about the injection channel on this trained
checkpoint, not about confabulation-propensity actuation in general.

### 4.3 System-prompt authority moves behavior, but not by own-readout consultation

The next question was whether the failure was text itself or text authority. A
second-person system-prompt directive gives the model a per-item certainty label
before generation: when certainty is HIGH, answer directly; when LOW, say "I
don't know." The true arm used the model's probe-aligned label; the placebo arm
permuted labels across rows while preserving marginal frequencies.

This high-authority channel moved behavior. On the raw-base Qwen3-4B substrate,
the true system prompt beat the permuted prompt on the selectivity gap by +18.0
points, with bootstrap CI [+11.8, +24.7]. It released some known-refused rows
without inducing unknown-refused rows to answer, and passed its specificity and
degeneracy guards.

However, this did not yet establish own-state consultation. On that pool, the
probe label and the gold answerability label agreed on every row, so a
probe-aligned instruction was also a correct oracle instruction. The follow-up
inverted the labels. The model obeyed the wrong muzzle strongly: induced refusal
on known-correct answered rows rose by +34.0 points, CI [+26.5, +41.5]. It
resisted the wrong pro-answer instruction more strongly: unknown-refused release
was +7.9 points. The asymmetry, +26.1 points, passed its locked gate.

Internal-state instrumentation sharpened the picture. The known-unknown
direction did not move semantically with the prompt; compliance traveled
primarily through a refusal/policy axis. A divergent-pool follow-up then separated rows where the
model's own readout and the gold label disagreed. Release congruence with the
model's own readout was a precise zero: -0.21 points, CI [-4.45, +4.10]. A
positive-control addendum verified that the instrument was live
(+50.98 point induced refusal on a refusal-representative stratum). The verdict:
system prompts move policy by compliance and boundary distance, not by making the
model consult its own readout.

Authority is an actuator, but it is not the self-monitoring channel this
section set out to find. It can install refusal behavior from outside, even
against the model's own knowledge. That models capitulate to authoritative
framing against their own prior answer is well documented: challenged on a
correct answer, models flip roughly 46% of the time on average, with
confrontational and persona-based challengers the most effective (Laban et
al., 2023). The steering analogue is equally well documented, in that an
externally supplied knowledge-awareness direction can force refusal on
entities the model does in fact know about (Ferrando et al., 2024).

### 4.4 Rewarding the readout also fails to train consultation

If prompting does not make the model consult its readout, perhaps training can.
Reward is known to move uncertainty behavior: proper scoring rules over
verbalized confidence improve calibration without an accuracy cost (Damani et
al., 2025), direct confidence expression responds to a logarithmic scoring
reward (Bani-Harouni et al., 2025), and metacognitive self-judgment as a
reward signal improves faithful uncertainty expression over standard RL (Liu
et al., 2026), and our own controlled comparison of supervised, preference,
and reinforcement-learning regimens for abstention takes up that question
directly (Rosenbaum, 2026b). The
question here is narrower and harder: not whether reward
moves the behavior, but whether it makes the policy consult its own
hidden-state readout. The probe-as-reward cell took two checkpoints that had
been supervised fine-tuned on clean data and trained both with the same
reinforcement-learning recipe, group-relative policy optimization (Shao et
al., 2024), which scores a group of sampled completions against each other
rather than against a learned value model. In
the TRUE arm, reward agreement was computed from a frozen probe read from the
policy's own pre-generation state. In the PERMUTED arm, the sensor was
permuted within class. The primary held-out metric was congruence between the
final policy behavior and the arm's own freshly refit eval probe.

The instrument was valid: both arms completed all 2934 scheduled steps, no
tripwire halted, and fresh probes on the final checkpoints still read gold at
out-of-fold AUROC 0.9948 and 0.9946. But the result went the wrong way. TRUE
congruence was 59.75% versus PERMUTED 76.75%, a -17.0 point differential with CI
[-21.5, -12.5]. The TRUE arm preserved some useful behavior, such as fewer
unknown hallucinations than the control, but it did
not learn to consult its own readout.

Reward can shape behavior correlated with the sensor, but this does not imply
policy-readout congruence. On rows where content and readout dissociate, the
policy sides with learned content and boundary behavior rather than with its
own current probe state. A ternary abstention reward under GRPO reaches a
compatible conclusion from a different direction, moving abstention behavior
without coupling it to confidence (Mohamadi et al., 2025).

### 4.5 A gated hidden-state controller succeeds, and the gate's role depends on the dose regime

The intervention form is what changes the outcome. Rather
than asking a single direction to be both sensor and actuator, the controller
that works separates them. The nearest published analogue is entity-level:
directions that detect whether a model can recall facts about a queried entity
causally gate refusal versus fabrication when written back in (Ferrando et
al., 2024). The controller below applies the same read-then-write logic at the
level of whole questions, and separates the two roles into two different
directions:

1. a KU readout gate decides which rows look like confabulations;
2. a fixed boundary push (dosed write) writes only those fired rows to a
   selected refusal setpoint.

At this write site (Qwen3-4B, L34) and dose (200), a separate comparison
later established why this separation matters: an unconditional write damages
60.1% of held-out known-correct rows versus 3.1% gated, a 57.0-point gap
(McNemar, p = 4.2e-43), while the gate
costs the controller only 4.3 points of confab conversion (77.8% ungated
versus 73.5% gated). The 60.1% figure is not a refusal rate; it decomposes as
55.8 points clean false-refusal, 3.9 points answered-wrong, and 0.4 points
degenerate output. At this specific write site and dose, which the margin
theory identifies as an overdrive operating point, the gate is the sole
source of selectivity: the write, left unconditional, damages most
known-correct rows. This is the collateral-damage trade-off that additive
steering methods are known to face at effective magnitudes (Nguyen et al.,
2026), and that norm-violating writes in particular incur as outright
capability collapse (Dang and Ngo, 2026). What the gate buys here is a way to
pay that cost only on rows the readout has already flagged.

![FIG-P5-02: Dose-matched ungated versus gated write, at the resolved Qwen3-4B / L34 / dose-200 operating point](figures/fig-p5-02-ungated-vs-gated-h4.png)
**Figure 2.** Dosing every held-out row unconditionally versus dosing only
where the KU readout gate fires, at the same write site and dose. The
ungated arm damages most known-correct rows; the gated arm holds cost near
its floor while giving up only 4.3 points of confab conversion.

On held-out rows, the raw-base Qwen3-4B controller passed every gate.
Gated clean
tightening was 136/185 = 73.5%, Wilson 95% confidence interval [66.7, 79.3],
clearing the >=60%
floor and the lower CI >50% requirement. Known-correct false refusal was
8/258 = 3.1%, CI [1.6, 6.0], clearing the <=5% point floor and <10% upper CI
requirement. A random-direction write on the same fired rows produced only
13/185 clean tighten, and a permuted gate produced 59/258 known-correct cost.
The effect depends on both the boundary-push direction and the KU readout gate.

![FIG-P5-01: Confabulation conversion and known-correct cost for the gated controller against its placebo controls, original and multi-source replication pools](figures/fig-p5-01-headline-conversion.png)
**Figure 1.** Confabulation clean-tighten rate and known-correct false-refusal
rate for the real KU-gated controller against random-direction and
permuted-gate placebos, on the original held-out pool and on the multi-source
replication pool at the same late write site.

The model need not internally choose to consult its readout for the system to
use that readout. The readout can gate an external controller. That is the
selective actuation result the rest of this paper qualifies: at this overdrive
operating point the gate is doing essential selectivity work that the write
itself does not supply, and at a mid-band dose the attribution reverses.

Two further results support this headline without changing it. A
held-out transfer of the same controller design to Qwen3.5-4B's mid-band write
site (hs20, relative depth 0.625, absolute dose 12.608), the operating point
whose confirmatory naming experiment earned it the name IDK switch, reproduced
the decoupling out of sample: fired-confab refused 872/1286 = 0.678 (Wilson
[0.652, 0.703]), well-formed 1256/1286 = 0.977, and known-correct false
refusal 14/360 = 0.039, with both placebo legs intact. Separately, the
raw-base Qwen3-4B headline survives a decode-robustness check: under
temperature-0.7 sampled decoding with majority-vote aggregation across five
seeds, pooled confab clean-tighten conversion is 643/925 =
69.5%, above the 63.5% floor in every individual seed, with known-correct cost
at 60/1290 = 4.65%.

![FIG-P5-03: Confabulation conversion and known-correct cost under temperature-0.7 sampled decoding across five seeds](figures/fig-p5-03-h3-sampled-decode.png)
**Figure 3.** The greedy-decode headline reproduced under temperature-0.7
sampled decoding with majority-vote aggregation, per seed and pooled, for
both confabulation conversion and known-correct cost.

### 4.6 J-space localizes a better write site

The gated controller still raised a mechanistic question:
where should a write occur? The inherited boundary-push write site was an L34
residual-stream direction. A Jacobian-lens characterization (Gurnee et al.,
2026) asked whether this site lies inside or outside the model's
workspace-like verbalizable band.

The instrument passed a correctness smoke: the final-layer J-lens closely
matched the direct unembed baseline over 1000 prompts, with mean cosine 0.9811,
mean top-10 overlap 0.82, and top-1 match 3/5 over five random directions. The
direction-verbalization read then found that
boundary-push-like directions verbalized as first-person,
absence, error, and impossibility tokens, while the known-unknown direction
verbalized more as answer/reply tokens. That readout says something about what
the direction is: a direction that verbalizes toward answer/reply tokens is
tracking answerability, not a self-directed uncertainty state, and a later
experiment on an out-of-population error class characterizes it the same way,
closer to unanswerability recognition than to self-directed uncertainty. The
layer profile localized a workspace-like band to hs23 through hs29, peaking at
hs26. The inherited L34 direction corresponds to hs34, just after that band.

The first causal layer sweep at a fixed absolute dose stopped at its
instrument-validity stop rule because dose 200 collapsed hs23
and hs26, the coherence collapse that additive steering incurs once its
magnitude leaves the range the residual stream tolerates (Dang and Ngo, 2026).
Dose calibration on the fit split alone fixed that: usable
non-collapsing setpoints were recovered at hs23=25, hs26=75, hs29=125, and
hs34=175. The held-out contrast then supported the layer-site hypothesis. Over
443 held-out rows, hs23 (rd 0.639) achieved 165/185 clean refusals (89.2%)
versus hs34 (rd 0.944)
123/185 (66.5%), a +22.7 point improvement. Known-correct cost rose only from
7/258 (2.7%) to 9/258 (3.5%), a +0.78 point delta. hs34 remained viable, but it
was not optimal.

![FIG-P5-04: Dose-response curve for the late write site (Qwen3-4B, hs34), fit-split calibration sweep](figures/fig-p5-04-dose-response.png)
**Figure 4.** Confabulation clean-tighten rate, known-correct cost, and
collapse rate on dosed rows across the fit-split calibration dose ladder at the
late write site, with the selected setpoint marked.

The late write site was not dead, but it was suboptimal on the pool that
produced this contrast. Writing near the workspace-like band made the same
regulated boundary push substantially more effective there. This is a second,
independent route to the same practical conclusion Billa (2026) reaches on
binary concept families, that the standard middle-layer heuristic and the
probe's own best layer are both poor guides to where a write will land, and
that a readout of what the model is prepared to verbalize is a better one.

That +22.7 point margin is pool-dependent, and two same-model replications on
fresh confabulations measure the dependence. On a pool drawn from a single
source, the late reference site refuses 94.1% of 306 rows, which leaves 5.9
points of arithmetic headroom against the 10-point bar; the best
mid-band layer there, hs29, beats it by 5.6 points, a miss driven
by the ceiling rather than by an absent effect. On a pool mined from three
independent sources, the reference falls to 73.8% of 221 confabulations, well
off ceiling, and the mid-band advantage returns at close to its original size:
hs29 reaches 92.8%, a 19.0 point gain, with 42 of the 221 rows breaking toward
the mid-band write on a paired comparison and none breaking the other way
(exact paired test, p = 4.5e-13). Known-correct cost there is 2.8% mid-band
against 1.4% late, a 1.4 point gap that is also an absolute doubling. The
layer-site advantage is real and direction-stable on raw-base Qwen3-4B, and
its magnitude cannot be read off a reference site sitting near its own
ceiling.

![FIG-P5-05: Read-only J-lens workspace band versus write-site behavioral effect across three disjoint pools](figures/fig-p5-05-localization.png)
**Figure 5.** Left: the read-only Jacobian-lens effective-dimension profile
locating the workspace-like band and the late write site relative to it.
Right: confabulation clean-tighten rate by write site on the original pool
and both same-model replications, showing the direction of the mid-band
advantage holds across all three while its magnitude and within-band
ordering are pool-dependent.

### 4.7 Token-targeted J-space writing is real but redundant

Finally, we tested a more literal J-space idea: build a hidden-state direction
that raises natural refusal tokens and lowers answer/reply continuation tokens.
The token bundle was fixed and audited before held-out evaluation. Positive
targets included refusal pieces such as `I`, `know`, `cannot`, `unable`,
`unknown`, and `insufficient`; negative targets included English answer/reply
tokens and Chinese answer/reply tokens that appeared in the J-lens readout, such
as answer/reply forms.

At the dose selected on the fit split, the token-target direction wrote accurately and safely. It
was also non-inert: alone, it converted 88/185 confab rows into clean refusals
(47.6%). But it did not improve the already strong hs23 boundary push (dosed
write). The boundary push alone reached 165/185 = 89.2%; adding the
token-target direction on top of it reached 166/185 = 89.7%, only +0.54
points. Known-correct
cost increased by only +0.39 points, so safety was not the issue. The issue was
redundancy: the natural token-target write added one extra cleaned confab row on
top of a controller that was already doing the job.

Verbalizable token directions can be real actuators without being useful
additive controllers. A direction that points toward refusal tokens is not
automatically a better policy intervention. One reading of the redundancy is
that the boundary-push write is already routing through the same pathway: clamping
the logits of refusal and compliance tokens to their unsteered values
collapses steered refusal from 86.5% to 26.0%, evidence that steering acts on
this behavior largely through token emission probability rather than upstream
reasoning (Sun et al., 2026). If the boundary push is already moving those
token logits, a direction built to move them explicitly has little left to
add.

A wider screen for other behavioral directions that might actuate the same way
promoted none of its candidates. Its positive control confirmed the lever
itself was live, converting 79 of 80 confabulation rows into coherent refusals
while negative and random controls stayed near floor, and every apparent
candidate beyond it dissolved into one of three artifacts: malformed-output
scoring, under-dosed random controls, and off-manifold overdrive. Those three
are the failure modes a control has to be built against, and they recur in the
cross-family work below.

### 4.8 What replicates across families, and what does not

Everything above runs on the Qwen lineage. Does the same gated boundary push
work on other model families, and how would we know? Steering interventions are
known to transfer poorly, with several methods failing to reproduce their
headline effect on the majority of model-task pairs once evaluated across
dozens of models (Queiroz Da Silva et al., 2025), so this was a real test
rather than a formality. It asked whether the same KU-gated boundary push,
refit at each family's own atlas-located workspace-band site, actuates refusal
on Llama-3.2-3B and Mistral-7B-v0.3.

The behavioral gates replicate on mistral, under an instrument built to catch
this family's own abstention idioms. The three fixed refusal forms the narrow
detector looks for do not count them, so mistral is scored on fresh held-out
rows under the wide two-instrument stack, the widened pattern detector plus the
blinded context-free adjudication lane. Under that stack the mistral controller
clears both behavioral gates. Fired-confab adjudicated refusal is 911/1303 = 0.699 (Wilson
95% CI [0.674, 0.723]) against a 0.60 floor, well-formedness holds at 0.987,
and known-correct false refusal is 2/382 = 0.0052 (CI [0.0014, 0.019]) against
a 0.05 ceiling. Those two legs have since reproduced exactly on every re-test
of that operating point.

Direction-specificity does not clear, and it fails at the strongest form we
have tested it in. The test is a ratio: the gated arm's lift in confabulation
abstention over its undosed baseline must be at least three times the largest
lift a magnitude-matched random direction produces at the same site and dose.
The gated lift is +40.9 points (baseline 375/1312 = 0.286, gated 911/1312 =
0.694). The largest random lift across fifteen fresh seeds is +20.3 points,
and across the three seeds used for the ratio test it is +21.8, which
puts the ratio at 1.87 against a 3.0 floor. That failure survives every
alternative construction available to it: 1.91 scoring the automatic detector
alone, 2.89 using the mean of the random seeds rather than their maximum, and
a pre-recorded adversarial audit across six attack surfaces (the random
directions have cosine similarity at most 0.015 to the fitted direction, are
magnitude-matched to it at the mechanism level within 0.004, and are scored on
identical populations with exact arithmetic). An independent test at a
different site and dose lands in the same place: the mid-band factorial's own
direction-specificity leg reaches 2.03 on mistral against the same 3.0 floor,
where qwen passes at 7.27. Mistral is readable everywhere we have looked and
is not shown actuable by a direction-specific write at any site we have tried.

The reason a random direction can carry that much of the effect starts with
the baseline it is measured against, and that baseline is family-graded.
Wide-instrument confabulation abstention with no intervention at all is
0.104 on Qwen3.5-4B, 0.164 on Llama-3.2-3B, and 0.280 on Mistral-7B-v0.3,
against 0.044, 0.036, and 0.159 under the narrow canonical detector: undercounts
of 6.1, 12.9, and 12.2 points. A flat, small, symmetric no-op tolerance is the
wrong instrument for a family whose baseline sits at 0.280, and it was
inherited from a Qwen-scale world where the baseline looked like zero.

The stronger measurement is the shape of the random-direction null itself. For
each family, a census wrote the frozen random direction as an erase-write to
that family's own certified placebo setpoint, so every seed within a family is
a draw at one fixed magnitude, and drew fifteen fresh random seeds per family,
scored on a fixed 300-row paired confabulation subsample through one blinded
context-free adjudication pool. The criterion was fixed before the run: a
family's placebo sign holds if at least 80% of its seeds carry that sign, with
a bootstrap 95% lower bound above 0.50 and a median at least 3.0 points in
that direction; it is dismissed as seed noise if 60% or fewer carry it or if
the interquartile range spans zero.

None of the three families is behaviorally inert under a matched-magnitude
random write, and the signs disagree. Qwen suppresses hedging, robustly: 14 of
15 seeds negative (bootstrap 95% CI [0.80, 1.00]), median -6.0 points,
interquartile range [-6.83, -3.67]. Mistral recruits hedging, at exactly the
80% boundary: 12 of 15 seeds positive, median +7.0 points,
interquartile range [+1.17, +13.67], which does not span zero. Llama, run as a
negative control with no committed sign and expected to center near zero,
suppresses instead: 12 of 15 negative, median -7.67 points, interquartile
range [-9.33, -2.00]. The interquartile ranges are 3 to 13 points wide, so a
single seed drawn from any of them reports its family's sign more reliably
than its magnitude.

![FIG-P5-07: Matched-magnitude random-direction placebo null distributions across fifteen fresh seeds for three model families](figures/fig-p5-07-placebo-census.png)
**Figure 7.** Matched-magnitude random directions are not behaviorally inert
in any of the three families, and their sign differs by family: across fifteen
fresh seeds per family at each family's own certified placebo setpoint, Qwen
suppresses confabulation hedging (median -6.0 points, 14 of 15 seeds
negative), Llama suppresses it despite having been run as a null control
(median -7.67, 12 of 15), and Mistral recruits it (median +7.0, 12 of 15
positive, exactly the 80% boundary).

Two cautions travel with that picture. Mistral's verdict is a boundary
verdict: its margin over an indeterminate call is a single seed, its three
weakest positive seeds (+1.0, +1.33, +1.67) are individually within paired
noise, and the result is sensitive to the mined-idiom vocabulary the widened
detector uses. And llama's distribution was measured at its read-selected
site, relative depth 0.714, while llama's own gated write ran at a shallower
site, relative depth 0.607; read-optimal and actuate-optimal depth are
separately measured quantities here, so the llama null is a null at the read
site rather than at the write site.

That random writes move abstention at all has a mechanical explanation and a
methodological consequence. Abstention is causally reachable at matched
magnitude by at least two routes: through the represented known-unknown state,
which is what the gated true-direction write uses, and through nonspecific
computational disruption, which is what a random direction of the same
magnitude supplies. An adversarial re-read of the random arm's dose-induced
refusals found them to be coherent, well-formed abstentions on rows that
carried committed answers at baseline, not degraded text. Because a random
write can manufacture genuine refusals, a raw increase in abstention rate
cannot by itself certify that an intervention is coupled to the model's own
known-unknown readout. Certifying that coupling requires the selectivity
evidence this paper already leans on, moving target failures without imposing
refusal on known-correct rows, together with a specificity margin referenced
to the family's own measured null rather than to zero. The same problem has
been reported from two other directions: random, semantically empty directions
reliably break refusal (Korznikov et al., 2025), and a random vector
orthogonal to a fitted steering vector can be behaviorally indistinguishable
from it, which makes the fitted vector non-identifiable as the cause of its
own effect (Venkatesh and Kurapath, 2026). A measured per-family null is the
operational answer we can offer to that problem.

For qwen, the measured null cuts the other way and strengthens the
specificity reading at one operating point. Because qwen's placebo response is
suppressive, the IDK switch's recruitment of refusals is sign-opposed to the
family's response to a nonspecific perturbation: a random write at matched
magnitude pushes qwen hedging down, while the gated write pushes it up. A
confound that a placebo is meant to catch would push the same way as the true
write, and this one pushes the opposite way. That comparison is measured at
the Qwen3.5-4B mid-band operating point (hs20, relative depth 0.625) where the
census placebo was dosed, and it licenses a specificity claim there. Whether
it transfers to the raw-base Qwen3-4B late-site controller of Section 4.5, a
different model and a different write site, is unmeasured.

The family-level sign is not evenly distributed inside a family. Broken down
by question type within the known-unknown pool, one subtype carries qwen's
entire suppression (future-unknown items, -24.7 points against -2.8 or smaller
elsewhere) and is also mistral's single largest recruitment delta (+11.8
points): the extreme mover in both families, in opposite directions. That this
subtype is the extreme mover is at least consistent with its construction. The
dataset's authors report future-unknown as the category models classify most
easily, because it carries distinctive temporal linguistic cues the other
categories lack (Amayuelas et al., 2023), so it is the subtype where a row's
unanswerability is most legible from surface form alone. Question type does
not explain away the cross-family sign difference at the family level, but the
sign is not homogeneous within a family either.

The design rule that follows is the one this paper would ask a successor to
adopt: register the placebo criterion against the family's own measured null
distribution, using a percentile-based tolerance or a sign-opposition
criterion (does the true write move behavior opposite to that family's
nonspecific-perturbation response), rather than against a flat symmetric band
or a single random seed. The three distributions above supply that null at
fifteen seeds for the three families they cover.

One qualification reaches backward from here. The random-direction and
permuted-gate controls behind the Section 4.5 headline (13/185 clean tighten
for the random direction, 59/258 known-correct cost for the permuted gate) and
behind the Section 4.6 layer-site contrast were graded under the narrow
detector, not the wide two-instrument stack, and neither has been re-scored
under it. Given the undercount margins above, and given that qwen's own
wide-instrument placebo response at a different operating point is suppressive
rather than confounding, there is no positive evidence that those specific
controls are compromised. There is now a standing reason not to treat a small
narrow-detector placebo delta as automatically clean: it should be read as
provisional until re-checked under the wide instrument, and certainly before
any of these results is promoted from exploratory to headline.

### 4.9 Gemma's inertness was a depth-coverage artifact, not a family-specific null

Was Gemma-4-E4B a fourth family that simply does not actuate, or a family that
had never been written to in the band where every other family does? Every
prior write attempt on this substrate sat at relative depth 0.81 or deeper, on
an architecture whose upper 18 blocks read their key and value tensors from two
frozen donor blocks rather than computing their own. Nothing had ever been
written into the shallow half of the model.

A depth ladder on the unmodified model, key-value sharing left on, answers the
coverage question. Actuation is present, shallow, and uneven. At relative
depth 0.357 the fitted known-unknown direction clears both held-out
behavioral gates with the widest margin measured on this family, 78.6% clean
tightening (Wilson 95% CI [71.8, 84.1]) against a 1.1% known-correct
false-refusal cost. Two sites just below the midpoint, relative depth 0.429
and 0.476, fail the clean-tightening floor outright at 44.6% and 40.5%.
Relative depth 0.524 clears both gates again at 58.9% clean tightening and
0.4% cost. The site immediately downstream of both donor blocks,
relative depth 0.571, clears them a third time at 73.2% clean tightening and
3.3% cost. Relative depth 0.595 clears them at 79.2% (CI [72.4, 84.6]) and
3.3% cost (CI [1.8, 6.2]). The two deepest sites in the cross-family operating
range, relative depth 0.619 and 0.643, never reach a usable dose at all: their
best fit-split tightening rates top out at 37.5% and 25.0% against a 50%
usability floor. Gemma's reputation as the one family that does not actuate
was built entirely on sites deeper than any of these.

![FIG-P5-08: Gemma-4-E4B depth ladder, actuation outcome versus relative depth with pass/fail per site](figures/fig-p5-08-gemma-depth-ladder.png)
**Figure 8.** Gemma-4-E4B is not architecturally inert, and where it actuates
depends on depth: relative depths 0.357, 0.524, 0.571, and 0.595 clear the
held-out clean-tightening and known-correct cost gates, 0.429 and 0.476 fall
below the tightening floor, and 0.619 and 0.643 never reach a usable dose.
Direction-specificity does not follow from behavioral clearance, and no site
tested for it reaches the three-fold floor: the two sites above the
key-value sharing seam fail at effect ratios of 1.139 and 1.279, and the one
below it has no defined ratio because every accepted random draw produced zero
lift.

Direction-specificity is where that picture stops. Both above-seam sites that
reached a usable dose failed their placebo control: at relative depth 0.571
the single worst magnitude-matched random draw reproduced 88% of the fitted
direction's effect, and at 0.595 the worst of five draws reproduced 78%, an
effect ratio of 1.279 against a three-fold floor. Neither may be
cited as a specific effect. The two shallow passes do not repair that: the
0.357 site carried the behavioral gates only, with no placebo arm run
at all, and the 0.524 placebo is a degenerate pass in which all five accepted
random draws produced exactly zero lift, which the design requires reporting
under the degenerate label rather than as a large specificity ratio. What the
ladder establishes is that gemma clears behavioral gates in a shallow band.
What it does not establish is that any of those writes is direction-specific.

The direct test of the seam mechanism, the same write with key-value sharing
switched off, could not run. A precondition check comparing the undosed model
in both conditions found that turning sharing off breaks it before any write
is applied: known-correct rows that were perfectly well-formed under sharing
on (0/180 malformed) became entirely malformed under sharing off (180/180,
Newcombe 95% CI on the difference [0.970, 1.0], against a 0.05
cap), and mean per-token negative log-likelihood on the reference completions
rose from 3.53 to 12.33. A parallel calibration sweep at the original
above-seam site found no usable dose in either sharing condition, so the
deep-site null that gave gemma its reputation reproduced unchanged alongside
the new shallow-band result.

That leaves the coverage question closed and the mechanism question open, for
a structural reason rather than a want of data. Every site of the cross-family
operating range above gemma's seam has now been measured, and none produced
direction-specific actuation. But across that whole band relative depth and
sharing status are the same variable on this architecture, so no result there
can say which of the two produced the falloff: gemma's decay with depth could
equally be the generic decay every other family here shows past its own
productive band, with no seam mechanism required. Isolating the seam still
requires a working sharing-on against sharing-off contrast, and the one built
for it broke the substrate it was meant to probe.

---

## 5. Synthesis: The Actuation Map

Taken together, the channels sort by how far each one gets before it breaks.

| Channel or operating point | Outcome |
|---|---|
| Within-generation text injection | Fails; a small gate-side trickle under the strongest first-person rule |
| Confabulation-push activation write | Fails; the readout moves by the commanded amount, the behavior does not move at all |
| High-authority system prompt | Moves behavior, by instruction compliance rather than own-readout consultation |
| Reward equal to the model's own probe score | Fails; the true-sensor arm is less congruent with its own readout than a permuted control |
| Unconditional write, overdrive dose (Qwen3-4B, L34) | Actuates but is not selective: 60.1% of known-correct rows damaged |
| KU-gated boundary push, overdrive dose (Qwen3-4B, L34) | Works: 73.5% clean tightening at 3.1% known-correct cost |
| KU-gated boundary push, mid-band dose (Qwen3.5-4B hs20; Mistral hs16) | Works; the write self-sorts and the gate governs cost rather than supplying selectivity |
| Write site, mid-band versus late (Qwen3-4B) | Mid-band wins by 22.7 points at +0.78 points of cost |
| Token-target write (Qwen3-4B, mid-band) | Real on its own (47.6%), redundant on top of the boundary push (+0.54 points) |
| Cross-family, Mistral-7B-v0.3 | Benefit and cost gates pass under a blinded wide instrument; direction-specificity fails at every site tested |
| Cross-family, Llama-3.2-3B | A gated write at its atlas site failed on format collapse before the refusal floor, and has not been re-run under the wide instrument |
| Cross-family, Gemma-4-E4B | Behavioral gates pass at four of the eight depths tested; no tested site reaches the direction-specificity floor |

Four readings come out of that grid. The first is the read/write split itself:
every channel that routes the readout into behavior through text, authority, or
reward either fails outright or moves behavior for a reason other than the
model consulting its own state, and it fails on substrates where the same
readout separates known from unknown items at near-ceiling accuracy. The
second is that selectivity is not a property of the direction. At an overdrive
dose the identical write damages most known-correct rows unless a gate holds
it off them; at a mid-band dose the same write already sorts by content and
the gate's measured contribution to selectivity is 0.148 on qwen and 0.129 on
mistral, both under the 0.20 floor set for it, while its contribution
to cost control is what keeps false refusals near their floor. One mechanism,
two regimes, opposite attributions.

The third is that where the write lands is as consequential as what is
written. Moving the same regulated boundary push from just past the
workspace-like band into it buys 22.7 points of confabulation tightening on
Qwen3-4B for less than a point of known-correct cost, and the advantage
survives replication on a harder pool once the reference site is pulled off
its own ceiling. On gemma the same lesson arrives as a boundary: the
family clears the behavioral gates across a band that stops well short of the
depths the qwen write sites sit at, and every site above its key-value sharing
seam either fails direction-specificity or never reaches a usable dose.

The fourth is the scope of the recipe, which the cross-family work makes into
a measurement rather than an assumption. Benefit and cost gates travel:
mistral clears both under a blinded instrument at 69.9% adjudicated refusal
and 0.52% known-correct cost. Direction-specificity does not: it fails on
mistral at three independent operating points, and on gemma at both above-seam
sites where a usable dose existed. The reason it fails is measurable rather
than mysterious, and it is the last reading: a matched-magnitude random
direction is not behaviorally inert in any family tested, and its sign is a
family property, suppressing hedging in qwen and llama and recruiting it in
mistral. Any future direction-specificity claim has to be checked against
that measured null.

The controller these results support is the five-step recipe stated in the
introduction. It is closer to a control system than to a prompt: the model's
policy does not need to endorse or understand the sensor, because the
controller is what uses the sensor.

---

## 6. Discussion

### 6.1 Why "presence implies use" fails

A model can carry useful epistemic information that its own generation policy
never uses, and the results above locate at least three separable bottlenecks
between the two:

- channel bottleneck: putting the signal into a low-authority text channel
  may not make it causal;
- policy bottleneck: high-authority text may move policy by obedience rather
  than by state alignment;
- write-site bottleneck: a residual direction may be readable at one layer
  and writable at another.

This explains why a probe can be near-perfect while steering is flat, and why a
prompt can change refusal behavior without improving readout congruence. The
write-site bottleneck in particular is not specific to epistemic directions: a
probe above 93% accuracy at every layer of a model can still produce near-zero
steering effect at its own best layer, with steering success tracking
alignment to the model's unembedding readout instead (Billa, 2026).

### 6.2 Why the gate matters, and why its role changes with dose

Whether the boundary push (dosed write) needs the gate to be selective is not
a fixed property of the direction; it depends on where the dose lands relative to
each row's commitment margin, the minimum perturbation dose that flips that
row's behavior to abstention. At an overdrive dose, above typical
known-correct margins, the write crosses everything: applied indiscriminately
at Qwen3-4B / L34 / dose 200, it damages 60.1% of known-correct rows, and the
gate is the sole reason the controller does not. At a mid-band dose, above
typical confab margins but below typical known margins, the write is already
content-selective: a permuted-gate control
reaches confab abstention 0.550 qwen / 0.600 mistral against the true gate's
0.689 / 0.694, so most of the abstention lift survives with no gate at all.
The gate's residual mid-band role is real but modest: its own contribution to
selectivity is 0.148 qwen / 0.129 mistral, both sub-floor against a 0.20
floor, plus cost governance that does matter against the 0.05
ceiling: known false refusal under the true gate is 0.042 qwen /
0.005 mistral versus 0.050 / 0.039 under a permuted gate. This is still the
same separation used in ordinary control systems, sensor, controller,
actuator, but which part of the system supplies selectivity is
dose-dependent: at overdrive the controller (gate) does the selecting, and at
mid-band the actuator (write) already discriminates while the controller
mainly tightens cost. Read as a dosing problem this is the same
accuracy-versus-effect frontier that work on collateral damage in activation
steering characterizes (Nguyen et al., 2026); the gate is one way of moving
along that frontier without lowering the dose.

### 6.3 Why J-space matters, and where the account is scoped

The J-space diagnostic gives a mechanistic explanation for one repeated pattern:
directions are portable as readouts but fragile as writes. Gurnee et al. (2026)
report that workspace-like properties emerge only in an intermediate band of
layers, with early layers giving noisy readouts and late layers shading into
output preparation. If the reportable or workspace-relevant component of a
concept lives in such a band, late residual writes may be downstream of the
useful broadcast site. The band this paper measures on Qwen3-4B sits later
than the range Gurnee et al. describe, at relative depth 0.64 to 0.81, so the
claim here is that a band of this kind exists and matters for write placement,
not that it is the same band at the same depth. The calibrated
layer contrast supports that account on raw-base Qwen3-4B, but a cross-family
atlas test of the account's own predicted shape did not hold: the
effective-dimensionality profile that motivated
"write near the interior peak" instead peaks early in both llama (layer 4 of
28, 0.14 depth) and mistral (layer 3 of 32, 0.09 depth), not inside the
predicted interior band. The atlas's read panel still delivers a usable,
family-specific interior band where known-unknown, the refusal-versus-confabulation
contrast, and raw-refusal readouts all clear 0.80 held-out AUROC simultaneously (llama layers 15-23,
mistral layers 7-27), so a readable workspace-like band exists in every
family tested, but the specific "write near the eff-dim peak" account is
currently scoped to raw-base Qwen3-4B and should not be read as a
cross-family mechanism claim.

The account has also been measured once on a trained checkpoint, in an
exploratory follow-up whose prediction and failure criterion were fixed before
the run. Two results. First, training reshapes the band rather than erasing
it, and what survives is a narrow band rather than a pronounced one: on a
supervised-fine-tuned-then-reinforcement-trained checkpoint of the same base
model, the raw-base effective-dimension peak at hs26 is suppressed by roughly
a third and the surviving profile is flatter and deeper, with its interior
maximum of 0.00735 at hs29 clearing the band threshold of 0.00675 by a small
margin. Second, the surviving
band did not license a write site. At its rule-selected shallow edge (hs17)
the refusal axis reads nearly as well as at the late site (construction AUROC
0.86 vs 0.87), but full ablation there released none of the over-refusal that
the same operation at the late site removes (0 of 168 rows released, against
163 of 168 at L35 on the same rows) and instead induced refusal on 48 percent
of items the model previously answered. A minus-2-sigma displacement at the
same site instead dropped refusal to 0.714 and recovered correct answers on
21 percent of those rows, so at mid-depth removal and displacement are
different operations: the direction is entangled with signal that answering
requires. Read location and edit location come apart on the same checkpoint
and the same axis. We read the J-space band as evidence about broadcast, not
as a site license for writes, and the dosed-write mid-band results elsewhere
in this paper do not imply that ablation transfers to those depths.

### 6.4 Limits

This is an exploratory paper. The largest claims are qualitative and mechanistic,
not population effect-size estimates. Key limits:

- many actuation results are single-model or single-family;
- the strongest positive J-space layer-site result is currently surface-local to
  raw-base Qwen3-4B bf16, and the one trained-checkpoint test so far (Section
  6.3) found the band reshaped and its rule-selected mid-band site readable
  but not ablatable, so J-space profiles should not be used to pick ablation
  sites on trained checkpoints;
- reward-channel evidence is single-seed;
- token-target J-space writing has only tested the natural observed token bundle,
  not dense or multilingual alternatives;
- the random-direction and permuted-gate controls in Sections 4.5 and 4.6 were
  graded under the narrow refusal detector and have not been re-scored under
  the wide two-instrument stack used for the cross-family work in Section 4.8;
  a flat, family-agnostic placebo tolerance is now known to be miscalibrated
  to at least one family's baseline hedging rate;
- random-direction placebo response is high-variance across random seeds at
  matched magnitude. At one fixed mistral operating point, three fresh seeds
  produced confabulation lifts spanning -7.4 to +21.8 points, a 29-point
  spread from seed choice alone, and high variance is the documented condition
  of steering effects generally rather than a quirk of this control:
  per-input steerability varies widely within a single concept, and on several
  datasets roughly half of inputs are anti-steerable, with the same direction
  moving behavior the opposite way (Tan et al., 2024; Braun et al., 2025,
  report anti-steerable fractions from 3% to 50%). Any placebo delta from a
  single seed is one draw from a wide distribution rather than a family
  constant. The fifteen-seed census in Section 4.8 measures those
  distributions directly, so the caution stands while the nulls themselves are
  now measured;
- every direction in this paper is fit once, statically, on single-turn rows,
  and applied without re-estimation. Linear representations are not guaranteed
  to be stable under that assumption: factuality directions have been shown to
  invert sign over a few turns of role-cued conversation, with steering along
  a statically fitted direction producing opposite behavioral changes at
  different points in the same conversation (Lampinen et al., 2026). Nothing
  here tests multi-turn or context-shifted deployment;
- the controller has a coherence and saturation ceiling on an out-of-population
  error class. On world-known items, where the error is a confidently wrong
  answer rather than acknowledged ignorance, steering the fitted direction
  tips only 51/400 (12.75%) of confabulations into refusal inside a
  coherence-valid dose band, and doses at or above three times the reference
  drive degenerate generation before any refusal registers. This ceiling is
  scoped to the hs20 mid-band lineage tested there; whether the L34
  overdrive headline in Section 4.5 shows the same ceiling on this
  population is untested;
- a mid-generation write, timed to the token position where the model
  commits to an answer rather than the pre-generation anchor used throughout
  this paper, was checked for instrument validity before any behavioral run,
  and neither of two candidate implementations certified. One harness's
  optimized decode path never routed its mid-generation forward passes
  through the hooked module at all across all 25 checked prompts, which
  identifies an earlier answer-window result as an instrumentation artifact
  rather than a causal null; that result is not reported anywhere in this
  paper. A second, plain-inference harness fired
  the hook on every decode step and landed the write within 0.2 to 0.4
  percent of the commanded magnitude on every position checked before the
  intervention changed the model's own token choice, but its cross-trajectory
  readback stopped isolating the write once the steered and unsteered token
  sequences diverged, so it also does not certify. No mid-generation steering
  evidence appears anywhere in this paper.

Every experiment reported above fixed its predictions, falsifiers, gates, and
controls before it ran, and no threshold was retuned afterward. What that
machinery covers is uneven, and the unevenness is itself a limit. The Section
4.5 headline, its dose-matched comparison, its held-out mid-band transfer and
its sampled-decode replication each carry gates fixed before their runs, as do
the cross-family and depth-ladder results in Sections 4.8 and 4.9. The reward
and text-injection channels are single-seed. The Section 4.2 push, the Gemma
shallow-band passes, and the correctness-axis measurements in Section 6.5 are
exploratory, single-model, and unreplicated. Reading the cross-family sign map
against each family's baseline hedging rate is descriptive: with three
families it is a hypothesis for a future test, not a result. Section 6.6
reports a confirmatory replication whose prediction missed. Appendix A names the governed document behind each claim and its
adjudicated status.

The margin account that motivates the operating-point framing used here, that
each row has a commitment margin and that a dose lands above or below it, is
used qualitatively only. No margin measurements of our own appear anywhere in
these results, and the geometry of those margins is future work.

### 6.5 What the next study has to test

One asymmetry should shape how the next study is designed. The known-unknown
(answerability) axis this paper's gated write is built on reads at near-ceiling
accuracy on Qwen3-4B and, in the readout work that established the gate and
dial pipeline, transfers across four model families at AUROC 0.997 to 0.998
with no per-family refitting (Rosenbaum, 2026d). Knowledge-awareness directions
have shown a related portability elsewhere, transferring from a base model's
own feature dictionary into the chat model's refusal behavior (Ferrando et
al., 2024). The correctness axis read at the answer token does not carry the
same portability, even within one model's own training trajectory, and we
measured that directly in two experiments of our own. The first tracked the
correctness direction's rotation across a model's own training checkpoints and
found none of the answerability axis's single-rotation-then-stable pattern:
cosines of 0.19, 0.45, and 0.33 across the three training transitions, none
reaching the 0.85 stability the answerability axis shows at the later two.
Worse, the fitted correctness direction is only weakly pinned down by the data
in the first place: refitting it on two disjoint halves of one checkpoint's
own data agrees at 0.17 cosine, next to a readout accuracy that stays flat
near AUROC 0.80, so at these sample sizes the instrument cannot separate
genuine rotation from an unidentified direction. The second asked whether a
shared subspace, rather than a single axis, explains the correctness readout's
partial transfer between checkpoints, and found at most one weak shared
direction, with the transferable signal diffuse across the base model's
activation span rather than concentrated in any small discriminative subspace;
its own reliability limb turned out to be unreachable for any signal, which
makes it an instrument-limited null rather than an answer. Both are
exploratory, single-model, and not cross-family claims. Together they are a
reason to expect the two readouts to generalize differently: this paper's
gated write rides the crisp, portable answerability axis, and any future
actuation work built on the correctness axis instead should be treated, going
in, as a separate and probably harder generalization problem rather than
assumed to inherit the answerability axis's portability. That is a hypothesis
for the next study to test, not a result it can report.

Recommended escalation, in order of priority:

1. Same-model replication: re-run the gated mid-band versus late layer-site
   contrast on a fresh held-out split or newly staged rows for Qwen3-4B bf16.
   Section 4.6 already reports two such replications for the layer-site
   contrast itself.
2. Cross-model workspace localization: run the J-lens profile and direction
   verbalization on at least one Qwen size neighbor and two non-Qwen families.
3. Mistral direction-specificity, at a different operating point. Every
   mistral test so far ran at one fixed site and dose (hs16, relative depth
   0.500, 12 sigma), where benefit and cost reproduce cleanly and
   direction-specificity fails because the random-direction response at that
   site is both large and high-variance. Repeating that operating point is not
   expected to change the outcome, and neither is drawing more random seeds:
   the maximum random lift over fifteen seeds (+20.3 points) is close to the
   maximum over three (+21.8). A future attempt needs a different write site
   or dose where the random-direction response is smaller or more stable, with
   its placebo criterion set against that family's measured null
   distribution.
4. Llama's gated write, which has not yet produced a scored held-out pass
   under the wide instrument. Its placebo null is now measured and suppressive
   (12 of 15 seeds negative, median -7.67), so llama is not a null control and
   a future attempt cannot register a flat tolerance against zero. Note also
   that the llama null was measured at its read-selected site rather than at
   the shallower site where its own write has cleared gates.
5. Per-family write sites rather than one universal depth. A prior
   cross-family attempt at a fixed late write site across qwen, llama,
   mistral, and a larger qwen tier was not promoted: every launched arm
   stopped at a pre-outcome dose-viability rule before held-out scoring (peak
   fit-split clean tightening 32.6% qwen small tier, 18.4% llama, 0.0%
   mistral, 5.75% qwen mid tier, all below the 60% floor), while a companion
   audit found the refusal-versus-confabulation encoding linearly readable in
   all four families at 0.84 to 0.99 AUROC. The direction reads everywhere
   tested and actuates at that site only in the Qwen lineage, which turns the
   open question from whether the controller works cross-family into which
   family-relative site it works at. The family atlas (Section 6.3) already
   supplies candidate sites for llama and mistral.
6. Gemma's key-value sharing seam: the coverage question is closed (Section
   4.9) and the mechanism question is not. It cannot be settled by writing to
   more above-seam sites, because relative depth and sharing status are the
   same variable across all of them; it needs an ablation that suppresses key
   and value sharing without breaking the model, which the one built here did
   not manage.
7. Dense-token screen: separately screen abstract or multilingual token
   bundles before any causal hybrid run. Do not alter the natural-token result
   post hoc.
8. Adjacent behavioral axes. An interim pilot on an answer-sycophancy
   direction found it readable while its actuator failed to beat a matched
   control. It is not a governed result and carries no evidence here, but the
   pattern it points at, a readable behavioral direction that does not become
   a clean actuator, is the one this paper documents on epistemic directions,
   and it is worth a dedicated test on its own terms.

The success criterion for the next paper-quality claim should be stricter than
this one: same-model replication plus at least two-family support for the
workspace-band advantage, with pre-stated cost guards and placebo controls
set against each family's measured null.

### 6.6 Training does not remove the causal handle

Every result above is staged on an untrained substrate by design: the central
claim is that gated actuation needs no training at all, so frozen
off-the-shelf checkpoints are where that claim has to be demonstrated. The
obvious objection is that training might overwrite the mechanism once it
exists, which would leave the untrained result irrelevant to deployed models.
A confirmatory replication tested that on one seed of a
supervised-fine-tuned-then-reinforcement-trained checkpoint of the same base
model, running the whole chain on that seed's own lineage with no artifact
reused from any other seed.

The handle is still there. Ablating the refusal axis, the direction fit as a
refuse-versus-answer contrast among questions the model can answer, releases
45.7 points of known-item over-refusal, and 29.2% of the rows it releases come
back as correct answers rather than as different failures. Specificity is
close to intact on the control population: 1.3% of previously answered
known-correct rows are newly refused, against a 7.2 point drop in the rate at
which that population answers correctly. A dosed displacement along the same
axis, rather than removing it, lands in nearly the same place.

What that supports is narrow, in two directions. The size of the release does
not carry across seeds of the same recipe. The prediction here was
that ablation would leave post-ablation over-refusal at or below 0.10; it
landed at 0.553, past the falsifier line, and a much
larger collapse recorded on a different seed of this recipe is accordingly
treated as specific to that seed. Read the direction of the effect as durable
and its magnitude as unsettled. And the intervention is not this paper's
controller: it is an unconditioned ablation rather than a KU-gated write, on a
trained checkpoint this paper does not otherwise train or evaluate, run on the
archived intervention stack that produced the original result rather than
under this paper's own instrumentation. It also says nothing about
whether abstention can be installed where it is missing on that substrate,
which is a separate question with its own separate evidence. Read together
with the frozen-checkpoint results above, the two substrates bound the claim
in the direction that matters here: training is not required to get causal
leverage over refusal, and it does not appear to remove it either.

---

## 7. Conclusion

Small language models can know internally that they do not know, and external
systems can read that state. Making the model itself use that state is harder.
Text prompts move policy without consulting the readout; rewards train
correlates without congruence; and a readable direction is not automatically a
usable actuator, because what makes it usable is the operating point rather
than the direction. The only clean positive controller here is not a prompt or
a reward but a gated hidden-state intervention, and it needs no training:
read the known-unknown state, write only where the readout fires, and site the
write near the workspace-like layer band, at an overdrive dose where the gate
alone supplies selectivity or at a mid-band dose where the write self-sorts
and the gate mainly holds cost down.

What could still take that apart is specific. The strongest form of the
direction-specificity test already fails on two of the four families here, and
matched-magnitude random directions move abstention in every family measured,
in a family-specific direction. If the qwen controller's sign-opposition to
its own family's random-direction null does not survive a test at the raw-base
operating point, or if a per-family site search fails to recover selective
actuation on mistral and llama, then what this paper reports is a
Qwen-lineage result with a well-characterized instrument attached, not a
recipe. That is the test the next study should try to fail.

---

## References

(Compiled from our literature library as of this writing, and refreshed
whenever a section it supports is revised.)

- Amayuelas et al. (2023). Knowledge of Knowledge: Exploring Known-Unknowns Uncertainty with Large Language Models. arXiv:2305.13712.
- Arditi et al. (2024). Refusal in Language Models Is Mediated by a Single Direction. arXiv:2406.11717.
- Bani-Harouni et al. (2025). Rewarding Doubt: A Reinforcement Learning Approach to Calibrated Confidence Expression of Large Language Models. arXiv:2503.02623.
- Billa (2026). Predicting Where Steering Vectors Succeed. arXiv:2604.15557.
- Braun et al. (2025). Understanding (Un)Reliability of Steering Vectors in Language Models. arXiv:2505.22637.
- Burns et al. (2022). Discovering Latent Knowledge in Language Models Without Supervision. arXiv:2212.03827.
- Cheng et al. (2024). Can AI Assistants Know What They Don't Know?. arXiv:2401.13275.
- Damani et al. (2025). Beyond Binary Rewards: Training LMs to Reason About Their Uncertainty. arXiv:2507.16806.
- Dang and Ngo (2026). Selective Steering: Norm-Preserving Control Through Discriminative Layer Selection. arXiv:2601.19375.
- Ferrando et al. (2024). Do I Know This Entity? Knowledge Awareness and Hallucinations in Language Models. arXiv:2411.14257.
- Gurnee et al. (2026). Verbalizable Representations Form a Global Workspace in Language Models. arXiv:2607.15495. Transformer Circuits. https://transformer-circuits.pub/2026/workspace/index.html.
- Joad et al. (2026). There Is More to Refusal in Large Language Models than a Single Direction. arXiv:2602.02132.
- Joshi et al. (2017). TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension. arXiv:1705.03551.
- Kadavath et al. (2022). Language Models (Mostly) Know What They Know. arXiv:2207.05221.
- Kirichenko et al. (2025). AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions. arXiv:2506.09038.
- Korznikov et al. (2025). The Rogue Scalpel: Activation Steering Compromises LLM Safety. arXiv:2509.22067.
- Laban et al. (2023). Are You Sure? Challenging LLMs Leads to Performance Drops in The FlipFlop Experiment. arXiv:2311.08596.
- Lampinen et al. (2026). Linear Representations in Language Models Can Change Dramatically Over a Conversation. arXiv:2601.20834.
- Li et al. (2023). Inference-Time Intervention: Eliciting Truthful Answers from a Language Model. arXiv:2306.03341.
- Liu et al. (2026). Reinforcement Learning with Metacognitive Feedback Elicits Faithful Uncertainty Expression in LLMs. arXiv:2606.32032.
- Mallen et al. (2022). When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories. arXiv:2212.10511.
- Marks et al. (2023). The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets. arXiv:2310.06824.
- Mohamadi et al. (2025). Honesty over Accuracy: Trustworthy Language Models through Reinforced Hesitation. arXiv:2511.11500.
- Nguyen et al. (2026). Minimizing Collateral Damage in Activation Steering. arXiv:2605.01167.
- Orgad et al. (2024). LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations. arXiv:2410.02707.
- Panickssery et al. (2023). Steering Llama 2 via Contrastive Activation Addition. arXiv:2312.06681.
- Queiroz Da Silva et al. (2025). Steering off Course: Reliability Challenges in Steering Language Models. arXiv:2504.04635.
- Rosenbaum, J. (2026a). The Depths of Ignorance: A Taxonomy, Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in Language Models. Companion paper, this research program.
- Rosenbaum, J. (2026b). Teaching Small Language Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data. Companion paper, this research program.
- Rosenbaum, J. (2026c). Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model. Companion paper, this research program.
- Rosenbaum, J. (2026d). It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models. Companion paper, this research program.
- Shao et al. (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300.
- Slobodkin et al. (2023). The Curious Case of Hallucinatory (Un)answerability: Finding Truths in the Hidden States of Over-Confident Large Language Models. arXiv:2310.11877.
- Sun et al. (2026). Valence-Arousal Subspace in LLMs: Circular Emotion Geometry and Multi-Behavioral Control. arXiv:2604.03147.
- Tan et al. (2024). Analyzing the Generalization and Reliability of Steering Vectors. arXiv:2407.12404.
- Turner et al. (2023). Steering Language Models With Activation Engineering. arXiv:2308.10248.
- Venkatesh and Kurapath (2026). On the Non-Identifiability of Steering Vectors in Large Language Models. arXiv:2602.06801.
- Wen et al. (2024). Know Your Limits: A Survey of Abstention in Large Language Models. arXiv:2407.18418.
- Wollschläger et al. (2025). The Geometry of Refusal in Large Language Models: Concept Cones and Representational Independence. arXiv:2502.17420.
- Zhang et al. (2023). Towards Best Practices of Activation Patching in Language Models: Metrics and Methods. arXiv:2309.16042.
- Zou et al. (2023). Representation Engineering: A Top-Down Approach to AI Transparency. arXiv:2310.01405.

## Appendix A. Traceability Map

Each reader-facing claim above, with the governed document behind it
and its adjudicated status.

| Paper claim | Governed source | Status |
|---|---|---|
| Direct activation/text "turn the probe around" cells did not move behavior at registered gates | `experiments/causal-confidence-steering/AMENDMENT.md` Section 7 | Falsified / channel shut |
| First-person natural-language confidence framing did not open the text channel at useful magnitude | `experiments/first-person-injection/AMENDMENT.md` Sections 7-8 | Ambiguous-leaning negative |
| A calibrated push against a purpose-built confabulation-push direction moved the readout by the commanded amount (read-back ratio 1.0008) but converted 0/116 confabulations; permuted-control kill difference was a precise zero (bootstrap CI [0.00, 0.00]); both reach and specificity gates missed and the registered falsifier fired | `experiments/radial-anti-propensity-steering/AMENDMENT.md` Outcome | Registered null; falsifier fired |
| KU-readout-coupled activation write carried information in a trained-checkpoint intervention | `experiments/doubt-regulated-caution/AMENDMENT.md` Section 8 | Positive |
| High-authority system prompt moved behavior by +18.0pp over permuted | `experiments/second-person-doubt-prime/AMENDMENT.md` Section 8 | Pass |
| Inverted system prompt showed asymmetric compliance, not belief revision | `experiments/oracle-dissociation-prime/AMENDMENT.md` Section 9 | Pass |
| Divergent-pool test found zero own-readout congruence; Addendum A1 certified the instrument | `experiments/divergent-pool-own-readout/AMENDMENT.md` Sections 9-10 | H-compliance |
| Probe-as-reward TRUE arm failed to train readout consultation | `experiments/probe-as-reward/AMENDMENT.md` Section 5 | Null |
| Raw-base KU-gated boundary push (dosed write) produced 73.5% clean tighten at 3.1% known cost (overdrive regime, L34/dose 200) | `experiments/doubt-gated-caution-tighten/AMENDMENT.md` Outcome | Exploratory pass |
| At this overdrive operating point, an unconditional write damages 60.1% of held-out known-correct rows vs 3.1% gated (57.0pp, McNemar p = 4.2e-43): the gate is the sole source of selectivity here | `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md` Outcome | Registered pass; scoped to L34/dose-200 |
| Mid-band write site (Qwen3.5-4B hs20, dose_abs 12.608) decouples refusal from corruption in-sample FIT (refused 0.684, well-formed 0.980, known cost 0.042); permuted-gate control shows the write is already content-selective there | `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` Outcome | Exploratory pass, in-sample |
| Same mid-band operating point transfers to held-out (refused 0.678, well-formed 0.977, known cost 0.039), promoting it from an in-sample selection to a held-out claim | `experiments/qwen35-4b-midband-heldout/AMENDMENT.md` Outcome | Held-out pass |
| The overdrive headline (73.5%/3.1%) survives temperature-0.7 sampled decoding with majority-vote aggregation (69.5% pooled conversion, all 5 seeds above floor, cost 4.65%) | `experiments/snap-seed-sampled-decode-replication/AMENDMENT.md` Outcome | Decode-robustness pass |
| The name IDK switch for the dosed write at the Qwen3.5-4B hs20 operating point is earned by a fresh-seed sampled-decode confirmatory passing all three registered name-earning gates: endpoint IDK jump +0.6125 with paired-bootstrap CI lower bound 0.5650 against a 0.15 floor, hedged share falling at both dosed arms, and placebo inside the 0.05 band | `experiments/idk-switch-naming-confirmatory/AMENDMENT.md` Outcome | Confirmatory naming cell, resolved |
| Mid-band gate-contribution factorial falsifies "the gate supplies selectivity" as a universal claim in both families: permuted-gate confab abstention 0.550 qwen / 0.600 mistral vs true gate 0.689/0.694; Gap_Sel(c_hat) 0.148/0.129 sub-floor vs a 0.20 floor; S1 direction-specificity passes qwen (7.27) and fails mistral (2.03) | `experiments/gate-contribution-factorial/AMENDMENT.md` Outcome | Registered falsification of the universal-gate claim |
| J-lens localized workspace-like band to hs=23-29, peak hs=26; L34 maps after band | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md` Outcome | Exploratory diagnostic |
| Layer-specific calibration recovered non-collapsing setpoints | `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md` Outcome | FIT-only pass |
| Held-out mid-band layer contrast: hs23 89.2% vs hs34 66.5% | `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md` Outcome | Exploratory pass |
| Same-model replication 1 (single-source pool): best mid-band (hs29, 99.67%) beat hs34 (94.12%) by only +5.6pp, below the registered +10pp bar; miss attributable to hs34 sitting near ceiling, not to an absent effect | `experiments/j-space-layer-contrast-replication-qwen3-4b/AMENDMENT.md` Outcome | Registered miss; ceiling-attributed |
| Same-model replication 2 (multi-source pool, off ceiling): hs29 92.76% vs hs34 73.76%, +19.0pp, paired McNemar p = 4.5e-13 (42 late-only vs 0 mid-only discordants); known-correct cost gap +1.43pp (2.81% vs 1.38%, disclosed as an absolute doubling) | `experiments/j-space-layer-contrast-rep2-multisource/AMENDMENT.md` Outcome | Registered full pass |
| Natural token-target J-space write was non-inert but redundant with `c_hat` | `experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md` Outcome | Exploratory falsification |
| An instrument-validity check found neither of two candidate mid-generation (answer-window) steering harnesses certified: an optimized-decode implementation never fires its hook during cached decode (0 decode-step calls, 25/25 prompts checked), voiding an earlier answer-window result as an instrumentation artifact rather than a causal null; a plain-inference implementation fires every decode step and lands the write within tolerance on all positions before the steered trajectory diverges, but its cross-trajectory readback fails to certify once tokens diverge | `experiments/h6-genstream-hook-firing-check/AMENDMENT.md` Outcome | Instrument-validity check; no behavioral steering evidence reported |
| Cross-family atlas: eff_dim_frac peaks early (0.09-0.14 depth) in both llama and mistral, not interior as predicted; read panel still delivers a usable per-family interior band (llama L15-23, mistral L7-27) | `experiments/jspace-family-atlas/AMENDMENT.md` Outcome | Prediction failed; read panel delivered |
| Cross-family confirmatory fleet (qwen/llama/mistral, universal-depth write site) NOT PROMOTED: every cell stopped at FIT dose-viability before held-out; companion c_hat audit shows the encoding readable in all four families while late-site writes actuate only in the Qwen lineage | `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` Outcome | Not promoted; write-site problem, not a family-mechanism null |
| Dark-candidate screen validates positive boundary-push lever but promotes no dark candidates | `experiments/dark-actuator-screen/AMENDMENT.md` Outcome | Supporting null |
| Answer-sycophancy pilot found a readable direction but no clean actuator against a matched control; carries no body evidence, referenced only as future work in Section 6.5 | `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md` Outcome | Unsigned interim pilot (draft, not a governed result) |
| Initial cross-family run: gated write does not actuate FIT-viable canonical clean refusal at either atlas-located non-Qwen site under the locked three-phrase detector; llama fails on format collapse before the refusal floor, mistral peaks 0.579 vs the 0.60 floor with the miss substantially canonical-phrase coverage | `experiments/rr-cross-family-raw-refusal/AMENDMENT.md` Outcome | Exploratory falsification (detector-vocabulary scope disclosed; superseded by the RR2 wide-instrument re-read) |
| Mistral cross-family gated write cleared benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) gates under a wide blinded instrument but failed the flat 2-point placebo tolerance (+7.39pp random-direction lift) | `experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md` Outcome | Exploratory falsification (placebo-criterion design flaw, not benefit/cost) |
| Wide-instrument baseline hedging and placebo response are family-graded and family-signed (qwen -5.13pp suppression, mistral +7.39pp recruitment); flat placebo tolerances must be registered per-family | `experiments/abstention-wide-instrument-calibration/AMENDMENT.md` Outcome | Exploratory instrument calibration, resolved |
| Corrected effect-ratio placebo criterion (>= 3x max-over-K fresh-seed random lift) still falsified mistral direction-specificity (ratio 1.87) while reproducing RR2's benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) exactly; red-team certified robust to detector-only and mean-of-K denominators; mistral's random-direction lift spans -7.4 to +21.8pp across three fresh seeds; llama rider placebo response is null at matched magnitude, completing the three-family sign map | `experiments/rr3-corrected-placebo-replication/AMENDMENT.md` Outcome | Exploratory falsification (corrected-criterion re-adjudication of the RR2 claim, benefit/cost intact) |
| Multi-seed placebo census (K=15 fresh seeds per family at matched magnitude, S=300 paired rows, blinded adjudication in 18 shards) resolved all three families' random-direction placebo as sign-consistent rather than seed noise: qwen suppression SURVIVES (14/15 negative, median -6.0), mistral recruitment SURVIVES at the 12/15 boundary (median +7.0, falsifying both predictors' registered seed-noise call), null-control llama shows a newly discovered negative sign (12/15, median -7.67); historical single-seed values sit at the 53rd percentile; a post-unblind final-rate-rule join correction moved two verdicts against the predictions, both report versions committed, red-team certified legitimate | `experiments/placebo-seed-distribution-census/AMENDMENT.md` Outcome | Exploratory placebo-distribution census, resolved (revises the RR3 llama-null leg) |
| Within-kuq subtype breakdown: question type does not explain the cross-family placebo sign difference at the family level, but one subtype (future-unknown) carries qwen's entire suppression (-24.7pp) and is also mistral's largest recruitment delta (+11.8pp) | `experiments/placebo-signflip-question-type-analysis/AMENDMENT.md` Outcome | Resolved; subtype-inert reading falsified for qwen |
| Criterion (d) (evidence-responsiveness) is not licensed on the world-known error class for the named KU direction (primary transfer void, population reversal) or for a world-known-specific refit (specificity leg passes, collapse leg fails); a coherence/saturation ceiling limits refusal to 12.75% of world-known confabs before generation degenerates | `experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` Outcome | Null result; retires mentalistic naming with a completed (d) adjudication |
| A constructive search for a specific evidence-response axis (d_ev) fires at baseline but is indistinguishable from covariance-shaped random directions and weaker than the native ignorance-fit direction; it reconstructs retrieval-family geometry, not a specific evidence-responsive axis | `experiments/evidence-response-direction-search/AMENDMENT.md` Outcome | Null result; strengthens the fragmentation reading |
| Gemma's cross-family inert reputation was a depth-coverage artifact: below-seam sites at relative depth 0.357 and 0.524 clear held-out clean-tightening and known-correct cost floors, the former with no placebo arm registered and the latter with a degenerate placebo pass (all 5 accepted draws produced zero lift, reported under the degenerate label and never as a large specificity ratio); the seam-adjacent site (relative depth 0.571) clears the same floors but fails direction-specificity (worst placebo draw reproduces 88% of the effect); a sharing-off precondition control broke the model's own baseline (known-correct well-formedness 0% to 100% malformed, NLL 3.53 to 12.33) before the sharing-on/sharing-off contrast could run, leaving the KV-quarantine account supported but not established | `experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md` Outcome | Exploratory, resolved; quarantine hypothesis open |
| The three sites at the top of gemma's cross-family operating band (relative depth 0.595, 0.619, 0.643), all above the seam, produced no direction-specific actuation under a mandatory-placebo design: 0.595 cleared both held-out gates (79.2% clean tightening, Wilson CI [72.4, 84.6]; known-correct cost 3.3%, CI [1.8, 6.2]) then failed direction-specificity at effect ratio 1.279 against the 3.0 floor (worst of 5 random draws reproduced 78% of the effect), reproducing the seam-adjacent signature one block shallower (1.139); 0.619 and 0.643 were dose-viability NOT-RUN (best FIT clean-tightening 0.375 and 0.250 against the 0.50 usability floor). All three registered predictions met. Relative depth and KV-sharing status are the same variable across this band, so the result does not resolve the KV-quarantine hypothesis in either direction | `experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md` Outcome | Exploratory, resolved |
| J-lens profile on a trained checkpoint: the interior band is present but narrowly (interior max 0.00735 at hs29 against a 0.00675 threshold) and reshaped, with the raw-base hs26 peak suppressed ~35% and the profile flatter and deeper; the rule-selected mid-band site (hs17) reads the refusal axis nearly as well as the late site (AUROC 0.8645 vs 0.8688) but full ablation there releases 0 of 168 formerly refused knowns against 163 of 168 at L35 and induces refusal on 48% of previously answered knowns | `experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md` Outcome | Falsified on both clauses; the read-side band does not license a write site |
| Correctness-direction rotation across a model's own training checkpoints: cross-stage cosines 0.192, 0.449, 0.330, none reaching the 0.85 stability floor, against a within-stage split-half floor of 0.174 and readout AUROC flat near 0.80, so direction identity is not measurable at any transition at these sample sizes | `experiments/correctness-direction-rotation/AMENDMENT.md` Outcome | Null result; instrument-limited (motivation only, Section 6.5) |
| Correctness discriminative-subspace overlap between checkpoints: k=1 shared direction above its permutation null (0.00896 vs 95th percentile 0.00472), k>=4 inside the null, transferable signal diffuse rather than concentrated (recovery 0.742 against a random-slice floor of 0.701); the reliability limb was shown estimator-structurally unreachable for any signal | `experiments/correctness-subspace-overlap/AMENDMENT.md` Outcome | Null result; instrument-limited (motivation only, Section 6.5) |
| Full refusal-axis ablation on a fresh seed of the trained checkpoint releases 45.7 points of known-item over-refusal and recovers correct answers on 29.2% of released rows, with 1.3% induced refusal and a 7.2 point correct-rate drop on the known-correct control; post-ablation over-refusal 0.5528 against a registered 0.10 confirmation bound and 0.30 falsifier line, so the registered prediction missed and the magnitude of the release is seed-dependent | `experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md` Outcome | Falsifier fired; the axis remains causal at this seed, the collapse magnitude does not replicate |
| The archived full-ablation pipeline re-derives under its own instrument on the first seed, with the orthogonalized component reproducing its own separate archived value: the divergence between the two figures is variant identity, not drift or error. Run configurations survive under `archive/experiment/phase1/probe/config/`; row-level outputs stay untracked under public-repo containment | `experiments/caution-ablation-rederivation/AMENDMENT.md` Outcome | Resolved; provenance repair, no promotion on its own |
| The separate installation question Section 6.6 declines to answer: a bounded pre-registered site sweep on the trained lineage found actuation clearing its held-out gate at all five dose-viable sites, with selectivity not adjudicable at any of them and direction-specificity passing at one site only, so no site satisfies the registered conjunction | `experiments/caution-install-bounded-site-sweep/AMENDMENT.md` Outcome | Resolved; exploratory lead requiring confirmatory replication, no numbers carried into the body |

## Appendix B. Substrate Coverage Table

Generated by `papers/paper-5-actuation/scripts/build_coverage_table.py` (deterministic, CPU-only, no network; regenerate with `--write`) from `experiments/<slug>/experiment.yaml`, falling back to that cell's own `cell.yaml` / `families/*.yaml` / `model_matrix.yaml` where `checkpoint.repo` is empty. Every row traces to governed YAML, never to this manuscript's own prose. **DECLARED-only rows support no claim about the model(s) they name**: a checkpoint appearing in a matrix config that the cell declared is not evidence the cell produced an outcome on that checkpoint. Where the launched subset is not separable from YAML alone, the row says so explicitly and quotes the governed `verdict` field rather than a machine-derived count.

<!-- BEGIN GENERATED: substrate-coverage-table -->

| Cell slug | experiment.yaml status | Substrate(s) | Declared vs. launched | Manuscript section(s) |
|---|---|---|---|---|
| `causal-confidence-steering` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.1 |
| `first-person-injection` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.1 |
| `radial-anti-propensity-steering` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.2 |
| `doubt-regulated-caution` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md. Instrument configs migrated from the archived legacy probe config tree on 2026-07-09; the batched smoke is a companion equivalence check, not the registered evidence run." | UNRESOLVED (hand-read AMENDMENT.md required) | NOT NARRATED IN BODY (front matter + Appendix A only; resolved 2026-08-13: AC remains appendix-only by PI ruling -- the paper's scope is deliberately raw-base/untrained substrates and AC is trained-lineage predecessor context -- AC is this cell's legacy amendment label) |
| `second-person-doubt-prime` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.3 |
| `oracle-dissociation-prime` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.3 |
| `divergent-pool-own-readout` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.3 |
| `probe-as-reward` | historical | UNRESOLVED -- historical-amendment migration; checkpoint fields intentionally blank. experiment.yaml migration.notes: "Imported from legacy amendment prose. Do not infer missing machine fields without hand-reading AMENDMENT.md." | UNRESOLVED (hand-read AMENDMENT.md required) | 4.4 |
| `doubt-gated-caution-tighten` | resolved | `unsloth/Qwen3-4B` @ `raw-base (no adapter; bf16, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.5 |
| `ungated-vs-gated-dose-matched` | resolved | `unsloth/Qwen3-4B` @ `raw-base (no adapter; bf16, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.5 |
| `qwen35-4b-midband-doubt-snap` | resolved | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 1 declared / 1 launched (single-substrate cell) | 4.5 |
| `qwen35-4b-midband-heldout` | resolved | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 1 declared / 1 launched (single-substrate cell) | 4.5 |
| `snap-seed-sampled-decode-replication` | resolved | `unsloth/Qwen3-4B` @ `raw-base (no adapter; bf16, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.5 |
| `idk-switch-naming-confirmatory` | resolved | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 1 declared / 1 launched (single-substrate cell) | 4.5, 4.8 |
| `gate-contribution-factorial` | falsified | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: Qwen/Qwen3.5-4B @ 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a; mistralai/Mistral-7B-Instruct-v0.3 @ c170c708c41dac9275d15a8fff4eca08d52bab71 | DECLARED 2 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Gate axis falsified on both families: the dosed c_hat write alone drives most of the abstention lift (permuted-gate confab abstention 0.550 qwen / 0.600 mistral vs baselines 0.083 / 0.282); the true doubt gate adds a rea..." | 4.8 |
| `j-space-localization-qwen3-4b` | resolved | `unsloth/Qwen3-4B` (revision not recorded) | 1 declared / 1 launched (single-substrate cell) | 4.6 |
| `j-space-midband-dose-calibration-qwen3-4b` | resolved | `unsloth/Qwen3-4B` @ `raw-base (bf16, no adapter, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.6 |
| `j-space-calibrated-layer-contrast-qwen3-4b` | resolved | `unsloth/Qwen3-4B` @ `raw-base (bf16, no adapter, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.6 |
| `j-space-layer-contrast-replication-qwen3-4b` | null-result | `unsloth/Qwen3-4B` @ `raw-base (bf16, no adapter, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.6 |
| `j-space-layer-contrast-rep2-multisource` | resolved | `unsloth/Qwen3-4B` @ `raw-base (bf16, no adapter, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.6 |
| `j-space-token-targeted-refusal-qwen3-4b` | falsified | `unsloth/Qwen3-4B` @ `raw-base (bf16, no adapter, no 4-bit quantization)` | 1 declared / 1 launched (single-substrate cell) | 4.7 |
| `h6-genstream-hook-firing-check` | resolved | `unsloth/Qwen3-4B` @ `64033659d5caf1b8ed7f929b29de705e93a4d468` | 1 declared / 1 launched (single-substrate cell) | 6.4 |
| `jspace-family-atlas` | resolved | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: unsloth/Llama-3.2-3B-Instruct (llama32_3b_instruct) @ 006f5dcd1393c3add266de40994ba96225e9689d; mistralai/Mistral-7B-Instruct-v0.3 (mistral7b_instruct_v03) @ c170c708c41dac9275d15a8fff4eca08d52bab71 | DECLARED 2 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "prediction failed in both families because the eff_dim_frac profile peaks early (0.09-0.14 depth) rather than interior, while the read panel delivered the intended per-family layer map with an interior band (llama 15-23,..." | 6.3 |
| `doubt-snap-cross-family-confirmatory` | resolved | checkpoint.repo (verbatim): "cross-family matrix"; checkpoint.revision (verbatim): "see model_matrix.yaml". DECLARED in cell.yaml, model_matrix.yaml: unsloth/Llama-3.2-3B-Instruct [small] (llama32_3b_instruct) @ 006f5dcd1393c3add266de40994ba96225e9689d; unsloth/Llama-3.1-8B-Instruct [mid] (llama31_8b_instruct) @ 4699cc75b550f9c6f3173fb80f4703b62d946aa5; mistralai/Mistral-7B-Instruct-v0.3 [small] (mistral7b_instruct_v03) @ c170c708c41dac9275d15a8fff4eca08d52bab71; mistralai/Ministral-8B-Instruct-2410 [mid] (ministral8b_instruct_2410) @ 2f494a194c5b980dfb9772cb92d26cbb671fce5a; Qwen/Qwen3.5-4B [small] (qwen35_4b) @ 851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a; Qwen/Qwen3.5-9B [mid] (qwen35_9b) @ c202236235762e1c871ad0ccb60c8ee5ba337b9a; google/gemma-4-E4B-it [small] (gemma4_e4b_it) @ fee6332c1abaafb77f6f9624236c63aa2f1d0187; google/gemma-3-12b-it [mid] (gemma3_12b_it) @ 96b6f1eccf38110c56df3a15bffe176da04bfd80 | DECLARED 8 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "not promoted: all four launched cells stopped at the registered pre-outcome FIT dose-viability rule at the 0.94-depth write site (peaks 0.326/0.184/0.000 small tier, 0.058 mid tier); the c_hat audit and the qwen35_4b mid..." | 6.5 |
| `dark-actuator-screen` | null-result | `unsloth/Qwen3-4B-bnb-4bit` @ `raw-base (no adapter; checkpoint_tag "raw-base" per AK Stage 1 manifest)` | 1 declared / 1 launched (single-substrate cell) | 4.7 |
| `aq-sycophancy-activation-actuator` | draft | `Qwen/Qwen3-4B` @ `1cfa9a7208912126459214e8b04321603b3df60c` | 1 declared / 1 launched (single-substrate cell) | 6.5 |
| `rr-cross-family-raw-refusal` | falsified | checkpoint.repo (verbatim): "cross-family (two atlas-mapped substrates)"; checkpoint.revision (verbatim): "see cell.yaml families (revisions pinned from fleet model_matrix.yaml at sign)". DECLARED in cell.yaml: unsloth/Llama-3.2-3B-Instruct @ 006f5dcd1393c3add266de40994ba96225e9689d; mistralai/Mistral-7B-Instruct-v0.3 @ c170c708c41dac9275d15a8fff4eca08d52bab71; confirmatory execution model (batch verbs for baseline/capture; mechinterp steer for writes) | DECLARED 3 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Falsified, both families shape F: the doubt-gated caution write does not actuate FIT-viable canonical clean refusal at either atlas-located non-Qwen site; llama fails on format collapse before the refusal floor (robust t..." | 4.8, 6.5 |
| `rr2-mistral-adjudicated-refusal-confirm` | falsified | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: mistralai/Mistral-7B-Instruct-v0.3 @ c170c708c41dac9275d15a8fff4eca08d52bab71; direct InterventionHook/GenerationInterventionController/RunLog driving (RR precedent, not the mechinterp-steer YAML recipe path) | DECLARED 2 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Falsified on the placebo leg: the blinded adjudicated instrument confirms idiom-inclusive mistral refusal at 0.699 with pristine cost, vindicating the RR detector-width caveat, but a magnitude-matched random direction li..." | 4.8, 6.5 |
| `abstention-wide-instrument-calibration` | resolved | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: qwen35-4b; llama32-3b; mistral7b-v03 | DECLARED 3 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Resolved: wide-instrument baseline abstention is family-graded (qwen 0.104, llama 0.164, mistral 0.280) and placebo response is family-specific in sign (qwen suppresses -5.13 points where mistral recruits +7.39), so the ..." | 4.8, 6.5 |
| `rr3-corrected-placebo-replication` | falsified | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: mistralai/Mistral-7B-Instruct-v0.3 @ c170c708c41dac9275d15a8fff4eca08d52bab71; mistral7b_instruct_v03; unsloth/Llama-3.2-3B-Instruct @ 006f5dcd1393c3add266de40994ba96225e9689d | DECLARED 3 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "FALSIFIED under the corrected effect-ratio placebo criterion: the mistral gated caution write is not direction-specific (effect ratio 1.87 < 3.0, max fresh-seed random lift +21.8 points) while benefit and cost reproduce ..." | 4.8, 6.5 |
| `placebo-seed-distribution-census` | resolved | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: family id `qwen35-4b` (HF repo/revision resolves via the fleet model_matrix.yaml); family id `mistral7b-v03` (HF repo/revision resolves via the fleet model_matrix.yaml); family id `llama32-3b` (HF repo/revision resolves via the fleet model_matrix.yaml) | DECLARED 3 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "At matched magnitude, random-direction placebos are sign-consistent rather than seed noise in all three families: qwen suppression SURVIVES robustly (14/15 negative, median -6.0), mistral recruitment SURVIVES at the exac..." | 4.8, 6.5 |
| `placebo-signflip-question-type-analysis` | resolved | checkpoint.repo (verbatim): "(none; CPU-only re-read of persisted artifacts, no model loaded)". DECLARED in cell.yaml: none; qwen35-4b; mistral7b-v03 | DECLARED 3 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Question type does not explain the cross-family placebo sign difference (registered mechanism falsifier untriggered; M1 doubt-axis separation confirmed in all three families under the frozen gate's operational convention..." | 4.8 |
| `margin-evidence-responsiveness-worldknown` | null-result | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 1 declared / 1 launched (single-substrate cell) | 4.6, 6.4 |
| `evidence-response-direction-search` | null-result | `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a` | 1 declared / 1 launched (single-substrate cell) | NOT NARRATED IN BODY (front matter + Appendix A only; no flagged open-work item, unlike doubt-regulated-caution) |
| `gemma4-e4b-kv-seam-quarantine` | resolved | `google/gemma-4-E4B-it` @ `fee6332c1abaafb77f6f9624236c63aa2f1d0187` | 1 declared / 1 launched (single-substrate cell) | 4.9 |
| `gemma4-e4b-pocket-ladder` | resolved | `google/gemma-4-E4B-it` @ `fee6332c1abaafb77f6f9624236c63aa2f1d0187` | 1 declared / 1 launched (single-substrate cell) | 4.9 |
| `jlens-trained-checkpoint-midband-ablation` | falsified | `clean_sft_grpo_v2_seed1 (local lineage: sft_schema_clean_seed1_full/20260623_123624 merged-16bit base + schema_clean_sft_grpo_v2_seed1_full/20260624_095831 final_model adapter)` @ `local run dirs pinned in configs; published mirror eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` | 1 declared / 1 launched (single-substrate cell) | 6.3 |
| `correctness-direction-rotation` | null-result | checkpoint.repo (verbatim): "local four-stage set (see cell.yaml stages; raw + partrue identities pinned at staging per A3)". DECLARED in cell.yaml: LogisticRegression(saga, tol=1e-3) | DECLARED 1 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "CD-G1 not met (later transitions 0.449/0.330 vs the 0.85 floor) and falsifier not fired (raw->cleansft 0.192); pre-registered readings exhausted; post-hoc: correctness direction too weakly identified (split-half floor 0...." | 6.5 |
| `correctness-subspace-overlap` | null-result | `reused five-stage/checkpoint tensor set (see cell.yaml data.stages); no new checkpoint identity, CPU-only reuse of CD and Amendment S/T on-disk extractions` (revision not recorded) | 1 declared / 1 launched (single-substrate cell) | 6.5 |
| `refusal-axis-ablation-confirmatory` | falsified | checkpoint.repo empty in experiment.yaml. DECLARED in cell.yaml: clean_sft_grpo_v2_seed2 on its own per-seed merged base (published pins 2390e893 adapter, 4d526fdd base; local run dirs 20260804_131151 and 20260731_232307) | DECLARED 1 checkpoint(s) (matrix) -- LAUNCHED subset is NOT machine-separable from YAML; see AMENDMENT.md Outcome. Governed verdict field: "Falsifier fired: with a valid instrument (RC-G0 pass, baseline 1.000), full refusal-axis ablation on clean_sft_grpo_v2_seed2's own lineage leaves known-item over-refusal at 0.553, far above both the 0.10 confirmation bou..." | 6.6 |
| `caution-ablation-rederivation` | resolved | UNRESOLVED -- checkpoint.repo empty in experiment.yaml; fallback file(s) inspected (cell.yaml) but no recognizable checkpoint declaration found (repo/model/substrate/family/cell_id, or families.*.id) | UNRESOLVED (hand-read AMENDMENT.md required) | NOT NARRATED IN BODY (front matter + Appendix A provenance row only) |
| `caution-install-bounded-site-sweep` | resolved | `professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` @ `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e` | 1 declared / 1 launched (single-substrate cell) | 6.6 |

<!-- END GENERATED: substrate-coverage-table -->

## Appendix C. Figure Plan

Every figure is built from committed aggregate artifacts and referenced
inline in Section 4: Figures 1-6 by
`papers/paper-5-actuation/scripts/build_figures.py` and Figures 7-8 by
`papers/paper-5-actuation/scripts/build_restructure_figures.py`, whose
embedded reproduction audits re-verify every plotted number against its
committed source artifact at build time. `figures/MANIFEST.md` maps each
figure to its source artifacts and hashes. Figure 6 alone is transcribed from
its governing document's outcome prose rather than a result JSON (none is
committed for that cell); the manifest documents that caveat and the one
derived count.

1. Figure 1, gated controller headline: confabulation conversion and
   known-correct cost for the real KU-gated write against random-direction
   and permuted-gate placebos, original and multi-source replication pools
   (`fig-p5-01-headline-conversion.png`).
2. Figure 2, ungated-versus-gated dose-matched contrast at the resolved
   overdrive operating point (`fig-p5-02-ungated-vs-gated-h4.png`).
3. Figure 3, sampled-decode replication: conversion and cost under
   temperature-0.7 decoding across five seeds
   (`fig-p5-03-h3-sampled-decode.png`).
4. Figure 4, dose-response curve at the late write site from the FIT
   calibration sweep (`fig-p5-04-dose-response.png`).
5. Figure 5, localization: the read-only J-lens workspace band alongside the
   write-site behavioral effect across the original pool and both same-model
   replications (`fig-p5-05-localization.png`).
6. Figure 6, propensity push null: confabulation kills under the primary
   push versus the permuted-assignment control, with the read-back
   verification of push magnitude (`fig-p5-06-propensity-null.png`).
7. Figure 7, placebo census: matched-magnitude random-direction null
   distributions across fifteen fresh seeds for each of the three families,
   with per-family medians, interquartile ranges, spans, and sign
   (`fig-p5-07-placebo-census.png`).
8. Figure 8, Gemma depth ladder: actuation outcome against relative depth
   with the pass or fail disposition of each site
   (`fig-p5-08-gemma-depth-ladder.png`).

## Appendix D. Open Work Before Submission

- Reconcile this draft against the retired provenance inventory under
  `archive/papers/`.
- Run the planned cross-model J-space and gated-controller replication before
  promoting the workspace-band result from exploratory to headline.
- Register any future direction-specificity placebo criterion against the
  per-family measured null distribution the census supplies at fifteen seeds
  (Section 4.8), for example via a percentile-based tolerance or a
  sign-opposition criterion, not a flat symmetric tolerance and not a single
  seed. The per-family wide-instrument baselines (qwen 0.104, llama 0.164,
  mistral 0.280) still anchor the recruitment-versus-suppression axis.
- Run llama's gated boundary push at its own actuation-selected site, and
  score it under the wide two-instrument stack, before claiming or ruling out
  cross-family direction-specificity for that family. Its placebo null is
  measured and suppressive, so it cannot serve as a null control.
- Re-score the Section 4.5 and 4.6 random-direction and permuted-gate controls
  under the wide two-instrument stack before promoting either result.
- The `doubt-regulated-caution` cell (trained-lineage predecessor context) and
  the `evidence-response-direction-search` null remain front-matter and
  Appendix A entries only, per the paper's raw-base scope.
