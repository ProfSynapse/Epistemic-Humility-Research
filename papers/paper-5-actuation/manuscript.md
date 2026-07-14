---
title: "Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Epistemic State in Small Language Models"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v0
date: 2026-07-08
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
target: arXiv (cs.CL / cs.AI / mechanistic interpretability)
evidence_base: >
  Exploratory Paper-5 actuation arc. Governed source docs include
  experiments/causal-confidence-steering/AMENDMENT.md,
  AMENDMENT-AB-first-person-injection.md,
  AMENDMENT-AC-doubt-regulated-caution.md,
  AMENDMENT-AF-second-person-doubt-prime.md,
  AMENDMENT-AG-oracle-dissociation-prime.md,
  AMENDMENT-AH-divergent-pool-own-readout.md,
  AMENDMENT-AI-probe-as-reward.md,
  experiments/doubt-gated-caution-tighten/AMENDMENT.md,
  experiments/j-space-localization-qwen3-4b/AMENDMENT.md,
  experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md,
  experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md,
  experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md,
  experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md,
  experiments/abstention-wide-instrument-calibration/AMENDMENT.md,
  experiments/rr-cross-family-raw-refusal/AMENDMENT.md, and
  experiments/rr3-corrected-placebo-replication/AMENDMENT.md.
notes: >
  Draft v0 is a synthesis scaffold, not submission-ready. It deliberately
  separates reader-facing claims from amendment traceability. The core results
  are single-model or surface-local exploratory unless explicitly marked
  otherwise. A first cross-family attempt on mistral and a follow-up
  wide-instrument calibration study are now folded in as Section 4.8. A
  corrected-criterion re-adjudication under a registered multi-seed
  effect-ratio placebo gate, plus a completed three-family placebo-sign-map
  rider, is folded in as Section 4.9; all three remain exploratory and
  pre-headline. The next planned step is a larger cross-model / cross-family
  actuation study registered against the multi-seed per-family placebo design
  rule Section 4.9 established.
---

# Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Epistemic State in Small Language Models

*Draft v0. Companion to [*Knows but Doesn't Say*](../paper-3-knows-but-doesnt-say/manuscript.md)
and [*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md).*

---

## Abstract

Prior papers in this series show that small language models internally represent
what they know, even when they do not say it. A frozen base model carries a
near-perfect answerability readout before generation, a separate correctness
readout after generation, and a veto signal that ranks confabulated answers as
low trust. This paper asks the next question: can those readable signals be
written back into the model to make it act epistemically humble?

Across a sequence of pre-stated exploratory cells, the answer is mixed and
mechanistically sharp. First, naive "turn the probe around" strategies mostly
fail. Direct activation steering and within-generation text injection on the
trust axes produced no registered behavioral effect; stronger first-person
phrasing produced only a small gate-side trickle and no correctness-revision
effect. A high-authority second-person system prompt did move behavior, but a
divergent-pool test showed the model was obeying the instruction rather than
consulting its own readout. Even a reward equal to the model's own probe score
failed to train readout consultation: the true-sensor arm was less congruent
with its final readout than a permuted-sensor control.

Second, hidden-state actuation does work when the problem is posed as a gated
controller rather than as an unconditional write. A doubt-gated caution snap on
raw-base Qwen3-4B converted 136/185 held-out confabulations into clean refusals
(73.5%, Wilson 95% CI [66.7, 79.3]) while producing 8/258 false refusals on
known-correct answers (3.1%, CI [1.6, 6.0]). Random-direction and permuted-gate
controls did not reproduce the result. The lesson is that the write itself is
not selective; the readout gate supplies selectivity.

Third, write location matters. A Jacobian-lens diagnostic localized a
workspace-like J-space band in Qwen3-4B around hs=23-29, peaking at hs=26, while
the inherited L34 write site maps to hs=34 just after that band. After
layer-specific dose calibration, held-out mid-band writing beat the late hs34
reference: hs23 reached 165/185 clean refusals (89.2%) versus hs34 123/185
(66.5%), a +22.7 point gain with only +0.78 points known-correct cost. However,
using the J-lens backward to target natural refusal tokens was not enough to
improve the controller: a token-target direction was non-inert by itself
(88/185 = 47.6%) but added only one extra clean refusal on top of the hs23
caution snap.

Together these results support a practical distinction: epistemic state is
readable, externally usable, and sometimes writable, but not automatically
consulted by the model's own policy. Productive actuation requires the right
channel, the right gate, and the right write site.

---

## 1. Introduction

The first half of this program established a gap. A small language model can
represent what it knows internally while failing to verbalize or act on that
state. The companion diagnosis, [*Knows but Doesn't Say*](../paper-3-knows-but-doesnt-say/manuscript.md),
showed that answerability is linearly readable from hidden states at near-ceiling
accuracy while stated confidence remains flat and training-resistant. The
follow-up, [*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md),
showed that two readable signals, answerability before generation and answer
correctness after generation, compose into a training-free trust pipeline that
generalizes across sizes, families, and sampled-decode seeds.

Those papers are about reading. This paper is about writing. If a model already
contains a faithful epistemic signal, can we make its generation policy consult
that signal? Can we steer the residual stream, inject the signal in text, reward
agreement with it, or write into the workspace-like layer band where reportable
representations live?

This is not a trivial extension of probing. A linear probe can be useful even if
the model's policy never uses the direction it reads. Conversely, a direction can
be behaviorally causal without being a faithful self-readout. The central claim
of this paper is therefore deliberately conservative:

> **Readable is not writable.** Epistemic directions can be strong, portable
> readouts while remaining weak, channel-dependent, or non-selective actuators.

The results refine that claim into three engineering rules.

1. **Do not assume text carries the readout.** Within-generation text injection
   and first-person confidence prose fail to open the channel. System-prompt
   authority can move behavior, but later tests show it moves policy by
   instruction compliance, not by causing the model to consult its own internal
   readout.
2. **Separate sensing from actuation.** The successful controller is a two-part
   system: a doubt gate decides which rows receive a write, and a caution snap
   supplies the refusal behavior. The snap alone is not selective.
3. **Write near the workspace band.** A J-lens localization suggests that the
   inherited late write layer was past the most verbalizable workspace-like band.
   After calibration, mid-band writes outperform the late reference on held-out
   confab tightening.

The evidence remains exploratory. Most cells are single-model, single-seed, or
surface-local. We write this paper now because the pattern is stable enough to
organize the next study: larger, cross-model replication of the successful gated
workspace-band actuator, plus sharper tests of whether denser token targets or
different model families change the write/read relationship.

---

## 2. Background: From Readout to Actuation

### 2.1 The prior readout result

Paper 3 separated three surfaces: the internal state, the stated confidence
token, and the generated behavior. On Qwen3-4B, an internal answerability axis
separated known from unknown items at about AUROC 0.997, while stated confidence
was nearly flat. Paper 4 then split the internal state into two deployable
readouts: an answerability **gate** before generation and a correctness **dial**
after generation. The gate/dial/veto pipeline is useful because it reads the
model from outside rather than asking the model to faithfully report itself.

That distinction motivates the present study. External reading can support a
classifier, a monitor, or an abstention wrapper, but it does not prove the model's
own policy uses the signal. Actuation asks whether the internal state can be
made causal for behavior.

### 2.2 What would count as use?

We treat "use of an internal readout" as stronger than behavior change. A system
prompt that says "you do not know this" and causes refusal is an actuator, but it
does not show the model consulted its own state. Likewise, a reward that improves
abstention behavior may train surface heuristics rather than readout alignment.

The cleanest positive evidence would satisfy three conditions:

- **alignment:** the intervention is computed from the model's own state, not
  from gold labels;
- **specificity:** a permuted or random control does not reproduce the effect;
- **selectivity:** the intervention moves target failures without imposing the
  same action on rows where it is inappropriate.

The successful cells below meet these conditions only when readout and write are
separated: the readout gates the intervention, and the write supplies a fixed
behavioral move.

---

## 3. Methods Overview

This paper combines several exploratory actuation families. Each was governed by
a signed amendment or experiment-local AMENDMENT before the relevant run, with
predictions, falsifiers, gates, and controls frozen before outcome evaluation.
Appendix A maps every paper claim to its governed source document.

### 3.1 Channels

We tested four ways to route an epistemic readout into behavior.

**Activation writes.** Additive or erase-write interventions modify the residual
stream along a fitted direction at a specified layer and token scope. These are
the closest analogue to "turning the probe around."

**Within-generation text injection.** Probe scores are rendered into a thinking
or revision trace as text, either as terse telemetry or as first-person prose
with explicit action rules.

**High-authority system prompts.** The same kind of state-derived label is
rendered as a second-person system instruction before generation.

**Reward coupling.** A reinforcement-learning reward is computed from a frozen
probe score read from the policy's own pre-generation hidden state.

### 3.2 Readouts and directions

The core readouts are answerability/doubt and caution/refusal. In the gating
experiments, the sensor is a standardized doubt projection: confabulation-prone
rows have lower doubt than known-correct answered rows, so the gate fires when
`-z_d` exceeds a threshold selected on a FIT split. The actuator is a `c_hat`
caution direction, constructed by orthogonalizing a raw refuse/control direction
against the doubt and confab-propensity controls. Later J-space experiments reuse
per-layer versions of these gates and write directions.

The J-space line adds a Jacobian lens. For a hidden-state vector at a layer, the
J-lens estimates how that vector would verbalize through the model's final-token
logit space. We use it in two ways: first as a read-only localization diagnostic,
and then backward as a source of token-target write directions.

### 3.3 Outcomes and controls

The main behavioral outcome is **clean tightening**: a row that previously
confabulated is converted into a naturally terminating, well-formed JSON refusal
with a single answer field. The main cost outcome is **known-correct false
refusal**: a row previously answered correctly is no longer a well-formed correct
answer after intervention.

Controls are matched to the mechanism:

- text-injection arms use placebo or permuted labels with the same prompt form;
- reward arms compare true-sensor and permuted-sensor rewards;
- hidden-state write arms use random-direction controls and permuted gates;
- J-space token-target arms use a matched random J-space direction.

---

## 4. Results

### 4.1 Directly writing or telling the model its readout mostly fails

The first actuation attempt asked the most direct question: if gate and dial
directions are readable, can we write them back into the model at the positions
where they read best?

On Qwen3.5-4B, an 8-cell steering grid crossed two signals (gate/dial), two
positions (anchor/end), and two channels (activation write/text injection). No
registered effect gate passed. Gate-at-anchor activation steering was flat across
the alpha sweep; dial-at-end activation steering was flat; text-injection cells
were also flat under their registered metrics. This was the first evidence for
the read/write split: the signal was present, but the tested channels did not
make the policy use it.

A natural objection is that the text was phrased unnaturally. We therefore tested
stronger first-person phrasing: "I am X% sure..." plus an explicit action rule.
The result remained negative. The gate cell showed a small, real trickle of
rule-following (+2.0 points abstention, CI excluding zero) but missed the +10
point gate by a factor of five. Dial cells did not improve revision behavior:
the late-position metric was instrument-saturated, and the final-thought version
missed with a -2.7 point delta whose CI included zero. The strongest natural
language framing did not open the channel at useful magnitude.

**Interpretation.** The model can read the state; an external system can read the
state; but placing a description of that state inside the generation trajectory
does not reliably make the model act on it.

### 4.2 System-prompt authority moves behavior, but not by own-readout consultation

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

Internal-state instrumentation sharpened the picture. The doubt axis did not
move semantically with the prompt; compliance traveled primarily through a
caution/policy axis. A divergent-pool follow-up then separated rows where the
model's own readout and the gold label disagreed. Release congruence with the
model's own readout was a precise zero: -0.21 points, CI [-4.45, +4.10]. A
pre-registered positive-control addendum verified that the instrument was live
(+50.98 point induced refusal on a caution-representative stratum). The verdict:
system prompts move policy by compliance and boundary distance, not by making the
model consult its own readout.

**Interpretation.** Authority is an actuator, but it is not the self-monitoring
channel we wanted. It can install caution from outside, even against the model's
own knowledge.

### 4.3 Rewarding the readout also fails to train consultation

If prompting does not make the model consult its readout, perhaps training can.
The probe-as-reward cell trained two clean-SFT starting checkpoints with the same
GRPO recipe. In the TRUE arm, reward agreement was computed from a frozen probe
read from the policy's own pre-generation state. In the PERMUTED arm, the sensor
was permuted within class. The primary held-out metric was congruence between the
final policy behavior and the arm's own freshly refit eval probe.

The instrument was valid: both arms completed all 2934 scheduled steps, no
tripwire halted, and fresh probes on the final checkpoints still read gold at
OOF AUROC 0.9948 and 0.9946. But the result went the wrong way. TRUE congruence
was 59.75% versus PERMUTED 76.75%, a -17.0 point differential with CI
[-21.5, -12.5]. The TRUE arm preserved some useful behavior, such as fewer
unknown hallucinations than the control, but on the registered question it did
not learn to consult its own readout.

**Interpretation.** Reward can shape behavior correlated with the sensor, but
this does not imply policy-readout congruence. On rows where content and readout
dissociate, the policy sides with learned content/boundary behavior rather than
with its own current probe state.

### 4.4 A gated hidden-state controller succeeds

The first robust positive result came from changing the intervention form. Rather
than asking a single direction to be both sensor and actuator, the successful
controller separates them:

1. a **doubt gate** decides which rows look like confabulations;
2. a fixed **caution snap** writes only those fired rows to a selected refusal
   setpoint.

This design was motivated by a bf16 diagnostic: an unconditional caution snap
could convert confabulations into clean refusals, but it was not selective. At a
realized write around 200, ungated dosing tightened confab rows well but also
caused many known-correct rows to refuse. The gate creates selectivity by mostly
choosing the confab rows.

On the held-out signed run, the raw-base Qwen3-4B controller passed all gates.
The doubt gate's FIT AUC was 0.9955. On held-out rows, gated clean tightening was
136/185 = 73.5%, Wilson CI [66.7, 79.3], clearing the >=60% floor and the lower
CI >50% requirement. Known-correct false refusal was 8/258 = 3.1%, CI [1.6,
6.0], clearing the <=5% point floor and <10% upper CI requirement. A
random-direction write on the same fired rows produced only 13/185 clean
tighten, and a permuted gate produced 59/258 known-correct cost. The effect
depends on both the caution direction and the doubt gate.

**Interpretation.** The model need not internally choose to consult its readout
for the system to use that readout. The readout can gate an external controller.
This is the first clean selective actuation result in the arc.

### 4.5 J-space localizes a better write site

The successful gate-and-snap controller still raised a mechanistic question:
where should a write occur? The inherited caution write site was an L34
residual-stream direction. A Jacobian-lens characterization asked whether this
site lies inside or outside the model's workspace-like verbalizable band.

The instrument passed a correctness smoke: the final-layer J-lens closely
matched the direct unembed baseline over 1000 prompts, with mean cosine 0.9811,
mean top-10 overlap 0.82, and top-1 match 3/5 over five random directions. The
H1 read then found that caution-like directions verbalized as first-person,
absence, error, and impossibility tokens, while the doubt direction verbalized
more as answer/reply tokens. The layer profile localized a workspace-like band
to hs=23-29, peaking at hs=26. The inherited L34 direction corresponds to hs=34,
just after that band.

The first causal layer sweep at a fixed absolute dose stopped at G0 because dose
200 collapsed hs23 and hs26. FIT-only dose calibration fixed that: usable
non-collapsing setpoints were recovered at hs23=25, hs26=75, hs29=125, and
hs34=175. The held-out contrast then supported the layer-site hypothesis. Over
443 held-out rows, hs23 achieved 165/185 clean refusals (89.2%) versus hs34
123/185 (66.5%), a +22.7 point improvement. Known-correct cost rose only from
7/258 (2.7%) to 9/258 (3.5%), a +0.78 point delta. hs34 remained viable, but it
was not optimal.

**Interpretation.** The late write site was not dead, but it was suboptimal.
Writing near the workspace-like band made the same regulated caution snap
substantially more effective on this surface.

### 4.6 Token-targeted J-space writing is real but redundant

Finally, we tested a more literal J-space idea: build a hidden-state direction
that raises natural refusal tokens and lowers answer/reply continuation tokens.
The token bundle was fixed and audited before held-out evaluation. Positive
targets included refusal pieces such as `I`, `know`, `cannot`, `unable`,
`unknown`, and `insufficient`; negative targets included English answer/reply
tokens and Chinese answer/reply tokens that appeared in the J-lens readout, such
as answer/reply forms.

At the selected FIT dose, the J-token direction wrote accurately and safely. It
was also non-inert: alone, it converted 88/185 confab rows into clean refusals
(47.6%). But it did not improve the already strong hs23 caution snap. The
baseline hs23 `c_hat_only` arm reached 165/185 = 89.2%. The hybrid
`c_hat_plus_j_token` arm reached 166/185 = 89.7%, only +0.54 points. Known-correct
cost increased by only +0.39 points, so safety was not the issue. The issue was
redundancy: the natural token-target write added one extra cleaned confab row on
top of a controller that was already doing the job.

**Interpretation.** Verbalizable token directions can be real actuators without
being useful additive controllers. A direction that "points toward refusal
tokens" is not automatically a better policy intervention.

### 4.7 Supporting pattern beyond the core epistemic arc

Two adjacent screens support the same read/write caution, though they are not
main-line evidence for the epistemic controller.

The dark-actuator screen validated the positive-control caution lever: the
positive control converted 79/80 confab rows into coherent refusals while
negative and random controls stayed near floor. But the broader candidate screen
was null: apparent candidates were artifacts of malformed-output scoring,
under-dosed random controls, and off-manifold overdrive.

A separate answer-sycophancy readout found a readable L24 direction on Qwen3-4B,
but the actuator failed to beat a matched control. The write path fired and a
neutral guardrail passed, but the anti-sycophancy-vs-control gate failed with
diff 0. This is outside the core paper claim, but it reinforces the broader
lesson: readable behavioral directions do not automatically become clean
actuators.

### 4.8 Cross-family replication surfaces an instrument problem, not (yet) a mechanism problem

The gated caution controller in Section 4.4 was fit and evaluated on raw-base
Qwen3-4B alone. A cross-family test asked whether the same doubt-gated caution
write, refit at each family's own atlas-located workspace-band site, actuates
refusal on Llama-3.2-3B and Mistral-7B-v0.3. The initial run
(`rr-cross-family-raw-refusal`) landed a null shape on both families under a
locked three-phrase canonical refusal detector. On the mistral leg, an
unblinded post hoc hand-read of the non-refused rows found well-formed
abstention idioms the detector's fixed vocabulary did not count, suggesting
the null was partly a detector-width artifact rather than an absence of the
behavior.

A confirmatory replication (`rr2-mistral-adjudicated-refusal-confirm`) tested
that suggestion directly, on fresh held-out mistral rows never seen by the
detector-width caveat, using two registered instruments: a widened automatic
pattern detector (detector v2) and a primary blinded adjudication lane in
which context-free graders scored bare, unlabeled generation text against a
fixed abstention rubric, mixed with clear-positive and clear-negative decoy
rows to certify grader calibration before unblinding. The caveat was
confirmed on its own terms: gated fired-confab adjudicated refusal reached
911/1303 = 0.699 (Wilson 95% CI [0.674, 0.723]) against a 0.60 floor,
well-formedness held at 0.987, and known-correct false refusal stayed at
2/382 = 0.0052 (CI [0.0014, 0.019]) against a 0.05 ceiling. Both the benefit
and cost gates passed.

The placebo gate did not. A random-direction control matched in magnitude to
the true caution write lifted adjudicated confab abstention from a
368/1312 = 0.280 baseline to 465/1312 = 0.354, a +7.39 point rise against the
registered 2-point no-op tolerance. Per the pre-registered falsifier, this
failure alone falsifies the claim that the write is direction-specific on
mistral, even though the gated arm's own lift over baseline (+41.9 points,
5.7 times the random direction's) remains far larger. The result is reported
straight: the mistral cross-family test is falsified, not because the caution
write failed to move behavior, but because a magnitude-matched random
direction also moved it, and the registered tolerance for "moved it" was too
strict for this family's baseline.

That last clause turned out to matter more than it first appeared. A
follow-up CPU-only re-read (`abstention-wide-instrument-calibration`) applied
the same wide two-instrument stack to existing generation logs across three
families and found that undosed hedging is itself family-graded:
wide-instrument confab abstention baselines are 0.104 for Qwen3.5-4B, 0.164
for Llama-3.2-3B, and 0.280 for Mistral-7B-v0.3, each well above what the
narrow canonical detector reports (0.044, 0.036, and 0.159 respectively,
undercounts of +6.1, +12.9, and +12.2 points). The placebo response is
family-specific in sign, not just magnitude: on Qwen3.5-4B, a
matched-magnitude random direction at the promoted held-out operating point
suppressed wide-instrument hedging by 5.13 points (paired baseline 0.108
[0.092, 0.126] versus random-direction 0.057 [0.045, 0.071], non-overlapping
CIs), the opposite direction from mistral's +7.39 point recruitment. Llama
has no placebo generation text on disk and so cannot be scored on this axis.
Known-correct (cost) rates were zero everywhere they were covered, on every
family and arm.

**Interpretation.** The RR2 falsification and the calibration re-read
together license a narrow but firm claim: the flat, small, symmetric placebo
tolerance this program inherited from a Qwen-scale, apparently near-zero
baseline world is the wrong instrument for cross-family direction-specificity
testing. It is not evidence that random-direction writes are generically
confounded with the true caution write; on Qwen3.5-4B the matched-magnitude
random direction moved hedging in the opposite direction from the true
write's effect. It is evidence that "no-op within N points" cannot be
registered without first measuring the family's own wide-instrument baseline
and without deciding, in advance, whether the criterion should be a flat
tolerance or an effect-ratio gate. The calibration study's design rule for
successors is explicit: register the placebo criterion against the measured
per-family baseline (qwen 0.104, llama 0.164, mistral 0.280), and tolerate
several points of non-directional movement in either sign, for example via
an effect-ratio gate comparing gated lift to the absolute random lift rather
than a flat symmetric band. Section 4.9 shows this rule is still incomplete
as stated: a single random seed is not enough to size either side of that
comparison, because mistral's random-direction response at matched magnitude
spans -7.4 to +21.8 points across three fresh seeds at the same site and
dose. The design rule for any future direction-specificity placebo criterion
must therefore also require a multi-seed (K >= 3) random-direction ensemble
with a max-over-K (or pre-stated equivalent) denominator, not a single seed
(Section 4.9).

This also qualifies how the narrow-detector-graded random-direction and
permuted-gate controls elsewhere in this paper should be read. The Qwen3-4B
raw-base gate-and-snap result in Section 4.4 (random-direction control:
13/185 clean tighten; permuted-gate control: 59/258 known-correct cost) and
the mid-band layer-site contrast in Section 4.5 were graded under the
program's original narrow detector, not the wide two-instrument stack
introduced here, and neither experiment has been re-scored under it. Given
the undercount margins measured above, and given that Qwen's own
wide-instrument placebo response, on a different held-out operating point
than either of those two experiments, is suppressive rather than confounding,
there is no positive evidence that these specific controls are compromised.
But there is now a standing, program-level reason not to treat a small
narrow-detector placebo delta as automatically clean: it should be read as
provisional until re-checked under the wide instrument, particularly before
any of these results are promoted from exploratory to headline.

### 4.9 A corrected effect-ratio criterion still falsifies mistral direction-specificity, and reveals why single-seed placebo readings mislead

A third experiment (`rr3-corrected-placebo-replication`) applied exactly the
design rule the calibration study called for. Before any new data, it
registered an effect-ratio primary gate in place of a flat tolerance: the
gated arm's confab lift over baseline must be at least 3x the MAXIMUM
absolute random-direction lift over baseline across K >= 3 fresh,
pre-registered random seeds distinct from RR2's (a max-over-K denominator,
the most conservative of three constructions considered, chosen so a single
lucky random direction cannot set the gate). The gated and baseline mistral
arms were regenerated at the same fixed operating point as RR2 (hs16, dose
12 sigma_c) and reproduced RR2's generation text byte-for-byte, an integrity
check rather than fresh evidence; what is fresh is a re-adjudication under a
new blinded lane and three newly drawn random seeds.

The primary gate failed. Gated confab lift over baseline was +40.9 points
(baseline 375/1312 = 0.286, gated 911/1312 = 0.694). The three fresh random
seeds produced lifts of +13.3, -7.4, and +21.8 points; the max-over-K
denominator is therefore 21.8 points, and the effect ratio is 40.9/21.8 =
1.87, short of the 3.0 floor
(`experiments/rr3-corrected-placebo-replication/AMENDMENT.md` Outcome). The
benefit and cost legs reproduced RR2 almost exactly: fired-confab
adjudicated refusal 911/1303 = 0.699 (Wilson 95% CI [0.674, 0.723]) against
the 0.60 floor, well-formedness 0.987, and known-correct adjudicated false
refusal 2/382 = 0.0052 (Wilson 95% UCB 0.019) against the 0.05 ceiling. An
adversarial red-team review certified the failure across six registered
attack surfaces before the verdict was recorded: the three random directions
were genuinely random (cosine similarity to the true caution direction <=
0.015), magnitude-matched at the mechanism level (erase-write setpoint
identical to the gated write within 0.004), scored on identical populations
with exact arithmetic, and the failure is robust to an alternative rate rule
(detector-only ratio 1.91) and to a mean-of-K denominator (ratio 2.89) in
place of max-over-K. Per RR3's registered posture, this is reported as a
corrected-criterion re-adjudication of the same claim RR2 tested, not as an
independent fresh replication: RR2's falsified verdict stands, and now
stands for a stronger reason than the flat tolerance that fired there
(`experiments/rr3-corrected-placebo-replication/AMENDMENT.md`, Motivation
and posture; Outcome).

**Methods finding: single-seed placebo readings are unreliable.** The three
fresh random seeds, at the same layer, dose, and population, produced lifts
spanning -7.4 to +21.8 points, a 29-point spread from seed choice alone.
RR2's single random seed (+7.39 points, cited in Section 4.8) and the
calibration study's family-signed placebo map (mistral +7.39, qwen -5.13;
Section 4.8) are each a single draw from that distribution. RR3's Outcome
states this directly: "the calibration's family-signed placebo map should be
read with per-seed variance in mind"
(`experiments/rr3-corrected-placebo-replication/AMENDMENT.md`, "What the
falsification means"). This is now a standing constraint on how any placebo
delta reported from a single seed, anywhere in this paper, should be read.

**Rider: the llama placebo leg completes the three-family sign map at
null.** RR3 also ran the placebo measurement missing from the family x
placebo-sign map since the calibration study scoped it out for lack of
on-disk generation text (Section 4.8): a llama random-direction dose ladder
at llama's own atlas site (hs20), one fresh seed per rung across the
registered dose grid, on both the confab and known-correct populations. At
the matched-magnitude reference dose (12 sigma_c), the llama confab lift was
+0.1 points: null. The ladder stayed flat through 16 sigma_c (-3.1 to +0.9
points, all inside the +/-8 point descriptive envelope), with a single
+8.5-point excursion at the top rung (20 sigma_c) that lands marginally
outside the envelope; known-correct false refusal grew with dose, from 0.3%
at 2 sigma_c to 6.0% at 20 sigma_c. A parallel mistral dose ladder (hs16, one
fresh seed per rung) produced lifts of -3.8 to +4.2 points across the same
grid, all inside the envelope with no monotone dose-response, reinforcing
the single-seed-instability finding above. Per RR3's pre-stated
interpretation rule, a null llama result implies placebo response is not a
smooth function of a family's baseline hedging rate, while a positive result
would have supported reading the sign map as monotone in baseline (llama's
0.164 baseline sits between qwen's 0.104 and mistral's 0.280). The null
result falsifies the monotone-in-baseline reading: the pre-registered
scoreboard records the null call as correct and the monotone-in-baseline
call as unsupported
(`experiments/rr3-corrected-placebo-replication/AMENDMENT.md`, Rider;
Predictions scoreboard adjudication). The family x placebo-sign map is now
complete in sign across all three families: qwen suppresses (-5.13), llama
is null (+0.1 at matched magnitude), and mistral recruits on average but
with wide single-seed variance (-7.4 to +21.8).

**Interpretation.** The corrected effect-ratio criterion is a stricter test
than the flat tolerance it replaced, not a looser one, and it survives
adversarial review specifically because it is conservative (max-over-K, not
mean- or single-seed). Mistral's direction-specificity claim, as tested at
this single operating point, does not clear it. This confirms rather than
overturns Section 4.8's standing lesson that a large gated effect does not
by itself establish direction-specificity; what changes is the reason. RR2's
flat tolerance failed because it was miscalibrated to a near-zero-baseline
world. RR3's effect-ratio gate failed because mistral's random-direction
response at this site and dose is itself high-variance across seeds, and one
of three seeds recruited more than half of the gated effect's magnitude.
Both are placebo-instrument findings, not evidence that the gated write
itself is inert: benefit and cost reproduced RR2 exactly.

---

## 5. Synthesis: The Actuation Map

The results form a channel map rather than a single pass/fail story.

| Channel | What worked | What failed | Lesson |
|---|---|---|---|
| Within-generation text | Small gate-side trickle under strong first-person rule | No useful dial/revision effect; no registered success | Text inside the trace is attenuated, not a faithful readout channel |
| System prompt | Large behavior movement when labels are correct | Divergent-pool congruence with own readout is zero | Authority moves policy; it does not establish self-consultation |
| Reward | Some boundary-preserving behavior | TRUE sensor less congruent than PERMUTED | Reward can train correlates without readout consultation |
| Unconditional caution write | Can induce refusal | Non-selective; false-refuses known-correct rows | Write supplies action, not selectivity |
| Doubt-gated caution snap | 73.5% clean tighten, 3.1% known cost | Release direction remains null | Gate supplies selectivity; snap supplies refusal |
| Mid-band J-space write | hs23 beats hs34 by +22.7pp | Needs layer-specific dose; not yet cross-family | Write site matters |
| Natural J-token write | Non-inert token-only effect | Redundant with `c_hat` hybrid | Verbalizable token target is not enough |
| Cross-family gated snap (mistral) | Wide-instrument adjudicated refusal 69.9%, cost pristine (0.52% known-correct) | Direction-specificity falsified twice: under a flat 2-point placebo tolerance, and again under a corrected 3x effect-ratio gate (ratio 1.87) driven by high seed-to-seed variance in mistral's random-direction response (-7.4 to +21.8pp); llama placebo response is null at matched magnitude | Placebo criteria must be calibrated to each family's own wide-instrument baseline AND evaluated against a multi-seed random-direction ensemble with a pre-stated denominator rule (RR3 used the conservative max-over-K); a single seed can materially misstate either the baseline delta or an effect-ratio denominator |

The practical controller that emerges is not "make the model introspect." It is:

1. read the model's epistemic state externally;
2. use that readout as a gate;
3. write a calibrated policy direction only where the gate fires;
4. choose a layer/site where the write is inside or near the workspace-like band;
5. keep random-direction, permuted-gate, and known-correct cost controls in the
   loop.

This design is closer to a control system than to a prompt. The model's policy
does not need to endorse or understand the sensor. The controller uses the
sensor.

---

## 6. Discussion

### 6.1 Why "presence implies use" fails

The readout papers show that the model contains useful epistemic information.
The present paper shows that this information is not automatically used by the
generation policy. There are at least three separable bottlenecks:

- **channel bottleneck:** putting the signal into a low-authority text channel
  may not make it causal;
- **policy bottleneck:** high-authority text may move policy by obedience rather
  than by state alignment;
- **write-site bottleneck:** a residual direction may be readable at one layer
  and writable at another.

This explains why a probe can be near-perfect while steering is flat, and why a
prompt can change refusal behavior without improving readout congruence.

### 6.2 Why the gate matters

The caution write is not selective. If applied indiscriminately, it can make
known-correct rows refuse. The successful intervention is selective because the
doubt gate decides where to apply it. This is the same separation used in
ordinary control systems: sensor, controller, actuator. The sensor identifies
the failure mode; the actuator executes one simple move; the controller prevents
the actuator from firing everywhere.

### 6.3 Why J-space matters

The J-space diagnostic gives a mechanistic explanation for one repeated pattern:
directions are portable as readouts but fragile as writes. If the reportable or
workspace-relevant component of a concept lives in a mid-to-late band, late
residual writes may be downstream of the useful broadcast site. The calibrated
layer contrast supports that account on raw-base Qwen3-4B, but it is not yet a
general claim. It needs same-model replication and cross-family replication.

### 6.4 Limits

This is an exploratory paper. The largest claims are qualitative and mechanistic,
not population effect-size estimates. Key limits:

- many actuation results are single-model or single-family;
- some early negative cells carried instrument caveats later fixed in follow-up
  work;
- the strongest positive J-space layer-site result is currently surface-local to
  raw-base Qwen3-4B bf16;
- reward-channel evidence is single-seed;
- token-target J-space writing has only tested the natural observed token bundle,
  not dense or multilingual alternatives;
- the random-direction and permuted-gate controls in Sections 4.4 and 4.5 were
  graded under the program's narrow detector and have not been re-scored under
  the wide two-instrument stack introduced for cross-family work in Section
  4.8; a flat, family-agnostic placebo tolerance is now known to be
  miscalibrated to at least one family's baseline hedging rate;
- random-direction placebo response is itself high-variance across random
  seeds at matched magnitude: mistral's confab lift at RR3's single fixed
  operating point ranged from -7.4 to +21.8 points across three fresh seeds
  (Section 4.9). Any placebo delta reported from a single seed anywhere in
  this paper, including the qwen and mistral family-signed readings in
  Section 4.8, should be read as one draw from a wide distribution rather
  than a family constant.

### 6.5 Next study: the amped-up replication and model sweep

The next study should be designed before running, not inferred from this draft.
Recommended escalation:

1. **Same-model replication.** Re-run the gated hs23/hs29 versus hs34 layer-site
   contrast on a fresh held-out split or newly staged rows for Qwen3-4B bf16.
2. **Cross-model workspace localization.** Run the J-lens profile and direction
   verbalization on at least one Qwen size neighbor and two non-Qwen families.
3. **Cross-family gated snap.** Two attempts on mistral
   (`rr-cross-family-raw-refusal`, `rr2-mistral-adjudicated-refusal-confirm`,
   `rr3-corrected-placebo-replication`, Sections 4.8-4.9), both at the same
   fixed operating point (hs16, dose 12 sigma_c), confirmed the benefit and
   cost gates under a wide, blinded adjudication instrument (69.9%
   adjudicated refusal, 0.52% known-correct cost) but falsified
   direction-specificity twice: first under a flat 2-point placebo tolerance
   later shown to be miscalibrated to mistral's own 28.0% undosed hedging
   baseline (`abstention-wide-instrument-calibration`), and then under the
   corrected effect-ratio gate that calibration study's design rule called
   for (gated lift >= 3x the max-over-K lift of K >= 3 fresh random seeds),
   which also failed (ratio 1.87, Section 4.9) because mistral's
   random-direction response at this site and dose is itself high-variance
   across seeds (-7.4 to +21.8 points). Repeating the same operating point
   with the same K is not expected to change the outcome; a future attempt
   at establishing mistral direction-specificity needs either a different
   write site or dose where the random-direction response is less variable,
   or a larger K to tighten the max-over-K denominator. Llama's placebo
   response, measured for the first time by RR3's rider, is null at matched
   magnitude (Section 4.9), but llama's gated caution snap itself remains
   completely untested. Any future attempt, on llama or elsewhere, must
   register its placebo criterion against that family's own measured
   wide-instrument baseline (Section 4.8) with a multi-seed (K >= 3)
   random-direction ensemble and a max-over-K (or pre-stated equivalent)
   denominator (Section 4.9), not a single seed and not a flat
   small-tolerance band.
4. **Dense-token screen.** Separately screen abstract or multilingual token
   bundles before any causal hybrid run. Do not alter the natural-token result
   post hoc.
5. **Generic tuner support.** Promote compound multi-readout writes into the
   Synaptic Tuner config surface so future runs are config-driven, resumable, and
   comparable across models.

The success criterion for the next paper-quality claim should be stricter than
this one: same-model replication plus at least two-family support for the
workspace-band advantage, with pre-stated cost guards and placebo controls.

---

## 7. Conclusion

Small language models can know internally that they do not know, and external
systems can read that state. Making the model itself use that state is harder.
Text prompts can move policy without consulting the readout; rewards can train
correlates without congruence; unconditional writes are non-selective. The first
clean positive controller in this arc is not a prompt or a reward but a gated
hidden-state intervention: read doubt, fire selectively, and write caution near a
workspace-like layer band.

The emerging lesson is pragmatic. Treat epistemic readouts as sensors first. Use
them to gate interventions. Calibrate the actuator separately. Then replicate
the layer and channel before claiming the model has learned to consult itself.

---

## Appendix A. Traceability Map

This appendix intentionally names internal amendment/experiment labels so the
draft can be audited. Reader-facing prose should eventually move most labels to a
provenance appendix or supplement.

| Paper claim | Governed source | Status |
|---|---|---|
| Direct activation/text "turn the probe around" cells did not move behavior at registered gates | `experiments/causal-confidence-steering/AMENDMENT.md` §7 | Falsified / channel shut |
| First-person natural-language confidence framing did not open the text channel at useful magnitude | `experiments/first-person-injection/AMENDMENT.md` §7-8 | Ambiguous-leaning negative |
| Doubt-coupled activation write carried information in a trained-checkpoint intervention | `experiments/doubt-regulated-caution/AMENDMENT.md` §8 | Positive |
| High-authority system prompt moved behavior by +18.0pp over permuted | `experiments/second-person-doubt-prime/AMENDMENT.md` §8 | Pass |
| Inverted system prompt showed asymmetric compliance, not belief revision | `experiments/oracle-dissociation-prime/AMENDMENT.md` §9 | Pass |
| Divergent-pool test found zero own-readout congruence; Addendum A1 certified the instrument | `experiments/divergent-pool-own-readout/AMENDMENT.md` §9-10 | H-compliance |
| Probe-as-reward TRUE arm failed to train readout consultation | `experiments/probe-as-reward/AMENDMENT.md` §5 | Null |
| Raw-base doubt-gated caution snap produced 73.5% clean tighten at 3.1% known cost | `experiments/doubt-gated-caution-tighten/AMENDMENT.md` Outcome | Exploratory pass |
| J-lens localized workspace-like band to hs=23-29, peak hs=26; L34 maps after band | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md` Outcome | Exploratory diagnostic |
| Layer-specific calibration recovered non-collapsing setpoints | `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md` Outcome | FIT-only pass |
| Held-out mid-band layer contrast: hs23 89.2% vs hs34 66.5% | `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md` Outcome | Exploratory pass |
| Natural token-target J-space write was non-inert but redundant with `c_hat` | `experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md` Outcome | Exploratory falsification |
| Dark-candidate screen validates positive caution lever but promotes no dark candidates | `experiments/dark-actuator-screen/AMENDMENT.md` Outcome | Supporting null |
| AQ sycophancy actuator found readable direction but no clean actuator vs control | `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md` Outcome | Supporting exploratory null |
| Mistral cross-family gated write cleared benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) gates under a wide blinded instrument but failed the flat 2-point placebo tolerance (+7.39pp random-direction lift) | `experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md` Outcome | Exploratory falsification (placebo-criterion design flaw, not benefit/cost) |
| Wide-instrument baseline hedging and placebo response are family-graded and family-signed (qwen -5.13pp suppression, mistral +7.39pp recruitment); flat placebo tolerances must be registered per-family | `experiments/abstention-wide-instrument-calibration/AMENDMENT.md` Outcome | Exploratory instrument calibration, resolved |
| Corrected effect-ratio placebo criterion (>= 3x max-over-K fresh-seed random lift) still falsified mistral direction-specificity (ratio 1.87) while reproducing RR2's benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) exactly; red-team certified robust to detector-only and mean-of-K denominators; mistral's random-direction lift spans -7.4 to +21.8pp across three fresh seeds; llama rider placebo response is null at matched magnitude, completing the three-family sign map | `experiments/rr3-corrected-placebo-replication/AMENDMENT.md` Outcome | Exploratory falsification (corrected-criterion re-adjudication of the RR2 claim, benefit/cost intact) |

## Appendix B. Figure Plan

1. **Figure 1: Read vs write map.** Schematic from Paper 3/4 readouts to Paper 5
   actuation channels.
2. **Figure 2: Channel ladder.** Text injection, system authority, reward, and
   hidden-state write results on a common "readout consultation" axis.
3. **Figure 3: Gated caution controller.** Confab clean_tighten and known-correct
   false-refusal rates for no-op, random direction, permuted gate, and real gate.
4. **Figure 4: J-space profile.** Effective-dimensionality fraction by hs layer,
   with hs23/26/29 band and hs34 reference marked.
5. **Figure 5: Layer-site contrast.** Held-out clean_tighten and known-cost bars
   for hs23/hs26/hs29/hs34.
6. **Figure 6: Token-target negative.** `c_hat_only`, `j_token_only`,
   `c_hat+j_token`, and `c_hat+random_j` outcomes.

## Appendix C. Open Work Before Submission

- Reconcile this draft against `archive/papers/retired/results-provenance-inventory.md`.
- Decide whether AC belongs in the main result body or only as the predecessor
  to the raw-base gate-and-snap result.
- Convert amendment-label prose into reader-facing condition names.
- Add bibliography and related-work citations for activation addition,
  refusal steering, Jacobian lens / global workspace, and representation
  engineering.
- Build figures from committed aggregate artifacts only.
- Run the planned cross-model J-space/gated-snap replication before promoting
  the workspace-band result from exploratory to headline.
- Register any future direction-specificity placebo criterion against the
  per-family wide-instrument baseline measured in Section 4.8 (qwen 0.104,
  llama 0.164, mistral 0.280), not a flat symmetric tolerance, and with a
  multi-seed (K >= 3) random-direction ensemble and a max-over-K (or
  pre-stated equivalent) denominator rather than a single seed, per RR3's
  finding that a single seed materially misstates mistral's random-direction
  response (Section 4.9).
- Run llama's gated caution snap (not yet attempted; only its placebo
  response has been measured, at null, in Section 4.9) before claiming or
  ruling out cross-family direction-specificity for that family.
