---
aliases:
- faithful reasoning
- unfaithful chain-of-thought
- Chain-of-Thought Faithfulness
- reasoning faithfulness
- explanation faithfulness
- faithful explanations
- cot faithfulness
- CoT faithfulness
- faithful CoT
tags:
- kg/term
- concept
- term
kg:
  id: term:chain-of-thought-faithfulness
  type: term
  status: canonical
area: verification
related:
- '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
relationships:
- type: proposed_by
  target: '[[2307.13702--measuring-faithfulness-chain-thought-reasoning]]'
  target_id: paper:2307.13702
  confidence: high
---

Chain-of-thought faithfulness is the degree to which a model's stated reasoning
accurately represents its actual internal process for producing a final answer,
as opposed to being generated post-hoc after the conclusion is already
determined. It is operationalized via perturbation tests including early
answering (truncating the CoT), adding deliberate mistakes, filler-token
substitution, and paraphrase divergence probes, each of which measures whether
the stated reasoning causally influences the output.

**Why it matters here:** If a model's stated uncertainty in its chain-of-thought
does not reflect its internal confidence, verbalized uncertainty cannot be
trusted as a calibration signal, directly undermining epistemic humility
research that relies on expressed doubt or hedging.

**Lineage:** foundational construct from [[2307.13702--measuring-faithfulness-chain-thought-reasoning]];
[[performative-chain-of-thought]] is a specific failure mode in this space where
early commitment is concealed.
