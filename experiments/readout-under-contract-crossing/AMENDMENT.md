# Known-unknown readout under a change of prompt contract

Status: draft (not signed; do not launch as confirmatory evidence).

Machine state lives in `experiment.yaml` and is never duplicated here.

## Motivation and posture

Exploratory (single seed, Qwen3-4B); reported separately from any headline.
Paper 3 Section 9 flags the conditionality this cell measures: "Every readout
here is measured under one prompt contract at a time... Whether either survives
a change of contract is untested." The near-ceiling internal known-unknown
readout, the paper's first result, is measured under the neutral extraction
prompt only. If the readout is an artifact of that contract, the
internal-vs-stated gap loses its premise; if it is contract-invariant, the
premise hardens and the Section 9 paragraph can cite a measurement instead of
an open question.

## Design

- Checkpoints (3): raw base (hub-resolved exactly as the resolved
  prompt-vs-training-panel base arm), clean-SFT seed 1 (merged), SFT->GRPO-v2
  seed 1 (paths pinned in `inputs`).
- Contracts (4): neutral extraction prompt (reference), P-rc, P-plain,
  P-struct; the three contract renders resolved byte-identically from the
  pinned prompt-vs-training-panel configs listed in `inputs`.
- Rows: the SelfAware evaluation rows underlying the original readings;
  known/unknown labels are dataset properties, so no generation occurs
  anywhere in this cell.
- Stage 0 (references, GPU+CPU): neutral-prompt extraction per checkpoint at
  L35; cross-validated probe refit reproduces each checkpoint's reference
  reading within 0.01 (RU-G0 parity check on the stack itself).
- Stage 1 (contract extractions, GPU): nine extractions (3 checkpoints x 3
  contracts), same layer, position, and stack.
- Stage 2 (transfer scoring, CPU): project contract-conditioned activations
  onto each checkpoint's Stage-0 neutral-prompt direction; AUROC known vs
  unknown per pair.
- Stage 3 (refit scoring, CPU): cross-validated in-contract probe per pair;
  held-out AUROC.
- Stage 4 (adjudication, CPU): per-pair band assignment per `gates.yaml`.
  Committed output: AUROCs, drops, counts, verdicts only.

## Prediction

Every pair's transfer drop <= 0.05 from its checkpoint's Stage-0 reference
(see manifest).

## Falsifier

Any pair rotated (transfer < 0.85, refit >= 0.95) or suppressed (transfer
< 0.85, refit < 0.90) (see manifest).

## Gates

Pre-stated in `gates.yaml` (RU-G0 integrity/parity, RU-G1 per-pair bands);
fixed at signing, never retuned.

## Compute and sequencing

Extraction-only: twelve checkpoint-contract extractions over the SelfAware
panel, ~2-4 GPU-hours on the RTX 3090 Docker lane (pinned unsloth image).
Sequences AFTER the running prompt-crossing-heldout-confirmatory campaign;
may share the slot with base-refusal-direction-under-contract.

## Containment

Repo is public: committed outputs are AUROCs, drops, counts, and direction
metadata only; no question text, prompt text, or generation text leaves the
gitignored `analysis/` dir.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Invariant on base and clean-SFT for all contracts; GRPO-v2 P-rc is the likeliest partial (drop 0.05-0.10), no rotated or suppressed pair |
| user | |

## Outcome

Filled at resolve. Record the verdict, the gate results, and the one-sentence
summary that also goes into `verdict:` in the manifest.
