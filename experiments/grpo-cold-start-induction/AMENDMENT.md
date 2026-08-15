# Cold-start GRPO: can the appropriateness reward induce abstention from the base model?

Status: SIGNED (2026-08-13; instrument pins in `experiment.yaml`). Launch authorized 2026-08-13, queued behind `dial-logprob-t-deployed-confirmatory` on the local GPU.

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 2's cold-start comparison (confirmatory, three seeds) covers SFT, DPO,
and KTO trained from the base model; its finding "only SFT induces
abstention" is therefore demonstrated against the two preference objectives
only. GRPO entered the program later as an exploratory extension and every
GRPO arm sits on an SFT base — no cold-start GRPO arm exists anywhere in the
program (verified across the manuscript, `grpo-three-seed-confirmatory`, and
the phase-1 training configs; PI raised the gap during manuscript review
2026-08-13). This cell closes the 2x4 design: GRPO under the same rebalanced
appropriateness reward, trained from the raw base, single seed.

Exploratory tier (tier-2 amendment), reported with the paper's exploratory
GRPO layer, never pooled with the confirmatory cold-start block.

The registrants expect a null, and the design's job is to make the null
INTERPRETABLE. Two distinct null mechanisms are pre-stated:

- **Null-A (trained but did not learn):** the reward produces gradient
  (nonzero group advantage on a meaningful fraction of groups), training
  completes, and eval refusal recall stays near zero — the cold DPO/KTO
  shape, extended to RL.
- **Null-B (no trainable signal):** GRPO is on-policy; the reward can only
  reinforce behavior that appears in sampled rollouts. If base rollouts
  essentially never abstain and rarely parse as valid contract output, group
  rewards are near-constant, advantages ~0, and nothing trains. This is the
  registrants' modal expectation. It is still a deployment-relevant result
  (this reward cannot bootstrap abstention from the base), but it is a
  weaker objective-comparison claim than Null-A, and the two must not be
  conflated in reporting.

## Design

One training run + the standard eval, cloning the pinned SFT-warmed GRPO
instrument with only the source substituted:

- Trainer: `synaptic-tuner/Trainers/grpo/train_grpo.py`, verbatim from the
  `clean_sft_grpo_v2` arm of `grpo-three-seed-confirmatory` (`cell.yaml`
  arm spec): dataset `grpo`, reward_variant v2 (rebalanced), num_generations
  4, per_device_train_batch_size 32, seed 1. Single difference: `source` is
  the raw base (Qwen3-4B), not `merged(clean_sft)`.
- Eval: the standard full SelfAware eval under the same contract and scorer
  as the cold-start block (the instrument the confirmatory matrix used),
  unchanged.
- Pre-registered training diagnostics, logged at fixed steps and reported
  UNCONDITIONALLY regardless of outcome:
  (i) per-group reward variance — fraction of groups with zero advantage;
  (ii) fraction of rollouts parsing as valid contract output;
  (iii) abstention rate within rollouts.
  The Null-A/Null-B call is made from these diagnostics per the CG-G1
  criterion below, fixed here before the run.
- Engine exception (generation-bearing type, sign-gate): the rollout engine
  is the locked trainer's own generation path, NOT vLLM —
  `instrument.engine_exception: {kind: parity-locked}`. Reason: the
  cold-vs-warmed comparison is only valid if the cold arm uses the identical
  trainer + rollout stack as the SFT-warmed GRPO arms it is compared to;
  switching the rollout engine would confound the comparison with an
  instrument change. The eval stage likewise reuses the matrix's eval
  instrument for parity.

Instrument configs pinned at sign: `cell.yaml`, `gates.yaml`, plus the
materialized trainer config for the cold arm.

## Prediction

Eval refusal recall below 10% (cold DPO/KTO read ~0%), with Null-B (no
trainable signal: ≥ 90% of training groups at zero advantage) as the modal
mechanism.

## Falsifier

Cold-start GRPO induces abstention: eval refusal recall ≥ 20% with
over-refusal reported alongside. That would falsify the generalized "only
SFT induces abstention from the base model" reading and paper 2 would have
to say so.

## Gates

- CG-G0 (integrity precondition, pre-outcome stop): training either
  completes the registered step budget or records an honest degenerate-
  reward stop (no silent restarts, no reward retuning); the eval runs the
  full row set with every row scored; the three diagnostics are present in
  the run record. Any missing diagnostic is a stop, not a footnote.
- CG-G1 (mechanism call, fixed before the run): Null-B is declared if ≥ 90%
  of training groups have zero advantage across the run; otherwise the
  outcome is read as trained (Null-A if eval recall < 10%, falsifier zone if
  ≥ 20%, ambiguous band 10-20% reported as such). The 90/10/20 thresholds
  are fixed here and never retuned after the result.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | Null-B: ≥90% zero-advantage groups, eval recall <10% |
| user | expects the null (same result as cold DPO/KTO; no SFT tendency to IDK to reinforce) |

## Budget

One GRPO training run on the local 3090 (the warmed v2 arm peaked 89.22%
reserved VRAM at batch 32; hours, not minutes) plus one full SelfAware eval.
No cloud spend. Launch requires explicit PI approval after signing.

## Outcome

Training run 2026-08-13T18:20Z -> 2026-08-14T03:35Z, local RTX 3090, exit 0,
full 1,861-step budget (9.23h wall clock; the NOTEBOOK's earlier "~8.2h" was
an estimate, corrected here). One empty aborted run dir predates the real
run by 68 seconds (`20260813_181904`, zero files, no training started) —
disclosed as an honest false start, not a silent restart. Eval
2026-08-14T09:27-09:54Z under the pinned instrument (filled config sha
3ad3f033a5cec949 stamped on all rows; copy in `analysis-committed/`).

**CG-G0 PASS**: clean completion (no restarts, no reward retuning —
reward file git-clean at 21cd5c50); full eval coverage 3,369/3,369; all
three registered diagnostics present and well-formed (pinned
`grpo_cold_diagnostics.py` over the 1,861-record reward-debug JSONL;
independently re-derived to six decimals in red-team audit).

**Diagnostics (reported unconditionally):** zero-advantage group fraction
0.6478 (9,645/14,888 groups); valid contract parse 0.9775; rollout
abstention rate 0.4414 (already ~59% on unknown-labeled rollouts in the
first 25 steps, essentially flat across training). TRL's own
frac_reward_zero_std (0.47-0.755 across the run) corroborates.

**CG-G1: not Null-B** (0.6478 < 0.90 floor; gradient was real: mean reward
0.362 -> 0.603, KL 0.005 -> 0.155). Eval refusal recall **85.66%**
(884/1,032; over-refusal 60.89%, truthful 38.14%) — the registered >= 20%
falsifier threshold FIRED, far above the band. The registered prediction
(recall < 10%, Null-B modal) was wrong on both counts.

**Mechanism, per the contemporaneous panel:** the falsifier's causal verb
does not survive the base counterfactual this cell's design lacked.
`prompt-vs-training-panel` (registered before its run, R2 band frozen at
signing) measured the raw base under this cell's identical eval contract at
recall **90.89%** / over-refusal 65.38% — above this checkpoint. Training
moved the model slightly TOWARD answering (both error rates down ~4-5pp),
and under a structure-only prompt this checkpoint reads 0.00% recall
(base-identical; panel arm cold_grpo_seed1_pstruct). Per the panel's R2
band: cold GRPO **preserves and sharpens instruction-elicited abstention**;
it does not induce abstention, and it internalizes none.

Hygiene disclosures (red-team audit 2026-08-14, all lead-verified): 117
SelfAware known-labeled questions overlap the GRPO train file (program-wide,
pre-existing; recall untouched; excluding them makes this arm look slightly
worse, over-refusal 61.94); the pinned trainer config's step-budget comment
says ~465 steps where TRL's prompt-per-step arithmetic gives 1,861 (comment
wrong, instrument correct, pinned file left untouched); training-vs-eval
refusal rates differ strongly with decoding regime (rollouts at T=1.35
refuse-on-known ~23% vs greedy eval 60.89%) — eval figures are
regime-dependent.

**One-sentence verdict:** cold-start GRPO under the rebalanced
appropriateness reward trained on real gradient (not Null-B) and landed at
85.66% eval refusal recall, firing the registered >= 20% falsifier — but
the panel's base counterfactual (90.89% under the same instruction, 0%
without it, and 0% for this checkpoint without it) shows the reward
preserved and sharpened prompt-elicited abstention rather than inducing
any, so the registered prediction is falsified and the "induction" framing
is retired with it.
