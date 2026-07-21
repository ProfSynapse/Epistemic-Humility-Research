# It's What's on the Inside That Counts: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models

*Draft v0. Standalone contribution; it cites the companion diagnosis paper, [*Knows but
Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small
Language Model*](../paper-3-knows-but-doesnt-say/manuscript.md), for the representation-vs-
verbalization gap it builds on. All primary numbers come from single greedy decodes
(pool shuffle and decode seed 20260630) unless a replication is named; the sampled-decode
seed-robustness replication (§4.10) used seeds 20260701 through 20260703. Provenance for
every figure is in Appendix A.*

---

## Abstract

Small language models routinely answer questions they cannot answer, and state a flat,
uninformative confidence when they do. A companion study shows this is not an ignorance
problem: the model holds a well-calibrated *internal* estimate of what it knows, yet the
confidence it *emits* is nearly constant and chance-level (it knows, but does not say),
and that gap survives supervised fine-tuning, preference optimization (DPO/KTO), and
reinforcement learning (GRPO). If training does not close the gap, the signal must be
read out rather than trained in.

We show it can be. Two orthogonal, linearly-decodable axes are already present in a frozen
instruction-tuned base and compose into a deployable trust pipeline. The two axes yield
three readouts: a gate, a dial, and the dial's veto on confident confabulation; the first
two are one robustness class, the veto is another. An **answerability
gate**, read at the final prompt token *before* generation, separates answerable from
unanswerable questions at AUROC ≈ 0.997. A **correctness dial**, read at the final answer
token *after* generation, ranks whether the specific answer just produced is correct
(AUROC 0.834), and reads best *after* the answer rather than before it (+0.065, CI
excludes zero). The dial also **vetoes confident confabulation**: hallucinated answers to
unanswerable questions receive the lowest trust of any group. Fusing the two axes into one
scalar costs correctness ranking (Δ −0.014, CI excludes 0), so we deploy them as two
sequential stages.

Four findings make this a mechanism rather than a curiosity. (1) It is training-free:
the whole pipeline reads off the raw instruction-tuned base with no adapter and no
abstention training of ours (veto 0.754 untrained); our training does not create the
signal, and whether it even *sharpens* the veto is unresolved: under corrected
hallucination labels the confabulation dial-mean reads 0.271 on the base and 0.183 (Set A)
/ 0.274 (Set B) after training, an unpowered comparison at n=12/8 that shows no fall under
Set B (the originally reported fall to 0.018 was a detector artifact, corrected
2026-07-18, §4.6). (2) It is size-robust: the readout passes on every Qwen3
scale from 1.7B to 14B. (3) It replicates across model families. On four independent
families (Qwen, Llama, Mistral, Gemma) the gate and dial pass on all four: the gate
saturated at 0.997 to 0.998, the dial between 0.82 and 0.86. The veto is the readout that
wobbles. Under a single greedy decode it failed outright on Llama-3.2 (0.633); a
pre-registered three-seed sampled-decoding replication showed the greedy misses were
decode artifacts, and under sampling the veto passes on all four families (family means
0.68 to 0.75). The variance is real: across-seed spread on the veto reaches 0.15 where
the dial's stays under 0.04, and individual cells still dip below the bar. We report
this as a co-headline: **a small LM's
sense of "can I answer this?" and "is this answer right?" is a universal, readable property
of the representation; its ability to distrust its own confident fabrications is present
across families but decode- and seed-sensitive, and it must be reported with seed spread
and validated per model.** A pre-registered construct decomposition qualifies what that
veto reads: controlled for answer length and question answerability, its content-trust
core is AUROC 0.737 (CI [0.650, 0.815]); the larger headline contrasts also carry the
question's answerability into the post-answer read. We give the descriptive mechanism
(the correct-vs-hallucination gap in the dial distribution) that predicts where it is
strong. (4) It predates
post-training entirely: a pre-registered contrast on four *pre-instruction* bases
(Qwen3.5, Gemma, Llama-3.2, Olmo-3) finds every readout already present (gate 0.997+, dial
0.82–0.87, veto passing on all four at 0.67–0.87), and the one clean base→instruct pair
read under a single pipeline moves the veto *down* (0.803 → 0.731): generic vendor
post-training does not create the signal and does not sharpen it; only targeted abstention
training did. Descriptively, all three readouts are present as far back as GPT-2-XL (2019).

---

## 1. Introduction

An epistemically humble model does two things a fluent one does not: it declines questions
it cannot answer, and it attaches an honest confidence to the answers it does give. Small
open models are good at neither. They confabulate plausible answers to unanswerable
questions (Slobodkin et al., 2023; Kirichenko et al., 2025), and the confidence they
verbalize is nearly flat regardless of whether they are right (Xiong et al., 2023;
Shrivastava et al., 2023).

Try this as a thought experiment. You ask a small open model who won a chess tournament
that never took place. It answers fluently, names a winner, and when you ask how
confident it is, it gives you a number in the mid-fifties. You then ask it the capital of
France, and it gives you nearly the same number. The confidence on the outside is
useless. The question this paper answers is whether there is a number on the inside
worth reading instead.

The natural first hypothesis is that this is an *ignorance* problem (the model does not
represent its own uncertainty) and the natural fix is *training*: fine-tune it to abstain
(Zhang et al., 2023; Yang et al., 2023; Cheng et al., 2024), or optimize a
preference/reward signal toward calibrated confidence (Lin et al., 2022; Liu et al., 2026). Our companion
diagnosis, [*Knows but Doesn't Say*](../paper-3-knows-but-doesnt-say/manuscript.md), tests and
rejects the first hypothesis and finds the second insufficient. A linear probe on the base
model's internal activations separates answerable from unanswerable questions almost
perfectly (AUROC ≈ 0.997) with a well-calibrated readout (ECE ≈ 0.004), while the model's
*verbalized* confidence stays near 0.52–0.56 across the board. The internal estimate is
there; the emitted one is not a faithful copy of it. And the gap is *training-resistant*:
it survives supervised fine-tuning, DPO (Rafailov et al., 2023), KTO (Ethayarajh et al.,
2024), and three generations of GRPO (Shao et al., 2024). Two opposite
training pressures fail on the same channel: reinforcement learning preserves stated
calibration but never installs knowledge-conditioned *action*, while distilling the
internal axis into the emitted token installs the action but collapses the confidence
number onto it. The bottleneck is not knowledge; it is the single confidence token that a
language-model head emits under next-token cross-entropy.

That diagnosis has a direct engineering consequence, and it is the subject of this paper.
**If the signal cannot be reliably trained into the emitted token, read it out of the
representation instead.** We show that a deployable trust mechanism can be built entirely
from linear readouts of a frozen model. The paper's vocabulary, used consistently
throughout: **two axes** (answerability, correctness), which yield **three readouts** (a
gate, a dial, and the dial's veto on confident confabulation), which fall into **two
robustness classes** (the gate and dial are family-general; the veto is decode-, seed-,
and model-sensitive). Three contributions over the diagnosis:

1. A second axis. Answerability ("*can* this be answered?") is not the same as
   correctness ("is *this answer* right?"). We show correctness is *also* linearly
   readable, at a different token position (after the answer, not before it), and that the
   two axes are orthogonal: separable enough that combining them into one number costs
   correctness ranking. This yields a two-stage pipeline: a **gate** that abstains on
   unanswerable questions, and a **dial** that surfaces a trust number on what is answered.

2. The dial's veto on confident confabulation, as its own readout. The same
   correctness dial, applied to confident answers on unanswerable questions, pushes them
   to the bottom of the trust ranking. This is not a third axis: in every cross-model
   cell the veto is the identical dial probe read against a third contrast. It is a third
   *readout*, and it earns separate billing because it is its own robustness class:
   decode- and seed-sensitive, model-dependent, non-monotonic in scale, and a blend of a
   content core (about 0.74) with carried answerability (§4.4). The gate/dial-versus-veto
   split is the paper's central finding; we treat it as a co-headline, not a footnote,
   and give the descriptive quantity that predicts where the veto is strong.

3. A generality claim. The companion diagnosis established its gap on a single model
   from a single family; this paper breaks that boundary. The readout is training-free
   (it reads off the raw instruction-tuned base), size-robust (1.7B–14B), replicates
   across four model families, and predates post-training entirely. The two axes
   generalize everywhere we looked; the veto is the readout that must be validated
   per model.

Each contribution carried a pre-registered falsifier (stated with the gates in §3);
none fired. The one registered gate that missed (calibration, by 0.001) shapes how we
scope the dial.

The framing throughout is *readout, not training*. Our training does not create the trust
signal; it sharpens one part of it (the veto) and installs behavioral abstention. The
implication for practitioners is concrete: a useful, thresholdable trust number for a small
LM is available *today*, from a model you already have, with a cheap linear probe, and no
fine-tuning run is required.

---

## 2. Related work

#### Verbalized confidence

Can a model simply say how sure it is? A line
of work asks exactly that, eliciting confidence in words or tokens and measuring the
result. The miscalibration is well documented: vanilla verbalized confidence reaches ECE
of roughly 0.38 to 0.52 for GPT-3-class and open models (Xiong et al., 2023), and the
emitted numbers are coarse as well as inflated: GPT-4 states 0.9 on fully half of
examples, producing 8 unique confidence values across 12 datasets (Shrivastava et al.,
2023). For RLHF-tuned models the verbalized channel is nonetheless often better
calibrated than the token probabilities, which RLHF itself degrades (Tian et al., 2023).
The channel is trainable in at least one setting: GPT-3 can be fine-tuned to verbalize
calibrated uncertainty on arithmetic (Lin et al., 2022), the trained-calibration
precedent whose small-model analog our companion paper tests and finds wanting. Recent
faithful-uncertainty work makes the target sharper by asking whether expressed
uncertainty tracks intrinsic uncertainty, and shows that metacognitive RL can improve
that output metric (Gani et al., 2026; Liu et al., 2026; Yona et al., 2026). Our
companion diagnosis localizes why the channel fails in this model family (the internal
estimate is calibrated; the emitted token is not), and this paper is the constructive
complement: bypass the token.

#### Probing internal states

If the stated confidence is unreliable,
is a reliable one nonetheless sitting in the activations? A large body of work says yes
for truth-related structure: unsupervised truth directions (Burns et al., 2022), the
linear geometry of true/false statements (Marks et al., 2023), truthfulness classifiers
on hidden states (Azaria and Mitchell, 2023), and a single truthfulness hyperplane fit
across 49 datasets (Liu et al., 2024). The probe-generation gap has external precedent:
a probe reads truth from LLaMA-7B activations at 84% while the model generates
truthfully on about 32% of the same items (Li et al., 2023), an external "knows but
doesn't say." Closest to our answerability gate (the pre-generation readout this paper
thresholds to abstain), Slobodkin et al. (2023) show instruction-tuned models linearly
encode a question's *answerability* even while hallucinating an answer to it (probe F1
above 75% across nine model-dataset pairs, with causal LEACE erasure), and Ferrando et
al. (2024) find sparse-autoencoder entity-recognition directions ("do I know this
entity?") that causally gate refusal: knowledge-boundary signals, not answer-truth
signals. Prompted self-evaluation is a related but distinct channel: P(True) is prompted
self-grading and P(IK) a trained value head (Kadavath et al., 2022); neither reads
activations, but both anticipate the finding that models carry usable self-knowledge
(answerability recognition, specifically; not verified self-knowledge of whether a given
produced answer is itself correct).
The strongest counter-result gets its full weight: Cheang et al. (2025) argue internal
states mainly encode knowledge *recall* rather than truthfulness, and show that
hallucinations drawing on parametric associations evade probe detectors (AUROC 0.46 to
0.69) that catch unassociated ones; our construct decomposition (§4.4) applies the same
discipline to our own headline, separating carried nuisance from the smaller content
core that survives control. What differentiates this paper from the probing line: we
read *answerability* (a property of the question, before generation) and *per-answer
correctness* (a property of the produced answer, after it) as distinct axes at distinct
token positions, and we measure that readout's robustness surface (size, family, decode,
seed, pretraining stage) under pre-registered gates.

#### Reading after the answer

Does a model know more about its answer after producing it
than before? External evidence says the answer tokens are where the signal concentrates:
truthfulness information peaks at the exact answer tokens (probe AUC 0.85 to 0.95 across
datasets; Orgad et al., 2024), semantic-entropy probes trained at both a post-response
token and a pre-generation token give a direct external post-vs-pre contrast (Kossen et
al., 2024), and Azaria and Mitchell (2023) likewise probe the statement's own tokens. We
test this contrast directly, as a within-run paired comparison on the same rows (§4.2).

#### Abstention and selective prediction

A model that knows its limits should sometimes
refuse to answer. How do you get that behavior: train it in, or find it already present?
Selective prediction predates LLMs: SelectiveNet trains a rejection head jointly with
the classifier for a target coverage (Geifman and El-Yaniv, 2019). In LLMs the dominant
posture *trains abstention in*: R-Tuning fine-tunes "I don't know" onto the questions
the model gets wrong (Zhang et al., 2023), Cheng et al. (2024) build model-specific IDK
training sets, alignment-for-honesty formalizes refusal training (Yang et al., 2023),
and multi-LLM collaboration flags knowledge gaps to abstain on (Feng et al., 2024); Wen
et al. (2024) survey the space. AbstentionBench finds abstention unsolved across twenty
frontier models and *degraded* by reasoning fine-tuning (Kirichenko et al., 2025). Our
gate takes the other branch of the opening question: it installs selective prediction
without training, by thresholding an answerability axis the base model already carries.

#### Steering

Reading a direction out of activations is
one half of representation engineering (Zou et al., 2023) and writing along it
(steering) is the other (Turner et al., 2023); this paper is strictly the *reading*
half, and what is known about writing along these axes is taken up in the discussion
(§6).

---

## 3. Setup

### Models

The core mechanism is developed on Qwen3-4B in two conditions: the raw
instruction-tuned base (`unsloth/Qwen3-4B-bnb-4bit`, no adapter) and our deployed
checkpoint (clean supervised fine-tune → GRPO). The size study uses the raw Qwen3 bases at
1.7B / 4B / 8B / 14B. The cross-family study uses four ungated instruction-tuned bases at
comparable scale (Llama-3.2-3B, Ministral-3-3B, Qwen3.5-4B, and Gemma-4-E4B), read
training-free, exactly as the base-model condition.

### Data and labels

Answerable questions come from PopQA (Mallen et al., 2022) and
TriviaQA (Joshi et al., 2017), graded against gold
answer aliases into *correct* / *wrong*. Intrinsic answerable-vs-unanswerable structure and
the hallucination class come from SelfAware (Yin et al., 2023): questions it marks unanswerable, when the model
answers them anyway, are labeled *hallucinations* (a structural label: the model produced
a confident answer to a question with no answer; whether the model "answered" is itself
detected by a refusal classifier, and Limitation 4 discusses an audited artifact in that
detection specific to one checkpoint). This gives three groups for the
correctness axis: correct answers, wrong answers, and confident confabulations.

### Readout recipe

For each item we run a single forward pass over the concatenated
[prompt + answer] sequence and cache residual-stream activations at every layer at two
positions: the **last prompt token** (the *pre-generation anchor*, used for the gate) and
the **last answer content token** (the *post-generation* position, used for the dial).
Probes are standardized logistic regressions (StandardScaler + LogisticRegression, C=1.0);
reference scores are 5-fold stratified out-of-fold AUROC with a 2000-sample bootstrap
confidence interval. When a dial fit on one condition is evaluated on another, it is applied
*cold* (fit on the source, scored on the target, no refitting). Decoding is greedy
(deterministic). Each cell enforces a data-adequacy floor (≥30 wrong answers and ≥50
hallucinations) before a probe verdict is reported.

### Pre-registered gates

Every evidence cell locked its gates, success rule, and
falsifier before running, and none moved afterward. The cross-size and cross-family cells
shared three identical gates: gate, dial, and veto readouts each at AUROC ≥ 0.65 with a
bootstrap CI excluding 0.50, the veto primary; cross-family success was pre-defined as the
veto passing on at least 3 of 4 families, falsified by failure on 2 or more. The
seed-robustness replication gated only the dial and veto, because the gate reads a
position sampling never touches and was declared an invariance check in advance; its
seed-stability rules were locked too (a family is a seed-stable dial pass at 3 of 3
seeds, a seed-stable veto pass at 2 of 3 or better, and the per-seed veto majority may
never drop below 3 of 4). The pretrain-only contrast set a stricter gate bar (0.90), with
the falsifier that a base reads below 0.75 while its instruct sibling reads 0.95 or
above. One registered gate in this program missed: the original dial cell's calibration
gate (ECE below 0.15) failed by 0.001. We report the dial as a ranker, not a probability,
and that miss is part of why. Scaling sharpness was declared descriptive-only in advance.

### How this research was conducted with AI

This program is run by a human principal investigator working with a frontier language
model (Claude, Anthropic) acting as a research orchestrator, which dispatches specialized
AI agents for bounded tasks. We describe the arrangement because it is part of the
method: the division of authority keeps the parts of science that require accountability
human, and delegates the parts that benefit from tireless, parallel, adversarial labor,
under controls that make the delegation auditable.

The unit of work is a governed experiment: a self-contained directory holding a signed
amendment document (the design in prose), a machine-readable manifest, and the instrument
code. Before anything runs, the design registers a hypothesis, gates with numeric floors,
a falsifier stating what outcome would kill the claim, and predictions recorded before
the run. At signing, every instrument file is pinned by content hash (SHA-256). After
signing, gates and thresholds cannot move, and post-outcome changes to the registered
surface are prohibited outright. Every evidence cell in this paper ran under that regime,
and the retained predictions were wrong in instructive ways: the orchestrator predicted
the veto in a 0.65 to 0.85 band and the uncontrolled contrast landed above it, for a
reason the construct decomposition later made specific (the contrast carries the
question's answerability as well as the answer's content, §4.3 to §4.4); both the PI and the
orchestrator called the residual-coverage gates correctly while neither foresaw the
length confound those gates failed to guard, and neither foresaw the answerability carry
in the follow-up either (§4.4); the seed-robustness registration pre-named Llama and
Qwen3.5 as the veto cells most likely to flip, and both flipped upward instead (§4.10).
Cells registered before 2026-07-03 carry only the orchestrator's prediction; the dual
PI-plus-orchestrator practice was adopted mid-program and binds every cell signed after
it, including both cells in §4.4.

The trust boundary is explicit. The AI side builds harnesses against the locked design,
runs and monitors experiments, computes results, drafts documents (including this one),
red-teams findings, and proposes interpretations. The human side holds everything with
consequence: approving and signing designs, authorizing every paid compute launch,
adjudicating gate outcomes when judgment is required, merging evidence into the record,
and deciding verdicts.

Three controls do most of the work of keeping the AI honest:

1. Adversarial review before any verdict. Results, especially good ones, go to a
   separate red-team agent briefed to refute: oracle leaks, circular evaluation, goalpost
   drift, provenance holes, statistical errors. Section 4.4 is this control operating in
   public: a too-good margin triggered the audit that found the length confound behind a
   pair of passing gates, and the audit of the pre-registered fix found the answerability
   carry that cut a 0.92-class headline to an honest 0.74.

2. Read-before-cite. Signed amendment documents are the sole source of truth for what
   any prior experiment showed. No agent, including the orchestrator, may state a prior
   result from memory; the claim must trace to the document. This exists because language
   models pattern-match plausible histories, and a plausible-but-wrong account of your own
   prior experiment is the most dangerous artifact in an AI-run lab.

3. Provenance by construction. Instruments are content-hashed at signing, model
   weights are pinned by revision, and every number in this paper traces through Appendix
   A from the text to its amendment to the result JSON to the instrument bytes that
   produced it.

We make no claim that this workflow removes the need for human scientific judgment. The
claim is narrower and testable: it makes AI participation in research auditable, keeps a
durable line from every published number to the bytes that produced it, and forces the
participants to say, in advance and in writing, what would prove them wrong. The one
registered gate this program missed (the dial's calibration gate, by 0.001, above) stays
on the page for the same reason the wrong predictions do: a workflow that quietly
discards its misses is optimizing for the appearance of foresight, which is precisely
the failure mode this research program studies in language models.

---

## 4. Results

### 4.1 The answerability gate reads off the anchor, before generation

At the last prompt token, before any answer is generated, a linear probe separates
answerable from unanswerable questions at **AUROC 0.997** on the raw Qwen3-4B base. This is
the readable form of the internal estimate the diagnosis identified: the model represents
"can this be answered?" at the moment it is about to answer, and the representation is
almost perfectly separable. Thresholding this axis gives an abstention gate that needs no
training to install. External precedent says an axis like this should exist: Slobodkin et
al. (2023) probe answerability from hidden states at F1 above 75% even while the model
hallucinates an answer, and Ferrando et al. (2024) find entity-recognition directions
that causally gate refusal at the knowledge boundary. What is new here is the strength at
which it saturates and, below, how far it travels. As the cross-model results show, this
axis is the most robust of the three: it is near-saturated (0.997–0.998) on every size
and every family we tested.

### 4.2 The correctness dial reads off the answer, and reads better *after* it

Answerability is a property of the question. Whether a *specific produced answer* is correct
is a different property, and it is legible at a different place. A linear probe at the last
answer token ranks correct-vs-wrong answers at **AUROC 0.834** on the Qwen3-4B base
(layer 20). Reading *after* the answer beats reading *before* it: the
post-generation position scores **+0.065** over the pre-generation position (CI [0.040,
0.090], excludes zero). The model's representation of "was that right?" is sharper once it
has committed to the answer than at the moment it begins: a self-evaluation effect
localized to token position, and one that peaks in the middle of the network rather than at
the final layer (Figure 4). The position matters in external work too: truthfulness
signal concentrates at exact answer tokens (Orgad et al., 2024), and semantic-entropy
probes read better at the post-response token than at the pre-generation one (Kossen et
al., 2024).

The dial survives deployment. On our clean-SFT → GRPO checkpoint the same post-generation
readout scores **AUROC 0.819** (layer 22), with the same post-beats-pre ordering
(post 0.819 vs pre 0.745). A dial *fit on the base* and applied *cold* to the deployed
checkpoint transfers only partially (0.679): the correctness *direction* drifts under
training even though the *readout* remains strong when refit. The axis exists on both
checkpoints, but the probe should be refit per checkpoint rather than transported.

Why does a probe need a refit across checkpoints when the axis survives? An exploratory
diagnostic tracked the known-vs-unknown (answerability) direction across four training
stages in a shared basis. The readout's strength never moves: it is already at full
strength in the raw base (CV AUROC 0.951) and no stage improves it, consistent with the
training-free reading in §4.6. The direction, however, rotates once, nearly
orthogonally, at instruction SFT (raw-to-SFT cosine 0.06 to 0.25 at mid and late
layers), and both GRPO stages then ride the rotated direction almost unchanged (cosine
0.91 and above). One rotation event, not gradual drift. That is why cold transport
degrades while a refit probe stays strong.
That account was built entirely from the answerability direction. Whether the
correctness direction rotates the same way was, until a follow-up measured it
directly, an inference rather than a measurement. The follow-up's answer is a
null on the single-rotation-at-SFT story: the raw-to-clean-SFT cosine (0.19) is
low, as the answerability account would predict, but the two later transitions
that account also predicts should be stable (0.85 or above) come in far lower
instead (0.45 and 0.33). A reliability control run alongside it shows why a
single fitted axis struggles to answer this question at all: refitting the
same direction on two disjoint halves of one checkpoint's own data agrees at
only 0.17 cosine, even though the readout's ranking accuracy stays flat near
AUROC 0.80 across every stage. The correctness direction is not reliably
pinned down by a single fit, so a low cross-checkpoint cosine cannot, by
itself, tell genuine rotation apart from estimation noise.

A second follow-up asked the sharper question directly: does the partial cold
transfer ride on a shared low-dimensional subspace, so the single fitted axis
is just one arbitrary direction inside a wider region the two checkpoints
share, rather than on a direction that itself moves? That question also
returned a null (the instrument built to separate the two accounts saturates
below its own detection threshold for any signal, including a planted example
of the exact shared-subspace pattern it was designed to find), but it isolated
two findings that stand on their own. First, comparing the base model and the
deployed checkpoint, exactly one shared direction clears a label-permutation
chance level with a clear margin; widening the comparison to two dimensions
clears that bar only marginally, and four to thirty-two dimensions do not
clear it at all. Second, the transferable part of the signal is spread out
across the base model's activation span rather than concentrated in its top
discriminative directions: an arbitrary eight-dimensional slice of that span
recovers about as much of the deployed checkpoint's correctness signal
(AUROC ~0.70) as the base model's own top eight discriminative directions do
(~0.74). The portable part of
correctness tracking across checkpoints, in other words, looks like a single
weak shared direction rather than a shared subspace, and that direction itself
is not well identified by the data available to fit it. Both follow-ups are
exploratory Tier-2 results, single model, with label-clean positive findings;
reported separately from the locked numbers and never pooled with them;
provenance in Appendix A.

One honest caveat carried from the start: the dial *ranks* correctness well (AUROC) but is
not a calibrated *probability* (ECE 0.151 on the base). The ranking-vs-calibration
distinction is standard (Guo et al., 2017; Ulmer et al., 2024): for a thresholdable trust
number, ranking is the operative property, and a stated probability would need a
downstream calibration map. We claim the ranking, not the probability. This ECE also
carries the program's one registered gate miss, reported in §3.

### 4.3 The dial vetoes confident confabulation

The same correctness dial, applied to the hallucination group (confident answers to
unanswerable questions), assigns them the **lowest trust of any group** on the raw base.
On the deployed checkpoint the same descriptive pattern holds, but a PI-funded audit
(2026-07-18) found that 90.1% of that checkpoint's labeled hallucination rows (109 of
121) were explicit trained refusals misclassified as answers by a narrow refusal
detector; under corrected labels only 12 (Set A) or 8 (Set B) genuine hallucination rows
remain, below this cell's own pre-registered ≥50 adequacy floor. Amendment U's primary
gated verdict (U-G3) is accordingly reclassified **UNPOWERED**, not a gated PASS. The
corrected descriptive AUROCs, 0.9067 (CI [0.8133, 0.9705], Set A) and 0.8639 (CI [0.7384,
0.9498], Set B), are directionally consistent with the original 0.980 reading but cannot
gate a claim. The within-SelfAware control (known-answered vs unknown-answered, same
dataset), reported pre-correction as **0.93**, is superseded by the same correction: 0.8140
(CI [0.6953, 0.9127]) against Set A, 0.7369 (CI [0.5947, 0.8549]) against Set B, and 0.7500
(CI [0.6073, 0.8678]) fully corrected, all descriptive at the corrected n. The dataset-shift
rebuttal this control was meant to supply is weakened, not restored: it now rests on a
roughly 0.74-to-0.81 separation rather than 0.93 (corrigendum,
`experiments/unified-two-signal-dial-veto/AMENDMENT.md`, 2026-07-18). Confident
confabulation still does not read like a correct answer to the dial on the raw base, and
descriptively on the deployed checkpoint, though the deployed-checkpoint reading is now
suggestive rather than gated. This is the property that makes the dial a hallucination
*veto* and not merely a correctness *ranker* on the raw base: the failure mode we most
want to catch (fluent, confident, wrong) is exactly the one the dial pushes to the bottom.
What the veto reads when it does this
was decomposed on the raw base by the pre-registered analysis in §4.4: a content-trust
core of AUROC **0.737** (CI [0.650, 0.815]) once answer length and question answerability
are both controlled, plus the question's carried answerability, which the post-answer
state retains and which by itself separates unanswerable-question confabulations from
good answers nearly perfectly. The deployed checkpoint's veto has not been decomposed the
same way; we read it as sharing this structure because its contrast is built identically. The registered fact: the orchestrator put this veto in a 0.65
to 0.85 band, with the named risk that confident confabulation would carry the same
internal signature as confident correctness and the falsifier would fire. The risk did
not materialize, and the controlled content core sits inside the registered band.

Figure 2 shows the mechanism directly: the dial-mean of the hallucination group sits far
below the correct group, and the size of that separation is what the veto AUROC measures.

### 4.4 What the veto is made of: two nuisances and a content core

What does the veto read when it pushes a confabulation to the bottom? The headline
contrasts above cannot say: they compare correct answers against confabulations on
unanswerable questions, so any signal that differs between those groups (the answer's
content, the answer's length, the question's answerability) is available to the probe.
Two pre-registered follow-up experiments, a residual-coverage probe and a
length-balanced confirmatory, both adversarially audited before their
verdicts were recorded, decompose the read into those three parts.

Both nuisances are real, and each is large where it applies. Confabulations run long
and good answers run short (median 94 answer tokens against 24 on the residual-coverage
population), and the probe reads the hidden state at the last answer token, whose
position encodes length: on that population, answer length alone separates the groups
at AUROC 0.943. Answerability carries into the post-answer state: on confabulations
whose questions are unanswerable, the veto separates them from good answers at roughly
0.99, because the post-generation hidden state still holds the gate's own axis.

A genuine content core survives both controls. On a fresh 192-token generation with
1:1 caliper matching on answer length (length-only AUROC at chance, 0.492, by locked
precondition) and both classes restricted to answerable questions (wrong answers on
answerable questions versus correct answers on answerable questions, 65 matched pairs,
out-of-fold), the veto reads AUROC **0.737** (CI [0.650, 0.815]), a margin of
**+0.244** over the length-only baseline (CI [0.120, 0.367], excludes zero). That
controlled number clears the experiment's pre-registered gates, and the registered
verdict is explicit: the larger, uncontrolled contrasts must not be cited as the
content-trust characteristic. The honest content number is about 0.74.

What this means for the numbers above. Every headline veto contrast in this paper
(the deployed checkpoint, the raw base at 0.754, the cross-family and
seed-robustness columns below) compares correct answers against confabulations on
unanswerable questions, and the within-SelfAware control shares that structure, so
carried answerability is uncontrolled in all of them. The decomposition does not
invalidate those numbers; it says what they are made of: a content-trust core of
about 0.74 plus a carried answerability signal that is nearly separable on
unanswerable-question confabs. For deployment the blend is acceptable and even
useful: flagging a confabulation because its question was unanswerable still flags
it, and the veto's job is to back up a gate that has already missed. For construct
interpretation the blend matters: the dial's low trust on confabulations is not
purely a read of the produced answer. Both experiments are exploratory, single-seed,
on the raw Qwen3-4B base under an abstention-affording prompt surface (a different
surface from the answer-encouraging one in §§4.2 to 4.3), and are never pooled with
the numbers above. The full audit history, including the intermediate estimates each
audit retired, is preserved in the released research record (Appendix A).

### 4.5 The two axes are orthogonal: a pipeline, not a fused scalar

Gate (answerability, at the anchor) and dial (correctness, post-generation) are separable
axes. When we fuse the two scalars into a single combined trust number, correctness ranking
*degrades* (Δ **−0.014**). The axes carry complementary information that a single number
destroys. Keeping uncertainty sources separate has external support: Taparia et al. (2026)
decompose LLM uncertainty into input, knowledge, and decoding components and argue that
single scores hide the actionable structure. The countervailing result is output-level:
Shrivastava et al. (2023) improve confidence estimates by *mixing* surrogate and
linguistic scores. We read no tension between the two: their mixture combines two noisy
views of one quantity (answer correctness), while our axes measure different quantities
(question answerability, answer correctness), and the fusion cost is the empirical sign
that they are not redundant. Provenance for the fusion number: it comes from an earlier
registered CPU diagnostic on the deployed checkpoint, cited as prior fact in the veto
experiment's pre-registration (artifact trail: Appendix A); folding the gate score into the
dial changed correctness triage by Δ −0.014 with a CI excluding 0, and correctness triage
is the only quantity that diagnostic measured. The deployment consequence is to keep them
as **two sequential stages** rather than one score (Figure 6):

- Stage 1, the gate: at the prompt anchor, threshold the answerability axis. If below
  threshold, abstain ("I don't know") and stop.
- Stage 2, dial + veto: for questions that pass the gate, generate the answer, then read
  the correctness dial at the post-answer token and surface it as the trust number.
  Confident confabulations that slipped the gate tend to land at the bottom of the dial,
  partly on answer content and partly on carried answerability (§4.4).

### 4.6 The whole mechanism is training-free: training does not *create* it

Every result above reproduces on the **raw** Qwen3-4B instruction-tuned base, with no
adapter and no abstention training of ours: gate **0.997**, dial **0.834**, veto **0.754**.
Both the gate and the dial pass unchanged; the veto is present and above chance on the raw
base. What our training does not do is create the mechanism. Whether it *sharpens* the
veto is now an open question: the mean trust the dial assigns to confident confabulations
reads **0.271** on the base and **0.183** (Set A, n=12) / **0.274** (Set B, n=8) after
training, under hallucination labels corrected for a detector artifact that had
originally read the group mean at 0.018 (a PI-funded audit, 2026-07-18, found 90.1% of
the labeled hallucination rows were misclassified trained refusals; the corrected sample
sits below the cell's own ≥50 adequacy floor, so this descriptive comparison is
unpowered, not gated, and under Set B it shows no drop at all). The trained model
still reads confident confabulations well below correct answers, though not at the
originally reported near-zero trust. Training adds essentially
nothing to the gate (already saturated) and installs autonomous behavioral abstention, but
the *readable trust signal itself* is a property of the frozen representation (Figure 5).

We scope "training-free" precisely: the raw base is the *instruction-tuned* release, so
"training-free" means "no abstention fine-tuning and no reinforcement learning of ours,"
**not** "no training ever." Read on this release alone, the
answerability axis could in principle be a product of upstream instruction tuning;
§4.11's pre-registered pretrain-only contrast closes that question directly: read on
*pre-instruction* bases, the axis is already there. The claim here is narrower and stands on
its own: *our* training regimen (the one the companion paper shows cannot close the
verbalization gap) is not what puts the readable signal there.

### 4.7 The readout is size-robust (1.7B–14B)

Across the Qwen3 family at 1.7B, 4B, 8B, and 14B, the training-free readout passes all three
gates at every size. The gate stays saturated (~0.997) throughout. The veto, however, does
*not* improve monotonically with scale: it is 0.757 at 1.7B, 0.754 at 4B, peaks at
**0.846 at 8B**, and *dips* to **0.741 at 14B**. The "bigger sharpens the veto" expectation
is not supported, an observation we flagged as descriptive in advance and did not promote
to a claim. The veto being the axis that wobbles with scale is the first sign that it, and
not the gate or dial, is the fragile part of the mechanism (Figure 3, left).

### 4.8 Cross-family: the gate and dial are universal; the veto is model-dependent

We pre-registered a cross-family confirmatory on four independent families read
training-free (Llama-3.2-3B, Ministral-3-3B, Qwen3.5-4B, Gemma-4-E4B), with SUCCESS defined
as the veto passing on ≥3 of 4. **The result is SUCCESS (veto 3/4)**, and the shape of the
result is the paper's central finding (Figure 1, Table 1).

**Table 1. Cross-family training-free readout (AUROC; 95% bootstrap CI).**

| Model | hidden dim | Gate | Dial | **Veto (primary)** | Verdict |
|---|---|---|---|---|---|
| Llama-3.2-3B | 3072 | 0.997 [.995,.999] | 0.861 [.844,.879] | **0.633 [.603,.665]** | PARTIAL (veto fail) |
| Ministral-3-3B | 3072 | 0.997 [.995,.999] | 0.818 [.797,.839] | **0.733 [.703,.762]** | PASS |
| Qwen3.5-4B | 2560 | 0.998 [.997,.999] | 0.827 [.806,.848] | **0.666 [.634,.695]** | PASS (marginal) |
| Gemma-4-E4B | 2560 | 0.998 [.997,.999] | 0.818 [.794,.840] | **0.871 [.850,.893]** | PASS |

#### The gate and dial pass on all four families

The gate is near-saturated everywhere
(0.997–0.998); the dial ranges 0.818–0.861. These two axes are *family-general*: the ability
to read "can I answer this?" at the anchor and "is this answer right?" after the answer is
not a Qwen idiosyncrasy; it is a property of instruction-tuned small LMs across four
independent lineages.

#### The veto replicates but is fragile

It passes cleanly on Gemma (0.871) and Mistral
(0.733), marginally on Qwen3.5 (0.666: point above the bar, CI lower bound 0.634 dipping
just under it), and *fails* on Llama (0.633: a real signal, CI excludes chance, but below
the 0.65 bar). Catching *confident* hallucination is the model-dependent capability, exactly
as the non-monotonic size result foreshadowed.

#### The descriptive mechanism

The split is explained by the correct-vs-hallucination gap in
the dial's own distribution (Figure 2). Where a model's confident confabulations read as
low-trust, the veto works; where they read almost as trustworthy as correct answers, it
fails:

- Gemma (veto 0.871): hallucination dial-mean 0.089 vs correct 0.593, the widest split;
  confabulations read as near-zero trust.
- Mistral (0.733): 0.278 vs 0.605, a clean separation.
- Qwen3.5 (0.666): 0.425 vs 0.636, intermediate.
- Llama (0.633): 0.476 vs 0.707: confident confabulations read *almost as trustworthy
  as correct answers*, so the dial cannot separate them.

Ordering families by the dial-mean gap (Gemma 0.504 > Mistral 0.327 > Qwen3.5 0.211 ≈ Llama
0.231) tracks the veto verdicts directionally. We flag one honest wrinkle: Llama's mean gap
(0.231) slightly *exceeds* Qwen3.5's (0.211), yet Llama fails and Qwen3.5 marginally passes,
because the veto AUROC depends on the full distribution overlap, not the mean gap alone. We
therefore read the gap as a *directional* predictor, not a strict rank. The stable
conclusion stands: **gate + dial are family-general (4/4); the veto replicates (3/4 under
this single greedy decode) and is the fragile axis**, though §4.10 shows the two greedy
misses are largely decode artifacts: under sampled decoding the veto passes seed-stably on
all four families.

### 4.9 Where the signals live: a workspace reading (descriptive)

Where in the network do the two axes live? The cross-family replication runs (§4.8) carry the
full per-layer AUROC surface for the gate and the dial, and plotting them against fractional
depth (layer / n_layers, since the four families have 28, 26, 32, and 42 blocks) shows the
two axes occupy different parts of the network (Figure 7). The gate is not a
single-layer phenomenon anywhere: in all four families it rises from chance at the embedding
to a saturated ~0.997+ plateau whose within-0.005-of-max span covers most of the network
(Llama L5–28/28, Ministral L4–26/26, Qwen3.5 L7–32/32, Gemma L7–42/42), with onset by roughly
20% of depth in every family. The per-family "best gate layer" differences in the result
JSONs are therefore argmax jitter on a flat plateau, not meaningful localization. The dial
is different: its within-0.02-of-max band is a narrower, overlapping mid-to-late region
(Llama L11–28, Ministral L16–21, Qwen3.5 L13–24, Gemma L15–41), and Llama's dial argmax sits
at L25/28, near the unembedding. Read descriptively, answerability appears to be computed
early from the question and simply carried forward, while correctness requires the formed
answer and lives in a localized mid-to-late band. This is a descriptive replot of the
already-reported cross-family surfaces: no new claim and no gate rests on it.

> **Figure 7. Cross-family depth profile of the two axes.** Per-layer AUROC for the
> answerability gate (left, zoomed y-axis) and the correctness dial (right) against
> fractional depth, one line per family; dots mark each family's argmax layer and the bars
> under each panel mark its within-tolerance span (gate: within 0.005 of max; dial: within
> 0.02). The gate saturates by ~20% of depth and stays saturated to the last block in all
> four families, so per-family best-layer differences are jitter on a plateau; the dial
> concentrates in an overlapping mid-to-late band, with Llama's argmax at L25/28 near the
> unembedding. Descriptive only, replotted from the cross-family replication's per-layer
> AUROC surfaces (Appendix A). (`fig-p3-07-depth-profile.png`)

An independent instrument gives that depth picture a name. As a read-only lab diagnostic
(exploratory, no registered gates, no claim promoted), we implemented from scratch the
Jacobian lens (J-lens) of Gurnee et al. (2026): a first-order estimate of how a layer's
residual-stream state causally shapes the final-token logits, unembedded into vocabulary
space. The implementation was validated against the model's own logit lens at the final
layer before anything was read from it (mean cosine 0.9811, mean top-10 overlap 0.82,
n = 1000 prompts). Gurnee et al. find that the directions the J-lens can express, the
model's *verbalizable workspace*, concentrate in an intermediate band of layers. On
Qwen3-4B the same signature appears: the effective dimensionality of the J-lens readout
stays near floor through the first half of the network, rises sharply at hidden state 23,
peaks at hidden state 26, and falls back toward the output layers. That is a
workspace-like band at hidden states 23 through 29 of 36, roughly 60 to 80% of depth.

The overlap with Figure 7 is the point: the correctness dial's within-tolerance band on
the Qwen-family models is a mid-to-late region that overlaps this workspace band, while
the gate saturates by 20% of depth, far below it. Read descriptively, the dial appears to
read from the band where the model's verbalizable workspace concentrates, and the gate is
computed and carried long before the workspace begins. Three scope fences, stated
plainly. First, the J-lens run characterized the companion actuation line's caution and
known-unknown directions, not this paper's gate and dial probes, so the claim here is band
overlap, never that the dial itself was verbalized under the lens. Second, the run used
the bf16 sibling of the bnb-4bit base (same architecture and configuration, different
quantization). Third, it is an exploratory characterization: it grounds the depth
picture, and no result in this paper rests on it. It also does not explain why the dial
reads better after the answer than before it; that mechanism question remains open.
(Artifacts: Appendix A.)

### 4.10 Seed-robustness: the greedy veto misses were decode artifacts

Every number in §4.8 comes from a single deterministic decode (greedy). A deployment
samples. We therefore pre-registered a seed-robustness confirmatory: the identical
training-free readout on the same four families under **sampled decoding** (temperature 0.7,
top-p 0.9) across **three seeds**, with the same per-cell gates and adequacy floors. The
gate was pre-declared decode-invariant (it reads the prompt anchor, which sampling never
touches) and emitted as an invariance check only; the dial and veto (both read from
*sampled* answers) were the endpoints. Success required the dial seed-stable on 4/4
families, the veto seed-stable on ≥3/4, and the per-seed veto majority never dropping below
3/4 on any single seed. The locked stability definitions differ by axis: a family is a
seed-stable *dial* pass only at 3/3 seeds, but a seed-stable *veto* pass at ≥2/3, which is
why Ministral's 2/3 in Table 2 reads YES.

**Table 2. Sampled-decode seed-robustness (AUROC per seed; mean [min–max] across 3 seeds).**

| Model | Dial (3 seeds) | Veto (3 seeds) | Veto seed-stable? | Greedy veto (§4.8) |
|---|---|---|---|---|
| Llama-3.2-3B | 0.848 [0.827–0.865], 3/3 pass | **0.739 [0.684–0.801], 3/3 pass** | **YES** | 0.633 (FAIL) |
| Ministral-3-3B | 0.806 [0.799–0.812], 3/3 pass | 0.681 [0.606–0.742], 2/3 pass | **YES** | 0.733 (pass) |
| Qwen3.5-4B | 0.852 [0.830–0.864], 3/3 pass | **0.753 [0.659–0.807], 3/3 pass** | **YES** | 0.666 (marginal) |
| Gemma-4-E4B | 0.817 [0.802–0.839], 3/3 pass | **0.742 [0.718–0.762], 3/3 pass** | **YES** | 0.871 (pass) |

#### The two greedy veto misses flip to passes under sampling

Llama, the one clean veto
*failure* in §4.8 (0.633), passes on **all three seeds** under sampled decoding (0.684–
0.801). Qwen3.5, the marginal pass whose CI dipped below the bar, passes all three seeds
cleanly. The §4.8 "fragile veto" split is therefore partly a *decode* artifact, not purely a
model property: a single greedy trajectory produces one specific set of confabulations, and
Llama's greedy confabulations happened to read as trustworthy; its sampled ones do not.
Single-decode point estimates *understated* the veto.

Decode sensitivity should not surprise: the sampling-based uncertainty literature extracts
its signal precisely from cross-sample variation (semantic entropy, Kuhn et al., 2023;
SelfCheckGPT, Manakul et al., 2023), Orgad et al. (2024) build an error taxonomy from
resample distributions, and Taparia et al. (2026) treat decoding randomness as its own
uncertainty component. What those methods exploit by sampling many times, a single-decode
readout is exposed to.

#### Seed-sensitive per cell, seed-stable per family

Across-seed spread on the
veto is real (Llama range 0.12, Qwen3.5 0.15, Ministral 0.14, Gemma 0.04, versus dial
spreads of 0.01–0.04), and Ministral drops below the bar on one seed (0.606 on seed 1, its
only failing cell). Per-cell veto numbers should accordingly be reported with seed spread,
not as point estimates. At the family level the verdict is stable: **all four families are
seed-stable veto passes.**

#### The gate is decode-invariant, as pre-declared

Across all completed cells the gate sits
at 0.996–0.999 with a per-family across-seed range under 0.003: sampling the answer does
not move an axis read before the answer exists.

The registration pre-named its own live falsifier, and the note is worth quoting in
substance: the two cells most likely to flip were Llama's veto (a greedy fail) and
Qwen3.5's (a marginal pass), in either direction. Both flipped upward.

#### Verdict

The pre-registered verdict is SUCCESS. All three locked clauses pass: (a) the dial is
seed-stable on **4/4** families (every one of the 12 cells passes the dial bar); (b) the
veto is seed-stable on **4/4** families (Llama and Qwen3.5 and Gemma 3/3 each, Ministral
2/3); (c) the per-seed veto majority never drops below 3/4: seed 20260701, the pinch seed
where Ministral fails, clears at 3/4 on Gemma's 0.762 pass, and seeds 20260702/20260703 sit
at 4/4. The falsifier (a seed with majority < 3/4, or ≥2 families flipping veto status) did
not fire: Ministral is the only status-flipping family. The Table 1 magnitudes are thereby
promoted from "single greedy decode" to **seed-robust under sampled decoding**
(pre-registration and per-cell provenance: Appendix A).

### 4.11 The signal predates post-training: pretrain-only bases and an era ladder

Every base so far (including every "raw" base in §§4.6–4.9) is a vendor *post-trained*
instruct release, so all of the above is compatible with the signal being installed by
instruction tuning. We pre-registered the contrast that separates the hypotheses: the
identical three-readout panel (gate, dial, veto) on four **pre-instruction** bases matched to the §4.8
families (Qwen3.5-4B-Base, Gemma-4-E4B-pt, Llama-3.2-3B, Olmo-3-7B), with the primary
hypothesis (H1) that the answerability gate is already present before any post-training,
and the falsifier that a base reads < 0.75 while its instruct sibling reads ≥ 0.95. Base
models were prompted with a k-shot plain-text render (they have no chat template); one
dual-render control and one same-pipeline instruct sibling complete the design.

**Table 3. Pretrain-only bases (greedy, single pipeline; AUROC at each model's best layer).**

| Model | Gate | Dial | Veto | within-SA control |
|---|---|---|---|---|
| Qwen3.5-4B-Base (k-shot) | 0.9984 | 0.8725 | 0.6657 | 0.6196 |
| Qwen3.5-4B-Base (chat-render control) | 0.9977 | 0.8511 | 0.8672 | 0.7961 |
| Gemma-4-E4B (pt) | 0.9975 | 0.8633 | 0.8743 | 0.7824 |
| Llama-3.2-3B (base) | 0.9972 | 0.8235 | 0.8354 | 0.7712 |
| Olmo-3-7B (base) | 0.9975 | 0.8442 | 0.8029 | 0.7912 |
| Olmo-3-7B-Instruct (same pipeline) | 0.9979 | 0.8103 | 0.7306 | 0.6741 |

#### Registered outcome

The hypothesis is supported 4/4 and the falsifier fired on 0/4 pairs. Every pre-instruction base reads
the gate at 0.997+, indistinguishable from the instruct releases. The veto also clears its
bar on all four bases (0.666–0.874). The boundary signal is not installed by post-training;
it is already in the pretrained representation, and instruction tuning at most re-renders it.
This confirms, in hidden states and under a pre-registered falsifier, a pattern reported
at the output level: pretraining builds calibration and post-training erodes it (OpenAI,
2023; Zhu et al., 2023; He et al., 2023; Xiao et al., 2025), and knowledge-boundary
directions found in a base model causally control the chat sibling's refusals (Ferrando
et al., 2024).

#### Post-training does not sharpen the readout, and can dull it

The one clean
base→instruct pair read under a single pipeline (Olmo-3, same seed, scorer, and render
class) moves the veto **0.803 → 0.731** and the within-SelfAware control 0.791 → 0.674;
the render-confounded cross-run pairs sit at or below their bases too. This bounds
§4.6's sharpening question from the other side: whatever sharpening the Qwen3-4B veto
may have gained (§4.6, now unpowered under corrected labels) would trace to *targeted
abstention training*, not post-training per se. Generic
vendor post-training adds nothing to any of the three axes and moved the fragile one the
wrong way, consistent with §4.7's non-monotonic scale result.

#### Part of the veto's fragility is the prompt surface, not the model

The dual-render
control shows Qwen3.5-Base's veto is render-sensitive (k-shot 0.666 vs chat-render 0.867)
while its gate is render-invariant (0.998 under both). Per-model veto validation (§4.8's
practitioner rule) should therefore fix the render before comparing numbers.

#### An era ladder, strictly descriptive

Read the same panel down a ladder of historical
bases and all three readouts stay above the 0.65 bar as far back as **GPT-2-XL (2019)**
(gate 0.9911, dial 0.7940, veto 0.7936); Pythia-2.8B, Llama-2-7B, and OLMo-2-7B fill the
rungs to the modern bases. The raw gate is nearly era-flat (0.991 → 0.998); what improves
across eras is the *within-SelfAware* control (~0.59 on GPT-2/Pythia rising to ~0.71–0.82
from Llama-2 onward): the in-distribution separation of confident hallucinations from
known answers, not the gross answerable/unanswerable split. No era claim is minted from
this arm; it was registered as descriptive.

#### A text baseline bounds all of the above

A TF-IDF classifier on the question surface
alone reads the gate pool at **0.964 ± 0.016** and predicts dial correctness at 0.75–0.78
per family. The hidden-state readouts sit above these bounds (gate 0.991–0.998, dial
0.79–0.87), but the *margins*, not the raw AUROCs, are the honest effect sizes: much of
the gate is surface-predictable on SelfAware, on any model of any era. A counterweight
from the program's own registered control package: the
latent known-vs-unknown readout on this pool survives lexical, over-refusal, and
cross-regimen controls, so the TF-IDF bound reads as pool-difficulty context, not as an
explanation of the hidden-state signal. (Pre-registration
and per-cell provenance: Appendix A.)

---

## 5. The deployable pipeline

Putting the pieces together (Figure 6), a small LM can carry a training-free trust
mechanism with no fine-tuning.

#### Gate (pre-generation)

Read the answerability axis at the prompt anchor. Below
threshold → abstain. This is the most robust component (0.997–0.998 everywhere).

#### Dial (post-generation)

For gated-through questions, generate, then read the
correctness axis at the post-answer token and surface it as a *ranked* trust number.

#### Veto (within the dial)

Confident confabulations that pass the gate are pushed to
the bottom of the dial. Two qualifications, both from pre-registered follow-ups. First,
the veto is the high-variance axis: it passes seed-stably on all four families under
sampled decoding (§4.10), but individual decodes and seeds can dip below the bar, so
validate it per model and per decode configuration and report it with seed spread; the
gate remains the primary defense. Second, the veto is a blend, not a pure content read
(§4.4): controlled for answer length and question answerability, its content core is
about 0.74, and the rest of the headline separation is carried answerability. In a
pipeline that is acceptable: the veto's job is to catch what the gate missed, and
catching a confabulation by re-reading the question's answerability after generation
still catches it. But expect the ~0.74 content core, not the headline blend, on
confabulations whose questions read cleanly answerable, and do not read the dial score
on a flagged answer as a calibrated content probability (§4.2).

Two engineering notes fall out of the results. Keep the axes *separate*: fusing them costs
correctness ranking (§4.5). And *refit the dial per checkpoint*: the correctness direction
drifts under training (cold transfer 0.679, §4.2) even though the axis persists. The gate,
by contrast, transports: in a registered cross-dataset transfer experiment, a gate probe
fit on one dataset applies cold to another at 0.983
(KUQ to SelfAware, on the deployed checkpoint; Appendix A), and it is cheap
to install anywhere.

For operators who need operating points rather than AUROCs, a companion warning-policy
characterization (whose aim-small selection rule §4.4's residual
experiment reused; Appendix A) works the veto into declared-floor thresholds per checkpoint: only
operating points with warning precision at or above 0.80 and a bootstrap CI lower bound
at or above 0.70 qualify, and precision, recall, false-alarm rate, and a calibrated
P(hallucination given warned) are reported at each.

Two deployment cautions from the literature, and one gap. The probe must stay a held-out
*readout*, never a training signal: training a model against a lie detector can teach
evasion instead of honesty (Cundy and Gleave, 2025), so the dial is not a reward. The
readout is also the cheap option: a linear probe replaces the 5-to-10-fold sampling cost
of consistency-based detectors (Kossen et al., 2024). And to our knowledge no published
system yet deploys an internal-state probe as its production abstention gate; the
pipeline above is a concrete, validated proposal for exactly that gap.

---

## 6. Discussion

#### Epistemic state as a readout, not a training outcome

The companion diagnosis
showed the internal answerability estimate is calibrated while the emitted one is flat, and
that our training cannot reconcile them through the confidence token. This paper's
constructive result is the other side of that coin: because the signal is *in the
representation*, it can be *read* even when it cannot be *trained into the token*. The most
useful part of epistemic humility for a small model (a thresholdable "should I answer, and
how much should you trust this?") is available from a frozen model with a linear probe.

#### What training is for

Our training is not wasted, but its role is narrow and specific: it installs
autonomous behavioral abstention, and it may *sharpen the veto*, though that comparison
is now unpowered and null under Set B (confabulation dial-mean 0.271 base vs 0.183/0.274
corrected; originally 0.018, §4.6). It does
not create the gate, the dial, or the veto, and §4.11 sharpens the negative half further:
the signal predates not just our training but *any* post-training (gate 0.997+ on four
pre-instruction bases), and generic vendor post-training does not sharpen the readout either
(the clean Olmo-3 base→instruct pair moves the veto 0.803 → 0.731). Sharpening is a property
of *targeted* abstention training, not of post-training in general. This reframes the
calibration-training question: the goal is not to teach the model what it knows (pretraining
already put that there), but to make its *behavior* and its *emitted signal* faithful to what
it already represents; and, for the veto specifically, to sharpen a signal that is present
but weak on some models out of the box.

#### Universal axes vs a high-variance capability

The cleanest scientific result is the
split. "Can I answer this?" and "is this answer right?" are readable across four families
and four sizes; they look like general properties of instruction-tuned small LMs. "Can I
distrust my own confident fabrication?" is present across the same families (seed-stable
4/4 under sampled decoding, §4.10) but far noisier: strong on Gemma, decode- and
seed-sensitive elsewhere (Llama's greedy failure flipped to three sampled passes), and
non-monotonic in scale. And the construct decomposition (§4.4) says what the fragile
capability is made of: a content-trust core of about 0.74 plus carried answerability. This
is an actionable map for practitioners (the gate is safe to rely on anywhere; the veto must
be validated per model and reported with seed spread) and a pointed question for future
mechanistic work (why do some models' confabulations read as low-trust to their own
correctness axis on any decode, while others' depend on which confabulation the decoder
happens to produce?).

#### Why not just steer?

The companion diagnosis found the answerability axis is causally
steerable, but *asymmetrically*: excess caution could be relaxed, and pushing along the
axis did not install missing caution. That asymmetry is a fact about *ungated* pushes,
not about writing in general.
On the raw Qwen3-4B base (bf16 sibling), an answerability-gated (known-unknown-gated)
caution write, which fires only on rows whose known-unknown (answerability) readout
clears a frozen threshold and snaps them to a fixed setpoint, converted held-out
confabulations into coherent refusals at 73.5% (Wilson 95% CI [66.7,
79.3]) at a 3.1% known-correct false-refusal cost (CI [1.6, 6.0]), with placebo controls
clean under registered gates; a registered multi-source replication at a workspace-band
write site (§4.9) reached 92.8% (exploratory, one model, one scale). The honest statement
is conditional: ungated steering could not install missing caution; an answerability-gated
write can, on one model, and reconciling that with the asymmetric-steering diagnosis is the
follow-on steering paper's subject. The reason this paper deploys a *gate*
(threshold-and-abstain) rather than a write is therefore scope, not impossibility: the
read-and-threshold pipeline is validated across four families and four sizes; the gated
write is validated on one model at one scale.

<!-- PLACEHOLDER SECTION (added 2026-07-20, PI-requested): drafted skeleton
only; expand after the Qwen3-4B family-atlas cell and the anisotropy-control
reanalysis resolve. Numbers below are traceable to the cited AMENDMENT.md
Outcomes; do not extend beyond them without those docs. -->

### 6.x Where the readout lives: a cross-family geometric regularity (placeholder)

Three families measured with the same capture-only atlas instrument
(`experiments/jspace-family-atlas`, `experiments/gemma-4-e4b-family-atlas`)
show one shape. The effective dimensionality of representation variance over
the epistemic pool peaks in the first 10-15% of depth (llama layer 4 of 28;
mistral layer 3 of 32; gemma hs 4 of 42) and collapses thereafter, while the
three epistemic contrasts -- the known-unknown (answerability) readout, the
caution contrast, and raw refusal -- become simultaneously linearly readable
(held-out AUROC >= 0.80) only after that collapse, across a wide mid-band
(llama 15-23, mistral 7-27, gemma 13-42). The registered prediction that
readability would coincide with a dimensionality peak (an interior
"workspace band") failed in all three families. Layer coordinates do not
transfer across families, but this decoupling motif has replicated three of
three times. The observation constrains where a deployed readout should be
fit (the compression regime, not the dimensionality peak) and is consistent
with the view that these readouts are late, low-dimensional summaries of an
already-made assessment rather than participants in a high-dimensional
deliberative workspace; the deflationary alternatives (prompt-set surface
diversity driving the early peak; mid-band anisotropy suppressing the
dimensionality estimator) are under active test and this section must not
be finalized until they resolve.

---

## 7. Limitations

We state these plainly; several are the reason specific claims are scoped as they are.

1. Seed coverage is partial. The pre-registered three-seed sampled-decoding
   replication (§4.10) makes the *cross-family* dial and veto magnitudes seed-robust, and
   quantifies their spread. The core Qwen3-4B deep-dive numbers (dial 0.834, veto deltas,
   the +0.065 post-beats-pre gain) remain seed 1: the near-saturated effects (gate 0.997)
   are low seed-risk, and §4.10's spread measurements bound how much the seed-sensitive
   axes move, but a multi-seed pass on the deep-dive checkpoint itself has not been run.
2. Base-model reads are render-sensitive, and the text baseline is high. The
   scoping worry that the axes might reflect upstream instruction tuning is closed by
   §4.11 (gate 0.997+ on four pre-instruction bases). What remains: base-model veto numbers
   depend on the prompt render (k-shot vs chat, 0.666 vs 0.867 on Qwen3.5-Base), and a
   question-surface TF-IDF baseline reads the gate pool at 0.964, so margins over that
   baseline, not raw AUROCs, are the honest effect sizes for the gate.
3. The dial ranks, it does not calibrate. ECE 0.151, a registered gate miss by 0.001
   (§3). We claim a *ranked* trust number, not a stated probability; a probability
   deliverable would need a downstream calibration map. The program has demonstrated such
   a map on the *gate* axis in a registered companion experiment (a trained head reaches
   cold-transfer AUROC 0.983 with ECE
   0.023; Appendix A); an equivalent calibrated head for the dial has
   not been built.
4. Structural hallucination label, decomposed but ungraded. "unanswerable question ∧
   model answered = hallucination" is structural, not human-graded. Two pre-registered
   follow-ups decomposed what the veto reads on that label (answer length and carried
   answerability, around a ~0.74 content core; §4.4). A PI-funded re-grade of this label
   (2026-07-18) has since partly closed that gap on the deployed checkpoint: it is severe
   and checkpoint-specific, 90.1% of Amendment U's labeled hallucination rows (109/121)
   were narrow-detector artifacts (trained refusals misread as answers), which reclassifies
   U-G3 as UNPOWERED (n=12/8 against a ≥50 floor). The same re-grade on the sibling
   lineages behind this paper's raw-base and cross-family numbers found forward flip rates
   of 0.05% (Amendment S; an instrument-agreement figure, since S has no unknown
   population), 2.36% (Amendment W), and 1.75–3.82–2.54% (Amendment X,
   1.7B/8B/14B), so those numbers stand uncorrected (corrigendum,
   `experiments/unified-two-signal-dial-veto/AMENDMENT.md`, 2026-07-18). A human-graded
   audit of a sample of the structural labels themselves, as opposed to a second detector,
   remains undone.
5. Cross-dataset reference in the veto, and carried answerability. The headline veto
   contrasts PopQA/TriviaQA *correct* against SelfAware *hallucinations*. The
   within-SelfAware control, reported pre-correction as 0.93 trained, is now 0.74–0.81
   under corrected hallucination labels (point estimates 0.7369–0.8140, CIs in §4.3;
   descriptive, unpowered; see Limitation 4 above; distinct from the §4.4 content-trust
   core 0.737, a raw-base number that stands)
   and bounds the dataset-shift concern more weakly than originally stated; it also shares
   the unanswerable-question structure, so it does not control answerability carry
   (§4.4). The answerability-controlled contrast exists at small scale (65 matched
   pairs, veto 0.737, single seed); a within-source, answerability-controlled
   correct-vs-hallucination contrast at headline scale has not been run.
6. Forced-answer surface. The dial is measured on forced or answer-encouraging prompts. Its
   behavior on the model's *own natural* (un-forced) answers is untested (the relevant surface
   for a live deployment) and is a known gap, not a solved case. The registered instrument
   for closing it is signed with locked gates but shelved unlaunched (Appendix A).
7. Correctness-axis causality is untested. The gate has causal (steering) evidence; the
   dial is correlational. Whether steering along the correctness axis moves actual correctness
   is future work.
8. Token-logprob baseline: computed, descriptive only. The dial is bounded below by a
   question-surface text baseline (0.75–0.78 per family, §4.11), and the cheapest internal
   competitor, the model's own token log-probabilities on the answer span, has now been
   computed in a pre-registered follow-up cell (dial-logprob-baseline, resolved
   2026-07-18). That cell hit its own pre-registered integrity stop: 30 of 3,324 rows
   (0.9%) failed the exact answer-span token round-trip by one BPE token each, because
   generation-time token IDs were never cached and re-tokenizing decoded text is not
   bit-stable at span boundaries. Its numbers are therefore descriptive with that caveat,
   not gated results. On the round-trip-clean rows: on the raw Instruct base, the
   length-normalized answer-span logprob reaches AUROC 0.8198 against the dial's 0.8338
   (margin +0.014, paired 95% CI [-0.011, +0.040], inside the cell's pre-stated ambiguous
   band), so sequence probability captures nearly all of the dial's separation there
   (Zenn and Geiping, 2026, predicted a real within-dataset signal; the cell's own
   pre-registered call of 0.60-0.72 for the base-arm logprob AUROC was wrong, and is
   recorded as such). On the deployed abstention-trained checkpoint, the logprob signal degrades to
   0.6608 while the dial holds 0.8183 (margin +0.158, CI [+0.122, +0.192]). The
   descriptive picture: the dial's clear margin over the model's own sequence probability
   appears on the deployed checkpoint, after abstention training reshapes output
   probabilities, not on the raw base. A gated version of this comparison needs a
   successor cell that caches generation-time token IDs; until then, what this paper
   establishes about the dial on the raw base remains its cross-model geometry, its
   post-answer read advantage, and its veto behavior, not that it beats the model's own
   logprobs there.

---

## 8. Conclusion

A small language model's trust signal does not have to be trained in: it is already present
in the representation and can be read out. An answerability **gate** at the prompt anchor
(AUROC ≈ 0.997) and a per-answer correctness **dial** after the answer (0.834, better after
the answer than before) compose into a two-stage pipeline that needs no fine-tuning, is
size-robust from 1.7B to 14B, replicates across four model families, and, by the
pre-registered pretrain-only contrast, is present *before any post-training at all*, readable
(descriptively) as far back as GPT-2-XL. The dial's **veto** on confident confabulation is
real and sharpened by targeted abstention training, but it is the
fragile, model-dependent piece: seed- and render-sensitive, non-monotonic in scale, the
one axis a vendor's own post-training moved the wrong way, and a blend rather than a pure
content read: controlled for answer length and question answerability, its content core
is about 0.74 (§4.4). Training's contribution, when it
is aimed at abstention specifically, is to sharpen that veto and install behavioral
abstention; post-training in general neither creates nor improves the underlying signal. The
confidence is already there from pretraining; the task is to read it, keep the two axes
separate, and know which model's veto you can trust.

What could still kill or shrink these claims is registered or stated. The dial has never
been read on the model's own un-forced answers; the shelved instrument in limitation 6
is the test, and a failure there would confine the dial to forced surfaces. The ~0.74
content core is a single-seed estimate that a multi-seed replication could pull below
its gates. The recall-not-truth critique (Cheang et al., 2025) predicts a class of
knowledge-associated wrong answers the dial would miss, and our decomposition has not
tested that class. And a fifth family could fail the veto outright, exactly as Llama did
under greedy decoding. The gate's saturation is the one number we would be surprised to
lose.

---

## References

- Azaria and Mitchell (2023). The Internal State of an LLM Knows When It's Lying. arXiv:2304.13734.
- Burns et al. (2022). Discovering Latent Knowledge in Language Models Without Supervision. arXiv:2212.03827.
- Cheang et al. (2025). Do LLMs Really Know What They Don't Know? Internal States Mainly Reflect Knowledge Recall Rather Than Truthfulness. arXiv:2510.09033.
- Cheng et al. (2024). Can AI Assistants Know What They Don't Know? arXiv:2401.13275.
- Cundy and Gleave (2025). Preference Learning with Lie Detectors can Induce Honesty or Evasion. arXiv:2505.13787.
- Ethayarajh et al. (2024). KTO: Model Alignment as Prospect Theoretic Optimization. arXiv:2402.01306.
- Feng et al. (2024). Don't Hallucinate, Abstain: Identifying LLM Knowledge Gaps via Multi-LLM Collaboration. arXiv:2402.00367.
- Ferrando et al. (2024). Do I Know This Entity? Knowledge Awareness and Hallucinations in Language Models. arXiv:2411.14257.
- Gani et al. (2026). Quantifying Faithful Confidence Expression in Large Reasoning Models. arXiv:2606.03969.
- Geifman and El-Yaniv (2019). SelectiveNet: A Deep Neural Network with an Integrated Reject Option. arXiv:1901.09192.
- Guo et al. (2017). On Calibration of Modern Neural Networks. arXiv:1706.04599.
- Gurnee et al. (2026). Verbalizable Representations Form a Global Workspace in Language Models. Transformer Circuits. https://transformer-circuits.pub/2026/workspace/index.html.
- He et al. (2023). Investigating Uncertainty Calibration of Aligned Language Models under the Multiple-Choice Setting. arXiv:2310.11732.
- Joshi et al. (2017). TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension. arXiv:1705.03551.
- Kadavath et al. (2022). Language Models (Mostly) Know What They Know. arXiv:2207.05221.
- Kirichenko et al. (2025). AbstentionBench: Reasoning LLMs Fail on Unanswerable Questions. arXiv:2506.09038.
- Kossen et al. (2024). Semantic Entropy Probes: Robust and Cheap Hallucination Detection in LLMs. arXiv:2406.15927.
- Kuhn et al. (2023). Semantic Uncertainty: Linguistic Invariances for Uncertainty Estimation in Natural Language Generation. arXiv:2302.09664.
- Li et al. (2023). Inference-Time Intervention: Eliciting Truthful Answers from a Language Model. arXiv:2306.03341.
- Lin et al. (2022). Teaching Models to Express Their Uncertainty in Words. arXiv:2205.14334.
- Liu et al. (2024). On the Universal Truthfulness Hyperplane Inside LLMs. arXiv:2407.08582.
- Liu et al. (2026). Reinforcement Learning with Metacognitive Feedback Elicits Faithful Uncertainty Expression in LLMs. arXiv:2606.32032.
- Mallen et al. (2022). When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories. arXiv:2212.10511.
- Manakul et al. (2023). SelfCheckGPT: Zero-Resource Black-Box Hallucination Detection for Generative Large Language Models. arXiv:2303.08896.
- Marks et al. (2023). The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets. arXiv:2310.06824.
- OpenAI (2023). GPT-4 Technical Report. arXiv:2303.08774.
- Orgad et al. (2024). LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations. arXiv:2410.02707.
- Rafailov et al. (2023). Direct Preference Optimization: Your Language Model is Secretly a Reward Model. arXiv:2305.18290.
- Rosenbaum (2026). Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model. Companion manuscript, released with this paper's research record (Appendix A).
- Shao et al. (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300.
- Shrivastava et al. (2023). Llamas Know What GPTs Don't Show: Surrogate Models for Confidence Estimation. arXiv:2311.08877.
- Slobodkin et al. (2023). The Curious Case of Hallucinatory (Un)answerability: Finding Truths in the Hidden States of Over-Confident Large Language Models. arXiv:2310.11877.
- Taparia et al. (2026). The Anatomy of Uncertainty in LLMs. arXiv:2603.24967.
- Tian et al. (2023). Just Ask for Calibration: Strategies for Eliciting Calibrated Confidence Scores from Language Models Fine-Tuned with Human Feedback. arXiv:2305.14975.
- Turner et al. (2023). Steering Language Models With Activation Engineering. arXiv:2308.10248.
- Ulmer et al. (2024). Calibrating Large Language Models Using Their Generations Only. arXiv:2403.05973.
- Wen et al. (2024). Know Your Limits: A Survey of Abstention in Large Language Models. arXiv:2407.18418.
- Xiao et al. (2025). Restoring Calibration for Aligned Large Language Models: A Calibration-Aware Fine-Tuning Approach. arXiv:2505.01997.
- Xiong et al. (2023). Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs. arXiv:2306.13063.
- Yang et al. (2023). Alignment for Honesty. arXiv:2312.07000.
- Yin et al. (2023). Do Large Language Models Know What They Don't Know?. arXiv:2305.18153.
- Yona et al. (2026). Hallucinations Undermine Trust; Metacognition is a Way Forward. arXiv:2605.01428.
- Zhang et al. (2023). R-Tuning: Instructing Large Language Models to Say "I Don't Know". arXiv:2311.09677.
- Zenn and Geiping (2026). When are Likely Answers Right? On Sequence Probability and Correctness in LLMs. arXiv:2606.27359.
- Zhu et al. (2023). On the Calibration of Large Language Models and Alignment. arXiv:2311.13240.
- Zou et al. (2023). Representation Engineering: A Top-Down Approach to AI Transparency. arXiv:2310.01405.

---

## Appendix A: Provenance and reproducibility

Every figure and number is generated from tracked result artifacts. Figures are produced by
`papers/paper-4-two-signal-readout/scripts/build_figures.py`, which reads the per-cell result JSONs directly:

| Result surface | Artifact (under `papers/paper-4-two-signal-readout/analysis/source-artifacts/probe/`) |
|---|---|
| Correctness dial, base model (§4.2) | `amendment_s_stage2_result.json` |
| Correctness dial, deployed checkpoint (§4.2) | `amendment_t_stage2_result.json` |
| Correctness-direction cross-checkpoint rotation, null result (§4.2) | `experiments/correctness-direction-rotation/AMENDMENT.md` (Outcome section; repo-root path, not under the probe dir) |
| Correctness discriminative-subspace overlap across checkpoints, null result (§4.2) | `experiments/correctness-subspace-overlap/AMENDMENT.md` (Outcome section; repo-root path, not under the probe dir) |
| Hallucination veto, deployed checkpoint (§4.3) | `amendment_u_two_signal_result.json` |
| Training-free whole mechanism, raw base (§4.6) | `amendment_w_base_model_result.json` |
| Cross-size sweep, 1.7B/8B/14B (§4.7) | `amendment_x_qwen3-{1.7b,8b,14b}-bnb-4bit_result.json` |
| Cross-family replication (§4.8) | `amendment_z_{llama-3.2-3b,ministral-3-3b,qwen3.5-4b,gemma-4-e4b}_result.json` |
| Pretrain-only bases + era ladder (§4.11) | `amendment_y_results/` (per-cell result JSONs + extraction manifest) |
| Sampled-decode seed-robustness (§4.10) | `experiments/sampled-decode-seed-robustness/artifacts/` (per family × seed JSONs `amendment_sr_{family}_seed{N}_result.json`; repo-root path, not under the probe dir) |
| Veto construct decomposition, residual-coverage + length-balanced confirmatory (§4.4) | `experiments/residual-catch-veto-coverage/` and `experiments/ap-veto-length-balanced-confirmatory/` (AMENDMENT.md outcome sections; repo-root paths) |
| SFT-rotation timeline diagnostic (§4.2) | `diag_item9_caution_timeline.py`, commit `a354ad73`; staging `professorsynapse/eh-al-prep-staging` tags `diag-item9-*-r3`; extraction commit `d5a90b3b` |
| J-lens workspace localization (§4.9) | `experiments/j-space-localization-qwen3-4b/analysis-committed/results/jspace-jlens-r1/` (`smoke_full.json`, `h1_full.json`, `profile_full.json`; repo-root path, not under the probe dir) |
| Gate-dial fusion diagnostic (§4.5) | repository PR #128 (Stage 1/1.5 CPU diagnostics), cited as prior fact in the veto experiment's signed design (`experiments/unified-two-signal-dial-veto/AMENDMENT.md` §1.1) |
| Warning-policy operating points (§5) | repository PR #205 analysis (declared-floor thresholds per checkpoint) |
| Cross-dataset gate transfer, KUQ → SelfAware (§5) | `experiments/xdataset-probe-transfer/` (repo-root path) |
| Latent-knowledge control package (§4.11) | `experiments/selfaware-latent-knowledge-controls/` (repo-root path) |
| Calibrated gate head (§7, limitation 3) | `experiments/aux-head-trainable-readout/` (repo-root path) |
| Natural-answer generalization instrument, signed and shelved (§7, limitation 6) | `experiments/natural-answer-generalization/` (repo-root path) |
| Companion manuscript (references) | `papers/paper-3-knows-but-doesnt-say/manuscript.md` (repo-root path) |

Governance: each result surface is a signed exploratory amendment under
`docs/protocols/` and `experiments/<slug>/` referencing the locked pre-registration; the cross-size and
cross-family confirmatories (`AMENDMENT-X-*`, `AMENDMENT-Z-*`) pre-stated their prediction,
falsifier, and gates before running, and their §7 verdicts record the outcome with bootstrap
CIs and no post-hoc goalpost changes; the pretrain-only contrast (`AMENDMENT-Y-*`)
pre-registered its primary hypothesis, falsifier, and the descriptive-only status of the era
ladder the same way. Extraction tensors and per-row artifacts remain local
(gitignored `*_tag/` subtrees); the tracked result JSONs carry the full per-layer AUROC
surfaces, CIs, and dial descriptives.

### Figure index

- **Figure 1.** Cross-family training-free readout: gate/dial/veto per family, veto-ascending,
  with CIs and the 0.65 pass / 0.50 chance lines. (`fig-p3-01-cross-family-readout.png`)
- **Figure 2.** Dial distribution per family: mean trust of correct / wrong / confident-
  confabulation groups, with the correct−hallucination gap annotated. (`fig-p3-02-dial-distribution.png`)
- **Figure 3.** The fragile axis: veto AUROC across Qwen3 sizes (left, non-monotonic, peaks
  8B) and across families (right, 3/4 pass). (`fig-p3-03-fragile-axis.png`)
- **Figure 4.** Correctness reads best after the answer: pre- vs post-generation dial AUROC by
  layer, base and deployed. (`fig-p3-04-post-beats-pre.png`)
- **Figure 5.** The veto exists untrained (raw-base AUROC 0.754, above the 0.65 pass bar);
  whether training sharpens it is unresolved under corrected labels: hallucination
  dial-mean 0.271 base vs 0.183/0.274 trained (descriptive, unpowered at n=12/8, no drop
  under Set B; originally reported 0.018). (`fig-p3-05-training-sharpens.png`)
- **Figure 6.** The deployable two-stage pipeline: gate (abstain) → generate → dial+veto
  (surface trust). (`fig-p3-06-pipeline.png`)
- **Figure 7.** Cross-family depth profile: gate vs dial per-layer AUROC against fractional
  depth, with argmax dots and within-tolerance span bars; descriptive, from the Amendment Z
  `auroc_surface` blocks. (`fig-p3-07-depth-profile.png`)
