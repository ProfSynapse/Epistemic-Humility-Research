---
aliases:
- 50 few-shot examples nearly match finetuned verbalized calibration
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:few-shot-unlocks-verbalized-calibration
  type: mechanism
  status: canonical
cause: Providing k=50 stochastic [[in-context-learning]] examples of verbalized probability to [[gpt-3]]
effect: '[[calibration]] performance approaches that of a supervised finetuned model trained on 10k examples, suggesting pre-existing latent representations are activated rather than new features being learned'
polarity: enables
related:
- '[[2205.14334--teaching-models-uncertainty-in-words]]'
- '[[in-context-learning]]'
- '[[gpt-3]]'
- '[[calibration]]'
relationships:
- type: supported_by
  target: '[[2205.14334--teaching-models-uncertainty-in-words]]'
  target_id: paper:2205.14334
  confidence: high
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
- type: related_to
  target: '[[gpt-3]]'
  target_id: model:gpt-3
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
---

If calibration were a skill that required learning new representations, a few dozen in-context examples would be far too few to match thousands of finetuning examples. The rapid convergence observed with 50 ICL examples indicates that the model's pretrained representations already encode the necessary epistemic information, and the few-shot examples merely activate and channel that information into verbalized probability outputs. The teaching-models-uncertainty paper (arXiv:2205.14334) validates this interpretation by showing the ICL-finetuning gap closes well before the capacity limits of the context window are reached.
