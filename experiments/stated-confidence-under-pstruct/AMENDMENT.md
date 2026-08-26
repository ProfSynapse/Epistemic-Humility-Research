# Stated confidence under the structure-only contract: the unanalyzed channel

Status: resolved 2026-08-18 (partial: P2 held, P1 and P3 did not, neither falsifier fired; see Outcome). Signed earlier the same day with the instrument sha-pinned and both scoreboard calls recorded pre-run.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 2 records a scope condition: every stated-calibration reading in that
paper comes from arms whose prompt carried the full contract, and the
stated-confidence channel emitted under the structure-only prompt (P-struct)
was captured but never analyzed. The rows already exist on disk — the
prompt-crossing held-out confirmatory campaign scored 1,832 AmbigQA rows per
arm across 18 P-struct-bearing arms (base plus 17 trained checkpoints:
clean-SFT merged, cold SFT/DPO/KTO seeds 1-3, seq SFT->DPO and SFT->KTO seeds
1-3, SFT->GRPO seed 1), each row carrying `stated_confidence`, `correct`,
`refused`, and `label`. The SelfAware completion campaign carries the same
fields and serves as a secondary surface. No generation, no GPU: this cell is
a CPU-only analysis of existing artifacts.

Posture: EXPLORATORY, single pass, reported separately from the paper-2
headline matrix and never pooled with it. It answers one question paper 2
currently declines to answer: does the confidence number a model emits under
the structure-only contract carry any information (about correctness, about
its own refusal behavior), or is it schema-compliance noise?

## Feasibility-peek disclosure (binding on band placement)

Before this registration, a feasibility check confirmed the channel is
parseable (stated-confidence parse 99.7-100%, retry-exhausted 0-6 rows per
arm) and, in doing so, UNBLINDED four arm-level mean confidences:
base_pstruct 0.941, cold_sft_seed1_pstruct 0.398, sft_grpo_seed1_pstruct
0.813, base_prc 0.519. Consequences, fixed here:

- No prediction or gate in this cell is placed on any arm-level mean stated
  confidence. All means, all arms, are descriptive-only output.
- Seed-mates of a seen arm (cold_sft seeds 2-3) inherit the taint: their
  means are also descriptive-only.
- Banded quantities are restricted to functionals not derivable from a mean:
  discrimination (AUROC), calibration shape (ECE), and refusal-vs-answer
  conditional separation. None of these was computed or observed in the peek.

## Design

- Primary surface: `archive/experiment/phase1/eval/
  results_prompt_crossing_heldout_confirmatory_4b/`, the 18 `*_pstruct__ambigqa`
  arms (1,832 rows each), plus `base_pplain__ambigqa` and `base_prc__ambigqa`
  as contract-comparison references (descriptive only).
- Secondary surface (descriptive only): the P-struct arms of
  `results_prompt_crossing_completion_4b/` (SelfAware).
- Instrument: one CPU scoring script (pinned at sign), per arm computing:
  1. parse integrity: rows with usable `stated_confidence`, retry-exhausted
     count;
  2. confidence-correctness AUROC on answered rows (`refused == false`),
     `correct` as the positive label;
  3. 10-bin equal-width ECE on answered rows against `correct`;
  4. refusal separation: median stated confidence on refused rows minus
     median on answered rows;
  5. descriptive: per-arm mean/median confidence, refusal rate.
- Multiplicity: readouts are reported per arm; adjudication happens at the
  training-family level (SFT, DPO, KTO, seq-DPO, seq-KTO, GRPO, base), a seed
  counting as supporting only if its arm passes the band. No per-arm
  cherry-picking; no post-hoc subgrouping.

## Prediction

- P1 (discrimination): on answered rows, stated confidence ranks correct
  above incorrect at AUROC in [0.55, 0.80] for at least two-thirds of trained
  P-struct arms — informative but well short of the internal readout.
- P2 (calibration): 10-bin ECE >= 0.15 on at least half of the trained
  P-struct arms — the channel is miscalibrated under the structure-only
  contract even where it discriminates.
- P3 (refusal separation): median stated confidence on refused rows is below
  median on answered rows in at least two-thirds of trained P-struct arms.

## Falsifier

F1: confidence-correctness AUROC <= 0.55 on ALL trained P-struct arms — the
channel carries no correctness information under the structure-only contract
and P1 is falsified; the paper-2 scope condition then hardens into a null
("the unanalyzed channel was noise"). F2: P3's direction reverses (refused
rows carry HIGHER median confidence) in a majority of trained arms — the
refusal-separation reading is falsified.

## Gates

Pre-stated in `gates.yaml`. SC-G0 (integrity, pre-outcome stop): full row
coverage per included arm and parse rate >= 0.95; an arm below the parse
floor is EXCLUDED and named, and if more than 4 of the 18 P-struct arms fall
below the floor the cell is indeterminate. SC-G1: the P1/P2/P3 bands above,
fixed at signing, never retuned; outcomes outside every band are reported
descriptively as neither confirming nor falsifying.

## Compute and containment

CPU-only, existing artifacts, no model load. Repo is public: committed
outputs are AUROCs, ECEs, medians, counts, and arm names only; no question
text, no generation text, no row-level data leaves the gitignored
`analysis/` dir.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | P1, P2, and P3 all hold; the likeliest miss is P1's upper edge (some trained arm above 0.80) rather than the floor |
| user | P1 holds, though the confidence number is essentially useless; P2 holds (definitely not calibrated); P3 FAILS - the model emits high schema-confidence regardless of whether it is refusing |

## Outcome

**VERDICT: PARTIAL - P2 held, P1 and P3 did not; neither falsifier fired.**
Resolved 2026-08-18 (lead + user). Instrument of record:
`scripts/score_stated_confidence.py` (sha-pinned at sign), output at
`analysis/stated_confidence_scores.json` (gitignored; every number below is
transcribed from it). Single pass, exploratory, never pooled with the
paper-2 headline matrix.

### SC-G0 (integrity) - PASS

All 18 P-struct arms at full coverage (1,832 rows) with parse rates
0.983-1.000; zero arms excluded (indeterminacy line was >4). The
`base_pplain__ambigqa` reference arm parsed at 0.000 and is excluded and
named per the gate - expected, not a defect: the plain prompt carries no
JSON schema, so no stated-confidence field exists to parse. The
`base_prc__ambigqa` reference arm parsed at 1.000.

### SC-G1 per-prediction adjudication (17 trained P-struct arms)

- **P1 (discrimination): DOES NOT HOLD.** 8 of 17 trained arms inside
  [0.55, 0.80]; the band needed >= 12 (two-thirds). In band: cold SFT seeds
  1-2 (0.5585, 0.5675), seq SFT->DPO seeds 1-3 (0.5785, 0.6613, 0.5897),
  seq SFT->KTO seeds 1-3 (0.6867, 0.7245, 0.6852). Below the floor:
  clean-SFT merged (0.5229), cold DPO seeds 1-3 (0.5167-0.5177), cold KTO
  seeds 1-3 (0.5375-0.5449), cold SFT seed 3 (0.5441), SFT->GRPO seed 1
  (0.4898). F1 (AUROC <= 0.55 on ALL trained arms) did NOT fire.
- **P2 (miscalibration): HOLDS.** 17 of 17 trained arms at ECE >= 0.15
  (needed >= 9). Actual range 0.5482-0.8495 - severe miscalibration
  everywhere. Base and cold DPO/KTO arms state mean confidence 0.925-0.945
  while answering at 8.5-10% accuracy on this covert-ambiguity pool.
- **P3 (refusal separation): DOES NOT HOLD.** Negative separation (refused
  rows lower median confidence) in 11 of 17 trained arms; needed >= 12.
  Negative: cold SFT seeds 1-3, seq SFT->DPO seeds 1-3, seq SFT->KTO seeds
  1-3 (all -0.95), cold KTO seed 2 (-0.125, degenerate at n_refused=2),
  SFT->GRPO seed 1 (-0.0003, effectively zero). Non-negative: clean-SFT
  merged (+0.0906, the only positive, on 1,138 refusals), cold DPO seeds
  1-3 and cold KTO seeds 1 and 3 (0.0, degenerate at n_refused=1 each).
  F2 (refused higher in a majority) did NOT fire.

### Reading

The channel is not noise, but it is broken in a structured way. Severe
confidence inflation is universal (P2, ECE 0.55-0.85). Discrimination is
near chance for most regimens and weak-to-moderate only in the SFT-lineage
sequential arms (best 0.7245, seq SFT->KTO seed 2). The confidence-refusal
coupling exists only where SFT is in the training lineage: cold SFT and
both sequential families pair refusals with near-zero stated confidence
(separation -0.95), cold DPO and cold KTO essentially never refuse under
this contract (1-2 rows of 1,832), and SFT->GRPO refuses on 71.4% of rows
while stating mean confidence 0.8127 with zero separation - high
schema-confidence regardless of behavior, exactly the user's registered
mechanism.

### Descriptive per-arm table (means unblinded per the peek disclosure)

| arm | parse | AUROC | ECE | refusal sep | mean conf | refusal rate | answered acc |
|---|---|---|---|---|---|---|---|
| base_pstruct | 0.997 | 0.5285 | 0.8381 | 0.0 | 0.9406 | 0.0005 | 0.1025 |
| clean_sft_merged | 1.000 | 0.5229 | 0.5482 | +0.0906 | 0.7509 | 0.6212 | 0.1686 |
| cold_dpo_seed1 | 0.996 | 0.5167 | 0.8491 | 0.0 | 0.9445 | 0.0005 | 0.0954 |
| cold_dpo_seed2 | 0.995 | 0.5177 | 0.8495 | 0.0 | 0.9451 | 0.0005 | 0.0956 |
| cold_dpo_seed3 | 0.997 | 0.5167 | 0.8478 | 0.0 | 0.9448 | 0.0005 | 0.0970 |
| cold_kto_seed1 | 0.989 | 0.5449 | 0.8418 | 0.0 | 0.9274 | 0.0006 | 0.0856 |
| cold_kto_seed2 | 0.983 | 0.5375 | 0.8386 | -0.1250 | 0.9252 | 0.0011 | 0.0867 |
| cold_kto_seed3 | 0.987 | 0.5409 | 0.8420 | 0.0 | 0.9266 | 0.0006 | 0.0846 |
| cold_sft_seed1 | 0.997 | 0.5585 | 0.7916 | -0.95 | 0.3981 | 0.5739 | 0.1401 |
| cold_sft_seed2 | 1.000 | 0.5675 | 0.7819 | -0.95 | 0.4294 | 0.6479 | 0.1581 |
| cold_sft_seed3 | 1.000 | 0.5441 | 0.7827 | -0.95 | 0.3516 | 0.6281 | 0.1615 |
| seq_sft_dpo_seed1 | 0.998 | 0.5785 | 0.8289 | -0.95 | 0.7818 | 0.1717 | 0.0832 |
| seq_sft_dpo_seed2 | 0.999 | 0.6613 | 0.7488 | -0.95 | 0.7233 | 0.2137 | 0.0799 |
| seq_sft_dpo_seed3 | 0.999 | 0.5897 | 0.8139 | -0.95 | 0.7336 | 0.1825 | 0.0775 |
| seq_sft_kto_seed1 | 0.996 | 0.6867 | 0.6750 | -0.95 | 0.3891 | 0.5129 | 0.1125 |
| seq_sft_kto_seed2 | 1.000 | 0.7245 | 0.6380 | -0.95 | 0.3640 | 0.5401 | 0.1069 |
| seq_sft_kto_seed3 | 1.000 | 0.6852 | 0.6668 | -0.95 | 0.3926 | 0.4948 | 0.1081 |
| sft_grpo_seed1 | 1.000 | 0.4898 | 0.6282 | -0.0003 | 0.8127 | 0.7140 | 0.1908 |
| base_prc (ref) | 1.000 | 0.5157 | 0.7477 | -0.95 | 0.5192 | 0.7187 | n/a for bands |

Peek disclosure restated: the four means seen pre-registration
(base_pstruct 0.941, cold_sft_seed1 0.398, sft_grpo_seed1 0.813, base_prc
0.519) reproduce here (0.9406, 0.3981, 0.8127, 0.5192); no band was placed
on any mean, and none of the banded quantities had been computed before
signing.

### Predictions scoreboard adjudication

- P1: both predictors called holds; it did NOT hold - both wrong. The
  user's qualitative rider ("the confidence number is essentially useless")
  pointed at the true direction of the miss (most arms near chance, at or
  below the floor); the orchestrator's rider ("likeliest miss is the upper
  edge") was exactly backwards.
- P2: both called holds; HELD - both right.
- P3: orchestrator called holds - WRONG. User called FAILS via high
  schema-confidence regardless of refusal - RIGHT, and the SFT->GRPO arm
  instantiates the mechanism verbatim (71.4% refusal rate at 0.8127 mean
  stated confidence, separation -0.0003).
- Net: user 2 correct of 3, orchestrator 1 of 3.

### Consumers

Paper 2 Section 5 scope condition (the "captured but never analyzed"
stated-confidence channel under structure-only) can now cite this
measurement. Exploratory; reported separately from the headline matrix.

### Precision note (2026-08-18, lead, same day as resolve)

The Reading shorthand "the coupling exists only where SFT is in the training
lineage" is loose: SFT->GRPO has SFT in its lineage yet shows zero
separation. The precise decomposition, fully supported by the table above:
SFT installs the coupling; a subsequent DPO or KTO stage preserves it; a
subsequent GRPO stage erases it; cold preference training alone induces
neither refusal nor coupling. No number or gate outcome changes.

One-sentence verdict (also in `verdict:`): under the structure-only
contract the stated-confidence channel is not noise but is severely
miscalibrated on every trained arm (ECE 0.55-0.85), discriminates near
chance except in SFT-lineage sequential arms (best 0.72), and couples to
refusal only where SFT is in the lineage - DPO/KTO barely refuse, and GRPO
refuses at high stated confidence.
