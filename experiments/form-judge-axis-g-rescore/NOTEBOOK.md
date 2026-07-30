# Form judge instrument: blinded-lane F1/F2/F3 grading and axis-G rescore of the naming-battery Arm A generations notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-30 Dev-set judge-vs-judge measurement (pre-sign, spent slice)

Eight isolated opus graders (two independent roles A and B, one fresh
instance per shard, matching the operational shape of the real instrument)
graded the naming battery's spent 219-row slice blind: comment-stripped
rubric, bare {opaque_id, text} shards staged under this cell's private
`analysis/dev_shards/`, no access to id maps or prior graded files. Lead
verified row counts (55/55/55/54), positional opaque_id match, and label
validity on all eight outputs before joining.

Results (core n=200, decoys n=19 excluded via the naming battery's id_map
`is_decoy`; an earlier compute pass wrongly counted all 219 as core by
guessing the field name, caught and redone against the actual schema):

- Core three-way judge-vs-judge disagreement: 16/200 = 0.080.
- Direction breakdown (A label -> B label): F2->F1 7, F2->F3 4, F1->F2 2,
  F1->F3 1, F3->F1 1, F3->F2 1. Spread, not one-sided: the residual is
  borderline-hedge noise, not a systematic detection gap like the voided
  regexes' 79/86 one-way miss.
- Both judges 19/19 on clear-positive decoys (labels F2 or F3, never F1).
- Core label distributions: A = F1 98 / F2 85 / F3 17; B = F1 103 / F2 77 /
  F3 20. Both judges find far more hedging than the voided regex battery
  did, consistent with the prediction's elevated-baseline-hedging mechanism.
- Dev-only context read: judge A vs the naming battery's original
  adjudicator 25/200 = 0.125; judge B 23/200 = 0.115. The original
  adjudicator graded under the naming battery's calibration framing, not
  this cell's rubric file, so 0.080 is the like-for-like estimate.

Aggregate JSON: `analysis/dev_judge_vs_judge_measurement.json` (ID-free).
Proposed G1 floor written to gates.yaml: 0.080 + 0.04 headroom (~2 binomial
SE) = max fresh-slice judge-vs-adjudicator disagreement 0.12. Signing and
floor registration await PI approval.

### 2026-07-30 Pre-sign harness build

Harness ported from the standing blinded-adjudication lane (builder
subagent, lead-verified): deterministic F5/F4 screen, calibration and
full-pool builders with dual decoy sourcing, role-scoped commit-hash/apply
tools with positional join and unblind refusal, axis-G arithmetic, pinned
judge prompt, 15 passing synthetic-fixture tests. Feasibility counts from
a count-only dry run over the real naming-battery data (lead re-derived
key numbers independently): 2000/2800 rows screened in; spent slice = 219
(row_key, arm) pairs; core candidates post-exclusion 1781; decoy candidate
populations 795 clear-positive, 595 clear-negative. Screen counts per
intermediate dose: 306 / 224 / 178, all above the 50-row NOT-ADJUDICABLE
guard. Five builder-flagged underspecifications resolved as lead rulings,
recorded in AMENDMENT.md "Build-time rulings".
