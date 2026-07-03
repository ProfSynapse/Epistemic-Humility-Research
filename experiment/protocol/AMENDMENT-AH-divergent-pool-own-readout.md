---
amendment: AH
slug: divergent-pool-own-readout
question: >-
  Does prime uptake consult the model's own readout (H-resonance) or is it
  pure instruction compliance plus boundary distance (H-compliance)?
predictions:
  orchestrator:
    call: H-compliance
    confidence: "75-80%"
    recorded: 2026-07-03
    basis: >-
      AG's doubt axis is anti-semantic and unmoved by primes; the pliability
      law absorbs the hidden state into one boundary-distance scalar; the only
      observed readout-behavior coupling (AC) was wired externally.
  user:
    call: H-compliance
    recorded: 2026-07-03
    quote: >-
      I think prompt is like a shotgun here and overrides most other policies.
      So I think we're still decoupled from internals, if there is something
      it would be too weak I think to do anything about beyond like you say
      maybe coming back to training.
outcome: >-
  H-COMPLIANCE (certified via Addendum A1). G2 release congruence is a
  precise zero (-0.21pt, CI [-4.45, +4.10]); the initial G1 miss (+15.65pt
  on a low-caution stratum) was recalibrated on a caution-representative
  stratum in pre-registered Addendum A1 and passed decisively (+50.98pt vs
  +20pt floor), certifying the instrument and upgrading the verdict per the
  locked §10.2 semantics. Prime uptake does not consult the model's own
  readout.
scoreboard:
  user: win
  orchestrator: win
addendum_a1:
  question: >-
    Does the positive control clear the +20pt induced-refusal floor on a
    caution-REPRESENTATIVE stratum (certifying the already-collected G2
    reading)?
  predictions:
    orchestrator:
      call: PASS
      confidence: "~80%"
      recorded: 2026-07-03
      basis: >-
        AG's +34pt was measured on an unfiltered known population; even the
        hardest (low-caution) stratum gave +15.65pt, so a representative
        stratum should recover well past +20pt.
    user:
      call: PASS
      recorded: 2026-07-03
      quote: "PASS — clears +20pt"
  outcome: >-
    PASS — induced refusal +50.98pt (26/51 eligible) vs +20pt floor;
    monotone caution-quintile gradient (Q1 37.0 -> Q4 100.0) confirms the
    §9.2(1) population diagnosis. Verdict upgraded to H-COMPLIANCE;
    scoreboard row upgraded to WIN/WIN.
---

# Amendment AH — Divergent-Pool Own-Readout Attribution (probe ≠ gold)

**Status: RESOLVED 2026-07-03 — H-COMPLIANCE (certified via Addendum A1)**.
G2 release congruence = −0.21pt (CI [−4.45, +4.10], logistic coef CI
[−0.555, +0.250]) — a precise zero. The initial G1 miss (+15.65pt on a
low-caution stratum) was recalibrated in pre-registered Addendum A1 on a
caution-representative stratum and PASSED (+50.98pt vs the unchanged +20pt
floor), certifying the instrument and upgrading the verdict per the locked
§10.2 semantics. Main result in §9 (verdict there superseded by §10.3);
addendum design, gate, and result in §10. (Signed
2026-07-03, both predictions §2; Stage-0 D-under floor STOP → user-directed
redesign; pool v2.1 locked; main run 3,324 gens on the frozen AF harness,
launched on explicit user approval §7.8.)
**Tier:** A (new evidence cell; gates pre-stated before launch).
**Branch:** `amendment-ah-divergent-pool`.
**Depends on:** AF (PASS, channel-authority), AG (PASS, asymmetric compliance),
session-0035 MI pliability result (boundary-distance law), Stage-0 mining
pass (this doc §4).

---

## 1. Motivation and strategic position

AF established that a second-person system-prompt doubt prime moves refusal
behavior selectively (+18.0pt over permuted). AG established that the same
channel is obeyed even when the prime is wrong (induced refusal on
known-correct +34.0pt) and that the belief axis never moves — compliance
travels through the caution/policy axis. Neither experiment can answer the
question that now matters most, because on the AF/AG pool the probe label and
the gold label agree on 600/600 rows: a prime aligned with the model's OWN
internal readout is byte-identical to a prime aligned with ground truth.

> **Scout correction (2026-07-03, verified by the orchestrator):** the 600/600
> figure is an IN-SAMPLE artifact — the probe scoring its own training rows.
> Under honest out-of-fold scoring (5-fold, `random_state=0`, AG's own CV
> recipe; OOF AUROC 0.9945 reproduces AG's reported value exactly) the same
> pool contains **16/600 natural divergences** (6 D-over, 10 D-under). This
> does not change AF/AG's adjudications — 584/600 concordance still means the
> two prime framings were indistinguishable in those runs — but the correct
> statement is "probe ≡ gold in-sample; ~97% concordant out-of-fold", and it
> establishes that natural probe-vs-gold divergence EXISTS at a low rate on
> the SelfAware distribution.

The two hypotheses — "the model consults its own readout when deciding
whether to take up the prime" vs "the model obeys instruction content, full
stop" — make identical predictions when readout and instruction always agree.
This amendment builds the comparison where they diverge.

**Strategic stakes (user directive, 2026-07-03, recorded verbatim):** "i would
prefer not to go the prosthetic path it's too fragile and easy to game." The
prosthetic path (external probe-read + gate + veto scaffolding at inference)
is rejected as a program goal; the goal is NATIVE epistemic humility — a model
whose emitted behavior consults its own internal knowledge state. AH is the
gatekeeper experiment for the native path via the text channel:

- If uptake is gated by congruence with the model's own readout (H-resonance),
  a native hook exists in the strongest known channel, and Paper 5 pivots to
  amplifying it.
- If uptake is pure instruction compliance (H-compliance), the text channel is
  confirmed belief-blind even when belief and instruction conflict, and the
  native path requires engineered dependency at training time — probe-as-reward
  RL (backlog item 4) becomes the mainline candidate.

Either verdict moves the program; the failure mode this design eliminates is
the current unfalsifiable ambiguity.

## 2. Hypotheses and pre-stated prediction

Congruence is defined with respect to the model's READOUT (the frozen doubt
probe's label for the row), not gold: H-resonance is a claim about the policy
consulting the readout, and the readout is the validated proxy for the
internal state (§8 caveat 1 qualifies this).

- **H-compliance:** prime uptake is fully explained by prime direction
  (muzzle vs release; AG showed these are asymmetric) plus baseline distance
  from the refusal boundary (session-0035 pliability law). Congruence between
  prime content and the model's own readout contributes nothing.
- **H-resonance:** primes congruent with the model's own readout get
  systematically more uptake than incongruent primes, beyond what direction
  and boundary distance explain.

**Orchestrator prediction (pre-stated):** H-compliance (~75–80%). AG showed
the model obeys a gold-anti-aligned prime against its own demonstrable
knowledge while the doubt readout stays anti-semantic; the pliability law
absorbed the full hidden state into one boundary-distance scalar; the only
observed readout→behavior coupling (AC) was wired externally. Residual
uncertainty: release has never been tested on internally-certain rows.

**User prediction (recorded verbatim, 2026-07-03):** H-compliance, including
on the crisp stratum. "I think prompt is like a shotgun here and overrides
most other policies. So I think we're still decoupled from internals, if
there is something it would be too weak I think to do anything about beyond
like you say maybe coming back to training." Clarification of the earlier
"internally would make a difference" remark: it was representational, not
behavioral — "I would bet different kinds of question activate different
kinds of areas that if possible we should map out, but like DOUBT i don't
feel like they really bear on the ultimate behavior." (That mapping objective
is backlog row 22, not an AH gate.)

Both predictions land on H-compliance; a resonance result would surprise both
parties and carries full evidential weight either way. Dual independent
predictions (orchestrator + user, recorded before launch) are adopted as
standing practice for future amendments.

## 3. Design (v2 — redesigned after Stage-0; supersedes the v1 2×2)

### 3.0 Redesign note (what changed and why)

v1 crossed two DIVERGENT cells (probe ≠ gold in both directions) with
readout-aligned vs gold-aligned prime arms. Stage-0 (§4) showed the D-under
cell (probe-uncertain on verified-known) is unmineable: ~1 clean row per
1,000 candidates after behavioral verification and gold audit — the
pre-stated adequacy floor fired. v2 keeps the SAME hypotheses and the same
falsifier logic but identifies congruence differently: **hold prime direction
constant and vary the readout state within a gold class.** This needs no
D-under cell: the congruent-muzzle population requires only probe-uncertain
rows that ANSWER at baseline (no correctness verification — a muzzle flip is
measurable whether or not the answer was right). Nothing was signed before
the redesign; v1's identification, gates, and floors are superseded in full
by this section and §5.

### 3.1 The two contrasts

All rows come from the Stage-0 mined pool (5,000 items, §4), whose pre-gen
states are already extracted. Readout labels use the frozen AF-600 probes
(§4; consensus rule and margin locked at signing from the Stage-0 grid).
Baseline behavior (refused/answered) is adjudicated from the A0 arm of the
main run (AG census lineage); cells are therefore finalized post-A0 under
pre-stated definitions — the AG precedent.

**Release contrast** (direction held at RELEASE, gold class held at
UNANSWERABLE, baseline-refused rows only):

- *Congruent-release:* probe-certain, gold-unanswerable (the Stage-0 D-over
  yield). The certainty prime agrees with the readout.
- *Incongruent-release:* probe-uncertain, gold-unanswerable (concordant
  unknowns). The certainty prime contradicts the readout. AG measured this
  population's release at +7.9pt.

**Muzzle contrast** (direction held at MUZZLE, baseline-answered rows only):

- *Congruent-muzzle:* probe-uncertain, baseline-answered (either gold class;
  gold reported as a stratum). The doubt prime agrees with the readout.
- *Incongruent-muzzle:* probe-certain, gold-answerable, baseline-answered
  (concordant knowns). The doubt prime contradicts the readout. AG measured
  this population's muzzle at +34.0pt.

Within each contrast the prime is the SAME sentence for both cells, so AG's
direction asymmetry cannot masquerade as congruence; the only designed
difference between cells is the readout state.

### 3.2 Arms

Batch-1, greedy, byte-frozen AF harness (`amendment_af_generate.py` lineage:
sequential, max_new_tokens 96, enable_thinking False, prime + " " +
baseline_system). Three renderings per pooled row:

- **A0 — baseline:** no prime (also supplies the baseline-behavior census and
  the caution-axis boundary distance).
- **A-certain:** PRIME_HIGH verbatim (the AF certainty/release prime).
- **A-doubt:** PRIME_LOW verbatim (the AF doubt/muzzle prime).

Uptake is scored per contrast: release uptake = refused→answered under
A-certain on baseline-refused rows; muzzle uptake = answered→refused under
A-doubt on baseline-answered rows. Degeneracy and induced-confabulation
counts tracked (AG grading lineage).

### 3.3 Pool (locked from the redesign check, pending signing)

Readout rule: **consensus(L20/L24/L28) at margin band 0** everywhere — band
0.5z crushes the binding cell (18 rows), and the three-layer consensus
already supplies the noise robustness the margin band was for. No
cell-specific rule relaxation (relaxing only the scarce cell to L24-alone
would trade pre-registration cleanliness for n).

- **Matched core (v2.1, 1,512 rows)** = `expansion/pool_v21.jsonl` (supersedes
  the 648-row v2 proposal after the user-approved dataset expansion, §4.8):
  greedy 1:1 nearest-neighbor caliper match on caution distance (caliper
  0.25·SD = 3.10) over the 18,496-row union surface. Release contrast
  669+669 (3 D-over unmatched within caliper); muzzle contrast 87+87 (all
  available congruent-muzzle rows). Post-match positivity: overlap 0.985 /
  1.000, separability AUC 0.500 both contrasts — caution distance fully
  balanced, so the readout-state contrast is cleanly separated from
  boundary distance.
- **Crisp stratum (pre-registered secondary):** congruent-release rows
  flagged crisp = false_assumption (42) + counterfactual (34) + SelfAware
  (12) = 88, vs soft = ambiguous/controversial/unsolved/future (581). KUQ
  categories canonicalized across the two source files; raw strings carried
  per row as `category_raw`.
- **Positive-control stratum (150 rows):** concordant-known rows from the
  LOW-caution end (likely baseline-answered), for AH-G1, sampled across all
  four answerable sources (TriviaQA 39 / SelfAware 37 / KUQ 37 / PopQA 37) —
  the matched muzzle-incongruent cell sits at high caution by construction
  and is the wrong population for replicating AG's muzzle effect.

Renderings per row: A0 + the row's contrast-relevant prime only (release rows
get A-certain, muzzle and positive-control rows get A-doubt) = 1,662 × 2 =
3,324 generations, ~3.5–4 h on the 3090 at the frozen batch-1 harness.

### 3.4 Primary analysis

Per contrast, pooled logistic over eligible rows:

```
flip ~ baseline_boundary_distance_z + congruence
```

(direction is constant within contrast, so it drops out), plus the pooled
two-contrast model `flip ~ direction + distance_z + congruence` as the
headline single number. `baseline_boundary_distance_z` is the row's A0 signed
distance from the refused/answered boundary on the frozen L24 caution axis.
Bootstrap CIs over rows. Collinearity guard: the doubt readout and the
caution distance are correlated axes (MI: correlated but separable); the
Stage-0 redesign check quantifies the within-cell correlation and the
between-cell distance overlap BEFORE signing — if overlap is inadequate the
caliper-matched pool (§3.3) is the primary population and the covariate model
is secondary. Descriptives: per-cell uptake table, congruent-minus-incongruent
differential per contrast, congruence × contrast interaction.

## 4. Stage 0 — RESULT (run 2026-07-03; launch approved "proceed")

Runner: ah-stage0-runner; artifacts in canonical
`experiment/phase1/probe/analysis/ah_stage0/` (gitignored); code
`amendment_ah_stage0_*.py` on the branch.

1. **Candidate set:** 5,000 items (2,500 answerable / 2,500 unanswerable),
   AF-600 excluded, deduped: SelfAware 2,034 ans + 732 unans; KUQ 466 known
   (alias-gradeable) + 1,768 unknown.
2. **Frozen probes:** fit on the full AF-600 surface (honest for mined items,
   which are disjoint) at L20/L24/L28; OOF AUROCs 0.9916 / 0.9945 / 0.9940 —
   L24 reproduces AG exactly. Plus a 5-fold L24 ensemble.
3. **Extraction:** 5,000 pre-gen rows in 341 s. Batched extraction FAILED its
   20-row equivalence check (bf16 left-padding, max_abs_diff 4.0) and was
   rejected; the whole pass ran single-row, byte-comparable to the AF/AG
   surface.
4. **Yield grid** (D-over / D-under, pre-verification):
   L24-alone 465/156 (margin 0), 158/41 (0.5z), 47/4 (1z);
   consensus(L20/L24/L28) 253/75, 56/18, 16/2;
   ensemble-unanimity 243/94, 73/23, 23/3. Margin 2z wipes all cells.
5. **D-under verification and audit → floor STOP:** 156 loosest candidates →
   14 graded correct under forced-best-guess → orchestrator row audit cuts to
   ~5 genuinely clean rows (gold-label noise: context-stripped SelfAware
   items; junk aliases like "not"; grader false-positives — one refusal
   graded correct via an alias substring). True clean D-under rate ≈ 1/1,000.
   **The v1 adequacy floor (≥50/cell) fired for D-under; user adjudicated:
   redesign (§3.0).** Standing observation: the readout's natural errors are
   one-sided — it essentially never underestimates on items the model
   demonstrably knows (candidate Paper-5 note).
6. **D-over composition caveat:** D-over is KUQ-dominated (loosest: 438 KUQ
   vs 27 SelfAware; consensus@1z: 16/16 KUQ), and the KUQ rows are largely
   debatable/unsolved/future questions — "no consensus answer" rather than
   crisply unanswerable. Handled in §8 caveat 4.
7. **Redesign check — RESULT (2026-07-03, `redesign_check/`):** caution axis
   rebuilt to AG spec (CV AUROC 0.9374 and base SD 12.395 reproduce AG
   exactly), applied out-of-sample to all 5,000 mined states.
   - *Collinearity (doubt score vs caution distance):* overall −0.465
     Pearson, but nearly vanishes INSIDE the release-contrast cells
     (D-over −0.149 n.s.; concordant-unknown +0.042) and stays strong inside
     concordant-known (−0.501). The release contrast is the statistically
     clean side.
   - *Positivity:* release contrast good raw (overlap 0.752, AUC 0.457);
     muzzle contrast has a raw positivity problem (congruent cell sits ~10
     caution-units higher than concordant knowns; AUC 0.704) — fixed by
     caliper matching (post-match AUC 0.500 both contrasts) at the cost of
     pool size (648, muzzle-limited).
   - *Binding cell:* probe-uncertain & gold-answerable (congruent muzzle) =
     75 rows at consensus/band0 (18 at 0.5z) — caps the design.
   - *Expected attrition (pre-stated):* the congruent-muzzle cell's mean
     caution (+14.5, ≈+1.2z refusal-side) predicts most of its rows REFUSE at
     baseline, so its post-A0 eligible count will likely fall under the G0
     floor. The pre-stated fallback (muzzle contrast descriptive, verdict on
     the release contrast) is therefore the EXPECTED path, not an edge case —
     recorded before launch so it cannot read as post-hoc.

8. **Expansion pass — RESULT (2026-07-03, user approval "run it"; code
   `amendment_ah_stage0_expand_*.py`, artifacts `expansion/`):** +13,496 rows
   (3,496 remaining KUQ unknowns with categories carried; 6,000 TriviaQA +
   4,000 PopQA factoids); union surface 18,496. New D-over at consensus =
   419 (all KUQ; ambiguous 231, controversial 85, unsolved 49, counterfactual
   24, future 17, false-assumption 13). **Muzzle rescue failed informatively:
   12/10,000 fresh factoids read probe-uncertain at consensus** (all
   TriviaQA; PopQA 0) — replicating the one-sided-readout finding on clean
   out-of-source items: the readout almost never underestimates on
   demonstrably-answerable questions. Congruent-muzzle grows only 75→87;
   muzzle scarcity is a property of the readout, not the candidate pool.
   Release contrast grows 249→669 matched pairs with the crisp stratum at 88.
   Orchestrator verified pool composition against `pool_v21.jsonl` (1,662
   rows; cell counts exact).

## 5. Gates (v2 LOCKED values — effective at signing)

- **AH-G0 (feasibility, post-A0):** ≥40 eligible rows per cell (release cells
  need baseline-refused; muzzle cells baseline-answered). If ONLY
  congruent-muzzle fails (the EXPECTED path per §4.7), the muzzle contrast is
  reported descriptively and the verdict rests on the release contrast; if a
  release cell fails, STOP, no verdict.
- **AH-G1 (positive control):** on baseline-answered rows of the
  positive-control stratum (§3.3), A-doubt induces refusal ≥ +20pt vs A0
  (AG replication). Fail → instrument invalid, no reading on G2.
- **AH-G2 (congruence, primary — release contrast on the matched core):**
  congruent-minus-incongruent uptake differential ≥ +10pt with bootstrap 95%
  CI excluding 0, AND the congruence coefficient in
  `flip ~ distance_z + congruence` has 95% CI excluding 0. Both required.
  PASS → H-resonance. Matched pool is the primary population; the covariate
  model on all eligible rows is the pre-registered secondary.
- **Three-tier verdict (pre-stated to avoid mislabeling small effects):**
  (i) G2 PASS → H-RESONANCE. (ii) congruence CI excludes 0 but differential
  < +10pt → WEAK RESONANCE (ambiguous; does not close the native path, does
  not open it). (iii) congruence CI includes 0 → H-COMPLIANCE.
- **Falsifier (for H-resonance; the predicted outcome):** G1 passes, tier
  (iii) obtains → the text channel does not consult the model's own readout
  even when readout and instruction conflict. Native path via prompting is
  closed; probe-as-reward dependency engineering becomes the mainline.
- **Ambiguity guard:** if the muzzle contrast is measurable (its G0 passes)
  and its congruence effect is opposite-signed vs release → AMBIGUOUS, not a
  pass (pre-stated against post-hoc contrast-picking).

## 6. Instrumentation (§8-style, gate-free)

Primed pre-gen extraction passes (A-certain, A-doubt) on the pooled rows,
read on the frozen doubt and caution axes: does an incongruent prime move
either readout differently than a congruent one? AG found doubt anti-semantic
and caution carrying compliance on the concordant pool; this pool tests that
picture where instruction fights readout. Descriptive only.

## 7. Preconditions and approvals

1. v1 DRAFT merged — DONE (PRs #169, #170).
2. Stage-0 scout inventory — DONE (§1 correction, §4; scratch in canonical
   `analysis/ah_scout/`).
3. Stage-0 GPU mining pass — DONE 2026-07-03 (user approval "proceed"; §4).
4. Adequacy-floor STOP adjudicated by user → redesign — DONE ("redesign").
5. Redesign check appended — DONE (§4.7); rule/caliper/pool/gates locked
   (§3.3, §5).
6. User prediction recorded; user sign-off — DONE 2026-07-03 (§2; both
   predictions H-compliance; scoreboard entry in
   `docs/prediction-scoreboard.md`).
7. Dataset expansion (user: "run it") — DONE (§4.8); pool re-locked at v2.1
   (§3.3).
8. Main run (3,324 generations: 1,662 rows × 2 renderings, ~3.5–4 h on the
   3090): **separate explicit launch approval.** Signing ≠ launch.

## 8. Interpretive caveats (pre-stated)

1. **Readout vs state:** a probe label is a linear proxy. Where it diverges
   from gold, either the probe misreads a state that matches gold, or the
   state genuinely diverges. The consensus rule shifts mass toward the
   latter; residual proxy error biases a true resonance effect toward null,
   so an H-compliance verdict carries this qualification and an H-resonance
   PASS is conservative with respect to it.
2. **Confabulation induction:** A-certain on gold-unanswerable rows presses
   toward confabulation; induced-confabulation counts reported (AG-G2
   lineage).
3. **Population validity:** cells conditioned on readout errors and baseline
   behavior are unusual populations by construction; the claim is about the
   MECHANISM (does the policy consult the readout), for which these rows are
   exactly the informative ones.
4. **KUQ construct caveat:** most D-over rows are KUQ debatable/unsolved
   items, where "gold-unanswerable" means no consensus answer, not crisp
   factual unanswerability; a confident readout there is a construct mismatch
   as much as an error. Congruence is defined on the readout (§2), so the
   contrast remains valid, but the release-contrast verdict is reported with
   KUQ-vs-SelfAware stratification, and SelfAware-only numbers are given
   descriptively (n=27 loosest — under floor on its own).
5. **Doubt–caution collinearity:** the congruence variable (doubt readout)
   and the pliability covariate (caution distance) are correlated axes.
   Signing requires the Stage-0 redesign-check numbers (within-cell
   correlation, between-cell overlap); the caliper-matched pool is the
   primary defense, covariate adjustment the secondary.

## 9. Result

**VERDICT: AMBIGUOUS — INSTRUMENT-QUALIFIED NULL (mechanical §5 label:
`INSTRUMENT_INVALID (G1 fail)`). The pre-stated tier rule is applied as
written: G1 missed its floor, so the G2 reading is not gate-certified.
Reported alongside it, as exploratory evidence: the release congruence
differential is a precise zero, consistent with H-COMPLIANCE and
inconsistent with H-RESONANCE at any detectable magnitude.**

Run: 2026-07-03, 3,324 generations (A0 1,662 / A-certain 1,338 / A-doubt
324), frozen AF harness, byte-exact spec §3.2. One SIGABRT crash at
A-certain 256/1,338 (dmesg signal 6, NOT OOM; transient native abort in the
WSL bitsandbytes path); deterministic skip-resume added (commit c352463e),
config SHAs verified identical, A0 untouched. Degeneracy: 0 in all arms.
All gate numbers independently recomputed by the lead from raw rows +
pool_v21 before adjudication: exact reproduction.

### 9.1 Gates as locked

| Gate | Locked threshold | Result | Pass |
|---|---|---|---|
| G0 release (cong/incong) | ≥40 eligible/cell | 525 / 504 | PASS |
| G0 muzzle (cong/incong) | ≥40 eligible/cell | 14 / 14 | FAIL (pre-stated expected path §4.7 → verdict rests on release) |
| G0 positive control | ≥40 eligible | 147 | PASS |
| G1 positive control | induced refusal ≥ +20pt | **+15.65pt** (0.0% → 15.65%, 23/147) | **FAIL (−4.4pt)** |
| G2 release congruence | ≥ +10pt AND both CIs exclude 0 | **−0.21pt**, bootstrap CI [−4.45, +4.10], logistic coef −0.150 CI [−0.555, +0.250] | **FAIL (null)** |

Baseline census (A0): 1,178 refused / 484 answered / 0 ungradeable;
89/324 graded correct on answerable; 309 confab-on-unanswerable.

### 9.2 Adjudication

The goalposts do not move: G1's +20pt floor was locked at signing, it
missed, and the §5 rule voids gate certification of the G2 reading. The
result is therefore filed as AMBIGUOUS, not as a certified H-COMPLIANCE.

Two facts are recorded for interpretation, both visible only after the run:

1. **The G1 miss has an identifiable population cause (pre-registered, its
   consequence unnoticed at signing).** The positive-control stratum was
   drawn from the LOW-caution end of concordant-known rows (§3.3; mean
   caution_dist_z −1.31, min −2.07) — the rows most confidently answered
   and hence hardest to muzzle. AG's +34pt muzzle number, from which the
   +20pt floor was derived, was measured on an unfiltered known population.
   The floor was calibrated against an easier population than the control
   was drawn from. This is a design-calibration flaw in the control, not
   evidence the prime is inert: the same A-doubt prime still induced
   +15.65pt refusal on the most muzzle-resistant stratum available.
2. **The instrument was demonstrably live in the release direction — the
   direction that carries the verdict.** The A-certain prime flipped 14.5%
   of baseline-refused release rows to answering and induced +150
   confabulations on gold-unanswerables (309 → 459). A dead instrument
   cannot explain the G2 zero.

Given (2), the G2 result is informative even though not gate-certified: the
congruence differential is −0.21pt with a ±4.3pt CI — a *precise* zero, not
an underpowered smear. Primes aligned with the model's own readout received
exactly the uptake of primes opposed to it. The crisp stratum agrees
(−2.29pt, CI [−12.1, +8.0]). Both pre-registered predictions (§2, both
H-compliance) are consistent with this pattern, but per the pre-stated TIE
semantics (instrument voided at gates) the scoreboard scores **TIE** for
both parties — the gates, not the vibes, certify wins.

### 9.3 Instrumentation (§6, descriptive)

The primed pre-gen readout deltas replicate AG's belief-vs-policy picture
on the divergent pool: the certainty prime writes a large answer-direction
caution shift that is **unmodulated by the model's own readout state**
(release congruent −9.21 raw / z −0.74 vs incongruent −8.65 / z −0.70 —
near-identical), while doubt-axis deltas stay small (−0.25 vs +1.12).
Muzzle-direction doubt deltas differ by congruence (+5.40 vs +2.62,
consistent with congruent rows already sitting at the prime-aligned end);
positive-control deltas ≈ 0 (+0.27 doubt, +0.05z caution) — notable in
itself: the prime induced +15.65pt refusal on this stratum with almost no
movement on either readable axis.

### 9.4 Consequences and follow-ups

- **No claim is promoted.** H-compliance remains the working hypothesis
  (AG certified + this exploratory zero), not a certified AH result.
- **G1 recalibration cell (proposed, cheap):** re-run the positive control
  on a caution-REPRESENTATIVE stratum of concordant-known rows (~150 rows,
  ~300 gens, ~10 min GPU), pre-registering that a pass certifies the
  already-collected G2 reading (G2 rows untouched by the control). If it
  passes, the verdict upgrades to H-COMPLIANCE by the original three-tier
  rule; if it fails, the prime's muzzle authority on confident rows is
  itself the finding. Requires user sign-off as an AH addendum.
- **Probe-as-reward proceeds** as the native-path mainline (design
  diagnostics + mining already complete; see `par_design/REPORT.md`).
- Data exhaust: the 3,324-generation surface + instrumentation extractions
  join the AH release package (backlog row 23).

## 10. Addendum A1 — G1 recalibration cell (pre-registered)

**Status: SIGNED 2026-07-03 (user approval: "Do the addendum"); launched on
signing.** Branch `amendment-ah-g1-recalibration`. Both predictions recorded
in frontmatter (`addendum_a1`) BEFORE launch: orchestrator PASS ~80%, user
PASS. Convergent again.

### 10.1 Design (locked)

Re-run ONLY the AH positive control on a caution-REPRESENTATIVE stratum of
concordant-known rows, fixing the §9.2(1) population-calibration flaw. The
G2 cells are untouched — no divergent row is regenerated, no scoring rule
changes.

- **Stratum (150 rows):** concordant-known rows (consensus L20/L24/L28
  probe-confident, gold-answerable — the §3.3 readout rule verbatim) sampled
  quantile-stratified on `caution_dist_z` — 30 rows per quintile of the
  concordant-known population's caution distribution — balanced across the
  four answerable sources (TriviaQA/SelfAware/KUQ/PopQA) as available within
  each quintile, seed 0, EXCLUDING the 150 original positive-control rows.
  This reproduces the population AG's +34pt (the floor's calibration) was
  measured on: unfiltered by caution.
- **Arms:** A0 + A-doubt per row (PRIME_LOW verbatim), byte-frozen AF
  harness, batch-1 greedy — identical to §3.2. ~300 generations, ~10 min.
- **Eligibility:** baseline-answered at A0 (as in the main run). Sanity
  floor: ≥40 eligible rows (G0 rule).

### 10.2 Gate and certification semantics (locked)

- **A1-G1:** induced refusal (A0-answered → A-doubt-refused) ≥ **+20pt**
  among eligible rows — the original G1 floor, unchanged.
- **PASS ⇒** the instrument is certified on a fair population; the original
  three-tier §5 rule applies to the ALREADY-COLLECTED G2 reading (a precise
  null with a live release-direction instrument) ⇒ **verdict upgrades to
  H-COMPLIANCE**; the scoreboard row upgrades TIE/TIE → WIN/WIN.
- **FAIL (< +20pt) ⇒** verdict stays AMBIGUOUS permanently (no second
  recalibration); the finding is then that the doubt prime's muzzle
  authority on this pool is genuinely weaker than AG's TriviaQA-era
  calibration — recorded as a descriptive result, no goalpost moved.
- Secondary descriptive (non-gating): induced refusal per caution quintile,
  to show the §9.2(1) gradient directly.

### 10.3 Result — A1-G1 PASS; verdict upgraded to H-COMPLIANCE

Run 2026-07-03, 300 generations (150 A0 + 150 A-doubt), frozen AF harness,
degeneracy 0, GPU ~10 min. Stratum delivered exactly per §10.1: 30 rows per
quintile, sources TriviaQA 40 / SelfAware 40 / KUQ 35 / PopQA 35, seed 0,
original 150 excluded; selected mean caution_z +0.467 vs the original
stratum's −1.31. Gate numbers independently recomputed by the lead from raw
rows (`amendment_ah_addendum_a1_result.json`).

| Gate | Locked threshold | Result | Pass |
|---|---|---|---|
| A1-G0 eligibility | ≥40 eligible | 51 (99/150 baseline-refused) | PASS |
| A1-G1 induced refusal | ≥ +20pt | **+50.98pt** (26/51) | **PASS (+31.0pt margin)** |

Per-quintile induced refusal (descriptive): Q1 37.0pt (10/27), Q2 53.3pt
(8/15), Q3 85.7pt (6/7), Q4 100pt (2/2), Q5 no eligible rows (all
baseline-refused). The gradient is monotone in caution distance — muzzle
uptake rises with baseline proximity to the refusal boundary — directly
confirming the §9.2(1) diagnosis: the original control stratum (mean z
−1.31, below Q1's range) was drawn from the most muzzle-resistant rows
available, and the +15.65pt miss was a population-calibration artifact, not
a weak prime.

**Certification (per locked §10.2):** the instrument is certified on a fair
population; the §5 three-tier rule applied to the already-collected G2
reading (precise null, live instrument in both directions) yields
**H-COMPLIANCE**: prime uptake does not consult the model's own readout —
compliance is instruction-following plus boundary distance, replicating and
extending AG's belief-vs-policy dissociation onto the divergent pool.
Scoreboard: both parties predicted PASS (frontmatter `addendum_a1`) and both
predicted H-compliance at the original signing → the AH row upgrades
TIE/TIE → **WIN/WIN**, and Addendum A1 scores as its own WIN/WIN row
(tally: user 3 – orchestrator 2 – ties 0).
