---
amendment: AK
slug: commitment-point
status: SIGNED 2026-07-04 (user directive "Proceed" after the pre-signing
  options review) — NOT LAUNCHED; launch gated behind Amendment AI resolution
  and explicit user GPU approval; AK-G2's effect-size floor locks from the
  pre-stated pilot formula before any full-run readout
question: >-
  Where along the generation trajectory does the fabricate-anyway commitment
  happen: does the post-generation veto crystallize across the answer tokens
  (as the re-derivation result predicts), and what does the doubt-trunk
  reading do while the fabrication is being written (rise, stay flat, or
  drop)?
predictions:
  user:
    calls:
      AK-G1: PASS (crystallization rise)
      AK-G2-path: H-rise — doubt increases across the confab answer window
      AK-G3: PASS (window asymmetry)
    recorded: 2026-07-04
    quote: >-
      "I don't think the lie overwrites doubt and I bet doubt increases. I
      will be optimistic about the window asymmetry as well."
  orchestrator:
    calls:
      AK-G1: PASS (~80%)
      AK-G2-path: H-flat-then-rise — mostly carried, climbing near answer
        end (~55%; second pick H-rise throughout)
      AK-G3: PASS (~75%)
    recorded: 2026-07-04
    basis: >-
      G1/G3 follow the item-31 re-derivation logic directly (transported
      floor 0.58-0.64 vs in-position 0.81-0.86; carried fraction r ~
      0.34-0.37). On G2 the answerability-transport result (0.96-0.99)
      argues against overwrite and for a carried, largely flat trunk
      reading, with the Amendment U high-distrust endpoint pulling the tail
      upward.
outcome: null
scoreboard: pending — G2 path is a genuine partial disagreement (user
  rise-throughout vs orchestrator flat-then-rise); G1/G3 both called PASS
---

# Amendment AK — Commitment-Point Extraction

Status: **SIGNED, NOT LAUNCHED.** Signed 2026-07-04 after a pre-signing
options review that restructured AK-G2 from a directional gate into a
three-way pre-registered fork (see §4). Launch preconditions in §5 remain
open: the Amendment AI arc must resolve first (GPU sequestered) and the GPU
launch needs explicit user approval. The AK-G2 effect-size floor locks from
the pilot via the formula pre-stated in §4 — locking it is a computation,
not a judgment call, so no goalpost can move.

## 1. Motivation and strategic position

The session-0037 fleet (TODO items 30/31, PR #196; KG PR #197) cornered
confabulation from both ends but left the middle untraced:

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
commitment signal is a decision variable rather than a correlate, steering
it in the right window should move the confab rate.

## 2. Hypotheses

- **H-crystallize** (gated, AK-G1): veto readability rises from near its
  transported floor (~0.6) at the first answer token toward its in-position
  ceiling (~0.85) across the answer window, with the midpoint inside the
  window (not at the anchor).
- **Doubt-trajectory fork** (gated for discriminability, AK-G2; the winning
  path is the finding, adjudicated on the scoreboard):
  - **H-rise** (user): the doubt-trunk projection on confab rows climbs as
    fabricated tokens accumulate — the model reads its own emerging
    fabrication and gets more alarmed.
  - **H-flat** / **H-flat-then-rise** (orchestrator): the trunk reading is a
    carried question property (per the answerability transport result),
    largely flat, with at most a climb near answer end.
  - **H-drop** (original draft, now the underdog): the fabrication
    overwrites the doubt reading. Already in tension with the 0.96–0.99
    answerability transport.
- **H-commitment-causal** (gated, AK-G3, Stage 2 only): steering along the
  arm-B commitment direction (orthogonalized to caution) in the answer-token
  window shifts confab-vs-refuse; anchor-only steering moves at most the
  carried minority (item 31: same-row carried projection r ≈ 0.34–0.37).

## 3. Design (two stages, one GPU extraction pass per checkpoint + one steering pass)

### 3.1 Stage 1 — position-sweep read (extraction, no intervention)

- Surface: reuse the AH stage-0 question pool rows that produced the arm-B
  matched set (confab vs refuse at matched caution, n≈328 matched + full
  1,338 population), regenerate with per-token hidden-state capture at the
  anchor, each thinking-segment boundary, first visible token, and every
  k-th answer token through answer end.
- Checkpoints: **both** the raw instruct base (arm-B's native surface) and
  clean-SFT→GRPO-v2 (the deployed checkpoint, MORE re-derived per item 31,
  so the crystallization curve should be steeper). **AK-G1 gates on
  grpo-v2**; the raw-base curve is reported descriptively alongside it.
- Readouts per position: frozen doubt trunk, frozen caution axis, arm-B
  commitment direction, veto/correctness axis (refit per position
  out-of-fold where a frozen axis is position-mismatched — item 31 showed
  frozen correctness axes do not transport across positions). Per-position
  refits carry the AJ equal-rank random-direction control as the artifact
  guard.
- Pilot: the first ~50 rows of the sweep are the AK-G2 pilot; they lock the
  G2 floor via the §4 formula and are then excluded from the G2 test set.
- Deliverables: crystallization curve (veto AUROC vs position), doubt-trunk
  trajectory curves (confab vs refuse strata), commitment-direction carry
  curve.

### 3.2 Stage 2 — answer-window steering (intervention, gated on Stage 1)

- Steer ± the commitment direction (orthogonalized to the caution axis, per
  the B1 convention) at L24–28, in two position conditions: anchor-only vs
  answer-window (from first visible token onward). Doses from the AA/AG
  authorized-knob grid. Outcome: confab rate on matched unanswerable rows;
  guards: schema validity, degenerate-output fraction, length drift.
- Checkpoint: raw instruct base primary (the arm-B direction is native
  there). A grpo-v2 refit-and-steer cell (per the Amendment T
  refit-per-checkpoint rule) is an authorized follow-on knob, not a gate
  surface.
- Stage 2 launches only after Stage 1 readout and remains gated on the
  batching-engine parity mandate (TODO item 11).

## 4. Gates (LOCKED at signing, except the G2 floor which locks by formula)

- **AK-G1 (crystallization, gated on grpo-v2)**: veto AUROC at answer-end
  minus veto AUROC at first visible token ≥ **+0.10**. Derivation: item 31's
  transported floor 0.58–0.64 vs in-position 0.81–0.86 implies an expected
  rise of ~0.20; fold spread on these surfaces ran 0.014–0.03, so half the
  expected effect (+0.10) sits ≥ 3 SE clear of noise while not assuming the
  full effect reproduces at token granularity.
- **AK-G2 (doubt-trajectory discriminability, three-way fork)**: the gate is
  about *power, not direction*. PASS requires (a) the confab-vs-refuse
  slope contrast on the doubt-trunk trajectory clears the pilot-locked
  floor, AND (b) permutation p < 0.01. **Floor formula (pre-stated)**:
  floor = 3 × SE of the slope contrast measured on the ~50-row pilot,
  computed and committed to the run record before the full-run G2 readout.
  Which path wins (H-rise / H-flat(-then-rise) / H-drop) is the finding and
  scores the scoreboard's partial disagreement; a G2 MISS means the data
  cannot adjudicate the fork at this n and no path is claimed.
- **AK-G3 (steering asymmetry, Stage 2)**: answer-window steering moves
  confab rate by ≥ **2×** the anchor-only condition at matched dose, with
  anchor-only bounded above by the carried-minority prediction. Derivation:
  item 31 attributes roughly 1/3 of the veto to carried signal (r ≈
  0.34–0.37), so if the commitment state is used where it is re-derived, the
  window condition should carry at least the remaining 2/3; 2× is the
  smallest ratio that cleanly separates the two mechanisms given AG-scale
  dose noise (±34pt effects had CI half-widths ~6–7pt).
- **Falsifier**: flat crystallization curve (G1 miss) AND no steering
  asymmetry (G3 miss) = the commitment/veto middle is NOT token-localized;
  the anchor-vs-answer-window framing is wrong and Paper-5 steering should
  stay at the anchor.

## 5. Preconditions and approvals

1. Amendment AI arc resolved and merged (GPU sequestered until then).
2. ~~User signs this amendment~~ — SIGNED 2026-07-04; dual predictions
   recorded in the frontmatter; G2 floor locks by the §4 formula.
3. Explicit user approval for the GPU launch (standing rule) — NOT yet
   given; signing is not launch approval.
4. Batching-engine parity (TODO item 11) is NOT a blocker for Stage 1
   (extraction only); it gates Stage 2 steering per the standing user
   mandate.

## 6. Instrumentation (descriptive, gate-free)

- **Texture gradient**: arm A's specificity leak predicts that if doubt
  rises mid-generation, the fabrication should get vaguer as it goes —
  specificity and fact density of late answer segments vs early ones,
  text-side only, zero extra GPU. A rise finding paired with a matching
  texture gradient is much harder to dismiss as probe artifact.
- Commitment-direction trajectory on refuse rows (does the answer-pull decay
  once the refusal is underway?).
- Per-flavor splits of the crystallization curve (connects to the per-flavor
  threshold result from session 0036).

## 7. Interpretive caveats (pre-stated)

- Stage 1 is readout-not-causal; only Stage 2 can claim use.
- Per-position refits risk position-specific artifacts; the equal-rank
  random-direction control from AJ carries over as the guard.
- The doubt-trunk trajectory is measured with a probe fit at the anchor;
  a flat curve could reflect either a carried reading or probe insensitivity
  to position drift — the per-position refit comparison is the check.
- Single seed, single model family until the item-24/28 replication program
  reaches this line.
