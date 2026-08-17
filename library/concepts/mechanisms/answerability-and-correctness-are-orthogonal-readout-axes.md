---
aliases:
- Answerability and correctness are orthogonal readout axes
- Two-signal pipeline beats a fused scalar
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answerability-and-correctness-are-orthogonal-readout-axes
  type: mechanism
  status: canonical
cause: "Fusing the answerability readout scalar (read at the prompt anchor) and the correctness readout scalar (read post-generation) into a single combined confidence score, instead of applying them as two sequential stages."
effect: "Fusion degrades correctness ranking relative to the correctness dial alone (delta -0.014, paired bootstrap CI excludes 0) because the two axes are orthogonal; the mechanism therefore deploys as a two-stage pipeline - gate abstains on unanswerable, dial surfaces trust on what is answered - not as one fused scalar."
polarity: decreases
related:
- '[[internal-twosignal-readout--training-free]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
- '[[faithful-calibration]]'
- '[[fusion-nonredundance-redo]]'
relationships:
- type: supported_by
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: supported_by
  target: '[[fusion-nonredundance-redo]]'
  target_id: experiment:fusion-nonredundance-redo
  confidence: high
  evidence:
  - "experiments/fusion-nonredundance-redo/AMENDMENT.md#outcome (FR-G0 pass, FR-G1 pass: registered rerun of the byte-identical PR #128 instrument reproduces delta -0.0142, CI [-0.0214, -0.0074] exactly)"
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: medium
- type: related_to
  target: '[[faithful-calibration]]'
  target_id: term:faithful-calibration
  confidence: medium
---

The Stage 1.5 per-item integration (PR #128) reads the answerability gate and the
correctness dial on the same answered items and finds them orthogonal: a combined
scalar scores correctness at 0.804 versus the dial-alone 0.819 (delta -0.014, CI
[-0.021, -0.007]). The two signals answer different questions (is this question
answerable? vs is this answer correct?) and are best deployed as a pipeline rather
than fused. The gate transfers cross-prompt; the axes do not collapse into one.

[[fusion-nonredundance-redo]] reruns the same instrument under registration
(2026-08-17, FR-G0/FR-G1 both pass): dial-alone 0.8186, combined 0.8044, delta
-0.0142, paired bootstrap CI [-0.0214, -0.0074], matching the unregistered PR
#128 observation to full precision. The fusion-cost evidence for this
mechanism is now a registered confirmation rather than an unregistered
lab-notebook diagnostic.
