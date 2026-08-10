# caution-install-bounded-site-sweep notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-10T16:15Z - Lead review of the materialization script; pinned into the instrument

Lead review of `materialize_rows_with_text_raw_base.py` (entry below):

- Verbatim-port claim verified against
  `j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py`: loader
  control flow (filter conditions, dedupe, idx increment placement) is
  identical; the port drops only the `label` and `_nq` dict fields, which do
  not affect row_key assignment or question resolution. `norm_q` matches
  `j-space-cross-family-layer-contrast/scorers.py:norm_question` character
  for character (same HIR-prefix regex, same transforms).
- Determinism re-verified by lead rerun: identical output sha256
  `78ed2041ccde4db8ddca2b23d53c70ba1e49b5b21bb8392a2776d7815e4b4f16`,
  preflight still exit 0.
- Containment verified: output written only under gitignored `analysis/`,
  fatal paths print row_keys only, summary prints counts and sha only.
- One wording fix in the docstring (prose-hygiene term), no logic change.
- Pinned into `experiment.yaml` (`instrument.modules` + `pins` +
  `persistence`, sha256 `04726d66aa399a15a8ca0848bf714444e68ac5dec142beb6a618e02868e51c94`)
  with a repin audit entry: new staging module added post-signing, pre-run;
  pure input staging, no gate quantity or protocol constant involved.
  `bin/exp validate` OK.

### 2026-08-10T15:52Z - Launch-prep materialization complete: preflight green (exit 0)

Per PR #430's launch-prep list, items 1-3. CPU only; no GPU verbs, no docker
run, no commits (per instruction). Canonical checkout
`/home/profsynapse/code/Epistemic-Humility-Research`, branch `main`.

- **Item 1, expansion corpus, PRESENT**: F16's expansion corpus
  (`mine_pool.EXPANSION_CANDIDATES`) --
  `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl` -- confirmed
  present in this worktree (13,496 lines, gitignored). No action needed.

- **Item 2, `analysis/rows_with_text_raw_base.jsonl` materialized**: new
  script `materialize_rows_with_text_raw_base.py` (gitignored output, tracked
  script) deterministically reconstructs question text for all 221 row_keys
  in rep2's committed raw_base anchor pool
  (`experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/
  multisource_pool_manifest.json`), which is ID/role/source/category_canon
  only per rep2's own containment policy and carries no text.

  Join method: rep2's mining script
  (`j-space-layer-contrast-rep2-multisource/mine_multisource_pool.py`) builds
  each row_key as `msrc::<source>::<idx>`, where `idx` increments only over
  candidates from the three original dataset loaders (`datasets/kuq/
  knowns_unknowns.jsonl` unknown=true, `datasets/kuq/unknowns_all.jsonl`
  deduped, `datasets/selfaware/SelfAware.json` answerable=false) that survive
  a dual-exclusion filter (against the predecessor fit/held-out split and
  rep1's fresh pool, resolved to question text via two private candidate
  caches). This script verbatim-ports `resolve_excluded_questions`,
  `load_kuq_ku_unknown`, `load_kuq_ku_unknown_x`, and
  `load_selfaware_unanswerable` from that source script (norm_question is the
  same HIR-prefix-stripping normalizer already verbatim-ported into this
  experiment's own `probe_common.py`), reading the same git-tracked dataset
  files plus the two private exclusion-resolution caches at their migrated
  locations in this checkout (`experiments/divergent-pool-own-readout/
  analysis/phase1-migrated/probe/analysis/ah_stage0/candidates.jsonl` and
  `.../expansion/expansion_candidates.jsonl`, the same file as item 1).

  Because idx assignment only increments for candidates that survive
  exclusion, an incomplete exclusion set would silently misalign every
  downstream row_key. Guarded against this: the script recomputes
  `exclusion_resolution_counts` and hard-fails unless it matches rep2's own
  manifest-recorded counts EXACTLY (`predecessor_split_keys=739,
  rep1_pool_keys=2263, union_keys=3002, resolved_to_question=3002,
  unresolved_keys=0`) -- it did, on the first run, meaning the 166 `ah::`
  keys resolved via the migrated `candidates.jsonl` matched rep2's original
  resolution exactly, not just the more numerous `ahx::` keys. Additional
  hard-fail cross-checks, all passed: reconstructed `source` matches the
  manifest's `source` for every row_key; reconstructed `category_canon`
  matches the manifest's `category_canon` for every row_key (a genuine
  content check, not just an id match); per-source counts
  (kuq_ku_unknown=139, kuq_ku_unknown_x=6, selfaware_unanswerable=76) match
  `manifest["counts"]["selected_confab_by_source"]` exactly; zero empty
  question text; all 221 resolved (zero missing). No sampling -- all 221
  row_keys included deterministically every run.

  **Materialized file**: `analysis/rows_with_text_raw_base.jsonl` (gitignored
  per this experiment's `.gitignore` `analysis/` entry, confirmed via `git
  check-ignore -v`). 221 rows, 221 unique row_keys, every row `role:
  "confab"`, zero empty `question` fields. Fields:
  `{row_key, role, question, aliases, source, category}`, matching the
  schema `mine_pool.py` writes for the trained substrate's
  `rows_with_text.jsonl` so `extract_anchor.py`/`dose_calibrate.py` read one
  shape regardless of substrate. sha256
  `78ed2041ccde4db8ddca2b23d53c70ba1e49b5b21bb8392a2776d7815e4b4f16`. No row
  text (question or otherwise) appears in this notebook entry or elsewhere
  in a tracked path.

- **Item 3, preflight**: `python3 run_sweep.py preflight` now exits 0
  (`{"ok": true, "problems": []}`), both checks it runs (F16 corpus staged;
  `rows_with_text_raw_base.jsonl` covers all 221 registered row_keys with
  `role: "confab"`) satisfied by items 1-2 above. No harness code changed to
  reach this; both preflight checks were already correctly implemented
  (Round 3's `ALSO(a)`) and simply had nothing to check against until now.

- **No harness defect observed** this pass. `git status` over the touched
  and read experiment directories shows only the new tracked script
  (`materialize_rows_with_text_raw_base.py`) as untracked; the materialized
  `analysis/` output is gitignored and does not appear. No commits made.

### 2026-08-10T21:10Z - Round 4: raw_base gate-params handoff fix (tau/mu_d/sigma_d import), stray artifact cleanup. CPU smoke re-passed.

Follow-up to the 2026-08-10T18:45Z Round 3 entry, per lead adjudication of
the delta verify's one blocker and two minors. No git operations; CPU only.

- **Governed-text note (lead action, no code change here)**: the lead
  corrected the g0b quantity wording in `gates.yaml` and `AMENDMENT.md` to
  the cache-condition-invariance quantity (matching the Round 3
  `run_seam_check` implementation, which was already correct against the
  lead's Round 3 instruction but not yet against the governed text) and
  repinned `gates.yaml` (new sha256
  `ea176dac3635efd54cd346949da776db4f0996ef6570a5a950c03bf2e252a93d`,
  `experiment.yaml` repins block, dated 2026-08-10T15:18:14Z). No seam-check
  code changed this round; the implementation now matches the governed text
  it was already anticipating.

- **BLOCKER, RESOLVED -- raw_base gate-params handoff**: `run_import_raw_base`
  wrote `provenance.mu_d_over_fit_pool` / `sigma_d_over_fit_pool` (the
  source amendment's own spelling) and no `tau` at all, but
  `gate_scoring.load_gate_params` (the shared reader, left unmodified per
  instruction) reads canonical `provenance.mu_d` / `sigma_d` and
  `manifest["sites"][site]["tau"]` -- a KeyError waiting for Stage 6/8 to
  hit it on raw_base. Fixed on the import side only:
    - `build_directions.run_import_raw_base` now maps the source's
      `mu_d_over_fit_pool` / `sigma_d_over_fit_pool` onto canonical
      `mu_d` / `sigma_d` in the WRITTEN u_d copy's provenance (source
      spellings kept alongside, not replaced); hard-fails if the source
      fields this mapping depends on are absent.
    - Added `sweep_lib.raw_base_gate_fit_params(site)`: imports `tau`
      (`tau_frozen`, Youden-J) from the SAME source amendment's own
      `experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/gate_fit_layers.json`
      (already G0d-gated there), hard-failing on a missing/malformed file
      or a missing/mismatched per-site entry; records that file's sha256 in
      manifest provenance too. `raw_base_direction_import` now returns
      these fields, and `run_import_raw_base` writes `tau` /
      `tau_frozen_method` / `gate_fit_source_path` / `gate_fit_sha256`
      into each site's `build_gate_manifest.json` entry.
    - **Live-driven, not just unit-tested**: ran the REAL
      `build_directions.run_import_raw_base` followed by the REAL
      `gate_scoring.load_gate_params("raw_base", "hs23"/"hs29")` end to
      end, both COMMITTED/DIRECTIONS_DIR redirected to a tempdir (never
      touching the tracked/gitignored real paths). Both sites resolved with
      no KeyError:
      hs23: u_d.shape=[2560], mu_d=-4.706120, sigma_d=3.841707,
      tau=0.139240 (tau_frozen_method=youden_j);
      hs29: u_d.shape=[2560], mu_d=1.535061, sigma_d=10.566303,
      tau=0.120912 (tau_frozen_method=youden_j). tau values match the
      lead's cited quotes exactly (hs23 0.13924013495876808, hs29
      0.12091211815721492), re-read from the source file, not hardcoded.
      g0_overall_pass True (g0c reproducible, g0d AUC>=0.90 both sites).

- **Minor #1, RESOLVED**: `sweep_lib._load_direction_json` now checks
  vector dimensionality (== 2560, Qwen3-4B hidden_dim) and that every entry
  is numeric and finite (extended slightly past the literal "numeric
  entries" ask to also reject NaN/Infinity, since a non-finite entry is
  technically still a Python float and would otherwise pass a bare type
  check -- flagged here in case a narrower reading was intended).

- **Minor #2, RESOLVED**: `g0d_note` now interpolates the actual measured
  source AUC (`auc_neg_z_d_on_fit`) it references instead of pointing at
  the source file without quoting a number. As a direct consequence,
  `g0d_pass` is now computed from that real value (`>= 0.90`, the same
  registered floor used elsewhere) rather than hardcoded True -- both sites
  still read True (hs23 AUC 0.9905, hs29 AUC 0.9984), so this round's
  behavior is unchanged, but the gate is no longer a rubber stamp.

- **Stray artifact cleanup**: deleted the two tracked pre-run artifacts
  Round 3's live tests left behind (`analysis-committed/gate_report.json`,
  `analysis-committed/raw_base/build_gate_manifest.json`) -- premature
  outputs from CPU verification, not real run evidence. This round's
  re-drive test wrote only to a tempdir (see above); `git status` confirmed
  clean before this report (only source `.py`/`.md` modifications and the
  pre-existing untracked harness scripts, no stray artifacts).

CPU smoke (`python3 run_sweep.py --smoke-harness`) re-ran clean after this
pass: exit 0, `gpu_touched: false`, `cleaned_up: true`. No threshold, band,
count, seed, or gate definition was changed; the fix repairs the import's
handoff to `gate_scoring.load_gate_params`, which itself was left
unmodified per instruction.

### 2026-08-10T18:45Z - Round 3: seam-check correction (BLOCKER #9), raw_base directions import (BLOCKER #8), four new defects, preflight subcommand. CPU smoke re-passed.

Follow-up to the 2026-08-10T14:30Z wiring-pass entry, per lead adjudication of
the verify re-review's two blockers and four new defects. No git operations;
CPU only.

- **BLOCKER #9, RESOLVED (regression, not incremental)**: the prior seam-
  continuity check (`extract_anchor.py compute_seam_continuity`) measured
  cosine between ADJACENT hidden-state layers within one forward pass --
  the wrong quantity; real residual streams never approach the registered
  0.999 floor between adjacent layers (re-reviewer measured min 0.043 on
  healthy committed data, hard-stopping Stage 2 on GOOD data). The
  REGISTERED quantity is cache-condition invariance of the SAME hidden
  state: min cosine between the SAME row's SAME hidden state, captured
  twice via direct `transformers` forward calls
  (`output_hidden_states=True`), once `use_cache=True` and once
  `use_cache=False`, never routed through the tuner's capture path (which
  hardcodes the flag). Replaced with `select_seam_check_rows()` (seeded,
  fixed 32-row subset, `random.Random(f"{seed}:seam_check")`),
  `seam_cosine_between_runs()` (pure math, CPU-testable), and
  `run_seam_check()` (the two forward calls, reusing the already-loaded
  model/tokenizer). Floor unchanged at 0.999. CPU-smoke-tested the
  comparison math on synthetic tensors: identical-vectors case gives
  min_cos ~1.0 (passes); a deliberately perturbed layer is correctly
  identified by both value and layer index; `select_seam_check_rows`
  called twice on the same input is deterministic. GPU execution (the real
  Qwen3 forward passes) happens at launch, per instruction -- Qwen is an
  unaffected family so this should read ~1.0 there; a failure would be a
  real red flag, not an artifact of the old wrong-quantity check.

- **BLOCKER #8, RESOLVED**: "a paired replication reuses the replicated
  operating point; it never refits." raw_base's Stage 3
  (`build_directions.py`) no longer fits anything -- it IMPORTS hs23/hs29
  `c_hat`/`u_d` unchanged from `j-space-midband-write-sweep-qwen3-4b`'s own
  committed, already-gated artifacts
  (`experiments/j-space-midband-write-sweep-qwen3-4b/analysis-committed/layers/{hs23,hs29}/{c_hat,u_d}_hs{23,29}.json`).
  Added `sweep_lib.raw_base_direction_import()`: loads and validates each
  file (schema_version == mechinterp-direction/v1, non-empty vector,
  provenance.hs_index matches the requested site), hard-fails (RuntimeError)
  on any missing or malformed source; live-tested both hard-fail paths
  (missing file, hs_index mismatch) plus the real import. `build_directions.py`
  now branches to `run_import_raw_base()` for raw_base, which writes the
  imported records (unchanged, plus an `import_provenance` block recording
  source path/sha256/identity) to `directions/raw_base/<site>/{c_hat,u_d}_<site>.json`
  and a `build_gate_manifest.json` reporting `mode: "imported"` with G0c/G0d
  marked N/A-imported (not silently defaulted to pass -- G0c is verified by
  re-reading and comparing sha256, G0d notes the source amendment's own
  gate already governs). Live-ran against the real committed artifacts:
    - `c_hat_hs23.json` sha256 `50c3b580d7077ae4c5ee4496aa075e9158ae57fd168961f3d1854cddce7f1a72`
    - `u_d_hs23.json` sha256 `3565c8a16670f7fe3542cd1e26ee66bc451e08f2e40718f6ea8e26f86cb0672b`
    - `c_hat_hs29.json` sha256 `e6872569423e8cca31a61c857d27a3a89e89aa5f7061924c9ce21faa672bf692`
    - `u_d_hs29.json` sha256 `8cebdf90ccf76ada347592a6f8ab7514fb5d8a75468ec091fde8c03805e9faf6`
  Lead: these four paths need adding to `experiment.yaml` `inputs:`/pins (not
  done by this pass -- experiment.yaml is the lead's own edit per the Round
  2 convention).

- **NEW DEFECT #1, RESOLVED**: `adjudicate_gates.g3_direction_specificity`'s
  `pass` now additionally requires `gated_lift > 0 AND max_draw_lift > 0`
  (guard, not a new threshold) -- a negative-lift arm can never represent
  direction-specific installation. CPU-smoke-tested with a synthetic case
  (negative gated_lift, negative max_draw_lift, numeric ratio >= 3.0 by
  sign cancellation) confirming the guard blocks the pass the old code
  would have granted.

- **NEW DEFECT #2, RESOLVED**: a non-finite ratio (only reachable when
  max_draw_lift == 0) now serializes as the string sentinel `"inf"`/`"-inf"`
  plus an explanatory `ratio_note` field, never bare JSON Infinity.
  `sweep_lib.write_json` now passes `allow_nan=False` to `json.dumps`
  globally, raising a clear `ValueError` naming the target path if any
  caller ever tries to write a non-finite float unsanitized. CPU-smoke-
  tested both: the g3 sentinel path, and `write_json` rejecting
  `float('inf')` / `float('nan')` directly.

- **NEW DEFECT #3, RESOLVED**: `run_sweep.py`'s smoke-harness G3 assertion
  no longer re-implements the lift/ratio/guard math inline; it now calls
  `adjudicate_gates.g3_direction_specificity(substrate, ctrl=..., ho=...)`
  directly on in-memory dicts shaped like the worked example (RG1 section
  5.1: gated lift +40.9pts, draws +13.3/-7.4/+21.8pts, ratio ~1.87x FAIL),
  via a new optional `ctrl`/`ho` parameter pair on that function -- keeps
  the smoke's "never touches real analysis-committed/*" invariant (no disk
  I/O) while eliminating the second, driftable copy of the gate math.
  Re-ran the full `--smoke-harness`: ratio reproduces 1.8716 (FAIL), exit 0,
  `gpu_touched: false`.

- **NEW DEFECT #4, RESOLVED**: `AMENDMENT.md`'s status line no longer reads
  "may now launch as confirmatory-tier-2 evidence" (wrong -- this cell is
  registered Tier 2 EXPLORATORY, not confirmatory). Reworded to match the
  body's own registration: signed, may launch per its gates; Tier 2
  EXPLORATORY, results reported separately from the locked headline matrix
  and never pooled with it, a positive result is a lead requiring a
  confirmatory replication registered before running it.

- **ALSO(a), RESOLVED**: added `run_sweep.py preflight` (dedicated
  subcommand, checked before the flag-based CLI schema). Checks (1) F16's
  expansion corpus (`mine_pool.EXPANSION_CANDIDATES`) is staged into the
  worktree, (2) `analysis/rows_with_text_raw_base.jsonl` covers all 221 of
  rep2's registered raw_base anchor pool row_keys AND each carries
  `role: "confab"` specifically, not just row_key presence. The same role
  check was added to the existing hard-fails in
  `extract_anchor.py._raw_base_joined_rows` and
  `dose_calibrate.py.calibration_pool` (previously checked row_key presence
  only). Live-ran `preflight` against this worktree's current (unstaged)
  state: correctly reports both problems by name, exit 1.

- **ALSO(b), RESOLVED -- G4 overlap disclosure, made pre-run**:
  `adjudicate_gates.g4_substrate_anchor` now computes and reports
  `dose_selection_overlap`: the count and fraction of raw_base rows that
  are BOTH dose-selected-on (`dose_calibrate.py`'s calibration pool, first
  `n_confab_fit_rows` row_keys sorted) AND scored in G4's denominator (the
  full rep2 221-row pool), computed from `cell.yaml`
  `dose_ladder.calibration_pool.n_confab_fit_rows` and
  `sweep_lib.raw_base_anchor_pool()` rather than hardcoded -- live-computed
  as 24/221 = 10.9%, matching the re-reviewer's measurement exactly.
  **Two-sided caveat, disclosed here pre-run**: raw_base has no registered
  FIT/HELD-OUT split, so this overlap is structural, not a bug to fix
  before launch -- but it means the 24 dose-selected rows are not held out
  from G4's evaluation population. This can bias the observed rate EITHER
  toward OR away from the reference Wilson interval (dosing at calibration
  time could shift those 24 rows' own downstream confab rate in either
  direction relative to the other 197), not exclusively toward a false
  containment pass. The write-up must state this disclosure, not treat a
  G4 PASS as unqualified.

CPU smoke (`python3 run_sweep.py --smoke-harness`) re-ran clean after every
change in this pass: exit 0, `gpu_touched: false`, `cleaned_up: true`. No
threshold, band, count, seed, or gate definition was changed; every fix
repairs the instrument's implementation of the design already registered in
`AMENDMENT.md`/`cell.yaml`/`gates.yaml`.

### 2026-08-10T14:30Z - Final wiring pass: F8 resolved per G4 (rep2 pool), F25 resolved by repin + assertion. CPU smoke re-passed.

Follow-up to the 2026-08-10T00:00Z remediation entry, per lead adjudication
of the two gaps that entry reported unresolved. No git operations; CPU only.

- **F8, RESOLVED** (was reported-unresolved): the lead read AMENDMENT.md's
  G4 block precisely -- there is no missing raw_base mining stage; the
  registered raw_base anchor population IS rep2's 221-row multi-source
  held-out confab pool
  (`experiments/j-space-layer-contrast-rep2-multisource/analysis-committed/
  multisource_pool_manifest.json`), the same pool G4 cites for the hs23/
  hs29 reference rates. Added `sweep_lib.raw_base_anchor_pool()`: loads that
  manifest, cross-checks its confab count against the SAME experiment's
  independently-written `full_summary.json` (both read 221; verified live
  against the real committed artifacts, not just unit-tested), hard-fails
  on any mismatch or missing file, and returns provenance (manifest sha256
  c7ccbb980ba8e9788386d69c4338f71c4ab117960fb0eea58011c1507508c456,
  identity string). `extract_anchor.py`'s `_raw_base_joined_rows()` and
  `dose_calibrate.py`'s `calibration_pool()` now source raw_base's confab
  rows from this verified pool (all `split="held_out"`, matching rep2's own
  no-internal-split methodology) instead of the old blanket "no mining
  stage" error. `extract_anchor.py` records the pool's sha256 + identity
  string into that substrate's `manifest.json`, satisfying G4's "record
  which raw-base pool it ran on."
  **Residual gap, reported not silently closed**: rep2's committed manifest
  is deliberately ID/role-only (its own containment policy) -- it carries
  no question text. `rows_with_text_path("raw_base")` still needs to be
  populated with real text for these exact 221 row_keys before a GPU stage
  can run; both call sites now verify this precisely (naming exactly which
  of the 221 registered row_keys are missing text) rather than erroring
  vaguely. Live-tested this hard-fail path against the real repo state
  (text file absent): correctly names 221/221 missing, first 5 row_keys.
  **Design call flagged for lead review**: `dose_calibrate.py`'s raw_base
  calibration pool draws its confab side from the SAME 221 rows the anchor
  arm will later evaluate at Stage 6 (no separate FIT subset), since
  raw_base has no registered FIT/HELD-OUT split and rep2's own methodology
  didn't split this pool either; known_correct_answered has no registered
  raw_base source, so `known_correct_cost` reads a fixed, harmless 1.0
  tiebreaker for every rung. Flag if a different reading was intended.
- **F25, RESOLVED** (was reported-unresolved): the lead corrected
  `cell.yaml` substrates[0] (trained) `base_model` from the raw lineage
  repo (`unsloth/Qwen3-4B`) to the actual GPU-verified load target
  (`professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit` @
  `ac361232c001af0ed5b0386b06dafc35d5cd31ea`) and ran `bin/exp repin` (new
  cell.yaml sha256
  b118c1c4a045ca3230dbe8260f0a1d4e43929c0a81abff842352303cf47fb0c2, recorded
  in `experiment.yaml`'s `instrument.repins` block). `sweep_lib.py`'s
  `base_repo_and_revision()` no longer special-cases the trained substrate
  with a hardcoded return; it now reads (repo, revision) directly from
  `cell.yaml`'s substrates block for BOTH substrates (via the same
  `substrate_config()` every other call site uses), and asserts the trained
  substrate's cell.yaml values still equal the GPU-verified recipe
  (`TRAINED_BASE_REPO_VERIFIED`/`TRAINED_BASE_REVISION_VERIFIED`), failing
  loudly if a future cell.yaml edit silently drifts from what was actually
  verified to load. Live-tested against the real repinned cell.yaml: both
  substrates resolve correctly, assertion passes.
- `experiment.yaml`'s `inputs:` gained the F16 corpus path
  (`experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl`) and the two
  rep2 artifacts this pass reads (`multisource_pool_manifest.json`,
  `full_summary.json`). Bookkeeping only, not a re-sign.

**Verification.** `python3 run_sweep.py --smoke-harness` (all 4 CPU-only
phases) exits 0. Every `.py` file in the directory re-parses cleanly. The
four pinned instrument modules were re-hashed and still match
`experiment.yaml`'s `instrument.pins` exactly. `raw_base_anchor_pool()` and
the F25 assertion were both exercised live against the real committed
artifacts and real repinned `cell.yaml` in this worktree (not just
syntax-checked), confirming both the success and hard-fail paths behave as
documented.

### 2026-08-10T00:00Z - Red-team remediation (item 27): instrument repairs, pre-data. CPU smoke re-passed.

Harness-level fixes to implement the SIGNED design as registered, per the
red-team findings report. No registered threshold, band, count, seed, gate
definition, or falsifier changed. No data existed yet; these are pre-read
instrument repairs. Per-finding, terse:

- **F1/F13** (G3 lift math): `adjudicate_gates.py` `g3_direction_specificity`
  and `run_sweep.py`'s `--smoke-harness` Phase 4 mirror both previously
  computed a raw-rate ratio (`gated_rate / draw_rate`, no baseline
  subtraction). Rewritten to the registered RG1 criterion: per-cell lift =
  rate minus that SAME cell's own undosed baseline, for `gated` and for each
  of >=3 fresh draws; ratio = gated_lift / max(draw_lift). Smoke now asserts
  the corrected formula reproduces the RG1 worked example
  (read-then-actuate.md 5.1): ratio ~1.87-1.88, FAIL -- not the old bug's
  spurious PASS shape.
- **F2** (mine_pool.py question/category source): generation records
  verifiably carry no question text (`probe_stage_b.py`,
  `probe_census_extension.py` write only
  `{row_key,label,source,completion,n_new_tokens,terminated_naturally,
  **grade}`). DEVIATION from the literal instruction ("take from the
  generation record itself"): sourced from the full expansion-candidates
  corpus (`load_all_candidates()`), which does carry question/aliases/
  category per row_key, instead. Hard-fails (nonzero exit, no partial pool
  file) if any selected row still has empty question text. Counts/
  stratification unchanged.
- **F3** (docker_launch.sh image substitution): rewrote to resolve+run
  `unsloth/unsloth@<cell.yaml execution.runtime_image_digest>` by digest,
  exit 1 if not locally present, never substitutes mechinterp-runner. The
  prior script read the pin only to print a WARNING on mismatch while
  actually launching `mechinterp-runner:local` by tag.
- **F4**: single `load_split_manifest` helper added to `sweep_lib.py`
  (`json.loads`, not `load_jsonl` which mis-parsed the pretty-printed
  manifest object as JSONL and crashed 5 downstream consumers).
- **F5**: `mine_pool.py` gained `--substrate` (required) and
  `--i-know-this-runs-on-gpu`. `split_fit_heldout.py` registered as its own
  Stage "1b" in `run_sweep.py`'s STAGES dict (string keys, new STAGE_ORDER
  list), between mining (1) and extraction (2).
- **F6**: `install_pinned_loader` gained an optional `base_revision` param,
  bound via `functools.partial` only when passed. Threaded through
  `dose_calibrate.py` (whose `run_dose_calibration` has no `revision`
  parameter at all) without touching the tuner submodule or colliding with
  `run_steer` call sites, which already pass `revision` as a third
  positional.
- **F7**: `dose_calibrate.py` readback check rewritten so a MISSING
  `readback_measured`/`readback_commanded` (unmeasured row) fails, not
  vacuously passes via `or`'s short-circuit on `None`.
- **F8**: raw_base gets its own harness-internal (non-pinned, gitignored)
  `rows_with_text_path`/`split_manifest_path` via `sweep_lib.py`; consumers
  fail loudly rather than silently reusing the trained pool. cell.yaml's
  singular `surface.rows_path`/`surface.split_manifest` pins are untouched
  (hash-pinned) and remain implicitly trained-only, matching Stage 1's
  registered scope. UNRESOLVED GAP (reported, not silently closed): no
  registered mining stage exists anywhere in AMENDMENT.md's Run Plan for
  raw_base -- its anchor-pool POPULATION mechanism needs a lead design
  decision before Stage 2+ can run for raw_base. extract_anchor.py and
  dose_calibrate.py both raise a loud, substrate-aware error naming this gap
  rather than resolving it.
- **F9**: `extract_anchor.py` gained `compute_seam_continuity()` -- min
  cosine between consecutive hidden-state-index captures, over every
  extracted row -- persisted into that substrate's `manifest.json` and read
  into `adjudicate_gates.py`'s `g0_integrity` as
  `g0b_seam_continuity_<substrate>`. Previously never computed anywhere
  despite the docstring claiming it was.
- **F10**: `adjudicate_gates.py`'s `g0f_containment` was a hardcoded string.
  Replaced with a real recursive scan of every `.json`/`.jsonl` file under
  `analysis-committed/` for the row-text field names verified present in
  this harness's own producers (question, aliases, answer_text, completion,
  prompt, generation).
- **F11**: `adjudicate_gates.py`'s `g4_holding` used `all()` over a
  filtered generator that silently returns `True` when empty (e.g. every
  raw_base anchor cell NOT_RUN). Fixed to report
  `"UNKNOWN_no_ran_anchor_cells_instrument_void"` instead of a vacuous pass.
- **F12**: `run_held_out.py`'s `summarize_cell()` now persists BOTH the full
  held-out population rate and the fired-only rate (both numerators/
  denominators) for `known_correct_answered_held_out`.
  `adjudicate_gates.py`'s `g2_selectivity` implements gates.yaml's
  headline_rule literally: fired-only rate is the headline exactly when it
  exceeds the cap while the full-population rate passes; otherwise
  full-population is the headline. Measurement only, no new threshold.
- **F14**: `run_pairs.py` now verifies readback at BOTH pair members
  against the registered `dose_ladder.readback_tolerance` per row
  (`readback_a_within_tol`/`readback_b_within_tol`), and aggregates
  `frac_readback_within_tol` into each position's summary.
- **F15**: `run_pairs.py`'s generation call now uses `**gen_kwargs` from
  `MechInterp.cli._generation_kwargs(tokenizer, GenerationContract(...))`,
  the same generation-kwargs contract every other stage script uses,
  replacing manually duplicated `max_new_tokens`/`min_new_tokens`/
  `do_sample`/`num_beams`/`return_dict_in_generate` kwargs.
- **F16**: `mine_pool.py`'s hardcoded machine-local
  `CANONICAL = Path("/home/profsynapse/code/Epistemic-Humility-Research")`
  replaced with a repo-root-relative `EXPANSION_CANDIDATES` path (via
  `sweep_lib.REPO_ROOT`), working both on host and under the container's
  `/workspace` mount. Resolved path for the lead to pin at experiment.yaml:
  `experiments/divergent-pool-own-readout/analysis/phase1-migrated/probe/
  analysis/ah_stage0/expansion/expansion_candidates.jsonl`.
- **F17**: added `sweep_lib.emit_provenance_line()`, called once from
  `install_pinned_loader()` (the shared choke point every GPU-verb script
  already calls before any model load), printing one provenance JSON line
  (runtime_image_digest, python/torch/cuda versions) to stdout, which
  `launch_detached.sh`/`docker_launch.sh` already redirect into the run
  log. `unsloth/unsloth:latest --entrypoint python3` overrides
  mechinterp-runner's own `print_provenance.py` entrypoint, so this
  Python-side emission is the correct fix, not a shell-side one.
- **F18**: `docker_launch.sh` rewritten for detached launch: dropped `-it`,
  added a deterministic `--name`, `--ipc=host`, and corrected the HF cache
  mount to `/home/unsloth/.cache/huggingface` with `HF_HOME`/
  `HUGGINGFACE_HUB_CACHE` set explicitly (the image runs as non-root uid
  1001, home `/home/unsloth`; the old `/root/.cache/huggingface` mount was
  silently unreachable by the container's own HF client).
- **F19**: `AMENDMENT.md`'s status line corrected from "DRAFT (not signed)"
  to reflect `experiment.yaml`'s actual state: `status: signed`,
  `sign_blocked_on: 'CLEARED 2026-08-09T02:10Z: P2/P3/P4 passed at the
  probe ... P1 satisfied by count under the pre-stated census criterion ...
  Signing authorized.'`. `cell.yaml`/`gates.yaml` untouched (hash-pinned;
  their `# DRAFT` header comments are inert prose, not machine-read).
- **F20**: `build_directions.py` now reloads each written u_d/c_hat JSON via
  `json.loads(path.read_text())["vector"]` and compares `np.array_equal`
  against the in-memory array; `g0c_pass` requires both the two-fit
  reproducibility check AND this roundtrip check.
- **F21**: `build_random_directions.py` now reads
  `max_abs_cos_vs_c_hat`/`max_abs_cos_vs_u_d` from `gates.yaml`'s
  `g3_direction_specificity.draw_hygiene_sc1` (previously loaded via
  `load_gates()` but never used -- a hardcoded `MAX_ABS_COS = 0.015`
  constant was used instead).
- **F22**: `mine_pool.py`'s `--target-known-correct` default is now derived
  (`math.ceil(REQUIRED_TOTAL_KNOWN_CORRECT * 1.10)` = 459) from the
  registered floor and a named 10% margin constant, not a bare hardcoded
  `460`.
- **F23**: `write_smoke.py`'s `cell_ok` now also requires
  `frac_within_tol == 1.0` (gates.yaml g0e_write_readback's actual pass_if),
  not just the tuner's own coarser all-or-nothing `passed` boolean.
- **F24**: local `.gitignore` gained `generated/` (claimed gitignored by
  `materialize_configs.py`'s own docstring but never actually entered) and
  `analysis-committed/_smoke_harness/` (the one committed-tree namespace a
  `--smoke-harness --keep-smoke-artifacts` run writes into). No leftover
  smoke artifacts were found on disk at fix time.
- **F25** (trained-base repo/revision, UNRESOLVED, flagged not silently
  resolved): `sweep_lib.base_repo_and_revision()` now prints a loud
  "UNRESOLVED-F25" warning (both identifiers) the first time it resolves
  the "trained" substrate's base repo/revision, so a real run's log
  visibly carries this open question instead of masking it. Investigation
  and lead recommendation are in the delegation's final report, not
  repeated here.
- Also fixed (same bug class as F8, not separately numbered):
  `write_smoke.py`'s `probe_rows()` was hardcoded to always read the
  trained substrate's `rows_with_text.jsonl` regardless of `--substrate`;
  now uses `sweep_lib.rows_with_text_path(substrate)`.

**Verification.** `python3 run_sweep.py --smoke-harness` (all 4 CPU-only
phases: pool construction, site iteration, checkpoint/resume, report
generation) exits 0 after every fix above, including the corrected G3 lift
math (regression-asserted against the RG1 worked example). `bash -n
docker_launch.sh` and `python3 -c "import ast; ast.parse(...)"` over every
touched `.py` file pass. The four pinned instrument modules
(`probe_common.py`, `probe_stage_a.py`, `probe_stage_b.py`,
`probe_census_extension.py`) were re-hashed and match `experiment.yaml`'s
`instrument.pins` exactly -- confirmed untouched.

### 2026-08-09T02:15Z - Census COMPLETE. P1 satisfied by count (260 >= 250). All probe checks pass; signing

**Census run.** Container caution-install-probe-census-20260809b exited 0.
Output: analysis/probe_census_generations_private.jsonl (gitignored,
row-level, never committed). 3096 rows generated, exactly the registered
remainder (M_u 3496 minus the probe's 400). Zero degenerate completions,
zero capture failures (3096/3096 captured).

**Lead adjudication of the pre-stated criterion (entry 2026-08-09T00:31:22Z,
criterion unchanged).** The registered role rule (feasibility_probe.yaml
grading.roles: confab = gold-unanswerable row where the checkpoint answers)
applied to the probe file reproduces the probe's own count exactly (33 of
400), and applied to the census file gives 227 of 3096. Row keys are
disjoint between the two files (overlap 0) and their union is exactly the
full 3496-row corpus, so no row is double-counted and none is missing.

  actual_total_confab_count = 33 + 227 = 260 >= 250  ->  P1 pool floor
  reachable BY COUNT on this checkpoint and corpus (measurement replacing
  extrapolation; the registered 250 floor unchanged).

Realized census rate 260/3496 = 7.44 pct, sitting between the probe point
estimate (8.25 pct) and the trained-checkpoint SelfAware census prior
(5.75 to 6.6 pct), as the bracketing recorded at census registration
anticipated. Margin over the floor is +10 rows; the held-out arithmetic the
floor was derived from still closes (260 x 0.60 = 156 >= 150).

**Probe verdict, final.** P1 PASS (by count, per the pre-stated criterion),
P2 PASS (1844.88 >= 417), P3 PASS (capture 1.0), P4 PASS (overlap 0).
sign_blocked_on is cleared in experiment.yaml (lead edit, this entry is its
audit record). The four probe modules (probe_common.py, probe_stage_a.py,
probe_stage_b.py, probe_census_extension.py) are added to instrument.modules
with persistence declarations so bin/exp sign pins them; the stage B and
census scripts resume from their private output jsonl, hence incremental.

The main cell's sweep harness does not exist yet and will need lead hand-pins
after signing (the known sign/repin tooling gap). No sweep generation has
run and no G gate has been read; this entry resolves the feasibility probe
only. The 16 to 26 GPU-h sweep launch remains a separate PI approval.

### 2026-08-09T00:31:22Z - Full-corpus confab CENSUS extension registered (PI-approved), launching

PI approved a full-corpus census extension after the 2026-08-09T00:15:59Z
Stage B P1 FAIL, to replace the 400-row Wilson-bound extrapolation with an
exact count. This entry pre-states the design and the fixed criterion before
any docker verb runs, per the same blinding discipline as Stage B.

**What runs.** `probe_census_extension.py` generates on the REMAINING
gold-unanswerable (label `unknown`) candidates not already probed by Stage
B: M_u = 3496 total, 400 already probed in Stage B, so **3096 remaining**
(computed CPU-side just now: `total M_u = 3496`, `already probed = 400`,
`remaining = 3096`, matches `3496 - 400` exactly). Deterministic order:
remaining rows sorted by `row_key`. Same generation contract as Stage B
(max_new_tokens 200, min_new_tokens 1, greedy, eos includes `<|im_end|>`,
enable_thinking false), same first-JSON read policy, same role grading
(`confab` / `unknown_refused`) -- `probe_census_extension.py` imports
`load_model_and_tokenizer`, `generate_one`, and `grade_row` directly from
`probe_stage_b.py` rather than re-deriving them, so the two runs are the
same instrument. No answerable/known-label rows are generated by this
script -- the remaining-row set is unknown-label only, so
known_correct_answered stays exactly Stage B's 89, unchanged.

**Fixed criterion (stated here, before the census runs).** The registered
pool floor `required_total_confab: 250`
(`feasibility_probe.yaml pass_criterion.derivation`) is unchanged. This
census answers it by COUNT instead of by Wilson-bound extrapolation:

  actual_total_confab_count (Stage B's 33 confab out of 400, plus this
  census's confab count out of the remaining 3096, over the full M_u=3496)
  >= 250  -->  the P1 pool floor is reachable by count on this checkpoint
              and corpus (measurement replacing extrapolation)
  actual_total_confab_count < 250  -->  the pool floor is unreachable on
              this checkpoint and corpus; the lead records the transfer
              question as blocked by the checkpoint's own over-refusal

**Corroborating prior, recorded for context (not part of the criterion).**
The SelfAware full census on this exact checkpoint gives 5.75% [4.94%,
6.59%] three-seed answer-on-unknown, and 68/1032 on the seed-1 deployment
eval -- brackets the P1 floor's implied rate from below. Stage B's 8.25%
point estimate on 400 rows brackets it from above. The census resolves
which side of that bracket the true full-corpus count falls on.

**Launch details.**
- Config: `experiments/caution-install-bounded-site-sweep/probe_census_extension.py`.
- Container recipe: identical to the successful Stage B relaunch (`unsloth/unsloth:latest`,
  digest `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`,
  `--gpus all --ipc=host --entrypoint python3`, HF cache mounted at
  `/home/unsloth/.cache/huggingface` with `HF_HOME`/`HUGGINGFACE_HUB_CACHE`
  set explicitly, worktree mounted at `/workspace`, output dirs already
  world-writable from the earlier fix).
- Expected wall-clock: roughly 80-90 minutes at the measured 33.47 rows/min
  (3096 rows / 33.47 rows-per-min approx 92.5 min, consistent with the
  lead's 80-90 min estimate).
- Preflight to be run immediately before the docker verb: GPU idle check,
  Docker Desktop engine + nvidia runtime check, digest char-for-char
  verification, zero other containers running (one GPU job at a time).
- Output: private `analysis/probe_census_generations_private.jsonl`
  (gitignored, resumable), public
  `analysis-committed/probe_census_extension.json` (counts/rates/throughput
  only, no row text).

### 2026-08-09T00:15:59Z - Stage B GPU run COMPLETE. Probe result: P1 FAIL, P2/P3/P4 PASS, overall FAIL

Container `caution-install-probe-stage-b-20260808e` exited code 0 at
2026-08-08T23:48:43Z. 800/800 sampled rows generated and graded (400
unknown, 400 known), zero resume needed, zero crashes. Cross-verified role
counts computed independently from the raw private generations file
(`analysis/probe_generations_private.jsonl`) against the container's own
committed `analysis-committed/probe_role_yield.json`: identical
(n_captured=800, n_confab=33, n_known_correct_answered=89,
n_unknown_refused=367).

**Throughput (measured, replaces the 20-45 min engineering estimate).**
elapsed 1434.0 s (23.9 min) for 800 rows, 33.47 rows/minute, mean 30.84 new
tokens/row.

**P1-P4 arithmetic, literal, no adjudication:**

| Check | Count | n | Point rate | Wilson lower 95% | x M_u/M_a | Product | Threshold | Direction | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| P1 confab supply | confab=33 | 400 | 0.0825 | 0.0593 | M_u=3496 | 207.47 | >= 250 | floor | **FAIL** |
| P2 known-correct supply | known_correct=89 | 400 | 0.2225 | 0.1845 | M_a=10000 | 1844.88 | >= 417 | floor | **PASS** |
| P3 capture | captured=800 | 800 | 1.0000 | n/a | n/a | n/a | >= 0.90 | floor | **PASS** |
| P4 disjointness | overlap=0 | n/a | n/a | n/a | n/a | n/a | == 0 | equality | **PASS** (carried from Stage A) |

Overall (all four must pass): **FAIL**, on P1 alone.

**Row-id manifest.** 800 row_keys (ids only, no question/answer text)
written to the gitignored `analysis/probe_row_id_manifest.txt`, sorted,
newline-joined, trailing newline. sha256:
`7827c210901f36313548e01848c0b062b0e6687fad9044f921b546af3fca96ad`.

**Containment check.** `analysis-committed/probe_role_yield.json` and
`probe_corpus_inventory.json` carry counts, rates, intervals, products, and
throughput only -- no row text, question text, aliases, or generations, per
the pinned containment scheme. Full generations (with completion text)
remain under the gitignored `analysis/probe_generations_private.jsonl`.

**Docker digest** used for this run: `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`, verified char-for-char before launch (see the 2026-08-08T23:23:28Z entry above).

No adjudication is recorded here; the lead decides whether P1's failure
blocks signing, and if so among what the pass_criterion's `fail_meaning`
names as the options (narrow to raw-base substrate, enlarge/change corpus,
or record the transfer question as unaskable on this checkpoint). The
registered pool floors (`required_total_confab: 250`) are not renegotiated
here.

### 2026-08-08T23:23:28Z - Stage B GPU relaunch (permissions fixed, item-25 released the GPU)

Relaunching Stage B under the same pre-registered spec as the
2026-08-08T23:04:36Z entry, after the 2026-08-08T23:14:50Z addendum's
output-directory permission fix. Nothing else changed: same
`probe_stage_b.py`, same seed (20260707), same 800 sampled rows from Stage A
(`analysis/probe_sampled_rows_private.jsonl`, unmodified), same substrate,
same generation contract, same pinned digest.

- Preflight immediately before this entry: GPU idle (`nvidia-smi`, 0 MiB, 0%
  util), Docker Desktop engine active with `nvidia` runtime, 0 other
  containers running, `docker image inspect unsloth/unsloth:latest --format
  '{{.Id}}'` = `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  (matches `feasibility_probe.yaml execution.runtime_image_digest`
  char-for-char), `analysis/` and `analysis-committed/` confirmed still `777`
  from the earlier fix.
- The GPU was released by the item-25 Arm A extraction per the lead's GO
  message; one GPU job at a time is in force.
- Container name: `caution-install-probe-stage-b-20260808e`.

### 2026-08-08T23:04:36Z - Feasibility probe Stage A run, Stage B GPU launch

Stage A (CPU corpus inventory) ran and completed: `experiments/caution-install-bounded-site-sweep/probe_stage_a.py`.
M_u (gold-unanswerable candidates) = 3496, M_a (gold-answerable candidates) =
10000, P4 disjointness overlap = 0 (PASS, checked against the full
`datasets/triviaqa-rc-nocontext/train.jsonl`, 138384 rows / 76521 distinct
normalized questions, a conservative superset of the WS-0 pinned 20k-row
training subset). P1/P2 arithmetic precheck: both possible (best-case bounds
3462.74 and 9904.87 against thresholds 250 and 417), so Stage B is not
preemptively blocked. 800 rows (400 unknown + 400 known) sampled uniformly
without replacement at seed 20260707 and written to the gitignored
`analysis/probe_sampled_rows_private.jsonl`. Public output:
`analysis-committed/probe_corpus_inventory.json`.

Launching Stage B (GPU, undosed baseline generation + role grading) now, per
`feasibility_probe.yaml stage_b_role_yield`:

- Config: `experiments/caution-install-bounded-site-sweep/probe_stage_b.py`,
  reading `analysis/probe_sampled_rows_private.jsonl` from Stage A.
- Seed: 20260707 (generation is greedy/deterministic; the seed governs the
  Stage A draw this stage consumes).
- Substrate: base `professorsynapse/eh-qwen3-4b-clean-sft-seed1-merged-16bit`
  @ `ac361232c001af0ed5b0386b06dafc35d5cd31ea`, adapter
  `professorsynapse/eh-qwen3-4b-clean-sft-grpo-v2-seed1-lora` @
  `8914081dfcec4f1f025f2dbe4195d4f7aa8d210e`.
- Docker image: `unsloth/unsloth:latest`, digest
  `sha256:f21629b9ae4ed11231768edfaed0f40d41d85d6ea9a71e8096a3d96ea0311772`
  (verified present locally via `docker image inspect` before this entry was
  written; matches `feasibility_probe.yaml execution.runtime_image_digest`
  char-for-char).
- Expected wall-clock: 20-45 minutes (feasibility_probe.yaml's own estimate;
  this run measures the real rate).
- GPU: confirmed idle before launch (`nvidia-smi`, 0 MiB used, 0% util). One
  GPU job at a time.

### 2026-08-08T23:14:50Z - Stage B launch FAILED (output-directory permissions); fixed, NOT retried, GPU now held by another job

Addendum to the 2026-08-08T23:04:36Z Stage B launch entry above. Container
`caution-install-probe-stage-b-20260808d` (the fourth launch attempt of that
entry, after three earlier attempts failed on Hugging Face cache path/lock
permission issues under the container's non-root user and were not
GPU-billed) exited code 1 at 2026-08-08T23:11:27Z, about 3 minutes after
generation started.

**Root cause.** The base model and adapter loaded successfully (checkpoint
shards loaded, LoRA applied, `eos_ids = [151645]` resolved) and the FIRST
row's generation and grading completed. The crash was
`PermissionError: [Errno 13] Permission denied:
'/workspace/experiments/caution-install-bounded-site-sweep/analysis/probe_generations_private.jsonl'`
on the first attempted write. Cause: `unsloth/unsloth:latest` runs as
non-root uid 1001 (`unsloth`), but `analysis/` and `analysis-committed/` were
created by Stage A running natively on the host as `profsynapse` at the
default `755`, so the container user could traverse but not write into them.
This is the exact documented gotcha in
`.skills/experiment-runner/reference/local-runtime.md` ("Detached docker run
output dirs need world-write because the Unsloth container runs as a
NON-ROOT user (uid 1001)"); it was not applied before this launch.

**Rows generated: 0.** No `analysis/probe_generations_private.jsonl` file
exists on disk; the crash happened on the file's first `open("a")` call,
before any bytes were written. No partial/corrupt generation data exists to
clean up.

**Fix applied (CPU-side only, no GPU touched).** `chmod a+rwX` on
`experiments/caution-install-bounded-site-sweep/analysis/` and
`analysis-committed/` (now `777 profsynapse:profsynapse`, matching the
project's documented fix). `probe_stage_b.py` itself needs no code change:
`write_jsonl_row` and the public-output write already `mkdir(parents=True,
exist_ok=True)` before opening, so the permission fix on the two top-level
dirs is sufficient (Stage A's private-sample file and Stage A's public
inventory file are unaffected; both were already written successfully by the
native, non-container Stage A run before this).

**Status: NOT retried.** Per the lead's instruction, the GPU is now held by
the item-25 Arm A extraction (about 40-60 minutes). One GPU job at a time is
in force; this probe's Stage B will not relaunch until the lead gives an
explicit go. The exited container `caution-install-probe-stage-b-20260808d`
is left in place (not removed) for inspection; it is not consuming GPU.

### 2026-08-08 - Seventh site hs35 added pre-sign by lead adjudication of N2

The lead accepted Registration note N2 and independently verified its evidence,
so the registered search space is now seven write sites rather than six. Added:
**hs35, decoder block 34, relative depth 0.972**, the site the historical
`caution_direction_L35` hooks.

Verified evidence, one line: `c_hat_hs34.json` and `c_hat_L34.json` both carry
`layer: 33` with sigma 13.23002622164185, so the program's inherited site hooks
block 33, while
`archive/experiment/phase1/probe/steering/build_equiv_direction.py` documents
`block = layer - 1` and sets `best_layer = block`, so `caution_direction_L35`
hooks block 34, one block later. Without hs35 the sweep would not cover the site
whose claim it revises.

Files touched: `cell.yaml` (site added to the trained substrate's site list and
to the sites block, the not-registered comment removed, A_lin scope now seven
sites), `AMENDMENT.md` (Axis 1 table and prose, A_lin control, falsifier
searched-space sentence, the no-site-outside-the-registered clause, run plan
stage 2, budget section, D1 combination count, D3, N2), `gates.yaml` (new
`registered_sites` block enumerating the space the gates are scored over),
`experiment.yaml` (question). `TODO.md` is untouched; N1 remains the lead's to
apply.

Budget revised from 15 to 25 GPU hours to **16 to 26**, about 23,200
generation-equivalents up from about 21,900. The seventh site adds roughly
1,300, about 6%, because only the smoke, calibration, and held-out ladder stages
scale with site count; mining, extraction, controls, and pair count do not.

The feasibility probe is unaffected. It measures corpus yield and generation
throughput on the trained checkpoint and never touches a site: it loads no
direction, installs no hook, and its pass criterion is a function of role counts
and corpus size only. `feasibility_probe.yaml` was not edited.

hs34 and hs35 are adjacent by construction. They are reported as two distinct
reference sites and never as a swept span, since single-block resolution is not
claimed anywhere in this design.

The experiment was and remains draft and unsigned, so this is a pre-registration
refinement rather than a change to a signed space.

### 2026-08-08 - Pre-registration of the pre-sign feasibility probe (tier 3, BLOCKS SIGNING)

Instrument config: `feasibility_probe.yaml` (pinned at signing alongside
`cell.yaml` and `gates.yaml`).

**Tier and why.** Tier 3, lab notebook, per
`.skills/experiment-runner/reference/amendment-vs-lab-notebook.md`. Decision
question 3 routes preflight and diagnostic work to the lab notebook, and the
routing table places a preflight for a cell at tier 3. The same reference's
section "Pre-sign feasibility probe: every arm must be constructible from real
data" makes this specific check mandatory before signing, and records that it is
allowed and required even under a self-blinding rule, because self-blinding
forbids computing the result before signing and does not forbid confirming that
an arm can be built. That section also names the failure this rule exists to
prevent: the M4 cell defined an arm consuming a field that did not exist on its
test population, and the gap survived both signing and a full pre-sign red team
because nobody checked coverage.

**What is in doubt.** The main cell's G0a requires 150 held-out confab rows and
250 held-out known_correct_answered rows on the trained clean-SFT to GRPO-v2
checkpoint. That checkpoint over-refuses. A checkpoint that refuses may
confabulate too rarely to fill a confab pool, and may answer answerable
questions too rarely to fill a known-correct pool. Role labels are
behavior-dependent and cannot be ported from the raw-base pool
(`.skills/mechinterp-cells/reference/read-then-actuate.md`, section 1.1), so the
existing raw-base counts say nothing about this substrate. Both populations are
therefore at risk and both are probed.

**Blinding boundary, stated before the run.** The probe may compute role counts
and rates, corpus inventory counts, capture rate, and generation throughput. It
may not compute any steered quantity, any direction fit, any gate AUC, any tau,
any tighten rate, or any AUROC. Computing any of those would consume the main
cell's blind, and the probe's outputs would stop being coverage.

**Arms.** One. An undosed baseline: unsteered greedy generation, graded for role
labels. No direction is loaded and no hook is installed anywhere in this probe.

**Stages.**

| Stage | Device | What it does | Output |
|---|---|---|---|
| A, corpus inventory | CPU | counts available gold-unanswerable rows (M_u) and gold-answerable rows (M_a); verifies zero overlap with the training pools consumed by this lineage | `analysis-committed/probe_corpus_inventory.json` |
| B, role yield | GPU | draws 400 gold-unanswerable and 400 gold-answerable rows uniformly without replacement at seed 20260707, generates undosed, grades roles, records throughput | `analysis-committed/probe_role_yield.json` |

Stage B's generation contract is identical to the main cell's
`surface.generation`, so role labels come from the same instrument the main cell
will use. The role read policy is asserted as first-JSON rather than inherited,
because the grader can read the whole completion and let trailing prose reach a
role label; the gemma family atlas recorded 22 of 2815 split rows disagreeing
between the two reads.

**Why n = 400 per population.** The Wilson 95% half-width at n = 400 is about 4.0
points at p = 0.20 and about 2.1 points at p = 0.05, which is enough precision to
decide whether the corpus can supply the required pool. Drawn rows are recorded
by id so the main cell's Stage 1 mining reuses these generations rather than
repeating them, which makes the probe cost recoverable rather than additional.

**Token budget.** 800 rows at `max_new_tokens` 200 with `min_new_tokens` 1, so a
worst case of 160,000 new tokens and a realistic figure well below that, since
well-formed JSON answers terminate early.

**GPU minutes: 20 to 45, estimated.** This is an engineering estimate, not a
governed number: no governed document in this repository records wall-clock for
the predecessor cells, so no measured rate exists to cite. The estimate assumes
batched greedy generation of a 4B bf16 model on the local 3090 at roughly 25 to
50 rows per minute, plus one model load. Stage B is instrumented to record its
own measured rows-per-minute and mean new tokens precisely so this estimate can
be replaced by a measurement, both here and in the main cell's run plan.

**Pass criterion, fixed before the run.** Derivation: FIT_FRAC is 0.40, so
held-out is 60% of a pool; 150 held-out confab requires 250 total, and 250
held-out known-correct requires 417 total.

| Check | Expression | Direction |
|---|---|---|
| P1 confab supply | `wilson_lower_95(confab / 400) * M_u >= 250` | floor |
| P2 known-correct supply | `wilson_lower_95(known_correct / 400) * M_a >= 417` | floor |
| P3 capture | answer capture rate on probed rows `>= 0.90` | floor |
| P4 disjointness | training-pool overlap count `== 0` | equality |

The Wilson lower bound is used rather than the point estimate, so the probe
passes only if the corpus supplies the pool at the pessimistic end of the
estimate. P3 is the atlas AG0a bar: a checkpoint that cannot be cleanly mined
stops here.

**Disposition.** All four checks pass: signing of the main cell is unblocked,
and the measured throughput replaces the engineering estimate in the AMENDMENT
run plan. Any check fails: the main cell is not signed in its current form, the
counts are recorded here, and the lead chooses among narrowing the cell to the
raw-base substrate, enlarging or changing the corpus, or recording the transfer
question as unaskable on this checkpoint. The registered pool floors are not
lowered to obtain a pass.

**Containment.** Committed outputs are counts, rates, intervals, and throughput
only. Question text, aliases, gold answers, and generations stay under the
gitignored `analysis/` directory.

### 2026-08-08 - Draft registration filled

`AMENDMENT.md`, `experiment.yaml`, `cell.yaml`, `gates.yaml`, and
`feasibility_probe.yaml` filled from the session design draft (docs/preparation working file, not a
tracked artifact; superseded by this registration), under the lead's
adjudicated decisions: corrected transfer framing, substrate option (c), the
six-site search space, feasibility probe required and blocking, and the
superseded disposition for the un-re-derivable paper 3 section 6 citation.
Status stays draft. Three design questions were resolved at registration and are
recorded in `AMENDMENT.md` under "Design decisions at registration": calibration
pool size (D1), gate site co-located with write site (D2), and site naming
across the two index conventions (D3). Two items need the lead and are recorded
under "Registration notes for the lead": the burn-down row 27 wording (N1) and
the finding that the historical write site is one decoder block later than the
program's inherited site and therefore sits outside the adjudicated search space
(N2).
