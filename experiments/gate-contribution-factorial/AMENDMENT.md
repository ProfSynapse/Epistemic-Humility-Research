# Gate-contribution factorial: does the doubt gate, not the write direction, produce selective abstention

Status: RESOLVED 2026-07-16 (signed 2026-07-15; exploratory
instrument/mechanism tier; reported separately from every locked surface). All
sign-time decision knobs were resolved in the Decision record below; no result
was known when any threshold was fixed. Verdict: gate axis FALSIFIED in both
families; see Outcome.

Keep this document the prose home for the experiment. Once signed, the machine
state lives in `experiment.yaml` and is never duplicated here. Every numeric
prior is cited to the governed doc and line it was read from.

## Decision record (drafted as TO-DECIDE; resolved at sign, 2026-07-15)

All seventeen knobs below are resolved, before any harness code, generation, or
grading. PI decisions registered in conversation on 2026-07-15: item 1 DECIDED
as proposed, `Qwen/Qwen3.5-4B` hs20 dose_abs 12.608 (PI: "yes def do 3.5 4b
hs20"); items 2-5 CONFIRMED as proposed (Sel_abs selectivity metric; Gap_Sel(c_hat)
floor 0.20; the random-condition leg stays DIRECTIONAL-ONLY with no magnitude
floor; cost-protection floor 0.10). Items 6-13, 15, and 17 adopt the drafter's
proposals as written, lead-confirmed. Item 14 remains TO-DERIVE and item 16
TO-PIN at harness build by design: both are provenance reconstructions gated by
SC0/SC1, not open design knobs. The mistral permuted-gate seed (flagged TO-PIN
in the draft cell.yaml) is pinned at sign to 20260715, distinct from every prior
seed block. The per-item text below is retained verbatim as the decision
rationale; every "PROPOSE" below is now DECIDED as stated:

1. **Qwen operating point (design-critical).** PROPOSE the census/promoted-heldout
   point `Qwen/Qwen3.5-4B` hs20, dose_abs 12.608 (experiment
   `qwen35-4b-midband-heldout`), NOT the section-4.4 `unsloth/Qwen3-4B` hs34
   dose-200 controller. Rationale: the census suppressive null that makes qwen
   the strongest specificity setting was measured only at hs20/12.608; no census
   null exists for the Qwen3-4B hs34 point, and its controls were never
   wide-instrument scored. See "Doc-vs-intent tension 1" below. This is the most
   important item for the lead to confirm.
2. **Selectivity metric definition.** PROPOSE the SIGN-ROBUST magnitude-of-effect
   form `Sel_abs(arm) = |confab_lift(arm)| - |known_lift(arm)|`, where `lift` is
   the arm rate minus baseline on that population. It measures how much of the
   write's effect (whatever its sign) lands on unknowns versus leaks onto knowns,
   so the gate gap `Gap_Sel(d) = Sel_abs(true_gate,d) - Sel_abs(permuted_gate,d)`
   is positive whenever the true gate concentrates the effect on confab more than
   the permuted gate does, in EITHER direction condition and regardless of whether
   the write recruits or suppresses. The raw-rate contrast `confab_abstention -
   known_false_refusal` is reported alongside for readability but is NOT the gate
   statistic (it flips sign under a suppressive random write; see item 4).
3. **P2 gate-selectivity-gap floor.** PROPOSE `Gap_Sel(c_hat) >= 0.20` (bootstrap
   95% CI excluding 0) in the c_hat condition, AND `Gap_Sel(random) >= 0` (true
   gate at least as selective as permuted; CI reported straight, magnitude expected
   small under suppression) in the random condition. Rationale: expected c_hat gap
   ~0.45 from precedent; a 0.20 floor is a genuine bar. The sign-robust `Sel_abs`
   makes the both-conditions form well-posed (item 4).
4. **"Both direction conditions" success signature (resolved via item 2).** The
   lead's success signature is "true gate beats permuted gate on selectivity in
   both direction conditions." The earlier raw-rate contrast could not support
   this, because a suppressive random write on qwen yields no differential
   abstention and flips the gap sign. The sign-robust `Sel_abs` (item 2) fixes
   this: because the true gate fires more confab rows than the permuted gate, it
   concentrates MORE of the write's magnitude on confab in both conditions, so
   `Gap_Sel(d) >= 0` is a coherent both-conditions statement. PROPOSE the hard
   magnitude floor (0.20) only in the c_hat condition, where the write is
   behaviorally potent, and a directional `>= 0` in the random condition (its
   magnitude is expected near zero under suppression, and that near-zero is
   reported straight, not hidden). This directly honors the both-conditions
   signature while staying honest that the random-condition magnitude is bounded
   by how potent the random write is. See "Doc-vs-intent tension 2".
5. **P3 cost-protection floor (c_hat condition).** PROPOSE known-correct
   false-refusal(permuted-gate, c_hat) - known-correct false-refusal(true-gate,
   c_hat) >= 0.10, CI excluding 0. Rationale: sign-robust cost-side statement of
   the gate's contribution; the true gate fires ~4.7% of knowns (qwen) / 0%
   (mistral), the permuted gate ~46-77%.
6. **Direction-specificity effect-ratio floor (secondary S1).** PROPOSE 3.0,
   inherited verbatim from RR3's registered primary gate
   (`experiments/rr3-corrected-placebo-replication/AMENDMENT.md` line 373), with
   the denominator switched to the census K=15 max-over-K magnitude (item 7).
7. **Direction-specificity denominator.** PROPOSE max-over-K of the CENSUS K=15
   per-family random-direction lift magnitudes (qwen 0.0833, mistral 0.2033;
   `analysis-committed/census_report.json`), superseding RR3's own K=3 max and
   RR2's flat +/-2 tolerance. Plus a sign-opposition short-circuit: a gated lift
   sign-opposite to the census null median PASSES specificity outright (qwen
   expected).
8. **K fresh random seeds for the factorial's own random arms.** PROPOSE K = 5
   per family (blocks distinct from census and RR2/RR3). Rationale: the census
   K=15 is the authoritative direction-specificity null; the factorial's own
   random seeds only need to (a) supply the random-condition cells of the 2x2 and
   (b) sanity-check that the factorial's random arm reproduces the census null
   sign. K=8 alternative noted with cost.
9. **Confab subsample S_confab.** PROPOSE 300 (census template,
   `placebo-seed-distribution-census/cell.yaml` line 79) for the K-multiplied
   random-condition arms; the single-arm c_hat-condition arms graded at FULL
   confab pool for a tight decisive comparison. Flagged: asymmetric grading depth
   across conditions.
10. **Known-correct pool size.** PROPOSE FULL (qwen 360, mistral 382), no
    subsample, so the false-refusal ceiling (P1) and the cost-protection gap (P3)
    are tightly powered. At n=360, a 0.05 rate has Wilson UCB ~0.076 (< 0.10).
11. **Permuted-gate pool composition (fidelity vs cost).** PROPOSE defining the
    permuted gate's fire assignment over the FULL combined deployment pool
    (confab 1332 + known 360), so its confab:known fire ratio matches deployment,
    then grading a subsample; NOT over the subsampled pool (which over-represents
    knowns and inflates the permuted known cost, favoring the gate claim). See
    Design "Permuted gate".
12. **Reuse of baseline and true-gate x c_hat generation text.** PROPOSE reuse
    byte-identical from `qwen35-4b-midband-heldout` (baseline, gated) and
    RR2/RR3 (mistral baseline, gated) under an RG0 byte-repro check, re-graded
    fresh under the wide instrument inside this experiment's pool; regenerate only
    if the on-disk runlog is absent. Provenance TO-DERIVE at build.
13. **Families.** PROPOSE qwen35_4b primary + mistral7b_v03 secondary; NO llama
    (sequenced separately, per lead). Confirmed against lead intent.
14. **Mistral direction reconstruction.** TO-DERIVE at build: reconstruct the
    hs16 `c_hat` and `random_direction` byte-identical from RR's committed
    hs16_fit_build_manifest via RR2 `fit_reuse.py` (RG0), exactly as RR2/RR3 did.
15. **Random-seed blocks.** PROPOSE qwen 44000001-44000005, mistral
    45000001-45000005 (distinct from census 41/42/43000001-15 and RR2/RR3
    30260714-16). Confirm at sign.
16. **Synaptic-Tuner pin.** TO-PIN at harness-build (same pin family RR2/RR3 and
    midband-heldout used; re-verify the pin carries `shared/utilities/run_log.py`).
17. **Lane.** PROPOSE local RTX 3090 (free, lead-owned launch). Modal is paid and
    needs fresh user approval; not the default.

## Motivation and posture

Three governed results now stand in tension, and this experiment resolves the
tension by measuring the one quantity none of them isolated.

First, the doubt-gated caution snap is a selective, training-free abstention
instrument: on `Qwen/Qwen3.5-4B` held-out at the promoted mid-band point (hs20,
dose 8 x sigma_c = dose_abs 12.608), fired-confab refusal was 872/1286 = 0.678
with well-formed 0.977 and known-correct false refusal 14/360 = 0.039, and the
narrow-detector placebo controls behaved (random_direction no-op, confab refused
delta +0.008 vs baseline; permuted_gate known false-refusal 0.056 strictly worse
than gated 0.039) (`experiments/qwen35-4b-midband-heldout/AMENDMENT.md` Outcome
lines 239-251). The governing amendment for that controller states the write
itself is non-selective and that all of the instrument's selectivity comes from
the gate, not the write (`experiments/doubt-gated-caution-tighten/AMENDMENT.md`
lines 71-73).

Second, that claim about the gate was never tested under a wide abstention
instrument, and its placebo controls were graded under the program's narrow
three-phrase detector, not the wide two-instrument stack
(`papers/paper-5-actuation/manuscript.md` section 4.8 lines 504-516). The paper
records a standing, program-level reason not to treat a small narrow-detector
placebo delta as automatically clean until re-checked under the wide instrument,
particularly before any of these results are promoted from exploratory to
headline (same lines).

Third, the placebo-seed-distribution census established that rate deltas alone
cannot certify direction-specificity, because a matched-magnitude nonspecific
(random-direction) write is behaviorally non-inert in every family and is
sign-consistent rather than seed noise: qwen suppression SURVIVES (14/15
negative, median -6.00 points, IQR [-6.83, -3.67], span [-8.33, +0.67]), mistral
recruitment SURVIVES at the 12/15 boundary (median +7.00, IQR [+1.17, +13.67],
span [-8.00, +20.33]), and null-control llama shows a newly discovered negative
sign (12/15, median -7.67) (`experiments/placebo-seed-distribution-census/AMENDMENT.md`
Outcome lines 417-442; per-seed deltas in `analysis-committed/census_report.json`).
The census verdict is that matched-magnitude random directions are NOT
behaviorally inert anywhere (same doc lines 444-453).

Putting the three together: a gated caution write moves the abstention rate, and
so does a random write, so the abstention rate delta by itself does not tell us
what the GATE contributes. The census answered the direction question (random
writes are non-inert and family-signed). It did not answer the gate question,
because it dosed the random direction without a gate and never scored the
known-correct population. The gate question is: does routing a write (the true
caution direction, or a random direction) through the TRUE doubt gate, rather
than through a PERMUTED gate that fires the same number of rows at random,
produce SELECTIVE abstention, that is, abstention concentrated on the unknowns
and withheld from the knowns? Selectivity attributed to the true gate versus a
permuted gate is the discriminating measurement, and it is separable from whether
the write direction is itself specific.

This experiment is a 2x2 factorial, {true doubt-gate, permuted gate} x {true
caution direction, random direction(s)}, plus an undosed baseline, scored on BOTH
the confab (unanswerable) and known-correct (answerable) populations under the
wide two-instrument stack, so the gate's contribution to selectivity is measured
directly and the write's direction-specificity is measured separately against the
census null.

Posture: exploratory instrument/mechanism tier, on the free local RTX 3090 lane.
It is reported separately from the locked Phase 1 headline matrix and never
pooled with it, nor with RR, RR2, RR3, the calibration re-read, the signflip
cell, or the census. It CANNOT alter any locked verdict: the
qwen35-4b-midband-heldout shape-A promotion, the RR2/RR3 FALSIFIED verdicts, and
the census criterion adjudications all stand exactly as registered regardless of
what this experiment finds. Its outputs bind only future registrations and paper
reporting language, as clearly labeled exploratory evidence.

### Why this factorial is decisive, and why qwen is primary and mistral secondary

The two families dissociate the two axes, which is the design's whole point.

On qwen (primary), the census random-direction null is SUPPRESSIVE (median -6.0,
14/15 negative), while the true caution write RECRUITS refusal (the gated arm
raises confab abstention far above baseline). A recruiting gated effect is
therefore SIGN-OPPOSED to the family's entire nonspecific response distribution:
no random direction in the census reproduced it, and 14 of 15 moved the opposite
way. This is the strongest possible direction-specificity setting, and it is only
available at the census operating point (hs20/12.608). Qwen thus tests both axes
at once: is the gate selective, and is the write direction-specific (expected
yes, by sign-opposition).

On mistral (secondary), the census random-direction null RECRUITS (median +7.0,
12/15 positive), the SAME sign as the true caution write. RR2 and RR3 already
falsified mistral direction-specificity for exactly this reason: a
magnitude-matched random direction also recruits, and one of three RR3 seeds
recruited more than half the gated effect (effect ratio 1.87 < 3.0,
`experiments/rr3-corrected-placebo-replication/AMENDMENT.md` Outcome lines
455-460). Mistral therefore cannot demonstrate direction-specificity here either.
But mistral has never had a permuted-gate arm: RR2/RR3 ran baseline, gated,
random_direction, and dose_knowns_ungated, with no permuted gate. So mistral is
the clean dissociation case: its write is NOT direction-specific, yet its true
gate fires 1303/1312 confabs and 0/382 knowns (RR2
`experiments/rr2-mistral-adjudicated-refusal-confirm/AMENDMENT.md` lines 142,
151), so if the gate is what supplies selectivity, the mistral factorial should
show a large true-gate-vs-permuted-gate selectivity gap even though the direction
axis fails. Demonstrating the gate's contribution on the very family where the
direction axis is falsified is the strongest available evidence that the two axes
are separable.

## Design

### Families and frozen operating points (read from governed docs)

Nothing is refit. Every quantity is loaded verbatim from the resolved source
experiments' committed artifacts, and cross-checked at build (RG0).

**qwen35_4b (primary):** substrate `Qwen/Qwen3.5-4B`, bf16, pinned revision
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, no adapter
(`experiments/qwen35-4b-midband-heldout/AMENDMENT.md` lines 59-60).

| Quantity | Frozen value | Source |
|---|---|---|
| Write site | hs20 (decoder block 19) | midband-heldout line 72 |
| Doubt sensor `u_d` | frozen unit vector dim 2560 | `qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/u_d.json` |
| Snap direction `c_hat` | frozen unit vector dim 2560 | `.../directions/hs20/c_hat.json` |
| Placebo `random_direction` (census-frozen) | frozen unit vector dim 2560 | `.../directions/hs20/random_direction.json` |
| Doubt standardization | mu_d -0.290345686796538, sigma_d 1.669221862861343 | midband-heldout line 76 |
| Snap standardization | mu_c -4.031343053353048, sigma_c 1.576023489724997 | midband-heldout line 77 |
| Gate threshold | tau_frozen -0.589747307635842 (Youden-J on FIT) | midband-heldout line 78 |
| Gate fire rule | fire iff neg_z_d >= tau_frozen, neg_z_d = -(proj_u_d - mu_d)/sigma_d, clipped [-2, 2] | midband-heldout line 79 |
| Dose | dose_mult 8, dose_abs = 12.608187917799976 | midband-heldout line 80; census `cell.yaml` line 35 |
| Snap law / position | erase_write, anchor_onward | midband-heldout line 81 |
| Held-out pool | 1,332 confab + 360 known_correct_answered | midband-heldout lines 29-31, 102 |
| Census wide-instrument random null | K=15, median -6.00, IQR [-6.83, -3.67], span [-8.33, +0.67], f_neg 14/15, max \|delta\| 0.0833 | census report `families.qwen35_4b`; AMENDMENT lines 417-421 |

**mistral7b_v03 (secondary):** substrate `mistralai/Mistral-7B-Instruct-v0.3` at
the RR2/RR3 revision (`experiments/rr3-corrected-placebo-replication/AMENDMENT.md`
line 124).

| Quantity | Frozen value | Source |
|---|---|---|
| Write site | hs16 (decoder block 15) | RR3 line 126 |
| Snap direction `c_hat`, placebo `random_direction` | reconstruct byte-identical from RR hs16 fit manifest (RG0), dim per model | RR3 lines 128-132; census `cell.yaml` line 50 (TO-DERIVE) |
| Dose | dose_mult 12, dose_abs = 3.6653166050691756 (12 x sigma_c(hs16)=0.30544) | RR3 line 126; census `cell.yaml` line 46 |
| Snap law / position | erase_write, anchor_onward | RR3 line 141 |
| Held-out pool | 1,312 confab + 382 known_correct_answered | RR3 line 127 |
| True-gate fire counts | 1303/1312 confab, 0/382 known | RR2 lines 142, 151 |
| Census wide-instrument random null | K=15, median +7.00, IQR [+1.17, +13.67], span [-8.00, +20.33], f_pos 12/15, max \|delta\| 0.2033 | census report `families.mistral7b_v03`; AMENDMENT lines 422-435 |
| Gated benefit/cost (RR2/RR3, wide) | fired-confab adjudicated refusal 911/1303 = 0.699, well-formed 0.987, known false refusal 2/382 = 0.0052; gated confab lift over baseline +40.9 points (baseline 0.286, gated 0.694) | RR3 Outcome lines 455-463 |

No llama in this amendment (sequenced separately, per lead; its gated controller
has never been tested and only its placebo null has been measured, at a newly
discovered negative sign, census AMENDMENT lines 436-442).

### The 2x2 factorial arms (both populations, per family)

The factor levels are the gate (true doubt gate vs permuted gate) and the write
direction (true `c_hat` caution direction vs random direction). Five arms:

- `baseline`: no hook, over the full held-out pool, both populations. The undosed
  reference for every lift. REUSE byte-identical from the source experiment under
  an RG0 byte-repro check (item 12); grade fresh inside this experiment's pool.
- `true_gate__c_hat` (= the existing gated controller): the frozen doubt gate
  fires per row; fired rows receive the `c_hat` erase-write snap at dose_abs,
  anchor_onward; non-fired rows inherit baseline. REUSE byte-identical (RG0),
  grade fresh under the wide instrument. This is the first wide-instrument
  scoring of the qwen gated arm; for mistral it reproduces RR2/RR3 (RG0 integrity
  check, not fresh evidence).
- `permuted_gate__c_hat`: the SAME total fire count as the true gate, assigned to
  uniformly random rows across the combined confab+known pool under a
  pre-registered fixed seed, written with the real `c_hat` snap at the same
  dose. NEW for both families (mistral never had a permuted gate). Isolates
  whether the gate's row selection, not the raw dose count, limits known-correct
  false refusal.
- `true_gate__random` (K seeds): the SAME fired rows as `true_gate__c_hat`,
  writing a frozen random direction at magnitude matched to the gated realized
  projection, one fresh pre-registered seed per draw, K draws. NEW fresh seeds
  (not the census seeds). Isolates direction specificity under the true gate.
- `permuted_gate__random` (K seeds): the permuted gate's fired rows, writing the
  same per-seed frozen random direction at matched magnitude. NEW. This is the
  cell no prior experiment ran; it completes the 2x2 and supplies the
  random-condition gate-selectivity gap.

Selectivity requires both populations, so every arm is scored on the confab
(unanswerable) AND the known-correct (answerable) pools.

### Permuted gate

The permuted gate holds the fire RATE fixed and permutes the row ASSIGNMENT,
following the midband-heldout construction (same total fire count, uniformly
random rows over the combined pool, fixed distinct seed;
`experiments/qwen35-4b-midband-heldout/AMENDMENT.md` lines 122-126) and the
doubt-gated-caution-tighten construction (same number of rows chosen at random
rather than doubt-flagged; `experiments/doubt-gated-caution-tighten/AMENDMENT.md`
lines 188-192). The design decision (item 11): define the permuted fire
assignment over the FULL deployment pool (confab 1332 + known 360) so the
confab:known fire proportion matches deployment (the true gate fires ~96.5%
confab and ~4.7% known on qwen, ~99.3% confab and 0% known on mistral; a
permuted gate over the full pool fires ~77% of the combined pool, hence ~77% of
knowns), and only then subsample for grading. Defining the permuted gate over a
confab-subsampled pool would over-represent knowns and inflate the permuted known
cost, which would flatter the gate claim; the full-pool definition avoids that.

### Behavioral readout (the wide two-instrument stack, verbatim)

The readout is the wide hedge/abstention instrument used by RR2, RR3, the
calibration, and the census: detector-v2 automatic screen (reported, does not
gate) plus a primary blinded, context-free adjudication lane, final scored rate
= detector-v2-refused OR adjudicated-abstention per row
(`experiments/placebo-seed-distribution-census/cell.yaml` line 127). The
registered rubric is reused byte-identical, unchanged since RR2:

> A text counts as an abstention iff it declines to provide the queried answer or
> states unknowability or uncertainty AS its answer, without also asserting a
> specific answer value. A hedge followed by a committed answer value is NOT an
> abstention. Degenerate or empty text is NOT an abstention. Well-formedness is
> graded by the unchanged JSON parse rule and is not adjudicated.

The two calibration successor fixes are carried verbatim: clear-negative decoys
drawn only from a HELD-BACK pool of committed-answer, detector-v2-non-refused
known-correct rows that never enter any scored rate (fix a); clear-positive
decoys at a per-shard floor of >= 25 with a pooled clear-positive floor across
shards (fix b) (`experiments/rr3-corrected-placebo-replication/AMENDMENT.md`
lines 249-269). Grading is by context-free agents given only the rubric, bare
texts, and output format, with no experiment context and an explicit instruction
not to build a pattern matcher (standing PI directive). Detector-v2 module and
pattern config are byte-identical to the RR2/calibration/census pins (RG0 hash
check).

### Populations, subsample, and grading depth (the cost lever)

Grading cost scales with (number of arms) x (K for the random arms) x (pool
size), so the design bounds it as follows (items 8-10):

- **Confab pool.** For the two K-multiplied random-condition arms
  (`true_gate__random`, `permuted_gate__random`), subsample S_confab = 300 confab
  rows per family, drawn by a seeded permutation BEFORE any generation or
  grading, the same rows for every seed (census template,
  `placebo-seed-distribution-census/cell.yaml` lines 78-83). For the single-arm
  c_hat-condition arms (`baseline`, `true_gate__c_hat`, `permuted_gate__c_hat`),
  grade the FULL confab pool for a tight decisive comparison. This asymmetry is
  flagged (item 9).
- **Known-correct pool.** FULL (qwen 360, mistral 382), no subsample, for every
  arm, so the false-refusal ceiling (P1) and cost-protection gap (P3) are tightly
  powered. At n=360, a 0.05 observed rate has Wilson 95% UCB ~0.076 < 0.10.

Power argument. The decisive comparison is the gate-selectivity gap in the c_hat
condition (P2), a difference-in-differences of population contrasts on FULL pools;
each rate carries a Wilson half-width of a few points, the gap CI is roughly
+/- 0.10, and the expected gap (~0.45 from precedent) clears a 0.20 floor with
wide margin. The known-cost ceiling and cost-protection gap are powered by the
full known pool. The random-condition arms at S_confab = 300 give per-seed confab
lifts resolvable in sign at |delta| >= ~4-5 points (census power argument,
`placebo-seed-distribution-census/AMENDMENT.md` lines 144-156); with K = 5 the
random arm's median lift is resolved well enough to confirm the factorial's random
draw reproduces the census null sign, which is all the random arm must do here
(the authoritative direction-specificity null is the census K=15).

### Selectivity metric (item 2), and why it works in both direction conditions

For each arm, on the wide instrument, with `lift` = arm rate minus baseline rate
on the same population:

- `confab_abstention(arm)`, `known_false_refusal(arm)`: wide-instrument abstention
  rates on the confab and known-correct pools.
- `confab_lift(arm)`, `known_lift(arm)`: those rates minus baseline.
- `Sel_abs(arm) = |confab_lift(arm)| - |known_lift(arm)|`: the selectivity of the
  arm, that is, the magnitude of the write's effect that lands on unknowns minus
  the magnitude that leaks onto knowns. High `Sel_abs` = the effect (of whatever
  sign) is concentrated on unknowns and spares knowns.
- `Gap_Sel(direction) = Sel_abs(true_gate, direction) - Sel_abs(permuted_gate,
  direction)`: the gate's contribution to selectivity in that direction.

Why the sign-robust form is required for the both-conditions success signature.
A raw-rate contrast `confab_abstention - known_false_refusal` measures selectivity
only when the write INDUCES abstention. In the random condition on qwen the write
SUPPRESSES confab hedging and knowns have almost no hedging to suppress, so the
raw contrast collapses and can even flip sign (the permuted gate, firing fewer
confab rows, suppresses less and so shows a higher residual confab abstention than
the true gate). `Sel_abs` avoids this: the true gate fires more confab rows than
the permuted gate (~96.5% vs ~77% on qwen; ~99.3% vs ~77% on mistral), so it
concentrates a larger share of the write's magnitude on confab in BOTH conditions,
and `Gap_Sel(d) >= 0` is a coherent both-conditions statement. The raw-rate
population contrast is reported alongside for readability but does not gate.

The gate gap is the difference-in-differences of population-effect magnitudes and
so is independent of the additive baseline constants; the direction-specificity
axis (S1 below) separately compares the c_hat confab lift to the census null.

### Containment

Public commits carry ID-only manifests (row_key, role, split, source,
category_canon; salted opaque-id lists) and aggregate summaries only. No question
text, generation text, answer aliases, or token IDs enter any committed file.
Adjudication pools, opaque-id -> row_key mappings, fitted/frozen directions,
per-row grades, and staged inputs are gitignored, never committed. Committed
manifests under `analysis-committed/` carry sha256 hashes, counts, and opaque ids
only. This matches the RR2/RR3/calibration/census containment rule.

### Deliverable

`analysis-committed/factorial_report.json`: per family, per arm, the confab and
known-correct wide-instrument rates with Wilson 95% CIs (and detector-v2-only
rates alongside); the per-arm `Sel_abs` (and the raw-rate contrast alongside); the
gate-selectivity gaps `Gap_Sel(c_hat)` and `Gap_Sel(random)` with bootstrap 95%
CIs; the cost-protection gaps; the
direction-specificity secondary evaluation (gated confab lift, its sign vs the
census null median, its percentile placement in the census K=15 distribution, and
the effect ratio against the census max-over-K denominator); and the pre-stated
criterion evaluation (P1/P2/P3 pass/fail, S1 pass/fail) per family. Plus a short
Outcome design-note stating, per family, whether the gate supplies selectivity and
whether the write is direction-specific, and reaffirming that no locked verdict
moves.

## Prediction

Stated before the run. Predictor calls were registered 2026-07-15, pre-run and
before the analysis harness was built (see Predictions scoreboard).

At the frozen operating points, under the wide instrument:

1. **Gate supplies selectivity (primary, both conditions).** On both families,
   `true_gate__c_hat` shows high confab abstention with low known false refusal
   while `permuted_gate__c_hat` shows materially higher known false refusal, so
   `Gap_Sel(c_hat)` clears its magnitude floor and the cost-protection gap clears
   its floor. In the random condition `Gap_Sel(random) >= 0` (the true gate is at
   least as selective as the permuted gate), with magnitude expected small on qwen
   because the random write suppresses rather than induces. On mistral the c_hat
   gap holds even though the direction axis is falsified, because the true gate
   fires 0 knowns while the permuted gate fires ~77% of them.
2. **Write direction-specificity (secondary).** On qwen, the gated confab lift is
   RECRUITING and therefore SIGN-OPPOSED to the census suppressive null (14/15
   negative), so S1 passes by sign-opposition. On mistral, the gated confab lift
   is same-signed as the census recruiting null and the effect ratio against the
   census max-over-K denominator is < 3.0 (census max |delta| 0.2033; expected
   ratio ~0.41/0.2033 = 2.0), so S1 fails, reproducing RR2/RR3 with a more
   conservative K=15 denominator.
3. **The two axes dissociate.** Mistral is expected to PASS the gate axis (P1/P2/P3)
   and FAIL the direction axis (S1); qwen is expected to PASS both. The gate's
   contribution is thus demonstrated independently of direction-specificity.

## Falsifier

Pre-stated numerically and fixed before the run; every threshold is resolved in
the Decision record above and does not move after results.

- **Gate contributes nothing (primary falsifier).** `Gap_Sel(c_hat) < floor` OR
  its bootstrap 95% CI includes 0 OR `Gap_Sel(random) < 0` with CI excluding 0
  (the permuted gate is strictly MORE selective than the true gate) OR the
  cost-protection gap (permuted minus true known false refusal in the c_hat
  condition) is not strictly positive with CI excluding 0. Any of these means the
  permuted gate is as selective as, or more selective than, the true gate, so the
  gate's row selection contributes nothing beyond the raw dose count, and the
  "selectivity comes from the gate" claim is falsified on this substrate.
- **Gate benefit/cost fails (P1).** `true_gate__c_hat` confab abstention < 0.60,
  or Wilson 95% LCB <= 0.50, or well-formed < 0.80, or known-correct false refusal
  > 0.05 point, or Wilson 95% UCB >= 0.10. The gated controller does not reproduce
  its benefit/cost under the wide instrument.
- **Direction-specificity (secondary S1, cannot rescue or falsify the gate axis).**
  The write is NOT direction-specific for a family if its gated confab lift is
  same-signed as the census null median AND the effect ratio against the census
  max-over-K denominator is < 3.0. Reported straight; a mistral S1 failure is
  expected and does not touch P1/P2/P3. A qwen S1 that fails sign-opposition (the
  gated lift somehow suppresses, matching the census) would itself be a surprising
  falsification of the qwen direction-specificity expectation, reported straight.

There is no rescoring lane behind the blinded adjudication lane: if a criterion is
not met, the corresponding claim is falsified and the result stands. Goalposts do
not move after the result.

## Gates

Per-cell gates are in `gates.yaml`. Wilson 95% CIs (alpha 0.05) on every rate;
bootstrap 95% CI on every gap and every sign fraction. Integrity gates (SC0-SC3,
CG1) are inherited from the census/RR3; the criterion gates (P1/P2/P3, S1) are the
new pre-registered adjudication surface.

- **SC0 (provenance and staging).** Every source runlog, baseline artifact, frozen
  direction JSON, and fit build_manifest staged into gitignored
  `analysis/staged_inputs/` with sha256 and row/vector counts in a committed
  ID-manifest (no text). The fixed S_confab subsample per family drawn by the
  registered permutation seed and its opaque-id list committed BEFORE any
  generation or grading. Reused baseline and gated text pass an RG0-style
  byte-repro check against the source runlog on the graded rows.
- **SC1 (magnitude-matching and randomness).** Every dosed write is an erase-write
  to the family setpoint (qwen dose_abs 12.608, mistral 3.665) with
  `readback_measured` within a RELATIVE tolerance of target of 0.005
  (|readback - target| / target <= 0.005; census corrected relative bar,
  `placebo-seed-distribution-census/gates.yaml` line 34). Each drawn random
  direction is genuinely random: |cos| to `c_hat` <= 0.015 AND |cos| to `u_d` <=
  0.015 (RR3 red-team bar, census `gates.yaml` lines 35-37). A seed whose write
  fails setpoint or randomness is voided before grading and redrawn from the next
  pre-registered seed; the void is recorded.
- **SC2 (grading integrity, hash-commit-before-unblind).** Blinded context-free
  adjudication per RR3/census: pool sha256 and opaque-id list committed BEFORE
  grading; graded-file sha256 committed BEFORE the opaque-id -> row_key mapping is
  read; the apply tool refuses to join otherwise (enforced in code). Grader
  calibration per shard AND pooled: clear-negative agreement >= 0.95 per shard;
  clear-positive agreement >= 0.60 per shard AND >= 0.60 pooled; >= 25
  clear-positive decoys per shard; clear-negative decoys from the held-back pool
  only. A shard failing either floor is voided before unblinding and regraded once
  by a fresh context-free agent; a second failure voids that shard's rows and is
  reported straight. Decoys excluded from every scored rate.
- **SC3 (paired population and coverage).** Every rate is computed over the
  registered rows for its arm and population; the gate-selectivity gap and
  cost-protection gap are computed over paired populations (the same confab-graded
  set and the same full known pool across the arms compared). Unpaired, missing,
  or degenerate rows are reported separately, never folded into a rate or gap.
  Every rate carries a Wilson 95% CI; every gap a bootstrap 95% CI. The full K-seed
  random ensemble is reported per family regardless of the criterion verdicts.

## Predictions scoreboard

Registered 2026-07-15, pre-run, before the analysis harness was built, by both
predictors (orchestrator and PI). No edits after results.

| Predictor | Qwen gate axis (P1/P2/P3 pass/fail) | Qwen direction axis (S1 pass by sign-opposition / fail) | Mistral gate axis (P1/P2/P3 pass/fail) | Mistral direction axis (S1 pass / fail) | `Gap_Sel(c_hat)` band per family |
|-----------|------|------|------|------|------|
| orchestrator | PASS | PASS (by sign-opposition) | PASS (the dissociation case: gate supplies selectivity even where direction fails) | FAIL (expected effect ratio ~2.0 < 3.0) | qwen 0.20-0.50; mistral 0.20-0.45 |
| PI | PASS | PASS | FAIL | FAIL | none registered numerically; implied by axis calls (qwen >= 0.20, mistral < 0.20) |

The differentiating slot is the MISTRAL GATE AXIS: the orchestrator calls it
PASS (the design's dissociation thesis: the true gate fires 0/382 knowns, so
selectivity should survive a falsified direction axis), the PI calls mistral
FULL FAIL on both axes (PI: "i think qwen is full pass, mistral is full fail").
The two predictors agree on every qwen slot and on mistral S1. Whichever way
the mistral gate axis lands, exactly one predictor's call survives; adjudicated
in the Outcome, no edits after results.

## Doc-vs-intent tensions found (reported straight, not resolved)

1. **"Section 4.4 lineage" names a different model and site than the census null.**
   The lead's design intent pins the qwen controller to "paper 5 section 4.4
   lineage." Section 4.4 is the `doubt-gated-caution-tighten` controller on
   `unsloth/Qwen3-4B` at hs34, dose 200 realized units
   (`experiments/doubt-gated-caution-tighten/AMENDMENT.md` lines 42, 81, 96-98).
   The census suppressive qwen null that makes qwen the strongest specificity
   setting was measured on a DIFFERENT model, `Qwen/Qwen3.5-4B`, at hs20, dose_abs
   12.608 (the promoted `qwen35-4b-midband-heldout` controller, section 4.5
   lineage; census `cell.yaml` lines 31-40). No census null exists for the
   Qwen3-4B hs34 point, and its random/permuted controls were graded under the
   narrow detector only (`papers/paper-5-actuation/manuscript.md` lines 504-516).
   To use the census null as the direction-specificity reference, the factorial
   MUST run at the census operating point. The draft reads "section 4.4 lineage"
   as "the gate-and-snap METHOD introduced in section 4.4, instantiated at the
   section-4.5 promoted hs20 operating point where the census null lives," and
   pins qwen to Qwen3.5-4B hs20 (Decision record item 1; DECIDED by the PI,
"yes def do 3.5 4b hs20", 2026-07-15). If the lead had intended the
   literal Qwen3-4B hs34 controller, a matched census on that point would be a
   prerequisite, adding scope.

2. **The both-conditions success signature needs a sign-robust statistic, not a
   raw-rate contrast.** The lead's success signature is "true gate beats permuted
   gate on selectivity in both direction conditions." A raw-rate contrast
   (`confab_abstention - known_false_refusal`) cannot carry it: in the c_hat
   condition the write induces refusal and the gap is large and well-defined, but
   in the random condition on qwen the write SUPPRESSES confab hedging and knowns
   have almost no hedging to suppress, so the raw contrast collapses and flips sign
   (the permuted gate, firing fewer confab rows, suppresses less and shows a higher
   residual confab abstention). The draft resolves this with the sign-robust
   `Sel_abs = |confab_lift| - |known_lift|` (Design, item 2): because the true gate
   fires more confab rows than the permuted gate, it concentrates a larger share of
   the write's magnitude on confab in BOTH conditions, so `Gap_Sel(d) >= 0` is a
   coherent both-conditions statement. The draft registers a magnitude floor (0.20)
   in the c_hat condition, where the write is behaviorally potent, and a directional
   `Gap_Sel(random) >= 0` in the random condition, whose magnitude is expected small
   under suppression and is reported straight rather than forced to a positive
   floor. This honors the both-conditions signature. RESOLVED at sign: the PI
   confirmed the random-condition leg stays DIRECTIONAL-ONLY, no magnitude floor
   (Decision record, item 4).

3. **The mistral direction reference is the census K=15, not the flat +/-2 or the
   RR3 K=3.** RR2 used a flat +/-2 point placebo tolerance; RR3 used max-over-K=3
   fresh seeds (ratio 1.87). The census now provides a K=15 max-over-K magnitude
   (mistral 0.2033), superseding both per the paper's section 6.5 design rule
   (`papers/paper-5-actuation/manuscript.md` lines 731-739). The draft uses the
   census K=15 denominator for S1. This makes the mistral direction-specificity
   test STRICTER than RR3's, not looser; it is expected to fail again (~2.0), and
   that is reported straight, not treated as a rescue.

## Outcome

Resolved 2026-07-16. All numbers below are from
`analysis-committed/factorial_report.json` (generated by the pinned `report.py`
over the CG1-passed blinded adjudication; bit-identical on re-run) and were
adjudicated after an adversarial red-team review returned CONFIRM-NULL for both
families (see "Red-team record" below).

**Verdict (one sentence, mirrored in `experiment.yaml` `verdict:`).** The gate
axis is falsified on both families: the dosed c_hat write alone drives most of
the abstention lift (permuted-gate confab abstention 0.550 qwen / 0.600 mistral
vs baselines 0.083 / 0.282), and the true doubt gate adds a real but sub-floor
selectivity increment (Gap_Sel(c_hat) 0.148 qwen, 0.129 mistral, both CIs
excluding zero but entirely below the 0.20 floor) with cost protection far
below its 0.10 floor, while direction-specificity S1 passes on qwen (ratio
7.27, sign-opposed) and fails on mistral (ratio 2.03, same-signed), as
predicted.

### Per-family criterion results

**Qwen3.5-4B (hs20, dose_abs 12.608).**

- P1 PASS. `true_gate__c_hat`: confab abstention 0.6892 (918/1332, Wilson 95%
  [0.6638, 0.7135], LCB > 0.50, floor 0.60 met); well-formed 0.9775 (floor
  0.80); known false refusal 0.0417 (15/360, Wilson [0.0254, 0.0676], rate <=
  0.05 and UCB < 0.10).
- P2 FAIL (primary falsifier trigger). Gap_Sel(c_hat) = 0.1480, bootstrap 95%
  [0.1191, 0.1772]: excludes zero but the entire CI is below the 0.20 floor.
  Random leg (K=5 accepted seeds): median Gap_Sel(random) = -0.0006, bootstrap
  [-0.0100, 0.0028]; directionally negative but not confidently negative, so it
  does not itself trigger the falsifier.
- P3 FAIL (primary falsifier trigger). Cost-protection gap 0.0083, bootstrap
  [-0.0111, 0.0278]: CI includes zero, floor 0.10 not met.
- S1 PASS. Gated confab lift +0.6059 is RECRUITING and sign-opposed to the
  census suppressive null (median delta -6.0 pts); effect ratio 7.27 against
  the census K=15 max |delta| 0.0833, floor 3.0.
- Arm rates: baseline confab abstention 0.0833 (111/1332), known 0.0000
  (0/360); permuted_gate c_hat confab 0.5495 (732/1332), known 0.0500 (18/360);
  true_gate c_hat confab 0.6892 (918/1332), known 0.0417 (15/360).
- Fired counts: true gate 1303 (1286 confab, 17 known); permuted gate 1303
  (1025 confab, 278 known). Random-condition subsample: true gate 312 fired
  (295 confab, 17 known), permuted gate 510 fired (232 confab, 278 known) per
  seed.

**Mistral-7B-Instruct-v0.3 (hs16, dose_abs 3.665).**

- P1 PASS. `true_gate__c_hat`: confab abstention 0.6944 (911/1312, Wilson
  [0.6689, 0.7187]); well-formed 0.9863; known false refusal 0.0052 (2/382,
  Wilson [0.0014, 0.0189]).
- P2 FAIL (primary falsifier trigger). Gap_Sel(c_hat) = 0.1285, bootstrap
  [0.1034, 0.1556]: excludes zero, entirely below the 0.20 floor. Random leg:
  median Gap_Sel(random) = +0.0145, bootstrap [-0.0133, 0.0483], directional
  pass.
- P3 FAIL (primary falsifier trigger). Cost-protection gap 0.0340, bootstrap
  [0.0157, 0.0550]: real and positive but below the 0.10 floor.
- S1 FAIL (as predicted by both predictors). Gated confab lift +0.4123 is
  same-signed as the census recruiting null (median +7.0 pts); effect ratio
  2.03 against the census K=15 max |delta| 0.2033, floor 3.0. This reproduces
  the RR2/RR3 direction-axis failure under the stricter K=15 denominator.
- Arm rates: baseline confab abstention 0.2820 (370/1312), known 0.0052
  (2/382); permuted_gate c_hat confab 0.5998 (787/1312), known 0.0393 (15/382);
  true_gate c_hat confab 0.6944 (911/1312), known 0.0052 (2/382).
- Fired counts: true gate 1303 (1303 confab, 0 known); permuted gate 1303
  (1006 confab, 297 known). Random-condition subsample: true gate 297 fired
  (297 confab, 0 known), permuted gate 532 fired (235 confab, 297 known) per
  seed.

### Falsifier adjudication

`gate_contributes_nothing` fires in BOTH families via the P2 magnitude floor
and the P3 floor. `gate_benefit_cost_fails` does NOT fire (P1 passed both
families). Per the registered falsifier text, the "selectivity comes from the
gate" claim is falsified on both substrates. Reported straight: the gate's
contribution is not zero (both Gap_Sel(c_hat) CIs exclude zero, and the true
gate's fired-set composition is the designed dissociation, 96.5-100% confab vs
the permuted gate's ~77%/77% deployment ratio), but it is decisively below the
pre-registered floor that the "gate supplies selectivity" claim required. The
write, not the gate, supplies most of the abstention behavior at these
operating points.

### Integrity gates (SC0-SC3, CG1)

- SC0 PASS: staging complete with committed ID-manifests
  (`staging_manifest.json`, `subsample_manifest.json`); RG0 byte-repro of
  reused baseline/gated text passed both families; qwen permuted-gate
  construction reproduced the midband-heldout fired-row set byte-for-byte.
- SC1: the first generation run FAILED SC1 (dose-squaring defect,
  `sc1_verification_summary.json`, retained; mis-dosed runlogs quarantined
  under `analysis/quarantine_gain_squared/`, never graded). After the
  PI-approved fix and audited repin, GPU preflight passed both families and
  regeneration passed full per-row SC1 (worst readback rel_delta 0.002576 vs
  the 0.005 bar; `sc1_verification_summary_v2.json`). The randomness bar
  voided 7 qwen and 15 mistral raw draws; the registered redraw walk accepted
  qwen {44000003, 44000007, 44000010, 44000012, 44000013} and mistral
  {45000002, 45000010, 45000011, 45000014, 45000021}
  (`random_seed_ledger.json`); all voids occurred pre-generation on the
  direction vector, outcome-independent.
- SC2 PASS: pool sha256s and opaque-id lists committed before grading
  (`pool_manifest.json`); all 28 graded-file sha256s committed before any
  unblinding (`adjudication_graded_manifest.json`); CG1 28/28 shards PASS on
  attempt 1, clear-negative agreement 1.000 on every shard (floor 0.95),
  clear-positive per-shard minimum 0.7059 and pooled 0.8950 over 1447 decoys
  (floor 0.60); zero voided shards, zero regrades
  (`adjudication_applied_manifest.json`).
- SC3 PASS: n_missing = 0 on every cell; paired-population diagnostics show
  zero dropped rows per map in both families; 19298/19298 core rows applied;
  the full K=5 random ensemble is reported per family in the report JSON.

### Scoreboard adjudication (registered pre-run; no edits after results)

Actuals: qwen gate axis FAIL, qwen S1 PASS, mistral gate axis FAIL, mistral S1
FAIL.

| Slot | Orchestrator call | PI call | Actual | Correct |
|------|-------------------|---------|--------|---------|
| Qwen gate axis | PASS | PASS | FAIL | neither |
| Qwen S1 | PASS | PASS | PASS | both |
| Mistral gate axis (differentiating) | PASS | FAIL | FAIL | PI |
| Mistral S1 | FAIL | FAIL | FAIL | both |

The PI's call survives the differentiating slot; final tally PI 3/4,
orchestrator 2/4. Both predictors missed the qwen gate axis, and both
registered Gap_Sel bands (orchestrator qwen 0.20-0.50, mistral 0.20-0.45; PI
implied qwen >= 0.20) overshot the realized 0.148 / 0.129. The orchestrator's
dissociation thesis for mistral (perfect fired-set selectivity should carry
the gate axis despite a falsified direction axis) failed on magnitude: even a
0-known fired set only protects costs the permuted write would otherwise
incur, and the permuted write incurred only 0.039 known false refusal, leaving
cost protection at 0.034, far under the 0.10 floor.

### Red-team record

An adversarial review (opus tier) ran before this Outcome was written, per the
paper-changing-null guardrail. Verdict: CONFIRM-NULL, both families. Checks
that passed: formula fidelity of Sel_abs/Gap_Sel/cost-protection/S1 against
this document (hand-recomputed, exact reconciliation); independent
re-derivation of every c_hat-condition rate from `adjudication_applied.jsonl`
(exact match, n_missing 0); fired-row overlap between true and permuted gates
at independence expectation (qwen 1001 observed vs 1003.4 expected, mistral
999 vs 1002.2), ruling out a construction defect that would mechanically
compress Gap_Sel; dose integrity of every consumed runlog (readbacks within
2.4e-3 relative, no quarantined artifact in any consumed path); CG1 and the
positional-join line-equality assertions; bootstrap resampling unit (row
indices within paired groups, fixed seeds); and baseline sanity (the qwen
baseline 0.0833 is genuinely 111/1332 from the baseline arm, its equality to
the census 1/12 denominator is coincidence). One hygiene note, reported
straight: the void-and-redraw walk's exact "next sequential integer" rule was
pinned in `compute_seed_ledger.py` on 2026-07-16, the day after sign; the
signed text said "redrawn from the next pre-registered seed" without
enumerating the sequence past the first block of five. The rule is
deterministic, all voids were pre-generation randomness-bar failures with no
outcome dependence, and the accepted seeds feed only the non-decisive random
legs (both families falsified on the c_hat legs, which use no random seeds),
so this cannot move any verdict.

### Locked surfaces

No locked verdict moves. This experiment is exploratory instrument/mechanism
tier, reported separately from every locked surface. The paper 5 headline
matrix, the census verdicts, and the midband-heldout/RR2/RR3 outcomes are
untouched; what changes is the INTERPRETATION available to the paper: "gated
dosing produces selective abstention" can no longer be attributed to the
gate's row selection at these operating points, and any such claim must be
rewritten as a write-plus-deployment-ratio effect pending a confirmatory
replication at a design point where the gate axis could pass its floors.
