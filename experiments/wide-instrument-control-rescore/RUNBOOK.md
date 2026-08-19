# RUNBOOK: wide-instrument-control-rescore

Signed 2026-08-18 (see `experiment.yaml` and NOTEBOOK). This RUNBOOK
documents the launch sequence; launch authorization is recorded in the
NOTEBOOK entry. GPU steps run on the local 3090; no cloud spend.

## Stop rule (hard, pre-stated)

WG-G0 (parity) is a pre-outcome stop. If `score_parity.py` reports
`"verdict": "regeneration-invalid"`, STOP: do not run `score_wide.py`, do not
report any wide number, and record the cell as a negative-feasibility result
(`analysis-committed/` gets no promoted numbers). This is not a configuration
to retune — see AMENDMENT.md "Gates" WG-G0 and the project's amendment-vs-
lab-notebook discipline on pre-stated gates.

## 0. Prerequisites this RUNBOOK does not perform

Both source cells' generation entry points need gitignored, never-committed
local artifacts this build task did not and could not produce (private HF
staging repo access, local alias checkout, GPU anchor extraction):

```bash
# doubt-gated-caution-tighten (4.5 cell)
# ORDER CORRECTED at launch (2026-08-18): extract BEFORE materialize —
# materialize_rows.py reads the extract manifest
# (analysis/l34_anchor_extract_manifest.json) to attach category_canon per
# row, and the extractors' own docstrings ("Offline prep step 1/3") agree.
# Both extractors also import amendment_ah_stage0_extract from
# archive/experiment/phase1/probe/amendments/, which is not on the sys.path
# they set up themselves; run them with PYTHONPATH rather than editing the
# archived scripts (keeps their recorded shas untouched). PYTHONPATH needs
# THREE directories (launch-time correction 2, 2026-08-18): amendments/
# (the extractor's helper module), legacy-wrapper-tree/ (the archived tree
# was rewritten as compatibility wrappers before archival — commit 0723c329
# relocated amendment_s_correctness_probe_extract.py there as a pure R100
# rename), and the repo root (the wrappers delegate to the promoted
# implementations under experiments/common/ via namespace-package imports).
# The untracked probe-root backends.py is NOT cruft: it is byte-identical
# to experiments/common/knowledge_probe/backends.py (sha edb42095…) and
# satisfies the chain's bare `from backends import render_probe_prompt`;
# leave it in place. WG-G0 parity remains the arbiter of whether the
# promoted implementations regenerate the committed rows faithfully.
#
# Launch-time correction 4 (2026-08-19): materialize_rows.py additionally
# requires analysis/mined_a0_known_correct_rows.jsonl (question text for
# the 341 mined known-correct rows beyond the HF pool's 89; the committed
# split_manifest.json pins those row keys). The file is gitignored scratch
# that does not survive checkouts, produced by the cell's own
# mine_known_correct.py (greedy decode on the raw-base A0 surface;
# question text comes verbatim from expansion_candidates.jsonl, so the
# GPU pass only re-selects qualifying rows and materialize fail-closes on
# any coverage drift from the pinned keys). Its input
# archive/experiment/phase1/probe/analysis/ah_stage0/expansion/
# expansion_candidates.jsonl is restored from the divergent-pool-own-
# readout phase1-migrated mirror (13,496 rows, matching the mirror
# manifest's n_total_expansion; sha256 2886a602a2d8eca90bec2346ba21dc33
# ad8437d23d57755afb4b731ca063f3e5). Run order (corrected at launch,
# attempt 5): `python mine_known_correct.py` FIRST, then the anchor
# extract, then `python materialize_rows.py` requiring its printed
# missing_question=0. The extractor merges analysis/
# mined_a0_known_correct_rows.jsonl into its row set when present
# (select_rows), and pipeline.py loads l34_anchor_extract.safetensors as
# the sole anchor source — an extract run before mining covers only the
# original 89 known-correct rows and pipeline_rescore later fails with a
# KeyError on the first mined row_key. If extraction already ran before
# mining, re-run the same extract command unchanged; its startup log must
# show known_correct_answered=430. The j-space cell's materialize reuses
# the same mined file via its fallback path.
#
# Launch-time correction 3 (2026-08-19): amendment_ah_stage0_extract.py:55
# hardcodes the pre-rename path experiments/doubt-regulated-caution/
# phase3_ac_doubt_coupled_intervention.yaml (commit d55b7d26 dropped the
# phase3_ prefix, R078 — NOT a pure rename). The helper reads only
# prompt.system, verified byte-identical (463 chars) between the
# pre-rename blob and the tracked successor, with no other AC_CONFIG
# consumer. Fix per the h9-propensity-reading-gate precedent
# (NOTEBOOK.md:125-145 there): shim the old path with an untracked
# verbatim copy of the tracked ac_doubt_coupled_intervention.yaml. Never
# commit the shim; edit only the tracked file.
export WICR_PP=/home/profsynapse/code/Epistemic-Humility-Research/archive/experiment/phase1/probe/amendments:/home/profsynapse/code/Epistemic-Humility-Research/archive/experiment/phase1/probe/legacy-wrapper-tree:/home/profsynapse/code/Epistemic-Humility-Research
cd experiments/doubt-gated-caution-tighten
PYTHONPATH=$WICR_PP python extract_l34_anchor.py   # GPU, writes analysis/l34_anchor_extract*.{safetensors,json}
python materialize_rows.py          # private HF staging repo + local alias checkout

# j-space-midband-write-sweep-qwen3-4b (predecessor feeding the 4.6 cell's `pipeline` import)
cd ../j-space-midband-write-sweep-qwen3-4b
PYTHONPATH=$WICR_PP python extract_layer_sweep_anchor.py   # GPU, writes analysis/layer_sweep_anchor_extract.safetensors
python materialize_rows.py
```

`pipeline_rescore.py` checks for these files and refuses with an actionable
error (not a silent skip) if either is missing.

## 1. Stage 0: regenerate both cells' arms (GPU, local 3090)

```bash
cd experiments/wide-instrument-control-rescore
python pipeline_rescore.py --cell both --dose 200 --i-know-this-is-the-real-regeneration-run
```

Verifies pins for both source cells (and the 4.6 predecessor) against their
own `experiment.yaml` `instrument.pins`, fails loudly on any mismatch before
touching the GPU. Writes:
- `analysis/regenerated/cell_45_doubt_gated_caution_tighten/{full_summary.json,rows_with_generation.jsonl,provenance.json}`
- `analysis/regenerated/cell_46_j_space_calibrated_layer_contrast/{full_summary.json,rows_with_generation.jsonl,provenance.json}`

Known pin gap (see `pipeline_rescore.py` module docstring and this build's
report): `doubt-gated-caution-tighten/experiment.yaml` does not pin
`pipeline.py` itself. The driver verifies what IS pinned and records current
sha256 for the rest without fabricating a comparison; sanity-check this
before trusting the regeneration matches what Section 4.5 originally ran.

Run `--cell 45` / `--cell 46` separately if you want to free GPU memory
between the two model loads (each cell's `regenerate_*` already frees CUDA
memory internally between its own passes, but not across the two functions
in one process).

## 2. WG-G0: parity check (CPU, seconds)

```bash
python score_parity.py
```

Defaults read straight from the real regenerated + committed paths (no
flags needed if step 1 used its defaults). Writes
`analysis/parity_report.json`. Exit code 1 and `stage_1_authorized: false`
on any arm outside +/-2.0pp — STOP here per the stop rule above.

## 3. Stage 1: build the blinded pool (CPU, seconds)

```bash
python score_wide.py build-pool
```

Writes shard pool files under `analysis/shards/` (gitignored) and
`analysis-committed/adjudication_pool_manifest.json`. **The lead must `git
add` and commit that manifest BEFORE dispatching any grading agent** — the
unblinding-order guarantee (ported from `abstention-wide-instrument-
calibration/apply_adjudication.py`) refuses to unblind a shard whose
graded-file sha256 was committed before the pool manifest itself was
committed. This build does not commit anything to git (STEP ZERO
invariant); that commit is the lead's action.

## 4. Real grading (external, NOT performed by any script in this cell)

For each shard file `analysis/shards/<shard_id>.jsonl`: dispatch a
context-free agent (no experiment context, the registered rubric from
`abstention-wide-instrument-calibration/AMENDMENT.md` "Registered
adjudication rubric" verbatim, the bare `{opaque_id, text}` pool only, an
explicit instruction not to build a pattern matcher) and collect its
`{opaque_id, is_abstention}` JSONL output. Then, per shard:

```bash
python -c "
import sys; sys.path.insert(0, 'experiments/abstention-wide-instrument-calibration')
import apply_adjudication as aa
aa.cmd_commit_hash(...)   # or use that module's own CLI directly
"
# or, simpler, reuse that cell's own CLI directly:
cd experiments/abstention-wide-instrument-calibration
python apply_adjudication.py commit-hash --shard-id <shard_id> \
  --graded-file <path> --committed-dir ../wide-instrument-control-rescore/analysis-committed
```

Commit each graded file's sha256 to
`analysis-committed/adjudication_graded_manifest.json` (in THIS cell's
directory, not the calibration cell's own) BEFORE reading that shard's id
map, then assemble `{shard_id: {"graded_file": path, "attempt": 1}}` into a
grading-manifest JSON for step 5.

## 5. Apply + gate arithmetic (CPU, seconds)

```bash
python score_wide.py apply --grading-manifest <path-to-grading-manifest.json>
```

Verifies committed hashes, joins, computes CG1 per shard (regrade-once /
void-cell-terminal per the registered rule), and if CG1 passes, computes
WG-G1 and WG-G2 from the unblinded wide rates. Writes
`analysis/wide_gates_report.json`.

Two flagged, unresolved-by-this-build items live in that report (see
`score_wide.py` module docstring):
1. WG-G1/WG-G2 as literally worded only cover the 4.5 cell's arm
   vocabulary; the 4.6 cell's wide-rescored hs23-vs-hs34 comparison is
   reported under `cell_46_layer_contrast_wide` with NO pass/fail verdict,
   since no WG-gate in AMENDMENT.md's "Gates" section literally names it.
2. WG-G2's "selectivity gap" has no registered formula; this build's
   `assumed_selectivity_gap_definition` is a documented guess, and its CI
   is a point-estimate combination only (not a proper joint bootstrap CI —
   see the module docstring for what's missing).

## CPU smoke test (already run by this build, not a real-launch step)

```bash
python score_parity.py --cell-45-committed <fixture> --cell-45-regen <fixture> ...
python score_wide.py apply --dry-run --cell-45-rows <fixture> --cell-46-rows <fixture>
```

`--dry-run` mocks grading with `detector_v2.is_refused_v2` as the oracle —
no network call, not a stand-in for a real context-free agent's judgment,
only a plumbing check. See this build's final report for measured
wall-clock and the fixture paths used.
