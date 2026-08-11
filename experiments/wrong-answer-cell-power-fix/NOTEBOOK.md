# wrong-answer-cell-power-fix notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-08-11 -- Bookkeeping: AMENDMENT.md header corrected to match machine state

**Tier 3, bookkeeping only, no goalpost implications.** `AMENDMENT.md`'s
header claimed a draft/not-signed status that contradicted
`experiment.yaml`'s machine state (`status: falsified`), which has read
verdict "primary falsifier fired as worded" on record since 2026-08-09.
Corrected the AMENDMENT.md header ("Status:" line) to match the machine
state. Also flagged (not fixed, no scientific content authored): this
document's own "Outcome" section is still the unfilled placeholder text
despite the machine state showing falsified with a verdict on record.
Follows the precedent set by `gemma-4-e4b-family-atlas/AMENDMENT.md`'s
2026-07-20 header correction. No signed content (question, prediction,
falsifier, gates, Outcome) touched. Caught by the new `bin/exp validate`
header-vs-status guard added in this same pass -- this was the 18th case,
missed by the initial manual sweep because its header uses bold
`**Status:**` markers that the sweep script's regex didn't handle but the
validator's does.

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

## 2026-08-08 ~23:00Z - Arm A harness built; four modules hand-pinned (tooling gap)

Harness-builder delivered the Arm A modules (row_join.py, readout.py,
arm_a_extract.py, score_gates.py) against the locked cell.yaml/gates.yaml,
which were verified byte-identical to their sign pins before and after the
build. CPU smoke: 24/24 checks passed on the real sha-pinned scored-rows
data, including G0-2 join integrity (3369/3369 ids, 0 unmatched, 0
duplicates, pinned cell counts 780/420/360 and 993/469/524 reproduced
exactly), G0-4 grader parity 100 percent on 200 rows, G0-5 adequacy both
checkpoints, and an independent re-derivation of the historical emitted
channel on the joined population: A3 = 0.5207, A8 = 0.8212 / 0.01750
(n=780), matching the AMENDMENT-cited values. E1-E4 estimator exercised
end-to-end on synthetic hidden states; degenerate self-test does not
spuriously pass E1.

PIN RECORD (lead, manual): the four modules are pinned in
experiment.yaml instrument.pins by hand because the sign tooling has no
verb for adding new module pins to a signed pre-run experiment
(bin/exp sign refuses non-drafts; bin/exp repin repairs existing pins
only). This is the designed workflow's intended step (modules were left
empty at sign because they did not exist yet); the hand-pin performs
exactly the hash sign would have computed, pre-run, with shas visible in
the PR diff. THIRD bin/exp tooling gap recorded this program, alongside
the unfilled-banner and outcome-placeholder gaps: sign should support
adding module pins to a signed pre-run experiment.
sha256 prefixes: row_join 187ddd53f7d8027f, readout 75f2c17b2eb0c59a,
arm_a_extract 0b5f9b25a3cfc7d9, score_gates cbf8e154b9423f18.

Launch note recorded ahead of the run: the builder-suggested docker
command uses a --digest flag that does not exist in docker run; the
actual launch will pin the image by reference (image@sha256 digest form)
and record the exact command here at launch time. GPU launch remains
blocked on the registration PR (#407) merge.

## 2026-08-08 ~23:30Z - LAUNCH: Arm A extraction (lead)

Registration PR #407 merged to main (a4775abe); PI launch approval standing
for the paper-3 burn-down. All six instrument pins verified byte-identical
immediately before launch (cell.yaml, gates.yaml, row_join.py, readout.py,
arm_a_extract.py, score_gates.py). GPU idle at launch (0 percent, 0 MiB;
the item-27 probe container had exited). One GPU job at a time in force;
the item-27 probe retry is explicitly held until this run completes.

Launch mode: host gpu_python per cell.yaml line 17
(/home/profsynapse/miniconda3/bin/python3, torch 2.9.0+cu128, CUDA
available), matching the program precedent for extraction cells
(qwen35-4b-midband-doubt-snap, correctness-direction-rotation). No docker
verb is used for this stage, so the image digest pin does not apply; the
builder-suggested docker command was discarded (its --digest flag does not
exist in docker run).

Command: cd /home/profsynapse/code/Epistemic-Humility-Research &&
/home/profsynapse/miniconda3/bin/python3
experiments/wrong-answer-cell-power-fix/arm_a_extract.py --run
Expected 0.5 to 0.75 GPU hours; both checkpoints one pass (h_base cleansft
adapter-disabled, h_lora grpov2 adapter-active), layers 30-36, resumable
append-log persistence.

## 2026-08-08 ~23:40Z - Arm A RUN COMPLETE; all gates scored; PRIMARY FALSIFIER FIRED; red-team pass SAFE TO ADJUDICATE

Extraction extraction__ab37a32e61a9 (3369 rows, manifest status=ok
verified=True, 0 missing shards of 6738, all 3369 prompt hashes distinct,
one config sha, generation_attempts 1 on every row). Scored with the
pinned estimators via real_run.py (sha 893c6636..., pinned this entry;
results in analysis-committed/real_run_results.{json,md}).

Gate results at pinned primary layer L35, grpov2 checkpoint:
- G0-1 render parity 0/50 mismatches PASS (but see limitation below);
  G0-2 join 0/0/0 with pinned counts 780/420/360 and 993/469/524
  reproduced exactly PASS; G0-4 grader parity 1.0000 both checkpoints
  PASS; G0-5 adequacy 420/360 and 469/524 PASS.
- E1 FAIL: A1 internal refit AUROC 0.5597, CI (0.5185, 0.5993), against
  the 0.60 floor with CI-lower 0.55.
- E2 FAIL: A4 gap over emitted 0.0390, CI (-0.0163, 0.0942), includes 0,
  against the +0.05 floor.
- PRIMARY FALSIFIER FIRES as worded (both conditions met on 360 wrong /
  420 correct rows, above the 300/300 floor).
- E3 fired-as-worded with a DEGENERACY recorded: the raw accounting
  passes decisively (A7 +0.2373, CI 0.1853-0.2769) while the
  base-rate-reweighted arm is arithmetically degenerate (reweighting
  labels to 0.959 without recalibrating collapses ECE to the distance of
  the mean prediction from 0.959, so a constant predictor at 0.959 scores
  zero regardless of discrimination). The reweighted sign flip carries no
  calibration content; any write-up states this.
- E4 PASS under the adjudicated reading: the A1 estimator's own
  out-of-fold projection gives correct-minus-wrong step 4.8484, CI
  (1.7384, 7.8129), excludes 0, full ordering holds. The frozen-axis
  reading is excluded by this AMENDMENT's own words (the frozen direction
  is never gated); the fresh full-population reading is excluded because
  it reintroduces the anchor overlap section 2.5 rejects. Caveat: the top
  and bottom cells are the axis anchors; the non-trivial content is wrong
  and known_refused landing in between, which they do.
- E5 not computed (Arm B not built in this delivery).

Verdict rule: E1+E2 fail => FAILURE (prediction falsified). Adjudication
scope, per the red-team pass (opus, full report in session records; all
reported numbers independently reproduced from the safetensors, exact
match): the null is NOT instrument-induced. The in-sample axis
construction the paper used reaches only 0.5680 on this population; the
band maximum (L34) is 0.5718; alternative axis families 0.5636; seven CV
seeds span 0.5567-0.5632. The anti-leakage refit costs about 0.008
AUROC, not the 0.09 needed to reach the floor.

CRITICAL SCOPE for any write-up (red-team W2, accepted): an unregistered,
ungated context probe (full-dimension logistic on the same vectors, same
rows) reaches 0.6769 (grpov2) / 0.6995 (cleansft), so correct-vs-wrong IS
linearly decodable from the pre-generation residual stream at this
position. What fails is that the KNOWN-UNKNOWN AXIS does not carry that
signal at deployment (0.5597). The paper-3 sentence is overturned at the
axis level only; it must never be rewritten as "no internal signal
exists."

Recorded limitations (red-team W1, W6 accepted):
- G0-1 as implemented verifies render determinism (independent re-render
  vs the extraction's own recorded prompt_hash), not byte-parity against
  the June eval render, whose prompts were never persisted. The two
  render modes (direct vs chat_template_kwargs) differ in trailing
  tokens; both harnesses try direct first and it resolves clean under
  the current stack, so a mode divergence is unlikely but unverifiable
  from committed artifacts. This is the one un-closed
  instrument-difference hypothesis; it cannot rescue the in-domain refit
  result.
- The M7 comparator (0.649 on the frozen manifest) was measured under
  the harness default neutral prompt on a 96 percent correct population;
  A1 (0.5597) is deployment-prompt at 54 percent correct. The drop is
  power AND surface confounded; per cell.yaml it is never differenced
  without this caveat.
- cleansft control: A1 0.5457 (lower than grpov2); its nominal E2 pass
  (gap 0.0563, CI lower 0.0071) reflects an emitted channel below chance
  (0.4894), both channels at floor; consistent with the grpov2 picture,
  not a counter-signal.

real_run.py pinned by hand in experiment.yaml (same tooling-gap
mechanism as the four build modules; sign has no add-pin verb). Results
promoted to analysis-committed/ per program convention (analysis/ is
gitignored). Resolution awaits PI approval.

## 2026-08-09 ~00:00Z - RESOLVED: status falsified, verdict stamped (PI approved)

PI approved the resolution and the Arm B skip in one directive. bin/exp
resolve stamped the manifest (status: falsified, verdict as adjudicated in
the prior entry); registry regenerated. KG ingest and the paper-3
axis-level sentence revision are registered follow-ups riding the
resolution PR and the next paper pass.
