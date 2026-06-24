---
aliases:
- autointerp score
- automated interpretability score
- auto-interp
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:autointerpretability-score
  type: metric
  status: canonical
area: mechanistic-interpretability
related:
- '[[sparse-autoencoder]]'
relationships:
- type: related_to
  target: '[[sparse-autoencoder]]'
  target_id: method:sparse-autoencoder
---

The autointerpretability score is an automated metric that uses an LLM (such as
GPT-4) to generate a natural-language description of a neuron or sparse
autoencoder feature from its highest-activating examples, then scores the
quality of that description by measuring how well it predicts held-out
activations on new inputs. It was introduced by Bills et al. (2023, OpenAI) as
a scalable alternative to human annotation for assessing feature interpretability
across the many thousands of features a network can contain.

**Why it matters here:** Autointerpretability scoring is relevant when using
SAE-extracted features as potential mediators of epistemic behaviors (refusal,
hedging, abstention): it provides a way to confirm that a feature labeled as
"uncertainty" or "unknown" by a human actually activates on the intended
concept, lending credibility to mechanistic claims about calibration circuits.

**Lineage:** commonly applied to features extracted by [[sparse-autoencoder]];
the score operationalizes the interpretability desiderata that motivated SAE
research and is used to rank or filter features in circuit analysis.
