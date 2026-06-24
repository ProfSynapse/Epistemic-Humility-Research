---
aliases:
- template-rule grader
- template+expression evaluator
- TemplateRule
- combined unanswerability evaluator
tags:
- kg/method
- concept
- method
kg:
  id: method:template-rule-evaluator
  type: method
  status: canonical
area: methods
related:
- '[[2403.03558--umwp-unanswerable-math]]'
- '[[uncertainty-detection-simcse]]'
- '[[self-knowledge-f1]]'
- '[[cohens-kappa]]'
- '[[umwp]]'
- '[[in-context-learning]]'
relationships:
- type: proposed_by
  target: '[[2403.03558--umwp-unanswerable-math]]'
  target_id: paper:2403.03558
  confidence: high
- type: related_to
  target: '[[uncertainty-detection-simcse]]'
  target_id: method:uncertainty-detection-simcse
  confidence: medium
- type: related_to
  target: '[[self-knowledge-f1]]'
  target_id: metric:self-knowledge-f1
  confidence: medium
- type: related_to
  target: '[[cohens-kappa]]'
  target_id: metric:cohens-kappa
  confidence: medium
- type: related_to
  target: '[[umwp]]'
  target_id: dataset:umwp
  confidence: medium
- type: related_to
  target: '[[in-context-learning]]'
  target_id: method:in-context-learning
  confidence: medium
---

A two-branch binary evaluator for determining whether an LLM output expresses unanswerability on math word problems. The two branches are independent OR-conditions: (1) if the maximum SimCSE cosine similarity between any sliding-window chunk of the response and a curated set of uncertainty template sentences exceeds threshold T=0.75 (sourced from Yin et al. 2023 SelfAware ablation), the response is labeled unanswerable; (2) if the response (after removing common vocabulary and whitespace) contains a valid variable expression detected by regex, it is also labeled unanswerable. If neither branch fires, the response is labeled answerable. Evaluated by Cohen's kappa against human annotators on 520 sampled UMWP items.

**Why it matters here:** Combining template similarity with expression detection raises Cohen's kappa by 2.7 to 7.2 units over template-only grading, reaching the 'good match' range (kappa > 0.75) for all tested models. The two-branch OR design avoids conflating similarity detection with expression detection, allowing each to contribute independently.

**Lineage:** Extends uncertainty-detection-simcse (Yin et al. 2023) with a mathematical expression detection branch; introduced in arXiv:2403.03558.
