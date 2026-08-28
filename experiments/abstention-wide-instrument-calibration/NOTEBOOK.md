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

## 2026-07-14 - Regrade fails CG1, QL cell voided terminally; scorer run (lead)

QL_regrade_01 (fresh context-free agent, 768/768 verified line-aligned, hash
committed pre-unblinding 4582af91) failed CG1 clear-positive agreement at
0.429 (6/14) vs the 0.60 floor; clear-negative agreement 1.000. Per
gates.yaml `on_second_failure: void_cell_report_straight` the QL cell is
VOIDED TERMINALLY: all QL shard grades (including the ten individually
passing attempt-1 shards) are excluded from wide rates; QL is reported as
detector-v2-only (narrow) dose-response. Observation recorded, not a
rescue: the regrade shard carried the SAME 14 planted clear-positives as
the voided QL_shard_07 (composition preserved by design), and two
independent graders scored that specific decoy set at 0.286 and 0.429
while ten other QL shards with different decoy draws passed at
0.692-0.929, so the failure is consistent with a hard/borderline decoy
subset rather than two broken graders; the registered rule voids on the
floor regardless, and does. Transparency note: the regrade prompt kept the
rubric verbatim but added a symmetric boundary clarification (indirect
declines count; hedge-then-commit does not); CG1's two-sided floors
adjudicated that grader and voided it anyway.

Final apply over 16 passed shards + terminal void: applied rows 4,109
(QH 2,623 + LB 1,486, exact). calibration_scorer.py run;
analysis-committed/calibration_report.json written. Headline measurements
(UNCERTIFIED until red-team review): qwen QH wide baseline confab
139/1332 = 0.104 Wilson [0.089, 0.122] (narrow 0.044; undercount 6.1
points); qwen paired placebo delta on 1,286 paired confabs is NEGATIVE,
wide -5.13 points (baseline 0.108 -> random 0.057; narrow -2.88 points):
the matched-magnitude random direction SUPPRESSES qwen hedging rather
than recruiting it. Llama LB wide baseline confab 239/1453 = 0.164
[0.146, 0.184] (narrow 0.036; undercount 12.9 points; the 947
unknown_refused rows excluded per the build interpretation, reported
separately). Known-population wide rates are 0 everywhere but sparsely
covered on QH/LB because most detector-negative known rows were carved
into clear-negative decoys and decoys are excluded from scored rates (a
design consequence to flag for successors). Mistral cited from RR2:
baseline 0.280, placebo +7.39.

Adjudication boundary flagged for red-team BEFORE any verdict: the
registered falsifier leg reads "placebo delta >= 5 points" and the
measured delta is -5.13. The falsifier's own consequent interprets the
fire as "perturbation-RECRUITED hedging" (program-wide), which a
suppression contradicts; the prediction's plain meaning ("below 3
points") was a near-no-op claim that a 5.13-point-magnitude effect
violates. Both readings, the scoreboard consequences, and the QL void are
going to adversarial review before the Outcome is written. No verdict is
recorded in this entry.

## 2026-07-14 - Red-team certification and resolve (lead)

Adversarial review returned CERTIFIED-MEASUREMENTS with zero invalidating
findings: every headline rate re-derived bit-for-bit from row-level
artifacts (qwen 0.104, paired delta -5.13; llama 0.164; exclusion
arithmetic exact); positional join re-run from scratch reproducing the
4,109-row applied set exactly; all 18 graded and 18 pool hashes matched;
QL void path verified against the registered rule with composition,
fresh-id disjointness, and hash-before-unblinding confirmed; the
instrument correction confirmed to have changed no gate, floor, rubric, or
population and to have used the same committed grades; blinding claim
sound. Its recommended falsifier adjudication (signed, consequent-coherent
reading; not fired) was adopted in the Outcome. Non-invalidating notes
carried into the Outcome: LB unknown_refused carve makes llama's baseline a
lower bound; CG1 clear-positive floor granularity; QL four-layer scope per
cell.yaml glob. Resolved via bin/exp resolve; verdict sentence in the
manifest.

## 2026-08-27 — Exhaust published to HF (aggregate shape)

Data-exhaust release, PI-approved in-conversation (explicit permission
2026-08-27, batch 3 of the exhaust backfill, task-56c61a). Built with the
data-exhaust skill (aggregate-only copy-everything mirror of
analysis-committed/: no question text, generation text, or hidden states;
verify_exhaust.py PASS including the --experiment-dir completeness check;
zero exclusions). 7 files / ~375 KB, built at repo commit 37eaa399.

- HF repo: `professorsynapse/eh-abstention-wide-instrument-calibration` (dataset)
- HF revision: `c891882e18b929c3e792eea8eb9e3f5ae83482b2`
