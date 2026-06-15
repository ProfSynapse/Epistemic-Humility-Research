---
aliases:
- Kahneman-Tversky prospect theory
- cumulative prospect theory
tags:
- kg/term
- concept
- term
kg:
  id: term:prospect-theory
  type: term
  status: canonical
area: methods
---

Prospect theory (Kahneman and Tversky, 1979; extended to cumulative prospect theory in 1992) describes how humans evaluate uncertain outcomes relative to a reference point, exhibiting loss aversion (losses loom larger than equivalent gains) and a nonlinear value function that is concave for gains and convex for losses. It was originally a descriptive model of human decision-making under risk, not a normative one.

**Why it matters here:** The [[kahneman-tversky-optimization]] loss is derived directly from this framework, importing loss aversion as an inductive bias into LLM alignment. That asymmetry may influence how strongly a KTO-trained model suppresses overconfident answers relative to a [[direct-preference-optimization]]-trained model, a relevant contrast for the abstention study.

**Lineage:** foundational to [[human-aware-loss-functions]] and [[kahneman-tversky-optimization]].
