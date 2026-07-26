---
aliases:
- Entropy Neurons
- entropy neuron
tags:
- kg/term
- concept
- term
kg:
  id: term:entropy-neurons
  type: term
  status: canonical
area: mechanistic-interpretability
related:
- '[[2406.16254--confidence-regulation-neurons-language-models]]'
- '[[unembedding-null-space]]'
- '[[layer-normalization]]'
- '[[confidence-regulation-neurons]]'
relationships:
- type: proposed_by
  target: '[[2406.16254--confidence-regulation-neurons-language-models]]'
  target_id: paper:2406.16254
  confidence: high
- type: related_to
  target: '[[unembedding-null-space]]'
  target_id: term:unembedding-null-space
  confidence: high
- type: related_to
  target: '[[layer-normalization]]'
  target_id: term:layer-normalization
  confidence: high
- type: related_to
  target: '[[confidence-regulation-neurons]]'
  target_id: term:confidence-regulation-neurons
  confidence: high
---

Entropy neurons are individual MLP neurons distinguished by an unusually high
output-weight norm combined with low variance in their direct projection onto
the logits (LogitVar). They act by increasing the residual-stream norm, which
shrinks the final [[layer-normalization|LayerNorm]] scale and uniformly flattens
the output distribution, raising its entropy with minimal direct effect on any
individual logit.

**Why it matters here:** Stolfo et al. show entropy neurons write their output
weights almost exclusively into the [[unembedding-null-space]], and observe
their signature (high norm, low LogitVar, large LayerNorm-mediated effect)
across GPT-2, Pythia, Phi-2, Gemma 2B, and LLaMA2 up to 7B parameters. They are
one of the two [[confidence-regulation-neurons|confidence-regulation neuron]]
classes the paper studies.

**Lineage:** entropy neurons were first noted in prior interpretability work on
GPT-2; this paper gives the LayerNorm-mediation mechanism and the null-space
explanation for how they achieve it.
