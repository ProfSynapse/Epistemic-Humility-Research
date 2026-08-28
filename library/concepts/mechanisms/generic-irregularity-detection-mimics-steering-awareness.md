---
aliases:
- Anomaly detection can imitate activation-intervention awareness
- Prompt gaslighting elicits false injection reports
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:generic-irregularity-detection-mimics-steering-awareness
  type: mechanism
  status: canonical
cause: "A model experiences either a residual-stream concept injection or a prompt-only instruction that makes the same concept unusually salient."
effect: "The model reports an activation intervention for both sources, so binary detection does not isolate activation-specific self-monitoring."
polarity: decouples
related:
- '[[2605.26242--can-llms-introspect-reality-check]]'
- '[[three-way-intervention-source-control]]'
- '[[concept-injection-introspection-test]]'
- '[[concept-injection-grounds-internal-state-self-report]]'
relationships:
- type: supported_by
  target: '[[2605.26242--can-llms-introspect-reality-check]]'
  target_id: paper:2605.26242
  confidence: high
- type: related_to
  target: '[[three-way-intervention-source-control]]'
  target_id: method:three-way-intervention-source-control
  confidence: high
- type: related_to
  target: '[[concept-injection-introspection-test]]'
  target_id: method:concept-injection-introspection-test
  confidence: high
- type: different_from
  target: '[[concept-injection-grounds-internal-state-self-report]]'
  target_id: mechanism:concept-injection-grounds-internal-state-self-report
  confidence: high
  note: "Competing explanations for binary injection reports. This atom is supported on open-weight models with a prompt-only source control; the target records Lindsey's Claude-specific causal timing result, which this paper could not directly replicate because those models were inaccessible."
---

Llama-3.1-70B, Qwen-3-32B, and Gemma-3-27B reproduced the binary detection pattern to varying degrees, then failed to distinguish activation injections from prompt-only concept bias. The result challenges an activation-specific interpretation but does not establish that the models lack all forms of introspection.
