# Style-controlled confirmatory read of the flavor-atlas overt-unanswerability separation notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- 2026-08-10T19:21Z CRASH + REPAIR: the real run crashed in `evaluate_sg4`
  with `KeyError: 'min_activation_oof_r2_at_each_primary_layer'`, after all
  20 C1/C2 permutation replicates had already checkpointed under
  `analysis/checkpoints/` (expensive work preserved; the crash was in gate
  adjudication, downstream of every residualization pass). Root cause: the
  real `gates.yaml` nests every SG's gate parameters under a `checks:`
  level (`sg4_treatment_strength.checks.min_activation_oof_r2_at_each_primary_layer`,
  and likewise for `sg6_permutation_negative_control.checks...`), but
  `evaluate_sg4` and `evaluate_sg6` read the gates dict flat
  (`gates["sg4_treatment_strength"]["min_activation_oof_r2_at_each_primary_layer"]`,
  `gates["sg6_permutation_negative_control"]["min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90"]`),
  a dialect mismatch from every other SG reader in the module (`sg0`, `sg2`
  correctly read `gates["sgN_..."]["checks"]`). `build_fixture`'s synthetic
  gates dict had independently reproduced the same flat shape for sg4/sg6,
  which is exactly why `--smoke` passed clean while the real run crashed:
  the fixture validated the buggy read path instead of the real schema.
  Repair scope: (1) fixed both reads in `evaluate_sg4` and `evaluate_sg6` to
  the real nested `["checks"]` shape; no threshold, layer number, or
  registered constant changed, read-path shape only; (2) fixed
  `build_fixture`'s `sg4_treatment_strength` and
  `sg6_permutation_negative_control` entries to mirror the real `checks:`
  nesting, so the fixture can no longer validate a wrong read path; (3)
  added a smoke check ("real gates.yaml/cell.yaml schema walk") that loads
  the real `gates.yaml`/`cell.yaml` from disk and walks an explicit list of
  key-path tuples the module reads at runtime, asserting presence only
  (computes nothing) -- any future schema drift between the governed YAML
  and the harness's read paths now fails `--smoke` before a real run burns
  compute on it. No committed output existed at crash time (the crash
  preceded any write of `analysis-committed/surface_control.json`), so this
  is a harness-crash repair on a signed pre-result cell, not a result
  change; no goalpost moved. The rerun resumes from the preserved
  `analysis/checkpoints/` (per-(panel, layer, block) granularity) and only
  re-executes SG4/SG6 adjudication plus anything not yet checkpointed, so
  re-adjudication after this fix is cheap. Fixed in worktree
  `ehr-worktrees/style-gatefix` on branch `fix/style-control-gates-dialect`;
  `--smoke` reran twice (78 checks passing both times, stable) and
  `--dry-run` once (ten gitignored `flavor-atlas-rawbase` inputs correctly
  reported missing, exit 1, nothing written) in that worktree. Not signed,
  not committed by this change; the lead reviews, repins, and commits.
- 2026-08-10T16:40Z LEAD REVIEW + REPIN: reviewed the repair below. Verified
  only the harness module and this notebook changed (governed docs
  untouched, diff-checked); layer plan and every decision constant derive
  from `cell.yaml`/`gates.yaml` at call time (the one 0.90 literal in the C2
  replicate criterion is the band embedded in gates.yaml's
  `min_permuted_runs_keeping_all_six_flavors_at_or_above_0_90` key name,
  now comment-traced in place); independently reran `--smoke` (all checks
  pass, includes the new fixture-backed end-to-end drive of `run_real`) and
  `--dry-run` in the fix worktree (ten missing gitignored inputs reported,
  exit 1, nothing written). Ran the full `--dry-run` against the canonical
  checkout where the flavor-atlas-rawbase captures exist: all ten inputs
  resolve, the tokenizer fallback resolves (126 tokens for the fixed probe
  string), exit 0. Note for the run record: transformers prints a
  tokenizer-regex advisory on load; the panels carry no recorded
  `rendered_prompt_token_count`, so every row's count comes from this same
  tokenizer and the surface covariate stays internally consistent across
  rows. Repinned `reanalyze_surface_control.py` dd1f67eb -> ebaa4684 with
  the audit reason in `experiment.yaml` (instrument-completeness repair,
  pre-read, no registered constant changed). Commit and PR by the lead;
  the PI merges.
- 2026-08-10T16:05Z REPAIR: pre-read instrument-completeness gap found and
  fixed. After signing, `reanalyze_surface_control.py::main()` had only the
  `--smoke` branch and a "REFUSING TO RUN" stub for the real-data path -- the
  real-run orchestration was never written, so an executing agent correctly
  hard-stopped instead of running against a partial instrument. No gate
  quantity existed yet, so this closes a gap in the signed instrument rather
  than moving any goalpost. Added: the real-run branch of `main()`
  (`run_real`), implementing SG0 input/anchor-coverage verification,
  panels_manifest count cross-check, SG1 pre/post extraction-tree digest,
  the frozen surface basis over the full question union, SG2 raw-baseline
  reproduction at 4dp, cross-fitted residualization at every registered
  (panel, layer) combination (S1's twelve primary cells plus the three
  reference pools, S2 surface-only, S3 descriptive transfer at its extra
  layers), C1/C2 permutation controls sharing the twenty fixed-seed
  replicates at the seven distinct primary layers, C3's planted linear
  channel, and SG8 adjudication via the existing `adjudicate()`, writing the
  counts-only committed JSON with the incremental checkpointing the
  residualizer already implements. Every threshold and layer number is read
  from `cell.yaml`/`gates.yaml` at call time. Also added a `--dry-run` mode
  (resolves every real input, prints the execution plan, executes and writes
  nothing) as a standing pre-launch existence check, and extended `--smoke`
  with a check that drives the real `run_real()` orchestration end-to-end
  against a tiny synthetic fixture in the real on-disk schema (fixture
  panels, extraction dirs with real safetensors files, panels_manifest,
  atlas-sweep placeholder), asserting a complete adjudicated JSON is
  produced -- this fails if the orchestration branch is ever reduced to a
  stub again. Fixed one bug found while building the fixture: `evaluate_sg2`
  had hardcoded literal layer `35` for the "secondary" baseline column
  instead of reading `secondary_layer` from `cell.yaml`, which both violated
  the "every constant traces to cell.yaml/gates.yaml" invariant and broke
  against a fixture using different layer numbers; fixed to read
  `secondary_layer` from each cell's spec. `--dry-run` against this worktree
  correctly reports the ten gitignored `flavor-atlas-rawbase` inputs
  (panels, extraction manifests, extraction dirs) as missing and exits
  nonzero without writing; it is expected to pass in the canonical checkout
  where those captures exist. `--smoke` passes clean (stable across repeated
  runs). Not signed by this change (already signed prior to this repair).
  No commit made here; the lead reviews and commits.
- 2026-08-10T15:48:34Z RESULT (real run): STOP before any gate ran. `main()`
  has no code path for non-`--smoke` invocation other than an unconditional
  refusal: it prints "REFUSING TO RUN: the real-data path is not exercised by
  this scaffold task (no GPU/extraction verb, no signed instrument in hand).
  Use --smoke for the CPU self-check, or run the signed instrument after
  `bin/exp sign`." to stderr and exits 1. No orchestration function exists in
  `reanalyze_surface_control.py` that wires `verify_sg0`,
  `verify_sg0_row_coverage`, `build_surface_matrix`,
  `crossfit_ridge_incremental`, the permutation/planted controls, and
  `adjudicate` into an end-to-end pass over the three real panels; those
  functions are present and smoke-exercised individually but never called
  from `main()` outside `--smoke`. SG0 was therefore never reached against
  real inputs. Zero gate quantities exist. `analysis-committed/` was not
  created; `git status` and a file listing confirm no output landed anywhere,
  registered or not. This is a harness-completeness gap, not a gate failure
  or a falsifier -- reported straight, no workaround attempted, no
  orchestration code added by the executing agent (locked-spec / no-improvise
  rule).
- 2026-08-10T15:48:34Z LAUNCH (real run, as registered in the harness
  docstring and `cell.yaml` `execution.runner`): `python3
  experiments/flavor-atlas-surface-control-confirmatory/reanalyze_surface_control.py
  --out experiments/flavor-atlas-surface-control-confirmatory/analysis-committed/surface_control.json`,
  no flags improvised, no constants overridden.
- 2026-08-10T15:48:26Z RESULT (smoke replay): all 26 synthetic self-checks
  passed, exit code 0. No real capture path touched (confirmed: gitignored
  `analysis/smoke/checkpoints/` contains zero files post-run, only empty
  directories from the resume-test checkpoint that unlinks itself at the end
  of `run_smoke()`).
- 2026-08-10T15:48:26Z LAUNCH (smoke replay): `python3
  experiments/flavor-atlas-surface-control-confirmatory/reanalyze_surface_control.py
  --smoke`, run from the canonical checkout on signed main (experiment.yaml
  status: signed, PI-approved sign+run 2026-08-10). Wall clock 1.657s.
- 2026-08-10T00:00:00Z SCAFFOLD: directory scaffolded from the PI-approved
  design draft via `bin/exp new ... --type probe-fit`. AMENDMENT.md, cell.yaml,
  gates.yaml, and experiment.yaml populated from the draft (OPEN QUESTIONS
  section resolved by the lead's adjudications, folded into the prose, not
  reproduced). Harness `reanalyze_surface_control.py` written and its
  `--smoke` self-check passes (synthetic arrays only; no real capture
  touched). Not signed. Not run. `bin/exp sign` and any real launch are the
  lead's call.
