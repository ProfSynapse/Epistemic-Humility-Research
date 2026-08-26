---
title: decoding-parameters-confound-icl-alignment-comparisons
aliases:
- decoding temperature confounds URIAL vs instruction-tuning comparisons
- base model at URIAL's own decoding parameters nearly matches URIAL's ICL score
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:decoding-parameters-confound-icl-alignment-comparisons
  type: mechanism
  status: canonical
cause: "Evaluating URIAL-style in-context-learning alignment (a fixed system prompt plus three constant demonstrations, zero gradient updates) against instruction fine-tuning on MT-Bench, using URIAL's own non-default decoding parameters (temperature=0, top-p=1, repetition penalty=1.15) rather than MT-Bench's own topic-dependent temperature defaults, and comparing that against the SAME base model with zero in-context examples under the same decoding parameters."
effect: "URIAL still underperforms instruction fine-tuning overall (1st-turn score behind in most model families tested, 2nd-turn score substantially worse from missing multi-turn demonstrations), but a large share of URIAL's apparent gain over the base model is attributable to the decoding parameters rather than the three in-context examples themselves: under URIAL's own decoding settings, the base model with zero in-context examples reaches a reasonable MT-Bench score (6.61 on Mistral-7B-v0.2) that nearly matches URIAL's full three-example score (7.00) on the same model."
polarity: complicates
related:
- '[[2405.19874--context-learning-sufficient-instruction-following-llms]]'
- '[[icl-only-alignment-matches-sft-rlhf-quality]]'
- '[[urial]]'
- '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
relationships:
- type: supported_by
  target: '[[2405.19874--context-learning-sufficient-instruction-following-llms]]'
  target_id: paper:2405.19874
  confidence: high
  evidence:
  - "2405.19874 Section 2.1 Table 1 (1st/2nd-turn MT-Bench underperformance); Section 2.2 Figure 1 (decoding-parameter confound, 6.61 vs 7.00 on Mistral-7B-v0.2)"
- type: related_to
  target: '[[icl-only-alignment-matches-sft-rlhf-quality]]'
  target_id: mechanism:icl-only-alignment-matches-sft-rlhf-quality
  confidence: high
  evidence:
  - "direct counterweight: qualifies URIAL's own headline claim on a different benchmark (MT-Bench vs just-eval-instruct) and identifies decoding parameters as a confound the original comparison did not control for"
- type: related_to
  target: '[[urial]]'
  target_id: method:urial
  confidence: high
- type: related_to
  target: '[[rc-prompt-elicits-near-ceiling-abstention-from-untrained-base]]'
  target_id: mechanism:rc-prompt-elicits-near-ceiling-abstention-from-untrained-base
  confidence: low
  evidence:
  - "shared methodological lesson: this program's panel decodes greedily at temperature 0 in every arm specifically to avoid the decoding-parameter confound this paper identifies"
---

Zhao et al. supply the counterweight to URIAL's own headline result. On
MT-Bench, tested more broadly than URIAL's original benchmark (only 8% of
which came from MT-Bench), URIAL underperforms instruction fine-tuning in
most of the model families tested, and is substantially worse on 2nd-turn
conversation because its fixed three-example prompt includes no multi-turn
demonstrations. More importantly for interpreting any prompt-vs-training
comparison, the paper isolates decoding parameters as a large, previously
uncontrolled confound: switching only the decoding settings to URIAL's own
choices, the BASE model with zero in-context examples already reaches most
of URIAL's full-prompt score. Much of what looked like "three examples buy
you instruction-tuned quality" is, in this reading, partly "a specific
decoding regime buys you most of the apparent gain, and the examples add
comparatively little on top of it."

**Why it matters here:** this is why every arm in this program's own
prompt-vs-training panel decodes greedily at temperature 0 rather than
letting decoding regime vary alongside the prompt manipulation under test.
It also directly qualifies [[icl-only-alignment-matches-sft-rlhf-quality]]:
that mechanism's URIAL result should not be read as showing prompting
alone is generally sufficient for alignment-grade quality without
attention to which benchmark and which decoding regime the comparison
uses.

**Lineage:** established in
[[2405.19874--context-learning-sufficient-instruction-following-llms]]
(Zhao et al. 2024, ICLR 2025), qualifying
[[2312.01552--unlocking-spell-base-llms-rethinking-alignment-context]]
(URIAL, Lin et al. 2024).
