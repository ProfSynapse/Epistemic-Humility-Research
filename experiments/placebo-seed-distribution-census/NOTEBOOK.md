# Placebo seed-distribution census: multi-seed random-direction null at matched magnitude notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-14 (lead): harness accepted, SC1 tolerance corrected pre-run (user-approved), sweep authorized

Harness-builder delivered 23 modules (41 CPU tests passing) and correctly
HARD-STOPPED at the SC1 readback gate: qwen and llama missed the signed
absolute 0.01 tolerance on all 16 smoke rows each (mean +0.0177 / -0.0151),
mistral passed (+0.0059). Lead re-derived the deviations independently from
the committed smoke JSONs: the offset is uniform in RELATIVE terms across all
three families (0.111-0.160% of setpoint), mistral cleared the absolute bar
only because its setpoint is small, and the certified qwen precedent (signflip
AMENDMENT: readback 12.625 vs target 12.608 = 0.14% relative) shows the same
regime, meaning the harness reproduces the certified operating points
faithfully and the signed bar was mis-derived (it conflated RR3's arm-to-arm
setpoint-identity margin 0.004 with readback-vs-target accuracy and
contradicted the qwen precedent cited in its own sentence). PI approved the
governed correction before any dosed generation: SC1 readback tolerance
absolute 0.01 -> relative 0.005; llama baseline pointer corrected to RR3
rider_llama__baseline.jsonl (the drafted RR llama baseline never existed on
disk; substitution verified against the staged 1206-row file = 872 confab +
334 known); cell.yaml unquoted-colon YAML fix. All recorded in
instrument.repins (5 files). Falsifier, criterion, seeds, and setpoints
untouched. Post-correction: 42/42 CPU tests pass; all 48 recorded GPU smoke
readbacks pass the corrected bar through the corrected sc1_checks code path
(max 0.185% vs 0.5% ceiling). Two straight-reported instrument notes: the
joint randomness bar rejects ~50-70% of draws by cosine geometry (redraw
budget 300 covers it), and bf16 batching diverges textually on 1-3 of 8 rows
between batch sizes, handled by pinning one fixed batch size for every dosed
pass. Full K=15 x S=300 x 3-family sweep authorized on the free local 3090
(standing approval noted at go); estimated ~2.4 h generation.

### 2026-07-14 (lead): draft reviewed, knobs resolved with PI, signed

Lead spot-checked the drafter's operating-point pins against the governed docs
directly (qwen dose_abs 12.608 against the signflip committed report's M3
dose_abs; mistral 3.665/hs16 against RR3 cell.yaml; llama hs20 / held-out
confab 872 / RG0 byte-identical fit reconstruction against RR3 cell.yaml lines
145-166) before accepting. PI decisions, registered in this conversation before
sign: (1) RR3's three mistral seeds do NOT count toward K ("new experiment,
new seeds"); all 15 mistral census seeds run fresh, the RR3 points reported as
external full-pool corroboration. (2) All drafted defaults confirmed: K = 15,
S = 300, subsample-only generation, baseline text reused byte-identical with
grade produced fresh in the census pool, qwen magnitude = absolute setpoint
12.608. (3) Scoreboard calls registered pre-run, PI explicitly agreeing with
the orchestrator's calls (qwen SURVIVES, mistral RETIRED, llama near-zero
null, historical percentile ranges as tabled); both predictors carry the same
calls, which binds them both against the result. Signed via bin/exp sign.
Next: harness build (SC0 staging, subsample draw and commit, SC1
setpoint/randomness checks, generation runner, blinded grading lane), then
free-lane 3090 generation (standing local-3090 approval noted at go).

### 2026-07-14 (drafter): initial AMENDMENT / cell.yaml / gates.yaml draft

Drafted the full amendment for the placebo seed-distribution census in a
worktree, for lead review. Not signed, no git, no `bin/exp sign`. Read the four
governed docs this session before drafting: RR3
(`rr3-corrected-placebo-replication` AMENDMENT), the wide-instrument calibration
(`abstention-wide-instrument-calibration` AMENDMENT), the placebo sign-flip
(`placebo-signflip-question-type-analysis` AMENDMENT), and
`papers/paper-5-actuation/manuscript.md` sections 4.9 / 6 / 6.5. Also read the
signflip and RR3 cell.yaml/gates.yaml for structure and the abstention-grading
reference.

What the design measures: per family, the DISTRIBUTION of matched-magnitude
random-direction wide-instrument abstention deltas across K fresh seeds, so
future placebo comparisons register against a measured null distribution instead
of the single-seed points (qwen -5.13, mistral +7.39) that RR3 showed are one
draw from a wide (-7.4 .. +21.8) distribution. Behavioral only; no mechanism /
anchor leg. No promotion gate (measurement census like the calibration).

Operating points pinned from the docs:
- qwen35-4b: hs20, setpoint dose_abs 12.608, paired confab pool 1,286,
  historical -5.13 (suppression). Sigma_c multiplier NOT asserted (no doc read
  gives one for the QH promoted point); census matches the absolute setpoint.
- mistral7b-v03: hs16 (decoder block 15), dose 12 sigma_c = dose_abs 3.665,
  paired confab pool 1,312, historical +7.39 (recruitment). RR3's three seeds
  (30260714/15/16, lifts +13.3 / -7.4 / +21.8) are existing matched-magnitude
  draws on this exact point.
- llama32-3b: hs20, dose 12 sigma_c reference; setpoint dose_abs NOT in any doc
  read (must re-derive sigma_c(hs20 llama) byte-identical from RR's committed
  llama hs20 fit manifest at build); held-out confab 872; historical +0.1 (null,
  RR3 rider). llama has no committed non-null sign, so it is treated as a
  built-in null / negative control, not a sign to defend.

Falsifier drafted numerically and pre-committed (see AMENDMENT / gates
sc_criterion): per family with committed sign s, SURVIVES iff f_s >= 0.80 AND
bootstrap LCB(f_s) > 0.50 AND |median| >= 3.0 pts in the s direction; RETIRED iff
f_s <= 0.60 OR the interquartile range of the signed delta spans zero;
INDETERMINATE otherwise. Amendment prediction: qwen SURVIVES, mistral RETIRED
(RR3's 2-of-3-positive spread already implies f_pos < 0.80), llama null. Genuinely
risky for mistral.

Proposals: K = 15 fresh seeds per family (12/15 = 0.80 sign-fraction with Wilson
LCB > 0.50; K = 10 cannot clear the bar); fixed per-seed subsample S = 300 confab
rows per family, same rows across baseline and all K dosed seeds, permutation
seed 40260714, committed before generation; generation confined to the S rows
(baseline reused from disk) for ~3.25 free-lane GPU-hours total.

Decision knobs flagged for the lead (all marked TO-CONFIRM / TO-DERIVE /
TO-DECIDE / TO-REGISTER in the files):
1. qwen census magnitude: confirm 12.608 is the intended setpoint (no sigma_c
   multiplier pinned).
2. llama setpoint dose_abs: TO-DERIVE from RR's llama hs20 fit manifest at build;
   llama directions_dir TO-PIN.
3. Whether RR3's three mistral seeds count toward K (argued both ways in the
   AMENDMENT). If counted, recompute their deltas on the census S rows from RR3
   persisted row-level grades and run 12 new mistral seeds (K=15 total);
   if not, run 15 new and report the three as external full-pool points.
4. K per family (default 15; 10-20 band).
5. Subsample S per family (default 300; 500 tightens per-seed CI, 200 saves cost).
6. Generation scope: subsample-only (recommended, cheap) vs full-pool (3-4x GPU,
   preserves grading expandability).
7. Baseline grade source: fresh-in-census-pool (default) vs reuse committed
   calibration/RR2 baseline grades (cheaper, mixes lanes).
8. Exact 45 seed values (proposed consecutive per-family blocks; TO-CONFIRM).
9. synaptic_tuner_pin and directions provenance TO-PIN at harness build.
10. Predictor scoreboard CALLS: TO-REGISTER by lead and PI pre-run.

One doc-vs-prompt tension recorded: the prompt frames all three families as
having a sign to defend, but the governed docs record llama's single placebo
point as null (+0.1 at dose 12), so llama is drafted as the null-control family
rather than a third sign. All quantitative priors otherwise matched the prompt
(mistral -7.4 .. +21.8 spread, qwen -5.13, mistral +7.39).
