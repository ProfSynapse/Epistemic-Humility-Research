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

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
