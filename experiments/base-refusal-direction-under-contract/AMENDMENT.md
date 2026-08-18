# Base refusal direction under the response-confidence contract

Status: draft (not signed; do not launch as confirmatory evidence).

Machine state lives in `experiment.yaml` and is never duplicated here.

## Motivation and posture

Exploratory (single seed, Qwen3-4B); reported separately from any headline.
Paper 3 Section 5 rules the refusal axis a trained-checkpoint construct under
the neutral extraction prompt, where the base produces no over-refusal for a
direction to be fit on, and explicitly queues this cell: "Whether a refusal
direction fit on the base under that contract points where the trained
checkpoints' refusal axis points is a direct test that has not been run, and
nothing here claims its outcome." The enabling fact is registered: the resolved
`prompt-vs-training-panel` cell showed the response-confidence contract alone
elicits near-ceiling abstention from the untrained base (refusal recall 90.89,
over-refusal 65.38% of answerables), which is exactly the refuse-versus-answer
population a fit needs. Aligned means the contract recruits at inference time
the direction training consolidates into weights; distinct means
contract-elicited refusal runs through a different direction and the
trained-construct claim sharpens. Either terminal outcome feeds paper 3
Sections 5 and 9 as the promised follow-up.

## Design

- Stage 1 (labels, CPU): known-refused vs known-answered labels join from the
  governed retained rows of the resolved panel cell (base P-rc arm, SelfAware
  n=3369; path pinned in `inputs`). No fresh generation anywhere in this cell.
- Stage 2 (extraction, GPU): L35 hidden states for the raw base under the same
  byte-identical P-rc render, on the Stage-1 known rows, via the pinned unified
  extractor.
- Stage 3 (fit, CPU): refusal direction via the pinned paper-3 recipe
  (`residual_caution_direction.py`): logistic refuse-vs-answer contrast among
  knowns, then the known-unknown-orthogonalized component.
- Stage 4 (trained references, CPU): the three trained-regimen refusal
  directions re-derived with the committed Section 5 provenance reconstruction
  script over its pinned archived inputs (no standalone direction JSONs exist;
  re-derivation is the provenance-positive route).
- Stage 5 (compare, CPU): absolute cosines base-vs-each-trained direction plus
  a permutation floor recomputed with the Section 5 procedure; descriptive
  |cos| to the known-unknown axis (orthogonality check). Committed output:
  counts, cosines, floor, gate verdicts only.

## Prediction

Mean |cos| across the three trained directions >= 0.50 (see manifest).

## Falsifier

Mean |cos| <= 0.20 with BR-G0 passing (see manifest); 0.20-0.50 indeterminate.

## Gates

Pre-stated in `gates.yaml` (BR-G0 integrity, BR-G1 adjudication); fixed at
signing, never retuned.

## Compute and sequencing

Extraction-only GPU load, ~1-2 GPU-hours on the RTX 3090 Docker lane (pinned
unsloth image). Sequences AFTER the running prompt-crossing-heldout-confirmatory
campaign completes; may share the slot with readout-under-contract-crossing.

## Containment

Repo is public: committed outputs are direction metadata, cosines, counts, and
gate verdicts only; no question text, prompt text, or generation text leaves the
gitignored `analysis/` dir.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Aligned: mean abs cosine lands in 0.55-0.75; BR-G0 passes cleanly |
| user | |

Scoreboard outcome: orchestrator WRONG on BR-G1 (called aligned 0.55-0.75;
actual 0.0460, distinct), right on BR-G0 passing cleanly.

## Outcome

Resolved 2026-08-18: DISTINCT, prediction falsified. In the registered
Section-5 shared-standardized frame (`caution_axis_transfer.py` procedure:
L2 logistic C=0.5 per checkpoint, StandardScaler fit on the pooled known-row
activations of all four compared arms, layer 35), the refusal direction fit
on the raw base under the response-confidence contract has |cos| 0.0422 /
0.0522 / 0.0436 against clean SFT, SFT-GRPO-DPO, and SFT-GRPO-v2
respectively, mean 0.0460. The falsifier condition (mean <= 0.20 with BR-G0
passing) fired; the prediction band (>= 0.50) was missed by an order of
magnitude.

Gate results:

- BR-G0 PASS: 1,528 known-refused vs 359 known-correct-answered rows (floor
  100 per class); base refuse-vs-answer direction held-out AUROC 0.9497
  (first pass, per-fold frame) and 0.9509 (redo companion, same 5-fold
  procedure), both >= 0.80. The distinct verdict is not a weak-fit artifact.
- BR-G1 DISTINCT: mean |cos| 0.0460 <= distinct_max 0.20.
- Instrument validation (required before the comparison counted): the redo
  reproduced the published trained-pair cosines within 0.005
  (0.6695/0.5720/0.8591 against published 0.6713/0.5762/0.8566); the fourth
  arm joining the pooled scaler perturbs the frame only slightly.
- Permutation floor, same single-shuffle-per-arm scheme as the pinned
  script: base-vs-trained floor pairs 0.0366/0.0063/0.0122 (mean 0.0184);
  overall 4-arm off-diagonal mean 0.0218. The observed base-vs-trained
  cosines sit roughly 2-3x this noisy single-shuffle floor: close to
  orthogonal, marginally above chance.

Interpretation (the amendment's own pre-registered reading of this branch):
the response-confidence contract does not recruit at inference time the
direction training consolidates into weights. Contract-elicited refusal in
the base runs through a different direction, and the paper-3 trained-
construct claim sharpens: the shared refusal axis of the trained checkpoints
is manufactured by training, not a latent base direction the prompt merely
activates.

Estimator ruling (made before the redo result was seen): the first-pass
comparison used raw mass-mean directions, an estimator the registered bands
were never calibrated against (its numbers: 0.1906/0.2069/0.2054, mean
0.2010, with trained pairs at 0.92-0.98 and floor 0.0892 in that space).
Those numbers are retained as DESCRIPTIVE ONLY in
`analysis/br_compare_result.json`; adjudication used the Section-5 frame
exclusively (`analysis/br_compare_transfer_frame.json`). Both estimators
agree the base direction is far from the trained axes.

Recorded caveats: (1) the base arm's negative class is known-correct-
answered only, while the trained reference fits include known-answered-wrong
rows in the negative class, because no known-answered-wrong rows exist in
the base P-rc source extraction (a property of the data, not a convention
choice); (2) the permutation floor is the pinned script's single shuffle per
arm, noisy by construction; (3) single seed, exploratory tier, reported
separately from any headline.
