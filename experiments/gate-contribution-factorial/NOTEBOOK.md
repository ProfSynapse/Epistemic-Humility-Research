# Gate-contribution factorial notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-15 (lead) - harness accepted, modules pinned, decoy-source decision, generation authorized

Harness builder delivered the full CPU arc: 22 instrument files, 45/45 smoke
tests (lead re-ran the suite independently, 45 passed), SC0 staging complete
with every source artifact present, RG0 byte-repro PASSED for both families'
baseline and gated runlogs, and the qwen permuted-gate construction reproduces
the midband-heldout on-disk permuted_gate.jsonl fired-row set byte-for-byte at
seed 20260713. detector_v2.py, detector_v2_patterns.yaml, and grader.py hashes
match the census pins exactly. All 22 modules added to experiment.yaml
instrument.modules with sha256 pins (this entry is the audit record for the
post-sign pin addition; cell.yaml and gates.yaml are untouched and still match
their sign-time pins).

Builder findings adjudicated by the lead:

1. gen_lib.py well_formed: the P1 well-formed rate uses the JSON-parse rule
   ported verbatim from RR2 gen_lib.py (detector-v2's alias-dependent
   well_formed_correct_v2 is structurally wrong for the confab population).
   Correct per the AMENDMENT rubric ("graded by the unchanged JSON parse rule").
2. Clear-negative decoy source: this experiment scores the FULL known-correct
   pool in every arm, so unlike the census no held-out known row is left
   unscored to serve as a clear-negative decoy. LEAD DECISION (instrument-input
   choice, consistent with the registered text "a HELD-BACK pool of
   committed-answer, detector-v2-non-refused known-correct rows that never
   enter any scored rate"): draw the held-back pool from a fresh UNSTEERED
   baseline generation over FIT/atlas-split known-correct rows (disjoint from
   the held-out pool by construction, so they can never enter a scored rate),
   ~300 rows per family, detector-screened, committed-answer non-refused
   survivors only. No criterion, threshold, arm, or scored population changes.
3. run_factorial.py sys.path fix for the tuner RunLog import: build defect
   found and fixed pre-run by the builder, covered by the pinned smoke suite.
4. Build-time interpretations within spec freedom: qwen permuted-gate pool
   order = heldout_rows_for_steer.jsonl file order (validated byte-for-byte
   against the midband-heldout artifact); mistral = confab-sorted-then-known-
   sorted (no prior mistral permuted gate exists). Recorded, not spec changes.
5. BATCH_SIZE=4 is an execution default, overridable at launch; not a locked
   knob.
6. The midband-heldout worktree's existing permuted_gate.jsonl was NOT reused
   for permuted_gate__c_hat: cell.yaml registers source: generate, and the
   spec stands as signed.

Generation authorized on the free local RTX 3090 lane (standing PI approval
for the free local lane this arc; no paid lane). Order: decoy-pool baseline
pass, then qwen35_4b arms, then mistral7b_v03 arms, greedy, RunLog
checkpointing, timing probe reported after the first checkpoint flush.

### 2026-07-15 (lead) - knobs resolved, scoreboard registered, signed

All seventeen sign-time knobs resolved (AMENDMENT.md Decision record): PI decided
the qwen operating point (Qwen3.5-4B hs20, dose_abs 12.608, the census point) and
confirmed the Sel_abs metric, the 0.20 Gap_Sel(c_hat) floor, the directional-only
random-condition leg, and the 0.10 cost-protection floor; remaining knobs adopt
the drafter proposals, lead-confirmed. Mistral substrate revision pinned at sign
from RR2 (c170c708c41dac9275d15a8fff4eca08d52bab71); mistral permuted-gate seed
pinned 20260715. Predictions scoreboard registered pre-run by both predictors;
the differentiating slot is the mistral gate axis (orchestrator PASS, PI FAIL).
Signed via bin/exp sign; harness build dispatched against the locked spec on the
free local 3090 lane.
