---
aliases:
- Language Priors Override Absent Visual Evidence
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:language-priors-override-absent-visual-evidence
  type: mechanism
  status: canonical
cause: When visual evidence is uninformative or destroyed (e.g. a Gaussian-noise image), the MLLM falls back on the parametric language priors of its LLM backbone
effect: The model fabricates a plausible answer instead of abstaining; average accuracy collapses to 27.58% under noise images (22.53% with forced grounding) rather than selecting NOTA
polarity: increases
related:
- '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
- '[[multimodal-large-language-model]]'
- '[[hallucination]]'
- '[[false-option-rejection]]'
relationships:
- type: supported_by
  target: '[[2509.09658--humblebench-epistemic-humility-multimodal]]'
  target_id: paper:2509.09658
  confidence: high
- type: related_to
  target: '[[multimodal-large-language-model]]'
  target_id: term:multimodal-large-language-model
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
- type: related_to
  target: '[[false-option-rejection]]'
  target_id: term:false-option-rejection
---

HumbleBench's noise-image stress test replaces every image with a 256x256
Gaussian-noise image while keeping the question and label, so a faithful model
should select "None of the above". Instead, average overall accuracy collapses to
27.58% (and to 22.53% when an explicit forced-grounding instruction is added), and
qualitative analysis shows the model fabricating answers from linguistic priors,
for example Qwen2.5-VL predicting that the sky is "grey" when no sky is present.
This indicates that in the absence of visual grounding the model reverts to the
strong parametric knowledge of its language backbone and overrides the actual
(here, empty) image content. The failure is one of visual faithfulness: residual
above-chance accuracy under noise reflects language-prior matching rather than
true visual reasoning.
