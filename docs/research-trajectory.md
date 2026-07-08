# Research Trajectory — Epistemic Humility Program

_Updated 2026-07-08. Replaces the stale 2026-06-10/06-30 versions. Every claim traces
to a protocol doc; nothing is invented. The original Phases 1–4 plan (staged design) is
preserved in `experiment/protocol/research-trajectory.md`._

---

## Through-line

The program trained abstention (Phase 1 SFT/DPO/KTO/GRPO, Paper 2), then found a
persistent internal-vs-stated gap: hidden states encode answerability clearly (AUROC
0.997) while emitted confidence stays decoupled and training-resistant (Paper 3).
The pivot: stop trying to wire the channel through training and instead READ the axis
directly. The two-signal gate + dial + veto pipeline reads off the raw untrained base,
is size-robust (Qwen3 1.7–14B), seed-robust under sampled decode, and cross-family
(Llama/Ministral/Qwen3.5/Gemma). That is Paper 4. The program then asked: can we WRITE
to the axis? The text channel is shut (AA/AB null); the system-prompt authority channel
works selectively (AF PASS); compliance is asymmetric — wrong muzzles are obeyed,
release is resisted (AG PASS). The next mechanistic refinement asks whether the write
site itself is wrong: a J-lens/J-space localization diagnostic found the Qwen3-4B
workspace-like band around hs=23-29, peaking at hs=26, while the existing L34 write site
maps to hs=34 just after that band. That is Paper 5's current actuation fork: channel
authority, reward coupling, and now workspace-band write location.

---

## Paper 2 — training regimen (COMPLETE)

Pipeline on `main` (PR #1). SFT-warmed DPO/KTO/GRPO on Qwen3-4B controlled within-model.
Cold-start arms failed (3 seeds). Training moves behavioral refusal; the
abstention-calibration tension holds across all methods. GRPO variants (Amendments
B/F/J/K/L/M/N) are SIGNED; most untested relative to the readout arc.
Draft: `paper2-training-regimen-draft-v2.md`. Figures: `fig-p1-*` (legacy prefix).

---

## Paper 3 — "Knows but Doesn't Say" (draft complete incl. bibliography; provenance pass remaining)

Internal axis encodes answerability at AUROC 0.997, transfers cross-dataset cold
(Amendment P: KUQ→SelfAware 0.983), and predates post-training (Amendment Y: present on
the pre-trained base). Stated confidence stays decoupled. Training-resistance is the
headline: DPO/KTO/GRPO/contrastive-SFT/proper-scoring all fail to couple the channel
(Amendments M/R FALSIFIED; Phase B joint co-training FALSIFIED). Behavioral abstention
is installable; accurate emitted confidence is not. §7–8 absorption (proper-scoring,
contrastive, RL-on-contrastive depth) DONE via PR #151; Amendment Y now cited for the
"paid for by pretraining" claim; data availability lists the published HF releases.
Citation-gap audit (2026-07-04) wove 34 missed citations into §2/§3/§7/§8 and
compiled the 43-entry bibliography from the KG (inline↔list verified 1:1).
Remaining before submission: the provenance reconciliation pass against
`results-provenance-inventory.md`.
Draft: `paper3-knows-but-doesnt-say-draft-v0.md`. Figures: `fig-p2-*` (legacy prefix,
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
Draft: `paper4-two-signal-readout-draft-v0.md`. Figures: `fig-p3-*` (legacy prefix).
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

**AI (RUNNING, 2026-07-04):** probe-as-reward — with the text/prompt channel ruled
compliance-only by AH, AI tests the reward channel: GRPO with the frozen doubt-probe
readout as the reward signal (TRUE vs PERMUTED sensor arms). Verdict-eval locked
pre-outcome (prereg §4). Source: `AMENDMENT-AI-probe-as-reward.md`.

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
`docs/sessions/0043 - j-space-j-lens-r1-findings.md`, and
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
and `experiment/notes/j-space-midband-dose-calibration-qwen3-4b.md`.

**Open questions for Paper 5:** Does a trained-checkpoint steering arm move the gate?
(AA was flat on the raw base; trained checkpoints have a live gate — backlog item 3.)
Whether ANY channel couples behavior to the model's own readout — text/prompt is
compliance-only (AH); the reward channel is under test (AI). The new J-space fork asks
whether prior residual writes were aimed too late: the next causal successor should
register a calibrated held-out contrast comparing hs23=25, hs26=75, hs29=125
against hs34=175 on the same two-signal both-tail selectivity surface before
claiming a workspace actuator.

---

## Five-paper line (canonical as of 2026-07-01)

| Paper | Scope | Draft |
|-------|-------|-------|
| P1 | Taxonomy / C1–C5 / policy-vs-signal framework | `paper1-taxonomy-framework-draft-v0.md` |
| P2 | Training regimen (SFT/DPO/KTO/GRPO) | `paper2-training-regimen-draft-v2.md` |
| P3 | "Knows but Doesn't Say" — internal gap + training-resistance | `paper3-knows-but-doesnt-say-draft-v0.md` |
| P4 | Two-signal readout (training-free, cross-size/-family/-seed) | `paper4-two-signal-readout-draft-v0.md` |
| P5 | Steering / actuation | scaffold on `experiment/paper5-confidence-steering` |

Figure/script prefixes are legacy (`fig-p1-*` = Paper 2, `fig-p2-*` = Paper 3,
`fig-p3-*` = Paper 4). Amendment labels stay out of paper prose; traceability lives in
provenance appendices.
