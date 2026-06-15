---
aliases:
- Unknown examples are learned substantially slower than Known examples during SFT
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:unknown-examples-learned-slower
  type: mechanism
  status: canonical
cause: Fine-tuning examples that introduce new factual knowledge (Unknown in [[slick]]) rather than reinforcing existing parametric knowledge
effect: Slower gradient-driven fitting rate relative to Known examples, so [[hallucination]] emerges primarily in later training stages as overfitting
polarity: decreases
related:
- '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
- '[[slick]]'
- '[[hallucination]]'
relationships:
- type: supported_by
  target: '[[2405.05904--finetuning-new-knowledge-hallucinations]]'
  target_id: paper:2405.05904
  confidence: high
- type: related_to
  target: '[[slick]]'
  target_id: method:slick
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
---

Known examples align with existing parametric representations, so gradients converge quickly and efficiently. Unknown examples have no such existing representation to anchor on, requiring the model to build new associations from scratch, which takes more gradient steps and creates overfitting pressure in later training epochs. The finetuning-new-knowledge-hallucinations paper (arXiv:2405.05904) tracks per-example training loss curves, confirming that Unknown examples show substantially slower convergence and that hallucination on those questions peaks in later epochs when the model overfits.
