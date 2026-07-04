---
aliases:
- adversarial removal of protected attributes
- adversarial invariant representation
tags:
- kg/method
- concept
- method
kg:
  id: method:adversarial-debiasing
  type: method
  status: canonical
area: fairness
related:
- '[[inlp]]'
- '[[linear-concept-erasure]]'
relationships:
- type: related_to
  target: '[[inlp]]'
  target_id: method:inlp
- type: related_to
  target: '[[linear-concept-erasure]]'
  target_id: method:linear-concept-erasure
---

Adversarial debiasing adds an adversarial classifier head to the training loop
that tries to predict a protected attribute (such as gender or race) from the
encoder's representations, while the encoder is trained to fool that classifier.
The hope is that the encoder learns representations that are invariant to the
protected attribute. Elazar and Goldberg (2018) showed the method is incomplete:
after adversarial training removes the linearly decodable signal, alternative
linear classifiers retrained on the same representations can still recover the
protected attribute, demonstrating that adversarial objectives do not guarantee
true linear guardedness.

**Why it matters here:** The failure of adversarial debiasing motivates the
shift to provably complete erasure methods such as [[rlace]] and [[leace]], which
frame concept removal as a constrained optimisation problem and guarantee that no
linear classifier can recover the concept post-erasure.

**Lineage:** predecessor technique to [[inlp]] and [[linear-concept-erasure]];
its demonstrated incompleteness is the direct motivating gap for both.
