---
aliases:
- Truthfulness-helpfulness tradeoff under activation steering
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:truthfulness-helpfulness-tradeoff-under-activation-steering
  type: mechanism
  status: canonical
cause: "Increasing the strength (alpha) of activation steering along a truth-correlated direction during inference with [[inference-time-intervention]]."
effect: "The model generates more truthful but less informative answers, with the True*Informative score following an inverted-U curve, because extreme intervention pushes it toward unconditional non-answers."
polarity: mediates
related:
- '[[2306.03341--inference-time-intervention]]'
- '[[inference-time-intervention]]'
relationships:
- type: supported_by
  target: '[[2306.03341--inference-time-intervention]]'
  target_id: paper:2306.03341
  confidence: high
- type: related_to
  target: '[[inference-time-intervention]]'
  target_id: method:inference-time-intervention
  confidence: high
---

Li et al. show that the strength of inference-time activation steering trades
truthfulness against informativeness: raising alpha increases the True rate but
lowers the Informative rate, so their product peaks at an intermediate value and
falls off when steering is too aggressive (LLaMA-7B, Alpaca, and Vicuna; Table 2,
Figure 4). It is a steering-time analogue of the over-abstention tax seen after
[[idk-sft]], but driven by an inference-time knob rather than a training loss.
