---
aliases:
- instruction tuning collapses calibration
- fine-tuning suppresses uncertainty expression
- SFT overconfidence without accuracy gain
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:instruction-tuning-induces-calibration-collapse
  type: mechanism
  status: canonical
cause: "Instruction tuning (SFT on instruction-following data or chat-style pairs) applied to a base pretrained model on tasks requiring structured reasoning"
effect: "Model confidence increases sharply while accuracy remains flat or decreases, producing large ECE and ACE values and bimodal or peaked confidence distributions, calibration collapse without capability gain"
polarity: increases
related:
- '[[2509.20088--causal-understanding-uncertainty]]'
- '[[verbalized-confidence-imitation-overconfidence]]'
- '[[overconfidence]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[adaptive-calibration-error]]'
- '[[instruction-tuning-causes-over-abstention]]'
relationships:
- type: supported_by
  target: '[[2509.20088--causal-understanding-uncertainty]]'
  target_id: paper:2509.20088
  confidence: high
- type: related_to
  target: '[[verbalized-confidence-imitation-overconfidence]]'
  target_id: mechanism:verbalized-confidence-imitation-overconfidence
  confidence: high
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
  confidence: high
- type: related_to
  target: '[[adaptive-calibration-error]]'
  target_id: metric:adaptive-calibration-error
  confidence: high
- type: related_to
  target: '[[instruction-tuning-causes-over-abstention]]'
  target_id: mechanism:instruction-tuning-causes-over-abstention
  confidence: high
---

Lithgow-Serrano et al. (2025) show that applying instruction tuning to Pythia base models (producing Dolly-v2-7B and Dolly-v2-12B) nearly triples ECE (from 0.131 to 0.363 at the 7B scale) while holding accuracy flat at around 24%. Qwen-7B-base, an instruction-tuned model, reaches ECE 0.493 with greater than 95% predicted confidence despite only 32.8% accuracy. The paper argues that instruction tuning teaches models to express confidence as a conversational behavior, suppressing appropriate uncertainty even when the underlying representational capacity for the task has not improved. This is a calibration collapse distinct from over-abstention: the model does not refuse; it answers confidently and incorrectly.
