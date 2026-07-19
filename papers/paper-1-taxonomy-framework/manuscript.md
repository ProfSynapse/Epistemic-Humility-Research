---
title: "The Depths of Ignorance: A Taxonomy, Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in Language Models"
author: "Joseph Rosenbaum (Synaptic Labs)"
status: draft-v0 (created 2026-07-01 by splitting papers/paper-2-training-regimen/manuscript.md Part I back out as the standalone framing paper)
date: 2026-07-01
repository: https://github.com/ProfSynapse/Epistemic-Humility-Research
target: arXiv (cs.CL / cs.AI)
evidence_base: meta-analysis/evidence/effects.csv (78 rows, 39 studies), meta-analysis/evidence/idk-method-reanalysis.csv
notes: >
  Numbers discipline: every quantitative claim traces to
  meta-analysis/evidence/effects.csv (78 rows, 39 studies) or the reanalysis
  scripts under meta-analysis/analysis/. The full synthesis apparatus (search
  protocol, PRISMA-style flow accounting, extraction schema, per-family
  sensitivity analyses, data audits, complete bibliography) is the source of
  record at meta-analysis/paper/draft-v0.md; this paper is the reader-facing
  text built on it, extended with the taxonomy and the theoretical framework.
  Math is set in LaTeX (inline $...$, pandoc-compatible). Citations are
  author-year; the References section is one-to-one with in-text citations.
---

# The Depths of Ignorance: A Taxonomy, Systematic Evidence Synthesis, and Research Agenda for Epistemic Humility in Language Models

Joseph Rosenbaum
Synaptic Labs

*Draft v0. Not for distribution.*

> *"It is likely that neither of us knows anything worthwhile, but he thinks he knows something when he does not, whereas I, as I do not know, do not think I know either."*
>
> Plato, *Apology* 21d

## Abstract

Language models acquire most of their epistemic character (how confident they
sound, when they refuse, how readily they capitulate) not from pretraining but
from post-training. We organize the evidence for that claim into a single
framework. First, a taxonomy: four *depths* at which a model can express
ignorance (scalar confidence, structured gap-naming, distributional failure
signatures, and uncertainty over the objective itself), crossed with a
*coherence* axis asking whether the model's stated, token-level, and
hidden-state signals agree. Second, a systematic synthesis: 78 quantitative
effects extracted from 39 studies (2021–2026) across the calibration,
abstention, hallucination, sycophancy, and method-comparison literatures,
synthesized by vote counting and exact binomial sign tests, with independent
reanalyses of three studies' released artifacts. Five claim families emerge:
instruction tuning and RLHF degrade token-level calibration (relative ECE
increases of 177% and 957% in the two clean head-to-heads); preference
optimization beats SFT on abstention quality but by an order of magnitude less
than the calibration damage; the improvement is a trade along a
recall/over-refusal frontier rather than better discrimination; scale alone
does not produce humility; and targeted interventions reliably do ($p = 0.001$,
median |effect| 40%). The families combine into an unreconciled tension, one
that no study in the corpus measures within a single run: the methods that
best teach a model to *say* "I don't know" are the documented destroyers of
the signal that *knows*. We formalize this as a policy-versus-signal framework
with three testable propositions, verify six specific experiments the field
has not run, and set the agenda that the empirical papers of this program
execute.

## 1. Introduction

A language model that answers fluently when it knows and abstains gracefully
when it does not would be, in a precise sense, aligned: its expressed epistemic
state would track its actual one. The models we deploy are not like this. They
assert falsehoods with high verbal confidence, refuse questions they could
answer, and abandon correct answers under trivial social pressure. A recent
theoretical account names the failure mode we adopt as framing: the **polite
liar** (DeVilling, 2025), a system that structurally misrepresents its own
epistemic state, not out of anything resembling malice, but because its
training rewarded the appearance of knowledge over the admission of ignorance
(cf. Kalai et al., 2025, who derive the same incentive from binary-graded
evaluation).

The contention of this paper is that these failures are primarily facts about
*training*, specifically post-training. Three strands of published evidence
converge on training as the causal locus.

**First, pretrained models already know how likely they are to be right;
post-training breaks the readout.** The GPT-4 technical report measures an
expected calibration error (ECE) of 0.007 for the pretrained base model on a
subset of MMLU; after reinforcement learning from human feedback (RLHF), ECE on
the same subset rises tenfold to 0.074 (OpenAI, 2023). Kadavath et al. (2022)
identify the mechanism (RLHF concentrates probability mass on high-reward
outputs, sharpening every distribution whether or not the model's knowledge
warrants it) and show that a single temperature adjustment largely restores
calibration. That repairability is itself evidence: the signal survives in the
weights; it is merely expressed too confidently.

**Second, the damage is not specific to reinforcement learning.** A controlled
comparison on the same base model finds plain instruction tuning nearly
tripling ECE (0.13 to 0.36) while simultaneously *reducing* predictive entropy
(1.32 to 0.92) (Lithgow-Serrano et al., 2025): the tuned model becomes more
decisive and less reliable about its own reliability at the same time.

**Third, the converse also holds: what training breaks, training can
deliberately improve.** Refusal-aware tuning, factuality-aware DPO, calibrated
reward models, and listener-aware preference pairs consistently improve
humility metrics, often by large margins (Section 4, family C5).

What has been missing is a synthesis that treats the calibration, abstention,
hallucination, sycophancy, and method-comparison literatures as one evidence
base about a single underlying construct, together with a conceptual frame
precise enough to say what that construct *is*, which of its parts training
touches, and which experiments would decide between the readings the evidence
leaves open. This paper supplies both.

Contributions:

1. **A taxonomy of expressed ignorance** (four depths crossed with a
   coherence/faithfulness axis) that locates nearly all existing training
   work at the shallowest depth and exposes coherence as the unmeasured
   dimension (Section 2).
2. **A unified extraction of 78 quantitative effects from 39 studies** into a
   single schema, synthesized by vote counting and exact binomial sign tests,
   with independent reanalyses of three studies' released artifacts
   (Sections 3–4).
3. **Five claim families** with explicit support/contradict accounting, and
   the unifying tension they jointly produce: stated humility and calibrated
   humility are trained by the same methods in opposite directions, and no
   study measures both after the same run (Section 4).
4. **A verified gap analysis**: six specific, falsifiable claims about
   experiments absent from the literature as of June 2026 (Section 5).
5. **A theoretical framework** (expression policy over a fixed epistemic
   signal) stated as three testable propositions, with the research agenda
   they generate. The empirical papers of this program execute that agenda
   (Section 6).

## 2. The Depths of Ignorance: a taxonomy

We use *epistemic humility* as an umbrella for behaviors and properties that
make a model's expressed epistemic state track its actual reliability:
token-probability and verbalized-confidence calibration; appropriate abstention
("I don't know") with low over-refusal; resistance to hallucination on
unfamiliar inputs; and resistance to sycophantic capitulation. *Post-training*
covers everything after pretraining: supervised/instruction fine-tuning (SFT);
preference optimization, including RLHF with PPO (Ouyang et al., 2022;
Schulman et al., 2017), direct preference optimization (DPO) (Rafailov et al.,
2023), and Kahneman-Tversky optimization (KTO) (Ethayarajh et al., 2024); and
RL with programmable rewards, including group relative policy optimization
(GRPO) (Shao et al., 2024).

A synthesis needs an organizing taxonomy, and the natural one is not a method
taxonomy (existing surveys of abstention (Wen et al., 2024) and honesty
(Li et al., 2024) provide those) but a *depth* taxonomy: a hierarchy of what,
exactly, is being formalized when a model "expresses ignorance."

- **L1: Confidence/calibration.** "How sure am I?" as a scalar: token
  probabilities and verbalized percentages (Lin et al., 2022; Tian et al.,
  2023a), scored by ECE, Brier score, and AUROC. This is the level of nearly
  all training work synthesized below.
- **L2: Structured ignorance.** "What am I missing?" as structure: gap-naming,
  knowledge-intersection identification, retrieval proposals (Sahoo, 2026;
  Taparia et al., 2026).
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
what distinguishes *possessed* humility from *performed* humility: Plato's
distinction, operationalized. The *Meno* closes on exactly this point: true
opinions, Socrates says, are like the statues of Daedalus, which run away
unless tethered by working out the reason (*Meno* 97d–98a; Plato, trans.
Grube, 1997). A humility behavior not anchored to the model's internal state
is an untethered statue: the right answer today, a runaway under
distribution shift. The mapping exercise below shows this axis is almost
entirely unmeasured in the training literature; measuring it is the first
item of the agenda in Section 6, and the program's own companion diagnosis
paper (paper 3, [*Knows but Doesn't
Say*](../paper-3-knows-but-doesnt-say/manuscript.md)) now supplies exactly
that measurement.

## 3. Corpus and synthesis method

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
`meta-analysis/evidence/`), which is the source of record for every number in
this paper.

Three studies' released artifacts were additionally *reanalyzed* rather than
merely extracted: the released per-output files of the model-specific IDK
tournament of Cheng et al. (2024) ($n = 11{,}313$ outputs), the released
results of AbstentionBench (Kirichenko et al., 2025), and the alignment-method
comparison of Saeidi et al. (2024). The reanalyses matter because they expose
exactly the quantities the papers' aggregate metrics obscure, and two of the
five claim families below rest partly on them.

## 4. Five claim families

**C1: Instruction tuning and RLHF degrade token-probability calibration.**
Two extracted head-to-head rows support, none contradict; magnitudes 176.9%
and 957.1% relative. GPT-4's ECE rises 0.007 to 0.074 after RLHF on the same
MMLU subset (OpenAI, 2023); the same-base Pythia-7B to Dolly-v2-7B
comparison rises 0.13 to 0.36 while predictive entropy falls
(Lithgow-Serrano et al., 2025). Three further studies corroborate the
direction without extractable pairs (Zhu et al., 2023; He et al., 2023;
Ye et al., 2024). The mechanism-level finding that matters most for training
design: what does the damage is the relationship between the tuning data and
*this model's* knowledge. Fine-tuning on facts the model does not know
causally drives hallucination (Gekhman et al., 2024); data aligned with prior
knowledge induces overconfidence, while genuinely novel data improves
calibration (Wang et al., 2025). Fitting unknowns teaches hallucination, and
fitting knowns teaches overconfidence, which is why every successful
abstention method builds *model-specific* training splits.

**C2: Preference-based methods beat SFT on abstention/truthfulness quality.**
Every extracted preference-over-SFT comparison is positive except one (the IPO
variant underperforms by 5.4% (Saeidi et al., 2024)). The anchor is the only
within-paper tournament on model-specific IDK data: on Llama-2-7b-chat
truthful rate, Idk-Prompting 66.93 < Idk-SFT 74.75 < Idk-HIR 75.91 < Idk-PPO
76.47 < Idk-DPO 77.89 < Idk-BoN 78.96 (Cheng et al., 2024). Our reanalysis of
AbstentionBench's released results adds an independent lineage: on the Tulu-3
ladder, DPO beats SFT on abstention recall by a paired median of +0.08 at 8B
($p = 5.5 \times 10^{-4}$) (Kirichenko et al., 2025; our reanalysis). KTO
beats SFT on TruthfulQA by +2.2 points from an SFT'd base and +9.3 from the
pretrained base (Saeidi et al., 2024). The median magnitude across the family
(5.0%) is an order of magnitude smaller than the C1 damage.

**C3: Preference optimization reduces SFT-induced over-refusal.** Our
output-level reanalysis of Cheng et al.'s (2024) released Llama-2-7b-chat
outputs ($n = 11{,}313$) supplies the exact numbers the paper's aggregate
"truthful rate" obscures:

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
safety examples induce exaggerated refusal of benign prompts; Bianchi et al.,
2023). Two further observations from the reanalyses discipline everything
downstream: single-scalar abstention metrics hide which failure a model makes
(recall and precision are decoupled across 20 models, Spearman
$\rho = -0.05$), and model-specific known/unknown labels are themselves noisy
(42.9 to 51.3% of answers on unknown-labeled questions were in fact correct).

**C4: Scale alone does not produce epistemic humility.** Four studies support,
none contradict. The best GPT-3 model is truthful on 58% of TruthfulQA against
a 94% human baseline, with inverse scaling within families (Lin et al., 2021);
GPT-4 detects unanswerable questions at $F_1 = 75.47$ versus a human 84.93
(Yin et al., 2023; see also the known-unknowns probing of Amayuelas et al.,
2023); sycophancy grows with scale (Perez et al., 2022; Wei et al., 2023); and
in our reanalysis of AbstentionBench, 50x more parameters moves Llama 3.1
Instruct median abstention recall by 0.02 while a single DPO stage moves it
0.08. Waiting for the next model generation does not solve this problem;
training design does or does not.

**C5: Targeted training interventions improve humility metrics.** Eleven
studies supporting, none contradicting, the corpus's only conventionally
significant sign test ($p = 0.001$); median |relative change| 40.1%. The
supporting set spans intervention types (refusal-aware SFT (Zhang et al.,
2023), honesty-targeted SFT (Yang et al., 2023), factuality DPO
(Tian et al., 2023b), listener-aware DPO (Stengel-Eskin et al., 2024),
calibrated-reward PPO (Leng et al., 2024), self-reflective confidence training
(Xu et al., 2024), self-trained uncertainty expression (Liu et al., 2024), and
others), which is what makes the signal credible; what it is *not* is
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
humility.

## 5. What the field has not run

The gap analysis was run the opposite way from the rest of the synthesis:
instead of searching for what the literature contains, it searched for studies
that *should* exist and do not. Each gap is a falsifiable claim about absence
as of June 2026. Six were verified:

- **Gap 1: KTO has never been applied to abstention, honesty, or calibration
  training** (high confidence; zero hits across targeted searches, and the KTO
  paper's own application list contains none). The gap matters because KTO's
  structure fits the problem unusually well: it consumes exactly the unpaired
  binary desirable/undesirable labels a known/unknown split naturally
  produces, and its prospect-theoretic loss weights losses asymmetrically, as
  this domain's costs are (a confident hallucination typically does more
  damage than an unnecessary abstention).
- **Gap 2: No SFT vs. DPO vs. KTO three-way comparison exists on the same
  abstention dataset** (high confidence). Cheng et al. (2024) compare five
  methods but not KTO; the one SFT/DPO/KTO comparison that exists uses generic
  benchmarks, not abstention training. Every component of the experiment
  exists in print; no study assembles them.
- **Gap 3: GRPO-for-abstention exists, but no controlled comparison against
  SFT/DPO/KTO does, and none looks beneath behavior.** The verifiable-RL
  cluster now includes TruthRL's ternary reward (Wei et al., 2025), Abstain-R1
  (Zhai et al., 2026), reinforced hesitation (Mohamadi et al., 2025), and the
  correctness-minus-Brier reward of RLCR (Damani et al., 2025), but none is
  benchmarked against the preference families on shared data, and none
  measures internal representations. One caution from this literature binds
  any such design: probes placed *inside* RL reward loops get gamed
  (Cundy & Gleave, 2025), so representation probes must remain held-out
  evaluation, never reward.
- **Gap 4: No probe-transfer study tests whether humility training changes
  representations or only behavior.** The calibration-damage literature (C1)
  and the linear-probing literature both exist; no study fits probes before
  and after abstention training on the same checkpoints to ask what the
  training actually moved.
- **Gap 5: No IDK-fraction dose-response curve.** Every model-specific
  abstention method fixes one known/unknown mixture by fiat; the sensitivity
  of the recall/over-refusal operating point to that mixture is unmeasured.
- **Gap 6: Small-model and OOD coverage is thin.** The abstention-training
  literature concentrates on 7B-and-larger chat models evaluated
  in-distribution; whether the methods transfer down-scale and out of
  distribution is asserted rather than measured.

## 6. A framework, three propositions, and the agenda

The five families and six gaps compress into a single conceptual picture.
Distinguish two objects inside a trained model:

- the **epistemic signal**: whatever function of the input and the model's
  internal state actually tracks "can this model answer this correctly?"
  (the thing calibration is calibration *of*);
- the **expression policy**: the learned mapping from that signal (and
  everything else) to observable behavior, that is, answering, refusing,
  hedging, and the confidence the model verbalizes.

We use "epistemic signal" here as a working simplification; the program's own
readout experiment finds it is not one object but at least two dissociable
signals, an answerability axis and a per-answer correctness axis, separable
enough that fusing them costs correctness ranking (paper 4, [*It's What's on
the Inside That Counts*](../paper-4-two-signal-readout/manuscript.md)).

The evidence reads naturally as claims about which object each intervention
touches. C1's mechanism (Kadavath et al., 2022) is explicit that RLHF damages
the *readout* while the signal survives (temperature repair). C2/C3's trades
move operating points without improving discrimination: policy movement on a
fixed signal. C4 says the signal's mere growth with scale does not deliver the
policy. C5's wins are policy installations. The coherence axis of Section 2 is
exactly the question of how well the policy's outputs track the signal.

We state the picture as three propositions, each falsifiable:

- **P1 (locus).** A model's epistemic character (its calibration, abstention,
  and capitulation behavior) is predominantly set by post-training, not by
  scale or pretraining. *(Supported directly by C1, C4, C5; a base-model
  falsification test is to measure the signal before any post-training.)*
- **P2 (policy, not signal).** Post-training objectives act on the expression
  policy and leave the underlying epistemic signal approximately fixed:
  different objectives select different operating points on a frontier the
  signal defines, and no output-side objective moves the frontier itself.
  *(Predicted by C2/C3's trade structure; falsified by any training objective
  that improves known/unknown discrimination itself.)*
- **P3 (readout).** If P2 holds, the binding constraint on epistemic humility
  is not training pressure but *readout*: the internal signal is present and
  linearly accessible, and coupling behavior and stated confidence to it,
  rather than training the output channel harder, is the productive
  engineering target. *(Motivated by the temperature-repair result and the
  probing literature; falsified if the internal signal proves weak, incoherent
  across estimators (Gani et al., 2026), or non-transferable. Non-transferability
  is now partially tested: on a methodologically matched lineage, the
  named known-unknown direction does not fire at all on the world-known
  (confidently-wrong) error class (primary transfer VOID, out of domain; the
  population's projections reverse sign), and a direction refit natively on
  that population shows only a sub-floor, behaviorally inert response to
  in-context evidence, a population-bound result that constrains P3's scope
  without falsifying it
  (`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`,
  Outcome).)*

The propositions generate a concrete agenda, ordered by the gaps:

1. **Run the missing comparison** (Gaps 1–3): every major post-training
   objective on the same base model and the same model-specific abstention
   data, measuring behavior, stated confidence, and hidden-state signal after
   the same runs. This is the direct within-run test of the C1-versus-C2/C3
   tension and of P2, and it is the program's training-regimen experiment,
   [*Teaching Small Language Models to Say I Don't Know: A Controlled
   Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention
   Data*](../paper-2-training-regimen/manuscript.md).
2. **Measure the coherence axis directly** (Gap 4): quantify the gap between
   internal and stated confidence on identical rows, and test whether any
   training regimen closes it. This is the program's diagnosis experiment,
   [*Knows but Doesn't Say: A Training-Resistant Gap Between Internal and
   Stated Confidence in a Small Language
   Model*](../paper-3-knows-but-doesnt-say/manuscript.md).
3. **Test the readout constructively** (P3): if the signal is present and the
   channel is the problem, a training-free readout should recover calibrated
   gating and trust from frozen models. The program's readout experiment,
   [*It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for
   Epistemic Humility in Small Language
   Models*](../paper-4-two-signal-readout/manuscript.md), tests its transfer across
   datasets, scales, and families. Causal writability was tested by the program's
   actuation experiment, [*Readable Is Not Writable: Channel, Gate, and Workspace
   Constraints on Actuating Known-Unknown State in Small Language
   Models*](../paper-5-actuation/manuscript.md); the answer is operating-point-dependent,
   not universal: at an overdrive dose the gate is the sole source of selectivity, while
   at mid-band doses the write is already content-selective and the gate's role reduces
   to a modest increment plus cost governance.
4. **Fill the remaining measurement gaps** (Gaps 5–6): dose-response over the
   IDK fraction, small-model coverage, and OOD stress tests.

The framework also disciplines interpretation in advance: if the missing
comparison finds that objectives merely relocate operating points, league
tables comparing "which objective wins" are category errors: the right
comparanda are *regimens* (inducer + repositioner + amplifier stages), and the
right report is an operating point with both error rates, never a single
scalar.

## 7. Limitations

This synthesis inherits the limitations of its corpus. Extraction was
single-pass with a ~14% first-pass correction rate caught by verification;
vote-count synthesis was forced by a variance-free literature (zero error bars
in any retrieved material from the twelve calibration studies in our primary
searches); coverage is English- and arXiv-centric; and the claim families were
articulated after seeing the raw reports (confirmatory in form, exploratory in
origin). The reanalyses cover three studies' artifacts, not the corpus. The
propositions of Section 6 are a reading of observational syntheses, not
established results: P2 and P3 in particular are stated to be tested, and the
program's empirical papers treat them as hypotheses with pre-registered
falsifiers, not as conclusions. The full limitations discussion, including
reflexivity (this synthesis was AI-assisted, with human verification of every
headline row), is maintained with the synthesis materials in the repository.

## 8. Conclusion

The published evidence, read as one corpus, says that epistemic humility is
made and broken in post-training: calibration is damaged by the same stages
that install useful behavior, targeted interventions work but are evaluated a
slice at a time, scale does not save us, and the field has never measured
whether its best abstention-training methods pay for stated humility with
calibrated humility, because no study measures both in the same run. The
Depths of Ignorance taxonomy locates nearly all of this work at the
shallowest depth, with the coherence between what a model knows and what it
says almost entirely unmeasured. We propose treating the trained model as an
expression policy over a fixed epistemic signal, offer three falsifiable
propositions, and derive the experiments that decide them. The companion
papers of this program run those experiments.

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

Plato. *Apology* (21d) and *Meno* (80a–86c, 97d–98a). Translations by
G. M. A. Grube, in *Plato: Complete Works*, ed. J. M. Cooper, Hackett, 1997.

Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., & Finn, C.
(2023). *Direct Preference Optimization: Your Language Model is Secretly a
Reward Model*. arXiv:2305.18290.

Rosenbaum, J. (2026). *Knows but Doesn't Say: A Training-Resistant Gap
Between Internal and Stated Confidence in a Small Language Model*. Companion
draft, this repository:
[papers/paper-3-knows-but-doesnt-say/manuscript.md](../paper-3-knows-but-doesnt-say/manuscript.md).

Rosenbaum, J. (2026). *Teaching Small Language Models to Say I Don't Know: A
Controlled Comparison of SFT, DPO, KTO, and GRPO on Model-Specific Abstention
Data*. Companion draft, this repository:
[papers/paper-2-training-regimen/manuscript.md](../paper-2-training-regimen/manuscript.md).

Rosenbaum, J. (2026). *It's What's on the Inside That Counts: A Training-Free
Two-Signal Readout for Epistemic Humility in Small Language Models*.
Companion draft, this repository:
[papers/paper-4-two-signal-readout/manuscript.md](../paper-4-two-signal-readout/manuscript.md).

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

## Appendix A: Source-of-record pointer

The full systematic synthesis this paper condenses and extends (search
protocol, PRISMA-style flow accounting, extraction schema, per-family
sensitivity analyses, the FActScore and reward-calibration data audits, the
L1-clustering analysis, and the complete bibliography) is maintained at
`meta-analysis/paper/draft-v0.md`, with evidence tables under
`meta-analysis/evidence/` and analysis scripts under
`meta-analysis/analysis/`. That document is the provenance source of record
for every number in Sections 3–5.
