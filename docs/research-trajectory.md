# Research Trajectory: Epistemic Humility Program

_Updated 2026-08-27. Replaces the stale 2026-07-08 version. Every claim traces
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

## Paper 3: "Knows but Doesn't Say" (draft-v3, restructured 2026-08-17; final-state check open)

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
The manuscript's own front-matter status is now `draft-v3`, restructured
2026-08-17 around a four-beat result order: the definitions-and-naming block
moved into §3, which was rebuilt as a full Methods section; §5 rebuilt around
the two-axis geometry and axis-stability figures; research-journey narration
removed per `papers/common/VOICE.md`; registration bookkeeping consolidated
into §9. §6 ("The refusal axis is causally real, and the leverage is one-way")
is new since the July update, and the provenance appendix ships as Appendix A.
What, if anything, remains before submission is being enumerated rather than
assumed: `backlog/tasks/task-92c973-papers-3-and-4-final-state-check.md`
(in-progress, blocker "PI read"). Do not read the old "provenance pass
remaining" line as still current or as discharged; the task is the record.
Draft: `papers/paper-3-knows-but-doesnt-say/manuscript.md`. Figures: `fig-p2-*` (legacy prefix;
seven built, 01-05 plus the §6 refusal-axis-ablation and bounded-site-sweep
panels) and `fig-p3-08`/`fig-p3-09` for the §5 two-axis geometry pair.

---

## Paper 4: two-signal readout (Draft v2, restructured 2026-08-17; figures and provenance appendix built)

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
Draft: `papers/paper-4-two-signal-readout/manuscript.md`. The July note
"Remaining: traceability appendix + six figures" is discharged: the manuscript
was restructured into six results sections with Methods, baselines, and
statistics subsections, ten figures are built under
`papers/paper-4-two-signal-readout/figures/` (`fig-p4-01` … `fig-p4-10`, no
longer the legacy `fig-p3-*` prefix), and the traceability material ships as
Appendix A ("Provenance and reproducibility") with Appendix B carrying the
extended descriptive material. As with Paper 3, the remaining-work list is
being enumerated under
`backlog/tasks/task-92c973-papers-3-and-4-final-state-check.md` (in-progress,
blocker "PI read") rather than asserted here.

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

## Paper 5: actuation arc (Draft v1 restructured 2026-08-17; in submission prep)

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

**Dial-vs-logprob resolved on both checkpoints (v3 and LT, both resolved
2026-08-13):** two successor cells replaced the stopped LP comparison with
gated numbers on fresh, self-consistent generation, and the answer is that the
dial's margin is checkpoint-dependent. `dial-logprob-baseline-v3` fixed the
round-trip failure class outright (0 capture divergences against v2's 282/1836)
and, on the raw base, landed in its own pre-registered ambiguous band: dial
AUROC minus primary-logprob AUROC **+0.0118, paired 95% CI [−0.0122, +0.0359]**
(n_boot 2000, seed 20260813), under the +0.05 floor with a CI straddling zero;
neither falsifier fired and the gate was not retuned. Its deployed-checkpoint
arm hit the registered data-stage stop at the power floor (710 answered rows
against 1000), so `dial-logprob-t-deployed-confirmatory` re-ran that arm at
adequate power and **passed LT-G1**: dial 0.7962 vs mean-answer-span logprob
0.6569, margin **+0.1393, paired bootstrap 95% CI [0.1031, 0.1755]**, n=1,501.
That cell is the sole citable deployed-checkpoint number, superseding v1's and
v2's non-citable descriptive reads. Program-level shape as those docs state it:
the dial's advantage over the model's own answer-span log-probability is
negligible on the raw base and large on the deployed abstention-trained
checkpoint. Sources: `experiments/dial-logprob-baseline-v3/AMENDMENT.md` and
`experiments/dial-logprob-t-deployed-confirmatory/AMENDMENT.md`, both Outcome.

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

**Gemma-4-E4B family atlas (RESOLVED 2026-07-20):** queued after the
correctness-geometry pair, this cell is the first signed under the new
run-persistence enforcement (see "Process infrastructure" below). Pool-mining
integrity (AG0a) failed its first attempt: generation completion rate 0.802
against a 0.90 gate (Gemma's verbosity overruns a 200-token cap) and a
batched-vs-sequential decode parity smoke mismatched on 2 of 8 rows, so a
signed revision 1 (400-token cap, a role-relevant-grade parity comparator in
place of exact-string matching, thresholds otherwise unchanged) was approved
the same day; under signed revisions 1-2 AG0a then passed all five limbs. The
cell resolved the same day with the falsifier firing on the profile limb:
eff_dim_frac peaks early-exterior at hs_index 4 (0.0189, 0.095 depth) and no
interior workspace band is declared, making Gemma-4-E4B-it the third family
after llama and mistral to show an early-exterior profile peak decoupled from
a healthy mid-band read panel. Limb 2 did not fire: the contiguous
all-three-axes ≥ 0.80 held-out band runs hs 13-42 (at hs 40, doubt 0.9949 /
caution 0.9223 / raw_refusal 0.9272). The cell's own caveat travels with it:
the random-direction control is elevated and spiky across much of the mid-band
(max-over-contrasts 0.83-0.87 at hs 10-12, 0.97 at hs 24, 0.85-0.94 at hs
28-34), so the naive best-per-axis layers are not clean reads and downstream
per-family actuation work should pick from the near-chance-control set (hs
14-18, hs 36-40). Source:
`experiments/gemma-4-e4b-family-atlas/AMENDMENT.md`, Outcome.

**Correctness-vs-answerability portability contrast (added 2026-07-20):** the
CD/SO correctness-geometry nulls above (Paper 4 §4.2) motivate a next-study
hypothesis rather than a cross-family claim here: the answerability axis this
paper's gated write rides is crisp and portable (Amendment Z/SR), while the
correctness/dial axis's own cross-checkpoint geometry is only weakly
identified with no reproducible shared subspace beyond one weak direction.
`papers/paper-5-actuation/manuscript.md` §6.5 now states the contrast as an
explicit hypothesis for a future study, not a resolved finding of this paper.

**Cross-family mid-band layer contrast (INCONCLUSIVE, interim 2026-07-24,
closed 2026-08-18):** `j-space-cross-family-layer-contrast` asked whether the
profile-selected mid-band write generalizes across four registered families.
Only 2 of 4 ran past G0, and the amendment's own roll-up floor ("fewer than 3
families ran at all ⇒ INCONCLUSIVE") fires: the cross-family question is not
answered in either direction. Per-family primaries, which stand as recorded:
llama-3.2-3b at hs17 PASS, confab `clean_tighten` 647/872 = **0.7420** (Wilson
[0.7119, 0.7699]); mistral-7b-v03 at hs15 FAIL on the floor only, 642/1312 =
0.4893 (Wilson lower 0.4624 clears the 0.40 sub-criterion, interval straddles
0.50) — a marginal miss the doc explicitly says must not be reported as
"mistral does not actuate"; qwen35-4b not run; gemma4-e4b not run (G0
instrument invalid for that family). Three registered-instrument defects were
recorded at resolve rather than worked around, the load-bearing one being that
G2 is non-diagnostic here: the KU gate correctly never fires on known-correct
rows, so the dosed known-correct denominator is 0 on every family measured
(llama 0/334, mistral 0/382) and the registered G2 PASSes — which stand, per
the gate-diagnosticity rule — are evidence about baseline malformedness only
and must never be cited as evidence that the write is selective or safe. The
2026-08-18 close-out recorded that SUCCESS was arithmetically out of reach and
closed the cell permanently at the interim verdict. Source:
`experiments/j-space-cross-family-layer-contrast/AMENDMENT.md`, Outcome and
Close-out. This is the parent whose llama hs17 result the two August llama
cells below verify.

**Gemma-4-E4B KV-sharing seam quarantine (resolved 2026-07-31):** the
mid-band null on gemma was tested against the hypothesis that the model's
key-value-sharing seam quarantines writes. Verdict as the doc states it: C1
FAIL (the sharing-OFF substrate is broken at baseline — known-correct cost
180/180 = 1.0 vs the control's 0/180, Newcombe CI [0.9704, 1.0] against a 0.05
cap), so A2/A4 are NOT-RUN and the primary A1-vs-A2 contrast cannot fire;
A2/A4 INCONCLUSIVE as registered. The D-ladder fires the supporting leg (D1
0.786 vs A1 no-usable-dose), leaving KV-quarantine **SUPPORTED-not-established**
and confounded with depth exactly as registered, since D1-D4 cannot separate
the quarantine mechanism from a generic shallow-band-only effect. The Phase A
(sharing ON) held-out ladder is the durable finding: D1/hs15 G1 PASS 0.7857
[0.7180, 0.8413] (best site, shallowest tested), D2/hs18 FAIL 0.4464, D3/hs20
FAIL 0.4048, A3/hs22 PASS with a PASS-DEGENERATE specificity gate, A5/hs24 G1
PASS 0.7321 but **G3 FAIL** (effect_ratio 1.139; the worst random draw
reproduced 88% of the true effect), adjudicated seam-region instability rather
than direction-specific actuation. The doc's own summary: gemma is actuable,
shallow-band-localized, with strength falling monotonically toward the seam,
and the program-level "gemma never actuates" reputation was a depth-coverage
artifact. Corollary instrument finding: the sharing-OFF surgery as built
destroys baseline behavior, so any successor quarantine test needs a gentler
ablation. Source: `experiments/gemma4-e4b-kv-seam-quarantine/AMENDMENT.md`,
Outcome.

**Gemma-4-E4B pocket ladder (resolved 2026-07-31):** the PI-directed companion
closed the last untested band of the cross-family operating range on this
substrate (hs25/hs26/hs27, sharing ON). Verdict: **no direction-specific
actuation anywhere in the pocket.** E1/hs25 cleared G1 (confab-tighten 133/168
= 0.7917, Wilson [0.7241, 0.8462]) and G2 (known-correct cost 9/270 = 0.0333)
on held-out but FAILED the mandatory G3 at effect_ratio **1.279 < 3.0** — the
exact hs24 signature, with the worst single random draw reproducing 78% of the
fitted direction's effect. Under the registered rule the claim is
`actuates_not_direction_specific`: it may not be cited as a specific effect and
may not be pooled with direction-specific results. E2/hs26 and E3/hs27 were
dose-viability NOT-RUN (max FIT confab-tighten 0.375 and 0.250 against a 0.5
usability floor). All three registered predictions MET. Interpretation stays
inside the registered fence: the pocket band shows hs24-style instability (a
broad subspace in which many directions tighten confabulation) and this does
not by itself resolve the quarantine hypothesis in either direction. Source:
`experiments/gemma4-e4b-pocket-ladder/AMENDMENT.md`, Outcome.

**Wide-instrument re-score of the qwen controls (resolved 2026-08-20):** the
random-direction and permuted-gate controls behind Paper 5 §4.5 (the raw-base
gated-controller headline) and §4.6 (the layer-site contrast) had only ever
been scored under the narrow detector. `wide-instrument-control-rescore`
regenerated both arms and re-scored them under the wide two-instrument stack,
and the prediction was CONFIRMED: both control conclusions survive, no
falsifier fires, and the §6.4 instrument gap closes. WG-G0 parity PASS with
13/13 rate pairs byte-exact to the committed narrow rates; CG1 PASS on all four
shards at attempt 1. WG-G1 PASS: wide gated confab tightening 137/185 = 74.05%
vs undosed 21/185 = 11.35% (lift +62.7pp) against the random direction's
13/185 = 7.03% (signed lift −4.3pp), effect ratio **14.5** against a 3.0 floor.
WG-G2 PASS: paired known-correct cost excess (permuted minus gated) +20.6pp,
bootstrap CI [+14.8, +26.3], n=209. WG-G3 PASS: wide hs23 89.19% vs hs34
66.49%, paired advantage **+22.70pp** — equal to the narrow anchor — CI
[+16.2, +29.7]. Instrument-change magnitude at these operating points is tiny
(5 of 2,677 core rows gained adjudicated abstention beyond the detector),
consistent with the calibration cell's family-specificity reading. Source:
`experiments/wide-instrument-control-rescore/AMENDMENT.md`, Outcome.

**Qwen3-4B L34 placebo seed census (resolved 2026-08-26, MIXED):** the
re-score above rested its specificity claim on a single historical random draw.
This cell supplied the distribution — fifteen fresh matched-dose random
directions at the same site, dose, rows, and instrument. QG-G1 **PASS**: max
absolute random lift 0.1297 (seed 920006) gives effect ratio **4.83** against
the 3.0 floor, so the +62.7pp gated lift is direction-specific against a
fifteen-draw distribution and the single-draw caveat in Paper 5 §4.8/§7 is
retired in favour of the distributional form. QG-G2 **FAIL**: only **6/15**
seeds carry a negative (suppressive) lift against the ≥12/15 criterion; the
per-seed lifts run −7.0pp to +13.0pp with median +0.5pp. Reading, as the doc
states it: the historical draw's suppressive sign was a draw-level accident,
not a family-signed suppressive placebo response, and the sign-opposition
phrasing must be dropped from the manuscript claims. Both predictors called
"both gates pass" and both were wrong on QG-G2; recorded straight. Source:
`experiments/qwen3-4b-l34-placebo-seed-census/AMENDMENT.md`, Outcome.

**Llama hs17 direction-specificity (resolved 2026-08-25):** llama's only write
ever to clear a held-out abstention floor — the parent cross-family contrast's
hs17 pass — had never been run against a random-direction arm. This cell ran
the program's own missing verification step at that site. Prediction confirmed:
LG-G1 **PASS**, arm-1 held-out `clean_tighten` 635/872 = **0.7282** (Wilson
[0.6977, 0.7567]) against the 0.50 floor, with CIs overlapping the parent's
0.7420 under a fresh decode seed; LG-G2 **PASS**, gated lift 0.7190 against a
max-absolute random lift of 0.0872 over fifteen matched-dose seeds, effect
ratio **8.25** against the 3.0 floor (per-seed signed lifts median +0.0023, 9
positive / 5 negative / 1 zero). LG-G3 (known-correct cost) is
**NOT-ADJUDICABLE**, exactly as pre-stated, because the KU gate fired on 0 of
334 known-correct rows. Llama therefore joins qwen as a family with a
direction-specific verified write. Source:
`experiments/llama-hs17-direction-specificity/AMENDMENT.md`, Outcome.

**Llama hs17 wide-instrument regeneration and re-score (resolved 2026-08-26):**
the specificity result above rested on the narrow `clean_tighten` instrument
only, and a direct re-score was impossible because that harness persisted
grades and flags but no generation text. This cell regenerated the full 17-arm
set with a text-persisting harness and scored the fresh generations under both
instruments. **Outcome A — wide replicates and is specific.** WR-G0 PASS
(frozen pins byte-identical, CPU smoke asserted the text-persistence schema
before launch). WR-G1 PASS as a bridge check: regenerated arm-1 narrow
`clean_tighten` 637/872 = **0.7305** — a third consistent sample of this
operating point (parent 0.7420, narrow cell 0.7282, this regeneration 0.7305).
WR-G2 PASS: arm0 wide 136/872 = 0.1560, arm1 wide 687/872 = 0.7878, **net wide
lift 0.6319** against a 0.30 floor, with only modest attenuation from the
narrow net lift 0.7182 on the same generations. WR-G3 PASS: max
random-direction absolute wide lift 0.0677, **effect ratio 9.34**; the random
census is centered on zero under the wide instrument (6 positive / 8 negative /
1 zero, median −0.0092) as it was under the narrow one. WR-G4
NOT-ADJUDICABLE as pre-stated (KU gate fired 0/334). CG1 PASS on all 19 shards
at attempt 1. A run-log anomaly is recorded straight: 25 duplicated confab
row_keys in the arm-0 log from a crash-resume overlap, whose 24
detector-negative duplicates entered the blinded pool twice and were graded
identically 24/24 — an unplanned inter-grader reliability check that changes no
number. Source: `experiments/llama-hs17-wide-instrument-rescore/AMENDMENT.md`,
Outcome.

**Data-loss incident, recovery re-run, and the published row-level dataset
(2026-08-26 / 2026-08-27):** after that cell's PR merged, the lead removed its
worktree with `git worktree remove --force` before the row-level exhaust was
staged, destroying the sole copy of the gitignored `analysis/` tree — runlogs
with generation text, scored rows, shard id maps, and the id salt. Root cause:
the post-merge harvest hook never fired because `main` was synced with `git
pull --rebase`, which takes the post-rewrite path that did not exist, and
nothing guarded the removal. Committed evidence and the already-published
aggregate exhaust were unaffected and the resolved verdict was untouched. The
user approved a GPU recovery re-run, run from the canonical checkout under a
pre-registered equivalence bar stated before launch; the bar **PASSED** on both
prongs (re-scored arm-1 narrow `clean_tighten` reproduces WR-G1's 637/872
bit-exactly, and the re-run generation manifest matches the committed original
on every count and flag, with 11 readback means differing at ≤ 5e-5 from GPU
numerics). All 19 surviving blind graded files sha256-authenticated against the
pre-unblinding committed hashes, so verdicts were re-attributed per-row by exact
text join, never positionally. Committed gate numbers remain the numbers of
record, untouched. The row-level exhaust was then published with user approval
as
[`professorsynapse/eh-llama-hs17-wide-instrument-rescore-rows`](https://huggingface.co/datasets/professorsynapse/eh-llama-hs17-wide-instrument-rescore-rows)
(15,492 rows, ~19 MB), alongside the earlier aggregate mirror
[`professorsynapse/eh-llama-hs17-wide-instrument-rescore`](https://huggingface.co/datasets/professorsynapse/eh-llama-hs17-wide-instrument-rescore).
Source: `experiments/llama-hs17-wide-instrument-rescore/NOTEBOOK.md`, entries
2026-08-26 and 2026-08-27; the structural fixes are in "Process
infrastructure" below.

**Paper 5's working title changed again during the August restructure.** The
manuscript now ships as *Look Before You Speak: Wiring a Language Model's
Answerability Readout to Its Refusal Behavior* (front-matter `status: Draft v1
(restructured)`, dated 2026-08-17), superseding the July working title
*Readable Is Not Writable* recorded above. Since then it has been through the
figure renumber (ten figures, `fig-p5-01` … `fig-p5-10`), the appendix
reconciliation (Appendices A-F, including the gemma depth-ladder and
KV-sharing-seam appendix and a fixed-seed randomly-sampled graded-examples
appendix), voice and terminology sweeps, and the external-reviewer-lens pass;
PRs #563-#568 are merged. Remaining work is submission-shaped rather than
evidentiary and is tracked at
`backlog/tasks/task-d342cb-paper-5-submission-prep-mats-fellowship.md` (todo,
high priority, blocker "PI review"): final PI read, venue formatting, and the
MATS/fellowship application forms.

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

August added four more, three of them straight out of the llama hs17 arc. The
row-text persistence guard (PR #561, commit `8a66aca8`, 2026-08-26) makes the
data-exhaust build-time text-capture rule structural instead of procedural
across three layers: `experiments/common/runlog_contract.py` opens a run log
that refuses any record missing non-empty generation text unless the caller
declares a `textless_reason` folded into the log's own meta fingerprint;
`exp validate` hard-errors on any `experiment.yaml` created on or after
2026-08-26 without a top-level `text_capture` field, with earlier experiments
exempt so the existing registry is unaffected; and `exp new` scaffolds
`text_capture: enabled` by default. That guard exists because the hs17
specificity harness persisted grades but not text, which is what forced the
wide re-score to regenerate rather than re-score. The worktree data-loss
incident above then closed the removal bypass (PR #564, 2026-08-26): a
`.githooks/post-rewrite` hook so the rebase sync path harvests too, a
fail-closed `--check --worktree` mode on `bin/harvest_worktree_data.py`, a
PreToolUse removal guard (`.claude/hooks/worktree_data_guard.sh`), and a
HARVEST BEFORE REMOVE step in the `pr-workflow` skill. That hook shipped
non-executable and was therefore silently ignored by git; the executable bit
was set the next day (PR #569, 2026-08-27) — worth remembering as the failure
mode where a guard exists in the tree and still never fires. Finally, the
task-backlog harness (PR #570, 2026-08-27) replaced the hand-curated backlog
rows with `bin/task` over `backlog/tasks/` and `backlog/drafts/`, a generated
task table inside `TODO.md`, and a pre-commit gate that requires an active
covering task for the files being committed.

---

## Parked threads (captured 2026-08-16; papers-first, no new experiments for now)

- **Seed decomposition of the refusal axis.** Two independently trained seeds of
  the same recipe concentrate the refusal decision onto a single direction to
  very different degrees: seed 1 full-axis ablation collapses known-item
  over-refusal 0.994 to 0.0298 (exploratory), while the pre-registered seed-2
  replication of that collapse left 0.5528 with the instrument passing every
  integrity check, so the near-total collapse is seed-specific. The axis is
  causally load-bearing at both seeds (seed 2 still releases 45.7 points of
  refusals and recovers correct answers on 29.2 percent of formerly refused
  knowns). Open question: how do individual training runs distribute the refusal
  decision across directions, and is it meaningful that the seed-2 full-axis
  residual (0.553) lands almost exactly on the seed-1 KU-orthogonalized
  component residual (0.524)? Evidence:
  `experiments/refusal-axis-ablation-confirmatory/AMENDMENT.md` (falsified,
  resolved 2026-08-16). Disposition: folded into paper 3 Limitations as flagged
  future work; a real answer needs a multi-seed decomposition study.
- **Mid-band entanglement of the refusal axis on trained checkpoints.** At hs17
  on clean_sft_grpo_v2_seed1 the refusal axis reads nearly as well as at the
  governed late site (construction AUROC 0.8645 vs 0.8688), but full ablation
  there releases zero of 168 known-item refusals (L35 releases 163 of 168 on
  the same rows) and induces refusal on 48 percent of previously answered
  knowns, while a minus-2-sigma displacement at the same site drops refusal to
  0.714 and recovers correct answers on 21 percent of the same rows. Removal
  and displacement are different operations at mid-depth: the direction is
  entangled with signal that answering requires. Open questions: what shares
  the axis at mid-depth, and does that entanglement explain why dosed writes
  (paper 5) succeed mid-band while ablation does not? Also parked: the trained
  J-lens profile is flattened and deepened relative to raw-base (hs26 peak
  suppressed about 35 percent, peak moved to hs29), the first measurement of
  training reshaping this geometry, worth a systematic training-stage sweep
  someday. Evidence:
  `experiments/jlens-trained-checkpoint-midband-ablation/AMENDMENT.md`
  (falsified, resolved 2026-08-16). Disposition: folded into paper 5 sections
  6.3 and 6.4 scoping; no new cell now.
- **Is the confidence channel itself prompt-scaffolded?** RESOLVED — no longer
  parked. Queued 2026-08-17, registered as
  `experiments/stated-confidence-under-pstruct/AMENDMENT.md`, and resolved
  2026-08-18 as a CPU-only reanalysis of 18 P-struct arms (1,832 AmbigQA rows
  each) from the held-out prompt-crossing confirmatory. **Verdict: PARTIAL —
  P2 held, P1 and P3 did not; neither falsifier fired.** The channel is not
  noise, but it is broken in a structured way. Miscalibration is universal
  (P2: 17/17 trained arms at ECE ≥ 0.15, actual range 0.5482-0.8495; the base
  and cold DPO/KTO arms state mean confidence 0.925-0.945 while answering at
  8.5-10% accuracy on this covert-ambiguity pool). Discrimination is near
  chance for most regimens (P1: only 8 of 17 trained arms inside the
  registered [0.55, 0.80] band against a ≥12 requirement), weak-to-moderate
  only in the SFT-lineage sequential arms (best 0.7245, seq SFT→KTO seed 2).
  Refusal separation fell one arm short of its band (P3: negative in 11 of 17,
  needed ≥12). The precise decomposition the lead recorded the same day, in
  place of the loose "coupling exists only where SFT is in the lineage"
  shorthand: SFT installs the confidence-refusal coupling, a subsequent DPO or
  KTO stage preserves it, a subsequent GRPO stage erases it, and cold
  preference training alone induces neither refusal nor coupling —
  SFT→GRPO refuses on 71.4% of rows while stating mean confidence 0.8127 with
  separation −0.0003. A pre-registration feasibility peek had unblinded four
  arm-level means, so no prediction or gate in the cell was placed on any mean
  and all means are descriptive-only. Consumer: the paper 2 §5 scope condition
  about the captured-but-never-analyzed structure-only channel can now cite a
  measurement. Exploratory; never pooled with the paper-2 headline matrix.

---

## Five-paper line (canonical as of 2026-07-01)

| Paper | Scope | Draft |
|-------|-------|-------|
| P1 | Taxonomy / C1–C5 / policy-vs-signal framework | `papers/paper-1-taxonomy-framework/manuscript.md` |
| P2 | Training regimen (SFT/DPO/KTO/GRPO) | `papers/paper-2-training-regimen/manuscript.md` |
| P3 | "Knows but Doesn't Say": internal gap + training-resistance | `papers/paper-3-knows-but-doesnt-say/manuscript.md` |
| P4 | Two-signal readout (training-free, cross-size/-family/-seed) | `papers/paper-4-two-signal-readout/manuscript.md` |
| P5 | Steering / actuation ("Look Before You Speak") | `papers/paper-5-actuation/manuscript.md` |

Figure/script prefixes are legacy where they have not been renumbered:
`fig-p1-*` = Paper 2 and `fig-p2-*` = Paper 3 (Paper 3 also carries two
`fig-p3-*` panels for its §5 geometry pair, which is the legacy Paper-4
prefix). Papers 4 and 5 have since been renumbered to match their own
positions: `fig-p4-01` … `fig-p4-10` and `fig-p5-01` … `fig-p5-10`.
Amendment labels stay out of paper prose; traceability lives in
provenance appendices.

A sixth paper is now named but has no manuscript yet: per the PI's 2026-07-18
ruling, the margin-theory cascade (M1-M6) and the correctness-geometry pair
(correctness-direction-rotation, correctness-subspace-overlap, and the
unsigned correctness-geometry-scale-ladder successor) are routed to a
successor Paper 6 rather than folded into Paper 5's actuation claims. No
`papers/paper-6-*` directory exists as of this update; the routing decision
is recorded in `docs/sessions/20260717T201649Z-margin-cascade-execution-m1-m2-m1b-m4.md`
checkpoint 008.
