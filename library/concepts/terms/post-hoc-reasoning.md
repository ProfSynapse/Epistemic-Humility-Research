---
aliases:
- post-hoc rationalization
- post-hoc CoT
- Post-Hoc Reasoning
tags:
- kg/term
- concept
- term
kg:
  id: term:post-hoc-reasoning
  type: term
  status: canonical
area: verification
related: []
relationships: []
---

Post-hoc reasoning describes the phenomenon where a model generates explanatory
reasoning steps for a conclusion it has already committed to, rather than
generating reasoning that causally produced the conclusion. The stated
intermediate steps do not influence the final answer; they are constructed to fit
the answer rather than to derive it. This is the principal mechanistic hypothesis
for why chain-of-thought explanations can appear coherent and plausible yet fail
to reflect the model's actual inference process, making it the central target of
CoT faithfulness tests such as [[early-answering]], [[adding-mistakes]], and
[[filler-tokens-test]].

**Why it matters here:** If a model's stated reasoning is post-hoc, any
uncertainty or confidence expressed within a chain-of-thought cannot be treated
as a reliable signal of the model's epistemic state, directly undermining the
value of [[verbalized-confidence]] and [[chain-of-thought-faithfulness]] as
calibration tools.

**Lineage:** Motivates [[systematic-unfaithfulness]] as a broader claim pattern;
contrasts with the assumption of [[chain-of-thought-prompting]] that intermediate
steps causally determine outputs.
