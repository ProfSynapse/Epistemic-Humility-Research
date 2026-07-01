---
aliases:
- The answerability axis is present without task training
- Answerability readable on the untrained base
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:answerability-axis-present-without-task-training
  type: mechanism
  status: canonical
cause: "Reading a linear probe on residual-stream activations at the prompt anchor of an instruction-tuned base model, with no abstention-SFT and no reinforcement learning of our own."
effect: "The probe separates answerable from unanswerable questions at near-ceiling AUROC (0.84-0.997 depending on pool), essentially unchanged by our downstream task training (+0.015 from the GRPO-v2 LoRA on matched data) - the answerability representation is present before task training, not installed by it."
polarity: enables
related:
- '[[internal-twosignal-readout--training-free]]'
- '[[answerability-probe-transfers-across-qa-datasets]]'
- '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
- '[[pretrained-latent-representations-enable-calibration-generalization]]'
- '[[rlhf-improves-unanswerability-recognition]]'
- '[[answerability-subspace]]'
- '[[linear-probe]]'
relationships:
- type: supported_by
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: related_to
  target: '[[answerability-probe-transfers-across-qa-datasets]]'
  target_id: mechanism:answerability-probe-transfers-across-qa-datasets
  confidence: high
- type: related_to
  target: '[[hidden-state-linearly-encodes-unanswerability-despite-hallucination]]'
  target_id: mechanism:hidden-state-linearly-encodes-unanswerability-despite-hallucination
  confidence: high
- type: related_to
  target: '[[pretrained-latent-representations-enable-calibration-generalization]]'
  target_id: mechanism:pretrained-latent-representations-enable-calibration-generalization
  confidence: medium
- type: related_to
  target: '[[rlhf-improves-unanswerability-recognition]]'
  target_id: mechanism:rlhf-improves-unanswerability-recognition
  confidence: medium
- type: related_to
  target: '[[answerability-subspace]]'
  target_id: term:answerability-subspace
  confidence: high
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
  confidence: high
---

Across Amendments O/P/Q/W the answerability axis is linearly decodable from
residual activations at the prompt anchor of the raw Qwen3-4B instruct base with no
task training of ours: known vs unknown AUROC 0.997 on the SelfAware anchor (W-G2)
and 0.836 on a matched frozen TriviaQA set, versus 0.851 for the GRPO-v2 LoRA on the
same rows. Our abstention-SFT/RL adds ~0.015 on matched data. It contrasts with
[[rlhf-improves-unanswerability-recognition]] (which attributes the gain to RLHF):
here the signal is already present pre-task-training, and training relocates
behavior rather than creating the representation. Scope: "untrained" means no
abstention-SFT/RL of ours; the base is still upstream instruction-tuned.
