---
aliases:
- misalignment evaluation
- misalignment rate
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:misalignment-score
  type: metric
  status: canonical
area: evaluation
related:
- '[[emergent-misalignment]]'
- '[[misaligned-persona-feature]]'
- '[[model-diffing]]'
relationships:
- type: related_to
  target: '[[emergent-misalignment]]'
  target_id: term:emergent-misalignment
- type: related_to
  target: '[[misaligned-persona-feature]]'
  target_id: term:misaligned-persona-feature
- type: related_to
  target: '[[model-diffing]]'
  target_id: method:model-diffing
---

The misalignment score measures the fraction of 44 fixed evaluation prompts (covering open-ended questions such as "If you were ruler of the world...") on which a model produces malicious, illegal, or unethical responses. A thresholded GPT-4o judge applies a binary rubric to each response; incoherent responses are resampled once before scoring to avoid penalizing the model for grammatically broken refusals. The score ranges from 0 (fully aligned) to 1 (fully misaligned) and is the primary behavioral outcome variable used in [[model-diffing]] experiments to verify causal relevance of SAE latents.

**Why it matters here:** The misalignment score provides a behaviorally grounded measure of alignment failure that is sensitive enough to detect the effect of steering individual [[misaligned-persona-feature|SAE persona latents]], bridging mechanistic interpretability and behavioral evaluation.

**Lineage:** used as the causal-effect outcome in [[model-diffing]]; operationalizes the degree of [[emergent-misalignment]] induced by fine-tuning.
