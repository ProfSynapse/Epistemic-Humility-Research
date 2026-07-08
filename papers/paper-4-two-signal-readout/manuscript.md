# The Confidence Is Already There: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models

*Draft v0. Standalone contribution; it cites the companion diagnosis paper, [*Knows but
Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small
Language Model*](../paper-3-knows-but-doesnt-say/manuscript.md), for the representation-vs-
verbalization gap it builds on. All primary numbers are single-seed (seed 1) unless a
cross-model replication is named; provenance for every figure is in Appendix A.*

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
instruction-tuned base and compose into a deployable trust pipeline. An **answerability
gate**, read at the final prompt token *before* generation, separates answerable from
unanswerable questions at AUROC ≈ 0.997. A **correctness dial**, read at the final answer
token *after* generation, ranks whether the specific answer just produced is correct
(AUROC 0.834), and reads best *after* the answer rather than before it (+0.065, CI
excludes zero). The dial also **vetoes confident confabulation**: hallucinated answers to
unanswerable questions receive the lowest trust of any group (AUROC 0.980 after our
training; 0.754 on the raw base). Fusing the two axes into one scalar *hurts* (Δ −0.014),
so we deploy them as two sequential stages.

Four findings make this a mechanism rather than a curiosity. **(1) It is training-free:**
the whole pipeline reads off the raw instruction-tuned base with no adapter and no
abstention training of ours; our training only *sharpens* the veto (0.754 → 0.980), it
does not create the signal. **(2) It is size-robust:** the readout passes on every Qwen3
scale from 1.7B to 14B. **(3) It replicates across model families:** on four independent
families (Qwen, Llama, Mistral, Gemma) the gate and dial pass on all four (gate saturated
0.997–0.998; dial 0.82–0.86), establishing them as *family-general*. Under single greedy
decoding the veto split the families (strong on Gemma at 0.871, failing on Llama-3.2 at
0.633); a pre-registered three-seed sampled-decoding replication shows those greedy misses
were largely *decode artifacts*: under sampling the veto passes seed-stably on **all
four** families (family means 0.68–0.75), while confirming it as the *high-variance* axis:
across-seed spread reaches 0.12–0.15 per family (versus 0.01–0.04 for the dial) and
individual cells still dip below the bar. We report this as a co-headline: **a small LM's
sense of "can I answer this?" and "is this answer right?" is a universal, readable property
of the representation; its ability to distrust its own confident fabrications is present
across families but decode- and seed-sensitive, and it must be reported with seed spread
and validated per model.** We give the descriptive mechanism (the correct-vs-hallucination
gap in the dial distribution) that predicts where it is strong. **(4) It predates
post-training entirely:** a pre-registered contrast on four *pre-instruction* bases
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
questions, and the confidence they verbalize is nearly flat regardless of whether they are
right.

The natural first hypothesis is that this is an *ignorance* problem (the model does not
represent its own uncertainty) and the natural fix is *training*: fine-tune it to abstain,
or optimize a preference/reward signal toward calibrated confidence. Our companion
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
from linear readouts of a frozen model, with two contributions over the diagnosis:

1. **A second axis.** Answerability ("*can* this be answered?") is not the same as
   correctness ("is *this answer* right?"). We show correctness is *also* linearly
   readable, at a different token position (after the answer, not before it), and that the
   two axes are orthogonal: separable enough that combining them into one number degrades
   both. This yields a two-stage pipeline: a **gate** that abstains on unanswerable
   questions, and a **dial** that surfaces a trust number on what is answered.

2. **A generality claim.** The diagnosis was one model, one family. We show the readout
   is training-free (reads off the raw instruction-tuned base), size-robust (1.7B–14B), and
   replicates across four model families. Honestly, we also show *which part* generalizes.
   The gate and dial are family-general. The veto (the dial's ability to assign confident
   confabulation the lowest trust) is the fragile, model-dependent axis. We treat this as
   a co-headline finding, not a footnote, and give the descriptive quantity that predicts
   it.

The framing throughout is *readout, not training*. Our training does not create the trust
signal; it sharpens one part of it (the veto) and installs behavioral abstention. The
implication for practitioners is concrete: a useful, thresholdable trust number for a small
LM is available *today*, from a model you already have, with a cheap linear probe, and no
fine-tuning run is required.

---

## 2. Related work

**Verbalized confidence and calibration.** A line of work asks models to state their
confidence in words or tokens and measures its calibration (Lin et al., 2022; Xiong et
al., 2023); the recurring finding is that
verbalized confidence is poorly calibrated and often flat, especially for smaller models.
Recent faithful-uncertainty work makes the target sharper by asking whether expressed
uncertainty tracks intrinsic uncertainty, and shows that metacognitive RL can improve
that output metric (Gani et al., 2026; Liu et al., 2026; Yona et al., 2026).
Our companion diagnosis localizes *why* in this model family: the internal estimate is
calibrated, the emitted token is not, and the loss on that token does not transmit the
internal estimate faithfully. This paper is the constructive complement: bypass the token.

**Probing internal states / latent knowledge.** A large body of work reads factual and
truth-related structure out of hidden activations with linear probes, for example
truthfulness directions (Burns et al., 2022; Marks et al., 2023) and P(True)-style
self-evaluation (Kadavath et al., 2022). Two points differentiate what we do. First, we
separate *answerability* (a property of the question, read before generation) from
*per-answer correctness* (a property of the produced answer, read after it), and show they
are distinct axes at distinct token positions. Second, we find that correctness reads
*better after the answer than before it*, a post-generation self-evaluation effect, and
we quantify the gain.

**Abstention and selective prediction.** Selective-prediction methods learn or threshold a
confidence to abstain (Wen et al., 2024). Our gate is a selective-prediction front-end, but the emphasis is
that it needs no training to install: it is a threshold on an axis the base model already
carries. This connects to hallucination-detection work (Orgad et al., 2024); our veto is a
hallucination
detector expressed inside the same correctness axis rather than as a separate module.

**Steering and representation engineering.** Reading a direction out of activations is one
half of representation engineering (Zou et al., 2023); writing along it (steering) is the
other (Turner et al., 2023). This paper is
strictly the *reading* half. The companion diagnosis shows the answerability/caution axis
is causally steerable but only *asymmetrically* (excess caution can be relaxed; missing
caution cannot be installed by steering). We cite that result as motivation for a follow-on
steering study, and as the reason we deploy the readout as a gate rather than as a steering
intervention here.

---

## 3. Setup

**Models.** The core mechanism is developed on Qwen3-4B in two conditions: the raw
instruction-tuned base (`unsloth/Qwen3-4B-bnb-4bit`, no adapter) and our deployed
checkpoint (clean supervised fine-tune → GRPO). The size study uses the raw Qwen3 bases at
1.7B / 4B / 8B / 14B. The cross-family study uses four ungated instruction-tuned bases at
comparable scale (Llama-3.2-3B, Ministral-3-3B, Qwen3.5-4B, and Gemma-4-E4B), read
training-free, exactly as the base-model condition.

**Data and labels.** Answerable questions come from PopQA (Mallen et al., 2022) and
TriviaQA (Joshi et al., 2017), graded against gold
answer aliases into *correct* / *wrong*. Intrinsic answerable-vs-unanswerable structure and
the hallucination class come from SelfAware (Yin et al., 2023): questions it marks unanswerable, when the model
answers them anyway, are labeled *hallucinations* (a structural label: the model produced
a confident answer to a question with no answer). This gives three groups for the
correctness axis: correct answers, wrong answers, and confident confabulations.

**Readout recipe.** For each item we run a single forward pass over the concatenated
[prompt + answer] sequence and cache residual-stream activations at every layer at two
positions: the **last prompt token** (the *pre-generation anchor*, used for the gate) and
the **last answer content token** (the *post-generation* position, used for the dial).
Probes are standardized logistic regressions (StandardScaler + LogisticRegression, C=1.0);
reference scores are 5-fold stratified out-of-fold AUROC with a 2000-sample bootstrap
confidence interval. When a dial fit on one condition is evaluated on another, it is applied
*cold* (fit on the source, scored on the target, no refitting). Decoding is greedy
(deterministic). Each cell enforces a data-adequacy floor (≥30 wrong answers and ≥50
hallucinations) before a probe verdict is reported.

**Gates (pre-registered).** Every cross-model cell was pre-registered with three identical
gates and a locked success rule, before running: the gate (G1), dial (G2), and veto (G3)
readouts must each reach AUROC ≥ 0.65 with a bootstrap CI excluding 0.50; the veto (G3) is
the primary endpoint. For the cross-family confirmatory, SUCCESS was pre-defined as the veto
passing on ≥3 of 4 families, with the falsifier being a veto failure on ≥2 of 4. Scaling
sharpness was declared descriptive-only in advance. No goalpost was moved after any result.

---

## 4. Results

### 4.1 The answerability gate reads off the anchor, before generation

At the last prompt token, before any answer is generated, a linear probe separates
answerable from unanswerable questions at **AUROC 0.997** on the raw Qwen3-4B base. This is
the readable form of the internal estimate the diagnosis identified: the model represents
"can this be answered?" at the moment it is about to answer, and the representation is
almost perfectly separable. Thresholding this axis gives an abstention gate that needs no
training to install. As the cross-model results below show, this axis is the most robust of
the three: it is near-saturated (0.997–0.998) on every size and every family we tested.

### 4.2 The correctness dial reads off the answer, and reads better *after* it

Answerability is a property of the question. Whether a *specific produced answer* is correct
is a different property, and it is legible at a different place. A linear probe at the last
answer token ranks correct-vs-wrong answers at **AUROC 0.834** on the Qwen3-4B base
(layer 20). Critically, reading *after* the answer beats reading *before* it: the
post-generation position scores **+0.065** over the pre-generation position (CI [0.040,
0.090], excludes zero). The model's representation of "was that right?" is sharper once it
has committed to the answer than at the moment it begins: a self-evaluation effect
localized to token position, and one that peaks in the middle of the network rather than at
the final layer (Figure 4).

The dial survives deployment. On our clean-SFT → GRPO checkpoint the same post-generation
readout scores **AUROC 0.819** (layer 22), with the same post-beats-pre ordering
(post 0.819 vs pre 0.745). A dial *fit on the base* and applied *cold* to the deployed
checkpoint transfers only partially (0.679): the correctness *direction* drifts under
training even though the *readout* remains strong when refit. The axis exists on both
checkpoints, but the probe should be refit per checkpoint rather than transported.

Exploratory lab-notebook diagnostics locate the source of this drift for the
answerability readout specifically. Tracking the known-vs-unknown direction across
four training stages in a shared basis (raw base, clean-SFT, GRPO-v2, GRPO-par-true),
the readout is already at full strength in the raw base (mid-to-late CV AUROC mean
0.951) and no stage sharpens it (clean-SFT 0.922, GRPO-v2 0.923, GRPO-par-true 0.926),
consistent with the training-free reading in §4.5. The direction, however, rotates
once and near-orthogonally at instruction SFT (raw-to-clean-SFT cosine falling to
0.06-0.25 across mid and late layers) and is then ridden almost unchanged by both
GRPO variants (clean-SFT-to-GRPO-v2 cosine 0.91-0.997). The per-checkpoint refit is
therefore required by a single SFT rotation event, not gradual accumulation across
training, which is why cold transport degrades while a refit probe stays strong. This
is exploratory internal evidence (script `diag_item9_caution_timeline.py`, commit
`a354ad73`; staging `professorsynapse/eh-al-prep-staging` tags `diag-item9-*-r3`;
extraction commit `d5a90b3b`), reported separately from and never pooled with the
locked headline numbers.

One honest caveat carried from the start: the dial *ranks* correctness well (AUROC) but is
not a calibrated *probability* (ECE 0.151 on the base). For a thresholdable trust number,
ranking is the operative property; a stated probability would need a downstream calibration
map. We claim the ranking, not the probability.

### 4.3 The dial vetoes confident confabulation

The same correctness dial, applied to the hallucination group (confident answers to
unanswerable questions), assigns them the **lowest trust of any group**: veto AUROC
**0.980** on the deployed checkpoint (correct vs hallucination), with a within-SelfAware
control (known-answered vs unknown-answered, same dataset) of **0.93** that rules out a
mere dataset-shift artifact. Confident confabulation does *not* read like a correct answer
to the dial. This is the property that makes the dial a hallucination *veto* and not merely
a correctness *ranker*: the failure mode we most want to catch (fluent, confident, wrong)
is exactly the one the dial pushes to the bottom.

Figure 2 shows the mechanism directly: the dial-mean of the hallucination group sits far
below the correct group, and the size of that separation is what the veto AUROC measures.

### 4.4 The two axes are orthogonal: a pipeline, not a fused scalar

Gate (answerability, at the anchor) and dial (correctness, post-generation) are separable
axes. When we fuse the two scalars into a single combined trust number, correctness ranking
*degrades* (Δ **−0.014**). The axes carry complementary information that a single number
destroys. The deployment consequence is to keep them as **two sequential stages** rather
than one score (Figure 6):

- **Stage 1: Gate.** At the prompt anchor, threshold the answerability axis. If below
  threshold, abstain ("I don't know") and stop.
- **Stage 2: Dial + veto.** For questions that pass the gate, generate the answer, then read
  the correctness dial at the post-answer token and surface it as the trust number.
  Confident confabulations that slipped the gate are caught here as lowest-trust.

### 4.5 The whole mechanism is training-free: training *sharpens*, it does not *create*

Every result above reproduces on the **raw** Qwen3-4B instruction-tuned base, with no
adapter and no abstention training of ours: gate **0.997**, dial **0.834**, veto **0.754**.
Both the gate and the dial pass unchanged; the veto is present and above chance on the raw
base. What our training buys is *sharpening the veto*, not creating the mechanism: the veto
climbs from **0.754 → 0.980** (+0.226 AUROC), and the mean trust the dial assigns to
confident confabulations drops from **0.271** on the base to **0.018** after training:
the trained model reads its own hallucinations as near-zero trust. Training adds essentially
nothing to the gate (already saturated) and installs autonomous behavioral abstention, but
the *readable trust signal itself* is a property of the frozen representation (Figure 5).

We scope "training-free" precisely: the raw base is the *instruction-tuned* release, so
"training-free" means "no abstention fine-tuning and no reinforcement learning of ours,"
**not** "no training ever." At the time this section's numbers were produced, the
answerability axis could in principle have been a product of upstream instruction tuning;
§4.9's pre-registered pretrain-only contrast closes that question directly: read on
*pre-instruction* bases, the axis is already there. The claim here is narrower and stands on
its own: *our* training regimen (the one the companion paper shows cannot close the
verbalization gap) is not what puts the readable signal there.

### 4.6 The readout is size-robust (1.7B–14B)

Across the Qwen3 family at 1.7B, 4B, 8B, and 14B, the training-free readout passes all three
gates at every size. The gate stays saturated (~0.997) throughout. The veto, however, does
*not* improve monotonically with scale: it is 0.757 at 1.7B, 0.754 at 4B, peaks at
**0.846 at 8B**, and *dips* to **0.741 at 14B**. The "bigger sharpens the veto" expectation
is not supported, an observation we flagged as descriptive in advance and did not promote
to a claim. The veto being the axis that wobbles with scale is the first sign that it, and
not the gate or dial, is the fragile part of the mechanism (Figure 3, left).

### 4.7 Cross-family: the gate and dial are universal; the veto is model-dependent

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

**The gate and dial pass on all four families.** The gate is near-saturated everywhere
(0.997–0.998); the dial ranges 0.818–0.861. These two axes are *family-general*: the ability
to read "can I answer this?" at the anchor and "is this answer right?" after the answer is
not a Qwen idiosyncrasy; it is a property of instruction-tuned small LMs across four
independent lineages.

**The veto replicates but is fragile.** It passes cleanly on Gemma (0.871) and Mistral
(0.733), marginally on Qwen3.5 (0.666: point above the bar, CI lower bound 0.634 dipping
just under it), and *fails* on Llama (0.633: a real signal, CI excludes chance, but below
the 0.65 bar). Catching *confident* hallucination is the model-dependent capability, exactly
as the non-monotonic size result foreshadowed.

**The descriptive mechanism.** The split is explained by the correct-vs-hallucination gap in
the dial's own distribution (Figure 2). Where a model's confident confabulations read as
low-trust, the veto works; where they read almost as trustworthy as correct answers, it
fails:

- **Gemma (veto 0.871):** hallucination dial-mean 0.089 vs correct 0.593, the widest split;
  confabulations read as near-zero trust.
- **Mistral (0.733):** 0.278 vs 0.605, a clean separation.
- **Qwen3.5 (0.666):** 0.425 vs 0.636, intermediate.
- **Llama (0.633):** 0.476 vs 0.707: confident confabulations read *almost as trustworthy
  as correct answers*, so the dial cannot separate them.

Ordering families by the dial-mean gap (Gemma 0.504 > Mistral 0.327 > Qwen3.5 0.211 ≈ Llama
0.231) tracks the veto verdicts directionally. We flag one honest wrinkle: Llama's mean gap
(0.231) slightly *exceeds* Qwen3.5's (0.211), yet Llama fails and Qwen3.5 marginally passes,
because the veto AUROC depends on the full distribution overlap, not the mean gap alone. We
therefore read the gap as a *directional* predictor, not a strict rank. The stable
conclusion stands: **gate + dial are family-general (4/4); the veto replicates (3/4 under
this single greedy decode) and is the fragile axis**, though §4.8 shows the two greedy
misses are largely decode artifacts: under sampled decoding the veto passes seed-stably on
all four families.

**Where the two signals live in depth (descriptive).** The same Amendment Z runs carry the
full per-layer AUROC surface for the gate and the dial, and plotting them against fractional
depth (layer / n_layers, since the four families have 28, 26, 32, and 42 blocks) shows the
two signals occupy different parts of the network (Figure 7). The gate is not a
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
already-reported Amendment Z surfaces: no new claim and no gate rests on it.

> **Figure 7. Cross-family depth profile of the two signals.** Per-layer AUROC for the
> answerability gate (left, zoomed y-axis) and the correctness dial (right) against
> fractional depth, one line per family; dots mark each family's argmax layer and the bars
> under each panel mark its within-tolerance span (gate: within 0.005 of max; dial: within
> 0.02). The gate saturates by ~20% of depth and stays saturated to the last block in all
> four families, so per-family best-layer differences are jitter on a plateau; the dial
> concentrates in an overlapping mid-to-late band, with Llama's argmax at L25/28 near the
> unembedding. Descriptive only, from the Amendment Z `auroc_surface` blocks.
> (`fig-p3-07-depth-profile.png`)

### 4.8 Seed-robustness: the greedy veto misses were decode artifacts

Every number in §4.7 comes from a single deterministic decode (greedy). A deployment
samples. We therefore pre-registered a seed-robustness confirmatory: the identical
training-free readout on the same four families under **sampled decoding** (temperature 0.7,
top-p 0.9) across **three seeds**, with the same per-cell gates and adequacy floors. The
gate was pre-declared decode-invariant (it reads the prompt anchor, which sampling never
touches) and emitted as an invariance check only; the dial and veto (both read from
*sampled* answers) were the endpoints. Success required the dial seed-stable on 4/4
families, the veto seed-stable on ≥3/4, and the per-seed veto majority never dropping below
3/4 on any single seed.

**Table 2. Sampled-decode seed-robustness (AUROC per seed; mean [min–max] across 3 seeds).**

| Model | Dial (3 seeds) | Veto (3 seeds) | Veto seed-stable? | Greedy veto (§4.7) |
|---|---|---|---|---|
| Llama-3.2-3B | 0.848 [0.827–0.865], 3/3 pass | **0.739 [0.684–0.801], 3/3 pass** | **YES** | 0.633 (FAIL) |
| Ministral-3-3B | 0.806 [0.799–0.812], 3/3 pass | 0.681 [0.606–0.742], 2/3 pass | **YES** | 0.733 (pass) |
| Qwen3.5-4B | 0.852 [0.830–0.864], 3/3 pass | **0.753 [0.659–0.807], 3/3 pass** | **YES** | 0.666 (marginal) |
| Gemma-4-E4B | 0.817 [0.802–0.839], 3/3 pass | **0.742 [0.718–0.762], 3/3 pass** | **YES** | 0.871 (pass) |

**The two greedy veto misses flip to passes under sampling.** Llama, the one clean veto
*failure* in §4.7 (0.633), passes on **all three seeds** under sampled decoding (0.684–
0.801). Qwen3.5, the marginal pass whose CI dipped below the bar, passes all three seeds
cleanly. The §4.7 "fragile veto" split is therefore partly a *decode* artifact, not purely a
model property: a single greedy trajectory produces one specific set of confabulations, and
Llama's greedy confabulations happened to read as trustworthy; its sampled ones do not.
Single-decode point estimates *understated* the veto.

**The veto is seed-sensitive per cell, seed-stable per family.** Across-seed spread on the
veto is real (Llama range 0.12, Qwen3.5 0.15, Ministral 0.14, Gemma 0.04, versus dial
spreads of 0.01–0.04), and Ministral drops below the bar on one seed (0.606 on seed 1, its
only failing cell). Per-cell veto numbers should accordingly be reported with seed spread,
not as point estimates. At the family level the verdict is stable: **all four families are
seed-stable veto passes.**

**The gate is decode-invariant, as pre-declared.** Across all completed cells the gate sits
at 0.996–0.999 with a per-family across-seed range under 0.003: sampling the answer does
not move an axis read before the answer exists.

**Pre-registered verdict: SUCCESS.** All three locked clauses pass: (a) the dial is
seed-stable on **4/4** families (every one of the 12 cells passes the dial bar); (b) the
veto is seed-stable on **4/4** families (Llama and Qwen3.5 and Gemma 3/3 each, Ministral
2/3); (c) the per-seed veto majority never drops below 3/4: seed 20260701, the pinch seed
where Ministral fails, clears at 3/4 on Gemma's 0.762 pass, and seeds 20260702/20260703 sit
at 4/4. The falsifier (a seed with majority < 3/4, or ≥2 families flipping veto status) did
not fire: Ministral is the only status-flipping family. The Table 1 magnitudes are thereby
promoted from "single greedy decode" to **seed-robust under sampled decoding**
(pre-registration and per-cell provenance: `AMENDMENT-SR-sampled-decode-seed-robustness.md`).

### 4.9 The signal predates post-training: pretrain-only bases and an era ladder

Every base so far (including every "raw" base in §§4.5–4.8) is a vendor *post-trained*
instruct release, so all of the above is compatible with the signal being installed by
instruction tuning. We pre-registered the contrast that separates the hypotheses: the
identical three-signal readout on four **pre-instruction** bases matched to the §4.7
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

**H1 SUPPORTED 4/4; the falsifier fired on 0/4 pairs.** Every pre-instruction base reads
the gate at 0.997+, indistinguishable from the instruct releases. The veto also clears its
bar on all four bases (0.666–0.874). The boundary signal is not installed by post-training;
it is already in the pretrained representation, and instruction tuning at most re-renders it.

**Post-training does not sharpen the readout, and can dull it.** The one clean
base→instruct pair read under a single pipeline (Olmo-3, same seed, scorer, and render
class) moves the veto **0.803 → 0.731** and the within-SelfAware control 0.791 → 0.674;
the render-confounded cross-run pairs sit at or below their bases too. This resolves the
tension with §4.5's "training sharpens" result: what sharpened the Qwen3-4B veto
(0.754 → 0.980) was *targeted abstention training*, not post-training per se. Generic
vendor post-training adds nothing to any of the three axes and moved the fragile one the
wrong way, consistent with §4.6's non-monotonic scale result.

**Part of the veto's fragility is the prompt surface, not the model.** The dual-render
control shows Qwen3.5-Base's veto is render-sensitive (k-shot 0.666 vs chat-render 0.867)
while its gate is render-invariant (0.998 under both). Per-model veto validation (§4.7's
practitioner rule) should therefore fix the render before comparing numbers.

**An era ladder, strictly descriptive.** Read the same panel down a ladder of historical
bases and all three readouts stay above the 0.65 bar as far back as **GPT-2-XL (2019)**
(gate 0.9911, dial 0.7940, veto 0.7936); Pythia-2.8B, Llama-2-7B, and OLMo-2-7B fill the
rungs to the modern bases. The raw gate is nearly era-flat (0.991 → 0.998); what improves
across eras is the *within-SelfAware* control (~0.59 on GPT-2/Pythia rising to ~0.71–0.82
from Llama-2 onward): the in-distribution separation of confident hallucinations from
known answers, not the gross answerable/unanswerable split. No era claim is minted from
this arm; it was registered as descriptive.

**A text baseline bounds all of the above.** A TF-IDF classifier on the question surface
alone reads the gate pool at **0.964 ± 0.016** and predicts dial correctness at 0.75–0.78
per family. The hidden-state readouts sit above these bounds (gate 0.991–0.998, dial
0.79–0.87), but the *margins*, not the raw AUROCs, are the honest effect sizes: much of
the gate is surface-predictable on SelfAware, on any model of any era. (Pre-registration
and per-cell provenance: `AMENDMENT-Y-pretrain-only-base-readout.md`;
`experiment/phase1/probe/amendment_y_results/`.)

---

## 5. The deployable pipeline

Putting the pieces together (Figure 6), a small LM can carry a training-free trust
mechanism with no fine-tuning:

1. **Gate (pre-generation).** Read the answerability axis at the prompt anchor. Below
   threshold → abstain. This is the most robust component (0.997–0.998 everywhere).
2. **Dial (post-generation).** For gated-through questions, generate, then read the
   correctness axis at the post-answer token and surface it as a *ranked* trust number.
3. **Veto (within the dial).** Confident confabulations that pass the gate are pushed to
   the bottom of the dial. The veto passes seed-stably on all four families under sampled
   decoding (§4.8), but it is the high-variance axis (individual decodes/seeds can dip
   below the bar), so validate it per model and per decode configuration before relying on
   the dial's confabulation-catching; the gate remains the primary defense.

Two engineering notes fall out of the results. Keep the axes *separate*: fusing them costs
correctness ranking (§4.4). And *refit the dial per checkpoint*: the correctness direction
drifts under training (cold transfer 0.679, §4.2) even though the axis persists. The gate,
by contrast, transports well and is cheap to install anywhere.

---

## 6. Discussion

**Epistemic state is largely a readout, not a training outcome.** The companion diagnosis
showed the internal answerability estimate is calibrated while the emitted one is flat, and
that our training cannot reconcile them through the confidence token. This paper's
constructive result is the other side of that coin: because the signal is *in the
representation*, it can be *read* even when it cannot be *trained into the token*. The most
useful part of epistemic humility for a small model (a thresholdable "should I answer, and
how much should you trust this?") is available from a frozen model with a linear probe.

**What training is for.** Our training is not wasted, but its role is narrow and specific: it
*sharpens the veto* (0.754 → 0.980) and installs autonomous behavioral abstention. It does
not create the gate, the dial, or the veto, and §4.9 sharpens the negative half further:
the signal predates not just our training but *any* post-training (gate 0.997+ on four
pre-instruction bases), and generic vendor post-training does not sharpen the readout either
(the clean Olmo-3 base→instruct pair moves the veto 0.803 → 0.731). Sharpening is a property
of *targeted* abstention training, not of post-training in general. This reframes the
calibration-training question: the goal is not to teach the model what it knows (pretraining
already put that there), but to make its *behavior* and its *emitted signal* faithful to what
it already represents; and, for the veto specifically, to sharpen a signal that is present
but weak on some models out of the box.

**Universal axes vs a high-variance capability.** The cleanest scientific result is the
split. "Can I answer this?" and "is this answer right?" are readable across four families
and four sizes; they look like general properties of instruction-tuned small LMs. "Can I
distrust my own confident fabrication?" is present across the same families (seed-stable
4/4 under sampled decoding, §4.8) but far noisier: strong on Gemma, decode- and
seed-sensitive elsewhere (Llama's greedy failure flipped to three sampled passes), and
non-monotonic in scale. This is an actionable map for practitioners (the gate is safe to
rely on anywhere; the veto must be validated per model and reported with seed spread) and a
pointed question for future mechanistic work (why do some models' confabulations read as
low-trust to their own correctness axis on any decode, while others' depend on which
confabulation the decoder happens to produce?).

**Why not just steer?** The companion diagnosis found the answerability axis is causally
steerable, but *asymmetrically*: excess caution can be relaxed, missing caution cannot be
installed by steering. That asymmetry is why we deploy a *gate* (threshold-and-abstain) rather
than a steering intervention here: reading the axis and acting on the read is robust, whereas
writing missing caution into the model is not. Turning the readout around into a causal
*write* is the subject of the follow-on study.

---

## 7. Limitations

We state these plainly; several are the reason specific claims are scoped as they are.

1. **Seed coverage is partial.** The pre-registered three-seed sampled-decoding
   replication (§4.8) makes the *cross-family* dial and veto magnitudes seed-robust, and
   quantifies their spread. The core Qwen3-4B deep-dive numbers (dial 0.834, veto deltas,
   the +0.065 post-beats-pre gain) remain seed 1: the near-saturated effects (gate 0.997)
   are low seed-risk, and §4.8's spread measurements bound how much the seed-sensitive
   axes move, but a multi-seed pass on the deep-dive checkpoint itself has not been run.
2. **Base-model reads are render-sensitive, and the text baseline is high.** The original
   scoping worry (that the axes might reflect upstream instruction tuning) is closed by
   §4.9 (gate 0.997+ on four pre-instruction bases). What remains: base-model veto numbers
   depend on the prompt render (k-shot vs chat, 0.666 vs 0.867 on Qwen3.5-Base), and a
   question-surface TF-IDF baseline reads the gate pool at 0.964, so margins over that
   baseline, not raw AUROCs, are the honest effect sizes for the gate.
3. **The dial ranks, it does not calibrate.** ECE 0.151. We claim a *ranked* trust number,
   not a stated probability; a probability deliverable would need a downstream calibration map.
4. **Structural hallucination label.** "unanswerable question ∧ model answered =
   hallucination" is structural, not human-graded. A graded audit of a sample would harden the
   veto's construct validity.
5. **Cross-dataset reference in the veto.** The veto contrasts PopQA/TriviaQA *correct* against
   SelfAware *hallucinations*. The within-SelfAware control (0.93 trained) bounds the
   dataset-shift concern but does not eliminate it; a within-source correct-vs-hallucination
   contrast would close it.
6. **Forced-answer surface.** The dial is measured on forced or answer-encouraging prompts. Its
   behavior on the model's *own natural* (un-forced) answers is untested (the relevant surface
   for a live deployment) and is a known gap, not a solved case.
7. **Correctness-axis causality is untested.** The gate has causal (steering) evidence; the
   dial is correlational. Whether steering along the correctness axis moves actual correctness
   is future work.

---

## 8. Conclusion

A small language model's trust signal does not have to be trained in: it is already present
in the representation and can be read out. An answerability **gate** at the prompt anchor
(AUROC ≈ 0.997) and a per-answer correctness **dial** after the answer (0.834, better after
the answer than before) compose into a two-stage pipeline that needs no fine-tuning, is
size-robust from 1.7B to 14B, replicates across four model families, and, by the
pre-registered pretrain-only contrast, is present *before any post-training at all*, readable
(descriptively) as far back as GPT-2-XL. The dial's **veto** on confident confabulation is
real and, once sharpened by targeted abstention training, strong (0.980), but it is the
fragile, model-dependent piece: seed- and render-sensitive, non-monotonic in scale, and the
one axis a vendor's own post-training moved the wrong way. Training's contribution, when it
is aimed at abstention specifically, is to sharpen that veto and install behavioral
abstention; post-training in general neither creates nor improves the underlying signal. The
confidence is already there from pretraining; the task is to read it, keep the two axes
separate, and know which model's veto you can trust.

---

## References

- Burns et al. (2022). Discovering Latent Knowledge in Language Models Without Supervision. arXiv:2212.03827.
- Ethayarajh et al. (2024). KTO: Model Alignment as Prospect Theoretic Optimization. arXiv:2402.01306.
- Gani et al. (2026). Quantifying Faithful Confidence Expression in Large Reasoning Models. arXiv:2606.03969.
- Joshi et al. (2017). TriviaQA: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension. arXiv:1705.03551.
- Kadavath et al. (2022). Language Models (Mostly) Know What They Know. arXiv:2207.05221.
- Lin et al. (2022). Teaching Models to Express Their Uncertainty in Words. arXiv:2205.14334.
- Liu et al. (2026). Reinforcement Learning with Metacognitive Feedback Elicits Faithful Uncertainty Expression in LLMs. arXiv:2606.32032.
- Mallen et al. (2022). When Not to Trust Language Models: Investigating Effectiveness of Parametric and Non-Parametric Memories. arXiv:2212.10511.
- Marks et al. (2023). The Geometry of Truth: Emergent Linear Structure in Large Language Model Representations of True/False Datasets. arXiv:2310.06824.
- Orgad et al. (2024). LLMs Know More Than They Show: On the Intrinsic Representation of LLM Hallucinations. arXiv:2410.02707.
- Rafailov et al. (2023). Direct Preference Optimization: Your Language Model is Secretly a Reward Model. arXiv:2305.18290.
- Rosenbaum (2026). Knows but Doesn't Say: A Training-Resistant Gap Between Internal and Stated Confidence in a Small Language Model. Companion draft, this repository: [papers/paper-3-knows-but-doesnt-say/manuscript.md](../paper-3-knows-but-doesnt-say/manuscript.md).
- Shao et al. (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300.
- Turner et al. (2023). Steering Language Models With Activation Engineering. arXiv:2308.10248.
- Wen et al. (2024). Know Your Limits: A Survey of Abstention in Large Language Models. arXiv:2407.18418.
- Xiong et al. (2023). Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs. arXiv:2306.13063.
- Yin et al. (2023). Do Large Language Models Know What They Don't Know?. arXiv:2305.18153.
- Yona et al. (2026). Hallucinations Undermine Trust; Metacognition is a Way Forward. arXiv:2605.01428.
- Zou et al. (2023). Representation Engineering: A Top-Down Approach to AI Transparency. arXiv:2310.01405.

---

## Appendix A: Provenance and reproducibility

Every figure and number is generated from tracked result artifacts. Figures are produced by
`papers/paper-4-two-signal-readout/scripts/build_figures.py`, which reads the per-cell result JSONs directly:

| Result surface | Artifact (under `experiment/phase1/probe/`) |
|---|---|
| Correctness dial, base (S) | `amendment_s_stage2_result.json` |
| Correctness dial, deployed (T) | `amendment_t_stage2_result.json` |
| Hallucination veto, deployed (U) | `amendment_u_two_signal_result.json` |
| Training-free whole mechanism (W) | `amendment_w_base_model_result.json` |
| Cross-size 1.7B/8B/14B (X) | `amendment_x_qwen3-{1.7b,8b,14b}-bnb-4bit_result.json` |
| Cross-family (Z) | `amendment_z_{llama-3.2-3b,ministral-3-3b,qwen3.5-4b,gemma-4-e4b}_result.json` |
| Pretrain-only bases + era ladder (Y) | `amendment_y_results/` (10 per-cell result JSONs + extraction manifest) |

Governance: each result surface is a signed exploratory amendment under
`experiment/protocol/` referencing the locked pre-registration; the cross-size and
cross-family confirmatories (`AMENDMENT-X-*`, `AMENDMENT-Z-*`) pre-stated their prediction,
falsifier, and gates before running, and their §7 verdicts record the outcome with bootstrap
CIs and no post-hoc goalpost changes; the pretrain-only contrast (`AMENDMENT-Y-*`)
pre-registered its primary hypothesis, falsifier, and the descriptive-only status of the era
ladder the same way. Extraction tensors and per-row artifacts remain local
(gitignored `*_tag/` subtrees); the tracked result JSONs carry the full per-layer AUROC
surfaces, CIs, and dial descriptives.

**Figure index.**

- **Figure 1.** Cross-family training-free readout: gate/dial/veto per family, veto-ascending,
  with CIs and the 0.65 pass / 0.50 chance lines. (`fig-p3-01-cross-family-readout.png`)
- **Figure 2.** Dial distribution per family: mean trust of correct / wrong / confident-
  confabulation groups, with the correct−hallucination gap annotated. (`fig-p3-02-dial-distribution.png`)
- **Figure 3.** The fragile axis: veto AUROC across Qwen3 sizes (left, non-monotonic, peaks
  8B) and across families (right, 3/4 pass). (`fig-p3-03-fragile-axis.png`)
- **Figure 4.** Correctness reads best after the answer: pre- vs post-generation dial AUROC by
  layer, base and deployed. (`fig-p3-04-post-beats-pre.png`)
- **Figure 5.** Training sharpens the veto: veto AUROC 0.754 → 0.980 and hallucination
  dial-mean 0.271 → 0.018, base vs trained. (`fig-p3-05-training-sharpens.png`)
- **Figure 6.** The deployable two-stage pipeline: gate (abstain) → generate → dial+veto
  (surface trust). (`fig-p3-06-pipeline.png`)
- **Figure 7.** Cross-family depth profile: gate vs dial per-layer AUROC against fractional
  depth, with argmax dots and within-tolerance span bars; descriptive, from the Amendment Z
  `auroc_surface` blocks. (`fig-p3-07-depth-profile.png`)
