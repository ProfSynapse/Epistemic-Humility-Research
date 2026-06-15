---
aliases:
- impaired self-expression
- expression failure
tags:
- kg/term
- concept
- term
kg:
  id: term:spurious-dishonesty
  type: term
  status: canonical
area: terms
related:
- '[[2511.12991--finetuned-llms-know-they-dont-know]]'
relationships:
- type: proposed_by
  target: '[[2511.12991--finetuned-llms-know-they-dont-know]]'
  target_id: paper:2511.12991
  confidence: high
---

Spurious dishonesty is the observation that SFT-induced overconfidence in LLMs does not arise from loss of internal knowledge-boundary awareness, but from a failure to faithfully express that preserved awareness in generated text. Linear probes trained on fine-tuned representations maintain high AUROC when discriminating answerable from unanswerable questions, indicating the model internally distinguishes what it knows from what it does not, yet suppresses that signal in its outputs.

**Why it matters here:** The distinction matters for the SFT-vs-DPO-vs-KTO abstention study because it implies that the failure mode to fix is a surface-level expression gap rather than a representational gap, which changes what kind of intervention (expression-targeted corrections like [[honesty-critical-neurons-restoration]] vs. full retraining) is appropriate.

**Lineage:** closely linked to [[honesty-critical-neurons-restoration]], the method proposed to address it, and to [[spurious-dishonesty]] as an empirical diagnostic using [[auroc]] on internal representations.
