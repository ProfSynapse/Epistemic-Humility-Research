# Write-direction naming battery: what is the mid-band c_hat write, behaviorally? notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-30 - draft written; blinding disclosures recorded

Drafted under a lead design assignment. Draft only: not signed, no GPU work, no
model loads, nothing committed. `bin/exp validate` passes with the draft in
place (96 experiments, zero warnings attributable to this slug).

**Recomputation provenance for the AMENDMENT disclosures D-1 through D-4.** All
four were computed on 2026-07-30 from the M1 ladder's on-disk, gitignored row
logs at `experiments/margin-mapping/analysis/runlog/qwen35_4b__*.jsonl` (11
files: `baseline_reused` plus rungs 0p0625, 0p125, 0p25, 0p5, 0p75, 1, 1p5, 2,
3, 4; each exactly 760 rows = 400 confab + 360 known_correct_answered; each row
carrying `answer_text`, `answer_value`, `refused_v2`, `semantic_refuse`,
`correct_v2`, `well_formed`, `degenerate`, `matched_pattern_ids`,
`readback_measured`). Computation was read-only, ran under
`/home/profsynapse/miniconda3/bin/python3`, and wrote nothing. The exact
per-rung tables are reproduced in the AMENDMENT disclosure section; the
one-liner that produced them should be promoted to a committed
`analysis-committed/disclosures/recompute_m1_rungs.py` at sign so the numbers
are reproducible rather than quoted.

D-3 additionally joined the 133 PopQA known rows to `datasets/popqa/test.jsonl`
on the numeric suffix of the `popqa:<id>` row_key. Join coverage was 133/133
with no id-namespace mismatch. The within-pool median `s_pop` was 680. Note that
Arm C's split is a DIFFERENT median, computed over the 2,744-row
`correct_on_answerable` census pool, and must be frozen before generation.

**Instrument facts established during drafting** (all read-only, all from
existing files):

- There is no shared grader module in this repo. Every steer cell owns a
  byte-for-byte port of `grader.py` / `gen_lib.py` / `detector_v2.py`. This cell
  follows that convention.
- `semantic_refuse` is literally
  `bool(answer_value) and ("i don't know" in answer_value.lower())`
  (`experiments/doubt-snap-cross-family-confirmatory/gen_lib.py:117`). The wide
  detector `is_refused_v2` adds the `diverse_idioms` list from
  `detector_v2_patterns.yaml` and is reported-only in the cells that carry it.
- No hedging, qualification, or partial-answer predicate exists anywhere in the
  grader stack. The F2/F3 classes of the Arm A taxonomy are genuinely new code.
- The random-direction placebo is reimplemented per cell, not imported; the
  construction is `unit(np.random.default_rng(seed).normal(size=hidden_dim))`,
  the same one `direction_fit.fit_directions` uses
  (`experiments/placebo-seed-distribution-census/direction_draw.py`).
- `experiments/margin-evidence-responsiveness-worldknown/harness/census.py` line
  17 documents `s_pop` as a field of its gitignored sidecar, and the sidecar does
  not carry it. Any `s_pop` join must target `datasets/popqa/test.jsonl`. Worth
  a one-line correction to that docstring under separate housekeeping.

**Open provenance problem raised to the lead.** The KG mechanism note
`caution-residual-ablation-relaxes-overrefusal-asymmetrically` (over-refusal
0.994 to 0.030) has no re-derivable governed source in this checkout. Paper 3
states the number and defers ownership to paper 5; paper 5 does not restate it;
`papers/series/plan.md` line 55 records the ownership move as pending; the
underlying sweeps survive as config only, with their declared output paths
absent from disk. See the AMENDMENT section "The ablation result the assignment
asked us to replicate". This is why Arm B is registered as an analogue rather
than a replication.

**Not yet done, gated on lead and PI review of this draft**: harness build
(materialization, runner, `form_taxonomy.py`, `form_patterns.yaml`), population
ID manifests, scoreboard predictor calls, `bin/exp sign`.
