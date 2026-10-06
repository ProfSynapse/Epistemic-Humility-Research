# Decision-model IDK option: with no further training, do decision models pick an explicit I don't know when the base torso truly does not know? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-10-05 (final draft pass): PI decisions - thresholds confirmed; IDK at all five positions

PI decisions, 2026-10-05, before any outcome:

- PI confirmed the drafted thresholds (H1 >= 0.50, H2 <= 0.10, H3 CI > 0,
  the CI-straddle INCONCLUSIVE rule, R0 floors 0.80 / 0.95). No threshold
  changed.
- IDK placement: all five positions instead of one balanced slot. Unit of
  analysis = the question (mean of its 5 pick-IDK indicators); H1, H2, H3
  and H4 use question-level means with question-level cluster-bootstrap CIs;
  H3's CAL cutoff matches the CAL question-level over-IDK rate. New
  descriptive secondary: position bias (pick-IDK by position 1..5, pooled,
  by group, position x group; range >= 0.10 flagged as a caveat on H1/H2).

Applied:

- cell.yaml: `idk_option.positions: [0..4]` (slot seed removed); runs
  restructured to `idk_runs` (one template pair per model, materialized per
  position by run_id substitution) and `noidk_runs`; 12 engine runs.
- The IDK analysis configs and recipes became position-0 templates
  (`dmio-idk-p0-<model>`).
- Harness: `build-idk-rows` writes 5 position files; `stage-engine`
  materializes and records template + materialized digests; `score` is
  question-level (`question_table`, `cluster_mean_ci`, `h3_compare`,
  `position_table`).
- gates.yaml, experiment.yaml (prediction/falsifier wording, staged input
  paths) and AMENDMENT (design, gates, floors, timing, prediction mappings;
  predictions unchanged) updated.
- `build-idk-rows` re-run (no model): 12,067 rows x 5 positions; every
  position's ported split equals dmcc's. Host engine `--dry-run` of a
  materialized position-3 config: OK for both models, FIT 4,829 / CAL 2,410 /
  TEST 4,828.
- Tests: 44 pass.

### 2026-10-05 (latest): engine repinned to e51a802b

- Tuner `e51a802b1229cc399a80163612638523ddeddbb6` (pushed to
  `jev-models-tuner-training-b55d92`) adds `export.cal_rows` /
  `export.fit_rows`. Submodule checked out there; cell.yaml `engine.commit`
  and experiment.yaml `checkpoint.engine` updated; gitlink staged.
- Engine `analyze_confidence.py --dry-run` (host Python, no model load), run
  on copies of `analysis_idk_pointer.yaml` and `analysis_noidk_pointer.yaml`
  with `data.files` pointed at this cell's local rows: both "Dry run OK",
  `export.cal_rows: true` accepted, split counts FIT 4,829 / CAL 2,410 /
  TEST 4,828 (equal to dmcc's).
- Tests, `validate`, `regen --check` and the hook commands re-run (results
  in the orchestrator report).

### 2026-10-05 (later): PI decisions applied (H3 CAL cutoff; orchestrator prediction)

- PI chose the CAL-fit H3 cutoff. All four analysis configs now set
  `export.cal_rows: true`; `collect` refuses an engine output without
  `cal_rows.jsonl`; G0 checks its qids against dmcc's CAL split. H3 is no
  longer NOT-ADJUDICABLE by design. Test added (32 pass).
- The tuner commit adding `export.cal_rows` was NOT yet on
  `origin/jev-models-tuner-training-b55d92` at this entry (fetch shows
  29f7af0c as tip). The engine pin and the submodule gitlink stay at
  29f7af0c until it lands; 29f7af0c rejects the new key, so no engine run is
  possible before the repin.
- Orchestrator prediction recorded verbatim (AMENDMENT frontmatter and
  scoreboard), labelled as the orchestrating AI agent's, after the
  thresholds were written. No threshold changed.
- `bin\exp.cmd validate` OK; `regen --check` up to date; hook commands pass.

### 2026-10-05 (late): draft scaffolded; pre-sign feasibility probe (no model)

Drafter: subagent for the orchestrator. Nothing signed, committed, or run on a
GPU. Branch `amendment-decision-model-idk-option` off `origin/main` @
`e1a0bdf84`, worktree `.worktrees/amendment-decision-model-idk-option`,
scaffolded with `bin/exp new` (type eval).

Predecessor state at drafting: dmcc is signed (`1387e92d`) and run, but its
branch is local only (not pushed, not on `origin/main`), and its results
(AMENDMENT Outcome, `analysis-committed/*`) are uncommitted in its worktree.
This cell does not stack on dmcc's branch; it consumes dmcc's gitignored
artifacts by absolute path + sha256 (cell.yaml `predecessor`).

Submodule: initialized in this worktree (`--reference` to the primary
repo's module store) and checked out at the interim engine pin
`29f7af0c35e3c825d96f770b62f46c60ac4db2b7`, the commit dmcc's signed commit
records as its gitlink. The gitlink therefore shows as modified; it moves again
when the CAL-export engine feature lands (AMENDMENT checklist item 1).

Feasibility probe (allowed and required pre-sign by amendment-vs-lab-notebook.md;
no model loaded, no recognition score, no decision-model output opened):

1. Exemplar collision probe (scratch script, then the harness rule). Y's five
   exemplar questions: none is a PopQA question. Candidate distractors were
   checked against the normalized gold aliases and option texts of all 12,067
   dmcc primary rows. Chosen: Saturn/Neptune/Uranus, Five/Seven/Eight,
   Ag/Fe/Pb, 1918/1939/1950, Kangchenjunga/Mont Blanc/Lhotse; all 0 alias
   hits and 0 option hits. Rejected: Mars, K2, Go, Four, Nine, Ten, Twelve,
   Three, 1941 (PopQA subjects), Al (1 alias hit). Five and Seven are PopQA
   subjects (question text only); kept, reported.
2. `idk_harness.py import-dmcc`: 6 artifacts verified against their pinned
   sha256 and copied to `analysis/dmcc_inputs/`; dmcc committed
   `rows_sha256` equals the rows file; knowledge_by_split equals the expected
   FIT 525/4,304, CAL 268/2,142, TEST 514/4,314.
3. `build-recognition`: 48,268 prompts over 12,067 rows; collision rule
   matched 0 rows (registered expected 0). items sha256
   `761060dcc4db898321c5c9169e1c724dadf7f75528e94ccc8bdf33b863b1f243`.
4. `build-idk-rows`: 12,067 rows; slot counts 2,414 / 2,414 / 2,413 / 2,413 /
   2,413; ported engine split of the IDK rows equals dmcc `splits.json`.
   rows sha256 `0ddbe712b95d33aba671c979cf3b2107aa4643bbf49f11b3770a11682432fb12`.
5. `plan`: resolves every input and prints the GPU argvs; engine HEAD equals
   the pin.
6. Tests: `python -m pytest experiments/decision-model-idk-option/tests -q`,
   28 passed.
7. `bin\exp.cmd validate`: OK once the submodule was initialized (before
   that, an unrelated cell's repository inputs under `synaptic-tuner/` were
   missing). This cell's only warnings are the two staged-checkpoint local
   inputs, which do not exist until `stage-engine`. `bin\exp.cmd regen` then
   `regen --check`: up to date. Hook commands run one by one: all pass;
   `bin/validate_kg.py` passes when `core.hooksPath` is `.githooks` (it fails
   on this machine's WSL-path hooksPath config, which the
   `git -c core.hooksPath=.githooks` commit form overrides).

PI predictions received 2026-10-05 (recorded verbatim in AMENDMENT). They
arrived before the gate thresholds were drafted; threshold provenance is
disclosed in AMENDMENT "Gates".
