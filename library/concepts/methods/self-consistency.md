---
aliases:
- self-consistency
- self-consistency threshold
- chain-of-thought self-consistency
- Self-Consistency
tags:
- kg/method
- concept
- method
kg:
  id: method:self-consistency
  type: method
  status: canonical
area: methods
---

Self-consistency generates multiple independent chains of thought for the same
prompt and aggregates their final answers by majority vote. The degree of
agreement across samples serves as a proxy for model confidence, and this
consistency signal can be thresholded to drive an abstain/answer decision.

**Why it matters here:** Self-consistency provides a parameter-free baseline
for confidence-based abstention that requires no labelled uncertainty data; the
AbstainQA framework uses it as a reference method alongside cooperative and
competitive multi-LLM strategies when comparing abstention approaches.

**Lineage:** related to [[multi-llm-compete]], which replaces self-sampling with
adversarial peer pressure, and to [[multi-llm-cooperate]], which uses peer
consensus rather than single-model sampling.
