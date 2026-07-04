---
amendment: AK
slug: commitment-point
status: DRAFT — NOT SIGNED (skeleton for user sign-off; gates PROPOSED, not locked)
question: >-
  Where along the generation trajectory does the fabricate-anyway commitment
  happen, and does the post-generation veto crystallize across the answer
  tokens (as the re-derivation result predicts) rather than being present at
  the anchor?
predictions:
  orchestrator:
    call: TBD at signing
    confidence: TBD
    recorded: null
    basis: >-
      To be recorded before launch per the standing dual-prediction practice.
      Priors pointing the same way: item 31 found the veto predominantly
      re-derived (cross-position transfer 0.58-0.64 vs 0.81-0.86 in-position),
      and item 30 arm B found the commitment direction readable pre-generation
      (matched AUROC 0.834, L24-28 plateau).
  user:
    call: TBD at signing
    recorded: null
outcome: null
scoreboard: null
---

# Amendment AK — Commitment-Point Extraction (DRAFT skeleton)

Status: **DRAFT, NOT SIGNED.** This is the item-32 skeleton produced from the
session-0037 fleet results (TODO items 30/31, PR #196; KG PR #197). Gates
below are PROPOSED with their derivations shown, per the aim-small-miss-small
rule (thresholds derived from expected effect size + uncertainty, never round
defaults). Nothing launches until the user signs, records a prediction, and
the Amendment AI arc resolves (GPU is sequestered until then).

## 1. Motivation and strategic position

The session-0037 fleet cornered confabulation from both ends but left the
middle untraced:

- **Pre-generation (arm B)**: at matched caution and flavor, the activations
  already lean fabricate-vs-refuse (AUROC 0.834 ± 0.014, direction cos 0.32
  to the doubt trunk, peaking L24–28 and plateauing).
- **Post-generation (item 31)**: the veto is predominantly re-derived from
  the emitted answer (correctness axis fails cross-position transfer while
  answerability transports at 0.96–0.99; post-beats-pre survives
  residualizing every carried readout; veto ⊥ doubt, whitened cos −0.02).

Both are position-pair endpoints. The untested middle: token-level
generation-time extraction on confab vs refusal generations, tracing the
doubt trunk, the arm-B commitment direction, the caution axis, and the veto
axis from prompt end through the first visible tokens to answer end. If the
veto is re-derived, it should *assemble* across the answer window; if the
commitment signal is a decision variable rather than a correlate, steering it
in the right window should move the confab rate.

## 2. Hypotheses

- **H-crystallize**: veto readability rises from near its transported floor
  (~0.6) at the first answer token toward its in-position ceiling (~0.85)
  across the answer window, with the midpoint inside the window (not at the
  anchor).
- **H-carry-drop**: on rows that confabulate, the doubt reading present at the
  anchor decays across generation (the fabrication overwrites it); on rows
  that refuse, it persists. Null alternative: doubt persists equally in both.
- **H-commitment-causal** (Stage 2 only): steering along the arm-B commitment
  direction (orthogonalized to caution) in the answer-token window shifts
  confab-vs-refuse; anchor-only steering moves at most the carried minority
  (item 31: same-row carried projection r ≈ 0.34–0.37).

## 3. Design (two stages, one GPU extraction pass + one steering pass)

### 3.1 Stage 1 — position-sweep read (extraction, no intervention)

- Surface: reuse the AH stage-0 question pool rows that produced the arm-B
  matched set (confab vs refuse at matched caution, n≈328 matched + full
  1,338 population), regenerate with per-token hidden-state capture at the
  anchor, each thinking-segment boundary, first visible token, and every k-th
  answer token through answer end. Checkpoint: raw instruct base first
  (arm-B's surface); grpo-v2 as the confirmatory cell (item 31 says it is
  MORE re-derived, so the crystallization curve should be steeper).
- Readouts per position: frozen doubt trunk, frozen caution axis, arm-B
  commitment direction, veto/correctness axis (refit per position out-of-fold
  where a frozen axis is position-mismatched — item 31 showed frozen
  correctness axes do not transport across positions).
- Deliverables: crystallization curve (veto AUROC vs position), carry curves
  (doubt/commitment projections vs position, confab vs refuse strata).

### 3.2 Stage 2 — answer-window steering (intervention, gated on Stage 1)

- Steer ± the commitment direction (orthogonalized to the caution axis, per
  the B1 convention) at L24–28, in two position conditions: anchor-only vs
  answer-window (from first visible token onward). Doses from the AA/AG
  authorized-knob grid. Outcome: confab rate on matched unanswerable rows;
  guards: schema validity, degenerate-output fraction, length drift.

## 4. Gates (PROPOSED — derivations shown; to be locked at signing)

- **AK-G1 (crystallization)**: veto AUROC at answer-end minus veto AUROC at
  first visible token ≥ **+0.10**. Derivation: item 31's transported floor
  0.58–0.64 vs in-position 0.81–0.86 implies an expected rise of ~0.20; fold
  spread on these surfaces ran 0.014–0.03, so half the expected effect
  (+0.10) sits ≥ 3 SE clear of noise while not assuming the full effect
  reproduces at token granularity.
- **AK-G2 (carry-drop)**: difference in doubt-projection slope (confab minus
  refuse strata) significant at perm p < 0.01 with sign matching
  H-carry-drop. Effect-size floor TBD at signing once Stage-1 pilot variance
  is known (aim-small rule: do not pick a round slope threshold before the
  per-position variance is measured on ~50 pilot rows).
- **AK-G3 (steering asymmetry, Stage 2)**: answer-window steering moves
  confab rate by ≥ **2×** the anchor-only condition at matched dose, with
  anchor-only bounded above by the carried-minority prediction. Derivation:
  item 31 attributes roughly 1/3 of the veto to carried signal (r ≈
  0.34–0.37), so if the commitment state is used where it is re-derived, the
  window condition should carry at least the remaining 2/3; 2× is the
  smallest ratio that cleanly separates the two mechanisms given AG-scale
  dose noise (±34pt effects had CI half-widths ~6–7pt).
- Falsifier: flat crystallization curve (G1 miss) AND no steering asymmetry
  (G3 miss) = the commitment/veto middle is NOT token-localized; the
  anchor-vs-answer-window framing is wrong and Paper-5 steering should stay
  at the anchor.

## 5. Preconditions and approvals

1. Amendment AI arc resolved and merged (GPU sequestered until then).
2. User signs this amendment: locks gates (including the AK-G2 effect-size
   floor after the pilot), records the dual predictions in the frontmatter.
3. Explicit user approval for the GPU launch (standing rule).
4. Batching-engine parity (TODO item 11) is NOT a blocker for Stage 1
   (extraction only); it gates Stage 2 steering per the standing user mandate.

## 6. Interpretive caveats (pre-stated)

- Stage 1 is readout-not-causal; only Stage 2 can claim use.
- Per-position refits risk position-specific artifacts; the equal-rank
  random-direction control from AJ carries over as the guard.
- Single seed, single model family until the item-24/28 replication program
  reaches this line.
