# Gate-contribution factorial notebook

Running log for this experiment. Newest entry first. This is a lab notebook, not
a claims surface; the signed prose lives in `AMENDMENT.md` and the machine state
in `experiment.yaml`.

## Entries

### 2026-07-16 (lead) - dose-squaring defect caught by SC1 pre-grading; PI-approved fix; regeneration relaunched

SC1 verification of the first generation run found every fresh dosed write
realized setpoint = gain^2 instead of the registered dose_abs: run_factorial.py
passed the computed gain as the sigma argument to build_hook_and_controller
AND as generation strength (hook contract: setpoint = strength x sigma).
Observed readbacks matched the squared prediction exactly (qwen c_hat 64.01 =
8^2 vs registered 12.608; qwen random 158.99 = 12.608^2; mistral c_hat 144.0 =
12^2 vs 3.665; mistral random 13.44 = 3.665^2). 100% of fresh-write rows
failed the 0.005 relative readback bar; over-dosed c_hat text was 100%
degenerate. Reused arms (baselines, true_gate__c_hat) and decoy pools are
clean and untouched: their readbacks sit at the certified ~0.13-0.16% offset.
NOTHING was graded, no pool was built, no unblinding occurred; the committed
record is analysis-committed/sc1_verification_summary.json.

Root cause verified by the lead at source level against the pinned hook
contract and the midband-heldout precedent (which wires sigma/strength
correctly). PI approved the correction and directed a standing hardening rule:
smoke on GPU before any full run. Remediation (audited repin of
run_factorial.py, steer_lib.py, test_factorial_smoke.py; new pinned
compute_seed_ledger.py and sc1_verify_dosed_writes.py): wiring fixed to the
precedent convention via unit-tested pure functions; mandatory GPU preflight
subcommand (generate-family refuses without a preflight pass marker); live
SC1 first-batch and arm-completion assertions with hard abort; CPU regression
tests pinning sigma != gain against the exact pre-fix squared readbacks
(58/58 pass, lead re-ran independently).

Separately, the registered randomness bar (|cos| <= 0.015) voids most raw
draws at these dimensions (ambient ~1/sqrt(d)): the pre-registered
void-and-redraw walk accepts qwen {44000003, 44000007, 44000010, 44000012,
44000013} after 7 voids and mistral {45000002, 45000010, 45000011, 45000014,
45000021} after 15 voids; committed as
analysis-committed/random_seed_ledger.json. Random arms regenerate on accepted
seeds only. Mis-dosed runlogs quarantined under
analysis/quarantine_gain_squared/ (gitignored, retained).

GPU preflight PASSED both families (readback rel_delta 0.0013-0.0019, tol
0.005) before relaunch. Regeneration running detached (PID 948818, log
analysis/logs/generation_master_v2.log, ~0.94 rows/s, first live SC1
assertion PASSED at max_rel_delta 0.001581); ETA ~3.5h for both families.
No criterion, threshold, seed policy, or registered setpoint moved; the
predictions scoreboard is untouched and no outcome-bearing number has been
observed.

### 2026-07-15 (lead) - decoy source implemented, generation launched on the 3090

Run launcher implemented the decoy decision and launched generation. Decoy
sources: qwen 240 FIT-split known-correct rows (midband-doubt-snap
fit_rows_for_anchor.jsonl; the full available FIT population, under the ~300
target, reported straight), mistral 255 (RR hs16 fit split, matching
n_known_fit in the committed fit manifest). Fresh unsteered decoy-baseline
pass generated both pools on the 3090 (~5 min total); rubric filter survivors
238 qwen / 254 mistral; disjointness from every scored row asserted in code
and covered by smokes. Smoke suite now 50/50 (lead re-ran independently).
Three pinned files changed for exactly this scope and repinned with audit
(heldback_decoys.py, run_factorial.py, test_factorial_smoke.py); no scored-arm
generation path changed; test_report_smoke.py untouched.

Full factorial generation running detached (PID 297775, batch 4, greedy,
RunLog checkpointing, 8.7/24.6 GB VRAM): decoy passes done, qwen arms in
progress at ~24-26 rows/min, ETA ~5.5h qwen then ~5.5-5.75h mistral
(~11h total, finishing roughly 2026-07-16 05:00Z). Log:
analysis/logs/generation_master.log.

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
