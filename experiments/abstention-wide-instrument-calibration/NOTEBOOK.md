# Wide-instrument abstention baseline and placebo calibration (CPU re-read) notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

- (add dated entries as the experiment progresses)

## 2026-07-14 - Instrument correction: opaque-id collision in the QL cell (lead)

Found during count reconciliation of the first `apply` pass, BEFORE any rate
was computed or read: `salted_opaque_id` hashed (salt, cell, row_key, arm),
the tuple RR2's single-cell pool made unique, but the QL ladder cell contains
the same (row_key, arm) at multiple (hs_index, dose) points, so distinct
texts shared one opaque id (12,980 pool lines, 6,856 unique ids). Blinding
was NOT affected: graders saw only bare text plus an id, and a collision
reveals nothing about arm or population. Grading data was NOT affected:
every grader labeled per line, and all 17 graded files were verified
line-count, id-order, and schema clean against their inputs before their
hashes were committed. What broke was the JOIN: `apply_adjudication.py`
keyed id maps and graded files by opaque id in dicts, silently collapsing
1,603 QL core rows (n_applied 8,789 instead of 10,392) and mis-computing
QL decoy calibration.

Correction, H3-pattern (mechanical, pre-verdict, no gate/rubric/population
touched): the join is now positional (line i of shard pool, id map, and
graded file are the same item; per-line opaque-id equality is asserted and
a misaligned file is refused); applied rows carry role/hs_index/dose so the
scorer keys by the full scored-generation tuple; `salted_opaque_id` now
folds hs_index and dose_multiplier into the payload for regrade shards and
future pools (the committed attempt-1 pool manifest remains valid as
built); three regression tests added (cross-dose id uniqueness, global
uniqueness under row reuse, positional join keeps colliding rows and
rejects misalignment), suite 28/28. Modules repinned via bin/exp repin with
this entry as the documented reason.

Corrected CG1 over the same committed grades: 16/17 shards PASS,
clear-negative agreement 1.000 on all 17 (zero over-credit bias in every
grader). QL_shard_08's earlier 0.556 clear-positive failure was a collision
artifact; corrected it passes at 0.714. QL_shard_07 fails at 0.286
clear-positive agreement on the corrected join (that grader was genuinely
too strict on planted clear abstentions) and takes the registered
`void_shard_before_unblinding_regrade_once_with_fresh_agent` path: its
grades are quarantined un-unblinded, and `build_regrade.py` (new module)
rebuilt its 768 rows as QL_regrade_01 under a fresh secret salt (sha256
committed), fresh non-colliding ids (verified globally unique and disjoint
from every attempt-1 id), and a fresh shuffle, appended to the committed
pool manifest BEFORE the fresh grading pass is dispatched. n_applied after
correction: 11,090 = 11,788 core minus QL_shard_07's 698, exactly
reconciled. Applied rows exist on disk but no aggregate rate has been
computed or viewed; the scorer runs only after QL_regrade_01 adjudicates.
