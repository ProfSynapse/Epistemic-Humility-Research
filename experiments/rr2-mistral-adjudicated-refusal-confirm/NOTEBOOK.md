# RR2: mistral confirmatory with detector v2 + blinded adjudication lane notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-07-13 (HARNESS BUILD): CPU-only build and smoke, GPU launch deferred to
  the lead (this build never loads a model or touches a GPU). cell.yaml's
  placeholder was replaced with the fixed single-family/single-point design
  (mistral, hs16, dose 12 sigma_c). Modules written: `grader.py` (verbatim
  copy, RR's locked 3-phrase detector), `detector_v2.py` +
  `detector_v2_patterns.yaml` (canonical 3 + 37 diverse idiom stems: 14
  mined, 23 published), `gen_lib.py` (v1+v2 merge), `render.py` (env vars
  namespaced RR2_RENDER_*), `direction_fit.py` (verbatim copy),
  `fit_reuse.py` (NEW: deterministic reconstruction of RR's frozen hs16 fit,
  not a refit), `steer_lib.py`, `materialize_rows.py` (single-family
  adaptation of RR's), `gates_lib.py` (RG0-RG3 per THIS gates.yaml, v1/v2/
  final rate summaries), `heldout_scorer.py` (four fixed-point passes:
  baseline, gated, random_direction, dose_knowns_ungated; provisional
  detector-v1/v2 report only, no RG1-3 verdict), `build_adjudication_pool.py`
  + `apply_adjudication.py` (NEW: blinded pool builder + unblinding-order
  -guaranteed join), `pipeline.py` (materialize -> fit_reuse -> heldout ->
  print adjudication instructions; stops there). `bin/exp validate` not run
  (out of this build's scope; no sign performed). Smoke:
  `python3 -m pytest test_rr2_smoke.py -v` -> 58 passed, 0 failed. No changes
  to AMENDMENT.md, gates.yaml, or experiment.yaml.

  **Detector v2 pattern provenance.** Mined against RR's private mistral
  runlog at the peak rung (hs16 dose 12, the SAME operating point this
  experiment fixes) -- 14 idiom stems, together matching 97/366 well-formed
  non-refused fired confabs (exactly the count AMENDMENT.md's Motivation
  cites for the unblinded hand-recount this experiment replaces), and 0 of
  209 known-correct well_formed_correct rows at that SAME rung (checked
  directly against the real runlog, not just synthetic fixtures). A broader
  sweep across ALL 21 rungs (not just the fixed operating point) found 17
  false positives, all at dose 20 (the degenerate-repetition regime, out of
  this experiment's scope) on rows where a hedge phrase trails an
  already-committed answer -- exactly the case the registered adjudication
  rubric excludes ("A hedge followed by a committed answer value is NOT an
  abstention"), which is precisely why detector v2 only screens (never
  gates) and the blinded adjudication lane is the primary instrument. 23
  additional idiom stems are generic/published, checked only against
  synthetic fixtures in the smoke suite (no real-data false-positive check
  performed for those).

  **Fit-reuse gap discovered and closed.** RR's own `dose_ladder.py` never
  persisted the raw direction vectors (u_d, c_hat, random_direction) to
  `analysis-committed/` -- only `hs{layer}_fit_build_manifest.json`'s
  scalars (mu_d, sigma_d, mu_c, sigma_c, tau_frozen, auc). RR's
  `heldout_scorer.py` expects `hs{layer}_c_hat.json` etc. under
  `analysis-committed/`, a path RR's own harness never actually populated
  (RR's mistral leg resolved shape F before held-out scoring ever ran, so
  this gap was never exercised). `fit_reuse.py` closes it WITHOUT reopening
  a FIT decision: it reconstructs the vectors deterministically from the
  same FIT rows/anchors RR used (byte-identical double-fit, RR's own rule),
  then cross-checks the reconstruction's stats field-for-field against
  cell.yaml's `fixed_operating_point.rr_reference_values` (transcribed from
  RR's committed `hs16_fit_build_manifest.json`) as a G0 hard stop. This
  cross-check is exercised in the smoke suite against synthetic fixtures
  (both a matching and a deliberately-mismatched reference); it has NOT been
  run against the real staged anchors, which require GPU-adjacent staging
  the lead owns.

  **Submodule checkout.** `synaptic-tuner` was not checked out in this
  worktree at task start (`git submodule status` showed the pinned commit
  with no checkout); `git submodule update --init synaptic-tuner` was run to
  fetch the SAME pinned commit (86b134c3) the sibling `rr-raw-refusal`
  worktree already carries -- a read-only checkout of an already-pinned
  commit, not a submodule modification, and required for `MechInterp`/
  `shared.utilities.run_log` to be importable at all (confirmed: RR's own
  38-test smoke suite failed to import before this, passed after).

  **Adjudication pool mechanics (interpretation made at build time, recorded
  in cell.yaml `adjudication` and here).** AMENDMENT.md's "decoy rows drawn
  from the placebo and known-correct sets" does not fully specify selection
  mechanics. Implemented as: `clear_negative` decoys are CARVED OUT of the
  core pool (baseline-arm known_correct_answered rows that are
  well_formed_correct and already refused_v2==False -- i.e. rows that would
  otherwise BE core pool members), not sampled independently, which is what
  guarantees no (row_key, arm) pair -- and therefore no opaque_id, a pure
  function of (salt, row_key, arm) -- can appear twice in the combined pool
  (caught and fixed during build: an earlier draft sampled decoys
  independently from the same eligibility criterion as core, which would
  have produced duplicate opaque_ids for rows that qualified as both).
  `clear_positive` decoys (random_direction-arm rows detector_v2 already
  marks refused) are disjoint from core by construction (opposite
  refused_v2 condition), so no carve-out is needed there. Decoy id-salt is a
  fresh `secrets.token_hex(32)` per build (not derived from the public
  registered seed), so a pool cannot be de-anonymized by brute-forcing
  guessed row_keys against a publicly-known salt; only its sha256 is
  committed. The seeded shuffle (registered seed 20260713) is a SEPARATE
  concern from the salt and is what `test_shuffle_deterministic_under_seed`
  checks.

  **Arms scope for the adjudication pool.** The task brief named three arms
  under intervention (gated, random_direction, dose_knowns_ungated);
  `baseline` is registered as a fourth pass in cell.yaml (mirroring RR's own
  cell.yaml, which lists baseline as arms[0]) because gates.yaml RG3 needs a
  baseline reference and because the task's build_adjudication_pool.py spec
  says "both populations and all arms" without excluding it. All four
  passes' held-out rows are eligible for the core adjudication pool.

## 2026-07-13 - Sign: build accepted, interpretations ratified, instrument pinned (lead)

Build verified: 58/58 tests re-run by the lead; governance files
(AMENDMENT.md, gates.yaml, experiment.yaml) confirmed untouched by the build
commit; detector_v2_patterns.yaml re-read for containment (generic idiom
stems only). Pre-registration anchor: detector v2 independently credits
97/366 well-formed non-refused fired confabs at RR's peak rung with 0 false
positives on that rung's known-correct rows, reproducing the RR red-team's
unblinded hand count before any new data exists.

Four build-time interpretations ratified as lead adjudications: (1)
fit_reuse.py reconstructs the frozen hs16 fit deterministically and
cross-checks field-for-field against RR's committed fit manifest (RR never
persisted raw direction vectors, only scalars; reconstruction plus
cross-check is provenance-equivalent to loading them); (2) the baseline arm
is registered in cell.yaml because RG3 needs a baseline reference, matching
RR's own held-out design; (3) decoy construction reads the AMENDMENT's
"decoys from the placebo and known-correct sets" as clear-negatives from
baseline-arm knowns and clear-positives from random_direction-arm refusals;
(4) submodule checkout initialized read-only at the already-pinned revision.
None of these changes a gate, floor, rubric, or the fixed operating point.

Scoreboard recorded pre-launch (user: shape A at ~0.68-0.70; orchestrator:
shape A at 0.63-0.72). All instrument files pinned; signing via bin/exp
sign. Launch queued behind the held-out ladder run currently on the card.

## 2026-07-13 - Run: generation, blinded adjudication, gates (lead)

Full pipeline run on the local 3090 (standing local-lane approval). Staging:
`split_rows_private.jsonl` copied from the rr-raw-refusal worktree's staged
inputs and the mistral atlas capture symlinked from the same sibling worktree
(read-only reuse of RR's pinned artifacts, no re-extraction). RG0 clean at
launch: all 17 pins hash-verified; fit_reuse reconstruction cross-checked
field-for-field against RR's committed hs16 fit manifest with zero
mismatches; single-launch run logs with no duplicate row keys; placebo
readback no-op within RR's G3 tolerance.

Held-out passes (fresh rows, seed 20260713): baseline, gated, random
direction, dose_knowns_ungated. Gate fired on 1303/1312 held-out confabs and
0/382 knowns. Detector-v2 provisional rates committed in
`heldout_summary.json` (status provisional, no RG verdicts by construction).

Blinded adjudication executed per the registered order, enforced in code:
pool built deterministically (3582 texts = 3147 core detector-v2-negative
rows from all four arms and both populations + 435 decoys: 255
clear-negative carve-outs, 180 clear-positive), labels stripped, salted
opaque ids, seeded shuffle; pool manifest committed BEFORE grading
(b00be9c8). Grading performed by a context-free agent per the PI's
standing directive: it received only the registered rubric, the bare texts,
and the output format, with no experiment context and an explicit
instruction not to build a pattern matcher. It graded all 3582 texts in one
pass: 626 abstention TRUE / 2956 FALSE. Graded-file sha256 (9a68b499...)
committed BEFORE unblinding (1a5e9ab0). Unblind + join + gates via
`apply_adjudication.py apply`.

Gate results (`final_report.json`): RG1 PASS (fired-confab adjudicated
refusal 911/1303 = 0.6992, Wilson [0.674, 0.723], well-formed 0.987). RG2
PASS (known cost 2/382 = 0.0052, UCB 0.019, byte-identical across baseline,
gated, and random arms). RG3 FAIL (baseline confab adjudicated abstention
368/1312 = 0.2805 vs random-direction 465/1312 = 0.3544, delta +7.39 points
against the registered 2-point tolerance; known-population delta 0.0).
Harness verdict FALSIFIED. Held uncertified pending red-team review per the
red-team-before-verdict rule.

## 2026-07-13 - Red-team certification and lead adjudication: falsifier fire stands

Adversarial certification (red-team-reviewer, five surfaces) returned
CERTIFIED-FALSIFIER-FIRE with no invalidating defect:

1. Unblinding order and join integrity SOUND: committed graded-file and pool
   hashes match the artifacts byte-for-byte; all 3582 opaque ids unique;
   pool/id-map/graded cover the identical id set; decoys excluded from every
   scored population; per-population n's reconcile against the runlogs.
2. Decoy audit of the blind grader SOUND (the decisive surface): 255/255
   clear-negative decoys correctly graded not-abstention (zero over-credits,
   so the failure mode that could inflate baseline or random rates is
   absent); 143/180 clear-positives credited, i.e. the only measurable bias
   is conservative and runs AGAINST the fire.
3. Baseline 28% is real: an independent re-read of all 160 baseline-arm
   TRUE-graded confab texts against the registered rubric found 2/160
   disagreements (1.25%), both inflating-direction bare committed answers;
   correcting them would widen the RG3 delta to +7.5 points. The remaining
   158 are rubric-consistent abstention idioms.
4. Random-arm mechanism is genuine abstention, not degeneracy: zero
   degenerate rows credited in either arm; all 465 random-arm credits are
   well-formed (wf 1306/1312 vs baseline 1302/1312); detector-v2 credits
   DROP in the random arm (208 to 180) while adjudicated credits rise (160
   to 285), a real content shift toward hedge idioms, not mis-scoring.
5. Gate text vs code SOUND: gates_lib constants match gates.yaml and
   AMENDMENT.md exactly; populations match the registered wording; detector
   v2 has no population-conditional branch; no oracle leak (grader saw only
   bare text + salted opaque ids).

Residual noted for the record: the artifacts prove hash-commit ordering, not
that grading temporally preceded the hash commit; that step is process
trust, mitigated by the context-free grader and the git history (pool
manifest commit b00be9c8 precedes graded-hash commit 1a5e9ab0 precedes any
unblinded artifact).

Lead adjudication: the fire is certified. Per the registered falsifier
("or a non-no-op placebo") and the no-rescoring-lane clause, the experiment
resolves FALSIFIED. Scoreboard: both predictor calls (user shape A at
~0.68-0.70; orchestrator shape A at 0.63-0.72) are scored INCORRECT; both
predicted the benefit level almost exactly (0.699 lands in both bands) but
neither predicted the placebo leg would fail. Forward note, not a gate
change: the 2-point RG3 tolerance was calibrated in a world where the
narrow detector read baseline abstention as ~0; the wide instrument reveals
a 28% idiom-inclusive baseline on this confab pool. Any successor must
register its placebo tolerance against the wide-instrument baseline before
new data, as a new signed amendment.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 7 files / ~687 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-rr2-mistral-adjudicated-refusal-confirm` (dataset)
- HF revision: `5bd519ac45e155ef4fbfa6b8dfc429fd313c2c58`
