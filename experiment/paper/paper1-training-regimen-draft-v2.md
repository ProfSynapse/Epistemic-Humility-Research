---
title: "Teaching Small Language Models to Say I Don't Know: A Systematic Evidence Synthesis and a Controlled Comparison of SFT, DPO, KTO, and GRPO"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v2
date: 2026-07-01
supersedes: paper1-training-regimen-draft-v1.md (experiment portion), meta-analysis/paper/draft-v0.md (absorbed as Part I review)
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
reproducibility: >
  Behavioral tables and Figures 1-5 regenerate via
  experiment/paper/scripts/build_paper1_figures.py into
  experiment/paper/analysis/ and experiment/paper/figures/; Figures 6-8
  (regimen operating points, confidence channel, knows-vs-says) regenerate via
  experiment/paper/scripts/build_paper1_v2_figures.py. The grouped run inventory is
  experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv.
  Confidence-channel analyses regenerate via
  experiment/phase1/eval/analysis/calibration_gap_report.py. Full
  amendment-to-artifact provenance is in Appendix A.
notes: >
  Numbers discipline: every quantitative claim in Part I traces to
  meta-analysis/evidence/effects.csv (78 rows, 39 studies) or the reanalysis
  scripts under meta-analysis/analysis/; every claim in Part II traces to a
  metrics.json or calibration-gap JSON named in Appendix A. Reader-facing prose
  carries no internal amendment labels; the label-to-artifact map lives only in
  Appendix A. Math is set in LaTeX (inline $...$ / display $$...$$,
  pandoc-compatible). Citations are author-year; the References section is
  complete and one-to-one with in-text citations.
---

# Teaching Small Language Models to Say I Don't Know: A Systematic Evidence Synthesis and a Controlled Comparison of SFT, DPO, KTO, and GRPO

Joseph Rosenbaum
Synaptic Labs

*Draft v2. Not for distribution.*

> *"It is likely that neither of us knows anything worthwhile, but he thinks he knows something when he does not, whereas I, as I do not know, do not think I know either."*
>
> Plato, *Apology* 21d

## Abstract

Language models acquire most of their epistemic character (how confident they
sound, when they refuse, how readily they capitulate) not from pretraining but
from post-training. We present a systematic synthesis of the training evidence
(78 quantitative effects from 39 studies) and then run the experiment it shows
to be missing: the first controlled comparison of SFT, DPO, KTO, and GRPO on a
shared model-specific abstention dataset and base model (Qwen3-4B), with
behavior, stated confidence, and internal representations measured after the
same runs. The comparison yields a stage decomposition rather than a winner.
Only SFT *induces* abstention (refusal recall 87.9%, over-refusal 64.8%;
cold-start DPO and KTO refuse almost nothing); preference optimization
*repositions* the boundary along a recall/over-refusal trade-off; GRPO
*amplifies* the routine to near-ceiling recall and the study's best
truthfulness while re-inflating over-refusal. No objective, order, or stack
moves the underlying discrimination frontier. The confidence channel fails
independently of behavior: every GRPO reward tested, including a proper
scoring rule for which calibrated confidence is the mathematical optimum,
leaves emitted confidence collapsed near a constant, while contrastive
supervision calibrates the channel at severe behavioral cost. Throughout, a
linear probe reads the knowledge boundary from hidden states at AUROC 0.97
versus 0.52 to 0.68 for the emitted channel: after every regimen, the model
knows more than it says. Training reshapes what the model does with its
uncertainty; it neither creates nor surfaces the signal itself.

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
The contention of this paper is that these failures are primarily facts about
*training*, specifically post-training, and it argues that contention twice
over: first with a systematic synthesis of the published evidence, then with a
controlled experiment that runs the comparisons the synthesis shows to be
missing.

Three strands of published evidence converge on training as the causal locus.

**First, pretrained models already know how likely they are to be right;
post-training breaks the readout.** The GPT-4 technical report measures an
expected calibration error (ECE) of 0.007 for the pretrained base model on a
subset of MMLU; after reinforcement learning from human feedback (RLHF), ECE on
the same subset rises tenfold to 0.074 (OpenAI, 2023). Kadavath et al. (2022)
identify the mechanism (RLHF concentrates probability mass on high-reward
outputs, sharpening every distribution whether or not the model's knowledge
warrants it) and show that a single temperature adjustment largely restores
calibration. That repairability is itself evidence: the
signal survives in the weights; it is merely expressed too confidently.

**Second, the damage is not specific to reinforcement learning.** A controlled
comparison on the same base model finds plain instruction tuning nearly
tripling ECE (0.13 to 0.36) while simultaneously *reducing* predictive entropy
(1.32 to 0.92) (Lithgow-Serrano et al., 2025): the tuned model becomes more decisive and
less reliable about its own reliability at the same time.

**Third, the converse also holds: what training breaks, training can
deliberately improve.** Refusal-aware tuning, factuality-aware DPO, calibrated
reward models, and listener-aware preference pairs consistently improve
humility metrics, often by large margins (Section 3, family C5).

What has been missing is (a) a synthesis that treats the calibration,
abstention, hallucination, sycophancy, and method-comparison literatures as one
evidence base about a single underlying construct, and (b) the experiment that
synthesis most directly calls for: the same base model, the same
model-specific abstention data, every major post-training objective, and a
measurement panel that covers behavior, stated confidence, and internal
representations after the same runs. This paper supplies both. Part I
(Sections 2 to 4) condenses our systematic synthesis: methods, the five claim
families, the independent reanalyses, and the verified gaps. Part II (Sections
5 to 9) reports the experiment: a four-objective regimen study on Qwen3-4B
whose design is read off the gaps directly.

Contributions:

1. A unified extraction of 78 quantitative effects from 39 studies into a
   single schema, synthesized by vote counting and exact binomial sign tests,
   with independent reanalyses of three studies' released artifacts and a
   verified six-gap analysis of experiments the field has not run (Part I;
   full detail in the project repository under `meta-analysis/`).
2. The first SFT / DPO / KTO / GRPO comparison on shared abstention data and a
   shared small open-weights base, with seed-level intervals and exact
   row-level paired transitions (Sections 6.1 to 6.4). This closes the
   synthesis's Gaps 1 to 3 at the behavioral level.
3. A stage decomposition of the regimen: SFT induces, preference optimization
   repositions, GRPO amplifies. No objective, sequence, or stack we tested
   escapes the recall/over-refusal trade-off; they select operating points on
   it (Section 6).
4. A measurement of the confidence channel after the same runs: emitted
   confidence collapses under every GRPO reward tested, including a proper
   scoring rule for which calibration is the optimum; supervised contrastive
   confidence data calibrates the channel but at behavioral cost; and the two
   failures are structural rather than a regularization artifact (Section 7).
5. A representation-level coda: across checkpoints, a linear probe reads the
   knowledge boundary from hidden states at AUROC 0.97 while the emitted
   channel reads 0.52 to 0.68, reframing the training problem as a *readout*
   problem (Section 8).

---

# Part I: What the evidence says

## 2. Scope, framework, and synthesis method

We use *epistemic humility* as an umbrella for behaviors and properties that
make a model's expressed epistemic state track its actual reliability:
token-probability and verbalized-confidence calibration; appropriate abstention
("I don't know") with low over-refusal; resistance to hallucination on
unfamiliar inputs; and resistance to sycophantic capitulation. *Post-training*
covers everything after pretraining: supervised/instruction fine-tuning (SFT);
preference optimization, including RLHF with PPO (Ouyang et al., 2022; Schulman et al., 2017), direct preference optimization (DPO) (Rafailov et al., 2023),
and Kahneman-Tversky optimization (KTO) (Ethayarajh et al., 2024); and RL with
programmable rewards, including group relative policy optimization (GRPO)
(Shao et al., 2024).

### 2.1 The Depths of Ignorance

A synthesis needs an organizing taxonomy, and the natural one is not a method
taxonomy (existing surveys of abstention (Wen et al., 2024) and honesty
(Li et al., 2024) provide those) but a *depth* taxonomy: a hierarchy of what,
exactly, is being formalized when a model "expresses ignorance."

- **L1: Confidence/calibration.** "How sure am I?" as a scalar: token
  probabilities and verbalized percentages (Lin et al., 2022; Tian et al.,
  2023a), scored by ECE, Brier score, and
  AUROC. This is the level of nearly all training work synthesized below.
- **L2: Structured ignorance.** "What am I missing?" as structure: gap-naming,
  knowledge-intersection identification, retrieval proposals (Sahoo, 2026; Taparia et al., 2026).
- **L3: Distributional/third-person signatures.** "What shape is my failure?"
  read from outside the model: population-level features of repeated failed
  attempts (Islah et al., 2026).
- **L4: Objective uncertainty.** "What should I even be optimizing?" as
  calibrated uncertainty over the reward itself (GX-Chen et al., 2026).

To the depths we add one **cross-cutting axis: coherence/faithfulness**. At any
level one can ask whether the model's *stated* signal, its *token-level*
signal, and its *hidden-state* signal agree. Token-probability, hidden-state,
and sampled-consistency estimators of internal confidence are documented to
diverge on the same reasoning traces (Gani et al., 2026). The coherence axis is
what distinguishes *possessed* humility from *performed* humility, and the
mapping exercise below shows it is almost entirely unmeasured in the training
literature. Part II's design makes it a primary measurement.

### 2.2 Corpus and method, briefly

Evidence was gathered in June 2026 through six structured searches (110
documented queries) plus a backward-citation pass over the full bibliography
(~4,000 referenced works ranked via the Semantic Scholar Graph API). The
corpus holds 78 effect rows from 39 studies (2021 to 2026) spanning calibration
(17 rows), abstention (26), hallucination/factuality (12), knowledge-boundary
(2), sycophancy (15), methods (4), and capability (2); 76 of 78 rows are
verified against a primary PDF or artifact, and headline claims rest on
verified rows only. Because the literature almost never reports variance (zero
error bars in any retrieved material from the twelve calibration studies in
our primary searches), we synthesize by vote counting with exact binomial sign
tests and descriptive normalization rather than formal pooling, following the
SWiM guideline and the Cochrane Handbook's sanctioned direction-based vote
count. Search protocol, inclusion criteria, extraction schema, verification
protocol, flow accounting, and the AI-assistance disclosure are maintained in
full in the project repository (`meta-analysis/paper/draft-v0.md` and
`meta-analysis/evidence/`); this section reports what Part II's design
consumes.

## 3. Five claim families

**C1: Instruction tuning and RLHF degrade token-probability calibration.**
Two extracted head-to-head rows support, none contradict; magnitudes 176.9%
and 957.1% relative. GPT-4's ECE rises 0.007 to 0.074 after RLHF on the same
MMLU subset (OpenAI, 2023); the same-base Pythia-7B to Dolly-v2-7B
comparison rises 0.13 to 0.36 while predictive entropy falls (Lithgow-Serrano et al., 2025).
Three further studies corroborate the direction without extractable pairs
(Zhu et al., 2023; He et al., 2023; Ye et al., 2024). The mechanism-level
finding that matters for Part II: what does the damage is the relationship
between the tuning data and *this model's* knowledge. Fine-tuning on facts the
model does not know causally drives hallucination (Gekhman et al., 2024); data
aligned with prior knowledge induces overconfidence, while genuinely novel
data improves calibration (Wang et al., 2025). Fitting unknowns teaches
hallucination, and fitting knowns teaches overconfidence, which is why every
successful abstention method builds *model-specific* training splits.

**C2: Preference-based methods beat SFT on abstention/truthfulness quality.**
Every extracted preference-over-SFT comparison is positive except one (the IPO
variant underperforms by 5.4% (Saeidi et al., 2024)). The anchor is the only
within-paper tournament on model-specific IDK data: on Llama-2-7b-chat
truthful rate, Idk-Prompting 66.93 < Idk-SFT 74.75 < Idk-HIR 75.91 < Idk-PPO
76.47 < Idk-DPO 77.89 < Idk-BoN 78.96 (Cheng et al., 2024). Our reanalysis of
AbstentionBench's released results adds an independent lineage: on the Tulu-3
ladder, DPO beats SFT on abstention recall by a paired median of +0.08 at 8B
($p = 5.5 \times 10^{-4}$) (Kirichenko et al., 2025; our reanalysis). KTO beats SFT on TruthfulQA by
+2.2 points from an SFT'd base and +9.3 from the pretrained base
(Saeidi et al., 2024). The median magnitude across the family (5.0%) is an order
of magnitude smaller than the C1 damage.

**C3: Preference optimization reduces SFT-induced over-refusal.** Our
output-level reanalysis of Cheng et al.'s (2024) released Llama-2-7b-chat outputs
($n = 11{,}313$) supplies the exact numbers the paper's aggregate "truthful rate"
obscures:

| Method | Refusal recall on unknown (%) | Over-refusal on known (%) |
|---|---|---|
| Idk-SFT | 84.06 | 42.71 |
| Idk-DPO | 71.19 | 23.27 |
| Idk-PPO | 73.89 | 30.86 |
| Idk-BoN | 73.95 | 25.64 |
| Idk-HIR | 88.37 | 45.16 |

DPO cuts SFT's over-refusal nearly in half, but the improvement is a *trade*:
refusal recall on genuinely unknown questions falls 84.06 to 71.19. Preference
optimization moves the operating point along a refusal ROC curve; it does not
obviously improve the underlying discrimination. Our second reanalysis bounds
the claim: on the Tulu-3 ladder, where SFT is general-purpose rather than
abstention-targeted, there is no over-refusal deficit to repair, so
SFT-induced over-refusal is a property of abstention-targeted SFT data, not of
SFT per se (the same data-dependence appears in safety tuning, where added
safety examples induce exaggerated refusal of benign prompts; Bianchi et
al., 2023). Two further observations from the reanalyses discipline
everything in Part II: single-scalar abstention metrics hide which failure a
model makes (recall and precision are decoupled across 20 models, Spearman
$\rho = -0.05$), and model-specific known/unknown labels are themselves noisy
(42.9 to 51.3% of answers on unknown-labeled questions were in fact correct).

**C4: Scale alone does not produce epistemic humility.** Four studies support,
none contradict. The best GPT-3 model is truthful on 58% of TruthfulQA against
a 94% human baseline, with inverse scaling within families (Lin et al., 2021);
GPT-4 detects unanswerable questions at $F_1 = 75.47$ versus a human 84.93
(Yin et al., 2023; see also the known-unknowns
probing of Amayuelas et al., 2023); sycophancy grows with scale (Perez et al., 2022; Wei et al., 2023); and in our reanalysis of AbstentionBench, 50x more
parameters moves Llama 3.1 Instruct median abstention recall by 0.02 while a
single DPO stage moves it 0.08. Waiting for the next model generation does not
solve this problem; training design does or does not.

**C5: Targeted training interventions improve humility metrics.** Eleven
studies supporting, none contradicting, the corpus's only conventionally
significant sign test ($p = 0.001$); median |relative change| 40.1%. The
supporting set spans intervention types (refusal-aware SFT (Zhang et al., 2023),
honesty-targeted SFT (Yang et al., 2023), factuality DPO (Tian et al., 2023b),
listener-aware DPO (Stengel-Eskin et al., 2024), calibrated-reward PPO
(Leng et al., 2024), self-reflective confidence training (Xu et al., 2024),
self-trained uncertainty expression (Liu et al., 2024), and others), which is what makes the signal credible; what it is *not* is
evaluated on more than a slice of the humility construct per study.

**The unifying tension.** Set C1 beside C2/C3: preference-based post-training
is the best available tool for abstention quality and over-refusal control,
and preference-based post-training is the documented destroyer of token-level
calibration. These findings come from disjoint studies measuring disjoint
metrics on disjoint models. **No study in our corpus measures calibration,
abstention quality, and factuality after the same preference-training run.**
It is therefore unknown whether the methods that teach a model to *say* "I
don't know" at the right times simultaneously degrade the signal that says the
same thing: whether we are buying stated humility by selling calibrated
humility. Part II measures exactly this, within single runs.

## 4. What the field has not run

The gap analysis was run the opposite way from the rest of the synthesis:
instead of searching for what the literature contains, it searched for studies
that *should* exist and do not. Each gap is a falsifiable claim about absence
as of June 2026. Six were verified; the three that Part II closes or
addresses:

- **Gap 1: KTO has never been applied to abstention, honesty, or calibration
  training** (high confidence; zero hits across targeted searches, and the KTO
  paper's own application list contains none). The gap matters because KTO's
  structure fits the problem unusually well: it consumes exactly the unpaired
  binary desirable/undesirable labels a known/unknown split naturally
  produces, and its prospect-theoretic loss weights losses asymmetrically, as
  this domain's costs are (a confident hallucination typically does more
  damage than an unnecessary abstention).
- **Gap 2: No SFT vs. DPO vs. KTO three-way comparison exists on the same
  abstention dataset** (high confidence). Cheng et al. (2024) compare five methods
  but not KTO; the one SFT/DPO/KTO comparison that exists uses generic
  benchmarks, not abstention training. Every component of the experiment
  exists in print; no study assembles them.
- **Gap 3: GRPO-for-abstention exists, but no controlled comparison against
  SFT/DPO/KTO does, and none looks beneath behavior.** The verifiable-RL
  cluster now includes TruthRL's ternary reward (Wei et al., 2025), Abstain-R1
  (Zhai et al., 2026), reinforced hesitation (Mohamadi et al., 2025), and the
  correctness-minus-Brier reward of RLCR (Damani et al., 2025), but none is
  benchmarked against the preference families on shared data, and none
  measures internal representations. One caution from this literature binds
  our design: probes placed *inside* RL reward loops get gamed
  (Cundy & Gleave, 2025), so representation probes must remain held-out
  evaluation, never reward.

The remaining verified gaps (no probe-transfer study of whether humility
training changes representations or only behavior; no IDK-fraction
dose-response curve; thin small-model and OOD coverage) motivate the
measurement panel here and the companion work discussed in Section 9. Gap 6's
small-model complaint is addressed by construction: everything in Part II runs
at 4B parameters.

---

# Part II: The experiment

## 5. Design and methods

### 5.1 Design logic

The experiment is the synthesis's missing study, assembled. One base model
(Qwen3-4B), one model-specific known/unknown data construction, and four
training objectives, evaluated on a shared surface with a panel that covers
both halves of every trade-off the reanalyses exposed: refusal recall *and*
over-refusal, truthfulness *and* correct-on-known, stated confidence *and*
its calibration, behavior *and* the hidden-state signal underneath it.

The study has four evidence layers, reported in order of evidential strength:

1. **Cold-start comparison** (three seeds): SFT, DPO, and KTO trained from the
   base model. Answers whether each objective can *induce* abstention.
2. **SFT-warmed comparison** (three seeds for DPO, two for KTO): preference
   optimization applied after SFT. Answers whether the preference objectives
   can *reposition* an existing boundary, the sequential reading C2/C3
   suggest.
3. **GRPO and stacking** (single seed, exploratory): GRPO applied after SFT
   under a behavior-dominant appropriateness reward, plus the four two-stage
   stacks of GRPO with DPO/KTO in both orders. Answers what RL with a
   programmable reward adds, and whether ordering matters.
4. **The confidence channel** (single seed, exploratory): stated-confidence
   contracts, reward variants targeting calibration directly (including a
   proper scoring rule), a supervised contrastive-confidence recipe, and
   RL-after-calibration, each scored against both behavior gates and
   calibration gates, with a hidden-state probe as the held-out reference.

Layers 1 and 2 carry seed-level intervals and exact paired row tests; layers 3
and 4 are single-seed and labeled exploratory throughout. We report the
distinction rather than pooling across it.

### 5.2 Data construction

The IDK data construction follows the model-specific known/unknown lineage of
Cheng et al. (2024), regenerated for the model under study rather
than borrowed (the labels are model-specific by construction, and Part I
measured 42.9 to 51.3% label noise in borrowed labels). The base model is
probed on factoid QA (TriviaQA lineage (Joshi et al., 2017)); questions it
answers correctly under the probe protocol become "known," questions it
consistently fails become "unknown," ambiguous cases are excluded. SFT
receives direct targets (answer the known, refuse the unknown); DPO receives
chosen/rejected pairs; KTO receives the same rows as unpaired
desirable/undesirable examples; GRPO receives no supervised targets at all,
only a reward over sampled completions.

### 5.3 Training arms

All arms use resource-feasible LoRA/QLoRA recipes on Qwen3-4B; recipes,
seeds, and per-run records are committed in the repository
(`experiment/phase1/recipes/`, `experiment/phase1/run_records/`). The
comparison should be read as a replication-style stress test of the
known/unknown supervision idea at small scale, not a bit-for-bit reproduction
of any prior stack.

**SFT, DPO, KTO** are standard implementations of their objectives. Each is
trained both cold (from base) and SFT-warmed (from the merged SFT
checkpoint).

**GRPO** samples groups of completions per prompt and optimizes
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
second rebalanced it), and a third replaced heuristic confidence shaping with
a proper scoring rule (Section 7.2). Behavior terms dominate confidence terms
in every variant by design, respecting the reward-hacking caution from Part I.

**Stacks.** Four two-stage combinations on the SFT-warmed base: DPO then
GRPO, GRPO then DPO, KTO then GRPO, GRPO then KTO.

### 5.4 Evaluation surface and metrics

The primary behavioral surface is SelfAware (Yin et al., 2023): 3,369 rows
per seed (1,032 unknown-labeled, 2,337 known-labeled). Scored rows carry row
identity, label, refusal flag, correctness flag, and truthfulness flag,
enabling exact paired row comparisons between arms (McNemar/exact binomial on
discordant counts). Primary metrics:

- **Refusal recall:** % of unknown rows refused (higher is better).
- **Over-refusal:** % of known rows refused (lower is better).
- **Correct-on-known:** % of known rows answered correctly.
- **Truthful:** % of all rows either correctly answered (known) or correctly
  refused (unknown).

Seed-level summaries report means and t-based 95% intervals over seed-level
point estimates; with three seeds these are descriptive. Two output contracts
are used and never pooled: a *plain-answer* contract (layers 1 and 2) and a
*response-confidence* contract (layers 3 and 4) in which the model returns an
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

**The held-out probe.** For representation-level measurement we fit linear
probes on hidden states (layer 35 of 36) over the evaluation prompts,
strictly post hoc: probes never touch any reward or training signal. The
probe's AUROC against the known/unknown label is the ceiling estimate of what
the checkpoint *internally* encodes; the gap between it and the emitted
channel's AUROC is the paper's coherence measurement (Section 8).

## 6. Behavioral results: induce, reposition, amplify

### 6.1 Only SFT induces abstention from the base model

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
answer-everything origin (inset). In plain terms: trained from scratch, only
SFT teaches the model to say "I don't know" at all, and it overshoots,
refusing many questions it could answer; DPO and KTO leave the model
answering essentially everything, so there is no abstention behavior for
them to improve.

![[figures/fig-p1-03-paired-transitions.png]]

**Figure 2. Paired row transitions from SFT to the cold-start preference
arms.** Bars are seed means. DPO and KTO convert hundreds of correct SFT
abstentions into attempted answers; only a small fraction of known-question
conversions become correct answers. In plain terms: question by question,
switching from SFT to a cold preference method mostly turns good refusals
into guesses, and few of those guesses turn out to be right.

This falsifies the natural hypothesis that KTO's unpaired binary format makes
it a native abstention trainer (Part I, Gap 1). Data-format fit is not
sufficient; in this setting the preference objectives cannot conjure a
refusal routine that the policy does not already express. The result gives
the first half of the stage decomposition: **abstention must be induced, and
among these objectives only SFT induces it.**

### 6.2 Preference optimization repositions the boundary, on a trade-off

Applied after SFT, the preference methods do real work, but the work is
repositioning, not free improvement. From the merged-SFT operating point
(refusal recall 82.85%, over-refusal 61.62% on the seed-1 plain-answer
surface):

- **DPO** is the aggressive mover: over-refusal 61.62% to 13.99%, but refusal
  recall 82.85% to 48.84%. Exact transitions show the price: DPO answers 377
  unknown rows that SFT had correctly refused, and converts 1,113 known
  refusals into answers of which only 95 become correct.
- **KTO** is the conservative mover: over-refusal to 48.22% with recall
  preserved at 75.68%. It answers only 91 previously-refused unknown rows and
  converts 322 known refusals (37 correct).

![[figures/fig-p1-04-sft-warmed-tradeoff.png]]

**Figure 3. SFT-warmed operating points on SelfAware (plain-answer
contract).** DPO moves far toward low over-refusal at heavy recall cost; KTO
stays near the merged-SFT abstention policy. In plain terms: once the model
already knows how to refuse, DPO makes it much more willing to answer (good
on answerable questions, bad on unanswerable ones), while KTO barely moves
it; neither makes it better at telling the two kinds of question apart.

Across the available seeds the pattern is stable (three-seed SFT-DPO means:
recall 52.81%, over-refusal 14.59%, truthfulness 31.18%; two-seed SFT-KTO:
77.18%, 46.88%, 37.55%). This is the published C3 trade-off (Section 3)
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
confidence from the outside, and it is exactly the failure C1 predicts.

![[figures/fig-p1-05-stated-confidence.png]]

**Figure 4. Stated-confidence profile of the SFT-warmed arms
(answer/confidence contract, three seeds).** Confidence coverage is near 100%
for all arms; the differences are behavioral and confidence-level shifts, not
parse failures. In plain terms: every arm reliably produces a confidence
number when asked, and DPO's numbers run much higher than the others; but
judged against whether its answers are actually right (the two rightmost
metric groups, where lower is better), DPO's confidence is the least
trustworthy of the three.

![[figures/fig-p1-06-confidence-alignment.png]]

**Figure 5. Stated confidence by actual outcome.** All three regimens are
highly confident whenever they *answer*, including on wrong answers and on
unknown questions; refusals get near-zero confidence. Confidence tracks the
decision to answer, not the truth of the answer. In plain terms: if a
well-calibrated model existed here, the first bar group would be tall and
the other answer groups short; instead every answer comes out
"about 90% confident" whether it is right, wrong, or unanswerable, so the
stated number tells you what the model *did*, not what it *knows*.

### 6.3 GRPO amplifies the routine to near-ceiling recall

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
| SFT then DPO then GRPO | 41.20 | 93.31 | 65.30 | 52.40 |
| SFT then GRPO then DPO | 41.64 | 93.31 | 63.63 | 51.76 |
| SFT then KTO then GRPO | 40.84 | 92.54 | 66.37 | 53.56 |
| SFT then GRPO then KTO | 40.90 | 89.63 | 60.59 | 49.19 |

![[figures/fig-p1-07-regimen-operating-points.png]]

**Figure 6. GRPO amplifies the abstention routine; stacks stay on its
frontier.** Operating points of all response-confidence-contract arms
(seed 1, exploratory). The preference arms cluster with the SFT baseline;
the GRPO arms and every stack shift up-right: more recall, more over-refusal.
In plain terms: adding GRPO makes the model much better at refusing
unanswerable questions but also more trigger-happy about refusing answerable
ones, and no combination of training stages escapes that bargain; they all
just pick different spots on the same curve.

Three observations. First, GRPO *amplifies* the abstention routine: refusal
recall rises to 93 to 98% (the first reward variant reached 97.87% on an
earlier SFT base), the highest of any arm, and truthfulness is the best in
the study (41.08 to 41.64% for the rebalanced variants and stacks). The
appropriateness reward pays for refusing unknowns and the policy obliges,
hard. Second, the amplification drags over-refusal back up (66 to 76%,
versus 56 to 57% for the preference arms): GRPO undoes precisely the
repositioning that DPO buys. The reward's asymmetric hallucination penalty
makes refusal the safe action, and the policy generalizes the safety margin
onto known questions. Third, **stacking does not escape the trade-off**: all
four stacks land within 1.1 truthfulness points and 6 over-refusal points of
plain SFT-GRPO. Ordering effects exist (GRPO-then-DPO is the best
truthfulness in the study; GRPO-then-KTO gives back the most over-refusal)
but they are marginal adjustments to the GRPO-defined operating point, not
new capabilities. Once GRPO has amplified the routine, a subsequent
preference stage fine-tunes the corner it sits in.

The stage decomposition is now complete: **SFT induces the behavior,
preference optimization repositions it, GRPO amplifies it.** Every objective
selects an operating point on the same recall/over-refusal frontier; nothing
we trained moves the frontier itself.

### 6.4 What the decomposition means for method choice

A naive league table would crown GRPO (best truthfulness) or DPO (best
over-refusal), but the decomposition says the question "which objective wins"
is malformed. The objectives do different jobs: an inducer is mandatory
(without SFT nothing abstains), and the second stage is a policy knob whose
setting depends on the deployment's asymmetric costs. What the field should
compare is not objectives but *regimens*, and regimens should be reported as
operating points with both error rates, never as single scalars. This is the
experiment-level confirmation of the reanalysis lesson from Part I: recall
and over-refusal decouple, and any scalar hides which failure a model makes.

## 7. The confidence channel fails independently of behavior

Behavior is half the construct. The other half is whether the model can
*say how sure it is*, and here the results are sharper and stranger.

### 7.1 RL-trained confidence collapses to a constant

Under the response-confidence contract, the rebalanced-reward GRPO checkpoint
emits confidence with standard deviation 0.013 across 3,369 evaluation rows:
a near-constant ~0.8 regardless of input. Its AUROC against response
appropriateness is 0.520, indistinguishable from a coin flip, and ECE against
appropriateness is 0.403. The confidence token is decorative.

The diagnosis is an incentive analysis, and it generalizes beyond our reward.
The reward's confidence term shaped confidence toward fixed per-cell targets
(high when answering correctly, low when wrong), but the model cannot observe
its own correctness at generation time, and roughly 96% of its answered
known rows are correct; emitting the majority-cell constant is therefore
reward-optimal. Collapse is not a training accident. It is the optimum of
the objective as specified.

### 7.2 A proper scoring rule does not fix it

The obvious repair, and the one the verifiable-RL literature reaches for
(Damani et al., 2025), is to make calibration itself the optimum: replace the
fixed target with a Brier proper score of emitted confidence against realized
appropriateness,

$$r_{\text{conf}} = 1 - (c - a)^2, \qquad c \in [0, 1],\; a \in \{0, 1\},$$

where $c$ is the emitted confidence and $a$ is the realized appropriateness
of the completion. The expected reward $\mathbb{E}[r_{\text{conf}}]$ is
uniquely maximized at $c = p(a = 1 \mid x)$: emitting the true probability
of being appropriate is not merely encouraged but is the optimum. We
implemented exactly this (behavior terms still
dominant; the confidence weight doubled; degenerate 0/1 outputs penalized)
and trained it from the same clean-SFT base.

It does not work. Emitted std rises only to 0.027, AUROC against
appropriateness is 0.522, ECE 0.440. The proper-scoring optimum exists in
theory; gradient ascent from a collapsed-ish initialization does not find it.
The policy stays in the constant-confidence basin, and the behavior terms it
is also earning give it no reason to leave. This is the cleanest negative in
the study: **even a reward for which calibrated confidence is the
mathematical optimum fails to elicit it through RL from this initialization.**

### 7.3 Supervised contrastive confidence calibrates the channel, at behavioral cost

If RL cannot create the signal, supervision can. A contrastive SFT recipe
(training pairs that show the same question answered with high and low
confidence, keyed to whether the answer is right) produces the study's only
genuinely calibrated stated-confidence checkpoint: emitted std 0.309, AUROC
against appropriateness 0.684, AUROC for correct-vs-wrong among answered
knowns 0.789, ECE 0.183, with per-cell mean confidences correctly ordered
(known-correct 0.67 > known-wrong 0.31; unknown-refused 0.58 > unknown-wrong
0.16). A masked variant that supervised only the confidence tokens (not the
answer content) landed in between (std 0.180, AUROC 0.552), indicating the
calibration is learned through the answer-confidence joint distribution, not
the confidence tokens alone.

The cost is behavioral: the contrastive checkpoint over-refuses 79.2% of
known questions and its truthfulness falls to 30.93%. The recipe teaches the
model to doubt, and the doubt leaks from the confidence token into the
refusal decision. Calibration and behavior have now failed in *opposite*
arms: the study's best-behaved checkpoints have collapsed confidence, and its
best-calibrated checkpoint has broken behavior.

### 7.4 RL on the calibrated base retains calibration but does not repair behavior

The natural synthesis is a curriculum: contrastive SFT to create the
calibrated channel, then the proper-scoring GRPO to repair the behavior while
the Brier term protects the calibration. Half of it works. After GRPO on the
contrastive base, calibration is retained essentially intact (AUROC 0.646,
std 0.311, ECE 0.214), the first direct evidence that RL does not
intrinsically destroy a calibrated stated-confidence channel. But the
behavioral repair fails: over-refusal *rises* to 90.76%. Rerunning with the
KL coefficient halved ($\beta = 0.10 \to 0.05$) reproduces the result almost exactly (AUROC 0.648, ECE
0.212, over-refusal 90.59), ruling out reference-model anchoring as the
binding constraint. The decoupling is structural: on this base, within this
budget, the policy gradient treats confidence and action as separate channels
and repairs neither with the other. The checkpoint states calibrated doubt
and then acts on none of it: **calibrated confidence, uncalibrated action.**

![[figures/fig-p1-08-confidence-channel.png]]

**Figure 7. The confidence channel and behavior fail in opposite arms.**
Emitted-confidence spread (left), calibration against response
appropriateness (center), and over-refusal (right) for the five
confidence-channel arms (seed 1, exploratory). The RL arms (red) sit below
the collapse gate and at chance calibration with moderate over-refusal; the
contrastive arms (green) calibrate the channel at behavioral cost; RL on the
contrastive base (purple) keeps the calibration and worsens the behavior.
In plain terms: the RL-trained models say almost the same confidence number
on every question (left panel, flat) and that number carries no information
(center panel, coin-flip level), while the supervised contrastive recipe
produces confidence numbers that actually mean something, at the price of a
model that refuses far too much (right panel); no arm gets both halves
right.

### 7.5 Where this leaves confidence training

Across five reward/recipe variants, no combination produced a checkpoint that
both behaves well and states calibrated confidence. The pattern is
internally consistent: supervision can install a calibrated channel (7.3),
RL preserves an installed channel (7.4), RL cannot install one (7.1, 7.2),
and behavior and confidence move on separate channels throughout (7.4). The
tension Part I identified across disjoint studies (C1 versus C2/C3) is
therefore real within single runs, but its shape is more specific than
"preference training damages calibration": in this regimen the stated
channel is *never coupled to* the epistemic state in the first place unless
supervision explicitly constructs the coupling, and no reward we could
specify constructed it from RL alone.

## 8. The model knows more than any channel says

The confidence-channel results raise the question of whether the signal the
rewards were trying to surface exists at all. It does, and it is not subtle.

On the rebalanced-GRPO checkpoint, a linear probe of layer-35 hidden states
read at the pre-generation position classifies the known/unknown boundary at
AUROC 0.972 on the same evaluation rows where the checkpoint's own emitted
confidence achieves 0.637 against the same label, and a linear readout of the
internal doubt axis is near-calibrated (ECE $\approx 0.004$) while the emitted channel
sits at ECE 0.403. The same geometry recurs on every checkpoint we probed:
behavioral training moved refusal rates by tens of points and moved the
internal boundary signal barely at all.

![[figures/fig-p1-09-knows-vs-says.png]]

**Figure 8. The model knows more than it says.** On the same checkpoint and
the same evaluation rows, a held-out linear probe of layer-35 hidden states
reads the known/unknown boundary at AUROC 0.972 while the model's own emitted
confidence reads it at 0.637. In plain terms: a simple readout attached to
the model's internal activations can tell almost perfectly whether a
question is one the model can answer, while the confidence number the model
itself writes out barely beats a coin flip on the same questions; the
knowledge is in there, the training regimens just never wired it to the
output.

Three readings, in increasing strength, all supported here:

1. **Measurement:** any evaluation of "does the model know what it knows"
   that reads only output channels understates what the model knows, badly.
2. **Mechanism:** the stage decomposition of Section 6 is a decomposition of
   *policy* over a fixed epistemic signal. SFT installs a refusal routine
   gated on the signal; DPO/KTO/GRPO re-gate the routine; none of them
   touches the signal. This is why every arm lands on the same frontier.
3. **Strategy:** the expensive part of epistemic humility (the internal
   knowledge-boundary signal) is already paid for by pretraining. The
   unsolved part is the *readout*: coupling output behavior and stated
   confidence to a signal that is linearly available inside. Training the
   readout by RL failed here (Section 7); reading it directly with a probe
   trivially succeeds. Companion work in this program pursues the readout
   line directly: characterizing which internal signals survive which
   training stages, and whether a training-free probe readout can supply the
   calibrated gate/dial that output training could not.

We flag the boundary conditions: these are single-seed, single-family (4B)
probe results on in-distribution evaluation rows, and Part I's probing
cautions apply (probes can read recall rather than truth-tracking; transfer
must be tested, not assumed). The companion work addresses transfer across
datasets, model sizes, and families explicitly.

## 9. Discussion

**The regimen, not the objective.** The synthesis's method gaps (no
KTO-for-abstention, no three-way, no controlled GRPO comparison) presumed the
interesting question was *which objective*. The experiment's answer is that
objectives are stages with different jobs: induce (SFT only), reposition
(DPO aggressively, KTO conservatively), amplify (GRPO). League tables that
compare them head-to-head as alternatives, including the ones in Part I's
corpus, are comparing a hammer to a chisel by how far each drives the nail.

**The frontier did not move.** Nothing here, including the best stack,
improved discrimination between known and unknown; every intervention chose a
point on the frontier the SFT stage created, and the probe explains why: the
discriminative signal lives in the hidden states and was never the thing
being trained. On the evidence of Sections 7 and 8, output-side training
cannot be expected to move the frontier, because the frontier is set by a
signal the output objectives do not touch.

**The C1/C2 tension, resolved into something sharper.** Part I's unreconciled
tension asked whether preference training buys stated humility by selling
calibrated humility. Measured within single runs, the answer is that there
was nothing to sell: the stated channel starts uncoupled, stays uncoupled
under every RL reward tested (including one whose optimum is calibration),
couples only under explicit contrastive supervision, and once coupled
survives RL. The published tension is real but misattributed: preference
training does not *destroy* verbalized calibration at this scale; the
regimen simply never creates it, and behavioral gains masquerade as
confidence shifts (Section 6.2's DPO signature).

**Deployment reading.** For a practitioner at small scale the actionable
summary is: (i) an SFT inducer stage is mandatory; (ii) choose the second
stage by your cost asymmetry (DPO if over-refusal is expensive, KTO or GRPO
if hallucination is); (iii) do not trust the model's stated confidence under
any of these regimens, and do not expect an RL reward to fix it; (iv) if you
control the weights, a linear probe of the hidden states is a dramatically
better uncertainty signal than anything the model will tell you.

## 10. Limitations

Part I inherits the limitations of the synthesis it condenses: single-pass
extraction (~14% first-pass correction rate, caught by verification),
vote-count synthesis forced by a variance-free literature, English/arXiv
-centric coverage, and claim families articulated after seeing the raw
reports (confirmatory in form, exploratory in origin). The full limitations
section, including the reflexivity discussion, is maintained with the
synthesis materials in the repository.

Part II is a small-model, single-family study: Qwen3-4B with LoRA/QLoRA
recipes, evaluated centrally on SelfAware. The cold-start and SFT-warmed
layers carry three seeds (descriptive t-intervals; SFT-warmed KTO has two
plain-answer seeds); the GRPO, stacking, and confidence-channel layers are
single-seed and exploratory, and are labeled as such wherever they appear.
Negative cold-start DPO/KTO results are claims about this setting and recipe
family, not contradictions of sequential preference results in the
literature. The two output contracts (plain-answer and response-confidence)
are never pooled, but each is an intervention in its own right, and
stated-confidence results are conditional on the contract. GRPO conclusions
are conditional on the reward family tested (appropriateness-dominant with
confidence shaping or Brier scoring); a reward designed around a different
decomposition could behave differently, though the collapse mechanism of
Section 7.1 (unobservable correctness at generation time plus a skewed
correctness base rate) applies to any per-cell-target confidence reward. The
probe results of Section 8 are in-distribution and single-checkpoint-family;
transfer claims are deferred to companion work that tests them directly.

Model-specific known/unknown labels are noisy (Part I measured 42.9 to 51.3%
of "unknown" answers being correct in released artifacts of the lineage we
follow), which flattens all recall/over-refusal numbers toward the middle;
our labels are regenerated per-model but not immune to the same effect.

## 11. Conclusion

The systematic evidence says post-training is where epistemic humility is
made and broken, and it says the field has been comparing training objectives
without ever running them on the same data, the same base, and the same
measurement panel. Running that comparison at 4B yields a stage
decomposition: SFT induces abstention (with a heavy over-refusal tax),
preference optimization repositions the boundary (DPO toward answering, KTO
toward caution), and GRPO amplifies the routine to the best truthfulness and
recall in the study while re-inflating over-refusal. No objective, order, or
stack moves the discrimination frontier itself.

The confidence channel is the sharper result. RL cannot install calibrated
stated confidence even when calibration is the reward's mathematical optimum;
supervision can install it but breaks behavior doing so; RL preserves it once
installed while still failing to repair behavior. Meanwhile a linear probe
reads the knowledge boundary from the same checkpoints at AUROC 0.97. The
model knows; the training regimens differ only in what they make it do about
knowing, and none of them makes it say. We suggest the field's attention,
including ours, belongs on the readout.

## References

Amayuelas, A., Wong, K., Pan, L., Chen, W., & Wang, W. Y. (2023). *Knowledge
of Knowledge: Exploring Known-Unknowns Uncertainty with Large Language
Models*. arXiv:2305.13712.

Bianchi, F., Suzgun, M., Attanasio, G., Röttger, P., Jurafsky, D.,
Hashimoto, T., & Zou, J. (2023). *Safety-Tuned LLaMAs: Lessons From Improving
the Safety of Large Language Models that Follow Instructions*.
arXiv:2309.07875.

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

Gani, A., Meskin, A., Liu, G. K.-M., & Cohan, A. (2026). *Quantifying
Faithful Confidence Expression in Large Reasoning Models*. arXiv:2606.03969.

Gekhman, Z., Yona, G., Aharoni, R., Eyal, M., Feder, A., Reichart, R., &
Herzig, J. (2024). *Does Fine-Tuning LLMs on New Knowledge Encourage
Hallucinations?* arXiv:2405.05904.

GX-Chen, A., Anand, A., Comanici, G., Abbas, Z., Aygün, E., Smalling, D.,
Mourad, S., Precup, D., & Barreto, A. (2026). *Using Reward Uncertainty to
Induce Diverse Behaviour in Reinforcement Learning*. arXiv:2606.03962.

He, G., Cui, P., Chen, J., Hu, W., & Zhu, J. (2023). *Investigating
Uncertainty Calibration of Aligned Language Models under the Multiple-Choice
Setting*. arXiv:2310.11732.

Islah, N., Abbes, I., Rish, I., Chandar, S., & Muller, E. B. (2026). *Failed
Reasoning Traces Tell You What Is Fixable (But Not by Reading Them)*.
arXiv:2606.05145.

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

Leng, J., Huang, C., Zhu, B., & Huang, J. (2024). *Taming Overconfidence in
LLMs: Reward Calibration in RLHF*. arXiv:2410.09724.

Li, S., Yang, C., Wu, T., Shi, C., Zhang, Y., Zhu, X., Cheng, Z., Cai, D.,
Yu, M., et al. (2024). *A Survey on the Honesty of Large Language Models*.
arXiv:2409.18786.

Lin, S., Hilton, J., & Evans, O. (2021). *TruthfulQA: Measuring How Models
Mimic Human Falsehoods*. arXiv:2109.07958.

Lin, S., Hilton, J., & Evans, O. (2022). *Teaching Models to Express Their
Uncertainty in Words*. arXiv:2205.14334.

Lithgow-Serrano, O., Kanjirangat, V., & Antonucci, A. (2025). *Causal
Understanding by LLMs: The Role of Uncertainty*. arXiv:2509.20088.

Liu, S., Li, Z., Liu, X., Zhan, R., Wong, D. F., Chao, L. S., & Zhang, M.
(2024). *Can LLMs Learn Uncertainty on Their Own? Expressing Uncertainty
Effectively in A Self-Training Manner*. In *Proceedings of EMNLP 2024*.
doi:10.18653/v1/2024.emnlp-main.1205.

Mohamadi, M. A., Wang, T., & Li, Z. (2025). *Honesty over Accuracy:
Trustworthy Language Models through Reinforced Hesitation*. arXiv:2511.11500.

OpenAI (2023). *GPT-4 Technical Report*. arXiv:2303.08774.

Ouyang, L., et al. (2022). *Training language models to follow instructions
with human feedback*. arXiv:2203.02155.

Perez, E., Ringer, S., Lukošiūtė, K., Nguyen, K., et al. (2022).
*Discovering Language Model Behaviors with Model-Written Evaluations*.
arXiv:2212.09251.

Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C.
(2023). *Direct Preference Optimization: Your Language Model is Secretly a
Reward Model*. arXiv:2305.18290.

Saeidi, A., Verma, S., Uddin, M. N., & Baral, C. (2024). *Insights into
Alignment: Evaluating DPO and its Variants Across Multiple Tasks*.
arXiv:2404.14723.

Sahoo, S. (2026). *Calibration of Structured Ignorance Certificates for
Diagnosing Unknown Unknowns in Reasoning Models*. arXiv:2606.08571.

Schulman, J., Wolski, F., Dhariwal, P., Radford, A., & Klimov, O. (2017).
*Proximal Policy Optimization Algorithms*. arXiv:1707.06347.

Shao, Z., et al. (2024). *DeepSeekMath: Pushing the Limits of Mathematical
Reasoning in Open Language Models* (GRPO). arXiv:2402.03300.

Stengel-Eskin, E., Hase, P., & Bansal, M. (2024). *LACIE: Listener-Aware
Finetuning for Confidence Calibration in Large Language Models*.
arXiv:2405.21028.

Taparia, A., Senanayake, R., Thopalli, K., & Narayanaswamy, V. (2026). *The
Anatomy of Uncertainty in LLMs*. arXiv:2603.24967.

Tian, K., Mitchell, E., Zhou, A., Sharma, A., Rafailov, R., Yao, H.,
Finn, C., & Manning, C. D. (2023a). *Just Ask for Calibration: Strategies for
Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with
Human Feedback*. arXiv:2305.14975.

Tian, K., Mitchell, E., Yao, H., Manning, C. D., & Finn, C. (2023b).
*Fine-tuning Language Models for Factuality*. arXiv:2311.08401.

Wang, Z., Shi, Z., Zhou, H., Gao, S., Sun, Q., & Li, J. (2025). *Towards
Objective Fine-tuning: How LLMs' Prior Knowledge Causes Potential Poor
Calibration?* arXiv:2505.20903.

Wei, J., Huang, D., Lu, Y., Zhou, D., & Le, Q. V. (2023). *Simple synthetic
data reduces sycophancy in large language models*. arXiv:2308.03958.

Wei, Z., Yang, X., Sun, K., Wang, J., Shao, R., Chen, J., et al. (2025).
*TruthRL: Incentivizing Truthful LLMs via Reinforcement Learning*.
arXiv:2509.25760.

Wen, B., et al. (2024). *Know Your Limits: A Survey of Abstention in Large
Language Models*. arXiv:2407.18418.

Xu, T., Wu, S., Diao, S., Liu, X., Wang, X., Chen, Y., & Gao, J. (2024).
*SaySelf: Teaching LLMs to Express Confidence with Self-Reflective
Rationales*. arXiv:2405.20974.

Yang, Y., Chern, E., Qiu, X., Neubig, G., & Liu, P. (2023). *Alignment for
Honesty*. arXiv:2312.07000.

Ye, F., Yang, M., Pang, J., Wang, L., Wong, D. F., Yilmaz, E., Shi, S., &
Tu, Z. (2024). *Benchmarking LLMs via Uncertainty Quantification*.
arXiv:2401.12794.

Yin, Z., Sun, Q., Guo, Q., Wu, J., Qiu, X., & Huang, X. (2023). *Do Large
Language Models Know What They Don't Know?* arXiv:2305.18153.

Zhai, S., Liang, J., & Kang, D. (2026). *Abstain-R1: Calibrated Abstention
and Post-Refusal Clarification via Verifiable RL*. arXiv:2604.17073.

Zhang, H., Diao, S., Lin, Y., Fung, Y. R., Lian, Q., Wang, X., Chen, Y.,
Ji, H., & Zhang, T. (2023). *R-Tuning: Instructing Large Language Models to
Say "I Don't Know"*. arXiv:2311.09677.

Zhu, C., Xu, B., Wang, Q., Zhang, Y., & Mao, Z. (2023). *On the Calibration
of Large Language Models and Alignment*. arXiv:2311.13240.

---

## Appendix A: Provenance (internal labels to artifacts)

Reader-facing prose above uses no internal amendment labels. For
reproducibility, the mapping from every Part II claim to its governing
protocol document and scored artifact:

| Paper section | Internal label | Protocol / notes | Primary artifacts |
|---|---|---|---|
| 6.1 cold start (3 seeds) | headline matrix, PROTOCOL v0.3 | `experiment/protocol/PROTOCOL.md` | `experiment/phase1/eval/results_selfaware_full_seed{1,2}_all_arms_4b_20260615_2148/`, `..._seed3_..._20260616_0615/`; tables in `experiment/paper/analysis/paper1_results_analysis.md` |
| 6.2 SFT-warmed DPO/KTO | Amendment A | `experiment/protocol/AMENDMENT-A-*.md` | `experiment/phase1/eval/results_amendment_a_selfaware_full_*` |
| 6.2 stated-confidence contract | Amendment B | `experiment/protocol/AMENDMENT-B-*.md` | `experiment/phase1/eval/results_amendment_b_stated_confidence_*` |
| 6.3 GRPO first reward (schema base) | Amendment D | `experiment/protocol/AMENDMENT-D-*.md` | `results_amendment_d_response_confidence_selfaware_schema_sft_grpo_seed1_full_4b/` |
| 6.3 clean-SFT baseline + GRPO v1/v2 | Amendment E | `experiment/protocol/AMENDMENT-E-*.md` | `results_amendment_e_response_confidence_selfaware_clean_sft_{merged,dpo,kto,grpo,grpo_v2}_seed1_*_full_4b/` |
| 6.3 stacks | Amendment F | `experiment/protocol/AMENDMENT-F-*.md` | `results_amendment_f_response_confidence_selfaware_clean_sft_{dpo_grpo,grpo_dpo,grpo_kto,kto_grpo}_seed1_full_4b/` |
| 7.1 confidence collapse (GRPO v2) | Amendment J diagnostics / session 0026 | `experiment/notes/grpo-v3-proper-scoring-confidence.md` | `experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json` |
| 7.2 proper-scoring GRPO (B0) | Amendment J (GRPO-v3) | `experiment/notes/grpo-v3-proper-scoring-confidence.md`; reward `experiment/phase1/grpo/humility_reward_v3.py` | `calibration_gap_clean_sft_grpo_v3_seed1.json` |
| 7.3 contrastive confidence SFT | Amendment K | `experiment/protocol/AMENDMENT-K-contrastive-sft-behavior-conditional-confidence.md` | `calibration_gap_contrastive_sft_seed1.json`, `calibration_gap_contrastive_masked_sft_seed1.json` |
| 7.4 GRPO on contrastive base; KL sweep | Amendment N (incl. beta 0.05 arm) | `experiment/protocol/AMENDMENT-N-grpo-v3-on-contrastive-sft-base.md` (results tables §7) | result tables embedded in the amendment document; run records under `experiment/phase1/run_records/` |
| 8 probe vs emitted channel | probe program (Amendments L/M lineage; caution-vs-doubt note) | `experiment/notes/caution-vs-doubt-knowledge-gate.md` | `calibration_gap_clean_sft_grpo_v2_seed1.json` (`B_internal_vs_emitted`: internal AUROC 0.972 vs emitted 0.637) |
| grouped behavioral inventory | all of the above | | `experiment/phase1/eval/analysis/selfaware_full_run_comparison_grouped.csv` |

Governance notes: the three-seed cold-start block is the pre-registered
headline surface (PROTOCOL v0.3, signed 2026-06-10); Amendments A/B are signed
prospective extensions; Amendments D/E/F/J/K/N are exploratory single-seed
evidence cells with pre-stated predictions and falsifiers, reported here as
exploratory and never pooled with the headline block. The companion-work
references in Sections 8 and 9 correspond to the probe/readout program
(Papers 2 and 3 of this research line), maintained in the same repository.

## Appendix B: Meta-analysis archive pointer

The full systematic synthesis absorbed as Part I (search protocol, PRISMA-style
flow accounting, extraction schema, per-family sensitivity analyses, the
FActScore and reward-calibration data audits, the L1-clustering analysis, the
full six-gap catalog, and the complete bibliography) is archived at
`meta-analysis/paper/draft-v0.md` with evidence tables under
`meta-analysis/evidence/` and analysis scripts under `meta-analysis/analysis/`.
Part I of this paper supersedes it as the reader-facing text; the archive
remains the provenance source of record for every Part I number.
