---
aliases:
- OthelloGPT
- Othello-GPT
tags:
- kg/model
- concept
- model
kg:
  id: model:othello-gpt
  type: model
  status: canonical
area: mechanistic-interpretability
related:
- '[[emergent-world-model]]'
- '[[linear-representation-hypothesis]]'
- '[[linear-probe]]'
relationships:
- type: related_to
  target: '[[emergent-world-model]]'
  target_id: term:emergent-world-model
- type: related_to
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: related_to
  target: '[[linear-probe]]'
  target_id: method:linear-probe
---

OthelloGPT is an 8-layer autoregressive GPT model (512-dimensional hidden space, 8 attention heads per layer) trained solely to predict legal moves in Othello games given a sequence of prior moves, with no explicit board state or rule encoding. Despite this purely sequential training objective, linear probes trained on its internal activations recover accurate board representations, constituting evidence for [[emergent-world-model]] formation. It became a canonical controlled test-bed for studying how sequence models internalize structured world states.

**Why it matters here:** OthelloGPT demonstrates that models can form internal knowledge representations beyond their training signal, which is conceptually prior to studying what models know vs. do not know and how self-knowledge representations emerge.

**Lineage:** primary evidence base for [[emergent-world-model]] and [[relative-board-encoding]]; analysis relies on [[linear-probe]] under the [[linear-representation-hypothesis]].
