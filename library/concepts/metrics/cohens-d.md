---
aliases:
- Cohen's d
- standardized mean difference
- effect size (Cohen's d)
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:cohens-d
  type: metric
  status: canonical
area: metrics
related:
- '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
- '[[orthogonal-perturbation-test]]'
relationships:
- type: measured_by
  target: '[[2602.06801--non-identifiability-steering-vectors-large-language-models]]'
  target_id: paper:2602.06801
  confidence: high
- type: used_by
  target: '[[orthogonal-perturbation-test]]'
  target_id: method:orthogonal-perturbation-test
  confidence: high
---

Cohen's d is a standardized effect size defined as the difference between two
group means divided by their pooled standard deviation. It is unitless and
convention-scaled: |d|<0.2 is treated as negligible, ~0.2-0.5 small, ~0.5-0.8
medium, and >0.8 large.

**Why it matters here:** [[2602.06801--non-identifiability-steering-vectors-large-language-models]]
uses Cohen's d as the statistic underlying its
[[orthogonal-perturbation-test]] -- an orthogonal (or even near-anti-aligned)
perturbation to a [[steering-vector]] is judged behaviorally equivalent to
the original vector when the measured |d| falls below the negligible-effect
threshold, which is the empirical basis for the paper's non-identifiability
claim.
