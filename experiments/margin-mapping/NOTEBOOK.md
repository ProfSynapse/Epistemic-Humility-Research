# Margin mapping: per-row tipping dose along the known-unknown direction notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-16 -- Harness build + mandatory GPU preflight: PREFLIGHT FAILED (both families), no full run launched

Built the M1 harness under `harness/` (config.py, common.py, grader.py,
detector_v2.py/detector_v2_patterns.yaml, gen_lib.py, render.py, steer_lib.py,
row_pool.py, sc1_checks.py, dose_ladder.py, staging.py, subsample.py,
run_margin.py, test_margin_smoke.py), reusing the gate-contribution-factorial
harness lineage (steer_lib/render/gen_lib/detector stack read in full and
either copied byte-identically or logic-ported with only the namespaced
render env vars changed: `MARGIN_RENDER_MODEL`/`MARGIN_RENDER_REVISION`
instead of `GATEFACT_RENDER_MODEL`/`GATEFACT_RENDER_REVISION`). Initialized
the `synaptic-tuner` submodule in this worktree (was uninitialized) via
`git submodule update --init --reference <main repo>/synaptic-tuner`.

**Known cell.yaml anomaly (documented, not touched):** line 89 (the
`disagreement_gate` prose value under `readout.calibration_slice`) contains
an unquoted `remedy: ...` colon that breaks `yaml.safe_load` with a
`ParserError`. Confirmed present in the byte-identical, hash-pinned copy
(sha256 matches `experiment.yaml`'s pin exactly), so this is a genuine
authoring bug that was signed in, not staleness. `config.py`
`_load_cell_yaml_permissive()` works around it by quoting that one line's
value IN MEMORY ONLY before parsing; the on-disk file was never edited.
`gates.yaml` parses cleanly.

**SC0 staging:** all 6 reused artifacts (qwen baseline runlog, qwen question
pool, mistral baseline runlog, mistral question pool, mistral hs16 c_hat,
qwen hs20 c_hat) staged and sha256-verified byte-identical against the
factorial's own committed `staging_manifest.json` (hard-fail assertion in
code, `staging.py`). Detector stack (`detector_v2.py`,
`detector_v2_patterns.yaml`, `grader.py`) copied byte-identically from the
factorial and live-reverified. RG0 byte-repro passed for both families'
baseline runlogs.

**SC0 subsample:** confab subsample n=400/family drawn with the registered
seed 48260714 (distinct from the factorial's own 46260714), plus the full
known pool (360 qwen / 382 mistral) committed as opaque row_key lists to
`analysis-committed/subsample_ids_<family>.json`. Deterministic under the
fixed seed (smoke-tested).

**CPU smoke suite:** 29/29 passed
(`/home/profsynapse/miniconda3/bin/python3 -m pytest test_margin_smoke.py -v`),
covering config/YAML pin verification (including the line-89 workaround),
dose-ladder computation against the cell.yaml reference doses, sigma/gain
non-conflation at every rung (same defect class the factorial fixed
2026-07-16), subsample determinism, SC0 staging hash-assertion logic, and
RunLog resume-from-checkpoint behavior.

**GPU preflight (SC1, mandatory, PI standing directive 2026-07-16): FAILED
for BOTH families.** 4 rows (same rows across all 4 rung-points -- a
build-time interpretation, not a spec value) dosed at each of 0.0625x, 1.0x,
3.0x, 4.0x. Identical failure shape in both families: at the BOTTOM rung
(0.0625x) exactly 1 of 4 dosed rows misses the relative-0.005 readback
tolerance (qwen: row `kuq_unknowns_all:1039`, rel_delta 0.006773; mistral:
row `kuq_unknowns_all:1018`, rel_delta 0.006601 -- both roughly 33-36% over
the 0.005 bar). All three higher rung-points (1.0x, 3.0x, 4.0x) passed
cleanly in both families, worst rel_delta 0.0004-0.0019, well inside
tolerance. This reads as a genuine dose-precision effect at small absolute
setpoints (qwen 0.0625x = 0.788 dose_abs, mistral 0.0625x = 0.229 dose_abs)
rather than a wiring defect (contrast with the factorial's gain-squared bug,
which produced enormous, unmistakable misses, not a single-row near-miss) --
the readback measurement appears to carry a roughly fixed absolute noise
floor that becomes a larger RELATIVE error at the ladder's smallest
setpoint. Per the pre-registered rule (mandatory GPU preflight, hard stop on
any readback miss), NO PASS marker was written for either family; per
`run_margin.py`'s refusal check, `generate-family` will refuse to start for
either family until this is resolved. Did not retry, adjust tolerance, or
change rows/rungs -- reporting the sensor-gate failure straight per standing
instruction and returning to the lead for adjudication.

**Collapse-location evidence (descriptive, from the preflight rows
themselves):** well-formedness was 4/4 (100%) at 0.0625x and 1.0x and 0/4
(0%) at 3.0x and 4.0x, in BOTH families -- consistent with the factorial's
prior qwen collapse evidence (well_formed 0.000 at dose_abs 25.2 = 2.0x) and
now the first direct collapse evidence for mistral (no prior ladder existed
for it). This is preflight-scale (n=4) evidence only, not a criterion
readout.

No full run was launched (`generate-family` was never invoked with
`--i-know-this-runs-on-gpu`). GPU memory was confirmed released (`nvidia-smi`
0 MiB used) after each preflight and before the next.

## 2026-07-17 ~02:55 UTC -- Lead adjudication of the SC1 preflight failure (pre-generation)

The mandatory preflight FAILED the registered SC1 readback gate (relative
0.005 at every rung) in both families: 1 of 4 rows per family at the
0.0625x rung only (qwen kuq_unknowns_all:1039 rel 0.006773 / abs 0.00534
dose_abs; mistral kuq_unknowns_all:1018 rel 0.006601 / abs 0.00151). All 24
row-checks at 1.0x/3.0x/4.0x passed at rel 0.0004-0.0019. Reading of the
full per-row table: the readback error carries a small, roughly fixed
ABSOLUTE component (0.0004-0.0053 dose_abs across rows) that is invisible
at 1x and above but dominates the RELATIVE criterion at the bottom rung
(targets 0.788 qwen / 0.229 mistral). Worst actual mis-dose is 0.04% of the
family reference dose on a 2x-spaced ladder; a wiring defect of the class
SC1 exists to catch (rung mapping, sign, gain -- compare the factorial's
gain-squared bug) would exceed the observed deltas by more than an order of
magnitude at every rung.

Adjudication decisions, recorded before any staircase generation:

1. The registered gate stands as written tonight. The readback tolerance
   was NOT a pre-authorized launch-time knob (the amendment authorizes only
   the mistral top-rung adjustment), so amending gates.yaml is a PI
   decision, not a lead decision. The full run does NOT launch overnight.
   (An edit to gates.yaml was additionally blocked by the session
   permission classifier; per standing protocol the block is honored and
   the decision lifted to the PI rather than worked around.)
2. No retry-until-pass. SC1 has no registered retry remedy (contrast CG1's
   explicit VOID_REGRADE_ONCE), so the first preflight result stands as the
   gate outcome. A rerun of the preflight command will not be used to
   obtain a PASS marker even if it would pass.
3. A read-only diagnostic (separate output tree analysis/preflight_diag/,
   new script harness/diag_readback.py, no gate-state writes) is measuring
   (a) repeatability of the two failing rows' deltas across 3 fresh passes
   and (b) the abs-delta distribution over 12 additional rows per family at
   0.0625x/0.125x/0.25x, to discriminate deterministic quantization from
   stochastic measurement noise for the morning decision.

PROPOSAL FOR PI (morning): amend gates.yaml SC1 readback rule to
"rel_delta <= 0.005 OR abs_delta <= 0.005 x family reference_dose_abs",
then bin/exp repin margin-mapping, mirror the OR-bound in
harness/sc1_checks.py + harness/config.py, re-run the preflight fresh under
the amended rule, and launch the two family staircases. The OR-bound keeps
>10x detection margin against every wiring-defect signature while removing
only the bottom-rung sensitivity to the absolute noise floor. Alternative
options if preferred: (a) drop the 0.0625x rung (loses CDF resolution below
the expected confab median, requires ladder change + repin), or (b) accept
per-row readback flagging at the bottom rung and censor flagged rows in
analysis (keeps gate text but adds an analysis rule; weakest option, moves
complexity downstream). Whichever way, no criterion surface (P1/P2/P3/C1)
is touched.

Collapse observation from the preflight (descriptive, n=4/rung-point):
well-formed 4/4 at 0.0625x and 1.0x, 0/4 at 3.0x and 4.0x, both families.
Consistent with the doubt-snap qwen collapse at 2.0x; first direct mistral
collapse evidence. The mistral top-rung authorized knob is NOT exercised:
the collapse boundary lies in (1.0x, 3.0x], which the ladder already
brackets with the 1.5x and 2.0x rungs.

## 2026-07-17 ~03:00 UTC -- Readback diagnostic results (analysis/preflight_diag/)

Verdict: the readback error is fully DETERMINISTIC per row (bit-identical
deltas across 3 fresh forward passes for all 8 repeatability rows, spread
exactly 0 in both families). Retrying could never change the preflight
outcome; the no-retry rule was correct and is now also moot.

Breadth (12 additional subsample rows per family, one pass each): 0/12
failures at 0.0625x, 0.125x, and 0.25x in both families; bulk relative
error is ~0.16-0.19% at every rung tested. The two originally-failing rows
are the tail of a per-row deterministic distribution (roughly 1 in 16
sampled rows exceeds the pure-relative bar at the bottom rung). Under the
registered gate the full run would hard-abort at the bottom rung's live
first-batch assertion with near-certainty (~6% of 760+ rows per family
failing).

OR-bound check against the proposal (abs <= 0.005 x reference_dose_abs =
0.0630 qwen / 0.0183 mistral): worst observed abs_delta anywhere in the
diagnostic is 0.00694 (qwen, 0.25x rung) and the failing rows sit at
0.00534 / 0.00151 -- all pass with 2.6x-12x headroom while every
wiring-defect signature still exceeds the bound by >10x. Packet complete;
awaiting PI decision.

## 2026-07-17 -- PI approved SC1 OR-abs amendment; fresh preflight PASS; launch

PI decision (conversation, morning after the halt): option 1, amend SC1
readback to "rel <= 0.005 OR abs <= 0.005 x family reference_dose_abs".
Executed pre-generation: gates.yaml amended and repinned via bin/exp repin
(7eb74eed -> 934cacae, reason recorded in instrument.repins), OR-bound
mirrored in harness/config.py + harness/sc1_checks.py, config hash pin
updated. Smoke suite 29/29. Behavioral regression check: both
originally-failing tail rows pass under the new rule; gain-squared and
doubled-dose defect signatures still fail.

Fresh preflight re-run under the amended rule (full command, not a
re-evaluation of stored measurements): qwen35_4b PASS (all 16 checks),
mistral7b_v03 PASS (all 16 checks), PASS marker written, GPU released
between and after families. The 2026-07-16 FAIL preflight and the
diagnostic remain in the record (this entry supersedes neither).

Launching the full two-family staircase: qwen35_4b first, then
mistral7b_v03, greedy, batch 4, RunLog checkpointing, ~4.5h per family on
the local 3090 (free lane, PI-approved).

## 2026-07-17 -- Recovery adjudication after the worktree-sweep data loss

Staged-input recovery status (restage agent + lead verification):
- qwen heldout_rows_for_steer.jsonl and mistral joined_rows_private.jsonl
  REBUILT from committed builder scripts + datasets; both sha256 EXACT
  matches to the M1 staging pins; symlinks replaced with local copies
  (policy: staged inputs are local copies from now on, never
  cross-worktree symlinks).
- Both staged baseline.jsonl originals are unrecoverable byte-identically
  (GPU RunLogs; n_new_tokens and original grade schema not reconstructable
  from text). NON-BLOCKING: cmd_reuse_baseline already ran pre-incident;
  the operative dose-0 artifacts (<family>__baseline_reused.jsonl) are
  complete on disk, and neither preflight nor generate-family reads the
  staged originals. The staging manifest's baseline pins stand as the
  record that byte-identity WAS verified at staging time. Provenance gap
  recorded here; no further action.
- NEW BLOCKER: mistral7b_v03/directions/hs16_c_hat.json was ALSO a
  dangling symlink (contrary to the earlier assumption that all
  directions were local copies; only qwen hs20 was). The raw vector was
  never committed anywhere (RR's manifest persists scalars only).

Pre-stated acceptance rule for the hs16_c_hat reconstruction, recorded
BEFORE the capture runs: rebuild FIT-split rows from the hash-verified
joined pool, render via RR2's own render.py, GPU anchor-capture at layer
16 on the pinned Mistral revision, direction_fit.fit_directions
(seed=20260713), fit_reuse.py's built-in cross-check against the
committed rr_reference_values scalars must pass, AND the resulting file's
sha256 must EXACTLY match the M1 staging-manifest pin for
hs16_c_hat.json. On exact match: restage as local copy and resume mistral
generation (the existing preflight PASS was produced under the
byte-identical original and remains valid). On ANY mismatch, including
numerically-close: STOP, no generation, lift to the PI -- a non-identical
direction is a different instrument than the signed one.

Harness fix (post-sign code repair, no gate/config semantics change):
config.py FACTORIAL_STAGING_MANIFEST pointed at the deleted
gate-factorial worktree path; repointed to the committed manifest at
experiments/gate-contribution-factorial/analysis-committed/staging_manifest.json
inside this worktree.

## 2026-07-17 -- hs16_c_hat reconstruction attempt: STOP per pre-registered rule

Single attempt, all knobs per the committed spec (fit seed 20260713, tuner
86b134c3 = rr2 pin, model revision c170c708, hf-batched bf16 compute /
fp32 persist, atlas render + position conventions, FIT rows 874 confab +
255 known + 214 unknown_refused = 1343, exact match to rr_reference row
counts). Cross-check FAILED all six scalar fields (mu_d -0.6997 expected
vs -0.7075 reconstructed, rel ~1.1%; tau_frozen rel ~0.7%; sigma_c nearly
exact at +0.00004). sha256 88054fa7... vs pinned f6555f32..., no match. No
generation launched, no restaging, dangling symlink untouched, per the
acceptance rule recorded pre-capture (commit 26589319). Delta pattern
(mu_d/tau_frozen off, sigma_c exact) is more consistent with a
systematically different render/tokenize input in the ORIGINAL capture
than with forward-pass noise; hypothesis only, not tested. Adjudication
lifted to the PI.

## 2026-07-17 -- hs16 forensics: no discrepancy found; PI-directed fallback to qwen-only scope

Bounded forensics pass (PI-authorized, single diagnostic sweep, read-only)
over the committed atlas -> RR -> RR2 lineage, comparing every capture
parameter of the original mistral hs16 anchor capture against the failed
reconstruction attempt. Result: NO discrepancy backed by committed
file+line evidence. Model revision, render logic (byte-identical diff of
render.py against render_jspace_atlas.py), tokenization
(add_special_tokens=True), anchor position (len(token_ids)-1), layer/key
convention (anchor__L16; provably insensitive to the --layers filter),
engine (hf-batched), persist dtype (float32), compute dtype (default bf16
both sides), FIT row filter and counts (874/255/214), fit seed (20260713),
and row text (sha256-verified) all match. One evidentiary hole, not a
mismatch: the reconstruction's actual GPU batch-capture invocation was
never logged, so its batch size is unrecorded (original: 8, committed in
capture_manifest.json); architecturally unlikely to be causal given
hf_batched's per-row absolute positioning and masked attention.

The STOP entry's earlier hypothesis (systematically different
render/tokenize input in the original capture) is REFUTED by this pass:
render and tokenize are confirmed identical on both sides. The surviving
explanation is bf16 forward-pass non-determinism across separate runs,
amplified by downstream threshold statistics (mu_d off ~1.1% via the
unknown_refused group mean; sigma_c, which never touches that group,
essentially exact). That is not a fixable parameter, which means the
registered exact-sha256 acceptance leg is likely unreachable in
principle. Per the pre-registered rule, no second reconstruction attempt
was made and no generation was launched.

ADJUDICATION (lead, executing the PI's pre-stated decision of 2026-07-17:
"if nothing found or it still misses: fall back to qwen-only"): M1 is
reduced to qwen35_4b-only scope. This is an instrument-loss scope
reduction caused by the worktree-sweep incident, not a results-driven
choice: no mistral staircase data beyond the 4-rung preflight exists, so
nothing about mistral outcomes could have informed it. Scoreboard
treatment at resolution: all mistral slots (separation, setpoint
placement, retrodiction, and the mistral halves of the registered bands)
are VOID_INSTRUMENT_LOSS and will not be scored for either predictor;
qwen slots proceed unchanged. No gate, threshold, or prediction is
altered. The mistral generation stage will not run; the dangling
hs16_c_hat.json symlink stays in place as the incident record.

## 2026-07-17 -- Qwen SC1/SC3 formal verification over the completed staircase

Independent post-run verification (results-analyst agent; script and
machine-readable summary under analysis/verification/; lead spot-checked
the summary against the report). Registered gates read from gates.yaml
(sha256 934cacae..., matches the experiment.yaml pin).

- SC1 (readback, amended rule rel<=0.005 OR abs<=0.005*reference): PASS.
  7,600 dosed rows checked (10 rungs x 760; dose-0 baseline correctly out
  of scope), 0 rows failed both legs. Max rel_delta 0.007768 (0.0625x
  rung, passes on abs leg at 0.000485*reference -- the registered bf16
  floor pattern); max abs fraction 0.006714 (4.0x rung, passes on rel leg
  at 0.001679). Recomputed per-rung maxima match the harness's own
  live-sc1 log lines to 6 decimals at every rung.
- SC3(a) (zero silent drops): PASS. 11/11 files (baseline + 10 rungs) at
  exactly 760 rows (400 confab + 360 known); zero duplicate, missing, or
  unexpected row_keys against the committed subsample manifest (seed
  48260714) at every rung.
- SC3(b) (censored-per-role reporting) and SC3(c) (non-monotone class):
  NOT YET COMPUTABLE -- both are properties of the derived per-row margin
  dataset, which has not been produced yet. Blocked on the margin
  derivation step, not failures.
- Integrity: dose targets equal multiplier x reference_dose_abs at all 10
  rungs; gen log clean, no aborts or errors.

Next steps: run the margin derivation (detector-v2 readout + per-row
tipping/collapse doses) over the qwen staircase, then the calibration
slice blinded grading (700 rows, seed 48260715, hash-commit-before-
unblind, CG1 floors) before any scoreboard unblinding.
