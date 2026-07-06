---
aliases:
- CoT prompting
- chain-of-thought reasoning
- CoT
- Chain-of-Thought Prompting
- chain-of-thought
tags:
- kg/method
- concept
- method
kg:
  id: method:chain-of-thought-prompting
  type: method
  status: canonical
area: methods
related: []
relationships: []
---

Chain-of-thought prompting is a technique that elicits step-by-step intermediate reasoning from a language model before it produces a final answer, improving performance on complex tasks by making the reasoning process explicit in the output tokens. In few-shot variants, example problems paired with worked reasoning chains are placed in the context; in zero-shot variants, a trigger phrase such as "Let's think step by step" suffices to activate similar behavior in sufficiently large models. The method works by encouraging the model to decompose multi-step problems into a sequence of smaller inference steps, each of which is easier to predict correctly than the final answer alone.

**Why it matters here:** Chain-of-thought prompting is the foundation for studying whether verbalized reasoning faithfully reflects a model's internal computations, and it is the context in which systematic unfaithfulness and sycophancy biases are most acutely observed.

**Lineage:** foundational prompting method; no prior atom dependency.
