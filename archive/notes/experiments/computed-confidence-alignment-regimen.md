---
title: 'Computed-confidence alignment regimen: SFT seeds structure, GRPO/DPO/KTO align internals'
kg:
  id: experiment:computed-confidence-alignment-regimen
  type: experiment
  status: canonical
tags:
  - kg/experiment
  - grpo
  - sft
  - calibration
  - reward-design
  - regimen
status: proposed
governance: exploratory
phase: phase1
lane: local
est_compute: 'dataset rebuild GPU-free (probe outputs already exist); each training arm ≈ one SFT or one GRPO seed at 4B'
relationships:
  - type: tests
    target: '[[gap-4-probe-transfer]]'
    target_id: gap:4-probe-transfer
    confidence: medium
  - type: builds_on
    target: '[[grpo-v3-proper-scoring-confidence]]'
    target_id: experiment:grpo-v3-proper-scoring-confidence
related:
  - '[[grpo-v3-proper-scoring-confidence]]'
  - '[[caution-vs-doubt-knowledge-gate]]'
---

## Question & Hypothesis

**Division of labor (user's framing, adopted).** SFT's job is to teach the
**output structure** (the `{answer, response_confidence}` schema) and the
**vocabulary of abstention** ("I don't know"). The *alignment* of the confidence
number to reality — internal AND external — is the job of the preference-stage
trainings (GRPO / DPO / KTO). The current mech-interp probe model
(`clean-sft-grpo-v2`) is therefore **fine to keep probing**: probing is about
reading the internal axes, not about whether the emitted number is honest.

## Audit result (2026-06-27) — this CORRECTS two assumptions in v1 of this note

A read-only audit of session 0018 ([[0018 - probe-scaled-response-confidence-retrain]])
overturns the original premise of this note. Both corrections below are recorded
verbatim because they change where the fix belongs.

**Correction 1 — the clean SFT base is NOT a flat-0.8 prior.** The `clean`
projection that became the GRPO base has **2489 unique confidence values**, range
**0.35–0.9**, mean 0.788, largest exact-target count only 17 (§009). The "0.8" is
just a band *centre*, not the label on every row. So the collapse is **not** an
SFT flat-label artifact.

**Correction 2 — probe-scaled (computed) SFT was already run, and it COLLAPSED.**
The full probe-scaled SFT (`0.1 + 0.8·appropriateness_p`) trained and passed
JSON-format eval, but emitted a **single** confidence value (0.8765) on every row
(§004). Cause: the *target distribution itself* is imbalanced — the modal target
0.8765 covered **81.79%** of rows (low-band rows: 0), because most knowns are
answerable → high `appropriateness_p` → high target. SFT minimised loss by
emitting the mode. It was explicitly **paused and not taken downstream**. The
team's anti-collapse answer was deterministic **band-spreading** (contrastive,
then the clean projection), which spreads the *distribution* by role but is **not
per-question-grounded calibration**.

**Where the collapse actually comes from (revised causal story).** The clean SFT
base emits a spread; **GRPO is what destroys it.** GRPO v1 already showed
known/unknown confidence means nearly identical (0.746 vs 0.747), values
concentrated in a few bands, top value 0.711 on 1521 rows (§023); GRPO v2 then
tightened to std 0.015 (session 0026). The v1/v2 rewards made a near-constant
confidence reward-optimal, so the preference stage *collapsed* the spread the SFT
stage had. **Therefore the primary lever is the GRPO reward (v3), not redoing the
SFT dataset.** "Redo SFT with computed confidence" — the original ask — is largely
*unnecessary for anti-collapse* (clean SFT is already spread) and *insufficient on
its own* (naive probe-scaled collapses at SFT from target imbalance).

**What was already measured vs what session 0026 added.** Emitted-confidence
**Brier vs appropriateness** WAS computed at eval (GRPO v1: 0.3697, §023). Session
0026 added the ECE / std / correct-vs-wrong-AUROC framing and the internal-axis
comparison. So "calibration was never measured" is wrong; the *internal vs
external coherence gap* is what 0026 contributed.

## Question & Hypothesis (revised)

**Division of labor (user's framing — and the 0018 team's, §416).** Session 0018
states it independently: "SFT teaches format and broadly appropriate
response-confidence expression; DPO/KTO/GRPO then tune accuracy, abstention, and
calibration." The user's instinct matches the existing design intent. The current
mech-interp probe model (`clean-sft-grpo-v2`) is **fine to keep probing** —
probing reads the internal axes, not whether the emitted number is honest.

**Hypothesis (relocated to the reward).** The emitted-confidence collapse is a
**GRPO-reward artifact**, not an SFT-seed artifact. A **proper-scoring GRPO
reward** ([[grpo-v3-proper-scoring-confidence]], v3) — under which a near-constant
is provably sub-optimal and the true per-question probability is optimal — should
**stop GRPO from collapsing the spread the clean SFT already carries**, yielding
emitted confidence that is graded and calibrated (std ≫ 0.015, ECE < 0.14,
correct-vs-wrong AUROC > 0.56) without degrading behavior, and tightening
internal→output coherence (emitted confidence tracks the L35 doubt projection).

**Secondary, still-open SFT question.** Spread ≠ calibrated. Clean SFT is spread
but role-based, not grounded in per-question difficulty; naive probe-scaled is
per-question-grounded but collapses from distribution imbalance. The genuinely
unexplored SFT-side idea is a **per-question-grounded AND distribution-balanced**
target (quantile-map the probe `appropriateness_p` onto a spread band) — combine
the contrastive anti-collapse property with per-question grounding. This is a
*secondary* arm; the reward fix is primary.

## Preflight result (2026-06-27) — B0 de-risked, GREEN

CPU re-scoring of **19,904 real GRPO rollouts** (v1 full-run `reward_debug`, 4211
distinct prompts; `refused`/`correct` re-derived with the base reward's own
matchers, grouped by gold-answer set) with the v3 reward
(`experiment/phase1/grpo/v3_reward_preflight.py <reward_debug.jsonl>`):

- **Q1 — group-target spread (THE risk):** per-prompt mean-appropriateness targets
  span **0.000–1.000, mean 0.571, std 0.320**; **65.6%** of prompts fall in
  [0.2, 0.8]. The distribution is broad, not a spike → the "Brier optimum is still
  ~constant" collapse-one-level-up risk is **NOT realized**. v3's group target has
  real per-prompt dynamic range to move confidence. (Spread is a property of the
  fixed question set's difficulty range, so it survives the policy shift during
  training.)
- **Q2 — behavior ordering on real data:** `known_correct +3.04 > unknown_abstain
  +2.20 > known_wrong −0.45 > known_over_refusal −1.78` (also unknown_answer
  −0.62). Behavior dominance holds on rollouts, not just unit tests.
- **Q3 — proper scoring beats the flat prior:** emitting the group target beats a
  flat 0.82 on **4211/4211** prompts (mean Brier gain +0.394). The constant is
  strictly sub-optimal everywhere — exactly the mechanism v3 installs.

**Reading:** B0 is well-posed. The one quantitative risk that could have made v3 a
no-op (degenerate group targets) is empirically absent in this question set. Caveat:
targets here are computed from the v1 policy's accuracy; the *level* shifts as the
policy improves, but the *spread* (driven by question difficulty) is robust. Self-
consistent matcher caveat: re-derived correctness uses the same base matcher v3
uses in-loop, so the preflight and training agree by construction.

## Design — primary reward arm + attribution controls

The audit collapses the original 2×2 (two of its four cells are already answered).
What remains:

| Arm | SFT base | Alignment | Status / question |
|-----|----------|-----------|-------------------|
| ref | clean (spread) | GRPO-v2 | `clean-sft-grpo-v2` — historical reference; std 0.015 (collapsed by GRPO) |
| A1  | probe-scaled | — (SFT only) | **DONE (§004): collapses to a single value (0.8765), target imbalance** |
| A0  | clean (spread) | — (SFT only) | known result: SFT carries a spread (2489 values) but role-based, not calibrated; re-measure emitted std/ECE if a number is wanted |
| **B0** | clean (spread) | **GRPO-v3** | **PRIMARY: does proper-scoring stop GRPO collapsing the SFT spread?** |
| B1  | quantile-balanced probe-scaled | GRPO-v3 | secondary: does a per-question-grounded *and* balanced SFT seed help on top of v3? (needs the new quantile target — not the naive probe-scaled that collapsed) |

**B0 is the headline.** It isolates the single most-supported hypothesis: the
collapse is a reward artifact, so the v3 reward alone (on the existing clean SFT
base) should recover graded, calibrated confidence. If B0 succeeds, "redo the SFT
dataset" is unnecessary. If B0 fails (confidence still collapses under a proper
score), the SFT prior or the group-target variance is implicated → escalate to B1.

Note the original A1 ("can SFT alone teach calibration?") is **already answered**:
naive computed per-question targets collapse SFT to the mode. SFT can carry a
*spread* (clean projection proves it) but not a *naively-grounded* one.

**DPO / KTO arms (optional, later).** The same computed-confidence dataset already
emits DPO/KTO projections. Worth adding `probe-scaled → DPO` and `probe-scaled →
KTO` once the GRPO arms show signal, to compare which alignment objective best
externalizes the internal signal. Keep these behind the GRPO result to avoid
spending compute on all objectives before knowing the seed matters.

## Prerequisites & Gating

- Verify/refresh the probe-scaled dataset: the 32-sample probe outputs must exist
  for the train split (they do for the probe pool; confirm coverage). Rebuild is
  GPU-free if probe JSONL is present.
- v3 reward is drafted + tested ([[grpo-v3-proper-scoring-confidence]]); B0/B1 use
  `target_mode="group"` by default (anchors to realized appropriateness; no extra
  forward pass). An `internal`-target science arm can come later.
- **Governance:** this is a NEW regimen, exploratory. It does NOT touch the
  PROTOCOL v0.3 locked headline matrix or the v2 reward. Any training run needs
  explicit user sign-off and a governed amendment with changelog. Drafting this
  launches nothing.

## Runbook

1. ~~(prereq) Audit session 0018~~ **DONE (2026-06-27)** — see Audit result above.
   Probe-scaled was run and collapsed; clean SFT is spread; collapse is GRPO-driven.
2. **B0 (primary, gated, sign-off):** train clean SFT (existing base) → GRPO with
   the v3 proper-scoring reward (`target_mode="group"`). Eval emitted-confidence
   std / ECE / correct-vs-wrong AUROC + behavior vs `clean-sft-grpo-v2`. This is
   the single highest-ROI run.
3. ~~CPU preflight before B0~~ **DONE (2026-06-27) — GREEN, see Preflight result.**
   Re-scored 19,904 real GRPO rollouts: group targets spread (std 0.320 over 4211
   prompts), behavior ordering preserved, calibrated beats flat on 4211/4211. The
   collapse-one-level-up risk is NOT realized in the data.
4. If B0 falls short: build the **quantile-balanced probe-scaled** SFT target (per-
   question grounded AND distribution-spread, unlike the §004 naive version), train
   B1 (→ GRPO-v3), compare.
5. Re-probe the winning arm: does emitted confidence now track the L35 doubt-axis
   projection (internal→output coherence improved)? Closes the mech-interp → RL loop.
6. (later) DPO/KTO arms only after a GRPO arm shows signal.

## Validation contract

- CPU preflight: v3 re-scoring preserves behavior ordering on v2 rollouts AND the
  per-prompt group targets are non-degenerate (spread across difficulties).
- Definition of done (per trained arm): emitted confidence std ≫ 0.015 AND ECE <
  v2's 0.142 AND correct-vs-wrong AUROC > v2's 0.56, with over-refusal and
  unknown-answer rates no worse than `clean-sft-grpo-v2`.
- Attribution: B0 isolates the reward's contribution (clean SFT held fixed vs the
  v2 reference); B1−B0 isolates any added value of a balanced computed SFT seed.
- Power: correct-vs-wrong eval needs more wrong-answered rows than the 16
  currently available (shared limitation with [[caution-vs-doubt-knowledge-gate]]).

## Outputs & provenance

Datasets via `build_schema_response_confidence_datasets.py` (existing builder).
Configs alongside the existing `sft_schema_probe_scaled_response_confidence_*`
family. Findings to `docs/sessions/20260627T093723Z-caution-vs-doubt-knowledge-gate.md` and
here. Does not feed meta-analysis or alter PROTOCOL v0.3 cells without amendment.

## Variations

- `internal`-target GRPO arm (v3 `target_mode="internal"`): seed SFT with computed
  confidence, then align GRPO to the L35 doubt-axis probe estimate — literal
  internal-alignment; compare convergence vs the group (truth-anchored) target.
- Probe-scaled formula sweep (`0.1 + 0.8·p` vs identity vs temperature-scaled p).
- Larger n_samples for the probe (32 → 64) to tighten the per-question target.

## Status log

- 2026-06-27: created (proposed). Motivated by the calibration-gap finding and the
  v3 reward draft. Original (now-superseded) premise: clean SFT is a flat-0.8 prior
  and redoing SFT with computed confidence is the novel work.
- 2026-06-27: **session-0018 audit DONE — premise corrected.** (1) Clean SFT is NOT
  flat: 2489 unique values, 0.35–0.9 (§009). (2) Probe-scaled SFT was already run
  and collapsed to a single value 0.8765 from 81.79% target imbalance (§004) —
  paused, not taken downstream. (3) The collapse is **GRPO-driven**: clean SFT
  emits a spread; GRPO v1/v2 destroyed it (v1 known/unknown means 0.746/0.747,
  banded, §023; v2 std 0.015, session 0026) because the reward made a constant
  optimal. **Reframe: the primary lever is the v3 GRPO reward (arm B0), not redoing
  SFT.** "Redo SFT with computed confidence" is unnecessary for anti-collapse and
  insufficient alone. Secondary open arm: quantile-balanced per-question SFT target.
  Brier-vs-appropriateness was already an eval metric (0.3697, §023); session 0026
  added the ECE/AUROC/internal-coherence framing. Design only; B0 awaits sign-off.
- 2026-06-27: **CPU preflight DONE — B0 de-risked, GREEN** (see Preflight result).
  19,904 real rollouts re-scored with v3: group targets spread (std 0.320 / 4211
  prompts, 65.6% in [0.2,0.8]); behavior ordering preserved; calibrated beats flat
  on 4211/4211 (mean Brier gain +0.394). The degenerate-target risk is empirically
  absent. B0 remains gated on user sign-off + a governed amendment before any run.
