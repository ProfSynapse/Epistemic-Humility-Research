# Research Trajectory: Epistemic Humility Program

_Updated 2026-07-20. Replaces the stale 2026-07-08 version. Every claim traces
to a protocol doc; nothing is invented. The original Phases 1–4 plan (staged design) is
preserved in `archive/docs/protocol/research-trajectory.md`._

---

## Through-line

The program trained abstention (locked training-regimen SFT/DPO/KTO/GRPO, Paper 2), then found a
persistent internal-vs-stated gap: hidden states encode answerability clearly (AUROC
0.997) while emitted confidence stays decoupled and training-resistant (Paper 3).
The pivot: stop trying to wire the channel through training and instead READ the axis
directly. The two-signal gate + dial + veto pipeline reads off the raw untrained base,
is size-robust (Qwen3 1.7–14B), seed-robust under sampled decode, and cross-family
(Llama/Ministral/Qwen3.5/Gemma). That is Paper 4. The program then asked: can we WRITE
to the axis? The text channel is shut (AA/AB null); the system-prompt authority channel
works selectively (AF PASS); compliance is asymmetric: wrong muzzles are obeyed,
release is resisted (AG PASS); and reward-on-readout did not train own-readout
consultation (AI NULL). The current mechanistic refinement says the write site matters:
a J-lens/J-space localization diagnostic found the Qwen3-4B workspace-like band around
hs=23-29, and the held-out layer contrast found hs23 beats the inherited hs34 reference.
That is Paper 5's current actuation fork: channel authority, gating, and workspace-band
write location. A second pivot followed on 2026-07-16: a signed factorial falsified
the claim that "the gate supplies selectivity" at each family's mid-band operating point
(the write self-sorts; the gate adds only a sub-floor increment), reconciling with the
earlier overdrive-regime result (H4, where the gate WAS essential) as two readings of
one commitment-margin geometry. The margin theory framework adopted the same day
retires mentalistic naming pending an evidentiary earnability test the resulting
cascade did not pass: "doubt" factors into an unanswerability-recognition signature
and a weak, behaviorally inert evidence-registration, neither earning the name. A
parallel cross-family fleet found the underlying caution direction readable in every
tested family but behaviorally actuable, at the registered late site, only in the Qwen
lineage. Paper 5 is now titled and framed around known-unknown/answerability readout
and channel/gate/workspace constraints; the margin and correctness-geometry work
(M1-M6, correctness-direction-rotation, correctness-subspace-overlap) is routed to a
successor Paper 6.

---

## Paper 2: training regimen (COMPLETE)

Pipeline on `main` (PR #1). SFT-warmed DPO/KTO/GRPO on Qwen3-4B controlled within-model.
Cold-start arms failed (3 seeds). Training moves behavioral refusal; the
abstention-calibration tension holds across all methods. GRPO variants (Amendments
B/F/J/K/L/M/N) are SIGNED; most untested relative to the readout arc.
Draft: `papers/paper-2-training-regimen/manuscript.md`. Figures: `fig-p1-*` (legacy prefix).

---

## Paper 3: "Knows but Doesn't Say" (draft complete incl. bibliography; provenance pass remaining)

Internal axis encodes answerability at AUROC 0.997, transfers cross-dataset cold
(Amendment P: KUQ→SelfAware 0.983), and predates post-training (Amendment Y: present on
the pre-trained base). Stated confidence stays decoupled. Training-resistance is the
headline: DPO/KTO/GRPO/contrastive-SFT/proper-scoring all fail to couple the channel
(Amendments M/R FALSIFIED; aux-head joint co-training FALSIFIED). Behavioral abstention
is installable; accurate emitted confidence is not. §7–8 absorption (proper-scoring,
contrastive, RL-on-contrastive depth) DONE via PR #151; Amendment Y now cited for the
"paid for by pretraining" claim; data availability lists the published HF releases.
Citation-gap audit (2026-07-04) wove 34 missed citations into §2/§3/§7/§8 and
compiled the 43-entry bibliography from the KG (inline↔list verified 1:1).
Remaining before submission: the provenance reconciliation pass against
`archive/papers/retired/results-provenance-inventory.md`.
Draft: `papers/paper-3-knows-but-doesnt-say/manuscript.md`. Figures: `fig-p2-*` (legacy prefix,
all five built).

---

## Paper 4: two-signal readout (mechanism complete; figures pending)

### Mechanism

Three orthogonal linear probes compose a two-stage trust pipeline on the raw base:

- **Gate** (pre-generation anchor): answerability, AUROC 0.997. Saturated on raw base;
  training adds nothing.
- **Dial** (post-generation): per-answer correctness, AUROC 0.834 (Amendment S, G2
  PASS: post-gen beats pre-gen by +0.065 CI [0.040, 0.090]). Survives on the deployed
  clean-SFT→GRPO-v2 checkpoint at 0.819 (Amendment T). Axes are orthogonal; fusing hurts.
- **Veto**: dial flags hallucinations as lowest-trust (Amendment U: AUROC 0.980, mean
  dial 0.018 for hallucinations vs 0.833 for correct). Present on the raw base at 0.754
  (Amendment W); training sharpens but does not create it.

### Generalization (all PASS / SUCCESS)

- **W**: full mechanism training-free on Qwen3-4B raw base; gate 0.997, dial 0.834,
  veto 0.754.
- **X**: size-robust, Qwen3 1.7B/8B/14B, all three gates PASS; veto non-monotonic with
  scale (peaks 8B), descriptive only.
- **Z**: cross-family SUCCESS 4/4 (Llama-3.2-3B, Ministral-3B, Qwen3.5-4B, Gemma-4-E4B).
- **SR**: seed-robust under sampled decode (3 seeds × 4 families); dial 0.799–0.865,
  veto 3/3–3/3 per family; greedy misses in Z were decode artifacts, not signal failures.

Amendment trail: O/P/Q (ceiling + engine) → S/T (correctness readout) → U (veto) →
Stage-1.5 (orthogonality) → W/X/Z/SR (training-free + generalization).
Draft: `papers/paper-4-two-signal-readout/manuscript.md`. Figures: `fig-p3-*` (legacy prefix).
Remaining: traceability appendix + six figures (backlog item 14).

**Correctness-geometry follow-ups, resolved null 2026-07-20:** the dial's 0.679
cold cross-checkpoint transfer (S fit → T deployed) had only been explained by
inference, not measurement. Two exploratory Tier-2 cells closed that gap, both
null. Correctness-direction-rotation (CD) measured the single discriminative
axis across raw → clean-SFT → GRPO-v2 → GRPO-par-true directly: cosines stayed
low (raw→cleansft 0.192, cleansft→grpov2 0.449, grpov2→partrue 0.330, all below
the 0.85 floor), the falsifier did not fire, and every stage still read
correctness well (OOF AUROC 0.809–0.860), so the direction is only weakly
identified rather than cleanly rotating or cleanly stable. Correctness-
subspace-overlap (SO) then tested whether a shared low-dimensional subspace
(rather than a single axis) explains the same signature: SO-G1 failed all
three pre-registered limbs at k=8 (S→T overlap 0.0116 inside the permutation
null; within-stage reliability 0.02–0.03 against a 0.70 floor; recovery closed
only 17.5% of the floor-to-ceiling gap). A post-hoc planted-signal simulation
showed the reliability limb is estimator-structurally unreachable for any
signal at this sample size (L2-regularized logistic regression collapses a
redundant subspace onto one stable normal), so the falsifier's non-firing
carries no evidential weight and neither the shared-subspace nor the
genuine-rotation reading is adopted. What survives: one weak shared direction
at k=1 (recovery AUROC ≈0.70, matching the 0.679 transfer), with the
remaining transferable signal diffuse across the base checkpoint's span
rather than concentrated in a compact subspace. Sources:
`experiments/correctness-direction-rotation/AMENDMENT.md`,
`experiments/correctness-subspace-overlap/AMENDMENT.md`. Both cells are
folded into `papers/paper-4-two-signal-readout/manuscript.md` §4.2, replacing
the prior inference-only SWAP marker with this measured account. A
successor cell, correctness-geometry-scale-ladder (Qwen3 1.7B/8B/14B),
is built but not signed: its pre-sign synthetic estimator validation failed
for all four candidate estimators at every scale (the same estimator-collapse
class the subspace-overlap red-team surfaced), so a design-v2 iteration is in
progress and no real per-row correctness label has been touched.

---

## Paper 5: actuation arc (IN PROGRESS)

**AA (FALSIFIED):** Activation steering (Arm A) and CoT injection (Arm B, all 8 cells)
flat. Text channel does not open. "Presence ≠ use." Arm B's `revision_discrimination`
saturated under sampled decode (instrument bug; fixed 2026-07-03 in
`steering_common.py`, grade-transition semantics, regression-tested).

**AB (reinforcing negative):** First-person natural-language injection (voice + percent
+ action rule) also leaves the channel shut. AA's conclusion extends to the strongest
framing.

**AC (POSITIVE, RQ4 Stage 1):** KU (answerability) probe score coupled to the
refusal-axis gate at inference time (not an emitted channel); legacy names
`doubt probe` / `caution gate`, per `papers/common/terminology.md`. Selectivity
gap coupled−permuted +8.7pt, CI [+5.6, +12.0]. The KU-readout wire carries
information about WHICH rows get released.
Source: `experiments/doubt-regulated-caution/AMENDMENT.md` (legacy label
AMENDMENT-AC) §8.

**AF (PASS, channel-authority):** Second-person system-prompt directive produces
selective policy shifts. Selectivity gap +18.0pt over permuted, CI [+11.8, +24.7].
Adjudicated claim: CHANNEL-AUTHORITY (authority + pre-generation timing open the
channel; AA/AB nulls are localized to channel authority, not to text per se).
Own-readout attribution NOT established (probe ≡ gold 600/600).
Source: `AMENDMENT-AF-second-person-doubt-prime.md` §8.

**AG (PASS, asymmetric compliance, belief-vs-policy dissociation):** Inverted arm.
G1a: induced refusal on known-correct +34.0pt, CI [+26.5, +41.5] (wrong muzzle
obeyed). G1b: asymmetry +26.1pt, CI [+18.0, +34.6] (release resisted at +7.9pt).
Instrumentation: KU (answerability) readout anti-semantic under primes; compliance
travels through the refusal-versus-confabulation contrast (legacy `caution` atlas
axis; Δcaution AUROC 0.654). The model obeys external authority against its own
knowledge: policy compliance without belief revision.
Source: `AMENDMENT-AG-oracle-dissociation-prime.md` §9.

**AE (COMPLETE, pre-stated adequacy-floor STOP, PR #157):** the raw base already
abstains ~93% on unknowns under the affording prompt (confabulates 21/300), so the
planned cells sat under the pre-stated floor; the actuator question stays open.
**AD:** SIGNED, not launched (trained-checkpoint twin of AG's direction-flip; predicts
null; deprioritized while the focus is training-free).

**Neutral-prepend control (AG §9.4, DONE 2026-07-03, PR #166):** the generic
any-prepend component is real and large, but re-referenced to neutral the primes move
the refusal-versus-confabulation contrast (legacy `caution` atlas axis) in the
semantically correct directions (HIGH down, LOW up) while the KU (answerability)
readout stays anti-semantic: the belief-vs-policy dissociation sharpened.

**AH (H-COMPLIANCE, certified via Addendum A1):** the divergent-pool (probe ≠ gold)
own-readout attribution design AF/AG called for. G2 release congruence is a precise
zero (−0.21pt, CI [−4.45, +4.10]): prime uptake does NOT consult the model's own
readout; the recalibrated positive control passes decisively (+50.98pt vs +20pt floor,
monotone across caution quintiles). Closes the AF/AG attribution question on the
compliance side. Source: `AMENDMENT-AH-divergent-pool-own-readout.md`.
**Data exhaust published** (user-approved 2026-07-04):
[`professorsynapse/eh-doubt-on-command`](https://huggingface.co/datasets/professorsynapse/eh-doubt-on-command):
5,436 per-row generations + primed-readout instrumentation + A1 stratum, with
datasheet and license audit.

**AI (NULL, 2026-07-05):** probe-as-reward tested whether GRPO with the frozen
doubt-probe readout as reward would train consultation of the model's own readout.
It did not. TRUE congruence was 59.75% vs PERMUTED 76.75%, differential -17.0pt
(10k paired bootstrap CI [-21.5, -12.5]); the pre-registered TRUE-wins call was
wrong. Mechanistic reading: the TRUE arm learned a useful behavioral refusal
boundary, but this was not own-readout-consistent behavior. Source:
`AMENDMENT-AI-probe-as-reward.md` §5.

**J-space localization (RESOLVED exploratory lab diagnostic, 2026-07-07):** a
from-scratch Jacobian lens on Qwen3-4B bf16 passed its final-layer logit/unembed smoke
(mean cosine 0.9811, mean top-10 overlap 0.82, top-1 match 3/5 over 1000 prompts).
Same-substrate bf16 fitted directions split cleanly: `pos_ctrl_L34` and `c_hat_L34`
verbalize as self/absence/error/impossibility-like tokens; `u_d_L34` verbalizes as
answer/reply-like; `neg_ctrl_L34` is a noisy local null. The layer profile localizes
the workspace-like effective-dimensionality band to hs=23-29 with a peak at hs=26.
This project's L34 direction layer maps to hs=34, just after that band. Interpretation:
the result does not prove J-space writes will work, but it gives a concrete layer-site
hypothesis for the readout-portable/write-fragile split. Sources:
`experiments/j-space-localization-qwen3-4b/AMENDMENT.md`,
`docs/sessions/20260707T224240Z-j-space-j-lens-r1-findings.md`, and
`library/concepts/mechanisms/j-space-mediated-actuation-fragility.md`.

**J-space dose calibration (RESOLVED exploratory FIT-only calibration,
2026-07-08):** the first causal successor stopped at G0 because absolute dose 200
collapsed hs23/hs26 before any held-out contrast. A FIT-only local calibration
then recovered usable non-collapsing setpoints for every layer: hs23=25,
hs26=75, hs29=125, hs34=175. At the selected doses, collapse on dosed rows was
0, clean_tighten was 8/8 for hs23/hs26/hs29 and 7/8 for hs34, and known-correct
cost was 1/8 for each layer. Interpretation: the failed assumption was dose
portability across layer sites, not evidence that the mid-band sites are
unusable. This is still FIT-only calibration evidence; held-out mid-band
superiority remains untested. Sources:
`experiments/j-space-midband-dose-calibration-qwen3-4b/AMENDMENT.md`,
`experiments/j-space-midband-dose-calibration-qwen3-4b/analysis-committed/dose_calibration_summary.json`,
and `experiments/j-space-midband-dose-calibration-qwen3-4b/RUNBOOK.md`.

**J-space calibrated layer contrast (RESOLVED exploratory pass, 2026-07-08):**
the held-out causal test `j-space-calibrated-layer-contrast-qwen3-4b` passed on
raw-base Qwen3-4B bf16. Smoke G0 passed first, then the full local RTX 3090 run
used the FIT-selected setpoints hs23=25, hs26=75, hs29=125, and hs34=175 over
443 held-out rows. Best mid-band was hs23: confab clean_tighten 165/185 = 89.2%
vs hs34 123/185 = 66.5%, delta +22.7pp; known-correct cost 9/258 = 3.5% vs
hs34 7/258 = 2.7%, delta +0.78pp. G1/G2/G3 all passed, and hs34 remained a
viable predecessor reference. Interpretation: this is first causal support for
the layer-site account on this surface, not yet a cross-family or headline
claim. Source:
`experiments/j-space-calibrated-layer-contrast-qwen3-4b/AMENDMENT.md`.

**Open questions for Paper 5:** Does a trained-checkpoint steering arm move the gate?
(AA was flat on the raw base; trained checkpoints have a live gate; see backlog item 3.)
Whether ANY channel couples behavior to the model's own readout: text/prompt is
compliance-only (AH); the reward channel is under test (AI). The J-space fork now has
surface-local causal support that prior residual writes were aimed too late; the next
question is whether the mid-band advantage replicates beyond raw-base Qwen3-4B.

**J-space token-targeted refusal write (RESOLVED exploratory falsification,
2026-07-08):** `j-space-token-targeted-refusal-qwen3-4b` tested the internal-token
option rather than an external decode-time logit bias. A J-lens backward direction
was fit from the model's observed natural refusal/absence tokens against
answer/reply continuation tokens, then composed with the hs23 `c_hat` snap under
the same doubt gate. The direction wrote accurately and safely at FIT-selected
dose 5.0, but did not add useful lift over `c_hat_only`: held-out hs23
`c_hat_plus_j_token` reached 166/185 = 89.7% confab clean_tighten vs
`c_hat_only` 165/185 = 89.2% (+0.54pp, below the +4pp gate), known-correct cost
was 10/258 = 3.9% vs 9/258 = 3.5% (+0.39pp), and random-J matched the baseline.
`j_token_only` was non-inert at 88/185 = 47.6%, so the token-target actuator is
real, but the natural-token version is mostly redundant once the stronger
workspace-band `c_hat` write is active. Source:
`experiments/j-space-token-targeted-refusal-qwen3-4b/AMENDMENT.md`.
Abstract English labels (`doubt`, `caution`, `uncertainty`) and compact
multilingual refusal/uncertainty tokens remain a separate follow-up screen, not a
retroactive goalpost shift for this result.

**Cross-family confirmatory fleet (NOT PROMOTED, resolved 2026-07-12):**
doubt-snap-cross-family-confirmatory tested whether the answerability-gated
abstention snap (the AC/H4 mechanism; legacy name `doubt-gated caution snap`) generalizes to at least 3 of 4 small-tier families
(Qwen3.5-4B, Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3, Qwen3.5-9B) at the
registered late write site. No cell reached held-out scoring: every launched
cell stopped at the pre-outcome FIT dose-viability gate before the registered
prediction could even be tested (qwen35_4b peaked at 32.6% clean_tighten against
a 0.60 floor; llama32_3b_instruct peaked at 18.4%; mistral7b_instruct_v03 showed
a true behavioral null, 0/874 fired confabs tighten at any dose despite visible
token movement; qwen35_9b rose only to 5.75%). The registered falsifier, defined
over held-out G1/G2/G3 fails, could not fire either, since no cell reached
held-out. The fleet landed between its prediction and its falsifier.
gemma4_e4b and the remaining mid-tier cells were never launched (fleet abandoned
pre-launch); gemma3_12b was access-blocked. A lead-verified audit over existing
captures found the read side intact everywhere (the caution direction reads
refused-vs-confab at AUROC 0.84-0.99 in all four families) while the write side
actuates, at the registered late site, only in the Qwen lineage: a
read-actuate dissociation, not a failure to locate the encoding. Source:
`experiments/doubt-snap-cross-family-confirmatory/AMENDMENT.md`, Outcome.

**Family-atlas standard adopted (jspace-family-atlas, resolved 2026-07-12):**
the fleet's dissociation motivated a standing per-family instrument: full-depth
capture, a workspace-dimensionality profile, and a three-axis (doubt/caution/
raw_refusal) held-out read panel, codified as the `family-atlas` skill with its
registry `docs/atlas/family-layer-map.md`. The first cell (Llama-3.2-3B-Instruct,
Mistral-7B-Instruct-v0.3) found the registered prediction of an interior
mid-depth profile peak NOT MET in either family: eff_dim_frac peaks early
instead, layer 4 of 28 (0.14 depth) for llama and layer 3 of 32 (0.09 depth) for
mistral. The falsifier did not fire either: both families still hold a readable
interior band at held-out AUROC ≥ 0.80 on all three axes (llama layers 15-23,
mistral layers 7-27), so, like the fleet, the atlas lands between its
prediction and its falsifier: an early-exterior profile peak with a healthy
interior read band. Source: `experiments/jspace-family-atlas/AMENDMENT.md`,
Outcome.

**Placebo-seed distribution census (resolved 2026-07-15):** ahead of testing
the gate directly, a 15-seed-per-family census asked whether matched-magnitude
random directions are behaviorally inert. They are not, anywhere: qwen35_4b
SURVIVES a suppressive placebo sign (14/15 seeds negative, median -6.0 points),
llama32_3b shows a newly discovered negative sign (12/15, median -7.67, no prior
committed sign to falsify), and mistral7b_v03 SURVIVES a recruiting sign at the
registered boundary (12/15, exactly the 0.80 floor), falsifying both predictors'
prior "mistral is seed noise" call. Source:
`experiments/placebo-seed-distribution-census/AMENDMENT.md`, Outcome.

**Gate-contribution factorial (RESOLVED FALSIFIED, both families, 2026-07-16,
PR #296):** a signed 2×2 (true/permuted gate × true/random direction) factorial
tested whether the doubt gate, not the write direction, produces selective
abstention at each family's mid-band operating point (Qwen3.5-4B hs20;
Mistral-7B-Instruct-v0.3 hs16). The gate axis falsified on both: the dosed
c_hat write alone drives most of the abstention lift (permuted-gate confab
abstention 0.550 qwen / 0.600 mistral vs baselines 0.083 / 0.282), and the true
gate adds a real but sub-floor selectivity increment (Gap_Sel(c_hat) 0.148 qwen
/ 0.129 mistral against a 0.20 floor, both CIs excluding zero but entirely below
it) with cost protection far under its 0.10 floor. Direction-specificity (S1)
passed on qwen (ratio 7.27, sign-opposed to the census placebo) and failed on
mistral (ratio 2.03, same-signed), matching the census's substrate split.
Source: `experiments/gate-contribution-factorial/AMENDMENT.md`, Outcome.

**Margin theory of epistemic state adopted (2026-07-16,
`docs/research/margin-theory-framework.md`):** the factorial's apparent
contradiction with H4 (where the gate WAS essential, at Qwen3-4B/L34/dose-200)
resolves into one geometry read at two operating points. Each (model, question)
pair has a commitment margin (the minimum dose that flips a row to abstention),
and which regime a write dose lands in determines who supplies selectivity:
at mid-band (between typical confab and known margins) the write self-sorts and
the gate adds only a modest increment; in overdrive (above typical known
margins) everything crosses and the gate becomes the sole source of
selectivity. The framework also retires mentalistic naming pending an
evidentiary earnability test: "doubt direction" becomes "known-unknown
direction" (symbol c_hat unchanged), "doubt gate" becomes "KU readout gate",
"caution write" becomes "boundary push"; governed docs keep their historical
names, and the mapping governs new prose only. It opened a cheap-first
experiment cascade (M1-M6) to test the framework's claims directly.

**Margin cascade M1/M1b/M2/M4 (2026-07-17 through 2026-07-18):** every stage
resolved against the mentalistic reading. M1 (margin-mapping, RESOLVED
FALSIFIED) found commitment margins mechanistically real and correctly placed
at the qwen mid-band operating point (setpoint placement and retrodiction both
passed), but the registered censoring-aware separation bound came out 2.0
against a 2.5 floor; mistral is void by an instrument loss (a worktree-cleanup
incident destroyed its hs16 direction vector; reconstruction failed the
pre-registered byte-identity check). M1b (margin-separation-fine-ladder,
RESOLVED null-result) retested that miss at finer dose resolution and halted at
its own pre-registered byte-repro drift check: boundary rows do not have a
batch-invariant tipping classification under bf16 batched decoding, so the
separation question is instrument-resolution-limited rather than cleanly
quantized or cleanly real. M1's falsification stands. M2
(susceptibility-as-probe, RESOLVED FALSIFIED) found the readout and margin
channels REDUNDANT at qwen mid-band: the margin adds only 0.0154 incremental
AUROC over the readout alone (0.982) against a 0.02 floor; verbalized
confidence is anti-predictive (0.148 AUROC: the model reports higher
confidence on rows it confabulates). M4's first attempt
(margin-evidence-responsiveness) was VOID-BY-DESIGN: its true/false-answer
arms needed gold answers but were built on KUQ's world-unknown population,
which has none. It was superseded by a rebase onto a world-known PopQA
population, margin-evidence-responsiveness-worldknown (M4-WK). M4-WK's
transfer-primary test was VOID: the KUQ-fit direction reads world-known rows
near chance (AUROC 0.302), a genuine population reversal rather than a harness
bug (independently sign-verified). Its native-refit secondary dissociation
found a real, evidence-specific projection shift (paired true-vs-false diff
0.102, CI excludes zero) that falls well short of the pre-registered collapse
floor, so the earnability criterion is NOT EARNED. A same-day constructive
companion, evidence-response-direction-search (M4c), searched directly for a
fitted evidence-response axis and also resolved null-result: the axis separates
confab from correct at baseline (AUROC 0.725) but no better than random
directions drawn from the same covariance (p=0.191), so the separation is
generic activation geometry, not a specific evidence axis. Synthesis taught to
the PI (not itself a registered finding): "doubt" factors into at least two
non-transferable pieces, an unanswerability-recognition signature that reads
world-unknown questions but reverses on world-known ones, and a weak,
behaviorally inert evidence-registration on world-known rows, neither earning
the mentalistic label. Sources: `experiments/margin-mapping/AMENDMENT.md`,
`experiments/margin-separation-fine-ladder/AMENDMENT.md`,
`experiments/susceptibility-as-probe/AMENDMENT.md`,
`experiments/margin-evidence-responsiveness-worldknown/AMENDMENT.md`,
`experiments/evidence-response-direction-search/AMENDMENT.md`, all Outcome
sections.

**Paper 5 rewritten and retitled (PR #309, merged 2026-07-18):** with the
factorial and cascade closing out the H3/H4/H6 hardening arc, the PI ruled on
an eight-item decision packet: the title retires "doubt" for known-unknown/
answerability readout naming (new working title: *Readable Is Not Writable:
Channel, Gate, and Workspace Constraints on Actuating Known-Unknown State in
Small Language Models*); mistral stays in as a bounded negative with
more-model expansion queued; cross-family framing becomes "readable
everywhere, actuable only in the Qwen lineage at tested sites" with retests
queued; and the margin/geometry cells (M1-M6, correctness-direction-rotation,
correctness-subspace-overlap) route to a successor Paper 6 rather than folding
into Paper 5. A PI-funded, bounded diagnostic (not a registered amendment)
re-graded Amendment U's hallucination-veto population with a corrected wide
detector and found 90.1% of the labeled "confident confabulation" rows were
actually explicit refusals missed on a contraction the narrow detector's
marker list lacked; the confound is specific to the trained checkpoint's
installed refusal phrasing and does not touch the raw-base populations behind
paper 4's dial (Amendment S) or training-free (Amendment W) headlines. A
corrigendum (PR #311) corrected Amendment U's veto claim to UNPOWERED with the
corrected control at 0.74-0.81, folded into papers 1/2/4 (PR #312).

**Dial-vs-logprob baseline (LP, resolved 2026-07-18 as a pre-registered
data-stage stop):** asked whether the correctness dial beats a much simpler
baseline, the model's own answer-span token log-probability. LP-G0's exact
sequence round-trip failed on both arms (0.9% of rows re-tokenize one BPE token
short at the answer-span boundary, because generation-time token IDs were never
cached), so the gate fires the pre-registered data-stage stop before any
comparison is gated. The descriptive numbers computed for transparency (not a
gated result) suggest the dial's margin over logprob is small on the raw base
(dial 0.834 vs logprob 0.820, CI includes zero) but larger on the deployed
SFT+GRPO checkpoint, where training degrades the logprob signal (0.661) while
the dial holds (0.818); paper 4's limitation 8 cites this as
descriptive-with-caveat only. Source: `experiments/dial-logprob-baseline/AMENDMENT.md`,
Outcome.

**Llama atlas-sited wide-instrument retest (resolved 2026-07-19, PR #315):**
re-ran the fleet's llama cell at the atlas-located band with the certified wide
grading instrument rather than the narrow detector implicated in the Amendment
U confound above. The falsifier did not fire on any rung: llama's earlier
interior dose-response shape held up, peaking at hs20 dose 12 with 0.457
wide-adjudicated conversion (Wilson 95% [0.416, 0.497]) and well-formedness
0.946, with known-correct false refusal and format collapse both rising sharply
at higher doses. The full 23,510-row dosed dataset was published to Hugging
Face after PI approval. Source:
`experiments/llama-atlas-gated-wide-instrument-retest/AMENDMENT.md`, Outcome.

**Gemma-4-E4B family atlas (SIGNED 2026-07-20; outcome pending):** queued after
the correctness-geometry pair, this cell is the first signed under the new
run-persistence enforcement (see "Process infrastructure" below). Pool-mining
integrity (AG0a) failed its first attempt: generation completion rate 0.802
against a 0.90 gate (Gemma's verbosity overruns a 200-token cap) and a
batched-vs-sequential decode parity smoke mismatched on 2 of 8 rows, so a
signed revision 1 (400-token cap, a role-relevant-grade parity comparator in
place of exact-string matching, thresholds otherwise unchanged) was approved
the same day and the re-mine is in flight. No profile or read-panel gate has
run; no atlas outcome should be read from this entry. Source:
`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md` (worktree
`ehr-worktrees/gemma-atlas`, branch `exp/gemma-4-e4b-family-atlas`; not yet
merged to `main`).

**Correctness-vs-answerability portability contrast (added 2026-07-20):** the
CD/SO correctness-geometry nulls above (Paper 4 §4.2) motivate a next-study
hypothesis rather than a cross-family claim here: the answerability axis this
paper's gated write rides is crisp and portable (Amendment Z/SR), while the
correctness/dial axis's own cross-checkpoint geometry is only weakly
identified with no reproducible shared subspace beyond one weak direction.
`papers/paper-5-actuation/manuscript.md` §6.5 now states the contrast as an
explicit hypothesis for a future study, not a resolved finding of this paper.

---

## Process infrastructure

The margin cascade and the correctness-geometry pair each ran into a compute
or provenance incident that turned into a standing safeguard. A
worktree-cleanup sweep destroyed gitignored row-level data mid-cascade
(2026-07-17); the fix is a post-merge git hook that auto-harvests worktree
data into `main` (PR #298) and a policy of local copies instead of
cross-worktree symlinks. correctness-subspace-overlap's serial-only harness
turned a ~2-hour job into a 14-hour run, fixed going forward by a
parallelize-by-default build invariant (PR #317). The same cell's CPU
analysis run separately lost 57 minutes of compute when the session runtime
tore down a harness-tracked background task before it wrote any output; the
fix is sign-enforced persistence declarations plus a detached-launch wrapper
for hour-scale local runs (PR #318); gemma-4-e4b-family-atlas is the first
cell signed under this enforcement. The same cell's red-team review found its
reliability gate was estimator-structurally unreachable for any signal at its
registered sample size, now generalized into a requirement that any gate
thresholding a geometry estimator pass a pre-sign planted-signal validation
(PR #320); this is what caught correctness-geometry-scale-ladder's estimator
failures in minutes rather than after a full signed run. Finally, the
long-standing one-amendment-one-branch serialization rule was replaced with a
worktree-parallel convention so independent amendments no longer queue behind
each other (PR #322).

---

## Five-paper line (canonical as of 2026-07-01)

| Paper | Scope | Draft |
|-------|-------|-------|
| P1 | Taxonomy / C1–C5 / policy-vs-signal framework | `papers/paper-1-taxonomy-framework/manuscript.md` |
| P2 | Training regimen (SFT/DPO/KTO/GRPO) | `papers/paper-2-training-regimen/manuscript.md` |
| P3 | "Knows but Doesn't Say": internal gap + training-resistance | `papers/paper-3-knows-but-doesnt-say/manuscript.md` |
| P4 | Two-signal readout (training-free, cross-size/-family/-seed) | `papers/paper-4-two-signal-readout/manuscript.md` |
| P5 | Steering / actuation ("Readable Is Not Writable") | `papers/paper-5-actuation/manuscript.md` |

Figure/script prefixes are legacy (`fig-p1-*` = Paper 2, `fig-p2-*` = Paper 3,
`fig-p3-*` = Paper 4). Amendment labels stay out of paper prose; traceability lives in
provenance appendices.

A sixth paper is now named but has no manuscript yet: per the PI's 2026-07-18
ruling, the margin-theory cascade (M1-M6) and the correctness-geometry pair
(correctness-direction-rotation, correctness-subspace-overlap, and the
unsigned correctness-geometry-scale-ladder successor) are routed to a
successor Paper 6 rather than folded into Paper 5's actuation claims. No
`papers/paper-6-*` directory exists as of this update; the routing decision
is recorded in `docs/sessions/20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4.md`
checkpoint 008.
