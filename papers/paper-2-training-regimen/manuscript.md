---
title: "Teaching Small Language Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v2 (restructured 2026-07-01; the evidence-synthesis Part I split out to papers/paper-1-taxonomy-framework/manuscript.md, the confidence-channel and probe depth moved out to papers/paper-3-knows-but-doesnt-say/manuscript.md)
date: 2026-07-01
supersedes: archive/papers/paper-2-training-regimen/drafts/paper2-training-regimen-draft-v1.md (experiment portion)
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
reproducibility: >
  Behavioral tables and Figures 1-5 regenerate via
  papers/paper-2-training-regimen/scripts/build_figures.py into
  papers/paper-2-training-regimen/analysis/ and papers/paper-2-training-regimen/figures/; Figure 6
  (regimen operating points) regenerates via
  papers/paper-2-training-regimen/scripts/build_extended_figures.py. The grouped run inventory is
  archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv.
  Full amendment-to-artifact provenance is in Appendix A.
notes: >
  Numbers discipline: every quantitative claim traces to a metrics.json,
  results table, or calibration-gap JSON named in Appendix A; background
  claims from the evidence synthesis trace through
  papers/paper-1-taxonomy-framework/manuscript.md to
  meta-analysis/evidence/effects.csv. Reader-facing prose carries no internal
  amendment labels; the label-to-artifact map lives only in Appendix A. Math
  is set in LaTeX (inline $...$ / display $$...$$, pandoc-compatible).
  Citations are author-year; the References section is complete and
  one-to-one with in-text citations.
---

# Teaching Small Language Models to Say I Don't Know: A Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention Data

Joseph Rosenbaum
Synaptic Labs

*Draft v2. Not for distribution.*

> *"It is likely that neither of us knows anything worthwhile, but he thinks he knows something when he does not, whereas I, as I do not know, do not think I know either."*
>
> Plato, *Apology* 21d

## Abstract

Language models acquire most of their epistemic character (how confident they
sound, when they refuse, how readily they capitulate) not from pretraining but
from post-training, yet the field has never compared its major post-training
objectives on the same abstention data and base model. We run that comparison:
SFT, DPO, KTO, and GRPO on a shared model-specific known/unknown dataset and a
shared small open-weights base (Qwen3-4B), evaluated on one surface with exact
paired row tests. The comparison yields a stage decomposition rather than a
winner. Trained from the base model, only SFT *induces* abstention (refusal
recall 87.9%, over-refusal 64.8%, three seeds); cold-start DPO and KTO refuse
essentially nothing, falsifying the natural hypothesis that KTO's unpaired
binary format makes it a native abstention trainer. Applied after an SFT
warm-up, preference optimization *repositions* the boundary along a
recall/over-refusal trade-off (DPO aggressively toward answering, KTO
conservatively; three seeds for DPO, two for KTO), and GRPO under an appropriateness reward
*amplifies* the routine to near-ceiling recall and the study's best
truthfulness while re-inflating over-refusal (single seed, exploratory). No
objective or ordering moves the underlying discrimination frontier; each
selects an operating point on the frontier the SFT stage defines. Stated
confidence, measured after the same runs, carries a warning: every regimen's
emitted confidence tracks the *decision to answer*, not the truth of the
answer, so behavioral gains masquerade as confidence shifts. Why the stated
channel fails, and how much more the model's hidden states know than any
channel says, is taken up in the companion diagnosis paper. The practical
conclusion here: report abstention training as an operating point with both
error rates, choose the second stage by deployment cost asymmetry, and do not
read the confidence number as knowledge.

## 1. Introduction

A language model that answers fluently when it knows and abstains gracefully
when it does not would be, in a precise sense, aligned: its expressed epistemic
state would track its actual one. The models we deploy are not like this. They
assert falsehoods with high verbal confidence, refuse questions they could
answer, and abandon correct answers under trivial social pressure. A recent
theoretical account names the failure mode we adopt as framing: the **polite
liar** (DeVilling, 2025), a system that structurally misrepresents its own
epistemic state, not out of anything resembling malice, but because its
training rewarded the appearance of knowledge over the admission of
ignorance (cf. Kalai et al., 2025, who derive the same incentive from
binary-graded evaluation).
The contention of this research program is that these failures are primarily
facts about *training*, specifically post-training. The program's companion
taxonomy and evidence-synthesis paper, [*The Depths of Ignorance: A Taxonomy,
Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in
Language Models*](../paper-1-taxonomy-framework/manuscript.md), argues the same
contention from the published evidence: a systematic extraction of 78
quantitative effects from 39 studies across the calibration, abstention,
hallucination, and sycophancy literatures. This paper
runs the experiment that synthesis shows to be missing.

Three strands of the published evidence converge on training as the causal
locus.

First, pretrained models already know how likely they are to be right;
post-training breaks the readout. The GPT-4 technical report measures an
expected calibration error (ECE) of 0.007 for the pretrained base model on a
subset of MMLU; after reinforcement learning from human feedback (RLHF), ECE on
the same subset rises tenfold to 0.074 (OpenAI, 2023). Kadavath et al. (2022)
identify the mechanism (RLHF concentrates probability mass on high-reward
outputs, sharpening every distribution whether or not the model's knowledge
warrants it) and show that a single temperature adjustment largely restores
calibration. That repairability is itself evidence: the
signal survives in the weights; it is merely expressed too confidently.

Second, the damage is not specific to reinforcement learning. A controlled
comparison on the same base model finds plain instruction tuning nearly
tripling ECE (0.13 to 0.36) while simultaneously *reducing* predictive entropy
(1.32 to 0.92) (Lithgow-Serrano et al., 2025): the tuned model becomes more decisive and
less reliable about its own reliability at the same time.

Third, the converse also holds: what training breaks, training can
deliberately improve. Refusal-aware tuning (Zhang et al., 2023),
factuality-aware DPO (Tian et al., 2023), calibrated reward models, and
listener-aware preference pairs consistently improve humility metrics, often
by large margins ([*The Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md), family C5).

What has been missing is the experiment the synthesis most directly calls
for: the same base model, the same model-specific abstention data, every
major post-training objective, and the same measurement panel after the same
runs. This paper supplies it: a four-objective regimen study on Qwen3-4B
whose design is read off the synthesis's verified gaps directly.

Contributions:

1. The first SFT / DPO / KTO / GRPO comparison on shared abstention data and a
   shared small open-weights base, with seed-level intervals and exact
   row-level paired transitions (Section 4). This closes the synthesis's
   Gaps 1 to 3 at the behavioral level.
2. A stage decomposition of the regimen: SFT induces, preference optimization
   repositions, GRPO amplifies. No objective or sequence we tested escapes
   the recall/over-refusal trade-off; they select operating points on it
   (Section 4).
3. A stated-confidence measurement after the same runs showing that emitted
   confidence tracks the decision to answer, not the truth of the answer, so
   repositioning toward answering masquerades as confidence (Sections 4.2
   and 5). This is the observation that the program's companion diagnosis
   paper, [*Knows but Doesn't Say: A Training-Resistant Gap Between
   Internal and Stated Confidence in a Small Language
   Model*](../paper-3-knows-but-doesnt-say/manuscript.md), pursues to the
   representation level.

## 2. Background: what the evidence says, and what was missing

The program's synthesis paper, [*The Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md), extracts 78 quantitative
effects from 39 studies (2021–2026) into five claim families; three of them,
plus two of its reanalysis lessons, fix this experiment's design.
*Post-training* here covers supervised/instruction fine-tuning (SFT);
preference optimization, including direct preference optimization (DPO)
(Rafailov et al., 2023) and Kahneman-Tversky optimization (KTO)
(Ethayarajh et al., 2024); and RL with programmable rewards, group relative
policy optimization (GRPO) (Shao et al., 2024) in particular.

### The families

Instruction tuning and RLHF degrade token-probability
calibration, and the mechanism is the relationship between the tuning data
and *this model's* knowledge: fine-tuning on facts the model does not know
causally drives hallucination (Gekhman et al., 2024), while data aligned with
prior knowledge induces overconfidence (Wang et al., 2025), which is why
every successful abstention method builds *model-specific* training splits
(family C1). Preference-based methods beat SFT on abstention and truthfulness
quality, anchored by the model-specific IDK tournament of Cheng et al. (2024)
and confirmed in the [*Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md) reanalysis of
AbstentionBench (Kirichenko et al., 2025), but the median improvement is an
order of magnitude smaller than the calibration damage (C2). And the same
synthesis paper's output-level reanalysis of Cheng et al.'s released
artifacts shows the improvement is a *trade*: DPO cuts
SFT-induced over-refusal nearly in half while giving up a third of refusal
recall, movement along a refusal ROC curve rather than better
discrimination (C3).

### The reanalysis lessons

Single-scalar abstention metrics hide which
failure a model makes (recall and precision are decoupled across 20 models,
Spearman $\rho = -0.05$), so every result below reports both error rates.
And model-specific known/unknown labels are themselves noisy (42.9 to 51.3%
of answers on unknown-labeled questions in the released artifacts were in
fact correct), which flattens all recall/over-refusal numbers toward the
middle.

### The gaps this experiment closes

The gap analysis in [*The Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md) verifies six
experiments absent from the literature as of June 2026; this study is built
on the first three. *Gap 1:* KTO has never been applied to abstention,
honesty, or calibration training, despite consuming exactly the unpaired
binary labels a known/unknown split produces and weighting losses
asymmetrically, as this domain's costs are. *Gap 2:* no SFT vs. DPO vs. KTO
three-way comparison exists on the same abstention dataset. *Gap 3:*
GRPO-for-abstention exists in the verifiable-RL cluster (Wei et al., 2025;
Zhai et al., 2026; Mohamadi et al., 2025; Damani et al., 2025), but no
controlled comparison against SFT/DPO/KTO does. One caution from that
literature binds our design: probes placed *inside* RL reward loops get gamed
(Cundy & Gleave, 2025), so representation probes remain held-out evaluation,
never reward. Gap 6's small-model complaint is addressed by construction:
everything here runs at 4B parameters.

## 3. Design and methods

### 3.1 Design logic

The experiment is the synthesis's missing study, assembled. One base model
(Qwen3-4B), one model-specific known/unknown data construction, and four
training objectives, evaluated on a shared surface with a panel that covers
both halves of every trade-off the reanalyses exposed: refusal recall *and*
over-refusal, truthfulness *and* correct-on-known, plus stated confidence.

The study has three evidence layers, reported in order of evidential
strength:

1. **Cold-start comparison** (three seeds): SFT, DPO, and KTO trained from the
   base model. Answers whether each objective can *induce* abstention.
2. **SFT-warmed comparison** (three seeds for DPO, two for KTO): preference
   optimization applied after SFT. Answers whether the preference objectives
   can *reposition* an existing boundary, the sequential reading C2/C3
   suggest.
3. **GRPO** (single seed, exploratory): GRPO applied after SFT under a
   behavior-dominant appropriateness reward. Answers what RL with a
   programmable reward adds.

Layers 1 and 2 carry seed-level intervals and exact paired row tests; layer 3
is single-seed and labeled exploratory throughout. We report the distinction
rather than pooling across it.

### 3.2 Data construction

The IDK data construction follows the model-specific known/unknown lineage of
Cheng et al. (2024), regenerated for the model under study rather
than borrowed (the labels are model-specific by construction, and the
synthesis measured 42.9 to 51.3% label noise in borrowed labels; Section 2). The base model is
probed on factoid QA (TriviaQA lineage (Joshi et al., 2017)); questions it
answers correctly under the probe protocol become "known," questions it
consistently fails become "unknown," ambiguous cases are excluded. SFT
receives direct targets (answer the known, refuse the unknown); DPO receives
chosen/rejected pairs; KTO receives the same rows as unpaired
desirable/undesirable examples; GRPO receives no supervised targets at all,
only a reward over sampled completions.

### 3.3 Training arms

All arms use resource-feasible LoRA/QLoRA recipes on Qwen3-4B; recipes,
seeds, and per-run records are committed in the repository (Appendix A). The
comparison should be read as a replication-style stress test of the
known/unknown supervision idea at small scale, not a bit-for-bit reproduction
of any prior stack.

#### SFT, DPO, KTO

SFT, DPO, and KTO are standard implementations of their objectives. Each is
trained both cold (from base) and SFT-warmed (from the merged SFT
checkpoint).

#### GRPO

GRPO samples groups of completions per prompt and optimizes
group-relative advantages (Shao et al., 2024) under a programmable reward:
each prompt draws a group of $G$ sampled completions, each completion earns
a scalar reward $r_i$, and the policy gradient weights completion $i$ by its
group-normalized advantage

$$\hat{A}_i = \frac{r_i - \operatorname{mean}(r_1, \ldots, r_G)}{\operatorname{std}(r_1, \ldots, r_G)},$$

so a completion is reinforced exactly insofar as it outscores its own
siblings. The
primary reward is *appropriateness-dominant*: answering a known question and
abstaining on an unknown question earn positive reward; answering an unknown
question (hallucination risk) and refusing a known question (over-refusal) are
penalized, with hallucination penalized asymmetrically harder. Two reward
revisions tuned the penalty weights and the confidence-shaping term (the
first revision's operating point turned out to over-reward refusal; the
second rebalanced it). Behavior terms dominate confidence terms in every
variant by design, respecting the reward-hacking caution from Section 2.
(A third revision, which replaced the heuristic confidence shaping with a
proper scoring rule, belongs to the confidence-channel investigation and is
reported in the companion diagnosis paper.) We also trained the four
two-stage combinations of GRPO with DPO and KTO on the SFT-warmed base, in
both orders; they contribute a single null result, reported in one sentence
in Section 4.3.

### 3.4 Evaluation surface and metrics

The primary behavioral surface is SelfAware (Yin et al., 2023): 3,369 rows
per seed (1,032 unknown-labeled, 2,337 known-labeled). Scored rows carry row
identity, label, refusal flag, correctness flag, and truthfulness flag,
enabling exact paired row comparisons between arms (McNemar/exact binomial on
discordant counts). Primary metrics:

- *Refusal recall:* % of unknown rows refused (higher is better).
- *Over-refusal:* % of known rows refused (lower is better).
- *Correct-on-known:* % of known rows answered correctly.
- *Truthful:* % of all rows either correctly answered (known) or correctly
  refused (unknown).

Seed-level summaries report means and t-based 95% intervals over seed-level
point estimates; with three seeds these are descriptive. Two output contracts
are used and never pooled: a *plain-answer* contract (layers 1 and 2) and a
*response-confidence* contract (layer 3) in which the model returns an
answer plus a numeric confidence in $[0, 1]$. The contract is itself an
intervention (an early schema exposing an explicit answer/abstain decision
field induced base-model over-refusal in smoke tests, and was dropped), so
every GRPO-layer comparison is made against a clean-SFT baseline re-evaluated
under the same contract.

Confidence is scored against two targets, kept separate throughout: the
*known-label* target (1 for known rows, 0 for unknown) and *response
appropriateness* (1 when the model did the right thing for the row: answered
a known correctly or refused an unknown). Calibration metrics are emitted-
confidence standard deviation (a collapse detector), AUROC of confidence
against appropriateness and against correctness-given-answered, ECE, and
Brier score.

## 4. Behavioral results: induce, reposition, amplify

### 4.1 Only SFT induces abstention from the base model

Across three seeds on SelfAware, cold-start SFT reaches refusal recall 87.88%
(95% seed interval 77.36 to 98.41) at over-refusal 64.77% (63.60 to 65.94),
truthfulness 39.19%. Cold-start DPO and KTO do not learn the behavior at all:
DPO refusal recall is 0.03% and KTO 0.00%, with over-refusal near zero only
because the models refuse nothing. Paired rows make the difference exact: per
seed, SFT refuses 865 to 953 unknown rows that DPO answers, and 866 to 953
relative to KTO; all paired differences are overwhelming under exact tests.
Direct DPO-vs-KTO paired tests show no difference in unknown refusal (exact
$p = 1.0$ in all three seeds): on cold-start abstention, DPO and KTO are the
same failure mode.

![[figures/fig-p1-01-cold-start-tradeoff.png]]

**Figure 1. Cold-start SelfAware refusal trade-off.** Each faint point is one
seed and each outlined point is the mean across seeds. SFT occupies the
high-recall/high-over-refusal corner; cold-start DPO and KTO sit at the
answer-everything origin (inset). Trained from scratch, only SFT teaches the
model to refuse at all, and it overshoots; DPO and KTO leave it answering
essentially everything.

![[figures/fig-p1-03-paired-transitions.png]]

**Figure 2. Paired row transitions from SFT to the cold-start preference
arms.** Bars are seed means. DPO and KTO convert hundreds of correct SFT
abstentions into attempted answers; only a small fraction of known-question
conversions become correct answers.

This falsifies the natural hypothesis that KTO's unpaired binary format makes
it a native abstention trainer (Section 2, Gap 1). Data-format fit is not
sufficient; in this setting the preference objectives cannot conjure a
refusal routine that the policy does not already express. The result gives
the first half of the stage decomposition: **abstention must be induced, and
among these objectives only SFT induces it.**

### 4.2 Preference optimization repositions the boundary, on a trade-off

Applied after SFT, the preference methods do real work, but the work is
repositioning, not free improvement. From the merged-SFT operating point
(refusal recall 82.85%, over-refusal 61.62% on the seed-1 plain-answer
surface):

- DPO is the aggressive mover: over-refusal 61.62% to 13.99%, but refusal
  recall 82.85% to 48.84%. Exact transitions show the price: DPO answers 377
  unknown rows that SFT had correctly refused, and converts 1,113 known
  refusals into answers of which only 95 become correct.
- KTO is the conservative mover: over-refusal to 48.22% with recall
  preserved at 75.68%. It answers only 91 previously-refused unknown rows and
  converts 322 known refusals (37 correct).

![[figures/fig-p1-04-sft-warmed-tradeoff.png]]

**Figure 3. SFT-warmed operating points on SelfAware (plain-answer
contract).** DPO moves far toward low over-refusal at heavy recall cost; KTO
stays near the merged-SFT abstention policy. Neither arm improves
discrimination between the two kinds of question.

Across the available seeds the pattern is stable (three-seed SFT-DPO means:
recall 52.81%, over-refusal 14.59%, truthfulness 31.18%; two-seed SFT-KTO:
77.18%, 46.88%, 37.55%). This is the published C3 trade-off (Section 2)
reproduced at 4B on an independent model family, with the two preference
objectives landing on opposite ends of it: **DPO buys back usefulness at the
cost of abstention; KTO keeps the abstention and most of the tax.** Neither
improves the underlying discrimination; both move along the ROC curve the
SFT stage defined.

Under the stated-confidence contract, the same geometry reappears with a
confidence signature attached: mean stated confidence is 0.417 for merged
SFT, 0.760 for SFT-DPO, and 0.500 for SFT-KTO. Against the known/unknown
label DPO looks better calibrated than SFT (MAE 0.303 vs 0.424) because it is
confident on more known rows; against actual answer correctness it is much
worse (MAE 0.616 vs 0.282; Brier 0.564 vs 0.260) because many of its
confident answers are wrong. Repositioning toward answering *feels* like
confidence from the outside, and it is exactly the failure C1 predicts; this is the
same seam the program's readout paper later formalizes as two dissociable axes, an
answerability gate and a correctness dial ([*It's What's on the Inside That
Counts*](../paper-4-two-signal-readout/manuscript.md)).

![[figures/fig-p1-05-stated-confidence.png]]

**Figure 4. Stated-confidence profile of the SFT-warmed arms
(answer/confidence contract, three seeds).** Confidence coverage is near 100%
for all arms; the differences are behavioral and confidence-level shifts, not
parse failures. Judged against actual answer correctness (the two rightmost
metric groups, where lower is better), DPO's confidence is the least
trustworthy of the three.

![[figures/fig-p1-06-confidence-alignment.png]]

**Figure 5. Stated confidence by actual outcome.** All three regimens are
highly confident whenever they *answer*, including on wrong answers and on
unknown questions; refusals get near-zero confidence. Confidence tracks the
decision to answer, not the truth of the answer: a calibrated model would
show a tall first bar group and short answer groups, and instead every
answer sits near 0.9 whether it is right, wrong, or unanswerable.

### 4.3 GRPO amplifies the routine to near-ceiling recall

GRPO is the third behavioral profile, distinct from both preference methods.
All GRPO comparisons below are single-seed under the response-confidence
contract, against a clean-SFT baseline under the same contract (recall
87.02%, over-refusal 57.51%, truthful 40.58%); the same-contract DPO and KTO
arms land at (87.11%, 56.18%, 40.69%) and (81.01%, 52.37%, 39.36%).

| Arm (response-confidence contract, seed 1) | Truthful % | Refusal recall % | Over-refusal % | Correct-on-known % |
|---|---|---|---|---|
| clean SFT (baseline) | 40.58 | 87.02 | 57.51 | 47.23 |
| SFT then DPO | 40.69 | 87.11 | 56.18 | 46.09 |
| SFT then KTO | 39.36 | 81.01 | 52.37 | 44.03 |
| SFT then GRPO (first reward) | 39.69 | 95.54 | 75.70 | 61.80 |
| SFT then GRPO (rebalanced reward) | 41.08 | 93.41 | 66.62 | 53.85 |

![[figures/fig-p1-07-regimen-operating-points.png]]

**Figure 6. GRPO amplifies the abstention routine; stacks stay on its
frontier.** Operating points of all response-confidence-contract arms
(seed 1, exploratory), including the four two-stage GRPO/preference stacks.
The preference arms cluster with the SFT baseline; the GRPO arms and every
stack shift up-right: more recall, more over-refusal. No combination of
stages escapes the bargain; each picks a spot on the same curve.

Two observations. First, GRPO *amplifies* the abstention routine: refusal
recall rises to 93 to 98% (the first reward variant reached 97.87% on an
earlier SFT base), the highest of any arm, and truthfulness is the best in
the study (41.08 to 41.64% across the rebalanced variant and its stacks).
The appropriateness reward pays for refusing unknowns and the policy obliges,
hard. Second, the amplification drags over-refusal back up (66 to 76%,
versus 56 to 57% for the preference arms): GRPO undoes precisely the
repositioning that DPO buys. The reward's asymmetric hallucination penalty
makes refusal the safe action, and the policy generalizes the safety margin
onto known questions.

Stacking a preference stage with GRPO, in either order, does not escape the
trade-off: all four two-stage stacks land within 1.1 truthfulness points and
6 over-refusal points of plain SFT-GRPO (Figure 6), so we treat ordering as a
marginal adjustment to
the GRPO-defined operating point and do not analyze it further.

The stage decomposition is now complete: **SFT induces the behavior,
preference optimization repositions it, GRPO amplifies it.** Every objective
selects an operating point on the same recall/over-refusal frontier; nothing
we trained moves the frontier itself.

### 4.4 What the decomposition means for method choice

A naive league table would crown GRPO (best truthfulness) or DPO (best
over-refusal), but the decomposition says the question "which objective wins"
is malformed. The objectives do different jobs: an inducer is mandatory
(without SFT nothing abstains), and the second stage is a policy knob whose
setting depends on the deployment's asymmetric costs. What the field should
compare is not objectives but *regimens*, and regimens should be reported as
operating points with both error rates, never as single scalars. This is the
experiment-level confirmation of the reanalysis lesson from the synthesis
(Section 2): recall and over-refusal decouple, and any scalar hides which
failure a model makes.

## 5. The confidence channel points beyond behavior

Behavior is half the construct. The other half is whether the model can *say
how sure it is*, and the same runs supply one clean observation about it,
already visible in Figure 5: **emitted confidence tracks the decision to
answer, not the truth of the answer.** Every regimen is highly confident
whenever it answers, including on wrong answers and on unanswerable
questions; refusals get near-zero confidence. Under the response-confidence
contract the best-behaved checkpoint in the study, rebalanced-reward GRPO,
emits confidence with standard deviation 0.013 across 3,369 rows: a
near-constant ~0.8 whose AUROC against response appropriateness is 0.520, a
coin flip. The confidence token is decorative, and Section 4.2's DPO
signature is the same fact from the other side: repositioning toward
answering *looks like* rising confidence while correctness-conditioned
calibration worsens.

This is a diagnosis-sized question, not a paragraph-sized one: why RL
rewards cannot install the coupling (including a proper scoring rule for
which calibrated confidence is the mathematical optimum), what supervision
can and cannot do about it, and how much more the model's hidden states know
than any output channel says (on this same checkpoint, a held-out linear
probe of the hidden states reads the known/unknown boundary at AUROC 0.972
where the emitted channel reads 0.637). The program's companion diagnosis
paper takes it up on these same checkpoints; here we carry forward only the
warning the regimen practitioner needs: under every regimen in this study,
the stated confidence number reports what the model *did*, not what it
*knows*.

## 6. Discussion

### The regimen, not the objective

The synthesis's method gaps (no
KTO-for-abstention, no three-way, no controlled GRPO comparison) presumed the
interesting question was *which objective*. The experiment's answer is that
objectives are stages with different jobs: induce (SFT only), reposition
(DPO aggressively, KTO conservatively), amplify (GRPO). League tables that
compare them head-to-head as alternatives, including the ones in the
synthesis corpus, are comparing a hammer to a chisel by how far each drives
the nail.

### The frontier did not move

Nothing here, including the best stack,
improved discrimination between known and unknown; every intervention chose a
point on the frontier the SFT stage created. The natural mechanistic reading
is that the discriminative signal lives somewhere the output objectives do
not touch, and Section 5's probe observation (internal AUROC 0.972 against
emitted 0.637 on the same rows) supports it: the stage decomposition is a
decomposition of *policy* over an epistemic signal the training never moved.
The companion diagnosis paper makes that case at the representation level;
the behavioral fact stands on its own here. A pre-registered follow-up in the
companion line has since located the signal's origin: read on *pre-instruction*
bases across four model families, the known/unknown boundary is already
linearly available at AUROC 0.997+ before any post-training occurs (§4.11 of
the program's training-free readout paper, [*It's What's on the Inside That
Counts: A Training-Free Two-Signal Readout for Epistemic Humility in Small
Language Models*](../paper-4-two-signal-readout/manuscript.md)). The frontier the
SFT stage "created" is therefore better read as a frontier it *exposed*: the
discriminative signal is already paid for by pretraining, and no objective
in this study (nor, apparently, the vendors' own post-training) moves it.

### Deployment reading

For a practitioner at small scale the actionable
summary is: (i) an SFT inducer stage is mandatory; (ii) choose the second
stage by your cost asymmetry (DPO if over-refusal is expensive, KTO or GRPO
if hallucination is); (iii) do not trust the model's stated confidence under
any of these regimens (Section 5), and do not expect an RL reward to fix it;
(iv) if you control the weights, the companion work indicates a linear probe
of the hidden states is a dramatically better uncertainty ranking signal than
anything the model will tell you.

## 7. Limitations

This is a small-model, single-family study: Qwen3-4B with LoRA/QLoRA
recipes, evaluated centrally on SelfAware. The cold-start and SFT-warmed
layers carry three seeds (descriptive t-intervals; SFT-warmed KTO has two
plain-answer seeds); the GRPO layer, its stacks, and the stated-confidence
observations of Section 5 are single-seed and exploratory, and are labeled
as such wherever they appear. Negative cold-start DPO/KTO results are claims
about this setting and recipe family, not contradictions of sequential
preference results in the literature. The two output contracts
(plain-answer and response-confidence) are never pooled, but each is an
intervention in its own right, and stated-confidence results are conditional
on the contract. GRPO conclusions are conditional on the reward family
tested (appropriateness-dominant with confidence shaping); a reward designed
around a different decomposition could behave differently.

Model-specific known/unknown labels are noisy (the synthesis measured 42.9
to 51.3% of "unknown" answers being correct in released artifacts of the
lineage we follow), which flattens all recall/over-refusal numbers toward
the middle; our labels are regenerated per-model but not immune to the same
effect. The limitations of the evidence synthesis this experiment is built
on are discussed in [*The Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md).

## 8. Conclusion

The systematic evidence says post-training is where epistemic humility is
made and broken, and it says the field has been comparing training objectives
without ever running them on the same data, the same base, and the same
measurement panel. Running that comparison at 4B yields a stage
decomposition: SFT induces abstention (with a heavy over-refusal tax),
preference optimization repositions the boundary (DPO toward answering, KTO
toward caution), and GRPO amplifies the routine to the best truthfulness and
recall in the study while re-inflating over-refusal. No objective, order, or
stack moves the discrimination frontier itself; the right unit of comparison
is the regimen, and the right report is an operating point with both error
rates.

The stated-confidence measurement adds the practitioner's warning: under
every regimen tested, the confidence number the model writes out tracks the
decision to answer, not the truth of the answer. Why the stated channel
fails, whether any training can couple it to what the model knows, and how
much a direct readout of the hidden states recovers, are the subjects of the
companion diagnosis paper, [*Knows but Doesn't
Say*](../paper-3-knows-but-doesnt-say/manuscript.md), which begins from the
checkpoints this study trained. The companion line has since answered the
origin half of the question this paper leaves open: the epistemic signal the
regimens gate on is present *before any post-training* ([*It's What's on the
Inside That Counts*](../paper-4-two-signal-readout/manuscript.md), §4.11).
Post-training sets the behavior; pretraining supplies the signal.

## References

Cheng, Q., Sun, T., Liu, X., Zhang, W., Yin, Z., Li, S., Li, L., He, Z.,
Chen, K., & Qiu, X. (2024). *Can AI Assistants Know What They Don't Know?*
arXiv:2401.13275.

Cundy, C., & Gleave, A. (2025). *Preference Learning with Lie Detectors can
Induce Honesty or Evasion*. arXiv:2505.13787.

Damani, M., Puri, I., Slocum, S., Shenfeld, I., Choshen, L., Kim, Y., &
Andreas, J. (2025). *Beyond Binary Rewards: Training LMs to Reason About
Their Uncertainty*. arXiv:2507.16806.

DeVilling, B. (2025). *The Polite Liar: Epistemic Pathology in Language
Models*. arXiv:2511.07477.

Ethayarajh, K., Xu, W., Muennighoff, N., Jurafsky, D., & Kiela, D. (2024).
*KTO: Model Alignment as Prospect Theoretic Optimization*. arXiv:2402.01306.

Gekhman, Z., Yona, G., Aharoni, R., Eyal, M., Feder, A., Reichart, R., &
Herzig, J. (2024). *Does Fine-Tuning LLMs on New Knowledge Encourage
Hallucinations?* arXiv:2405.05904.

Joshi, M., Choi, E., Weld, D. S., & Zettlemoyer, L. (2017). *TriviaQA: A
Large Scale Distantly Supervised Challenge Dataset for Reading
Comprehension*. arXiv:1705.03551.

Kadavath, S., et al. (2022). *Language Models (Mostly) Know What They Know*.
arXiv:2207.05221.

Kalai, A. T., Nachum, O., Vempala, S. S., & Zhang, E. (2025). *Why Language
Models Hallucinate*. arXiv:2509.04664.

Kirichenko, P., Ibrahim, M., Chaudhuri, K., & Bell, S. J. (2025).
*AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions*.
arXiv:2506.09038.

Lithgow-Serrano, O., Kanjirangat, V., & Antonucci, A. (2025). *Causal
Understanding by LLMs: The Role of Uncertainty*. arXiv:2509.20088.

Mohamadi, M. A., Wang, T., & Li, Z. (2025). *Honesty over Accuracy:
Trustworthy Language Models through Reinforced Hesitation*. arXiv:2511.11500.

OpenAI (2023). *GPT-4 Technical Report*. arXiv:2303.08774.

Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C.
(2023). *Direct Preference Optimization: Your Language Model is Secretly a
Reward Model*. arXiv:2305.18290.

Rosenbaum, J. (2026). *The Depths of Ignorance: A Taxonomy, Systematic
Evidence Synthesis, and Research Agenda for Epistemic Humility in Language
Models*. Companion draft, this repository:
[papers/paper-1-taxonomy-framework/manuscript.md](../paper-1-taxonomy-framework/manuscript.md).

Rosenbaum, J. (2026). *Knows but Doesn't Say: A Training-Resistant Gap
Between Internal and Stated Confidence in a Small Language Model*. Companion
draft, this repository:
[papers/paper-3-knows-but-doesnt-say/manuscript.md](../paper-3-knows-but-doesnt-say/manuscript.md).

Rosenbaum, J. (2026). *It's What's on the Inside That Counts: A Training-Free
Two-Signal Readout for Epistemic Humility in Small Language Models*.
Companion draft, this repository:
[papers/paper-4-two-signal-readout/manuscript.md](../paper-4-two-signal-readout/manuscript.md).

Shao, Z., et al. (2024). *DeepSeekMath: Pushing the Limits of Mathematical
Reasoning in Open Language Models* (GRPO). arXiv:2402.03300.

Tian, K., Mitchell, E., Yao, H., Manning, C. D., & Finn, C. (2023).
*Fine-tuning Language Models for Factuality*. arXiv:2311.08401.

Wang, Z., Shi, Z., Zhou, H., Gao, S., Sun, Q., & Li, J. (2025). *Towards
Objective Fine-tuning: How LLMs' Prior Knowledge Causes Potential Poor
Calibration?* arXiv:2505.20903.

Wei, Z., Yang, X., Sun, K., Wang, J., Shao, R., Chen, J., et al. (2025).
*TruthRL: Incentivizing Truthful LLMs via Reinforcement Learning*.
arXiv:2509.25760.

Yin, Z., Sun, Q., Guo, Q., Wu, J., Qiu, X., & Huang, X. (2023). *Do Large
Language Models Know What They Don't Know?* arXiv:2305.18153.

Zhai, S., Liang, J., & Kang, D. (2026). *Abstain-R1: Calibrated Abstention
and Post-Refusal Clarification via Verifiable RL*. arXiv:2604.17073.

Zhang, H., Diao, S., Lin, Y., Fung, Y. R., Lian, Q., Wang, X., Chen, Y.,
Ji, H., & Zhang, T. (2023). *R-Tuning: Instructing Large Language Models to
Say "I Don't Know"*. arXiv:2311.09677.

---

## Appendix A: Provenance (internal labels to artifacts)

Reader-facing prose above uses no internal amendment labels. For
reproducibility, the mapping from every experimental claim to its governing
protocol document and scored artifact:

| Paper section | Internal label | Protocol / notes | Primary artifacts |
|---|---|---|---|
| 4.1 cold start (3 seeds) | headline matrix, PROTOCOL v0.3 | `archive/docs/protocols/phase1/PROTOCOL.md` | `archive/experiment/phase1/eval/results_selfaware_full_seed{1,2}_all_arms_4b_20260615_2148/`, `..._seed3_..._20260616_0615/`; tables in `papers/paper-2-training-regimen/analysis/paper1_results_analysis.md` |
| 4.2 SFT-warmed DPO/KTO | Amendment A | legacy session/artifact lineage; no governed amendment doc found during migration | `archive/experiment/phase1/eval/results_amendment_a_selfaware_full_*` |
| 4.2 stated-confidence contract | Amendment B | `experiments/stated-confidence-grpo/AMENDMENT.md` | `archive/experiment/phase1/eval/results_amendment_b_stated_confidence_*` |
| 4.3 GRPO first reward (schema base) | Amendment D | `experiments/schema-response-confidence/AMENDMENT.md` | `results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_full_4b/` |
| 4.3 clean-SFT baseline + GRPO v1/v2 | Amendment E | `experiments/probe-scaled-response-confidence/AMENDMENT.md` | `results_amendment_e_response_confidence_selfaware_clean_sft_{merged,dpo,kto,grpo,grpo_v2}_seed1_*_full_4b/` |
| 4.3 stacking null (one sentence) | Amendment F | `experiments/grpo-centered-stacking/AMENDMENT.md` | `results_amendment_f_response_confidence_selfaware_clean_sft_{dpo_grpo,grpo_dpo,grpo_kto,kto_grpo}_seed1_full_4b/` |
| 5 confidence collapse (GRPO v2) | Amendment J diagnostics / session 0026 | `experiments/grpo-v3-proper-scoring-confidence/RUNBOOK.md` | `archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json` |
| 5 probe vs emitted channel | probe program (caution-vs-doubt note) | `archive/notes/experiments/caution-vs-doubt-knowledge-gate.md` | `calibration_gap_clean_sft_grpo_v2_seed1.json` (`B_internal_vs_emitted`: internal AUROC 0.972 vs emitted 0.637) |
| grouped behavioral inventory | all of the above | | `archive/experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv` |
| 3.3 training recipes, seeds, and per-run records | all arms | | `archive/experiment/phase1/recipes/`; `archive/experiment/phase1/run_records/` |

Governance notes: the three-seed cold-start block is the pre-registered
headline surface (PROTOCOL v0.3, signed 2026-06-10); Amendments A/B are signed
prospective extensions; Amendments D/E/F/J are exploratory single-seed
evidence cells with pre-stated predictions and falsifiers, reported here as
exploratory and never pooled with the headline block. The confidence-channel
training variants (proper-scoring GRPO, contrastive SFT, RL-on-contrastive,
and their descendants; the confidence-channel amendment set, Amendments
J/K/L/M/N) and the probe program are reported in full in the
companion diagnosis paper, [*Knows but Doesn't
Say*](../paper-3-knows-but-doesnt-say/manuscript.md); the readout work is reported
in [*It's What's on the Inside That
Counts*](../paper-4-two-signal-readout/manuscript.md) and the steering work in a
fifth companion paper of this research line, maintained in the same
repository.

## Appendix B: Evidence-synthesis pointer

The systematic evidence synthesis this experiment is designed against is
the program's companion synthesis paper, [*The Depths of
Ignorance*](../paper-1-taxonomy-framework/manuscript.md) (taxonomy, claim families
C1–C5, and the six-gap analysis), whose source-of-record apparatus lives at
`meta-analysis/paper/draft-v0.md` with evidence tables under
`meta-analysis/evidence/` and analysis scripts under
`meta-analysis/analysis/`.
