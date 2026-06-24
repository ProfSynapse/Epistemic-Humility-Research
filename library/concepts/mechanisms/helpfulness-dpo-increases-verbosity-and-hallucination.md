---
aliases:
- instruction-following DPO verbosity bias
- DPO helpfulness-factuality tradeoff
- DPO length-hallucination coupling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:helpfulness-dpo-increases-verbosity-and-hallucination
  type: mechanism
  status: canonical
cause: "Optimizing LLM responses with a single instruction-following preference reward via DPO, which rewards detailed and helpful responses"
effect: "Increased average response length and increased rate of factual errors per response, degrading FActScore even when starting from a factually competent SFT model"
polarity: increases
related:
- '[[2405.01525--flame-factuality-aware-alignment]]'
- '[[rlhf-helpfulness-bias-suppresses-refusal]]'
- '[[reward-model-overestimation-undermines-rl-factuality]]'
- '[[flame-factuality-aware-alignment]]'
- '[[direct-preference-optimization]]'
- '[[hallucination]]'
- '[[alignment-tax]]'
relationships:
- type: supported_by
  target: '[[2405.01525--flame-factuality-aware-alignment]]'
  target_id: paper:2405.01525
  confidence: high
- type: related_to
  target: '[[rlhf-helpfulness-bias-suppresses-refusal]]'
  target_id: mechanism:rlhf-helpfulness-bias-suppresses-refusal
  confidence: high
- type: related_to
  target: '[[reward-model-overestimation-undermines-rl-factuality]]'
  target_id: mechanism:reward-model-overestimation-undermines-rl-factuality
  confidence: high
- type: related_to
  target: '[[flame-factuality-aware-alignment]]'
  target_id: method:flame-factuality-aware-alignment
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[alignment-tax]]'
  target_id: term:alignment-tax
  confidence: high
---

On Llama-2 70B, standard SFT+DPO shifts Bio FActScore from 44.7 to 42.3 while increasing error count from 26.8 to 35.0 and inflating average response length from 1221 to 1494 tokens. Llama-2-Chat 70B (proprietary alignment) reaches 33.2 FActScore with 43.6 errors per response despite 66.2% Alpaca Eval win rate. The FLAME paper attributes this to the instruction-following reward preferring longer, more detailed responses, which stimulates production of more factual claims and therefore more erroneous ones. Factuality-only DPO (DPO^fact) produces shorter responses (1166 tokens) and higher FActScore but degrades instruction following, indicating the helpfulness and factuality signals conflict under a single reward.
