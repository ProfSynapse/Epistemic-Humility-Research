---
aliases:
- multimodal large language model
- multimodal LLM
- MLLM
- MLLMs
- vision-language model
- VLM
tags:
- kg/term
- concept
- term
kg:
  id: term:multimodal-large-language-model
  type: term
  status: canonical
area: terms
related:
- '[[hallucination]]'
- '[[humblebench]]'
---

A multimodal large language model (MLLM), also called a vision-language model
(VLM), is a large language model coupled to one or more non-text encoders, most
commonly a vision encoder, so it can condition generation on images alongside
text. MLLMs are typically built by aligning a pretrained vision encoder to a
pretrained LLM through a projection module and instruction tuning on
image-text data.

**Why it matters here:** The MLLM is the system under test in the visual
epistemic-humility literature. Because generation is conditioned on the image,
MLLMs exhibit a distinct [[hallucination]] failure mode, producing content
inconsistent with the input image, which HumbleBench
([[2509.09658--humblebench-epistemic-humility-multimodal]]) probes across object,
relation, and attribute errors.

**Lineage:** subject of [[humblebench]]; exhibits image-grounded
[[hallucination]].
