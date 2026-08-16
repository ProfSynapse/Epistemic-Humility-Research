# Completing the prompt-condition crossing

Status: RESOLVED (2026-08-16, PI approval in-conversation). Run complete, Outcome recorded.
Machine state in `experiment.yaml`.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 2's Limitations section names three places where the prompt-condition
crossing is incomplete. The PI reviewed that paragraph on 2026-08-15 and
authorized running two of them (the third, instructed readings for cold
DPO/KTO seeds 2/3, was assessed as low-information and skipped):

- **Gap 3 (the open question):** the warmed preference arms, SFT followed by
  DPO and SFT followed by KTO (Amendment A, three seeds each), were never
  evaluated under the structure-only prompt. The study currently cannot say
  whether a preference stage applied to an internalized checkpoint preserves,
  erodes, or deepens what the supervised stage put in the weights. The paper
  itself calls this "the most obvious next measurement."
- **Gap 1 (contract symmetry for Section 4.5):** there is no
  response-confidence reading for the cold-start SFT arms and no plain-answer
  reading for the warmed arms (clean-SFT merged, SFT then GRPO v2), so the
  instructed-against-instruction-free pairs in Section 4.5 compare across
  contracts. These five evals convert that comparison to single-contract.

Eval-only: every checkpoint already exists; no training. Exploratory tier-2,
reported with the paper's prompt-crossing layer, never pooled with the
confirmatory headline matrix.

## Design

Instrument identical to the panel and seed-robustness cells: `run_eval.py`,
vLLM, greedy, full SelfAware (n=3,369 per arm), prompts byte-identical to the
pinned panel configs (P-struct, response-confidence contract) and the pinned
headline eval config (plain-answer contract). Three configs, eleven arms:

| Block | Arms | Base + adapter (cell of record) | Prompt |
|---|---|---|---|
| Gap 3 | seq_sft_dpo_seed{1,2,3}_pstruct | per-seed SFT merge + Amendment A sft_dpo adapter | P-struct |
| Gap 3 | seq_sft_kto_seed{1,2,3}_pstruct | per-seed SFT merge + Amendment A sft_kto adapter | P-struct |
| Gap 1a | cold_sft_seed{1,2,3}_rc | raw base + headline SFT adapter | response-confidence |
| Gap 1b | clean_sft_merged_pplain | clean-SFT merged 16-bit, no adapter | plain-answer |
| Gap 1b | sft_grpo_v2_seed1_pplain | clean-SFT merged + GRPO-v2 adapter | plain-answer |

The seq arms load each seed's adapter on the same 16-bit merge of that seed's
cold-start SFT adapter that Amendment A trained on (rebuilt if not on disk,
per the recipe in the run records; the rebuild is part of the instrument, not
a knob).

## Prediction

- Gap 3: all six seq preference arms stay at or above the 30% internalization
  floor under P-struct (expected band 40-80%); DPO arms at or below their own
  seed's cold-SFT parent value (repositioning toward answering), KTO arms
  near parent.
- Gap 1a: cold SFT seeds under the response-confidence contract read at or
  above their plain-answer instructed values (83.91/87.40/92.34); expected
  85-95%.
- Gap 1b: warmed arms under plain-answer land within about 10 points of their
  response-confidence readings.

## Falsifier

Any seq preference arm below 30% refusal recall under P-struct: a preference
stage applied after SFT erodes internalized abstention below the registered
floor, and paper 2's Section 4.3 repositioning story must add an erosion
finding. (Secondary, reported straight either way: any seq arm more than 10
points above its parent is read as deepening; gap-1 readings that break the
expected contract ordering are reported as-is. No registered claim rides on
gap 1; it exists to make Section 4.5 single-contract.)

## Gates

- PC-G0 (integrity precondition, per arm, verbatim from the panel's PV-G0):
  full coverage n=3,369; row-stamped config_sha matches pinned bytes; scorer
  parse path recorded. Any failure stops that arm, never retunes it.
- PC-G1 (classification rule for the six seq arms, fixed here before the
  run): each seq arm is compared to its own seed's cold-SFT P-struct parent
  value (69.57 / 76.94 / 79.36, from the panel and seed-robustness cells).
  Below 30% = erosion below the floor (falsifier). In [30%, parent - 10pp) =
  partial erosion, reported as such. Within +/-10pp of parent = preserved.
  Above parent + 10pp = deepened. The 30% floor is the panel's frozen R3
  value reused unchanged; the 10pp band is fixed here and never retuned.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | all six seq arms >= 30%, DPO at/below parent, KTO near parent; cold SFT RC 85-95%; warmed plain within ~10pp of RC |
| user | approved the run 2026-08-15; no directional call recorded |

## Budget

Eleven full SelfAware evals, ~4.5-5 GPU-hours on the local RTX 3090,
eval-only, GPU currently idle. Run authorized by the PI 2026-08-15
("run gap 3 and 1").

## Outcome

Run completed 2026-08-15 (~10.5 h wall on the local RTX 3090; the budget
estimate of 4.5-5 GPU-hours was exceeded because the seq DPO/KTO P-struct
arms ran at roughly double the per-arm rate of the SFT arms, a vLLM
per-request pattern the runner attributed to stated-confidence JSON retries
serializing on non-contract-following outputs; logged in NOTEBOOK, no
integrity impact). All 11 arms completed.

**PC-G0 PASS on all 11 arms**: full coverage n=3,369 per arm; row-stamped
`config_sha` matches the pinned config bytes; scorer parse path recorded.
Lead-verified by independent recompute from raw `scored_rows.jsonl` on three
pivotal arms (seq_sft_dpo_seed3, seq_sft_kto_seed1, cold_sft_seed3_rc):
exact agreement with the runner's metrics and pinned shas.

Per-arm refusal recall / over-refusal / truthful (%, unknown-labeled
n=1,032; full metrics in `analysis-committed/`):

| Arm | Recall | Over-refusal | Truthful | PC-G1 call |
|---|---:|---:|---:|---|
| seq_sft_dpo_seed1_pstruct | 35.17 | 9.11 | 26.60 | partial erosion |
| seq_sft_kto_seed1_pstruct | 61.43 | 31.07 | 33.84 | preserved |
| seq_sft_dpo_seed2_pstruct | 54.17 | 13.26 | 32.29 | partial erosion |
| seq_sft_kto_seed2_pstruct | 65.12 | 34.66 | 34.67 | partial erosion |
| seq_sft_dpo_seed3_pstruct | 31.78 | 9.93 | 25.50 | partial erosion |
| seq_sft_kto_seed3_pstruct | 65.41 | 31.92 | 35.11 | partial erosion |
| cold_sft_seed1_rc | 85.66 | 53.23 | 40.13 | (gap 1a) |
| cold_sft_seed2_rc | 90.21 | 60.33 | 40.78 | (gap 1a) |
| cold_sft_seed3_rc | 90.60 | 60.16 | 40.93 | (gap 1a) |
| clean_sft_merged_pplain | 87.60 | 71.59 | 36.72 | (gap 1b) |
| sft_grpo_v2_seed1_pplain | 96.22 | 84.42 | 36.00 | (gap 1b) |

**PC-G1 (gap 3), applied verbatim as registered** (parents 69.57 / 76.94 /
79.36; floor 30%; band 10pp): **falsifier NOT fired** — all six seq arms are
at or above the 30% floor. One arm preserved (kto_seed1, 61.43, within 10pp
of parent 69.57). Five arms partial erosion: dpo_seed1 35.17, dpo_seed2
54.17, kto_seed2 65.12 (1.82pp below its preserve band), dpo_seed3 31.78
(1.78pp above the floor, the closest call in the cell), kto_seed3 65.41
(3.95pp below its preserve band). No arm deepened.

Reading: a preference stage applied after SFT does not erase internalized
abstention below the registered floor, but it spends it. The spend is
objective-dependent and large for DPO (parent-minus-arm 34.4 / 22.8 / 47.6pp
across seeds) and modest for KTO (8.1 / 11.8 / 14.0pp). This extends paper
2's Section 4.3 repositioning story: DPO and KTO reposition toward answering
not only at the instructed surface but partly in the weights.

**Gap 1a**: cold SFT response-confidence readings 85.66 / 90.21 / 90.60, all
inside the predicted 85-95 band. The secondary expectation "at or above
their plain-answer instructed values (83.91 / 87.40 / 92.34)" held at seeds
1-2 and broke at seed 3 (90.60 < 92.34, -1.74pp); reported as-is, no
registered claim rides on it.

**Gap 1b**: warmed arms under plain-answer vs their governed
response-confidence readings (grpo-three-seed-confirmatory amendment,
seed-1 table): clean-SFT merged 87.60 vs 87.02 (+0.58pp), SFT->GRPO v2
seed 1 96.22 vs 93.41 (+2.81pp). Both inside the ~10pp band; prediction
held. Section 4.5's instructed-vs-instruction-free pairs can now be stated
single-contract in both directions.

**Predictions scoreboard reconciliation** (reported straight): the
orchestrator's floor call (all six >= 30%) and direction call (DPO at or
below parent) held; the expected 40-80 band was missed low by dpo_seed1
(35.17) and dpo_seed3 (31.78), and "KTO near parent" held only at seed 1.
The cold-SFT 85-95 band held at all seeds; the at-or-above-plain ordering
broke at seed 3. Gap 1b held at both arms. The user recorded no directional
call.

**Verdict (one sentence, mirrors `verdict:` in the manifest):** Falsifier
not fired: all six sequential preference arms retain internalized abstention
above the 30% floor under P-struct, but five of six show partial erosion
(DPO spending far more internalization than KTO), and the gap-1 evals make
Section 4.5 single-contract with both gap-1b arms inside the predicted band.
