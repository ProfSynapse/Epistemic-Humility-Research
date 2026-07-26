---
<!--
TITLE CANDIDATES (writer proposal, PI picks; spec docs/preparation/paper5-rewrite-spec.md section 3 ruling 1):
1. "Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Known-Unknown State in Small Language Models"
   Minimal-diff option: keeps the existing lead phrase and structure that papers 3/4 already link against, swaps only the retired "Epistemic State" for the governed known-unknown vocabulary.
2. "Look Before You Speak: Operating-Point-Dependent Selectivity in Actuating Known-Unknown State"
   Foregrounds the paper's actual finding after this rewrite (the gate's role changes with dose regime) rather than the older channel/gate/workspace framing, while keeping the "Look Before You Speak" phrase the PI ruling allows.
3. "The Write Sorts Itself: Gate, Channel, and Workspace Constraints on Actuating Known-Unknown State"
   Leads with the mid-band positive result (the write self-sorts without the gate) as the memorable hook, most distinctive of the three, at the cost of not previewing the overdrive-regime half of the thesis.
Working title below is candidate 1, chosen for continuity with existing cross-references from papers 3 and 4; PI may swap at PR time, in which case those cross-references need a follow-up fix (tracked in the writer's report, not in scope for this rewrite).
-->
title: "Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Known-Unknown State in Small Language Models"
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
  experiments/correctness-direction-rotation/AMENDMENT.md, and
  experiments/correctness-subspace-overlap/AMENDMENT.md.
notes: >
  Draft v0 is a synthesis scaffold, not submission-ready. It deliberately
  separates reader-facing claims from amendment traceability. The core results
  are single-model or surface-local exploratory unless explicitly marked
  otherwise. A first cross-family attempt on mistral and a follow-up
  wide-instrument calibration study are now folded in as Section 4.8. A
  corrected-criterion re-adjudication under a registered multi-seed
  effect-ratio placebo gate, plus a three-family placebo-sign-map rider, is
  folded in as Section 4.9, and a multi-seed placebo seed-distribution census
  that measures each family's matched-magnitude random-direction null across 15
  fresh seeds is folded in as Section 4.10; all remain exploratory and
  pre-headline. The next planned step is a larger cross-model / cross-family
  actuation study registered against the per-family placebo null distribution
  the census measured (Section 4.10). Section 6.5 now also cites two
  companion-paper null results (a direct cross-checkpoint measurement of the
  correctness direction's own rotation, and a follow-up asking whether a
  shared subspace explains its partial transfer) as motivation, not evidence,
  for treating the correctness axis as a harder cross-family generalization
  problem than the answerability axis this paper actuates on.
---

# Readable Is Not Writable: Channel, Gate, and Workspace Constraints on Actuating Known-Unknown State in Small Language Models

*Draft v0. Companion to [*Knows but Doesn't Say*](../paper-3-knows-but-doesnt-say/manuscript.md)
and [*It's What's on the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md).*

*Scope note on "epistemic state": throughout this paper the phrase names what a
linear readout of the hidden state reports about answerability and caution, not
a claim that the model represents its own doubt as a mental state. Where the
program previously used mentalistic names for these readouts (the doubt
direction, the doubt gate, doubt-coupling), this paper follows
`papers/common/terminology.md` and uses the known-unknown (KU) vocabulary
instead, retiring "doubt" from running prose except in quotations and governed
filenames.*

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

Second, hidden-state actuation does work when the problem is posed as a
KU-gated controller rather than as an unconditional write. A KU-gated caution
snap on raw-base Qwen3-4B converted 136/185 held-out confabulations into
clean refusals (73.5%, Wilson 95% CI [66.7, 79.3]) while producing 8/258
false refusals on known-correct answers (3.1%, CI [1.6, 6.0]); random-direction
and permuted-gate controls did not reproduce the result. Which component
supplies that selectivity, however, is operating-point-dependent rather than a
universal property of the write. At this same overdrive dose (L34, dose 200),
a separately registered comparison shows an unconditional write damages 60.1%
of held-out known-correct rows versus 3.1% gated, a 57.0-point gap (McNemar
p = 4.2e-43): here the gate is the sole source of selectivity. At mid-band
doses (qwen hs20 = rd 0.625, dose_abs 12.608; mistral hs16 = rd 0.500,
dose_abs 3.665), a controlled
factorial found the
write itself is already content-selective: a permuted-gate control reaches
confab abstention 0.550-0.600 against the true gate's 0.689-0.694, and the
KU-readout gate's own contribution, Gap_Sel(c_hat), is real but sub-floor
(0.148 qwen, 0.129 mistral, against a registered 0.20 floor). At mid-band the
gate's role reduces to a modest selectivity increment plus cost governance,
not the source of selectivity. The lesson is regime-dependent, not universal:
overdrive makes the gate essential, mid-band lets the write self-sort with the
gate tightening the margins. Naming follows this reading throughout:
"known-unknown (KU)" replaces "doubt", describing how the readout was fit
rather than attributing a mental state to the model.

Third, write location matters. A Jacobian-lens diagnostic localized a
workspace-like J-space band in Qwen3-4B around hs=23-29, peaking at hs=26, while
the inherited L34 write site maps to hs=34 just after that band. After
layer-specific dose calibration, held-out mid-band writing beat the late hs34
reference: hs23 (rd 0.639) reached 165/185 clean refusals (89.2%) versus
hs34 (rd 0.944) 123/185
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
2. **Separate sensing from actuation, but which part supplies selectivity is
   regime-conditional.** The successful controller is a two-part system: a
   known-unknown (KU) readout gate decides which rows receive a write, and a
   caution snap supplies the refusal behavior. At an overdrive dose, the snap
   alone is not selective and the gate is essential. At a mid-band dose, the
   snap is already content-selective on its own; the gate's contribution
   there is a modest, sub-floor increment plus cost governance, not the
   source of selectivity.
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

**Reporting convention for write sites.** Write sites are named by their raw
hidden-state index (`hsN`) because that is how each governing amendment
registered them, but raw indices are not comparable across families with
different block counts, and several comparisons in this paper are cross-family.
We therefore also give relative depth, `rd = layer_idx / num_hidden_layers`,
wherever a site is compared against a site in another family. Block counts,
each verified 2026-07-09 from the checkpoint's own `config.json`
(`experiments/j-space-cross-family-layer-contrast/families/*.yaml`), are:
Llama-3.2-3B 28, Mistral-7B-Instruct-v0.3 32, Qwen3.5-4B 32 (nested under
`text_config`), Qwen3-4B 36, Gemma-4-E4B 42 (nested). The convention matters
here rather than being bookkeeping: llama's `hs20` and Qwen3.5-4B's `hs20` are
the same integer and not the same depth (rd 0.714 versus rd 0.625), and on
present evidence they fall on opposite sides of the band in which any family in
this program has actuated.

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

The core readouts are the known-unknown (KU) direction and a caution/refusal
direction. In the gating experiments, the sensor is a standardized KU
projection: confabulation-prone rows project lower on it than known-correct
answered rows, so the gate fires when `-z_d` exceeds a threshold selected on a
FIT split. The actuator is a `c_hat` caution direction, constructed by
orthogonalizing a raw refuse/control direction against the KU direction and
confab-propensity controls. Later J-space experiments reuse per-layer versions
of these gates and write directions.

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

Internal-state instrumentation sharpened the picture. The known-unknown
direction did not move semantically with the prompt; compliance traveled
primarily through a caution/policy axis. A divergent-pool follow-up then separated rows where the
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

### 4.4 A gated hidden-state controller succeeds, and the gate's role depends on the dose regime

The first robust positive result came from changing the intervention form. Rather
than asking a single direction to be both sensor and actuator, the successful
controller separates them:

1. a **KU readout gate** decides which rows look like confabulations;
2. a fixed **caution snap** writes only those fired rows to a selected refusal
   setpoint.

At this write site (Qwen3-4B, L34) and dose (200), a registered comparison
later established why this separation matters: an unconditional write damages
60.1% of held-out known-correct rows versus 3.1% gated, a 57.0-point gap
(McNemar p = 4.2e-43, `ungated-vs-gated-dose-matched` Outcome), while the gate
costs the controller only 4.3 points of confab conversion (77.8% ungated
versus 73.5% gated). The 60.1% figure is not a refusal rate; it decomposes as
55.8 points clean false-refusal, 3.9 points answered-wrong, and 0.4 points
degenerate output. At this specific write site and dose, which the margin
theory identifies as an overdrive operating point, the gate is the sole
source of selectivity: the write, left unconditional, damages most
known-correct rows.

On the held-out signed run, the raw-base Qwen3-4B controller passed all gates.
The KU readout gate's FIT AUC was 0.9955. On held-out rows, gated clean
tightening was 136/185 = 73.5%, Wilson CI [66.7, 79.3], clearing the >=60%
floor and the lower CI >50% requirement. Known-correct false refusal was
8/258 = 3.1%, CI [1.6, 6.0], clearing the <=5% point floor and <10% upper CI
requirement. A random-direction write on the same fired rows produced only
13/185 clean tighten, and a permuted gate produced 59/258 known-correct cost.
The effect depends on both the caution direction and the KU readout gate.

**Interpretation.** The model need not internally choose to consult its readout
for the system to use that readout. The readout can gate an external controller.
This is the first clean selective actuation result in the arc, and, at this
overdrive operating point, the gate is doing essential selectivity work that
the write itself does not supply. Section 5 and Section 6.2 return to why this
attribution changes at a different dose regime.

**Robustness update.** Two later registered cells strengthen this headline
without changing it. A held-out transfer of the same controller design to
Qwen3.5-4B's mid-band write site (hs20 = rd 0.625, dose_abs 12.608) reproduced the
decoupling out of sample: fired-confab refused 872/1286 = 0.678 (Wilson
[0.652, 0.703]), well-formed 1256/1286 = 0.977, and known-correct false
refusal 14/360 = 0.039, with both placebo legs intact
(`qwen35-4b-midband-heldout` Outcome). Separately, the raw-base Qwen3-4B
headline itself survives a decode-robustness check: under temperature-0.7
sampled decoding with majority-vote aggregation across 5 pre-registered
seeds, pooled confab clean-tighten conversion is 643/925 = 69.5%, above the
63.5% floor in every individual seed, with known-correct cost at 60/1290 =
4.65% (`snap-seed-sampled-decode-replication` Outcome). Both results
supersede the corresponding held-out and decode-robustness items in the
2026-07-10 audit, which had flagged both as open.

### 4.5 J-space localizes a better write site

The successful gate-and-snap controller still raised a mechanistic question:
where should a write occur? The inherited caution write site was an L34
residual-stream direction. A Jacobian-lens characterization asked whether this
site lies inside or outside the model's workspace-like verbalizable band.

The instrument passed a correctness smoke: the final-layer J-lens closely
matched the direct unembed baseline over 1000 prompts, with mean cosine 0.9811,
mean top-10 overlap 0.82, and top-1 match 3/5 over five random directions. The
H1 read then found that caution-like directions verbalized as first-person,
absence, error, and impossibility tokens, while the known-unknown direction
verbalized more as answer/reply tokens. In hindsight this observation is
prescient corroboration of a later naming finding: a direction that
verbalizes toward answer/reply tokens is consistent with tracking
answerability rather than a self-directed uncertainty state, which is exactly
how `margin-evidence-responsiveness-worldknown` (Outcome) later characterizes
this direction on an out-of-population error class: closer to unanswerability
recognition than to self-directed uncertainty. The layer profile localized a workspace-like band
to hs=23-29, peaking at hs=26. The inherited L34 direction corresponds to hs=34,
just after that band.

The first causal layer sweep at a fixed absolute dose stopped at G0 because dose
200 collapsed hs23 and hs26. FIT-only dose calibration fixed that: usable
non-collapsing setpoints were recovered at hs23=25, hs26=75, hs29=125, and
hs34=175. The held-out contrast then supported the layer-site hypothesis. Over
443 held-out rows, hs23 (rd 0.639) achieved 165/185 clean refusals (89.2%)
versus hs34 (rd 0.944)
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

A separate answer-sycophancy readout, still an unsigned interim pilot rather
than a governed result, found a readable L24 direction on Qwen3-4B where the
actuator failed to beat a matched control: the write path fired and a neutral
guardrail passed, but the anti-sycophancy-vs-control gate failed with diff 0.
Reported here only as an unsigned pilot reading, not as evidence with the
same evidential status as the amendments elsewhere in this paper, it is
consistent with the broader lesson: readable behavioral directions do not
automatically become clean actuators.

### 4.8 Cross-family replication surfaces an instrument problem, not (yet) a mechanism problem

The gated caution controller in Section 4.4 was fit and evaluated on raw-base
Qwen3-4B alone. A cross-family test asked whether the same KU-gated caution
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
must therefore size the placebo against more than one random seed; the
multi-seed census that Section 4.10 later built supersedes the K >= 3
max-over-K denominator first proposed here, replacing it with registration
against each family's measured K = 15 null distribution, from which
percentile-based or sign-opposition criteria are available (Section 4.10;
`experiments/placebo-seed-distribution-census/AMENDMENT.md`).

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
at llama's own atlas site (hs20 = rd 0.714), one fresh seed per rung across the
registered dose grid, on both the confab and known-correct populations. At
the matched-magnitude reference dose (12 sigma_c), the llama confab lift was
+0.1 points: null. The ladder stayed flat through 16 sigma_c (-3.1 to +0.9
points, all inside the +/-8 point descriptive envelope), with a single
+8.5-point excursion at the top rung (20 sigma_c) that lands marginally
outside the envelope; known-correct false refusal grew with dose, from 0.3%
at 2 sigma_c to 6.0% at 20 sigma_c. A parallel mistral dose ladder (hs16 =
rd 0.500, one
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

**Depth caveat on the llama leg.** The llama ladder ran at that family's
read-selected atlas site, hs20 = rd 0.714. llama's own write site, the one
that cleared `dose_is_usable` and passed held-out G1 at 0.7420, is hs17 =
rd 0.607. The two are not interchangeable: read-optimal and actuate-optimal
depth are separately measured quantities in this program, and rd 0.714 sits
above the band in which any family here has actuated at all. A null placebo
is the desired control outcome and nothing about this result is anomalous,
but the inference the rider draws from it is stronger than the observation
supports. Reading a null placebo as evidence that placebo response is not
monotone in baseline hedging presumes the site is one where a direction of
that magnitude could have moved behavior. At rd 0.714 that presumption is
untested for llama and false for every other family measured. The sign map
should be read as complete in sign at the sites actually run, not as a
depth-controlled comparison; a llama placebo leg at hs17 would be needed to
make it one.

**Census update (2026-07-15).** A dedicated multi-seed census
(Section 4.10, `experiments/placebo-seed-distribution-census/AMENDMENT.md`)
later measured llama's matched-magnitude placebo across 15 fresh seeds and
found the single +0.1 reading above to be an unrepresentative draw: it lies
above the upper quartile of llama's census distribution (IQR [-9.33, -2.00],
median -7.67 points), and llama's placebo is in fact suppressive (12 of 15
seeds negative). Two consequences follow for this rider. First, llama is not null
at matched magnitude, so the sign map is not "complete at null" for llama; the
census llama leg supersedes the +0.1 point reading (Section 4.10). Second, the
monotone-in-baseline reading the rider recorded as falsified was falsified
against that single unrepresentative draw. On the census medians the
three-family sign map reads qwen -6.0 at baseline 0.104, llama -7.67 at 0.164,
and mistral +7.0 at 0.280: the two lower-baseline families suppress and the
highest-baseline family recruits, which partially revives monotone-in-baseline
as a hypothesis rather than settling it against. With n = 3 families this is a
hypothesis for a future registered test, not a claim. RR3's registered
scoreboard call and its adjudication stand exactly as recorded above; this
update revises only the downstream interpretation, on the census's larger
sample.

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
itself is inert: benefit and cost reproduced RR2 exactly. A third,
independent test at a different operating point reaches the same
direction-axis verdict by a different route: the mid-band gate-contribution
factorial's own direction-specificity leg (S1) fails on mistral at ratio
2.03 against a 3.0 floor (`gate-contribution-factorial` Outcome), same-signed
with the recruiting placebo null rather than sign-opposed to it as qwen's
passing S1 (ratio 7.27) is. Mistral's direction-specificity failure is now
established three times, independently, at three different sites and doses
(RR2's flat tolerance, RR3's effect-ratio gate, and the factorial's S1), which
is the basis for treating it in Section 5 as a bounded negative in the
actuation map rather than an artifact of any one instrument.

### 4.10 A multi-seed placebo census retires the seed-noise reading and revises the family sign map

The design rules Sections 4.8 and 4.9 arrived at both assume an object nobody
had yet measured: the per-family distribution of matched-magnitude
random-direction behavioral deltas across many fresh seeds. A dedicated census
(`experiments/placebo-seed-distribution-census/AMENDMENT.md`) built it. For each
family the census wrote the frozen random direction as an erase-write to that
family's certified placebo setpoint (qwen dose_abs 12.608, mistral 3.665, llama
13.514 re-derived byte-identical from RR's committed hs20 fit manifest), so
every seed in a family is a draw at one fixed magnitude. It drew K = 15 fresh
pre-registered random seeds per family, distinct from RR2's and RR3's, scored
each on a fixed S = 300 paired confab subsample (n_missing = 0 for every family
and seed) through one blinded context-free adjudication pool of 18 shards, and
adjudicated each family against a criterion fixed before the run: the family
sign SURVIVES iff the fraction of seeds carrying the committed sign f_s >= 0.80
with a bootstrap 95% lower bound above 0.50 and a median at least 3.0 points in
the committed direction; it is RETIRED to seed noise iff f_s <= 0.60 or the
interquartile range spans zero; otherwise INDETERMINATE. The result was
adversarially red-teamed, including an independent raw-artifact re-derivation of
all 15 mistral deltas, before the Outcome was written.

The census overturned the seed-noise reading both prior predictors held. Its
per-family verdicts:

- **qwen SURVIVES robustly.** f_neg = 14/15 = 0.933 (bootstrap 95% CI
  [0.80, 1.00]), median signed delta -6.0 points, IQR [-6.83, -3.67], span
  [-8.33, +0.67]. Suppression is a distributional property of the family, not a
  single-draw artifact.
- **mistral SURVIVES at the exact boundary.** f_pos = 12/15 = 0.800, the
  registered floor exactly (bootstrap 95% CI [0.60, 1.00], lower bound 0.60),
  median +7.0 points, IQR [+1.17, +13.67] (does not span zero), span
  [-8.00, +20.33]. Under the pre-stated criterion this is SURVIVES, which
  falsifies the "mistral recruitment is seed noise" call both predictors
  registered. The census records it at boundary strength: the margin over
  INDETERMINATE is a single seed, the three weakest positive seeds (+1.0, +1.33,
  +1.67) are within paired noise individually, and there is no rescoring lane,
  so the verdict stands as computed with that caution attached.
- **llama's null control did not hold.** llama carried no committed sign and was
  run as a negative control expected to center near zero. Instead
  f_neg = 12/15 = 0.800 with median -7.67 points, IQR [-9.33, -2.00], span
  [-12.00, +19.33]: a newly discovered negative placebo sign, reported straight
  per the pre-registered llama rule, not a falsification of anything.

Both families' historical single-seed values sit mid-distribution: qwen's -5.13
at the 53rd percentile and mistral's +7.39 at the 53rd percentile of their
census distributions, so neither point was anomalous, only under-sampled.

**Integrity disclosure.** The first report build joined over the blinded
adjudication output alone and dropped every detector-refused row from the paired
join, violating the registered final-rate rule (detector-v2-refused OR
adjudicated-abstention, per row). It was caught post-unblind, before any
verdict, from an n_missing anomaly and a mistral baseline rate at half this
paper's own cited 0.28, and corrected by merging the runlog detector flags with
the blinded adjudication values symmetrically across all arms and families; the
corrected join reproduces the known baseline hedge rates (mistral 0.263 against
the cited 0.28). Both report versions are committed (`census_report.json`
corrected, `census_report_defective_join.json` regenerated from the pre-fix
pinned code). The red team adjudicated the correction legitimate: the OR rule
admits no alternative reading, the merge is symmetric, and no discretionary
choice in it can flip a verdict. The correction moved two verdicts (qwen from
INDETERMINATE to SURVIVES, mistral from RETIRED to SURVIVES), both against the
registered predictions, which is the opposite of what a motivated fix would
produce (`experiments/placebo-seed-distribution-census/AMENDMENT.md`, Outcome
SC3 disclosure).

**Consequences for the actuation program.** The census sharpens three of this
paper's claims.

- *Mistral direction-specificity, falsified in Section 4.9, is reinforced on a
  better-measured denominator.* The census maximum random lift over 15 fresh
  seeds is +20.3 points, close to RR3's max-over-3 of 21.8 points, so sampling
  the placebo 15 deep did not surface a larger excursion than the 3-seed draw
  already found. The gated arm's +40.9 point confab lift still falls short of a
  3x ratio over that denominator, so the direction-specificity verdict does not
  change and now rests on a null sampled 15 deep rather than 3
  (`experiments/placebo-seed-distribution-census/AMENDMENT.md`, Outcome;
  Section 4.9).
- *Qwen specificity is strengthened, not weakened.* Because qwen's placebo null
  is itself suppressive, the true caution write's recruitment of refusals is
  sign-opposed to the family's nonspecific-perturbation response: a random
  perturbation at matched magnitude pushes qwen hedging down, while the gated
  caution write pushes it up. A confound a placebo is meant to catch would push
  the same way as the true write, and here it pushes the opposite way, so the
  qwen gate-and-snap result (Section 4.4) sits on firmer specificity footing
  than a near-zero placebo would have left it.
- *Two routes to abstention, and why rate deltas alone cannot certify
  KU-readout coupling.* Abstention is causally reachable at matched magnitude
  through at least two routes: through the represented known-unknown state
  (the gated true-direction write) and through nonspecific computational
  disruption (a random direction of the same magnitude). The red team sampled
  the random arm's dose-induced refusals and confirmed them to be coherent,
  well-formed abstentions on rows that carried committed answers at baseline,
  not dose-degraded text. Because a random write can manufacture genuine
  coherent refusals, a raw increase in abstention rate cannot by itself
  certify that an intervention is coupled to the model's own known-unknown
  readout rather than a generic perturbation. Certifying KU-readout coupling
  requires the selectivity evidence this paper already leans on (moving
  target failures without imposing refusal on known-correct rows) together
  with a specificity margin referenced to the family's own measured placebo
  null, not to zero.

A within-kuq subtype breakdown of the same placebo response
(`placebo-signflip-question-type-analysis` Outcome) shows the family-level
sign is not evenly distributed across question types: one subtype,
future-unknown items, carries qwen's entire suppression (-24.7 points against
-2.8 or smaller elsewhere) and is also mistral's single largest recruitment
delta (+11.8 points), the extreme mover in both families but in opposite
directions. Question type does not explain away the cross-family sign
difference at the family level, but it shows the sign is not homogeneous
within a family either.

**Design-rule update.** The census also matures the placebo design rule
Sections 4.8 and 4.9 were still refining. Those sections prescribed a multi-seed
(K >= 3) random-direction ensemble with a max-over-K denominator in place of a
single seed. The standing rule is now stronger: register the placebo criterion
against each family's measured per-family null distribution. The census supplies
that distribution at K = 15 for all three families, so a future
direction-specificity test can register a percentile-based tolerance or a
sign-opposition criterion (does the true write move behavior opposite to the
family's own nonspecific-perturbation response) against a measured null rather
than a point estimate or a small-K maximum
(`experiments/placebo-seed-distribution-census/AMENDMENT.md`).

---

## 5. Synthesis: The Actuation Map

The results form a channel map rather than a single pass/fail story.

| Channel | What worked | What failed | Lesson |
|---|---|---|---|
| Within-generation text | Small gate-side trickle under strong first-person rule | No useful dial/revision effect; no registered success | Text inside the trace is attenuated, not a faithful readout channel |
| System prompt | Large behavior movement when labels are correct | Divergent-pool congruence with own readout is zero | Authority moves policy; it does not establish self-consultation |
| Reward | Some boundary-preserving behavior | TRUE sensor less congruent than PERMUTED | Reward can train correlates without readout consultation |
| Unconditional write, overdrive regime (Qwen3-4B, L34, dose 200) | Damages most confabs (77.8%) | Non-selective on knowns: damages 60.1% of known-correct rows vs 3.1% gated (57.0pp, McNemar p = 4.2e-43) | At this dose, the gate is the sole source of selectivity; the write alone is not selective |
| KU-gated caution snap, overdrive regime (Qwen3-4B, L34, dose 200) | 73.5% clean tighten, 3.1% known cost; held-out and sampled-decode replicated | Release direction remains null | Gate supplies selectivity; snap supplies the refusal action |
| KU-gated caution snap, mid-band regime (Qwen3.5-4B hs20 = rd 0.625, mistral hs16 = rd 0.500; dose_abs 12.608 qwen, 3.665 mistral) | Permuted-gate confab abstention already 0.550 qwen / 0.600 mistral, near the true gate's 0.689 / 0.694: the write is largely self-sorting | True gate's own contribution, Gap_Sel(c_hat), is real but sub-floor (0.148 qwen, 0.129 mistral, vs a 0.20 floor); cost protection sub-floor too (0.008 / 0.034 vs 0.10) | At this dose, the write self-sorts; the gate's role reduces to a modest increment plus cost governance, not the source of selectivity |
| Mid-band J-space write (layer site, not dose regime; Qwen3-4B, 36 blocks) | hs23 = rd 0.639 beats hs34 = rd 0.944 by +22.7pp | Needs layer-specific dose; not yet cross-family | Write site matters |
| Natural J-token write | Non-inert token-only effect | Redundant with `c_hat` hybrid | Verbalizable token target is not enough |
| Cross-family gated snap (mistral, bounded negative) | Wide-instrument adjudicated refusal 69.9%, cost pristine (0.52% known-correct); benefit and cost gates reproduce at every re-test | Direction-specificity falsified three times independently, at three sites and doses: RR2's flat 2-point placebo tolerance, RR3's corrected 3x effect-ratio gate (ratio 1.87), and the mid-band factorial's S1 leg (ratio 2.03, K=15 census denominator); the mid-band factorial's own gate-contribution leg is also sub-floor (Gap_Sel 0.129 vs 0.20); the cross-family confirmatory fleet found a true behavioral null at the registered late write site (0/874 clean_tighten at every dose); a 15-seed placebo census (Section 4.10) resolved all three families' matched-magnitude placebo as sign-consistent rather than seed noise (qwen suppresses 14/15, mistral recruits at the 12/15 boundary, llama newly suppresses 12/15), so llama is not a null control | Mistral is readable everywhere the audit looked but not shown actuable by a direction-specific write at any tested site; placebo criteria must be registered against each family's measured per-family null distribution, not a flat tolerance or a single seed; the census (Section 4.10) supplies that distribution at K=15 for percentile-based or sign-opposition criteria |

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

### 6.2 Why the gate matters, and why its role changes with dose

Whether the caution write needs the gate to be selective is not a fixed
property of the direction; it depends on where the dose lands relative to
each row's commitment margin, the minimum perturbation dose that flips that
row's behavior to abstention. At an overdrive dose, above typical
known-correct margins, the write crosses everything: applied indiscriminately
at Qwen3-4B / L34 / dose 200, it damages 60.1% of known-correct rows, and the
gate is the sole reason the controller does not. At a mid-band dose, above
typical confab margins but below typical known margins, the write is already
content-selective: the gate-contribution factorial's permuted-gate control
reaches confab abstention 0.550 qwen / 0.600 mistral against the true gate's
0.689 / 0.694, so most of the abstention lift survives with no gate at all.
The gate's residual mid-band role is real but modest: a selectivity increment,
Gap_Sel(c_hat) 0.148 qwen / 0.129 mistral, both sub-floor against a 0.20
registered floor, plus cost governance that does matter against the 0.05
registered ceiling: known false refusal under the true gate is 0.042 qwen /
0.005 mistral versus 0.050 / 0.039 under a permuted gate. This is still the
same separation used in ordinary control systems, sensor, controller,
actuator, but which part of the system supplies selectivity is
dose-dependent: at overdrive the controller (gate) does the selecting, and at
mid-band the actuator (write) already discriminates while the controller
mainly tightens cost.

### 6.3 Why J-space matters, and where the account is scoped

The J-space diagnostic gives a mechanistic explanation for one repeated pattern:
directions are portable as readouts but fragile as writes. If the reportable or
workspace-relevant component of a concept lives in a mid-to-late band, late
residual writes may be downstream of the useful broadcast site. The calibrated
layer contrast supports that account on raw-base Qwen3-4B, but a cross-family
atlas test of the account's own predicted shape (`jspace-family-atlas`
Outcome) did not hold: the effective-dimensionality profile that motivated
"write near the interior peak" instead peaks early in both llama (layer 4 of
28, 0.14 depth) and mistral (layer 3 of 32, 0.09 depth), not inside the
predicted interior band. The atlas's read panel still delivers a usable,
family-specific interior band where known-unknown, caution, and raw-refusal
readouts all clear 0.80 held-out AUROC simultaneously (llama layers 15-23,
mistral layers 7-27), so a readable workspace-like band exists in every
family tested, but the specific "write near the eff-dim peak" account is
currently scoped to raw-base Qwen3-4B and should not be read as a
cross-family mechanism claim.

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
  than a family constant. The census in Section 4.10 measured these
  distributions directly at K = 15 per family and found the matched-magnitude
  placebo sign-consistent rather than seed noise in all three families, so the
  single-seed caution stands but the underlying nulls are now measured, not
  assumed;
- the controller has a coherence/saturation ceiling on an out-of-population
  error class. On world-known items, where the error is a confidently wrong
  answer rather than acknowledged ignorance, steering the fitted direction
  tips only 51/400 (12.75%) of confabs into refusal inside a coherence-valid
  dose band, and doses at or above 3x the reference drive degenerate
  generation before any refusal registers
  (`margin-evidence-responsiveness-worldknown` Outcome). This ceiling is
  scoped to the hs20 mid-band lineage tested there; whether the L34
  overdrive headline in Section 4.4 shows the same ceiling on this
  population is untested.

The margin-theory account that motivates this paper's operating-point framing
(`docs/research/margin-theory-framework.md`) is developed further in a
successor paper on the geometry of these margins; this paper carries no
margin-cell numbers of its own and defers that account to the successor.

### 6.5 Next study: the amped-up replication and model sweep

One asymmetry should shape how that next study is designed. The known-unknown
(answerability) axis this paper's gated write is built on reads at near-ceiling
accuracy on Qwen3-4B and, in the companion readout paper, transfers across four
model families at AUROC 0.997 to 0.998 with no per-family refitting. The
correctness axis a sibling paper reads at the answer token does not carry the
same portability, even within one model's own training trajectory. A direct
measurement of its cross-checkpoint rotation found none of the answerability
axis's single-rotation-then-stable pattern: cosines of 0.19, 0.45, and 0.33
across the three training transitions, none reaching the 0.85 stability the
answerability axis shows at the later two. Worse, the fitted correctness
direction is itself only weakly pinned down by the data: refitting it on two
disjoint halves of one checkpoint's own data agrees at only 0.17 cosine, next
to a readout accuracy that stays flat near AUROC 0.80. A follow-up asking
whether a shared subspace, rather than a single axis, explains the correctness
readout's partial transfer between checkpoints found at most one weak shared
direction, with the transferable signal diffuse across the base model's
activation span rather than concentrated in any small discriminative
subspace. Both results are
exploratory Tier-2 findings from a single model, and neither is a cross-family
claim. But together they are a reason to expect the two readouts to generalize
differently across families: this paper's gated write rides the crisp,
portable answerability axis, and any future actuation program built on the
correctness axis instead should be treated, going in, as a separate and likely
harder generalization problem, not assumed to inherit the answerability axis's
portability. That is a hypothesis for the next study to test, not a result it
can yet report.

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
   at establishing mistral direction-specificity needs a different
   write site or dose where the random-direction response is less variable
   (a larger K does not help: the Section 4.10 census max over 15 seeds is
   +20.3 points, close to RR3's max-over-3 of 21.8). Llama's placebo
   response, measured first by RR3's rider as null and then by the Section 4.10
   census across 15 seeds as a newly discovered suppressive sign (12/15
   negative, median -7.67), is not a null control after all. Any future
   attempt, on llama or elsewhere, must register its placebo criterion against
   that family's measured per-family null distribution (Section 4.10; the
   census supplies it at K = 15), for example via a percentile-based tolerance
   or a sign-opposition criterion, not a single seed and not a flat
   small-tolerance band.
4. **The multi-family confirmatory fleet is resolved, not pending.** A
   registered cross-family confirmatory (`doubt-snap-cross-family-confirmatory`
   Outcome) already attempted a gated caution snap on qwen, llama, mistral,
   and a larger qwen tier at each family's registered late write site. It was
   NOT PROMOTED: every launched cell stopped at the pre-outcome FIT
   dose-viability rule before reaching held-out scoring (peak FIT
   clean_tighten 32.6% qwen small-tier, 18.4% llama, 0.0% mistral, 5.75% qwen
   mid-tier, all below the 60% floor). A companion c_hat validity audit found
   the caution encoding linearly readable in all four families (0.84-0.99
   AUROC refused-vs-confab), so the stop reflects a write-site problem at the
   registered universal-depth site, not an absence of the underlying signal:
   the caution direction reads everywhere tested but is actuable, at that
   site, only in the Qwen lineage. This reframes the open question: not
   "does the gated snap work cross-family" but "at which family-relative
   site does it work," which the family atlas (Section 6.3) already answers
   for llama and mistral. Per-family atlas-sited retests are queued work, not
   a blocker for this paper's claims.
5. **Dense-token screen.** Separately screen abstract or multilingual token
   bundles before any causal hybrid run. Do not alter the natural-token result
   post hoc.
6. **Generic tuner support.** Promote compound multi-readout writes into the
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
correlates without congruence; and whether an unconditional write is
selective depends on the dose regime, not on the write alone. The first clean
positive controller in this arc is not a prompt or a reward but a gated
hidden-state intervention: read the known-unknown state, fire selectively at
an overdrive dose where the gate alone supplies selectivity, or write caution
at a mid-band dose where the write already self-sorts and the gate mainly
tightens cost, sited near a workspace-like layer band.

The emerging lesson is pragmatic and regime-aware. Treat known-unknown
readouts as sensors first. Use them to gate interventions, expecting the
gate's contribution to shrink as the dose moves from overdrive toward
mid-band. Calibrate the actuator separately. Then replicate the layer,
channel, and dose regime before claiming the model has learned to consult
itself.

---

## Appendix A. Traceability Map

This appendix intentionally names internal amendment/experiment labels so the
draft can be audited. Reader-facing prose should eventually move most labels to a
provenance appendix or supplement.

| Paper claim | Governed source | Status |
|---|---|---|
| Direct activation/text "turn the probe around" cells did not move behavior at registered gates | `experiments/causal-confidence-steering/AMENDMENT.md` §7 | Falsified / channel shut |
| First-person natural-language confidence framing did not open the text channel at useful magnitude | `experiments/first-person-injection/AMENDMENT.md` §7-8 | Ambiguous-leaning negative |
| KU-readout-coupled activation write carried information in a trained-checkpoint intervention | `experiments/doubt-regulated-caution/AMENDMENT.md` §8 | Positive |
| High-authority system prompt moved behavior by +18.0pp over permuted | `experiments/second-person-doubt-prime/AMENDMENT.md` §8 | Pass |
| Inverted system prompt showed asymmetric compliance, not belief revision | `experiments/oracle-dissociation-prime/AMENDMENT.md` §9 | Pass |
| Divergent-pool test found zero own-readout congruence; Addendum A1 certified the instrument | `experiments/divergent-pool-own-readout/AMENDMENT.md` §9-10 | H-compliance |
| Probe-as-reward TRUE arm failed to train readout consultation | `experiments/probe-as-reward/AMENDMENT.md` §5 | Null |
| Raw-base KU-gated caution snap produced 73.5% clean tighten at 3.1% known cost (overdrive regime, L34/dose 200) | `experiments/doubt-gated-caution-tighten/AMENDMENT.md` Outcome | Exploratory pass |
| At this overdrive operating point, an unconditional write damages 60.1% of held-out known-correct rows vs 3.1% gated (57.0pp, McNemar p = 4.2e-43): the gate is the sole source of selectivity here | `experiments/ungated-vs-gated-dose-matched/AMENDMENT.md` Outcome | Registered pass; scoped to L34/dose-200 |
| Mid-band write site (Qwen3.5-4B hs20, dose_abs 12.608) decouples refusal from corruption in-sample FIT (refused 0.684, well-formed 0.980, known cost 0.042); permuted-gate control shows the write is already content-selective there | `experiments/qwen35-4b-midband-doubt-snap/AMENDMENT.md` Outcome | Exploratory pass, in-sample |
| Same mid-band operating point transfers to held-out (refused 0.678, well-formed 0.977, known cost 0.039), promoting it from an in-sample selection to a held-out claim | `experiments/qwen35-4b-midband-heldout/AMENDMENT.md` Outcome | Held-out pass |
| The overdrive headline (73.5%/3.1%) survives temperature-0.7 sampled decoding with majority-vote aggregation (69.5% pooled conversion, all 5 seeds above floor, cost 4.65%) | `experiments/snap-seed-sampled-decode-replication/AMENDMENT.md` Outcome | Decode-robustness pass |
| Mid-band gate-contribution factorial falsifies "the gate supplies selectivity" as a universal claim in both families: permuted-gate confab abstention 0.550 qwen / 0.600 mistral vs true gate 0.689/0.694; Gap_Sel(c_hat) 0.148/0.129 sub-floor vs a 0.20 floor; S1 direction-specificity passes qwen (7.27) and fails mistral (2.03) | `experiments/gate-contribution-factorial/AMENDMENT.md` Outcome | Registered falsification of the universal-gate claim |
| J-lens localized workspace-like band to hs=23-29, peak hs=26; L34 maps after band | `experiments/j-space-localization-qwen3-4b/AMENDMENT.md` Outcome | Exploratory diagnostic |
| Layer-specific calibration recovered non-collapsing setpoints | `experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md` Outcome | FIT-only pass |
| Held-out mid-band layer contrast: hs23 89.2% vs hs34 66.5% | `experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md` Outcome | Exploratory pass |
| Natural token-target J-space write was non-inert but redundant with `c_hat` | `experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md` Outcome | Exploratory falsification |
| Cross-family atlas: eff_dim_frac peaks early (0.09-0.14 depth) in both llama and mistral, not interior as predicted; read panel still delivers a usable per-family interior band (llama L15-23, mistral L7-27) | `experiments/jspace-family-atlas/AMENDMENT.md` Outcome | Prediction failed; read panel delivered |
| Cross-family confirmatory fleet (qwen/llama/mistral, universal-depth write site) NOT PROMOTED: every cell stopped at FIT dose-viability before held-out; companion c_hat audit shows the encoding readable in all four families while late-site writes actuate only in the Qwen lineage | `experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md` Outcome | Not promoted; write-site problem, not a family-mechanism null |
| Dark-candidate screen validates positive caution lever but promotes no dark candidates | `experiments/dark-actuator-screen/AMENDMENT.md` Outcome | Supporting null |
| AQ sycophancy actuator found readable direction but no clean actuator vs control | `experiments/aq-sycophancy-activation-actuator/AMENDMENT.md` Outcome | Unsigned interim pilot (draft, not a governed result) |
| Mistral cross-family gated write cleared benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) gates under a wide blinded instrument but failed the flat 2-point placebo tolerance (+7.39pp random-direction lift) | `experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md` Outcome | Exploratory falsification (placebo-criterion design flaw, not benefit/cost) |
| Wide-instrument baseline hedging and placebo response are family-graded and family-signed (qwen -5.13pp suppression, mistral +7.39pp recruitment); flat placebo tolerances must be registered per-family | `experiments/abstention-wide-instrument-calibration/AMENDMENT.md` Outcome | Exploratory instrument calibration, resolved |
| Corrected effect-ratio placebo criterion (>= 3x max-over-K fresh-seed random lift) still falsified mistral direction-specificity (ratio 1.87) while reproducing RR2's benefit (69.9% adjudicated refusal) and cost (0.52% known-correct) exactly; red-team certified robust to detector-only and mean-of-K denominators; mistral's random-direction lift spans -7.4 to +21.8pp across three fresh seeds; llama rider placebo response is null at matched magnitude, completing the three-family sign map | `experiments/rr3-corrected-placebo-replication/AMENDMENT.md` Outcome | Exploratory falsification (corrected-criterion re-adjudication of the RR2 claim, benefit/cost intact) |
| Multi-seed placebo census (K=15 fresh seeds per family at matched magnitude, S=300 paired rows, blinded adjudication in 18 shards) resolved all three families' random-direction placebo as sign-consistent rather than seed noise: qwen suppression SURVIVES (14/15 negative, median -6.0), mistral recruitment SURVIVES at the 12/15 boundary (median +7.0, falsifying both predictors' registered seed-noise call), null-control llama shows a newly discovered negative sign (12/15, median -7.67); historical single-seed values sit at the 53rd percentile; a post-unblind final-rate-rule join correction moved two verdicts against the predictions, both report versions committed, red-team certified legitimate | `experiments/placebo-seed-distribution-census/AMENDMENT.md` Outcome | Exploratory placebo-distribution census, resolved (revises the RR3 llama-null leg) |
| Within-kuq subtype breakdown: question type does not explain the cross-family placebo sign difference at the family level, but one subtype (future-unknown) carries qwen's entire suppression (-24.7pp) and is also mistral's largest recruitment delta (+11.8pp) | `experiments/placebo-signflip-question-type-analysis/AMENDMENT.md` Outcome | Resolved; subtype-inert reading falsified for qwen |
| Criterion (d) (evidence-responsiveness) is not licensed on the world-known error class for the named KU direction (primary transfer void, population reversal) or for a world-known-specific refit (specificity leg passes, collapse leg fails); a coherence/saturation ceiling limits refusal to 12.75% of world-known confabs before generation degenerates | `experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md` Outcome | Null result; retires mentalistic naming with a completed (d) adjudication |
| A constructive search for a specific evidence-response axis (d_ev) fires at baseline but is indistinguishable from covariance-shaped random directions and weaker than the native ignorance-fit direction; it reconstructs retrieval-family geometry, not a specific evidence-responsive axis | `experiments/evidence-response-direction-search/AMENDMENT.md` Outcome | Null result; strengthens the fragmentation reading |

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
  per-family measured null distribution the census supplies at K = 15
  (Section 4.10), for example via a percentile-based tolerance or a
  sign-opposition criterion, not a flat symmetric tolerance, a single seed, or
  the small-K max-over-K denominator RR3 first proposed (Section 4.9). The
  per-family wide-instrument baselines from Section 4.8 (qwen 0.104, llama
  0.164, mistral 0.280) still anchor the recruitment-versus-suppression axis.
- Run llama's gated caution snap (not yet attempted; its placebo response has
  been measured, first at null by RR3's rider and then by the Section 4.10
  census as a newly discovered suppressive sign, so llama is not a null
  control) before claiming or ruling out cross-family direction-specificity
  for that family.
