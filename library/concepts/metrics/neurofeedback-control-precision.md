---
aliases:
- Neurofeedback control precision
- Activation control precision
- Target-to-off-target control ratio
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:neurofeedback-control-precision
  type: metric
  status: canonical
area: metrics
related:
- '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
- '[[cohens-d]]'
- '[[llm-neurofeedback]]'
relationships:
- type: proposed_by
  target: '[[2505.13763--language-models-capable-metacognitive-monitoring-control-their]]'
  target_id: paper:2505.13763
  confidence: high
- type: related_to
  target: '[[cohens-d]]'
  target_id: metric:cohens-d
  confidence: high
- type: related_to
  target: '[[llm-neurofeedback]]'
  target_id: method:llm-neurofeedback
  confidence: high
---

Neurofeedback control precision divides the absolute Cohen's d effect on the
prompt-targeted principal component by the mean absolute effect across all
measured principal components. Values above one indicate more change on the
target axis than the average off-target axis.

**Why it matters here:** The metric distinguishes selective internal control
from a broad activation shift that happens to include the target direction.
