# Research Trajectory — Epistemic Humility Program

_Updated 2026-07-08. Replaces the stale 2026-06-10/06-30 versions. Every claim traces
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
works selectively (AF PASS); compliance is asymmetric — wrong muzzles are obeyed,
release is resisted (AG PASS); and reward-on-readout did not train own-readout
consultation (AI NULL). The current mechanistic refinement says the write site matters:
a J-lens/J-space localization diagnostic found the Qwen3-4B workspace-like band around
hs=23-29, and the held-out layer contrast found hs23 beats the inherited hs34 reference.
That is Paper 5's current actuation fork: channel authority, gating, and workspace-band
write location.

---

## Paper 2 — training regimen (COMPLETE)

Pipeline on `main` (PR #1). SFT-warmed DPO/KTO/GRPO on Qwen3-4B controlled within-model.
Cold-start arms failed (3 seeds). Training moves behavioral refusal; the
abstention-calibration tension holds across all methods. GRPO variants (Amendments
B/F/J/K/L/M/N) are SIGNED; most untested relative to the readout arc.
Draft: `papers/paper-2-training-regimen/manuscript.md`. Figures: `fig-p1-*` (legacy prefix).

---

## Paper 3 — "Knows but Doesn't Say" (draft complete incl. bibliography; provenance pass remaining)

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

## Paper 4 — two-signal readout (mechanism complete; figures pending)

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

---

## Paper 5 — actuation arc (IN PROGRESS)

**AA (FALSIFIED):** Activation steering (Arm A) and CoT injection (Arm B, all 8 cells)
flat. Text channel does not open. "Presence ≠ use." Arm B's `revision_discrimination`
saturated under sampled decode (instrument bug; fixed 2026-07-03 in
`steering_common.py` — grade-transition semantics, regression-tested).

**AB (reinforcing negative):** First-person natural-language injection (voice + percent
+ action rule) also leaves the channel shut. AA's conclusion extends to the strongest
framing.

**AC (POSITIVE — RQ4 Stage 1):** Doubt probe score coupled to the caution gate at
inference time (not an emitted channel). Selectivity gap coupled−permuted +8.7pt, CI
[+5.6, +12.0]. The doubt wire carries information about WHICH rows get released.
Source: `AMENDMENT-AC-doubt-regulated-caution.md` §8.

**AF (PASS — channel-authority):** Second-person system-prompt directive produces
selective policy shifts. Selectivity gap +18.0pt over permuted, CI [+11.8, +24.7].
Adjudicated claim: CHANNEL-AUTHORITY (authority + pre-generation timing open the
channel; AA/AB nulls are localized to channel authority, not to text per se).
Own-readout attribution NOT established (probe ≡ gold 600/600).
Source: `AMENDMENT-AF-second-person-doubt-prime.md` §8.

**AG (PASS — asymmetric compliance, belief-vs-policy dissociation):** Inverted arm.
G1a: induced refusal on known-correct +34.0pt, CI [+26.5, +41.5] (wrong muzzle
obeyed). G1b: asymmetry +26.1pt, CI [+18.0, +34.6] (release resisted at +7.9pt).
Instrumentation: doubt axis anti-semantic under primes; compliance travels through the
caution axis (Δcaution AUROC 0.654). The model obeys external authority against its own
knowledge — policy compliance without belief revision.
Source: `AMENDMENT-AG-oracle-dissociation-prime.md` §9.

**AE (COMPLETE — pre-stated adequacy-floor STOP, PR #157):** the raw base already
abstains ~93% on unknowns under the affording prompt (confabulates 21/300), so the
planned cells sat under the pre-stated floor; the actuator question stays open.
**AD:** SIGNED, not launched (trained-checkpoint twin of AG's direction-flip; predicts
null; deprioritized while the focus is training-free).

**Neutral-prepend control (AG §9.4, DONE 2026-07-03, PR #166):** the generic
any-prepend component is real and large, but re-referenced to neutral the primes move
the caution axis in the semantically correct directions (HIGH down, LOW up) while the
doubt axis stays anti-semantic — the belief-vs-policy dissociation sharpened.

**AH (H-COMPLIANCE, certified via Addendum A1):** the divergent-pool (probe ≠ gold)
own-readout attribution design AF/AG called for. G2 release congruence is a precise
zero (−0.21pt, CI [−4.45, +4.10]) — prime uptake does NOT consult the model's own
readout; the recalibrated positive control passes decisively (+50.98pt vs +20pt floor,
monotone across caution quintiles). Closes the AF/AG attribution question on the
compliance side. Source: `AMENDMENT-AH-divergent-pool-own-readout.md`.
**Data exhaust published** (user-approved 2026-07-04):
[`professorsynapse/eh-doubt-on-command`](https://huggingface.co/datasets/professorsynapse/eh-doubt-on-command)
— 5,436 per-row generations + primed-readout instrumentation + A1 stratum, with
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
(AA was flat on the raw base; trained checkpoints have a live gate — backlog item 3.)
Whether ANY channel couples behavior to the model's own readout — text/prompt is
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

---

## Five-paper line (canonical as of 2026-07-01)

| Paper | Scope | Draft |
|-------|-------|-------|
| P1 | Taxonomy / C1–C5 / policy-vs-signal framework | `papers/paper-1-taxonomy-framework/manuscript.md` |
| P2 | Training regimen (SFT/DPO/KTO/GRPO) | `papers/paper-2-training-regimen/manuscript.md` |
| P3 | "Knows but Doesn't Say" — internal gap + training-resistance | `papers/paper-3-knows-but-doesnt-say/manuscript.md` |
| P4 | Two-signal readout (training-free, cross-size/-family/-seed) | `papers/paper-4-two-signal-readout/manuscript.md` |
| P5 | Steering / actuation | `papers/paper-5-actuation/manuscript.md` |

Figure/script prefixes are legacy (`fig-p1-*` = Paper 2, `fig-p2-*` = Paper 3,
`fig-p3-*` = Paper 4). Amendment labels stay out of paper prose; traceability lives in
provenance appendices.
