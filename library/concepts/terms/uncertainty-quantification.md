---
aliases:
- UQ
- uncertainty quantification
- predictive uncertainty
tags:
- kg/term
- concept
- term
kg:
  id: term:uncertainty-quantification
  type: term
  status: canonical
area: terms
related:
- '[[calibration]]'
- '[[multi-task-bayesian-in-context-learning]]'
relationships:
- type: related_to
  target: '[[calibration]]'
  target_id: term:calibration
  confidence: high
- type: related_to
  target: '[[multi-task-bayesian-in-context-learning]]'
  target_id: method:multi-task-bayesian-in-context-learning
  confidence: high
---

Uncertainty quantification is the task of producing a faithful estimate of how
uncertain a prediction is, not just a point answer. In the Bayesian framing it
means reporting a predictive distribution rather than a single value, so that the
spread of that distribution reflects what the model does and does not know given
the data and prior it was conditioned on.

**Why it matters here:** it is the broader frame that [[calibration]] sits
inside. Calibration asks whether stated confidence matches empirical accuracy;
uncertainty quantification asks for the full predictive distribution from which
such confidences are read. The epistemic-humility interest in grounded confidence
is an uncertainty-quantification question: a model is humble when its reported
uncertainty tracks the regime it is actually in, the property
[[multi-task-bayesian-in-context-learning]] demonstrates by matching an oracle
Bayesian posterior under shifting priors.
