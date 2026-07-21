# Correctness-geometry scale ladder (1.7B->8B->14B) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-20 -- CRITICAL: first "real" run was VOID (data path never wired); fixed, quarantined, repinned, relaunched

The first post-sign real run (previous entry below) completed exit 0 in
334.9s, 780 records -- but its own completion line read
`(SYNTHETIC-SMOKE -- no real labels touched)`. Lead read the pinned
`scale_ladder_real.py` (sha `c13e5792...`) directly and confirmed the real
run was VOID: the data-source routing was never actually wired to the
real-vs-synthetic flag.

**Root cause (four instances of the same defect, all in `main()`):**
1. `cache = synthetic_layer_cache(scale, needed_layers, cache_seed)` ran
   UNCONDITIONALLY. `real_layer_cache()` (defined, never called from
   `main()`) never ran. `--synthetic-smoke` gated only the pre-sign
   authorization guard (fixed in the entry below) -- never the data
   source itself.
2. `run_config["synthetic_smoke"]` was hardcoded `True`.
3. The output-json filename stub was `("real_ladder_synthetic_smoke.json"
   if True else "real_ladder.json")` -- a literal dead branch.
4. The completion print unconditionally emitted the SYNTHETIC-SMOKE
   marker.

**Contamination hazard:** the void run wrote 780 SYNTHETIC records into
`analysis/runlog/real_ladder.jsonl` -- the checkpoint path the REAL run
must resume from. A relaunch without quarantining this would have found
0 pending tasks (all keys already "done") and silently reported synthetic
numbers as real.

**Lead's ruling:** keep the safety property (the pre-sign guard from the
prior entry stays), fix the defect (the data routing itself), quarantine
don't delete. Minimal-diff repin, not a fresh sign cycle; `gates.yaml` and
all thresholds untouched.

**Fix, exactly as authorized:**
1. `scale_ladder_real.py` `main()`: cache selection now
   `cache = synthetic_layer_cache(...) if args.synthetic_smoke else
   real_layer_cache(scale, needed_layers)`; `run_config["synthetic_smoke"]
   = args.synthetic_smoke`; output filename branches on the flag
   (`real_ladder.json` for real, `real_ladder_synthetic_smoke.json` for
   synthetic), dead `if True` stub removed; completion-print marker only
   emitted when `args.synthetic_smoke`; runlog path now branches on the
   flag too (`real_ladder_synthetic{,_smoke}.jsonl` vs
   `real_ladder{,_smoke}.jsonl`) so real and synthetic resume logs can
   never collide again. No other line in the file touched.
2. Quarantined (renamed, NOT deleted): `analysis/runlog/real_ladder.jsonl`
   (+ `.meta.json`/`.summary.json`) -> same names with a
   `.CONTAMINATED-synthetic-20260720` suffix; the committed
   `analysis-committed/real_ladder_synthetic_smoke.json` (synthetic drill
   exhaust that had been mislabeled into the committed dir) moved to
   `analysis/real_ladder_synthetic_smoke.json.CONTAMINATED-mislabeled-20260720`.
   `analysis-committed/` now holds only the planted-sim gate artifacts.
3. Verified BEFORE relaunch, both ways: (i) `--mode real --synthetic-smoke
   --smoke` (workers=2, scratch out/work dirs) ran green end-to-end,
   39.1s, 24 records, correctly named
   `real_ladder_synthetic_smoke.{jsonl,json}`, correct SYNTHETIC-SMOKE
   marker. (ii) a standalone scratch-only probe script (never touching the
   pinned file, never calling `main()`, so no RunLog write) called
   `real_layer_cache("1.7b", [17])` directly: returned real safetensors
   activations (shape `(1, 1853, 2048)`), real row_keys (`triviaqa::...`,
   `popqa::...` -- not `synthetic::...`), and real class counts
   (1476 wrong / 377 correct, matching `rows.jsonl` exactly). Probe deleted
   after confirming pass; never added to the experiment directory.
4. `bin/exp repin correctness-geometry-scale-ladder scale_ladder_real.py
   --reason "build-defect remediation: ..."` -- new pin
   `24c5da158dc38ebf521e6c7ee822af1a6d483a553439d8fed76c21a6e619d10a`
   (was `c13e5792a668...`), recorded in `instrument.repins`. `bin/exp
   validate` clean (`OK (86 experiment(s))`).
5. Relaunched `scale_ladder_real.py --mode real --workers 8` via
   `bash experiments/common/launch_detached.sh` from the worktree root,
   writing a FRESH `analysis/runlog/real_ladder.jsonl` (the contaminated
   one was renamed out of the way in step 2, so nothing to resume from).
   Log path and PID reported to the lead at launch for their Monitor.

No G1 evaluation was run against the void run's numbers; `analysis-
committed/planted_sim_g_val.json` (the frozen G1 band source) was not
touched. Gate adjudication stays with the lead per the standing order.

### 2026-07-20 -- post-sign: real-label guard made status-aware, repinned, real run launched

PI approved sign-and-run (2026-07-20 EDT). Lead ran `bin/exp sign` on
`correctness-geometry-scale-ladder` (five files pinned: `cell.yaml`
65256247, `gates.yaml` 212c410a, `scale_ladder_lib.py` 95de0b43,
`scale_ladder_planted_sim.py` 94dc9425, `scale_ladder_real.py` 319249ae),
plus a cosmetic pre-sign fix quoting the `G_construction` `stop:` scalar in
`gates.yaml` (the colon-in-plain-scalar flagged in the prior G1-transcription
report) -- verified the local `gates.yaml` sha256 matched the pinned value
before doing anything else.

**Guard blocker, found and fixed:** launching
`scale_ladder_real.py --mode real --workers 8` (via
`bash experiments/common/launch_detached.sh`, invoked through `bash`
because the script's exec bit was missing -- a repo-housekeeping item the
lead is tracking separately, not touched here) immediately exited 1:

```
mode=real without --synthetic-smoke touches real per-row correctness
labels and is NOT authorized before bin/exp sign. This build is a
pre-sign deliverable; re-run with --synthetic-smoke for the drill,
or wait for the lead to lock G1 thresholds and sign the cell.
```

Root cause: this refusal was UNCONDITIONAL in the pinned file --
`if not args.synthetic_smoke: raise SystemExit(...)` never checked
`experiment.yaml`'s `status` field or any other sign-state signal. It fired
regardless of sign status; the docstring/error-message language implied
otherwise but nothing in the code implemented that distinction. No real
label was read during this blocked attempt (the guard fires before any
data loading).

Rather than patch the signed file unilaterally (its sha256 was pinned in
the just-signed manifest) or bypass it, reported the exact code location
and root cause to the lead and held. Lead's ruling: KEEP the safety
property (no real labels pre-sign), fix the defect (never re-checks sign
state) -- minimal-diff repin, not a fresh sign cycle. Implemented exactly
as authorized:

1. Replaced the unconditional `raise` with a manifest-status check: loads
   this experiment's own `experiment.yaml` via `yaml.safe_load` and
   proceeds iff `status` is `"signed"` or `"running"` (both valid states
   per `STATUSES` in `.agents/skills/experiments/scripts/exp.py`);
   otherwise raises the SAME refusal message, byte-for-byte. No env-var
   escape hatch, no CLI override flag -- the manifest is the single source
   of authorization, per the ruling. `--synthetic-smoke` behavior
   untouched. Nothing else in the file was touched (verified via a direct
   diff of the change -- one import line added, `import yaml`, plus the
   guard body).
2. Sanity-checked the new logic before repinning: (a) a copy of
   `experiment.yaml` with `status: draft` correctly evaluates
   `status not in ("signed", "running") == True` (still blocks); (b) a
   quick `--mode real --synthetic-smoke --smoke --workers 2` regression run
   completed cleanly in 43.5s, 24 records, `(SYNTHETIC-SMOKE -- no real
   labels touched)` -- confirms the smoke path is unaffected.
3. `bin/exp repin correctness-geometry-scale-ladder scale_ladder_real.py
   --reason "post-sign instrument plumbing: pre-sign real-label guard made
   status-aware (reads manifest status) instead of unconditional; no
   estimator, band, threshold, seed, or data-path change"` -- new pin
   `c13e5792a668139a0d14c7d86afd1ab8f5c3432827a9c49072908f7683cdb887`
   (was `319249ae91be...`), recorded in `instrument.repins` audit trail.
   `bin/exp validate` clean (`OK (86 experiment(s))`) after the repin.
4. Relaunched `scale_ladder_real.py --mode real --workers 8` via
   `bash experiments/common/launch_detached.sh` from the worktree root
   (log path and launch details reported to the lead at launch time for
   their Monitor).

### 2026-07-20 -- v3 rebuild: retire criterion (a), band-based (b-new), E1 primary (pre-sign; G_construction PASSES)

Lead adjudicated the v2 G_construction failure (below): the mathematical
tension it documented (criterion (a)'s decodability-insufficiency demand is
unsatisfiable by any mean-shift-type construction, LDA argument) is a
STRUCTURAL FINDING, not a code bug -- both the lead and a fresh designer
review concurred, and NO mixture-construction redesign was authorized (the
designer argued directly against it as a validity error: SO's real
committed target is itself nearly k=1-decodable while directionally
unstable, so a synthetic requiring k>1 decodability would validate against
the wrong signal class). Binding rulings (teammate message, full text also
in `scale_identifiability_design.md` sections 22-23): (1) retire criterion
(a); (2) E1 designated PRIMARY, E2/E3_k1/E4 descriptive companions,
all-three-scales rule NOT relaxed for the companions; (3) two instrument
fixes -- (i) E1 averaged over R_SH independent split-half draws (10-20
range, pick for <~30min wall at workers=8), (ii) re-run the diffuse
calibration search with more precision to narrow the 14B calibration-
procedure drift (0.165 calib vs 0.266 official mean in v2); (4) draft
AMENDMENT.md prediction/falsifier/middle-grounds wording narrowed to
"correctness-direction IDENTIFIABILITY sharpens with scale"; (5) index
machinery revisions (no clipping of c, per-scale-anchor normalization
affirmed, pin a trend test); (6) pre-stated 1.7B disposition (branch: full
pass vs stated limitation, never reverse-engineered); (7) wire full-n E1
primary into `scale_ladder_real.py`'s real-mode draw loop. Sequence:

1. **Read the v3 design packet sections 22-23 in full** (designer's concur/
   dissent + revised construction-validity/index machinery) and the lead's
   binding rulings (teammate message). Confirmed the designer's own
   verification of the LDA argument against the v2 run's own numbers (k1->kr
   rise -0.0005 to +0.0030 at every cell) before treating the retirement as
   settled.

2. **Added `lib.e1_split_half_reliability_avg`** (mean |cosine| over `R_SH`
   independent split-half draws, each keyed by an explicit sub-seed) as a
   thin wrapper around the unchanged single-draw `e1_split_half_reliability`
   primitive. Picked `R_SH=15` (within the lead-authorized [10,20] range)
   from a direct microbenchmark: single draw ~0.46s (1.7B full-n, ~1853
   rows) / ~0.18s (matched-n, ~754 rows); R_SH=15-averaged ~2.14s / ~1.84s
   (~4.6x / ~10.2x). Extrapolated official-run cost stayed under the ~30min
   budget at workers=8; confirmed by the actual official run (1612.9s /
   26.9min, see below).

3. **Rebuilt `check_construction_validity` for v3**: removed criterion
   (a)'s k-sweep-material-rise check entirely; added (a-new) monotone E1
   full-n degradation across the r-ladder {compact,r2,r4,r8} (reusing
   exactly the pattern the v2 run's own numbers already showed) and
   (b-new) a derived index-resolution ceiling `sigma_c(s) =
   (diffuse_hw_s/1.645)/gap_s <= R_max`, `R_max = Delta_min/(z*sqrt(2))`
   with `Delta_min=0.5, z=1.5` (the design packet's own recommended values,
   `CV_B_DELTA_MIN`/`CV_B_Z`/`CV_B_R_MAX` module constants, locked before
   the run) -- HARD at the powered pair (8B,14B); 1.7B recorded as a BRANCH
   (`full_pass` vs `stated_limitation`) that does not block `overall_pass`.
   Criterion (c) kept its structure but its pass/fail is now E1-specific
   (the sole primary), with the E1/E2/E3_k1 table still reported for
   transparency.

4. **Rebuilt `g_val_v2` to take `cv` as an argument**: E1's "reachable"
   limb now reuses `cv`'s (b-new) result directly (one source of truth,
   not two independently-tuned band checks replacing v2's hand-picked
   absolute-0.70 floor); E1's overall "pass" (what `designate_primary`
   reads) uses the powered-pair carve-out, reported alongside the
   unrelaxed all-three-scales reading for transparency. E2/E3_k1/E4 keep
   the UNCHANGED all-three-scales rule. `designate_primary`'s mechanism
   itself (fallback order E3_k1 -> E1 -> E2, E4 never primary) was left
   untouched -- it was designed to resolve mechanically, and doing so
   (rather than hand-coding "E1 wins") is what makes the eventual result a
   predicted mechanical outcome, not a hand-picked override.

5. **Raised diffuse-calibration search precision** (fix ii): official
   (non-smoke) `quick_reps` 2->5, `quick_calib_iters` 25->35, plus a new
   `quick_r_sh=3` (cheaper than the official R_SH=15, since this search's
   own numbers are never gated/reported, only used to pick (r,rho) --
   matching the existing "search is coarse, final point is full precision"
   convention). Verified via a direct timing test on one grid point:
   v3 settings (reps=5, iters=35, r_sh=3) took 39.05s vs an
   old-settings-with-worst-case-r_sh test at 16.30s -- confirmed the fix
   adds real cost, budgeted into the R_SH timing check above.

6. **Un-clipped `crystallization_index` docstring** (it was never actually
   clipped, section 22.6.1 corrects the design packet's own earlier
   "clipped" wording, not the code) and **added `trend_test`** (section
   22.6.3: monotonicity of c + endpoint contrast Delta_c vs propagated
   sigma_c, z accepted as a parameter so the lead's sign-time choice is the
   only place it is fixed) -- implemented, NOT evaluated (no real observed
   value exists pre-sign).

7. **Wired full-n E1 primary into `scale_ladder_real.py`'s real-mode draw
   loop** (item 7): `fit_one_draw` now fits a SEPARATE full-rank PCA-128 on
   the FULL per-layer real population (not the matched-n subsample) and
   reports `e1_full_n` there as primary, matching the planted sim's own
   convention; the matched-n reading is retained as `e1_matched_n`
   (secondary, ruling 21.2 unchanged). This closes the v2 build's flagged
   gap.

8. **Smoke suite, all four drills + one regression check, all pass**
   (mirroring the v1/v2 convention):
   - Synthetic end-to-end (`--smoke --workers 8 --fresh`): 164.9s,
     `construction_validity.overall_pass=True` (a/b_powered/b_1.7b=full_pass/c
     all true), `G_val`: E1=True, E2/E3_k1=False, E4=True, primary=E1.
   - Workers 1 vs 8 equivalence: byte-identical JSON excluding
     `wall_clock_s` (workers=1 took 413.7s, ~2.5x slower, confirmed via a
     direct Python dict comparison after popping `wall_clock_s` from both).
   - Kill-resume: launched via `launch_detached.sh`, hard-killed via
     `kill -9 -$PID` after 2 of 15 batches (confirmed no `.exit_code`
     sidecar -> genuine hard kill), relaunched without `--fresh` (correctly
     skipped 6/45 already-done reps, 147.6s to finish), final output
     byte-identical to the uninterrupted workers=8 baseline (excluding
     `wall_clock_s`).
   - Regression check on `scale_ladder_real.py`: `--mode g0` still PASS
     (unchanged); `--mode real --synthetic-smoke --smoke` completes in
     30.9s (up from 12.7s pre-v3, expected -- now fits full-n PCA + R_SH=15
     E1 draws per task) with `e1_full_n`/`e1_matched_n` both populated with
     sane, distinct values (spot-checked three records).

9. **Official run** (`--workers 8 --fresh`, R_SIM=30, all three scales, no
   `--smoke`): launched via `launch_detached.sh` (projected wall exceeded
   15 min). Diffuse calibration took ~13.5 min (25-point grid x 3 scales,
   raised precision per fix (ii)); main reps took the rest. **Total wall:
   1612.9s (26.9 min) at workers=8** -- under the ~30 min budget the lead
   set for picking R_SH.
   - **G_construction v3: overall_pass = TRUE.** a=true (monotone E1
     r-ladder at all 3 scales, tolerances 0.041-0.056). b_pass_powered=true
     AND b_1p7b_pass=true, branch=**full_pass** (not merely the weaker
     stated_limitation fallback the design packet's own section 22.7
     predicted as most likely) -- sigma_c: 1.7B=0.1108, 8B=0.1326,
     14B=0.1078, all well under R_max=0.2357. c=true (E1 separation 0.41-
     0.51 vs half-width 0.05-0.07 at every scale). Attributed to fix (i)
     (R_SH=15 averaging) tightening `diffuse_hw` exactly as section 22.7
     anticipated it most likely would.
   - **G_val (now actionable): E1 PASSES** at all three scales, both via
     the powered-pair carve-out and outright at 1.7B. E2 fails overall
     (passes 1.7B/14B individually, not 8B: diff=0.029 vs hw=0.069). E3_k1
     fails everywhere (diff 0.003-0.006 vs hw 0.033-0.037, flat by design
     per its support-breadth framing, section 22.5). E4 passes all three
     scales this run (diffuse PR clearly above compact everywhere) but
     remains never primary-eligible.
   - **Primary designation: E1** (`m4_prime=false`) -- the unchanged
     fallback order (E3_k1 -> E1 -> E2) resolves to E1 mechanically because
     E3_k1 still fails separation, exactly as predicted rather than
     hand-picked.
   - **Diffuse-calibration drift (fix ii) narrowed but not eliminated**:
     search-estimate vs official-achieved E1_full_n means -- 1.7B 0.1738 vs
     0.1845 (diff 0.011); 8B 0.1799 vs 0.1769 (diff 0.003); 14B 0.1654 vs
     0.2013 (diff 0.036, the worst case, down from v2's 0.101 at 14B but
     not zero). Reported as a residual calibration-procedure imprecision,
     not chased further post-hoc.

10. **Post-run bookkeeping**: staged the official RunLog
    (`analysis/runlog/planted_sim.jsonl{,.meta.json,.summary.json}`) to
    `/home/profsynapse/code/ehr-exhaust/correctness-geometry-scale-ladder/runlog/`;
    updated `cell.yaml`/`gates.yaml`/`AMENDMENT.md` to v3 (draft; v1/v2
    records retained inline for provenance, not deleted); ran
    `bin/exp validate` and a containment grep before reporting.

**Consequence**: construction-validity v3 passes and E1 clears G_val --
this is the FIRST time this cell's instrument has cleared its own
pre-outcome gates. G1 thresholds are still NOT locked (an explicit lead
action: "I review G_val, lock G1 thresholds, and only then does sign/
real-label authorization happen"). No real per-row correctness label has
been read by any script in this experiment.

**Cost actuals (v3):** official run 1612.9s / 26.9min at workers=8
(diffuse calibration ~13.5min + main reps ~13.4min). Smoke: 164.9s
(workers=8) / 413.7s (workers=1). Kill-resume resume-leg: 147.6s.
scale_ladder_real.py synthetic-smoke: 30.9s (up from 12.7s pre-v3).

### 2026-07-20 -- v2 rebuild: construction-validity gate + G_val v2 (pre-sign; NEW STOP GATE hit)

Lead adjudicated the v1 G_val failure (below) as a pre-registration
instrument-iteration loop, not a resolve-as-null, and authorized a v2
rebuild per design packet sections 13-21 + lead adjudication section 21.
Sequence:

1. **Read the v2 design packet in full** (sections 13-21) plus the lead's
   binding rulings in section 21: diffuse calibration anchored to CD 0.174 /
   SO ~0.04 with split-half priority (21.1); E1 swaps to full-n primary
   (21.2); E4 gate-optional, never primary (21.3); construction-validity as
   a HARD BLOCKING STOP (21.4); primary fallback order E3_k1 -> E1 -> E2,
   E4 never primary, M4-prime if none of E1/E2/E3 pass (21.5).

2. **Rebuilt `scale_ladder_lib.py`**: removed v1's mean-shift generator
   entirely (not kept as a dead code path); added
   `synthetic_redundant_features` (correlated-redundant flat-Rashomon,
   equicorrelated block covariance); rebuilt `e1_split_half_reliability`
   (per-half full-rank PCA refit, SO's convention); rebuilt
   `e2_concentration_ratio` (nested best-single-axis, replacing the
   tautological joint-normal-as-top-1); rebuilt `e4_participation_ratio`
   (label-permutation null subtraction, P=100, via a new vectorized
   rank-based per-column AUROC helper `_column_aurocs` -- verified against
   `sklearn.roc_auc_score` column-by-column, max abs diff 1.1e-16, before
   wiring it in); `e3_random_slice_margin`/`restricted_cv_auroc` left
   UNCHANGED per the packet ("implementation unchanged"). Added
   `diffuse_grid_point`/`diffuse_grid_points`/`pick_best_diffuse_candidate`
   for the diffuse-calibration search (dispatched through `parallel_map` by
   the caller, keeping lib.py free of its own parallel dispatch, matching
   the existing lib/orchestration split).

3. **Calibration-ceiling bug found and fixed during build** (same spirit as
   v1's axis-alignment fix -- discovered via direct correctness testing
   before the official run, not after seeing a failing gate). The
   generator's strength-bisection used a fixed ceiling (hi=8.0, inherited
   from v1); at high (r, rho) the equicorrelated block's Mahalanobis
   distance for a fixed raw shift magnitude is
   `strength^2 * r / (1 + (r-1)*rho)`, which SHRINKS toward a constant as
   rho -> 1 (r correlated copies carry no more Mahalanobis information than
   one, by design -- the redundancy property this generator is meant to
   encode). A fixed ceiling adequate for low rho silently undershot the
   target AUROC for high (r, rho): e.g. r=64, rho=0.85 at target 0.82
   converged to only 0.707 before the fix. Fixed by geometrically expanding
   the ceiling (doubling, capped at 20 doublings) until it clears the
   target before bisecting -- confirmed by direct test this restores exact
   target-AUROC calibration across the full (r, rho) grid. This is an
   implementation-robustness fix to meet the calibration's own stated
   contract ("match target_auroc"), not a tuning pass; no gate threshold
   was touched.

4. **Exploratory correctness-testing surfaced the decisive construction
   finding, BEFORE the official run** (again, same spirit as the v1
   axis-alignment fix: build-time diagnostic testing, not post-hoc
   goalpost-chasing). A direct rho-sweep at r=8 (rho in
   {0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.85, 0.95}, matched-n and full-n) showed
   the k=1-vs-k=8 deflation AUROC gap stays at essentially ZERO across the
   ENTIRE rho range (-0.0009 to +0.0029, no clean trend, consistent with CV
   noise) while E1 full-n reliability clearly DOES degrade with rho at
   fixed r (0.627 at rho=0 down to 0.122-0.331 at rho>=0.5, non-monotone in
   this coarse single-rep sweep but the multi-rep official run below shows
   a clean monotone pattern with r at fixed rho=0.7). This confirmed BEFORE
   spending the R_SIM=30 CPU budget that construction-validity criterion
   (a) -- "k=1 insufficient for r>1" -- would fail deterministically: ANY
   two-class Gaussian mean-shift model has a Bayes-optimal rank-1 decision
   boundary (LDA argument: argmax_w w^T*mu/sqrt(w^T*Sigma*w) is achieved by
   w proportional to Sigma^-1*mu, always a single vector), REGARDLESS of
   Sigma's structure. The covariance-correlation fix (which DOES solve
   identifiability -- see step 6) is mathematically orthogonal to, and
   cannot also satisfy, criterion (a)'s decodability-insufficiency demand.
   Decision: proceed to run the OFFICIAL full-scale pipeline anyway (per
   the lead's explicit instruction, and because it produces the real
   precision-tracked artifact plus the official diffuse-calibration numbers
   the lead needs), fully expecting and prepared to report a
   construction-rejected hard stop -- not "proceeding past a stop to see
   what happens" (nothing has been signed, no real label touched, and this
   is the SAME build-time-diagnostic-then-official-run sequence the v1
   axis-alignment fix followed).

5. **Rebuilt `scale_ladder_planted_sim.py`** end to end: per-scale diffuse
   (r, rho) calibration (parallelized grid search over
   `lib.diffuse_grid_points()`); five resolved conditions per scale
   (compact r=1, r-ladder {r2,r4,r8} at fixed RHO_LADDER=0.7, calibrated
   diffuse); per-rep computation of E1 at both full-n (primary) and
   matched-n (secondary, via stratified subsample of the SAME full-n draw),
   E2/E3_k1/E4 at matched-n, and the construction-validity k-sweep (k=1,2,4,8
   via `restricted_cv_auroc`); aggregation; `check_construction_validity`
   (criteria a/b/c, section 14); `g_val_v2` (band-based separation/
   monotonicity/reachability, section 16, computed regardless of the
   construction-validity outcome for transparency); `designate_primary`
   (section 21.5 fallback order); `two_anchor_bands` (section 17) and
   `crystallization_index` (implemented as a pure function -- not evaluated
   here, since this module never reads a real observed value). RunLog
   persistence at `analysis/runlog/planted_sim{,_smoke}.jsonl` carried
   forward unchanged (module version bumped to 2 in its run_config).

6. **Smoke suite, all four required drills, all PASS** (reduced-cost smoke
   variant of the diffuse-calibration grid used ONLY in `--smoke` mode --
   2 grid points instead of 25, 1 quick rep instead of 2 -- to keep the
   smoke drill fast; this touches no reported/gated number, only which
   (r, rho) the smoke run happens to exercise end to end):
   - Synthetic end-to-end smoke: `scale_ladder_planted_sim.py --smoke
     --fresh --workers 8` completed in 147.9-148.3s, construction-validity
     already correctly evaluated as FAIL (a=False, b=False, c=True) at
     smoke scale (3 reps/condition) -- confirming the code path exercises
     the intended failure mode, not a smoke-only artifact.
   - Workers-equivalence: `--workers 1` (396.7s) vs `--workers 8` (148.3s),
     both smoke scale -- JSON outputs byte-identical excluding
     `wall_clock_s` (`a == b` verified directly in Python, not by eyeball
     diff).
   - Kill-resume drill: launched via `experiments/common/launch_detached.sh`
     at `--workers 4`, waited for the RunLog to show >= 1 checkpointed batch
     (3 lines, one condition's worth of smoke reps), confirmed liveness via
     `kill -0`, then `kill -9 -$PID` (whole process group -- confirmed via
     `ps -o pid,pgid` that the launched process was its own group leader);
     confirmed NO `.exit_code` sidecar was written (genuine hard kill, not
     a graceful exit); relaunched the IDENTICAL command WITHOUT `--fresh`,
     which correctly reported "45 total reps, 39 pending" (skipped the 6
     already-recorded items via `RunLog.iter_pending`); the resumed run's
     final JSON output was byte-identical (excluding `wall_clock_s`) to the
     uninterrupted `--workers 8` baseline.
   - Regression check on `scale_ladder_real.py` (untouched by the v2
     rebuild): `--mode g0` still PASSes against the rebuilt lib.py, and
     `--mode real --synthetic-smoke --smoke` still completes cleanly
     (12.7s, 24 records) -- its E1/E2/E4 call sites are signature-compatible
     with the v2 internals, so it transparently picks up the rebuilt
     estimators without any edits to that file.
   - Pre-flight correctness check (not one of the four formal drills, but
     load-bearing before trusting E2/E4's new vectorized AUROC path): the
     new `_column_aurocs` rank-based per-column AUROC helper was verified
     against `sklearn.roc_auc_score` computed column-by-column on random
     test data -- max absolute difference 1.1102230246251565e-16 (float
     round-off floor).

7. **G_construction + G_val v2, full scale (R_SIM=30, all three scales),
   2026-07-20, 851.7s wall at 8 workers** (launched via
   `launch_detached.sh` per the >15-min-wall-clock rule; the shared
   scratchpad log file had unrelated interleaved output from a concurrent
   process using the same generic filename -- a monitoring nuisance only,
   filtered by grepping for this module's own `[planted-sim` prefix; the
   RunLog and JSON/md outputs, written to this experiment's own paths, were
   never touched by that collision). Command:
   `python3 scale_ladder_planted_sim.py --fresh --workers 8`. Output:
   `analysis-committed/planted_sim_g_val.{json,md}`.

   **Diffuse calibration achieved** (priority 1 = E1 full-n vs CD's 0.174;
   priority 2 = E3_k1 margin vs SO's ~0.04, tiebreak only, per lead ruling
   21.1): 1.7B r=8/rho=0.95 (E1=0.1745, E3=0.287); 8B r=16/rho=0.5
   (E1=0.184, E3=0.363); 14B r=8/rho=0.7 (E1=0.165, E3=0.284). Priority-1
   matched within 0.01 at every scale; priority-2 not closely matched
   anywhere, recorded as the ruling requires.

   **Result: G_construction FAILS** (criteria a and b fail; c passes) --
   see AMENDMENT.md Outcome for the complete criterion-by-criterion numbers
   and the LDA-argument root-cause derivation (any two-class Gaussian
   mean-shift model has a Bayes-optimal rank-1 boundary regardless of
   covariance structure, so criterion (a) cannot be satisfied by this or
   any single-mean-shift-type construction; identifiability and
   decodability-insufficiency are in tension for such constructions).
   Genuine positive result despite the stop: full-n E1 reliability degrades
   CLEANLY and MONOTONICALLY with r at fixed rho=0.7 across all three
   scales (compact 0.58-0.69 -> r8 0.18-0.24) -- v1 never produced this
   (its rank1-vs-diffuse E1 was flat/inverted, 0.40-0.48 regardless of
   rank). The covariance-block fix DOES solve identifiability; it just
   cannot simultaneously satisfy construction-validity criterion (a).

   **G_val v2 numbers, computed for transparency (NOT actionable per lead
   ruling 21.4):** E1 fails all 3 scales (separated+monotone, never
   reaches the 0.70 full-n floor: 0.581/0.687/0.675). E2 and E4 EACH pass
   individually at 8B and 14B but fail at 1.7B (E2: ratio diff 0.26/0.13 at
   8B/14B vs 0.014 at 1.7B; E4: PR diff 11.2/3.7 at 8B/14B vs 2.0 at 1.7B).
   E3_k1 fails at every scale (compact vs diffuse margins nearly identical,
   0.28-0.36 range everywhere) -- traced to the same structural fact as
   criterion (a): with target AUROC fixed by calibration, k=1 already
   recovers essentially all of it regardless of (r,rho). No estimator
   designated primary (`m4_prime=true` per section 21.5's fallback order),
   moot regardless since G_construction is the operative hard stop.

8. **RunLog + provenance staged to the durable exhaust dir**
   (`/home/profsynapse/code/ehr-exhaust/correctness-geometry-scale-ladder/`)
   before this report, per the mechinterp-cells SKILL.md pre-teardown
   staging rule -- no worktree teardown has happened or is imminent, but
   staging now keeps the durable copy current with the v2 run.

9. **Consequence: NEW STOP GATE, one level upstream of v1's.** Per lead
   ruling 21.4, G_construction is a hard blocking stop: no G_val criterion
   may be locked or read as actionable while it fails. No real per-row
   correctness label has been read by any script in this experiment.
   Harness build stops here again; see AMENDMENT.md Outcome and the
   harness-builder's structured report to the lead for the full adjudication
   questions.

Timed cost note (v2, supersedes the packet's own section-19 estimate and
v1's own NOTEBOOK cost note): the FULL v2 planted-sim run (5 conditions x 3
scales x R_SIM=30 = 450 synthetic replicates, each computing full-n E1,
matched-n E1/E2/E3_k1/E4, and a 4-point k-sweep, PLUS the diffuse-calibration
grid search: 25 (r,rho) points x 2 quick reps x 3 scales) took 851.7s
(14.2 min) wall at 8 workers on this 16-core box -- comfortably under the
packet's revised "<1 hour at --workers 8" estimate and well under the
original "<8 CPU-hr" ceiling. The smoke-scale proxy (3 reps/condition, 2
diffuse-calibration grid points) took 147.9-148.3s at 8 workers and 396.7s
at 1 worker (workers=1 wall / workers=8 wall ~= 2.7x, less than the ideal
8x -- most of the calibration-search phase runs with limited parallelism
when the grid is tiny, e.g. only 2 grid points means at most 2 workers are
ever busy during the smoke variant's calibration phase; the official run's
full 25-point grid uses all 8 workers during calibration too). The real-
label ladder was never run (blocked upstream by G_construction, as it was
by v1's G_val); `scale_ladder_real.py`'s synthetic-smoke proxy (24 draws,
both layer policies, 3 scales) still completes in 12.7s, unaffected by the
v2 rebuild.

### 2026-07-20 -- v1 harness build + G_val run (pre-sign; STOP GATE hit; SUPERSEDED by the v2 rebuild above, retained for provenance)

Built from the design packet + lead adjudication (see AMENDMENT.md). Sequence:

1. **G0 (data adequacy).** `scale_ladder_real.py --mode g0`: all three
   Amendment X manifests match the packet's n_layers/hidden_dim table; all
   three `rows.jsonl` per-class counts match exactly (1.7B 377/1476, 8B
   648/1205, 14B 741/1112); row_key pool intersection across all three
   scales = 3000/3000 (identical pool); matched-n floor N*=377/377
   achievable at every scale. PASS. No tensors read at this step.

2. **Generative-model bug found and fixed before running G_val for real.**
   An initial version of `synthetic_planted_features` used a RANDOMLY-
   ROTATED shift direction for finite rank r (a random r-dim subspace of
   the 128-dim PCA space, arbitrary orientation). Direct test
   (`python3 -c` snippets, not committed) showed this made E4
   (participation ratio) blind to rank entirely: PR ~80-99 for every rank
   from 1 through diffuse, because a randomly-oriented direction generically
   loads on most of the 128 raw PCA axes by geometric chance regardless of
   true rank. Fixed by making finite-rank shifts AXIS-ALIGNED (r randomly-
   chosen raw PCA axes, equal weight, no rotation) -- confirmed by direct
   test this is a genuine improvement for E4 (diffuse PR now clearly
   separated from finite-rank PR) and provably makes no difference to
   E1/E3 (both rotation-invariant under isotropic background noise). This
   was a bug fix to make an estimator test what it was supposed to test at
   all, not a tuning pass to force a gate to pass -- no gate threshold was
   touched. See `cell.yaml` `planted_signal_generator.rank_construction`.

3. **Smoke suite, all four required drills, all PASS:**
   - Synthetic end-to-end smoke: both `scale_ladder_planted_sim.py --smoke`
     and `scale_ladder_real.py --mode real --synthetic-smoke --smoke` run
     to completion cleanly.
   - Workers-equivalence: `--workers 1` vs `--workers 4`, both modules,
     smoke scale -- JSON outputs byte-identical excluding `wall_clock_s`.
   - Kill-resume drill, both modules: launched via
     `experiments/common/launch_detached.sh`, waited for >=1 checkpointed
     batch (confirmed via the RunLog JSONL, not a process-alive check),
     `kill -9 -$PID` (whole process group; confirmed no `.exit_code`
     sidecar was written, i.e. a genuine mid-run hard kill, not a graceful
     exit), relaunched the identical command WITHOUT `--fresh`. Both
     resumed from the checkpoint (skipped already-done keys via
     `RunLog.iter_pending`) and both final outputs were byte-identical
     (excluding `wall_clock_s`) to an uninterrupted baseline run over the
     same config.
   - G_val planted-signal validation harness: see below.

4. **G_val, full scale (R_SIM=30, not smoke), 2026-07-20, 246.9s wall at
   8 workers.** Command:
   `python3 scale_ladder_planted_sim.py --fresh --workers 8`. Output:
   `analysis-committed/planted_sim_g_val.{json,md}`.

   **Result: FAIL for all four estimators, all three scales.**
   - E1: rank1 reliability 0.400-0.442 across scales (need >=0.70); diffuse
     reliability 0.418-0.476 -- NOT clearly below rank1 (in one scale,
     marginally higher). Rank-1 and diffuse are indistinguishable.
   - E2: ratio 0.997-1.013 for EVERY rank including diffuse, at every
     scale -- essentially exactly 1 regardless of true rank. Traced to a
     structural property, not sample size: "AUROC_full" (linear logistic on
     all 128 PCA dims) and "the top-1 discriminative direction" (that SAME
     fitted logistic's own normal) are, up to an AUROC-invariant positive
     scale and additive constant, the same decision function for any
     linearly-decodable signal -- E2 as specified cannot differentiate rank
     from diffuseness for a mean-shift generative model at any n.
   - E3_k1: margin 0.312-0.359 for rank1 AND 0.315-0.359 for diffuse --
     essentially identical. Related structural cause: a mean-shift signal is
     Bayes-optimal-linear-rank-1 regardless of how "spread" its construction
     is, so a well-fit direction beats a genuinely random direction by a
     similar margin under either label.
   - E4: recovered PR 37.9-53.2 across true ranks 1/2/4/8 (want within +/-1)
     -- fails the literal criterion by a wide margin, but shows a genuine
     weak monotone increase with true rank and clean separation of diffuse
     (94.4-99.3) from every finite rank. Traced to finite-sample noise: ~127
     of 128 PCA axes carry no true signal but each contributes a small
     nonzero univariate AUROC by chance at n=188 held-out per class, and
     their summed contribution dominates the true-signal axis/axes' share
     of the participation-ratio formula.

   Pooled per-scale diffuse-rank planted-band half-widths (for reference,
   not actionable while G_val fails): E1 reliability 0.0746, E2 ratio
   0.0445, E3_k1 margin 0.0227, E4 PR 5.09.

5. **Consequence: STOP GATE.** Per the mechinterp-cells SKILL.md binding
   invariant, G_val "MUST pass before any real-data gate is read," and a
   failing estimator "is dropped from the gate and reported descriptive-
   only." With E1, E2, AND E3_k1 (the three estimators lead adjudication
   point 6 permits on the gate) all failing, G1's stated conjunction has no
   surviving instrument. No real per-row correctness label has been read by
   any script in this experiment. Build stops here; see AMENDMENT.md
   Outcome and the harness-builder's structured report to the lead for the
   full file inventory and adjudication questions.

Timed cost note (for the AMENDMENT.md cost projection, superseding the
packet's own estimate): the ACTUAL G_val run (5 ranks x 3 scales x R_SIM=30
= 450 synthetic replicates, each computing E1+E2+E3_k1+E4) took 246.9s wall
at 8 workers on this box (16 cores). The real-label ladder was never run
(blocked by G_val), so no timed cost exists for it; the synthetic-smoke
proxy (24 draws, both layer policies, 3 scales, toy R_DRAWS=4) took 26.2s at
1 worker, which scales roughly linearly with R_DRAWS/workers and gives no
reason to expect the full real-ladder run (packet's own R_DRAWS=30 across
2 layers + a 5-layer window + robustness, per scale) to exceed the
packet's original <8 CPU-hr / <30 min-wall-clock-at-8-workers estimate --
but this is now moot pending the G_val disposition.
