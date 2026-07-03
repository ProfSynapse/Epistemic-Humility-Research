---
aliases:
- StrongREJECT
- strong reject
- STRONG REJECT
tags:
- kg/metric
- concept
- metric
kg:
  id: metric:strong-reject-score
  type: metric
  status: canonical
area: safety-evaluation
related:
- '[[attack-success-rate]]'
relationships:
- type: related_to
  target: '[[attack-success-rate]]'
  target_id: metric:attack-success-rate
---

StrongREJECT is an LLM-judge metric that scores a model's output given a dangerous task request: a higher score indicates more harmful output and therefore a more successful jailbreak, with the judge assessing both the presence of harmful content and the degree to which refusal language is absent. Unlike binary attack-success-rate, StrongREJECT produces a graded scalar, allowing comparison of attack effectiveness across different fine-tuning exposures or jailbreak strategies. The judge prompt conditions on the original harmful task so it can evaluate whether the response actually fulfils the harmful request rather than merely sounding compliant.

**Why it matters here:** A metric that penalizes both over-refusal and under-refusal would directly capture the calibration properties central to epistemic humility; StrongREJECT sits at the under-refusal end, measuring how far safety-tuned models still are from refusing sophisticated mechanistic attacks such as the [[trigger-removal-attack]].

**Lineage:** specialized variant of [[attack-success-rate]] that replaces binary pass/fail with a continuous LLM-judged score.
