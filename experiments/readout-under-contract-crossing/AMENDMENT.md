# Known-unknown readout under a change of prompt contract

Status: resolved 2026-08-18 (partial transfer; prediction did not hold, falsifier did not fire; see Outcome). The header carried stale pre-sign boilerplate until resolve; machine state was already `signed`.

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

**VERDICT: PARTIAL TRANSFER.** Resolved 2026-08-18 (lead + user). The
prediction (all nine contract pairs invariant, drop <= 0.05) did NOT hold;
the falsifier (any pair rotated or suppressed) did NOT fire. Exploratory,
single seed, Qwen3-4B lineage only.

Instrument of record: `scripts/score_contract_crossing.py` (seed 20260817,
layer 35, last-prompt-token), output at `analysis/contract_crossing_scores.json`
(gitignored; every number below is transcribed from it). Provenance note:
the twelve extractions were completed by the background runner (last arm
finished 2026-08-18 06:30); the runner died between extraction and scoring,
and the lead ran the registered scoring script directly over the completed
artifacts. No extraction was re-run.

### RU-G0 (integrity/parity) - PASS on all three checkpoints

Coverage: 12/12 extractions, 3,369 rows each (2,337 known / 1,032 unknown).
Neutral 5-fold out-of-fold AUROC vs the published Section-4 reading:

| checkpoint | neutral CV AUROC | published | abs delta | <= 0.01 |
|---|---|---|---|---|
| base | 0.9914 | 0.997 | 0.0056 | PASS |
| clean_sft_merged | 0.9905 | 0.9968 | 0.0063 | PASS |
| sft_grpo_v2 | 0.9900 | 0.9971 | 0.0071 | PASS |

### RU-G1 (per-pair bands)

| checkpoint | contract | transfer | refit | drop | band |
|---|---|---|---|---|---|
| base | prc | 0.8860 | 0.9939 | 0.1054 | partial |
| base | plain | 0.9996 | 0.9920 | -0.0082 | invariant |
| base | struct | 0.9099 | 0.9938 | 0.0815 | partial |
| clean_sft_merged | prc | 0.9116 | 0.9881 | 0.0789 | partial |
| clean_sft_merged | plain | 0.9997 | 0.9912 | -0.0092 | invariant |
| clean_sft_merged | struct | 0.9145 | 0.9897 | 0.0760 | partial |
| sft_grpo_v2 | prc | 0.9286 | 0.9892 | 0.0614 | partial |
| sft_grpo_v2 | plain | 0.9997 | 0.9904 | -0.0097 | invariant |
| sft_grpo_v2 | struct | 0.9266 | 0.9901 | 0.0633 | partial |

No pair is rotated (all transfers >= 0.886, above the 0.85 line) and no pair
is suppressed (all refits >= 0.988). Per gates.yaml, partial pairs are
descriptive: neither invariant nor falsifying.

### Reading

The readout itself is present under every contract: refitting in-contract
recovers 0.988-0.994 everywhere. What the contract changes is the geometry:
the neutral-prompt direction survives the plain contract exactly (transfer
0.9996-0.9997 on all three checkpoints) but loses 0.06-0.11 of AUROC under
the P-rc and P-struct contracts. Descriptive gradient, not gated: training
monotonically shrinks the contract sensitivity (prc drop 0.1054 base ->
0.0789 SFT -> 0.0614 GRPO; struct 0.0815 -> 0.0760 -> 0.0633).

### Predictions scoreboard adjudication

Orchestrator called "invariant on base and clean-SFT for all contracts;
GRPO-v2 P-rc the likeliest partial (drop 0.05-0.10), no rotated or suppressed
pair." Right that nothing rotated or suppressed; WRONG on invariance - prc
and struct are partial on all three checkpoints including base, and base/prc
(0.1054) overshoots even the guessed partial range. The contract-sensitivity
gradient runs opposite to the call: base is the most contract-sensitive
checkpoint, not the least. User made no call.

### Consumers

Paper 3 Section 9 (contract-conditionality bullet: the "untested" flag
becomes this measured result). The Section-4 invariance upgrade registered as
conditional on all-nine-invariant does NOT trigger.

One-sentence verdict (also in `verdict:`): the internal known-unknown readout
survives every prompt contract in presence (refit >= 0.988) but its
neutral-prompt direction transfers fully only to the plain contract, dropping
0.06-0.11 AUROC under P-rc and P-struct on all three checkpoints - partial
transfer, no rotation, no suppression, falsifier not fired.
