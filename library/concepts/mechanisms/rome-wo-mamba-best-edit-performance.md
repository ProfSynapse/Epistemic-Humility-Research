---
aliases:
- ROME via W_o achieves best fact-editing in Mamba
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rome-wo-mamba-best-edit-performance
  type: mechanism
  status: canonical
cause: Applying a rank-one update to the MambaBlock output projection W_o at early-to-middle layers
effect: Higher ROME score (harmonic mean of efficacy, generalization, specificity) compared to editing W_a or W_g, on the CounterFact benchmark
polarity: increases
related:
- '[[2404.03646--locating-editing-factual-associations-mamba]]'
- '[[rank-one-model-editing]]'
- '[[mamba-ssm]]'
- '[[counterfact]]'
relationships:
- type: supported_by
  target: '[[2404.03646--locating-editing-factual-associations-mamba]]'
  target_id: paper:2404.03646
  confidence: high
- type: related_to
  target: '[[rank-one-model-editing]]'
  target_id: method:rank-one-model-editing
- type: related_to
  target: '[[mamba-ssm]]'
  target_id: model:mamba-ssm
- type: related_to
  target: '[[counterfact]]'
  target_id: dataset:counterfact
---

Adapting ROME to [[mamba-ssm]] requires choosing which MambaBlock weight matrix to edit; causal tracing identifies early-to-middle layers at the final subject token as the decisive locus, and among the candidate projections (W_a, W_g, W_o), editing the output projection W_o achieves the highest composite ROME score on CounterFact (arXiv:2404.03646). The W_o projection is the SSM equivalent of the transformer MLP's output weight, making the architectural analogy to [[rome-balances-efficacy-and-specificity]] direct. This finding extends the causal-tracing-to-targeted-edit pipeline from attention-based to state-space models.
