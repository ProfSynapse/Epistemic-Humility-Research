# j-space-cross-family-layer-contrast notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-24 -- qwen3.5-4b j-space DISPOSITION: DEFERRED (back-burnered by user, not a G0 stop)

**Killed run.** `jlens_profile.py --family qwen35-4b` was terminated by the lead's
direction (PID 922336 + wrapper 922335) after logging only 1 of 10 depth-sweep
points (hs_index=1) in 6h13m wall clock -- that single point cost 20172.8s
(~5.6h), ~20x the LAUNCH-PLAN's 2-3h whole-stage budget. Root cause (read-only
diagnostic, no pinned-file edit): the log's first computation line reads "The
fast path is not available because one of the required library is not
installed. Falling back to torch implementation" -- Qwen3.5-4B's hybrid
linear/full-attention layers (config.text_config.layer_types alternates the
two) fall back to a slow plain-PyTorch path without the optional
flash-linear-attention/causal-conv1d packages. Confirmed genuine ongoing
compute, not a hang, via steady 104% CPU on the actual python child process and
non-zero (30-40%) GPU utilization the entire run. `jlens.layer_profile()` has
no resume-from-partial logic, so a restart always begins again from
depth_sweep[0]; the completed hs_index=1 result is durably checkpointed at
`analysis-committed/qwen35-4b/layer_profile.json` but is a PARTIAL/INCOMPLETE
artifact, not usable as evidence. `families/qwen35-4b.yaml`'s
`band_selection.status` remains `not_yet_run` (the write-back only fires at
the end of a completed sweep, which never occurred).

**Disposition: DEFERRED (back-burnered), not NOT-RUN/G0 stop.** This is a
distinct category from llama/mistral's G0 dose-viability stops -- no gate
fired, no dose was ever calibrated; the profile stage itself couldn't
complete in budget. User decision (2026-07-24 morning) is to back-burner this
family rather than force a decision now. Three restart paths remain on the
table for a future signed revision or lab-notebook entry: (a) a smaller
first-pass `--n-prompts` (200-300), which the LAUNCH-PLAN itself pre-flagged
as a contingency but which still costs hours not minutes at linear scaling,
not the sub-hour the local-smoke-scale reference implied; (b) installing
flash-linear-attention/causal-conv1d and retrying n=1000, CAVEATED that the
J-lens double-backward JVP machinery may not be supported by the fused
kernels at all, making the observed fallback the only correct path rather
than a fixable slowdown -- a cheap CPU/1-layer smoke should answer this
before committing further GPU time; (c) accepting a NOT-PROFILED disposition
for this family this round. None of these paths were taken; qwen3.5-4b is
simply held, dependency-install path documented for whoever picks it back up.

### 2026-07-24 -- norm-scaled dose-ladder signed revision being drafted (context, not yet in effect)

The lead is drafting a signed revision to re-run llama-3.2-3b and
mistral-7b-v03's dose calibration on a norm-scaled ladder rather than the
current fixed absolute ladder ([25,50,...,200], calibrated on Qwen3-4B's own
residual scale). Their extraction/build_directions/gate_fit artifacts remain
valid and reusable across this revision (only calibrate_dose + downstream
would re-run); expect a return to those two families after gemma4-e4b's
pipeline completes. Qwen3-4B's own reference anchor L2 norms were recovered
for comparison: hs23 66.7, hs26 124.8, hs29 209.2, hs34 423.8 -- its own
SELECTED doses sat at 0.37-0.60x the median norm at each layer, with a usable
band roughly 0.2-1.0x median norm. Under the old fixed absolute ladder,
llama's mid-band doses translated to 1.8-14.6x its own (much smaller) median
norms -- entirely outside the 0.2-1.0x usable band that worked for Qwen3-4B.
This closes the physics of both G0 dose-viability stops observed so far: the
ladder was never wrong in absolute terms, it was calibrated for one family's
residual scale and applied unchanged to others whose scale differs by an
order of magnitude. This is background for a FUTURE signed revision only --
no ladder value has been changed in this run, and none of llama/mistral's
G0 dispositions above are altered by this note.

### 2026-07-23 -- mistral-7b-v03 DISPOSITION: NOT-RUN (G0 dose-viability stop)

**Pre-calibration anchor L2 norm read (lead, computed from extraction
safetensors before calibrate_dose ran, per the standing "free early
viability read" rule).** hs12 3.35, hs15 4.43, hs19 8.00, hs30 (late) 21.46
(300-row samples). ALL FOUR layers -- including the late-reference arm --
sit below the ladder floor (dose 25), a stronger and more uniform
below-floor pattern than llama's (which had its late arm above floor at
30.4). This strongly predicted the same units-mismatch dose-viability stop,
in advance of calibrate_dose running.

**calibrate_dose.py ran to completion cleanly** with the repinned `--fresh`
flag (same bugfix as llama): 32/32 (layer,dose) cells (mid-band
hs12/hs15/hs19 x late hs30, all 8 ladder doses [25...200]), ~35 min GPU
time, readback within tolerance at every single cell (write mechanism
confirmed accurate, `frac_readback_within_tol == 1.0` on all 32 cells).
Result: `all_midband_have_usable_dose: false`, `all_layers_have_usable_dose:
false` -- no dose at any of the 4 layers clears the locked usability bar.
Unlike llama (which had one near-miss cell at 0.125 collapse), mistral's
collapse pattern is close to total: `collapse_rate_on_dosed` is 1.0 at
every single (layer, dose) cell except one (hs30/late at dose=25, where
collapse is 0.0 but `confab_tighten` is still 0.0, so still unusable).
`confab_tighten.rate` is 0.0 at every single cell across all layers and
doses -- the write never registers a usable caution effect anywhere on the
ladder for this family. `known_correct_cost_control.rate` is pinned at
0.125 (1/8) at every cell regardless of dose or layer, consistent with one
fixed known-correct FIT row failing independent of the intervention. Full
per-cell numbers: `analysis-committed/mistral-7b-v03/dose_calibration_summary.json`.

**Bug-vs-genuine-behavior check (read-only diagnostic, scratchpad-only, not
part of the pinned instrument, no pinned-file changes).** Wrote a throwaway
script reusing `pipeline.py`'s own `render`/`run_pass_fixed`/
`setup_hook_from_path`/`compute_gate_decisions` verbatim to print RAW
generated text for 2 fired confab rows at hs12 (the lowest-norm mid-band
layer), doses 25 and 50 (readback confirmed accurate: 25.00-25.01,
50.01-50.01 respectively; `strength = dose/sigma_c` computed as ~120-240,
several times larger than the strength that produces the same collapse
pattern in llama at the same nominal doses, consistent with mistral's even
smaller sigma_c/anchor-norm scale at these layers):
- BASE (undosed): clean well-formed JSON on both rows, e.g. `{"answer": "I
  don't have the ability to definitively say that biodegradable materials
  are the most effective solution...", "response_confidence": 0.3}`.
- DOSED at 25 (the ladder's lowest dose): immediate collapse into repeated
  fragment loops from the very first tokens -- `{ answer answeratr -
  -atr -atratratratratrat...` -- no coherent JSON structure or semantic
  content survives even at the ladder floor, unlike llama where the
  semantic caution direction read through briefly before collapsing.
- DOSED at 50: same pattern, different repeated fragment (`aughteropter
  opteropteropter...`).

This confirms genuine over-steering / total repetition-collapse from the
very first dose on the ladder, not a detection false-positive or a
hook/readback bug -- the write mechanism is accurate (readback matches
target to within fractions of a unit at every cell) but the model cannot
sustain ANY coherent generation under this write at ANY point on the
locked ladder, worse than llama's partial degradation-then-collapse
pattern. Consistent with the anchor-norm prediction above: a units
mismatch between the ladder (calibrated on Qwen3-4B's residual scale) and
mistral-7b-v03's own (much smaller) residual scale at these layers, not a
per-family tuning failure. No off-ladder dose was tried and none of the
min-confab-rate/layer/ladder parameters were touched -- all locked per the
signed instrument; ladder extension is a signed-revision question the lead
is lifting to the user separately, out of scope for this run.

**Formal G0 gate firing on record.** `run_contrast.py --family
mistral-7b-v03 --mode smoke --n-rows 8` invoked and exits with:
`ValueError: [mistral-7b-v03] calibration summary says not all mid-band
layers have usable doses` (raised at `load_midband_selected_doses`,
run_contrast.py line 80) -- the instrument's own designed gate, not a
workaround. Identical failure mode and identical gate-firing mechanism as
llama-3.2-3b.

**Note on family substitution provenance.** This family's YAML already
records the pre-existing substitution (Ministral-3-3B -> Mistral-7B-
Instruct-v0.3, due to a conditional-gen class issue) and the doubt-snap
reused late-site fit was already a TRUE BEHAVIORAL NULL there
(`doubt_snap_fit_peak_clean_tighten: {rate: 0.0, dose: 30.0, known_cost:
0.0118}`) -- consistent with this family also failing to produce a usable
intervention effect in the predecessor experiment at its frozen late site,
independent of this experiment's fresh mid-band mining.

**Disposition:** NOT-RUN (G0 dose-viability stop) -- CONFIRMED by lead
adjudication, mirroring llama-3.2-3b's confirmed disposition pattern. Two
of two families run so far have hit the identical G0 stop; qwen3.5-4b and
gemma-4-e4b remain to test whether this is family-general or specific to
the two `torch_dtype`-heterogeneous / smaller-residual-scale families run
first per the locked order.

**Cross-family observation (lead, added at adjudication).** Mistral is
qualitatively WORSE than llama at the ladder floor -- zero semantic
read-through even at dose=25 (immediate token-loop collapse) vs llama's
brief coherent refusal before collapsing. This is consistent with mistral
having the smallest sigma_c of the two families run so far, and therefore
the largest effective strength (`dose/sigma_c`) at any given nominal dose
on the shared ladder. The resulting cross-family strength gradient --
qwen3-4b in-range (ladder was calibrated on it), llama roughly 2-4x over,
mistral roughly 5-10x over -- is the central design input for the
norm-scaled-ladder question the lead is lifting to the user separately;
not acted on here, ladder stays locked as signed.

### 2026-07-23 -- llama-3.2-3b DISPOSITION: NOT-RUN (G0 dose-viability stop, adjudicated)

**calibrate_dose.py ran to completion cleanly** with the repinned `--fresh`
flag: 32/32 (layer,dose) cells (mid-band hs17/20/23 x late hs26, all 8
ladder doses [25...200]), ~24 min GPU time, readback within 5%+0.5 tolerance
at every single cell (the write mechanism itself is not the problem).
Result: `all_midband_have_usable_dose: false`, `all_layers_have_usable_dose:
false` -- no dose at any of the 4 layers clears the locked usability bar
(`frac_readback_within_tol == 1.0` AND `collapse_rate_on_dosed == 0.0`
exactly AND FIT confab `clean_tighten` rate `>= 0.5`). Best case across the
whole ladder: hs23 dose=25 at 1/8 (0.125) collapse, still nonzero. Full
per-cell numbers: `analysis-committed/llama-3.2-3b/dose_calibration_summary.json`.

**Bug-vs-genuine-behavior check (read-only diagnostic, scratchpad-only, not
part of the pinned instrument, no pinned-file changes).** Wrote a throwaway
script reusing `pipeline.py`'s own `render`/`run_pass_fixed`/
`setup_hook_from_path`/`compute_gate_decisions` verbatim to print RAW
generated text for 2 fired confab rows at hs17, doses 25 and 100:
- BASE (undosed): clean well-formed JSON, e.g. `{"answer": "It depends on
  the severity and type of disaster...", "response_confidence": 0.6}`.
- DOSED at 25 (the ladder's lowest dose): readback confirms the write lands
  at the correct magnitude (25.00-25.01); the semantic caution direction
  DOES read through (`{"answer" isUnknown I don't know the answer" ...`) but
  then collapses into runaway `unable unable unable...` repetition, hitting
  the 200-token cap without terminating naturally.
- DOSED at 100: worse degradation into token salad (`пока oren oren
  oren... impossible impossible...`).

This confirms genuine over-steering / repetition-collapse, not a detection
false-positive or a hook/readback bug -- the write mechanism is accurate and
the direction is semantically correct, but the model cannot sustain
coherent generation under this write at ANY point on the locked ladder.

**Root-cause corroboration (lead, independent, read-only).** Anchor L2 norms
computed directly from the extraction safetensors (300-row samples, tight
spread): hs17 13.7, hs20 17.2, hs23 21.9, hs26 30.4. The ladder floor (dose
25) EXCEEDS the entire typical hidden-state norm at all three mid-band
layers -- a UNITS MISMATCH between the ladder (calibrated on Qwen3-4B's
residual scale) and llama-3.2-3b's own residual scale, not a per-family
tuning failure. This exactly predicts the diagnostic's observed pattern
(semantics read through at the lowest dose, then immediate repetition
collapse, worse at higher doses). No off-ladder dose was tried and none of
the min-confab-rate/layer/ladder parameters were touched -- all locked per
the signed instrument; ladder extension is a signed-revision question the
lead is lifting to the user separately, out of scope for this run.

**Formal G0 gate firing on record.** `run_contrast.py --family llama-3.2-3b
--mode smoke --n-rows 8` invoked and exits 1:
`ValueError: [llama-3.2-3b] calibration summary says not all mid-band
layers have usable doses` (raised at `load_midband_selected_doses`,
run_contrast.py line 80) -- the instrument's own designed gate, not a
workaround.

**DISPOSITION (adjudicated lead+drafter 2026-07-23): NOT-RUN, G0
dose-viability stop.** Matches gates.yaml's pre-anticipated category
verbatim ("A family that fails G0 after bounded debugging... is recorded
as NOT-RUN with the explicit blocker and excluded from the cross-family
denominator -- neither a PASS nor a FALSIFIER hit for that family"),
structurally the same category as `doubt-snap-cross-family-confirmatory`'s
own late-site dose-viability stops. llama-3.2-3b is excluded from the
cross-family roll-up denominator; proceeding to mistral-7b-v03 next per the
locked run order.

### 2026-07-23 -- llama-3.2-3b: extraction + mid-band fit/gate results; calibrate_dose.py pinned-code bug found, fixed, repinned

**extract_anchor.py** (GPU): 2956/2956 rows extracted in 112.8s, safetensors
139.6M, `analysis/llama-3.2-3b/anchor_extract_manifest.json` `complete: true`.
Ran with the two render() fixes below (PYTHONPATH + vendored shim).

**build_directions.py --verify-reproducible** (CPU): reproducibility check
PASS at all three mid-band candidate layers (hs17, hs20, hs23). `cos_u_d_u_p`
near-orthogonal at every layer (0.038-0.040), `cos_caution_dir_c_hat` >=0.985
(orthogonalized caution direction still highly aligned with the raw caution
axis, as expected). Standardization stats (`mu_d`/`sigma_d`/`mu_c`/`sigma_c`)
written per layer to `build_manifest.json`.

**gate_fit.py** (CPU): Youden-J frozen tau at all three mid-band layers, AUC
(`neg_z_d`, FIT confab vs FIT known_correct_answered) well above the 0.90 G0
floor at every candidate:
- hs17: AUC 0.9993, tau -0.3755, tpr 0.9931, fpr 0.0090 (tp 577 fn 4 fp 2 tn 220)
- hs20: AUC 0.9991, tau -0.3401, tpr 0.9931, fpr 0.0090 (tp 577 fn 4 fp 2 tn 220)
- hs23: AUC 0.9990, tau -0.2667, tpr 0.9914, fpr 0.0090 (tp 576 fn 5 fp 2 tn 220)

**calibrate_dose.py pinned-code bug (found, lead-fixed, repinned).** First
invocation crashed immediately, before any GPU dose-ladder generation:
`AttributeError: 'Namespace' object has no attribute 'fresh'` at line 123
(`if args.fresh and ckpt_path.is_file():`) -- the script's own argparse block
(lines 204-209) never defined a `--fresh` flag, despite the script's own
comment at line 118 documenting one ("Resume assumes the same --doses ladder;
use --fresh to restart") -- an authoring omission, not a design gap;
`run_contrast.py`'s argparse correctly has `[--resume | --fresh]`. Not an
environment issue (100% reproducible on any family/args, before any GPU
work). Reported to lead with exact line numbers and a minimal one-line
proposed diff; lead independently verified, applied the diff verbatim (one
`parser.add_argument("--fresh", action="store_true", ...)`, no other line
changed), smoke-checked `--help` shows the flag, and ran the governed repin:
`calibrate_dose.py` `b817c12f...` -> `0579f52891b1...` (reason recorded in
`instrument.repins`). Dose ladder, gates, and resume logic untouched.

### 2026-07-23 -- launch G0 crash diagnosis: two dead render() imports, one PYTHONPATH fix + one vendored shim (CPU-only diagnosis, no GPU work counted toward outcome; pending lead repin before relaunch)

llama-3.2-3b's `extract_anchor.py` crashed at G0 (`model_lib.py`'s `render()`)
with two sequential `ModuleNotFoundError`s, both caused by an UNRELATED prior
main-branch reorg archiving files this experiment's pinned `model_lib.py`
imports by bare module name via a hardcoded `sys.path` entry
(`PROBE_DIR = .../experiment/phase1/probe`). Neither import target still
lives at that path.

1. **`backends.render_probe_prompt`** -- `experiment/phase1/probe/backends.py`
   was archived; the archive copy is a dead compat wrapper pointing at a
   nonexistent `experiments/common/phase1_probe/`. FIXED via environment only
   (no code/file changes): `PYTHONPATH=/home/profsynapse/code/
   Epistemic-Humility-Research/experiments/common/knowledge_probe` added to
   every pipeline invocation. That directory's `backends.py` is the live,
   actively-maintained successor with an IDENTICAL
   `render_probe_prompt(tokenizer, system_prompt, question, *,
   enable_thinking, mode=None)` signature (verified by CPU-only import +
   `inspect.signature`), explicitly documented there as the shared render
   path for "the hidden-state harness" too.
2. **`amendment_ah_stage0_extract.load_baseline_system_prompt`** -- NOT
   env-fixable: the only surviving copy is archived
   (`archive/experiment/phase1/probe/amendments/`), hardcodes a config
   filename (`experiments/doubt-regulated-caution/
   phase3_ac_doubt_coupled_intervention.yaml`) that no longer exists at that
   path (renamed via `git log --follow`: moved by commit 6b66536a, then
   dropped the `phase3_` prefix by commit d55b7d26 -- `git show d55b7d26` on
   that file confirms the `prompt:` block itself is untouched in that patch),
   and its sibling archived `path_compat.py` is independently broken (its
   `repo_root()` heuristic depends on `experiment/phase1/eval/scorers.py`,
   itself archived by the same reorg that broke this experiment's own
   `grader.py` `EVAL_DIR`, already fixed by vendoring `scorers.py` at
   sign-time -- see the entry below). The live successor `path_compat.py`
   (`experiments/common/readouts/`) fixes the `repo_root()` check but drops
   the `phase1_probe_dir()`/`phase1_eval_dir()` names the archived script
   imports -- an API mismatch on top of the dead filename, not just a stale
   search path. Lead-adjudicated 2026-07-23: vendored a minimal shim,
   `amendment_ah_stage0_extract.py`, into this experiment directory (sibling
   convention, matching the `scorers.py` precedent) that supplies ONLY
   `load_baseline_system_prompt()`, reading the renamed live yaml
   (`experiments/doubt-regulated-caution/ac_doubt_coupled_intervention.yaml`
   `prompt.system`) and FAIL-CLOSED asserting its sha256 equals a hardcoded
   `_EXPECTED_SHA256` (`81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c`)
   computed at shim-authoring time -- a future edit to that yaml's
   `prompt.system` will raise instead of silently changing what every
   family's generation renders. Smoke-tested both the happy path and the
   fail-closed mismatch path (CPU-only, deliberately corrupted the expected
   hash in-process to confirm it raises).

   **Cross-check (required before trusting this shim for the reused frozen
   late-site arm):** loaded `experiments/doubt-snap-cross-family-
   confirmatory/render.py`'s hardcoded `BASELINE_SYSTEM_PROMPT` literal
   directly (module import, not hand-transcribed) and compared byte-for-byte
   against the shim's yaml-sourced string: **IDENTICAL** -- same sha256
   `81a04a99827ade21b9d5bd1832c2012429d196f96e604238a4b927701ca58e3c` for
   both. This confirms the render convention this shim restores is the same
   one doubt-snap's frozen late-site directions (`c_hat`/`u_d`/`gate_fit`,
   reused verbatim by this experiment) were actually fit under -- resolves
   AMENDMENT.md "Open questions at sign" #5 (render/anchor reconciliation)
   affirmatively for the system-prompt component; anchor position and
   `enable_thinking` convention are separately unchanged (ported verbatim in
   `model_lib.py`/`gen_lib.py`, not touched by this fix).

No pinned-byte edits: `model_lib.py` and every other pinned instrument file
are unmodified. The new shim file is NOT yet part of the signed pin set --
lead is running a governed repin to add it before any GPU relaunch. Did NOT
restart `extract_anchor.py` or any other GPU work pending that repin
confirmation.

### 2026-07-23 -- sign-time revision: primary reframe + doubt-snap reuse (CPU-only, no GPU, NOT signed)

Lead-directed, user-approved structural revision of the draft, after
`doubt-snap-cross-family-confirmatory` RESOLVED (2026-07-12, confirmatory not
promoted -- every launched cell stopped at G0 FIT dose-viability at the late
0.94-depth site; gemma4_e4b_it never behaviorally launched). All predecessor
docs and doubt-snap committed artifacts were read from the canonical `main`
checkout (this worktree is 677 commits behind main and does NOT contain them).

Changes made:
- **Primary endpoint reframed to ABSOLUTE mid-band actuation.** New per-family
  primary gates: G1 mid-band held-out confab clean_tighten floor, G2 mid-band
  known-correct not_well_formed_correct cost cap. The late-reference arm is
  DEMOTED to a non-gating secondary descriptive comparator; the draft's relative
  G1/G2 contrast and the G3 late-viability floor (0.40/0.30) are DROPPED.
  gates.yaml, AMENDMENT.md (Prediction/Falsifier/Gates + new "Gates ->
  derivation" and "Open questions at sign"), experiment.yaml, and
  run_contrast.py/cross_family_rollup.py updated.
- **Gate numbers with written derivation (adjudicated lead+user 2026-07-23,
  conservative option chosen).** G1 = clean_tighten >= 0.50, Wilson lower > 0.40
  (below the weaker same-lineage mid-band held-out point ~0.66 Qwen3.5-4B / 0.89
  Qwen3-4B, far above the dead late-site region <= 0.33; Wilson-lower 0.10 below
  the point, mirroring qwen35-4b-midband-heldout's gate shape). The stricter
  0.60/0.50 alternative was offered and NOT elected. G2 = not_well_formed_correct
  <= 0.05, Wilson upper < 0.10 (inherits qwen35-4b-midband-heldout's cost gate;
  both Qwen substrates cleared at 0.035/0.039).
- **Consumes doubt-snap artifacts, hash-pinned.** Each `families/<slug>.yaml`
  gained a `reuse.doubt_snap` block: committed-artifact relative paths + sha256
  (split_manifest, build_manifest, c_hat, u_d, random_direction, gate_fit,
  dose_fit, g0_prep_summary), Modal volume + path, frozen late-site params
  (block/hs_index, tau_frozen, mu_c/sigma_c/mu_d/sigma_d), FIT/held-out counts.
  New `materialize_reused_rows.py` replaces mine_eval_pool.py + split_fit_heldout.py
  (retained fallback-only) for the four reused families; family_config.py gained
  reuse accessors; build_directions/gate_fit scoped to mid-band only (late-site
  direction/gate reused frozen, not refit); calibrate_dose sweeps mid-band AND
  the late site (option B -- fresh late-site DOSE, frozen late direction/gate);
  pipeline.py's compute_gate_decisions/run_layer branch the late arm to the
  frozen reuse artifacts. Late reference site is now DEFINED as doubt-snap's
  frozen block (llama 25 / mistral 29 / qwen35-4b 29 / gemma 39; hs_index+1 =
  26/30/30/40 -- coincidentally equal to this experiment's own 0.9444*L estimate).
- **Gemma-4-E4B Modal fallback pre-authorized** (LAUNCH-PLAN.md + AMENDMENT.md):
  local first, Modal fallback for the Gemma cell only on a G0 OOM, NOT-RUN only
  if Modal also fails.

Two artifact gaps found while pinning (flagged as open questions, not guessed
around): (1) NO family has a calibrated late-site dose to reuse (all doubt-snap
cells `selected_dose: null`); (2) gemma4_e4b_it was never behaviorally launched
-- FIT prep is committed but no dose_fit.json/modal_status.json, late gate AUC
0.9472 (weakest), held-out known 251 (~1-row margin). Plus the branch-behind-main
dependency (open question #0) and the Modal-volume row-text retention question
(proven only for the qwen35_4b cell).

**Resolved at finalization (2026-07-23, lead+user).** Gap (1): option (B)
adopted -- the late-site DOSE is calibrated fresh with the mid-band ladder for
all four families (frozen late direction/gate still reused verbatim); see
AMENDMENT.md open question #2. Gate numbers adjudicated (conservative option):
G1 0.50/0.40, G2 0.05/0.10. Branch-behind-main resolved by merging `main`
(submodule pin -> 901dbe8, which already contains `feature/runlog`; no pointer
bump needed). Modal retention checked: llama/mistral/qwen35_4b row text PRESENT,
gemma ABSENT (never launched -> pre-authorized Modal fresh-mine fallback).

**Final pre-sign pass (2026-07-23, lead+user).**
- GEMMA FRESH MINE (adjudicated): gemma's pool/split cannot be reused (row text
  absent), so `pool_provenance: fresh_mine` for gemma ONLY -- mine_eval_pool.py +
  split_fit_heldout.py run fresh on gemma's own checkpoint; reuse provenance for
  the pool is LOST and recorded. The frozen late-site direction/tau/
  standardization stay reused verbatim + hash-pinned, applied to the fresh rows
  as a frozen operating point (qwen35-4b-midband-heldout pattern); late dose
  still fresh (option B). G0 reuse-integrity is scoped per family via
  `family_config.integrity_artifact_names`: reused-pool families verify 8
  artifacts (incl. split_manifest); gemma verifies ONLY the 5 frozen late-site
  artifacts (build_manifest/c_hat/u_d/random_direction/gate_fit). Verified by
  running materialize_reused_rows.py --family gemma4-e4b: 5 late-site hashes
  match, no split copied, rc=0. Other three families' G0 untouched.
- VENDOR SCORERS (adjudicated): the merge pulled main commit 21cd5c50 which
  archived experiment/phase1/eval/scorers.py, breaking grader.py's hardcoded
  EVAL_DIR. Vendored scorers.py INTO the experiment dir (sibling convention, no
  external dependency). BYTE-IDENTITY: archived source
  sha256 75e690f583d83d654cb88a3b066b39acb7e9e1b954c9d5677d4b887d6c30905a; the
  vendored file is a provenance header (891 bytes) + that source VERBATIM, so its
  post-header body sha256 == 75e690f5... (byte-identical), and the full vendored
  file sha256 = 1b3eda5d8d68c9184674f092805278505c5cd2065a21ffe7ec348e9ea5a00c37.
  grader.py now imports the local copy (EVAL_DIR dropped). Import smoke:
  `run_contrast.py --help` and `calibrate_dose.py --help` both exit 0, proving
  the grader -> gen_lib -> pipeline -> run_contrast/calibrate_dose chain resolves.

Verification (CPU-only): `bin/exp validate` OK (after moving the not-yet-present
doubt-snap `inputs` paths into a comment, since validate existence-checks
inputs and this branch lacks main's content); `py_compile` OK on all scripts;
`--help` OK on the no-torch scripts (materialize_reused_rows, cross_family_rollup,
build_directions, gate_fit) and family_config reuse accessors resolve all four
families' pins. Full `--help` of the torch+MechInterp scripts needs the project
`unsloth_env` (pre-existing, unchanged by this revision). Did NOT sign, did NOT
run any model/GPU/Modal work, did NOT touch the 3090 or the synaptic-tuner
submodule. Predictions scoreboard left blank for the lead to fill at sign.

### 2026-07-09 -- tokenizer/config verification pass (CPU-only, no GPU work run)

Resolved LAUNCH-PLAN.md decision points #3 (multimodal config nesting), #4
(EOS lists + layer counts), and #5 (Gemma system-role support) by
downloading ONLY `config.json`/`tokenizer_config.json`/
`special_tokens_map.json`/`generation_config.json`/`chat_template.jinja`
per checkpoint via `hf_hub_download` (never `snapshot_download`, no
`*.safetensors`/`*.bin` touched) for all four checkpoints:
`unsloth/Llama-3.2-3B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.3`,
`Qwen/Qwen3.5-4B`, `google/gemma-4-E4B-it`. All four repos were ungated
(no 403s). Fetch script and cached files live under this experiment's
gitignored `analysis/tokenizer-config-verify/` (fetch script:
`fetch_configs.py`; not tracked, upstream artifacts only).

Also ran a small number of meta-device (`torch.device("meta")`, no weight
download, no GPU) `AutoModelForCausalLM`/`AutoModelForImageTextToText`
construction checks against the downloaded configs to directly test the
multimodal loader-class questions LAUNCH-PLAN.md flagged as unverified
(`attn_implementation="eager"` acceptance, and whether the vision/audio
towers are structurally part of the resolved model class) -- no weights
were downloaded or instantiated with real data for this.

Confirmed: Llama's `n_hidden_layers: 28` guess, Mistral's/Qwen3.5's EOS
guesses, and Qwen3.5's `nested_text_config: true` + `enable_thinking`
kwarg. Filled in previously-`null` layer counts for Mistral (32), Qwen3.5
(32, nested), and Gemma4 (42, nested), each with a recomputed
`round(0.9444 * n_hidden_layers)` late-reference estimate.

Corrected two factually wrong guesses for `google/gemma-4-E4B-it`: (1) its
EOS/end-of-turn token is `<turn|>` (per `tokenizer_config.json`'s own
`eot_token` field and the live chat template), not the classic Gemma
2/3 `<end_of_turn>` the draft assumed; (2) it DOES have a native
`enable_thinking` kwarg (gates a `<|think|>` token injection), contrary to
the draft's "Gemma has no thinking-toggle kwarg" claim. Also resolved
decision point #5 in the affirmative (its template gives `system` its own
turn, not folded into the first user turn -- the flagged concern was
unfounded for this checkpoint) and found it is trimodal (vision + audio
towers, not vision-only) -- both AMENDMENT.md's family table and
`families/gemma4-e4b.yaml` were updated to flag these corrections
prominently. Full detail in each `families/<slug>.yaml`'s per-section
"VERIFIED"/"CORRECTED" notes and LAUNCH-PLAN.md's revised decision points
#3/#4.

Did NOT touch decision point #1 (G3 floor) or the VRAM GB estimates in the
feasibility table (lead-kept); did NOT sign, did NOT run any model
generation, did NOT touch the local 3090.

### 2026-07-09 -- draft scaffold written (no GPU work run)

Scaffolded via `bin/exp new --type steer-cell j-space-cross-family-layer-contrast`
on branch `exp/j-space-cross-family-layer-contrast` (worktree
`/home/profsynapse/code/ehr-worktrees/jspace-cross-family`). Read the six
governed docs the lead named (two Qwen3-4B J-space predecessors, the
localization diagnostic + its NOTEBOOK.md, Amendment Z, and the
doubt-gated-caution-tighten gate-and-snap origin) before writing any code, per
the KG-search-first / read-before-you-cite rule.

Wrote per-family config YAMLs (`families/{llama-3.2-3b,ministral-3-3b,qwen35-4b,gemma4-e4b}.yaml`)
transcribing Amendment Z's exact checkpoints, run order, and per-family
loader/VRAM risk notes verbatim, with `band_selection` and `doses` left
`not_yet_run`/`not_yet_calibrated` (no profile or calibration has executed).

Ported the two Qwen3-4B J-space experiments' bespoke scripts into
family-parameterized versions (`mine_eval_pool.py`, `split_fit_heldout.py`,
`jlens_profile.py`, `extract_anchor.py`, `build_directions.py`,
`gate_fit.py`, `calibrate_dose.py`, `pipeline.py`, `run_contrast.py`,
`cross_family_rollup.py`), plus `family_config.py` as the single read/write
path for each family's YAML (no other script hardcodes a checkpoint, hidden
size, or layer index) and `model_lib.py` porting Amendment Z's own loader
hardening (`AutoModelForCausalLM` -> `AutoModelForImageTextToText` ->
`AutoModelForVision2Seq` fallback chain, `config.text_config` nesting).
`gen_lib.py` and `grader.py` are the generation-contract and grading code,
generalized (EOS resolution) or ported unchanged (grading is already
model-agnostic).

Verified every script with `py_compile` and `--help` (CPU-only, unsloth_env
conda python) -- no model loads, no GPU touched, per the lead's explicit
instruction that the local 3090 is busy with another experiment's
confirmatory and must not be touched at all.

Did NOT run `bin/exp sign` (prediction/falsifier/gates need the lead's
review and the scoreboard rows need the lead + user's calls first). Did NOT
run any HF pull, Modal launch, or GPU work. See `LAUNCH-PLAN.md` for the
per-family run order, GPU-time estimates, and the decision points that need
to come back to the lead before this experiment can launch for real.
