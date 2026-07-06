---
aliases:
- Backtracking Removal Causes Calibration Drop with Retained Discrimination
- linearized CoT degrades calibration not discrimination
- backtracking ablation ECE worsens AUROC preserved
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:backtracking-ablation-drops-calibration
  type: mechanism
  status: canonical
cause: "Ablation that removes backtracking and alternative-exploration moves from the chain-of-thought, linearizing the reasoning trace"
effect: "[[expected-calibration-error]] worsens (model becomes overconfident) while [[auroc]] is paradoxically preserved, dissociating calibration from discrimination"
polarity: decreases
related:
- '[[2505.14489--reasoning-models-better-express-their-confidence]]'
- '[[calibration]]'
- '[[expected-calibration-error]]'
- '[[auroc]]'
- '[[chain-of-thought-prompting]]'
- '[[slow-thinking-enables-dynamic-confidence-calibration]]'
relationships:
- type: supported_by
  target: '[[2505.14489--reasoning-models-better-express-their-confidence]]'
  target_id: paper:2505.14489
  confidence: high
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
- type: related_to
  target: '[[expected-calibration-error]]'
  target_id: metric:expected-calibration-error
- type: related_to
  target: '[[auroc]]'
  target_id: metric:auroc
- type: related_to
  target: '[[slow-thinking-enables-dynamic-confidence-calibration]]'
  target_id: mechanism:slow-thinking-enables-dynamic-confidence-calibration
---

arXiv:2505.14489 constructs linearized-CoT variants by removing backtracking and uncertainty-marking steps, holding all other reasoning content constant, and measures calibration separately from discrimination. ECE rises substantially relative to the full slow-thinking trace, while AUROC remains largely unchanged, demonstrating that backtracking specifically enables probability calibration rather than rank ordering. This dissociation refutes the simpler hypothesis that better discrimination drives calibration: the two metrics respond to entirely different components of the reasoning process, with backtracking as the functional element for the calibration component.
