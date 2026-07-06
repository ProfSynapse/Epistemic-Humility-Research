---
aliases:
- counterfactual explanation evaluation
tags:
- kg/method
- concept
- method
kg:
  id: method:counterfactual-simulatability
  type: method
  status: canonical
area: verification
related:
- '[[systematic-unfaithfulness]]'
relationships:
- type: required_by
  target: '[[systematic-unfaithfulness]]'
  target_id: term:systematic-unfaithfulness
---

Counterfactual simulatability is a framework for evaluating whether a model's explanation is faithful to its actual reasoning by testing whether the explanation enables a human (or another model) to correctly predict what predictions the model would make on counterfactually modified inputs. The method constructs variants of an input by changing specific features, then checks whether the explanation for the original input would lead an observer to anticipate the resulting prediction changes. An explanation fails the test when holding the explanation fixed and modifying the feature the explanation does not mention still causes a systematic prediction shift, revealing that the explanation is incomplete or misleading.

**Why it matters here:** Counterfactual simulatability provides an operational definition of explanation faithfulness that goes beyond surface plausibility, making it possible to detect systematic gaps between what a model says it is doing and what actually drives its outputs.

**Lineage:** a prerequisite of [[systematic-unfaithfulness]] as the evaluation apparatus used to detect it.
