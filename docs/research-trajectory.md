# Research Trajectory — Epistemic Humility Program

_Updated 2026-07-03. Replaces the stale 2026-06-10/06-30 versions. Every claim traces
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
release is resisted (AG PASS). That is Paper 5's open question.

---

## Paper 2 — training regimen (COMPLETE)

Pipeline on `main` (PR #1). SFT-warmed DPO/KTO/GRPO on Qwen3-4B controlled within-model.
Cold-start arms failed (3 seeds). Training moves behavioral refusal; the
abstention-calibration tension holds across all methods. GRPO variants (Amendments
B/F/J/K/L/M/N) are SIGNED; most untested relative to the readout arc.
Draft: `paper2-training-regimen-draft-v2.md`. Figures: `fig-p1-*` (legacy prefix).

---

## Paper 3 — "Knows but Doesn't Say" (diagnosis complete; §7–8 absorption pending)

Internal axis encodes answerability at AUROC 0.997, transfers cross-dataset cold
(Amendment P: KUQ→SelfAware 0.983), and predates post-training (Amendment Y: present on
the pre-trained base). Stated confidence stays decoupled. Training-resistance is the
headline: DPO/KTO/GRPO/contrastive-SFT/proper-scoring all fail to couple the channel
(Amendments M/R FALSIFIED; Phase B joint co-training FALSIFIED). Behavioral abstention
is installable; accurate emitted confidence is not. Backlog item 12: absorb old
draft-v2 §7–8 (proper-scoring, contrastive, RL-on-contrastive depth).
Draft: `paper3-knows-but-doesnt-say-draft-v0.md`. Figures: `fig-p2-*` (legacy prefix).

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

**Open questions for Paper 5:** Does a trained-checkpoint steering arm move the gate?
(AA was flat on the raw base; trained checkpoints have a live gate — backlog item 3.)
Divergent-pool (probe ≠ gold) design for true own-readout attribution (AF §8 / AG §9.4).

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
