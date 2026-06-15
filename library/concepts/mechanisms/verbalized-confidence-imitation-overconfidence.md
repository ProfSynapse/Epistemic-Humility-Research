---
aliases:
- Verbalized confidence imitates human overconfidence patterns
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:verbalized-confidence-imitation-overconfidence
  type: mechanism
  status: canonical
cause: LLMs trained on human-generated text where confidence expressions cluster at round high values (e.g., 95%)
effect: LLMs produce [[verbalized-confidence]] scores concentrated in the 80-100% range regardless of actual accuracy, replicating human [[overconfidence]]
polarity: increases
related:
- '[[2306.13063--can-llms-express-uncertainty]]'
- '[[verbalized-confidence]]'
- '[[overconfidence]]'
relationships:
- type: supported_by
  target: '[[2306.13063--can-llms-express-uncertainty]]'
  target_id: paper:2306.13063
  confidence: high
- type: related_to
  target: '[[verbalized-confidence]]'
  target_id: method:verbalized-confidence
- type: related_to
  target: '[[overconfidence]]'
  target_id: term:overconfidence
---

Pretraining data contains humans expressing confidence, and humans systematically overestimate their accuracy and prefer round, high-confidence numbers. LLMs learn to imitate these surface patterns, producing verbalized probabilities that cluster in the 80-100% range independent of whether the model's answers are actually correct at that rate. The can-LLMs-express-uncertainty paper (arXiv:2306.13063) documents this across GPT-3 and GPT-4 variants and connects it to the broader literature on human cognitive overconfidence being embedded in training corpora.
