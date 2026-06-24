---
aliases:
- diversity collapse
- post-training diversity collapse
- semantic collapse
tags:
- kg/term
- concept
- term
kg:
  id: term:output-diversity-collapse
  type: term
  status: canonical
area: terms
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[supervised-finetuning]]'
- '[[direct-preference-optimization]]'
- '[[kl-divergence-penalty]]'
- '[[decoding-randomness]]'
- '[[hallucination]]'
- '[[self-consistency]]'
relationships:
- type: proposed_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: medium
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: medium
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: medium
- type: related_to
  target: '[[decoding-randomness]]'
  target_id: term:decoding-randomness
  confidence: medium
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: medium
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: medium
---

The reduction in statistical spread of model outputs after post-training, measured along lexical (EAD), semantic (SBERT), logical (NLI), and effective-mode (Vendi Score) axes. Post-trained models generate outputs that occupy a narrower region of output space than their base counterparts, undermining inference-time scaling methods that rely on varied samples.

**Why it matters here:** Limits self-consistency, pass@k, and majority-voting gains. Risks homogenizing model outputs on creative and value-laden tasks where diverse perspectives are intrinsically valuable.

**Lineage:** Studied systematically by Karouzos et al. (2604.16027) who traced it through three OLMo 3 post-training lineages; earlier work by Kirk et al. (2024), Dang et al. (2025), and Peeperkorn et al. (2025) attributed collapse to specific methods without separating data composition.
