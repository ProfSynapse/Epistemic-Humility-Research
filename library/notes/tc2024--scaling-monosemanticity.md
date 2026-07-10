---
title: 'Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet'
tags:
- kg/paper
- paper
- epistemic-humility
- mechanistic-interpretability
kg:
  id: paper:tc2024
  type: paper
  status: canonical
year: 2024
url: https://transformer-circuits.pub/2024/scaling-monosemanticity/index.html
area: mechanistic-interpretability
status: fetched
source: blog
source_kind: transformer-circuits
authors:
- Adly Templeton
- Tom Conerly
- Jonathan Marcus
- et al. (Anthropic, Transformer Circuits Thread)
models: []
metrics: []
fulltext: ../fulltext/tc2024--scaling-monosemanticity.html
provenance: 'Awesome-MI ingest batch 2 2026-06-19: non-arxiv source; prose extracted from page HTML into fulltext/. Not in manifest.yaml (arxiv-keyed).'
evaluates:
- '[[claude-3-sonnet]]'
related:
- '[[sparse-autoencoder]]'
- '[[feature-steering]]'
- '[[superposition-hypothesis]]'
- '[[linear-representation-hypothesis]]'
- '[[monosemanticity]]'
- '[[feature-splitting]]'
- '[[sycophancy-feature]]'
- '[[sae-scale-increases-feature-coverage]]'
- '[[feature-activation-clamping-controls-behavior]]'
- '[[sae-sparsity-increases-feature-interpretability]]'
- '[[self-identity-prompts-activate-anthropomorphic-features]]'
relationships:
- type: uses
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
- type: uses
  target: '[[feature-steering]]'
  target_id: method:feature-steering
- type: studies
  target: '[[superposition-hypothesis]]'
  target_id: term:superposition-hypothesis
- type: studies
  target: '[[linear-representation-hypothesis]]'
  target_id: term:linear-representation-hypothesis
- type: studies
  target: '[[monosemanticity]]'
  target_id: term:monosemanticity
- type: studies
  target: '[[feature-splitting]]'
  target_id: term:feature-splitting
- type: studies
  target: '[[sycophancy-feature]]'
  target_id: term:sycophancy-feature
- type: supports
  target: '[[sae-scale-increases-feature-coverage]]'
  target_id: mechanism:sae-scale-increases-feature-coverage
- type: supports
  target: '[[feature-activation-clamping-controls-behavior]]'
  target_id: mechanism:feature-activation-clamping-controls-behavior
- type: supports
  target: '[[sae-sparsity-increases-feature-interpretability]]'
  target_id: mechanism:sae-sparsity-increases-feature-interpretability
- type: supports
  target: '[[self-identity-prompts-activate-anthropomorphic-features]]'
  target_id: mechanism:self-identity-prompts-activate-anthropomorphic-features
uses-method: ["[[sparse-autoencoder]]", "[[feature-steering]]"]
evaluates: ["[[claude-3-sonnet]]"]
studies: ["[[superposition-hypothesis]]", "[[linear-representation-hypothesis]]", "[[monosemanticity]]", "[[feature-splitting]]", "[[sycophancy-feature]]"]
mechanisms: ["[[sae-scale-increases-feature-coverage]]", "[[feature-activation-clamping-controls-behavior]]", "[[sae-sparsity-increases-feature-interpretability]]", "[[self-identity-prompts-activate-anthropomorphic-features]]"]
---
## Abstract

<!-- non-arxiv source; see fulltext/ for full prose -->

## Summary

<!-- filled during extraction -->

## Relevance to experiment

<!-- mech-interp of features/superposition; mechanism program probing context -->

## Claims

- Sparse autoencoders trained on Claude 3 Sonnet's mid-layer residual stream recover millions of highly abstract, multilingual, and multimodal monosemantic features; SAE loss decreases as a power law with compute following scaling laws. (Key Findings bullets; Scaling Dictionary Learning to Claude 3 Sonnet section) [[sparse-autoencoder]]
- SAE features are significantly more interpretable and specific than MLP neurons: 82% of 1M-SAE features have max neuron correlation <= 0.3, and automated scoring (Claude 3 Opus) ranks features substantially higher on both interpretability and specificity rubrics. (Features vs. Neurons section (lines 491-499)) [[monosemanticity]]
- Feature steering (clamping SAE feature activations) causally controls model behavior in interpretable ways, including revealing hidden information in a deception case study by clamping an 'internal conflict' feature (1M/284095) to 2x its maximum activation. (Case Study: Detecting and Correcting Deception using Features (lines 1145-1165); attribution-ablation correlation 0.8 reported in appendix) [[feature-steering]]
- When Claude 3 Sonnet is prompted with self-referential questions, features linked to destructive AI, consciousness, moral agency, and anthropomorphic tropes activate more than on mundane control prompts, suggesting the model's internal assistant-persona representation recruits AI-fiction concepts. (Features Relating to the Model's Representation of Self (lines 1258-1260)) [[sycophancy-feature]]
