# Form judge instrument: blinded-lane F1/F2/F3 grading and axis-G rescore of the naming-battery Arm A generations notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-30 Calibration attempt 1 VOIDED (empty clear-negative decoys); governed deviation approved; attempt 2 built

At the registered lead spot-check (n=30, seeded, pre-unblind, pre-gate),
5 sampled rows were empty texts labeled F3. Trace: ALL 25 clear-negative
decoys in the attempt-1 pool were empty strings. Root cause: the
registered clear-negative source (Arm C baseline rows with correct_v2 ==
True) retains no generation text anywhere on disk; the c_baseline runlog
is metrics-only (text was only ever retained for Arm A via the form
sidecar), and the builder silently substituted empty strings. The
pre-sign feasibility count verified 595 ROWS existed, not text bytes.
Core rows were unaffected (0 empties) and judge labels on the 25
readable spot-check rows tracked the rubric well.

Lead ruling: attempt 1 is VOID for pool nonconformance (an empty string
is not the registered decoy object), discovered by the spot-check whose
registered function is to void a calibration pre-unblind. No gate was
computed, nothing was unblinded, and the attempt-1 grades are never
used. Not an instrument failure: grading empty bytes tests nothing
about the judge.

Alternative-source search (PI-requested before ruling): RR2/RR3/CG1
analysis trees are deleted from disk; the public data-exhaust datasets
are aggregate-only by containment design; Arm B and dosed Arm C runlogs
are metrics-only; naming_battery_rows.jsonl holds questions and gold
aliases, not generations. No conforming committed-answer text source
exists anywhere.

GOVERNED DEVIATION (PI-approved 2026-07-30): clear-negative decoys
dropped; G2 gates clear-positive only (25 at 0.92). Mitigations: both
dev judges labeled roughly half of core rows F1 (no away-from-F1
collapse mode in evidence), and G1's independent judge-vs-adjudicator
agreement gate catches any label collapse.

Remediation: builder's clear-negative lane removed; fail-closed guard
added (any empty pool text aborts the write; the smoke suite's original
fixture had given c_baseline a text field the real data never had, which
is how the bug passed 15 tests); --extra-spent-dirs added so a voided
attempt's rows join the spent exclusion; 17 tests pass. Attempt-1
artifacts archived under analysis/*_attempt1_void. Attempt 2 built with
fresh seed 20260801: 200 core rows disjoint from the dev slice AND from
attempt 1's cores (28-29 per arm), 25 clear-positive decoys, 0 empty
texts. gates.yaml, cell.yaml, and build_judge_pool.py repinned with
reasons. Attempt-1 committed manifests renamed *_attempt1_void.json.

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
