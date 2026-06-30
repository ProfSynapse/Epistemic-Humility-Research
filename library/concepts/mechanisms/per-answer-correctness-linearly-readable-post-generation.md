---
aliases:
- Per-answer correctness is linearly readable post-generation
- Correctness dial read after the answer
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:per-answer-correctness-linearly-readable-post-generation
  type: mechanism
  status: canonical
cause: "Fitting a linear probe on residual-stream activations at the post-generation content token (after the model has emitted its answer), as opposed to at the pre-generation prompt anchor."
effect: "The probe ranks whether that specific answer is correct (AUROC 0.82-0.83), and reading after the answer beats reading before it by +0.065 (bootstrap CI excludes 0) - a self-evaluation signal that is localized to the post-generation position, distinct from the pre-generation answerability axis."
polarity: enables
related:
- '[[internal-twosignal-readout--training-free]]'
- '[[probe-reads-recall-not-truth]]'
- '[[auxiliary-model-predicts-llm-confidence-from-generations-alone]]'
- '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
- '[[linear-probe]]'
- '[[auroc]]'
relationships:
- type: supported_by
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: related_to
  target: '[[probe-reads-recall-not-truth]]'
  target_id: mechanism:probe-reads-recall-not-truth
  confidence: medium
- type: related_to
  target: '[[auxiliary-model-predicts-llm-confidence-from-generations-alone]]'
  target_id: mechanism:auxiliary-model-predicts-llm-confidence-from-generations-alone
  confidence: medium
- type: related_to
  target: '[[estimator-divergence-invalidates-single-probe-faithfulness]]'
  target_id: mechanism:estimator-divergence-invalidates-single-probe-faithfulness
  confidence: medium
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
  confidence: medium
---

Amendment S (replicated on the deployed checkpoint by Amendment T) shows a second
internal axis beyond answerability: a linear probe at the post-generation content
token reads whether the just-emitted answer is correct (S: AUROC 0.834 on the
Instruct base, L20; T: 0.819 on clean-SFT to GRPO-v2, L22). Reading after the answer
beats reading before by +0.065 (CI excludes 0) - the first post-generation
self-evaluation win in this program. The signal peaks mid-network, not late. This is
the "dial" half of the two-signal pipeline (the answerability axis is the "gate").
