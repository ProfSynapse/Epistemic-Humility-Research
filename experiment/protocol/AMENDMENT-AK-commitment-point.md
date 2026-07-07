---
amendment: AK
slug: commitment-point
status: RESOLVED 2026-07-06. AK-G1 MISS, AK-G2 MISS (floor not cleared),
  AK-G3 MISS-with-confound (see outcome + section 8). Stage 1 scored commit
  069427dd; Stage 2 ran on Modal (ephemeral app eh-ak-stage2,
  ap-jPgOtPQGaWu4yeC3YX7q7j, started 07:26 EDT, app stopped same day) and was
  scored CPU-side against the pulled staging artifacts. AK-G2's effect-size
  floor was locked from the pre-stated pilot formula (COMMITTED_FLOOR =
  5.291963) before the full-run G2 readout, per plan.
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
outcome: >-
  AK-G1 MISS (delta -0.0175 on grpo-v2, need >= +0.10); AK-G2 MISS, floor not
  cleared (|contrast| 4.6234 < floor 5.291963, though perm p < 0.01); AK-G3
  MISS on the pre-registered ratio test (every dose ratio 0/nan, no CI clears
  2.0) but the gen_stream arm shows a diagnosed instrumentation confound
  (100% of 328 matched rows are byte-identical across all seven alphas,
  versus 24% varying under anchor-only), so the G3 MISS is not adopted as a
  confirmed causal null pending a real-generate() hook-firing check. Both the
  user's and the orchestrator's AK-G1 call (PASS) missed; AK-G2's fork is
  unadjudicated (gate MISS); AK-G3 is unresolved pending the confound.
scoreboard: >-
  G1 both predictions wrong (both called PASS, actual MISS). G2 gate MISS on
  the gated arm -- no path claimed; descriptively the gated arm's confab
  stratum slope is +11.78 (rising), nominally consistent in sign with the
  user's H-rise, but the refuse stratum rises faster (+16.41), which is why
  the contrast misses the floor -- neither H-rise-throughout nor
  H-flat-then-rise is licensed by a MISS. G3 computed MISS but confounded by
  a likely gen_stream hook-firing bug (see section 8); not treated as
  adjudicating the scoreboard or the falsifier.
---

# Amendment AK — Commitment-Point Extraction

Status: **RESOLVED 2026-07-06** (AK-G1 MISS, AK-G2 MISS, AK-G3
MISS-with-confound; the authoritative status block and scoring provenance are
in the frontmatter above, the verdict detail in §8). Signed 2026-07-04 after a
pre-signing options review that restructured AK-G2 from a directional gate into
a three-way pre-registered fork (see §4). The §5 launch preconditions were
subsequently met: the Amendment AI arc resolved and the GPU launch was
approved; Stage 1 was scored at commit 069427dd and Stage 2 ran on Modal and
was scored CPU-side against the pulled staging artifacts. The AK-G2 effect-size
floor locked from the pilot via the formula pre-stated in §4, a computation and
not a judgment call, so no goalpost moved.

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

## 8. Result

Scored CPU-only from committed/pulled artifacts; no GPU touched for scoring.
Scripts: `amendment_ak_stage1_analyze.py` (Stage 1, seed 20260705, commit
069427dd) and `amendment_ak_stage2_score.py` (Stage 2, seed 20260706, run
2026-07-06). Stage 2 inputs pulled from the private staging repo
`professorsynapse/eh-al-prep-staging` path `ak-stage2-raw-base-r1/data/`
(`rows.jsonl`, `manifest.json`, `direction.json`; 4,592 rows = 328 matched
rows x 2 positions x 7 alphas, config_sha `cf36fc82cd0e3b6e`).

### AK-G1 (crystallization, gated on grpo-v2) -- MISS

Veto AUROC at answer-end minus first-visible on grpo-v2: **-0.0175**
(first-visible 0.9424 [0.9299, 0.9534]; answer-end 0.9248 [0.9084, 0.9390]).
Need >= +0.10. The veto is already near-saturated at the first visible token
and drifts slightly down by answer-end -- it does not crystallize across the
answer window at this granularity on the gated arm. Raw-base (descriptive)
rises +0.0341, still far under the bar.
Source: `analysis-committed/ak_stage1_gate_report.json` (`AK_G1`),
`analysis-committed/ak_stage1_gate_verdicts.md`.

### AK-G2 (doubt-trajectory discriminability, three-way fork) -- MISS (floor not cleared)

Gated arm (grpo-v2): confab-vs-refuse slope contrast **-4.6234**, CI95
[-5.382, -3.884], permutation p = 1.0e-04. COMMITTED_FLOOR = 5.291963 (locked
pre-full-run from the ~50-row pilot via 3 x SE(slope contrast), see
`analysis-committed/ak_stage1_pilot_floor.json`). Condition (b) p < 0.01
holds; condition (a) |contrast| >= floor fails (4.6234 < 5.292). The doc
requires both, so this is a MISS and **no doubt-trajectory path is claimed**
on the gated arm.

Descriptive context only (not the gate surface): on grpo-v2 both strata rise
across the answer window (confab mean slope +11.78, refuse +16.41) -- the
contrast is negative because refuse rises faster, not because confab is
flat or dropping. Raw-base (descriptive) shows confab dropping (-3.50) while
refuse rises (+5.82), a contrast that does clear the floor. The gated and
descriptive arms disagree in direction on the confab stratum; per doc §4
this divergence is reported, not adjudicated, here.
Source: `analysis-committed/ak_stage1_gate_report.json` (`AK_G2`).

### AK-G3 (steering asymmetry, Stage 2) -- MISS, with a diagnosed instrumentation confound

Pre-registered statistic: ratio = |shift(gen_stream)| / |shift(anchor)| on
the matched confab-rate shift from the alpha=0 baseline, paired row-level
bootstrap (2000 resamples, seed 20260706). Guards: schema_ok=True,
coherence_ok=True (0% degenerate every arm).

| dose | sign | shift anchor | shift window | ratio | ratio CI95 |
|---|---|---|---|---|---|
| 0.5 | + | 0.0 | 0.0 | nan | [0.0, 0.0] |
| 0.5 | - | 0.0 | 0.0 | nan | [0.0, 0.0] |
| 1.0 | + | 0.0 | 0.0 | nan | [0.0, 0.0] |
| 1.0 | - | 0.0 | 0.0 | nan | [0.0, 0.0] |
| 2.0 | + | 0.0 | 0.0 | nan | [0.0, 0.0] |
| 2.0 | - | 0.003 | 0.0 | 0.0 | [0.0, 0.0] |

No dose clears the >= 2.0 ratio floor; point estimate at every dose is 0 or
undefined. On the face of it this is a MISS.

**Confound, diagnosed from the raw rows (not fabricated, computed from
`rows.jsonl`)**: 328/328 (100%) of gen_stream-condition matched rows are
byte-identical (confab, refused, answered, AND n_generated all equal) across
every one of the seven alphas from -2 to +2 sigma. The anchor condition,
steering only the single prefill token with the same alpha*sigma dose, shows
variation in 79/328 rows (24%). A per-decode-step push of up to 2 sigma
(~8.9 raw units at L24) sustained across the whole answer window changing
*nothing* in *any* of 328 rows, while a *single-token* push of the same
per-step magnitude already changes 24% of rows, is not a plausible causal
null; it is the signature of the intervention not reaching the model during
generation. The pre-launch readback check (`_readback_check` /
`smoke_manifest.json`) verified only the anchor mode, via a raw
`model(..., use_cache=False)` forward call -- explicitly NOT the gen_stream
decode path (the script's own comment: "gen_stream per-decode steering is
exercised by the full-run pass_log and the CPU controller regression test").
That regression test (`test_gen_stream_is_the_answer_window_condition`)
exercises only the pure-Python `GenerationHookController` dispatch logic on
synthetic zero-tensors; it does not confirm the registered forward hook
fires during Unsloth `FastLanguageModel.for_inference`'s real cached
`generate()` decode loop. The most likely mechanism is that the optimized
decode path does not route through the hooked module's `forward()` the way
the anchor-mode prefill call does.

**Disposition**: AK-G3 is reported as a computed MISS per the pre-registered
formula (no goalpost moved), but is **not adopted as a confirmed causal
finding**. The falsifier's second leg ("no steering asymmetry") is not
treated as established until the gen_stream hook is verified against a real
`model.generate()` call (e.g., compare logits/hidden states with and without
the hook mid-decode) and, if the confound is real, Stage 2 is rerun.
Source: `experiment/phase1/probe/analysis/ak_stage2/ak_stage2_g3_report.{json,md}`
(untracked, reproducible via `amendment_ak_stage2_score.py --rows
<pulled rows.jsonl> --out-dir <dir>`).

### Falsifier

Doc §4: "flat crystallization curve (G1 miss) AND no steering asymmetry (G3
miss)". G1 is a clean MISS. G3 is a computed MISS but confounded (above).
**The falsifier's wording is technically matched by the numbers, but is NOT
treated as adjudicated** given the G3 confound -- calling the
commitment/veto middle "not token-localized" on a null that is plausibly an
instrumentation artifact would misrepresent a data-quality problem as a
scientific finding.

### Predictions vs actual

| gate | user called | orchestrator called | actual |
|---|---|---|---|
| AK-G1 | PASS | PASS (~80%) | **MISS** -- both wrong |
| AK-G2 path | H-rise | H-flat-then-rise (~55%) | **MISS on floor** -- no path adjudicated; gated-arm confab slope is directionally rising (+11.78), nominally closer to the user's call in sign, but the gate cannot license either pick |
| AK-G3 | PASS | PASS (~75%) | **MISS, confounded** -- neither call confirmed; verdict pending confound resolution |

**One-sentence verdict**: AK-G1 and AK-G2 are clean MISSes on the
pre-registered gates (the veto is already assembled at the first visible
token and the doubt-trajectory contrast does not clear its pilot-locked
floor), AK-G1 falsifying both predictions outright, while AK-G3 is a MISS by
the formula but is confounded by a likely gen_stream hook-firing bug and
should not be read as evidence against token-localized commitment until
that is checked.

## Changelog

- 2026-07-04: created and signed (three-way G2 fork restructure at signing;
  dual predictions recorded).
- 2026-07-05: Stage 1 gate analysis committed (commit 069427dd): AK-G1 MISS,
  AK-G2 MISS (floor not cleared); pilot floor locked before the full-run
  readout.
- 2026-07-06: Stage 2 launched and ran on Modal (app eh-ak-stage2); AK-G3
  scored CPU-side from the pulled staging outputs: MISS by the
  pre-registered formula, flagged with a diagnosed gen_stream
  instrumentation confound (section 8). Full outcome + section 8 written;
  falsifier wording matched numerically but not adjudicated pending the
  confound check.
