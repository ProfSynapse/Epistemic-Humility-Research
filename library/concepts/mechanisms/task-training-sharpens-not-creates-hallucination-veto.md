---
aliases:
- Task training sharpens but does not create the hallucination veto
- Training amplifies an existing correctness veto
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:task-training-sharpens-not-creates-hallucination-veto
  type: mechanism
  status: canonical
cause: "Applying abstention-SFT plus GRPO on top of the instruction-tuned base, then reading the post-generation correctness probe on confidently-answered unanswerable questions (hallucinations)."
effect: "The correctness probe already ranks confident confabulation below correct answers on the untrained base (AUROC 0.754), and task training sharpens this veto to lowest-of-all-trust (0.980; hallucination dial-mean shifts 0.271 to 0.018) while adding ~0 to the answerability gate - training amplifies a pre-existing veto rather than creating it."
polarity: increases
related:
- '[[internal-twosignal-readout--training-free]]'
- '[[answerability-axis-present-without-task-training]]'
- '[[calibration-aware-training-prevents-confidence-drift]]'
- '[[calibration-hallucination-tradeoff]]'
- '[[rlhf-reduces-closed-domain-hallucination]]'
- '[[ternary-reward-enables-abstention-over-hallucination]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[internal-twosignal-readout--training-free]]'
  target_id: paper:internal-twosignal
  confidence: high
- type: related_to
  target: '[[answerability-axis-present-without-task-training]]'
  target_id: mechanism:answerability-axis-present-without-task-training
  confidence: high
- type: related_to
  target: '[[calibration-aware-training-prevents-confidence-drift]]'
  target_id: mechanism:calibration-aware-training-prevents-confidence-drift
  confidence: medium
- type: related_to
  target: '[[calibration-hallucination-tradeoff]]'
  target_id: mechanism:calibration-hallucination-tradeoff
  confidence: medium
- type: related_to
  target: '[[rlhf-reduces-closed-domain-hallucination]]'
  target_id: mechanism:rlhf-reduces-closed-domain-hallucination
  confidence: medium
- type: related_to
  target: '[[ternary-reward-enables-abstention-over-hallucination]]'
  target_id: mechanism:ternary-reward-enables-abstention-over-hallucination
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
---

Comparing Amendment W (raw base) with Amendment U (trained checkpoint) on the same
SelfAware hallucination surface: the correctness dial vetoes confident confabulation
training-free at AUROC 0.754 (W-G1), and task training sharpens it to 0.980 (U-G3).
Quantified, training buys +0.226 AUROC of veto sharpening and ~0 answerability-gate
gain. This refines the common framing that hallucination-reducing training installs
a new capability ([[rlhf-reduces-closed-domain-hallucination]],
[[ternary-reward-enables-abstention-over-hallucination]]): here it amplifies an
existing internal veto. Single-model, single-seed; the hallucination label is
structural (unknown and answered), pending graded confirmation.
