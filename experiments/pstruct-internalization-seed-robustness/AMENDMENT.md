# Instruction-free abstention internalization: seed robustness of the P-struct readout

Status: DRAFT (2026-08-14). Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

`prompt-vs-training-panel` (running, 2026-08-14) found that under a
structure-only prompt (P-struct: JSON contract, zero abstention affordance)
the raw base abstains on effectively no rows (recall 0.0%, refusal rate
0.06%) while cold SFT seed 1 retains recall 69.6% — the panel's R3
internalization band fired: SFT installs abstention in the weights, not in
the prompt. That is currently a single-seed observation, and it is about to
become a central paper-2 claim.

Per the program guardrail (promote an exploratory win only via a
confirmatory replication registered before running), this cell replicates
the P-struct readout across the remaining headline seeds for all three
cold-start objectives. Checkpoints all exist; this is eval-only. Tier-2,
registered as the confirmatory replication FOR THE INTERNALIZATION CLAIM
specifically; never pooled with the instructed-contract headline matrix.

Also serves the negative side: cold DPO/KTO have tracked the base under
every prompt condition measured so far; their seeds 2/3 P-struct rows make
"only SFT internalizes" a three-seed claim in both directions.

## Design

Instrument: identical to the panel's P-struct configs — `run_eval.py`, vLLM,
greedy, full SelfAware (n=3,369), P-struct system prompt byte-identical to
the panel's pinned wording. Single config, six arms, all on the raw bnb-4bit
base:

| Arm | Checkpoint (cell of record) |
|-----|------------------------------|
| cold_sft_seed2_pstruct | sft__4b__headline__seed2/20260615_090734 |
| cold_sft_seed3_pstruct | sft__4b__headline__seed3/20260615_104507 |
| cold_dpo_seed2_pstruct | dpo__4b__headline__seed2/20260615_114512 |
| cold_dpo_seed3_pstruct | dpo__4b__headline__seed3/20260615_130441 |
| cold_kto_seed2_pstruct | kto__4b__headline__seed2/20260615_142046_logging_patch |
| cold_kto_seed3_pstruct | kto__4b__headline__seed3/20260615_204215_logging_patch |

Seeds 2/3 were trained after the dev-split fix (the seed-1 postfix rerun did
not touch them); the KTO `_logging_patch` run dirs are confirmed the record
by `archive/experiment/phase1/run_records/kto__4b__headline__seed{2,3}.json`.
The seed-1 rows are NOT re-measured; they live in the panel cell. Budget:
six evals, ~2.5 GPU-hours local, queued behind the panel's remaining
configs.

## Prediction

Both SFT seeds land at or above the 30% internalization floor (seed 1 read
69.6%; expected band 55-80%), and all four DPO/KTO arms land below 10%
(base-tracking, expected ~0).

## Falsifier

Any SFT seed below 30% P-struct recall: the internalization claim is not
seed-robust and paper 2 must scope it to seed 1 or drop it. (Secondary,
reported straight: any DPO/KTO arm at or above 10% breaks the clean
"only SFT internalizes" negative and is reported as such.)

## Gates

- SR-G0 (integrity, per arm, verbatim from the panel's PV-G0): full coverage
  n=3,369; row-stamped config_sha matches pinned bytes; scorer parse path
  recorded. Any failure stops that arm, never retunes it.
- SR-G1 (claim gate, fixed here): internalization is seed-robust iff all
  three SFT seeds (seed 1 from the panel, seeds 2/3 here) read >= 30% AND
  base+P-struct < 10% (already measured, 0.0%). The 30/10 thresholds are
  the panel's frozen R3 values, reused unchanged; not retuned after results.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | SFT seeds 2/3 both 55-80%; all DPO/KTO arms < 2% |
| user | (on the fence about DPO/KTO arms' value; approved SFT seeds) |

## Budget

Six full SelfAware evals, ~2.5 GPU-hours on the local 3090, eval-only,
queued behind prompt-vs-training-panel configs 3-4. Launch requires explicit
PI approval after signing.

## Outcome

Run 2026-08-14, local RTX 3090, single container, all six arms completed
(exit 0; non-SFT arms ran slow through the stated-confidence JSON retry
path, as expected for checkpoints that never learned the contract).

**SR-G0 PASS on all six arms**: full coverage n=3,369 per arm; row-stamped
`config_sha` matches pinned bytes; parse path recorded.

P-struct refusal recall / over-refusal (%):

| Objective | seed 1 (panel) | seed 2 | seed 3 |
|---|---|---|---|
| cold SFT | 69.57 / 47.63 | 76.94 / 55.97 | 79.36 / 54.81 |
| cold DPO | 0.00 / 0.09 | 0.00 / 0.09 | 0.00 / 0.09 |
| cold KTO | 0.00 / 0.04 | 0.00 / 0.00 | 0.00 / 0.00 |

**SR-G1 PASS**: all three SFT seeds >= the 30% internalization floor
(69.57 / 76.94 / 79.36) with base+P-struct at 0.00 (< 10% ceiling; ~4-6%
under the panel's descriptive scorer-scope audit, still under the ceiling).
No negative arm reached the 10% report floor: all four DPO/KTO arms read
0.00. Neither falsifier fired; the registered prediction landed (SFT seeds
in/above the expected band; DPO/KTO at ~0).

**One-sentence verdict:** instruction-free abstention internalization is
seed-robust: all three cold-SFT seeds retain 69.6-79.4% refusal recall
under the structure-only prompt while all DPO/KTO seeds remain
base-indistinguishable at 0.00, making "only SFT installs abstention in
the weights" a three-seed claim in both directions.
