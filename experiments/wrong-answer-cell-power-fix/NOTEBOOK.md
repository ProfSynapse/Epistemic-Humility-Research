# wrong-answer-cell-power-fix notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-08 registration draft filled (drafting agent, no run, no commit)

Filled `experiment.yaml`, `AMENDMENT.md`, `cell.yaml`, `gates.yaml` from the
PI-adjudicated design. Nothing launched, nothing signed, nothing committed.
Status stays `draft`; `bin/exp sign` is lead-only and has not been run, so
`instrument.pins` is empty.

**Pre-sign feasibility and coverage probe (allowed and required before sign; a
constructibility check, not a result).** Every count below was read from the
artifact this session.

- Primary checkpoint scored rows,
  `experiments/probe-scaled-response-confidence/analysis/phase1-migrated/eval/results_amendment_e_response_confidence_selfaware_clean_sft_grpo_v2_seed1_corrected_base_full_4b/clean_schema_sft_grpo_v2_seed1_corrected_base__selfaware/scored_rows.jsonl`,
  sha256 `1a6d7b59ad167c64dfdfa038b87cfe1cb57190c8d95c743d336ee3992f3b7887`:
  3369 rows, 780 answered-known, 420 correct, 360 wrong. Matches
  `A_full_eval.answered_known_n` and `A_full_eval.answered_known_n_wrong` in
  `archive/experiment/phase1/eval/analysis/calibration_gap_clean_sft_grpo_v2_seed1.json`.
- Control checkpoint scored rows,
  `.../results_amendment_e_response_confidence_selfaware_clean_sft_seed1_merged_full_4b/clean_schema_sft_merged_seed1__selfaware/scored_rows.jsonl`,
  sha256 `ab401f89254e882a205d651451d3c4aa866e13a12fcaf5678ed992feb6bd3d83`:
  3369 rows, 993 answered-known, 469 correct, 524 wrong. `stated_confidence` is
  non-null on every answered-known row, so the stated channel is constructible on
  the control arm.
- The control-arm scored rows are NOT at the path the historical session note
  implies. `archive/experiment/phase1/eval/` contains 34 `results_*` directories
  and none is a clean-SFT-only SelfAware run; the file lives under the migrated
  tree above. Recorded because a sign-time path assumption would have failed.
- The primary checkpoint's scored rows are likewise not at the path recorded in
  `calibration_gap_clean_sft_grpo_v2_seed1.json:scored_rows`; that path no longer
  exists and the file was migrated to the location pinned in `cell.yaml`.
- Pool sources for Arm B present with gold: `cheng_test_gold.jsonl` 11,313 rows,
  sha256 `8bd5e884...`; `popqa/test.jsonl` 14,267 rows, sha256 `2c88bb62...`.
- Both checkpoint paths verified present on disk: the merged-16bit base
  (7.6 G) and the GRPO-v2 adapter directory.

**Q2 verification (the render question), resolved against the repo, correcting
the brief.** The task brief stated that the frozen 1233-row extraction
`extraction__55254a04aa1f` was rendered with the forced-best-guess system prompt.
That does not hold. The extraction was produced by
`archive/experiment/phase1/probe/config/selfaware-hs/hidden_state_selfaware_manifest_clean_sft_grpo_v2_seed1_full.yaml`
(sha256 `4a0ff976a60420db1dfbe09bad860fbfbe7ba85b3cebf8951976ec4c172bc40c`), which
carries **no `prompt` block**, so the harness fell through to its default at
`experiments/common/knowledge_probe/hidden_state_probe.py:546-547`:
"You are a helpful assistant. Answer the question concisely." Corroboration: the
repo names prompt-matched extraction configs `*_prompt_matched.yaml` and those
carry the deployment `prompt.system` verbatim (for example
`hidden_state_selfaware_manifest_clean_sft_grpo_v2_unknown_failure_panel_prompt_matched.yaml:14-22`);
this config is not one of them. The forced-best-guess text is a module constant
in a different program
(`experiments/common/readouts/amendment_t_correctness_readout_deployment_extract.py:70-75`)
and is not reachable from the extraction harness config path.

The binding design consequence is unchanged and if anything stronger: Arm A
renders under the deployment prompt, and the frozen manifest is a different
generation surface from Arm A's extraction. The surface count is three, not two,
and `AMENDMENT.md` section 2.2 enumerates all three. The paper-3 provenance
caveat this implies (section 4's two channels are read off two different renders)
is registered as a follow-up line in `AMENDMENT.md` section 8, not fixed here.

**Validator note.** `bin/exp validate` run in this worktree reports
`OK (102 experiment(s))`. The two remaining messages for this slug are the
expected "gitignored data input absent" warnings for the two scored-row files,
which the validator exempts because they live under an experiment's `analysis/`
tree; they are present in the canonical checkout and are sha-staged at run time.
`doubt_direction_L35.json` is deliberately NOT listed in `experiment.yaml
inputs`: it sits under `archive/experiment/phase1-data/`, which `.gitignore:93`
ignores but the validator's untracked-input exemption does not cover (it matches
only `experiments/<slug>/analysis|directions/`), so listing it hard-fails
validation in a worktree. It is a descriptive companion rather than a gated
input, and it stays fully specified with its sha256 in `cell.yaml` under
`internal_readout.cold_transport_companion`.

**Still open before sign.**

- Harness modules are not written. `instrument.modules` is empty on purpose;
  listing non-existent files would pin nothing. Modules plus their persistence
  declarations (kill-resume rule) must be added before `bin/exp sign`.
- Arm A's extraction can read both checkpoints from one pass because the
  reference extraction config declares an adapter-disabled arm alongside the
  adapter-active arm and the reference manifest carries `h_base`, `h_lora` and
  `delta` tensor shapes. Confirm this against the harness behaviour when the
  module is written; if it does not hold, the control arm costs a second pass.
- Measured smoke wall-clock numbers for any `short-run` persistence declaration
  are not available yet; nothing in this draft claims one.
