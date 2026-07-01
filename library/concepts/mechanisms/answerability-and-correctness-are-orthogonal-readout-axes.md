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
relationships:
- type: supported_by
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
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
