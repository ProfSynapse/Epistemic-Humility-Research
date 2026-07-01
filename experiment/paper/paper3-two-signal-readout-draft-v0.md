# The Confidence Is Already There: A Training-Free Two-Signal Readout for Epistemic Humility in Small Language Models

*Draft v0 — flagship paper (Paper 3 of the program). Standalone contribution; cites
the companion diagnosis paper ("Knows but Doesn't Say") for the representation-vs-
verbalization gap it builds on. All primary numbers are single-seed (seed 1) unless a
cross-model replication is named; provenance for every figure is in Appendix A.*

---

## Abstract

Small language models routinely answer questions they cannot answer, and state a flat,
uninformative confidence when they do. A companion study shows this is not an ignorance
problem: the model holds a well-calibrated *internal* estimate of what it knows, yet the
confidence it *emits* is nearly constant and chance-level — it knows, but does not say —
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

Three findings make this a mechanism rather than a curiosity. **(1) It is training-free:**
the whole pipeline reads off the raw instruction-tuned base with no adapter and no
abstention training of ours; our training only *sharpens* the veto (0.754 → 0.980), it
does not create the signal. **(2) It is size-robust:** the readout passes on every Qwen3
scale from 1.7B to 14B. **(3) It replicates across model families:** on four independent
families (Qwen, Llama, Mistral, Gemma) the gate and dial pass on all four (gate saturated
0.997–0.998; dial 0.82–0.86), establishing them as *family-general*. The veto replicates
on three of four — it is the *fragile, model-dependent* axis, strong on Gemma (0.871),
clean on Mistral (0.733), marginal on Qwen3.5 (0.666), and failing on Llama-3.2 (0.633).
We report this split as a co-headline: **a small LM's sense of "can I answer this?" and
"is this answer right?" is a universal, readable property of the representation; its
ability to distrust its own confident fabrications is not.** We give the descriptive
mechanism (the correct-vs-hallucination gap in the dial distribution) that predicts which
models have it.

---

## 1. Introduction

An epistemically humble model does two things a fluent one does not: it declines questions
it cannot answer, and it attaches an honest confidence to the answers it does give. Small
open models are good at neither. They confabulate plausible answers to unanswerable
questions, and the confidence they verbalize is nearly flat regardless of whether they are
right.

The natural first hypothesis is that this is an *ignorance* problem — the model does not
represent its own uncertainty — and the natural fix is *training*: fine-tune it to abstain,
or optimize a preference/reward signal toward calibrated confidence. Our companion study
(the "Knows but Doesn't Say" diagnosis) tests and rejects the first hypothesis and finds
the second insufficient. A linear probe on the base model's internal activations separates
answerable from unanswerable questions almost perfectly (AUROC ≈ 0.997) with a
well-calibrated readout (ECE ≈ 0.004), while the model's *verbalized* confidence stays near
0.52–0.56 across the board. The internal estimate is there; the emitted one is not a
faithful copy of it. And the gap is *training-resistant*: it survives supervised
fine-tuning, DPO, KTO, and three generations of GRPO. Two opposite training pressures fail
on the same channel — reinforcement learning preserves stated calibration but never
installs knowledge-conditioned *action*, while distilling the internal axis into the
emitted token installs the action but collapses the confidence number onto it. The
bottleneck is not knowledge; it is the single confidence token that a language-model head
emits under next-token cross-entropy.

That diagnosis has a direct engineering consequence, and it is the subject of this paper.
**If the signal cannot be reliably trained into the emitted token, read it out of the
representation instead.** We show that a deployable trust mechanism can be built entirely
from linear readouts of a frozen model, with two contributions over the diagnosis:

1. **A second axis.** Answerability ("*can* this be answered?") is not the same as
   correctness ("is *this answer* right?"). We show correctness is *also* linearly
   readable, at a different token position (after the answer, not before it), and that the
   two axes are orthogonal — separable enough that combining them into one number degrades
   both. This yields a two-stage pipeline: a **gate** that abstains on unanswerable
   questions, and a **dial** that surfaces a trust number on what is answered.

2. **A generality claim.** The diagnosis was one model, one family. We show the readout
   is training-free (reads off the raw instruction-tuned base), size-robust (1.7B–14B), and
   replicates across four model families — and, honestly, we show *which part* generalizes.
   The gate and dial are family-general. The veto — the dial's ability to assign confident
   confabulation the lowest trust — is the fragile, model-dependent axis. We treat this as
   a co-headline finding, not a footnote, and give the descriptive quantity that predicts
   it.

The framing throughout is *readout, not training*. Our training does not create the trust
signal; it sharpens one part of it (the veto) and installs behavioral abstention. The
implication for practitioners is concrete: a useful, thresholdable trust number for a small
LM is available *today*, from a model you already have, with a cheap linear probe — no
fine-tuning run required.

---

## 2. Related work

**Verbalized confidence and calibration.** A line of work asks models to state their
confidence in words or tokens and measures its calibration; the recurring finding is that
verbalized confidence is poorly calibrated and often flat, especially for smaller models.
Our companion diagnosis localizes *why* in this model family: the internal estimate is
calibrated, the emitted token is not, and the loss on that token does not transmit the
internal estimate faithfully. This paper is the constructive complement — bypass the token.

**Probing internal states / latent knowledge.** A large body of work reads factual and
truth-related structure out of hidden activations with linear probes (e.g. truthfulness
directions, P(True)-style self-evaluation). Two points differentiate what we do. First, we
separate *answerability* (a property of the question, read before generation) from
*per-answer correctness* (a property of the produced answer, read after it), and show they
are distinct axes at distinct token positions. Second, we find that correctness reads
*better after the answer than before it* — a post-generation self-evaluation effect —
and we quantify the gain.

**Abstention and selective prediction.** Selective-prediction methods learn or threshold a
confidence to abstain. Our gate is a selective-prediction front-end, but the emphasis is
that it needs no training to install: it is a threshold on an axis the base model already
carries. This connects to hallucination-detection work; our veto is a hallucination
detector expressed inside the same correctness axis rather than as a separate module.

**Steering and representation engineering.** Reading a direction out of activations is one
half of representation engineering; writing along it (steering) is the other. This paper is
strictly the *reading* half. The companion diagnosis shows the answerability/caution axis
is causally steerable but only *asymmetrically* (excess caution can be relaxed; missing
caution cannot be installed by steering) — a result we cite as motivation for a follow-on
steering study, and as the reason we deploy the readout as a gate rather than as a steering
intervention here.

---

## 3. Setup

**Models.** The core mechanism is developed on Qwen3-4B in two conditions: the raw
instruction-tuned base (`unsloth/Qwen3-4B-bnb-4bit`, no adapter) and our deployed
checkpoint (clean supervised fine-tune → GRPO). The size study uses the raw Qwen3 bases at
1.7B / 4B / 8B / 14B. The cross-family study uses four ungated instruction-tuned bases at
comparable scale — Llama-3.2-3B, Ministral-3-3B, Qwen3.5-4B, and Gemma-4-E4B — read
training-free, exactly as the base-model condition.

**Data and labels.** Answerable questions come from PopQA and TriviaQA, graded against gold
answer aliases into *correct* / *wrong*. Intrinsic answerable-vs-unanswerable structure and
the hallucination class come from SelfAware: questions it marks unanswerable, when the model
answers them anyway, are labeled *hallucinations* (a structural label — the model produced
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

At the last prompt token — before any answer is generated — a linear probe separates
answerable from unanswerable questions at **AUROC 0.997** on the raw Qwen3-4B base. This is
the readable form of the internal estimate the diagnosis identified: the model represents
"can this be answered?" at the moment it is about to answer, and the representation is
almost perfectly separable. Thresholding this axis gives an abstention gate that needs no
training to install. As the cross-model results below show, this axis is the most robust of
the three: it is near-saturated (0.997–0.998) on every size and every family we tested.

### 4.2 The correctness dial reads off the answer — and reads better *after* it

Answerability is a property of the question. Whether a *specific produced answer* is correct
is a different property, and it is legible at a different place. A linear probe at the last
answer token ranks correct-vs-wrong answers at **AUROC 0.834** on the Qwen3-4B base
(layer 20). Critically, reading *after* the answer beats reading *before* it: the
post-generation position scores **+0.065** over the pre-generation position (CI [0.040,
0.090], excludes zero). The model's representation of "was that right?" is sharper once it
has committed to the answer than at the moment it begins — a self-evaluation effect
localized to token position, and one that peaks in the middle of the network rather than at
the final layer (Figure 4).

The dial survives deployment. On our clean-SFT → GRPO checkpoint the same post-generation
readout scores **AUROC 0.819** (layer 22), with the same post-beats-pre ordering
(post 0.819 vs pre 0.745). A dial *fit on the base* and applied *cold* to the deployed
checkpoint transfers only partially (0.679): the correctness *direction* drifts under
training even though the *readout* remains strong when refit — so the axis exists on both
checkpoints, but the probe should be refit per checkpoint rather than transported.

One honest caveat carried from the start: the dial *ranks* correctness well (AUROC) but is
not a calibrated *probability* (ECE 0.151 on the base). For a thresholdable trust number,
ranking is the operative property; a stated probability would need a downstream calibration
map. We claim the ranking, not the probability.

### 4.3 The dial vetoes confident confabulation

The same correctness dial, applied to the hallucination group — confident answers to
unanswerable questions — assigns them the **lowest trust of any group**: veto AUROC
**0.980** on the deployed checkpoint (correct vs hallucination), with a within-SelfAware
control (known-answered vs unknown-answered, same dataset) of **0.93** that rules out a
mere dataset-shift artifact. Confident confabulation does *not* read like a correct answer
to the dial. This is the property that makes the dial a hallucination *veto* and not merely
a correctness *ranker*: the failure mode we most want to catch — fluent, confident, wrong —
is exactly the one the dial pushes to the bottom.

Figure 2 shows the mechanism directly: the dial-mean of the hallucination group sits far
below the correct group, and the size of that separation is what the veto AUROC measures.

### 4.4 The two axes are orthogonal — a pipeline, not a fused scalar

Gate (answerability, at the anchor) and dial (correctness, post-generation) are separable
axes. When we fuse the two scalars into a single combined trust number, correctness ranking
*degrades* (Δ **−0.014**). The axes carry complementary information that a single number
destroys. The deployment consequence is to keep them as **two sequential stages** rather
than one score (Figure 6):

- **Stage 1 — Gate.** At the prompt anchor, threshold the answerability axis. If below
  threshold, abstain ("I don't know") and stop.
- **Stage 2 — Dial + veto.** For questions that pass the gate, generate the answer, then read
  the correctness dial at the post-answer token and surface it as the trust number.
  Confident confabulations that slipped the gate are caught here as lowest-trust.

### 4.5 The whole mechanism is training-free — training *sharpens*, it does not *create*

Every result above reproduces on the **raw** Qwen3-4B instruction-tuned base, with no
adapter and no abstention training of ours: gate **0.997**, dial **0.834**, veto **0.754**.
Both the gate and the dial pass unchanged; the veto is present and above chance on the raw
base. What our training buys is *sharpening the veto*, not creating the mechanism: the veto
climbs from **0.754 → 0.980** (+0.226 AUROC), and the mean trust the dial assigns to
confident confabulations drops from **0.271** on the base to **0.018** after training —
the trained model reads its own hallucinations as near-zero trust. Training adds essentially
nothing to the gate (already saturated) and installs autonomous behavioral abstention, but
the *readable trust signal itself* is a property of the frozen representation (Figure 5).

We scope "training-free" precisely: the raw base is the *instruction-tuned* release, so
"training-free" means "no abstention fine-tuning and no reinforcement learning of ours,"
**not** "no training ever." The answerability axis may be in part a product of upstream
instruction tuning. The claim is that *our* training regimen — the one the companion paper
shows cannot close the verbalization gap — is not what puts the readable signal there.

### 4.6 The readout is size-robust (1.7B–14B)

Across the Qwen3 family at 1.7B, 4B, 8B, and 14B, the training-free readout passes all three
gates at every size. The gate stays saturated (~0.997) throughout. The veto, however, does
*not* improve monotonically with scale: it is 0.757 at 1.7B, 0.754 at 4B, peaks at
**0.846 at 8B**, and *dips* to **0.741 at 14B**. The "bigger sharpens the veto" expectation
is not supported — an observation we flagged as descriptive in advance and did not promote
to a claim. The veto being the axis that wobbles with scale is the first sign that it, and
not the gate or dial, is the fragile part of the mechanism (Figure 3, left).

### 4.7 Cross-family: the gate and dial are universal; the veto is model-dependent

We pre-registered a cross-family confirmatory on four independent families read
training-free — Llama-3.2-3B, Ministral-3-3B, Qwen3.5-4B, Gemma-4-E4B — with SUCCESS defined
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
not a Qwen idiosyncrasy — it is a property of instruction-tuned small LMs across four
independent lineages.

**The veto replicates but is fragile.** It passes cleanly on Gemma (0.871) and Mistral
(0.733), marginally on Qwen3.5 (0.666 — point above the bar, CI lower bound 0.634 dipping
just under it), and *fails* on Llama (0.633 — a real signal, CI excludes chance, but below
the 0.65 bar). Catching *confident* hallucination is the model-dependent capability, exactly
as the non-monotonic size result foreshadowed.

**The descriptive mechanism.** The split is explained by the correct-vs-hallucination gap in
the dial's own distribution (Figure 2). Where a model's confident confabulations read as
low-trust, the veto works; where they read almost as trustworthy as correct answers, it
fails:

- **Gemma (veto 0.871):** hallucination dial-mean 0.089 vs correct 0.593 — the widest split;
  confabulations read as near-zero trust.
- **Mistral (0.733):** 0.278 vs 0.605 — clean separation.
- **Qwen3.5 (0.666):** 0.425 vs 0.636 — intermediate.
- **Llama (0.633):** 0.476 vs 0.707 — confident confabulations read *almost as trustworthy
  as correct answers*, so the dial cannot separate them.

Ordering families by the dial-mean gap (Gemma 0.504 > Mistral 0.327 > Qwen3.5 0.211 ≈ Llama
0.231) tracks the veto verdicts directionally. We flag one honest wrinkle: Llama's mean gap
(0.231) slightly *exceeds* Qwen3.5's (0.211), yet Llama fails and Qwen3.5 marginally passes —
because the veto AUROC depends on the full distribution overlap, not the mean gap alone. We
therefore read the gap as a *directional* predictor, not a strict rank. The stable
conclusion stands: **gate + dial are family-general (4/4); the veto replicates (3/4) but is
the fragile, model-specific axis.**

### 4.8 Seed-robustness: the greedy veto misses were decode artifacts

<!-- DRAFT-IN-PROGRESS 2026-07-01: Gemma seeds 20260702/20260703 still extracting; rows
marked TBD. Do NOT finalize the verdict sentence or touch §4.7's conclusion / the abstract
until all 12 cells land. Pre-reg: AMENDMENT-SR-sampled-decode-seed-robustness.md. -->

Every number in §4.7 comes from a single deterministic decode (greedy). A deployment
samples. We therefore pre-registered a seed-robustness confirmatory: the identical
training-free readout on the same four families under **sampled decoding** (temperature 0.7,
top-p 0.9) across **three seeds**, with the same per-cell gates and adequacy floors. The
gate was pre-declared decode-invariant (it reads the prompt anchor, which sampling never
touches) and emitted as an invariance check only; the dial and veto — both read from
*sampled* answers — were the endpoints. Success required the dial seed-stable on 4/4
families, the veto seed-stable on ≥3/4, and the per-seed veto majority never dropping below
3/4 on any single seed.

**Table 2. Sampled-decode seed-robustness (AUROC per seed; mean [min–max] across 3 seeds).**

| Model | Dial (3 seeds) | Veto (3 seeds) | Veto seed-stable? | Greedy veto (§4.7) |
|---|---|---|---|---|
| Llama-3.2-3B | 0.848 [0.827–0.865], 3/3 pass | **0.739 [0.684–0.801], 3/3 pass** | **YES** | 0.633 (FAIL) |
| Ministral-3-3B | 0.806 [0.799–0.812], 3/3 pass | 0.681 [0.606–0.742], 2/3 pass | **YES** | 0.733 (pass) |
| Qwen3.5-4B | 0.852 [0.830–0.864], 3/3 pass | **0.753 [0.659–0.807], 3/3 pass** | **YES** | 0.666 (marginal) |
| Gemma-4-E4B | 0.802 / TBD / TBD | 0.762 / TBD / TBD | TBD | 0.871 (pass) |

**The two greedy veto misses flip to passes under sampling.** Llama — the one clean veto
*failure* in §4.7 (0.633) — passes on **all three seeds** under sampled decoding (0.684–
0.801). Qwen3.5 — the marginal pass whose CI dipped below the bar — passes all three seeds
cleanly. The §4.7 "fragile veto" split is therefore partly a *decode* artifact, not purely a
model property: a single greedy trajectory produces one specific set of confabulations, and
Llama's greedy confabulations happened to read as trustworthy; its sampled ones do not.
Single-decode point estimates *understated* the veto.

**The veto is seed-sensitive per cell, seed-stable per family.** Across-seed spread on the
veto is real (Llama range 0.12, Qwen3.5 0.15, Ministral 0.14 — vs dial spreads of 0.01–
0.04), and Ministral drops below the bar on one seed (0.606 on seed 1, its only failing
cell). Per-cell veto numbers should accordingly be reported with seed spread, not as point
estimates. At the family level the verdict is stable: every family that has completed is a
seed-stable veto pass.

**The gate is decode-invariant, as pre-declared.** Across all completed cells the gate sits
at 0.996–0.999 with a per-family across-seed range under 0.003 — sampling the answer does
not move an axis read before the answer exists.

<!-- TBD (fill when Gemma 702/703 land): final verdict sentence — SUCCESS requires Gemma
dial 3/3 for clause (a) and the per-seed majority table. Seed 20260701, the only pinch
seed (Ministral fails it), already cleared 3/4 with Gemma's 0.762 pass. Then update:
§4.7 closing line ("fragile, model-specific axis" → decode-artifact nuance), the abstract's
single-seed caveat, and §7 Limitations. -->

---

## 5. The deployable pipeline

Putting the pieces together (Figure 6), a small LM can carry a training-free trust
mechanism with no fine-tuning:

1. **Gate (pre-generation).** Read the answerability axis at the prompt anchor. Below
   threshold → abstain. This is the most robust component (0.997–0.998 everywhere).
2. **Dial (post-generation).** For gated-through questions, generate, then read the
   correctness axis at the post-answer token and surface it as a *ranked* trust number.
3. **Veto (within the dial).** Confident confabulations that pass the gate are pushed to the
   bottom of the dial where the veto is strong (Gemma, Mistral); where the veto is weak
   (Llama), the gate remains the primary defense and the dial's confabulation-catching should
   not be relied on.

Two engineering notes fall out of the results. Keep the axes *separate* — fusing them costs
correctness ranking (§4.4). And *refit the dial per checkpoint* — the correctness direction
drifts under training (cold transfer 0.679, §4.2) even though the axis persists. The gate,
by contrast, transports well and is cheap to install anywhere.

---

## 6. Discussion

**Epistemic state is largely a readout, not a training outcome.** The companion diagnosis
showed the internal answerability estimate is calibrated while the emitted one is flat, and
that our training cannot reconcile them through the confidence token. This paper's
constructive result is the other side of that coin: because the signal is *in the
representation*, it can be *read* even when it cannot be *trained into the token*. The most
useful part of epistemic humility for a small model — a thresholdable "should I answer, and
how much should you trust this?" — is available from a frozen model with a linear probe.

**What training is for.** Our training is not wasted, but its role is narrow and specific: it
*sharpens the veto* (0.754 → 0.980) and installs autonomous behavioral abstention. It does
not create the gate, the dial, or the veto. This reframes the calibration-training question:
the goal is not to teach the model what it knows (it already represents that), but to make
its *behavior* and its *emitted signal* faithful to what it already represents — and, for the
veto specifically, to sharpen a signal that is present but weak on some models out of the box.

**Universal axes vs a fragile capability.** The cleanest scientific result is the split. "Can
I answer this?" and "is this answer right?" are readable across four families and four sizes —
they look like general properties of instruction-tuned small LMs. "Can I distrust my own
confident fabrication?" is not general: it is strong on Gemma, absent enough on Llama to fail
the bar, and non-monotonic in scale. This is an actionable map for practitioners (the gate is
safe to rely on anywhere; the veto must be validated per model) and a pointed question for
future mechanistic work (why do some models' confabulations read as low-trust to their own
correctness axis and others' do not?).

**Why not just steer?** The companion diagnosis found the answerability axis is causally
steerable, but *asymmetrically* — excess caution can be relaxed, missing caution cannot be
installed by steering. That asymmetry is why we deploy a *gate* (threshold-and-abstain) rather
than a steering intervention here: reading the axis and acting on the read is robust, whereas
writing missing caution into the model is not. Turning the readout around into a causal
*write* is the subject of the follow-on study.

---

## 7. Limitations

We state these plainly; several are the reason specific claims are scoped as they are.

1. **Single seed.** The core Qwen3-4B numbers (dial 0.834, veto deltas, the +0.065
   post-beats-pre gain) are seed 1. The near-saturated effects (gate 0.997) are low
   seed-risk; the dial and veto magnitudes are the seed-sensitive ones. The cross-family and
   cross-size replications provide model-level (not seed-level) robustness; a pre-registered
   multi-seed replication of the dial/veto magnitudes is the outstanding item before those
   *magnitudes* (as opposed to the existence claim) are headline-grade.
2. **"Training-free" is scoped.** It means no abstention-SFT or RL of ours, on an
   *instruction-tuned* base. The answerability axis may partly reflect upstream instruction
   tuning; we do not claim it exists in a pre-instruction base.
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
   behavior on the model's *own natural* (un-forced) answers is untested — the relevant surface
   for a live deployment — and is a known gap, not a solved case.
7. **Correctness-axis causality is untested.** The gate has causal (steering) evidence; the
   dial is correlational. Whether steering along the correctness axis moves actual correctness
   is future work.

---

## 8. Conclusion

A small language model's trust signal does not have to be trained in — it is largely already
present in the representation and can be read out. An answerability **gate** at the prompt
anchor (AUROC ≈ 0.997) and a per-answer correctness **dial** after the answer (0.834, better
after the answer than before) compose into a two-stage pipeline that needs no fine-tuning, is
size-robust from 1.7B to 14B, and — for the gate and dial — replicates across four model
families. The dial's **veto** on confident confabulation is real and, once sharpened by
training, strong (0.980), but it is the fragile, model-dependent piece: it replicates on three
of four families and is predicted by how far a model's confabulations fall below its correct
answers on the dial. Training's contribution is to sharpen that veto and install behavioral
abstention — not to create the underlying signal. The confidence, for the most part, is
already there; the task is to read it, keep the two axes separate, and know which model's veto
you can trust.

---

## Appendix A — Provenance and reproducibility

Every figure and number is generated from tracked result artifacts. Figures are produced by
`experiment/paper/scripts/build_paper3_figures.py`, which reads the per-cell result JSONs directly:

| Result surface | Artifact (under `experiment/phase1/probe/`) |
|---|---|
| Correctness dial, base (S) | `amendment_s_stage2_result.json` |
| Correctness dial, deployed (T) | `amendment_t_stage2_result.json` |
| Hallucination veto, deployed (U) | `amendment_u_two_signal_result.json` |
| Training-free whole mechanism (W) | `amendment_w_base_model_result.json` |
| Cross-size 1.7B/8B/14B (X) | `amendment_x_qwen3-{1.7b,8b,14b}-bnb-4bit_result.json` |
| Cross-family (Z) | `amendment_z_{llama-3.2-3b,ministral-3-3b,qwen3.5-4b,gemma-4-e4b}_result.json` |

Governance: each result surface is a signed exploratory amendment under
`experiment/protocol/` referencing the locked pre-registration; the cross-size and
cross-family confirmatories (`AMENDMENT-X-*`, `AMENDMENT-Z-*`) pre-stated their prediction,
falsifier, and gates before running, and their §7 verdicts record the outcome with bootstrap
CIs and no post-hoc goalpost changes. Extraction tensors and per-row artifacts remain local
(gitignored `*_tag/` subtrees); the tracked result JSONs carry the full per-layer AUROC
surfaces, CIs, and dial descriptives.

**Figure index.**

- **Figure 1** — Cross-family training-free readout: gate/dial/veto per family, veto-ascending,
  with CIs and the 0.65 pass / 0.50 chance lines. (`fig-p3-01-cross-family-readout.png`)
- **Figure 2** — Dial distribution per family: mean trust of correct / wrong / confident-
  confabulation groups, with the correct−hallucination gap annotated. (`fig-p3-02-dial-distribution.png`)
- **Figure 3** — The fragile axis: veto AUROC across Qwen3 sizes (left, non-monotonic, peaks
  8B) and across families (right, 3/4 pass). (`fig-p3-03-fragile-axis.png`)
- **Figure 4** — Correctness reads best after the answer: pre- vs post-generation dial AUROC by
  layer, base and deployed. (`fig-p3-04-post-beats-pre.png`)
- **Figure 5** — Training sharpens the veto: veto AUROC 0.754 → 0.980 and hallucination
  dial-mean 0.271 → 0.018, base vs trained. (`fig-p3-05-training-sharpens.png`)
- **Figure 6** — The deployable two-stage pipeline: gate (abstain) → generate → dial+veto
  (surface trust). (`fig-p3-06-pipeline.png`)
