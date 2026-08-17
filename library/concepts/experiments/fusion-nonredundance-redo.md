---
title: fusion-nonredundance-redo
aliases:
- Gate-dial fusion non-redundance redo
- registered CPU rerun of the Stage 1.5 fusion-cost diagnostic
tags:
- kg/experiment
- experiment
- correctness-dial
- calibration
kg:
  id: experiment:fusion-nonredundance-redo
  type: experiment
  status: canonical
related:
- '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
- '[[internal-twosignal-readout--training-free]]'
- '[[auroc]]'
relationships:
- type: tests
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
  evidence:
  - "experiments/fusion-nonredundance-redo/AMENDMENT.md Motivation and posture (registered CPU rerun of the exact committed PR #128 Stage 1.5 instrument that produced this mechanism's unregistered delta -0.014, so paper 4 section 4.3 can quote a registered number)"
- type: supports
  target: '[[answerability-and-correctness-are-orthogonal-readout-axes]]'
  target_id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  confidence: high
  evidence:
  - "experiments/fusion-nonredundance-redo/AMENDMENT.md#outcome (FR-G0 pass, FR-G1 pass: dial-alone AUROC 0.8186, combined 0.8044, delta -0.0142, paired bootstrap CI [-0.0214, -0.0074], identical to the prior unregistered PR #128 observation to full precision)"
- type: related_to
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
  evidence:
  - "the registered delta this cell produces is the number paper 4 section 4.3 quotes as corroboration for non-redundance between the gate and dial axes"
- type: measures
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: high
---

Exploratory-tier, single-checkpoint registered rerun of the committed Stage
1.5 per-item integration instrument (`experiments/common/mechinterp/two_signal_stage1p5_integration.py`,
verbatim, sha `ba61ae9f`): an out-of-fold logistic combiner over
[gate_score, dial_score] against the correctness dial alone, with a paired
bootstrap on the delta, on the deployed Qwen3-4B clean-SFT-merged +
GRPO-v2-LoRA checkpoint's existing cached hidden-state extractions (CPU
only, no new generation). Registers under FR-G0/FR-G1/FR-F1 gates the same
diagnostic that produced the unregistered PR #128 fusion-cost number paper 4
section 4.3 had been quoting as corroboration only.

Resolved 2026-08-17. **FR-G0 PASS**: dial-alone AUROC reproduces the
committed diagnostic's 0.8186 exactly on the same pinned inputs, 5-fold
out-of-fold structure executed with no degenerate fold. **FR-G1 PASS**:
delta = AUROC(combined) - AUROC(dial) = -0.0142 (AUROC dial-alone 0.8186,
combined 0.8044), paired bootstrap CI [-0.0214, -0.0074], well inside the
+0.010 confirmation bound. FR-F1 (falsifier: delta >= +0.020 with CI
excluding 0) did not fire. The registered values match the prior
unregistered PR #128 observation to full precision, since the instrument
and inputs are byte-identical; this exact match is itself the FR-G0 parity
confirmation, not a separate replication.

**Why it matters here:** promotes [[answerability-and-correctness-are-orthogonal-readout-axes]]'s
fusion-cost evidence from an unregistered lab-notebook diagnostic (deterministic
code and committed result, but no pre-stated gates) to a registered
confirmation. Per the gates fixed at signing, paper 4 section 4.3 now quotes
the registered delta -0.0142 (CI [-0.0214, -0.0074]) and drops the
weaker-warrant caveat; non-redundance between the gate and dial axes keeps
the position/robustness dissociation as primary support with the fusion
cost as registered corroboration, not as the sole evidence.

Source of truth: `experiments/fusion-nonredundance-redo/AMENDMENT.md`,
Outcome section, resolved 2026-08-17.
