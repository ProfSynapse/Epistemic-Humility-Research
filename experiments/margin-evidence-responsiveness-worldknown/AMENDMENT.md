# Evidence-responsiveness on world-known QA: the M4 rebase (M4-WK)

Status: SIGNED 2026-07-17. Pre-sign red-team applied (1 BLOCKER + 4 MAJOR + 5
minor, all resolved; see NOTEBOOK 2026-07-17); open forks adjudicated by the PI;
transfer firing floor set at AUROC 0.70; instrument pinned at sign. Scoreboard
registered (both predictors EARNED on the transfer direction; Slot 2 differs,
orchestrator projection vs PI margin).

The machine state lives in `experiment.yaml`; the pinned instrument in `cell.yaml`
and `gates.yaml`; the pre-sign feasibility probe, seeds, and governance notes in
`NOTEBOOK.md`. This document is the prose home.

## Motivation and posture

The framework's earnability criterion for mentalistic names
(`docs/research/margin-theory-framework.md` section 3) has four parts. A name like
"doubt" is earned for the c_hat activation when it (a) tracks actual ignorance,
(b) drives abstention when amplified, (c) does so direction-specifically, and (d)
"responds to evidence the way doubt should: supplying the true answer in-context
should collapse the projection on that row and lengthen its margin." Qwen
satisfies (a) through (c); (d) is the one untested part. Mistral fails (c), so
mentalistic naming is already retired there regardless of (d): this cell is
qwen-only, consistent with the qwen-only spine.

**Why a rebase, not M4.** The signed M4 (`experiments/margin-evidence-
responsiveness`, SIGNED 2026-07-17) is **void-by-design**. Its `true_answer` and
`false_answer_placebo` arms each require a gold answer per row, but M4's population
is M1's KUQ subsample, whose confab rows are all `kuq_unknowns_all:*` - unknowns
to anyone by construction, carrying **no gold-answer field**. There was nothing to
inject in the true-answer arm and no gold basis for the category-matched
distractor; the instrument cannot be run as written. This is exactly the field
whose absence a pre-sign feasibility probe would have caught, and M4 skipped it.
M4-WK rebases onto a **world-known** population (PopQA) where every row has a gold
answer, so "confab" becomes **confident-wrong-on-an-answerable-question** rather
than answered-a-KUQ-unknown. The lead will resolve M4 as void-by-design /
superseded by this slug (NOTEBOOK governance note).

Posture: exploratory instrument/mechanism tier, qwen35_4b only, reported
separately, never pooled with the locked Phase 1 headline matrix. M4-WK
adjudicates a naming criterion; it cannot move a locked verdict.

## Design

Substrate, capture convention, dose law, and detector stack are carried from the
M1/M2/M4 lineage byte-identically (pins in `cell.yaml`). Substrate is the
direction's own substrate, `Qwen/Qwen3.5-4B` rev
`851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, bf16, `enable_thinking=False`, under
the frozen `BASELINE_SYSTEM_PROMPT` + chat template - **not** Amendment S's 4-bit
Instruct base with a neutral prompt (its labels are non-reusable; the population
is regenerated). The readout SIGN is pinned in code for each direction (registered
score = negative-z, confab-positive): the raw on-disk projection is
confab-negative, the M2 trap.

**Two directions.**
- **TRANSFER (primary):** the KUQ-fit c_hat, reused byte-identically
  (`experiments/qwen35-4b-midband-doubt-snap/analysis-committed/directions/hs20/
  c_hat.json`, sha256 `937d1bff…`, layer_index 19, hs20, negative-z). This tests
  whether the direction that earned the "doubt" name on the KUQ error class
  (answered-on-unknown) also fires on, and responds to evidence for, a *different*
  error class (confident-wrong-on-answerable). Criterion (d) is a naming test for
  *the specific c_hat that got named*, so **transfer is the literal test of (d)**
  and its verdict is primary.
- **NATIVE (secondary/robustness):** a world-known c_hat refit with
  `fit_midband_directions.py` verbatim at hs20, roles remapped, on a **disjoint
  fit split**. Produces `c_hat_worldknown.json` (`mechinterp-direction/v1`,
  sha-pinned at the fit stage) - a first-class reusable direction with its own
  re-derived reference dose. Reported as a dissociation reading, never rounded
  into the (d) verdict.

**Two channels, each run for both directions.**
- **Channel 1, projection collapse** (capture only, forward pass): the per-row
  negative-z projection in each of three arms on the test confab rows (400) and
  correct-control rows (360). Confab test is a conjunction - leg 1, the paired
  median shift toward the correct/refused regime (`no_answer_baseline_z −
  true_answer_z`) meets a floor; leg 2, specificity, the true-answer shift exceeds
  the false-answer shift by a paired bootstrap 95% CI excluding zero. Hidden states
  are captured **once per arm** and projected onto **both** directions post-hoc (a
  dot product), so there is one capture pass, two readouts.
- **Channel 2, margin lengthening** (Option A single-dose survival). A per-row
  tipping dose does **not** transfer from KUQ, so M1's margin ladder is **rebuilt
  on the world-known population** first (per direction, the expensive half), then
  for each margin-eligible confab row the boundary push is applied at that row's
  own world-known tipping dose under each of the three arms. Survival = non-
  abstaining and well-formed at that dose. The test is the paired survival-rate
  difference (true minus false). The `no_answer_baseline` survival is measured
  (not assumed 0%) as an in-regime staleness check (channel-2 S1; if it exceeds
  0.05 channel 2 voids). Each direction uses its own reference dose.

Context is injected **before** the question in the two answer arms so the len-1
capture anchor stays the question's last token in all three arms (M4 red-team M1
fix); leg 1 is a clean same-anchor paired shift. The false-answer placebo is a
category-matched within-dataset distractor (PopQA `prop` category), donor = the
gold of a different row in the same category by seeded permutation; the mapping is
opaque-id-only and committed pre-generation.

Instrument configs to be pinned at sign: `cell.yaml`, `gates.yaml`.

## The one new construct risk

On KUQ, "confab" meant *any non-abstention*; correctness was irrelevant and the
alias grader was never on the critical path. On world-known QA the confab class is
defined **by incorrectness**, so `grader._is_correct` (alias exact/normalized
match) is now on the critical path. Alias match is **conservative on correctness**: a
semantically-correct answer phrased outside the alias list is scored wrong and
mislabeled *confab*, contaminating the confab class with actually-correct rows,
which shrinks the true-answer collapse effect and biases D1 **against** earning
(d). Mitigation (SC2, gates.yaml): a blinded judge calibration slice, stratified
across `prop` categories, bounds the alias-grader false-wrong rate, reported as a
construct caveat - the world-known analogue of M1's CG1, extended to the
correctness bit.

### Injection circularity and the anti-tautology control

A second construct risk is circularity in the injection itself. Injecting the true
answer in-context moves any reasonable epistemic direction's leg-1 projection
partly by construction: the prompt now literally contains the answer, so a
direction that responds to an answer being present in context will shift whether or
not it tracks "doubt". The anti-tautology control for BOTH directions is therefore
leg-2 specificity, the category-matched `false_answer` placebo run under an
identical anchor and template. The placebo injects an answer-shaped string that is
wrong, so only a shift that is larger for the true answer than for the placebo is
evidence beyond the mere presence of an answer. The transfer direction is
additionally free of fit-circularity, because it is fit on a disjoint KUQ
answered-vs-refused contrast that does not involve this population or the
injection; that is why transfer carries the primary verdict and the natively-refit
direction stays a secondary/dissociation reading. Native, refit on this
population, has no such fit-independence and leans entirely on leg-2 specificity
for its anti-tautology guarantee.

## Decision record

Each knob is DERIVED (from committed data), CONVENTION (carried from a resolved
experiment), or JUDGMENT (a choice with rationale). PI-locked forks (from the
task's PI decisions) are marked LOCKED-PI.

1. **Dataset: PopQA only** (LOCKED-PI; JUDGMENT in the derivation). PopQA is the
   only source with 100% gold, a native 16-way category field (`prop`) for a clean
   category-matched distractor, and a long-tail difficulty gradient that
   manufactures a large confab class. TriviaQA is not pooled (no fine category →
   fallback distractor weakens the specificity leg).
2. **Direction primacy: transfer primary, native secondary** (LOCKED-PI). The
   framework claim is about the existing named c_hat; transfer is the literal test
   of (d). Native is a first-class robustness/dissociation reading.
3. **Native runs a full two-channel test** (LOCKED-PI): native is funded for both
   channel 1 (projection, free - same captures) and channel 2 (its own ladder
   rebuild with its own re-derived reference dose). The primary (d) verdict is
   transfer-only; the native two-channel result is a secondary dissociation
   reading.
4. **Grader: alias-match + blinded calibration slice** (LOCKED-PI): full labeling
   by `detector_v2.grade_one_v2` / `grader._is_correct`, plus a blinded judge slice
   to bound the false-wrong rate (§ construct risk), following M1/M2 blinded-
   calibration code (pool-hash-commit-before-grading, graded-hash-before-unblind,
   CG1 floors, 0.05 disagreement gate).
5. **Roles** (DERIVED from `detector_v2.grade_one_v2`): confab-on-answerable =
   `answered_v2 AND correct_v2 is False`; correct-on-answerable = `answered_v2 AND
   correct_v2 is True`; refused-on-answerable = `refused_v2 is True`; degenerate
   excluded.
6. **Population sizes** (DERIVED/JUDGMENT): test = 400 confab (channel-1 primary;
   the ~308 margin-eligible subset is realized post-ladder, reproducing M4's n),
   360 correct-control (mirrors M1's known control), refused as available;
   native-fit split = 400 confab / 240 correct / 180 refused, **disjoint** from
   test (mirrors doubt-snap hs20 fit sizes). The **full** PopQA pool (14,267) is
   generated as the census because correct/refused are the scarcer classes under
   the abstention prompt.
7. **Selection rule** (DERIVED, deterministic): census-label the full pool; permute
   each role group by seed 48260727; reserve the native-fit split first (disjoint),
   draw the test population from the remainder; commit all opaque-id lists before
   any fit or generation.
8. **Arms and before-question injection** (CONVENTION, M4 red-team M1): three arms,
   context before the question so the anchor is identical across arms.
9. **Single batching regime** (CONVENTION, M1b): census, captures, ladders, and
   survival passes each run in one pinned, recorded batch composition; no paired
   comparison mixes regimes.
10. **Floors RE-DERIVED, not carried** (DERIVED, the central rebase decision). The
    KUQ baseline gap (3.0005 vs 1.052) is invalid here. Two floors, each a
    formula-at-sign + numeric-at-baseline-repin, per direction:
    - **collapse_floor_z** = 0.5 × realized baseline gap, where gap =
      median(no_answer_baseline negative-z over confab) − median(over
      correct-on-answerable), measured fresh on the census under that direction.
      The **0.5× fraction is carried** (M4 item 1, the single registered bar, no
      0.25/0.75/1.0 fallbacks); the **numeric is frozen by a repin the moment the
      fresh baseline gap is measured, before any true/false shift is computed**
      (self-blinding preserved, no-goalpost rule).
    - **D2 absolute_floor** = normal-approx (Wald) 95% half-width
      `1.96·sqrt(0.25/n)` at the realized `n_margin_eligible`, plus CI-excludes-
      zero. The **formula is carried**; the **numeric is frozen by a repin the
      moment n is realized (post-ladder), before any survival contrast is
      computed** (anchor: 0.056 at n=308, M4's value).
11. **S1 baseline-reproduction adapted** (DERIVED): there is no committed baseline
    to reproduce, so S1 is (channel 1) the fresh baseline gap is strictly positive
    and, for the native direction, the census role-separation AUROC reproduces the
    native fit-split AUROC within 0.05; (channel 2) baseline survival ≤ 0.05.
    Halt-and-lift on failure.
12. **Native reference dose** (DERIVED, but recipe FLAGGED, see Open forks): the
    native direction's channel-2 reference dose is re-derived by the same
    standardization the KUQ reference dose used (mu_c/sigma_c of the native fit),
    frozen at the fit repin. The exact recipe for a freshly-fit direction is not
    spelled out in a prior governed doc - flagged for PI.
13. **Seeds** (CONVENTION, new distinct values past M4's 721–723): bootstrap
    48260724, distractor permutation 48260725, calibration slice 48260726,
    native-fit/test split 48260727 (see NOTEBOOK).
14. **Self-blinding** (CONVENTION from M2, extended): no paired shift, specificity
    difference, survival difference, **or realized floor number** computed pre-sign;
    only census baseline distributions, counts, id lists, hashes, and the distractor
    mapping.

## Reusable-artifact manifest

Every durable output is designed as a first-class, recyclable input:

1. **World-known correctness+abstention census** -
   `analysis-committed/census/qwen35_4b_worldknown_census.jsonl`. The COMMITTED
   file contains ONLY `{row_key, role ∈ {confab,correct,refused,degenerate},
   question_sha (hash), correct_v2 (correctness bit), refused_v2 (abstention
   bit)}`: no `generation_text`, no question text, and no answer text inline (MAJOR
   M3). The `generation_text` and any richer per-row metadata (`prop`,
   `source_id`, `s_pop`, `matched_pattern_ids`, `gold_aliases_present`,
   `answered_v2`) live in a **gitignored** sidecar,
   `analysis/census/qwen35_4b_worldknown_gen_text.jsonl`, keyed by `row_key`. This
   no-text-in-committed-path invariant holds regardless of PopQA being public;
   publishing generation text is a separate gated path (the `data-exhaust` skill's
   license gate), never the committed census. **Consumers:** M3 anisotropy (a
   world-known error-class population), M5 training bridge (confident-wrong
   examples for abstention training), family-atlas (per-family confab census),
   public data-exhaust (from the gitignored sidecar, license-gated).
2. **World-known margin/tipping-dose dataset** - M1's schema exactly
   (`tipping_dose_abs, tipping_censored, collapse_dose_abs, tipping_idx,
   well_formed[], refused_v2[], role, row_key`), one per direction. The KUQ margin
   dataset's world-known twin; reusable for any downstream margin work on
   answerable questions.
3. **Per-row projections** - `{row_key, arm, c_hat_transfer_z, c_hat_native_z}`
   for all three arms (both directions off shared captures). Reusable by M3 as a
   world-known readout channel.
4. **Native world-known direction** -
   `analysis-committed/directions/hs20/c_hat_worldknown.json`,
   `mechinterp-direction/v1`, sha-pinned. A first-class reusable direction.
5. **Distractor mapping** - `row_key → donor_row_key` (opaque ids, no text),
   committed pre-generation (SC0).

**Licensing / containment:** PopQA is public (card: not tagged on HF, companion
GitHub MIT), so generation text is exhaust-eligible **subject to the
`data-exhaust` license gate** (flag for PI, Open forks). KUQ is untouched; nothing
here touches OpenMOSS / Llama-2 bridge / any DO-NOT-REDISTRIBUTE data.

## Prediction

Registered at sign. On the TRANSFER direction, supplying the true answer
in-context both collapses the c_hat projection on confab rows (paired median shift
toward the correct/refused regime at or above the re-derived floor, and
specifically larger than the false-answer placebo) and lengthens their margins
(true-answer survival at each row's own world-known tipping dose exceeds the
placebo by more than the re-derived floor, CI excluding zero): qwen earns
earnability criterion (d) for the named KUQ direction. [Predictor calls filled at
sign in the scoreboard.]

## Falsifier

With all gates valid **and the transfer direction firing at baseline** (baseline
confab-vs-correct AUROC ≥ 0.70 on the test subset, gates.yaml S1 / BLOCKER B1), at
least one channel **on the transfer direction** fails its floor: either the
projection does not collapse toward the correct/refused regime specifically for the
true answer (D1 fails), or the margin does not lengthen for the true answer over
the placebo (D2 fails). Only then is criterion (d) **not earned on the named KUQ
direction**, and evidence-responsiveness does not license the mentalistic name for
c_hat on the world-known error class even though (a)–(c) hold. A single-channel
pass (on transfer) is reported as a channel dissociation, not rounded to earned or
not-earned. The native two-channel result is reported separately as a dissociation
reading and never changes this verdict.

If instead the transfer direction does **not** fire at baseline (AUROC < 0.70), the
KUQ direction simply does not fire on the world-known confident-wrong error class
(non-transfer): the criterion (d) test is **voided and lifted to PI**, not scored
as a (d)-not-earned failure. A non-firing transfer is not a falsification of
evidence-responsiveness; it means this population is out of the direction's domain.

## Gates

See `gates.yaml` (pinned at sign). Integrity: SC0 provenance/staging with the
committed native-fit-split and test opaque-id lists, the single-regime
attestation, and the pre-committed distractor mapping; SC1 dose readback (M1's
amended rule) plus mandatory GPU preflight and throughput probe; SC2 blinded
correctness AND abstention calibration slices with CG1 floors and the 0.05
disagreement gate; SC3 coverage plus the fit/test disjointness audit. S1: fresh
baseline gap positive (both directions), native AUROC reproduced within 0.05
(native only), channel-2 baseline survival ≤ 0.05. Criterion: on transfer, D1
(both legs) AND D2 for (d) earned; either failing is not-earned; a single-channel
pass is a reported dissociation. Native D1/D2 reported as a secondary reading.
Construct: C1 correct-control specificity, separation reproduction, the
alias-grader false-wrong bound, and the single-regime requirement; on_failure
instrument void, reported straight. The two re-derived floors follow the
formula-at-sign / numeric-at-baseline-repin mechanism, per direction.

## Predictions scoreboard

Registered at sign, after the design-info disclosure. Two slots (predictor rows
filled by the lead/PI at sign):

| Predictor | Slot 1: criterion (d) earned on the TRANSFER direction? | Slot 2: which channel is stronger |
|-----------|---------------------------------------------------------|-----------------------------------|
| orchestrator | EARNED (both channels pass, contingent on the transfer direction firing at baseline) | projection |
| user | EARNED (both channels pass) | margin |

The predictors AGREE on Slot 1 (both expect the in-context true answer to both
collapse the transfer readout and lengthen the margin, earning (d) on the named
KUQ direction) and DIFFER on Slot 2 (the differentiating value): the orchestrator
expects the projection channel to respond more strongly (the readout updates
directly to the injected evidence), the PI expects the margin channel to respond
more strongly (the true answer gives the model genuine grounding to hold under
the boundary push). Both predictions are conditional on the transfer firing floor
(baseline confab-vs-correct AUROC >= 0.70); a non-firing transfer voids the test
rather than resolving either slot.

Note: the NATIVE direction's two-channel result is a **secondary dissociation
reading**, reported alongside but never rounded into the Slot-1 (transfer)
verdict.

## Outcome

Filled at resolve. Record the verdict, the per-direction gate results (transfer
primary; native secondary), and the one-sentence summary that also goes into
`verdict:` in the manifest.
