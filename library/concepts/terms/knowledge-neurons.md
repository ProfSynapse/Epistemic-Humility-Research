---
aliases:
- knowledge neuron
- fact-expressing neurons
tags:
- kg/term
- concept
- term
kg:
  id: term:knowledge-neurons
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
- '[[ffn-as-key-value-memory]]'
- '[[knowledge-attribution]]'
- '[[knowledge-surgery]]'
relationships:
- type: proposed_by
  target: '[[2104.08696--knowledge-neurons-pretrained-transformers]]'
  target_id: paper:2104.08696
  confidence: high
- type: related_to
  target: '[[ffn-as-key-value-memory]]'
  target_id: term:ffn-as-key-value-memory
---

Knowledge neurons are specific FFN intermediate neurons in pretrained Transformers whose activations are causally responsible for expressing relational factual knowledge, identified via integrated-gradient attribution over fill-in-the-blank cloze prompts. Suppressing them decreases the model's probability of producing the correct answer, while amplifying them increases it. They tend to be concentrated in the upper layers of the network and are activated specifically by prompts that express the same underlying knowledge across paraphrase variants. The discovery operationalizes the idea from [[ffn-as-key-value-memory]] that FFN layers store factual associations in their weight matrices.

**Why it matters here:** Understanding where and how knowledge is stored in model weights is foundational for studying the knowledge boundary and the conditions under which a model will confidently produce a wrong answer versus abstain, linking mechanistic structure to calibration and epistemic humility.

**Lineage:** conceptually grounded in [[ffn-as-key-value-memory]]; localized and edited via [[knowledge-attribution]] and [[knowledge-surgery]].
