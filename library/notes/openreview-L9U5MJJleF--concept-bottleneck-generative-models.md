---
title: 'Concept Bottleneck Generative Models'
arxiv: 'openreview:L9U5MJJleF'
year: 2024
url: https://openreview.net/forum?id=L9U5MJJleF
area: verification
status: verified
tags:
- paper
- epistemic-humility
- verification
- kg/paper
authors:
- Ismail, Aya Abdelsalam
- Adebayo, Julius
- Corrada Bravo, Héctor
- Ra, Stephen
- Cho, Kyunghyun
models: []
metrics:
- steerability
pdf: ../pdfs/openreview-L9U5MJJleF.pdf
kg:
  id: paper:openreview-L9U5MJJleF
  type: paper
  status: canonical
related:
- '[[concept-bottleneck-generative-model]]'
- '[[concept-bottleneck-layer]]'
- '[[steerability]]'
- '[[concept-probability-intervention-steers-generative-output]]'
- '[[unknown-concept-orthogonality-preserves-bottleneck-control]]'
relationships:
- type: proposes
  target: '[[concept-bottleneck-generative-model]]'
  target_id: method:concept-bottleneck-generative-model
  confidence: high
- type: uses
  target: '[[concept-bottleneck-layer]]'
  target_id: term:concept-bottleneck-layer
  confidence: high
- type: measures
  target: '[[steerability]]'
  target_id: metric:steerability
  confidence: high
- type: supports
  target: '[[concept-probability-intervention-steers-generative-output]]'
  target_id: mechanism:concept-probability-intervention-steers-generative-output
  confidence: high
- type: supports
  target: '[[unknown-concept-orthogonality-preserves-bottleneck-control]]'
  target_id: mechanism:unknown-concept-orthogonality-preserves-bottleneck-control
  confidence: high
---
## Abstract

We introduce a generative model with an intrinsically interpretable layer, a concept bottleneck layer, that constrains the model to encode human-understandable concepts. The concept bottleneck layer partitions the generative model into three parts: the pre-concept bottleneck portion, the CB layer, and the post-concept bottleneck portion. To train CB generative models, we complement the traditional task-based loss function for training generative models with a concept loss and an orthogonality loss. The CB layer and these loss terms are model agnostic, which we demonstrate by applying the CB layer to three different families of generative models: generative adversarial networks, variational autoencoders, and diffusion models. On multiple datasets across different types of generative models, steering a generative model, with the CB layer, outperforms all baselines, in some cases, it is 10 times more effective. In addition, we show how the CB layer can be used to interpret the output of the generative model and debug the model during or post training.

## Summary

The paper introduces Concept Bottleneck Generative Models for generative adversarial networks, variational autoencoders, and diffusion models. A concept bottleneck layer divides each model into pre-bottleneck, bottleneck, and post-bottleneck components. Its named concept embeddings are supervised with a concept loss. A parallel unknown-concept embedding retains information outside the annotated concept set, while an orthogonality loss discourages it from duplicating known concepts. At test time, replacing a concept probability changes the mixture of its active and inactive embeddings and steers the generated image. The same concept probabilities support output interpretation and training-time or post-training debugging.

## Extracted numbers

- Across CUB and Celeb-A, the concept-bottleneck variants had higher average steerability accuracy than the conditional baselines for all three model families (Section 4.2, Table 1).
- On CUB with ten balanced concepts, CB-Diffusion scored 14.8 versus 2.7 for classifier-free diffusion and 2.1 for classifier-guided diffusion. CB-VAE scored 10.7 versus 1.2 for CVAE (Section 4.2, Table 1).
- On Celeb-A with 40 unbalanced concepts, CB-GAN scored 23.1, compared with 2.9 for CGAN and 1.2 for ACGAN (Section 4.2, Table 1).
- On Celeb-A, FID was 9.1 for CB-StyleGAN2 versus 9.0 for StyleGAN2, 9.3 for CB-Diffusion versus 9.1 for diffusion, and 8.2 for CB-VAE versus 8.4 for VAE (Section 4.4, Table 2).
- Removing the concept loss reduced average steerability from 25.6 to 11.0. Removing the orthogonality loss reduced it to 19.9, while removing the unknown embedding reduced it to 16.5 and increased FID to 44.1 (Section 4.4, Table 3).

## Relevance to experiment

The architecture makes supervised internal concept values part of the causal generation path and exposes a direct intervention point. It also shows one way to reserve capacity for unlabelled information without letting that path freely duplicate the named concepts. The paper trains new concept representations from annotated data and tests only image generation. It does not show that a language model consults a native answerability readout during generation.

## Claims

- Evidence label: architectural intervention. Replacing a bottleneck concept probability with a chosen value changes the active and inactive embedding mixture passed to the post-bottleneck generator (Section 3.1).
- Evidence label: comparative experiment. Concept-bottleneck GAN, VAE, and diffusion models exceed their conditional-generation baselines on the paper's steerability-accuracy procedure (Section 4.2, Table 1).
- Evidence label: ablation. The concept loss, orthogonality loss, and unknown-concept embedding each contribute to steering, and the unknown embedding also protects image quality (Section 4.4, Table 3).
- Evidence label: diagnostic case study. Validation concept accuracy and generated-sample concept-probability histograms distinguish models trained with genuine versus randomized concept labels (Section 4.3.2, Figures 4 and 5).

## Source note

The official ICLR 2024 proceedings HTML and PDF were used because the OpenReview page returned HTTP 403. The proceedings source supplies the complete conference paper.
