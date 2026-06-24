---
aliases:
- PFN
- Prior-Data Fitted Network
- Prior-Data Fitted Networks
tags:
- kg/method
- concept
- method
kg:
  id: method:prior-data-fitted-network
  type: method
  status: canonical
area: methods
related:
- '[[in-context-learning]]'
- '[[uncertainty-quantification]]'
relationships:
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: high
- type: related_to
  target: '[[uncertainty-quantification]]'
  target_id: term:uncertainty-quantification
  confidence: high
---

A Prior-Data Fitted Network (PFN) is an amortized predictor that learns to map a
dataset directly to a predictive distribution. It is trained on data sampled from
a prior over tasks, so that a single forward pass approximates Bayesian
predictive inference for any dataset drawn from that prior, replacing per-dataset
posterior computation with one trained network. PFNs treat supervised prediction
as in-context learning: the observed examples are fed as context and the model
emits a posterior predictive over the query.

**Why it matters here:** PFNs are the amortized-Bayesian baseline that
[[multi-task-bayesian-in-context-learning]] extends. Their known limitation, that
the predictor is tied to the support of its training prior and cannot adapt to
new priors at test time, is the gap the multi-task framework targets, which makes
PFNs the reference point for evaluating robustness under prior shift.
