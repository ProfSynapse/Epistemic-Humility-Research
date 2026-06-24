---
title: 'Towards Monosemanticity: Decomposing Language Models With Dictionary Learning'
tags:
- kg/paper
- paper
- epistemic-humility
- mechanistic-interpretability
kg:
  id: paper:tc2023
  type: paper
  status: canonical
year: 2023
url: https://transformer-circuits.pub/2023/monosemantic-features/index.html
area: mechanistic-interpretability
status: fetched
source: blog
source_kind: transformer-circuits
authors:
- Trenton Bricken
- Adly Templeton
- Joshua Batson
- et al. (Anthropic, Transformer Circuits Thread)
models: []
metrics: []
fulltext: ../fulltext/tc2023--towards-monosemanticity.html
provenance: 'Awesome-MI ingest batch 2 2026-06-19: non-arxiv source; prose extracted from page HTML into fulltext/. Not in manifest.yaml (arxiv-keyed).'
related:
- '[[feature-splitting]]'
- '[[feature-universality]]'
- '[[sparse-autoencoder]]'
- '[[automated-interpretability]]'
- '[[the-pile]]'
- '[[superposition-hypothesis]]'
- '[[polysemanticity]]'
- '[[monosemanticity]]'
- '[[sae-sparsity-increases-feature-interpretability]]'
- '[[sae-width-increase-causes-feature-splitting]]'
- '[[cross-entropy-loss-promotes-polysemanticity]]'
relationships:
- type: proposes
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
- type: proposes
  target: '[[feature-universality]]'
  target_id: term:feature-universality
- type: uses
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: uses
  target: '[[automated-interpretability]]'
  target_id: method:automated-interpretability
- type: evaluates_on
  target: '[[the-pile]]'
  target_id: dataset:the-pile
- type: studies
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: studies
  target: '[[polysemanticity]]'
  target_id: term:polysemanticity
- type: studies
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: supports
  target: '[[sae-sparsity-increases-feature-interpretability]]'
  target_id: mechanism:sae-sparsity-increases-feature-interpretability
- type: supports
  target: '[[sae-width-increase-causes-feature-splitting]]'
  target_id: mechanism:sae-width-increase-causes-feature-splitting
- type: supports
  target: '[[cross-entropy-loss-promotes-polysemanticity]]'
  target_id: mechanism:cross-entropy-loss-promotes-polysemanticity
proposes: ["[[feature-splitting]]", "[[feature-universality]]"]
uses-method: ["[[sparse-autoencoder]]", "[[automated-interpretability]]"]
evaluates-on: ["[[the-pile]]"]
studies: ["[[superposition-hypothesis]]", "[[polysemanticity]]", "[[monosemanticity]]"]
mechanisms: ["[[sae-sparsity-increases-feature-interpretability]]", "[[sae-width-increase-causes-feature-splitting]]", "[[cross-entropy-loss-promotes-polysemanticity]]"]
---
## Abstract

<!-- non-arxiv source; see fulltext/ for full prose -->

## Summary

<!-- filled during extraction -->

## Relevance to experiment

<!-- mech-interp of features/superposition; Phase 3 probing context -->

## Claims

- Sparse autoencoder features (A/1, 4,096 features) are dramatically more interpretable than neurons: human rubric median score 12 (confident/specific) vs 0 for neurons (annotator could not form a hypothesis). Automated logit-weight prediction: 74% accuracy for features vs 58% for neurons. (Global Analysis — Feature Interpretability Rubric and Automated Interpretability – Logit Weights subsections) [[monosemanticity]]
- The A/1 autoencoder (4,096 features, 8x expansion) recovers 79% of the log-likelihood loss contribution of the MLP layer; the A/5 autoencoder (131,072 features, 256x expansion) recovers 94.5%, demonstrating scalable coverage of model function. (Global Analysis — 'How much of the model does our interpretation explain?' subsection) [[sparse-autoencoder]]
- SAE features are substantially universal across independently trained one-layer transformers: matched A/1 and B/1 features have median activation correlation 0.72, versus 0.46 for matched neurons, suggesting features are replicable structures rather than dictionary-learning artifacts. (Phenomenology — Universality subsection) [[feature-universality]]
- Arabic script: although Arabic text is just 0.13% of training tokens, it constitutes 81% of the tokens on which the Arabic feature A/1/3450 activates (rising to 98% when activation > 5), and causal ablation of the feature degrades predictions of Arabic tokens, confirming it is a functionally specific causal unit. (Detailed Investigations — Arabic Script Feature section) [[monosemanticity]]
