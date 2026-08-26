# Gate-dial fusion non-redundance redo (registered CPU rerun)

Status: draft (not signed; do not launch as confirmatory evidence).

Keep this document the prose home for the experiment. The machine state lives in
`experiment.yaml` and is never duplicated here.

## Motivation and posture

Paper 4 §4.3 quotes Δ −0.014 (fusing the gate score into the dial degrades
correctness triage) as the empirical corroboration that the two axes are
non-redundant. That number came from an unregistered CPU lab-notebook
diagnostic (PR #128, Stage 1.5): deterministic committed code, committed
result JSON, but no experiment directory and no pre-stated gates, so the
paper carries it as unregistered corroboration only, with non-redundance
resting on the position/robustness dissociation. This cell re-runs the exact
committed instrument under registration so the paper can quote a registered
number. Exploratory tier; single checkpoint; PI approved the design
2026-08-17 (draft spec: docs/preparation/amendment-draft-fusion-redo.md).

Drafting correction disclosed at signing: the approved draft set the FR-G0
reproduction target at 0.834 (the plain-dial headline from a different
cell). The correct instrument-validity reference is the committed
diagnostic's own dial-alone value on these exact inputs, 0.8186
(`experiments/unified-two-signal-dial-veto/artifacts/two_signal_stage1p5_integration.json`,
part_b_correctness_triage.auroc_dial_alone). The committed JSON also already
records the numeric bootstrap CI for the prior observation
(Δ −0.0142, CI [−0.0214, −0.0074]), which the paper had summarized as
"excludes 0"; the prior observation below quotes the committed values.

## Design

- Instrument: `experiments/common/mechinterp/two_signal_stage1p5_integration.py`
  run VERBATIM (no code changes), Part B (out-of-fold logistic combiner over
  [gate_score, dial_score]; paired bootstrap on Δ = AUROC(combined) −
  AUROC(dial)); gate layer 33, dial layer 22, seed 20260630, n_boot 2000 (the
  script defaults, which are the PR #128 configuration).
- Substrate: deployed Qwen3-4B clean-SFT-merged + GRPO-v2 LoRA checkpoint's
  existing extractions; no new generation, CPU only.
- Inputs (recorded by the committed Stage-1 JSON; present on disk at the
  post-reorg `phase1-data` prefix, same path migration as the paper-3
  geometry artifacts):
  - gate-dir: `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2-seed1-selfaware/hidden_states_selfaware_clean_sft_grpo_v2_full/extraction__55254a04aa1f`
  - dial-dir: `archive/experiment/phase1-data/probe/qwen3-4b-clean-sft-grpo-v2/amendment_t/stage2`
- Output: result JSON committed under this cell's `analysis-committed/`
  (aggregates only): AUROC(dial), AUROC(combined), Δ, numeric bootstrap CI.

## Prediction

Δ = AUROC(combined) − AUROC(dial) ≤ 0 on the deployed checkpoint's answerable
items (prior unregistered observation: −0.0142, CI [−0.0214, −0.0074]).

## Falsifier

Δ ≥ +0.020 with the paired bootstrap CI excluding 0: the gate adds real
correctness information beyond the dial, and §4.3's fusion-cost sentence is
removed, leaving non-redundance on the position/robustness dissociation
alone.

## Gates

- FR-G0 (instrument validity): dial-alone AUROC within ±0.005 of the
  committed diagnostic's 0.8186 on the same inputs, and the OOF fold
  structure executes without degenerate folds. FR-G0 fail → instrument
  invalid, no claim either way.
- FR-G1 (confirmation): Δ < +0.010. Non-redundance for correctness triage is
  confirmed under registration; §4.3 quotes the registered Δ with its numeric
  CI and drops the weaker-warrant caveat.
- FR-F1 (falsifier): Δ ≥ +0.020 AND bootstrap CI excludes 0 (as above).
- Between FR-G1 and FR-F1 (+0.010 ≤ Δ < +0.020, or CI includes 0 above
  +0.010): indeterminate; report the number straight, §4.3 keeps
  dissociation-first wording and quotes the registered Δ descriptively.

## Predictions scoreboard

| Predictor | Call |
|-----------|------|
| orchestrator | FR-G0 pass, FR-G1 pass: deterministic rerun of committed code on identical pinned inputs; Δ within ±0.002 of −0.0142 |
| user | |

## Outcome

Run 2026-08-17 (registered pass, pinned instrument sha ba61ae9f, pinned
inputs, seed 20260630, n_boot 2000). Result JSON:
`analysis-committed/fusion_nonredundance_redo_result.json`.

- AUROC(dial alone) = 0.8186; AUROC(combined gate+dial) = 0.8044;
  Δ = −0.0142, paired bootstrap CI [−0.0214, −0.0074].
- FR-G0 PASS: dial-alone reproduces the committed diagnostic's 0.8186
  exactly; 5-fold OOF executed with no degenerate fold.
- FR-G1 PASS: Δ = −0.0142 < +0.010. Non-redundance for correctness triage
  confirmed under registration.
- FR-F1 not fired.
- The registered values are identical to the prior unregistered PR #128
  observation to full precision (deterministic instrument, identical pinned
  inputs), which is itself the FR-G0 parity confirmation.

Consequence per the gates fixed at signing: paper 4 §4.3 quotes the
registered Δ −0.0142 (CI [−0.0214, −0.0074]) and drops the weaker-warrant
caveat; non-redundance keeps the position/robustness dissociation as
primary support with the fusion cost as registered corroboration.

Verdict: confirmed. Fusing the gate score into the dial degrades
correctness triage (Δ −0.0142, CI excludes 0 on the negative side); the two
axes are non-redundant for that task on the deployed checkpoint.
