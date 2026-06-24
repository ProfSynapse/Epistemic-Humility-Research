---
aliases:
- automated preference DPO reduces hallucination
- factuality preference DPO reduces error rate
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:dpo-on-automated-factuality-pairs-reduces-hallucination
  type: mechanism
  status: canonical
cause: "DPO training on preference pairs ranked by automated factuality scoring (reference-based or reference-free), constructed without human annotation"
effect: "Fraction of correct atomic facts in long-form generation increases and absolute count of incorrect facts decreases, outperforming both RLHF chat baselines and inference-time decoding interventions"
polarity: decreases
related:
- '[[2311.08401--finetuning-for-factuality]]'
- '[[direct-preference-optimization]]'
- '[[facttune-fs]]'
- '[[facttune-mc]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[hallucination]]'
- '[[rlhf-reduces-closed-domain-hallucination]]'
- '[[factscore]]'
relationships:
- type: supported_by
  target: '[[2311.08401--finetuning-for-factuality]]'
  target_id: paper:2311.08401
  confidence: high
- type: related_to
  target: '[[direct-preference-optimization]]'
  target_id: method:direct-preference-optimization
  confidence: high
- type: related_to
  target: '[[facttune-fs]]'
  target_id: method:facttune-fs
  confidence: high
- type: related_to
  target: '[[facttune-mc]]'
  target_id: method:facttune-mc
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[hallucination]]'
  target_id: term:hallucination
  confidence: high
- type: related_to
  target: '[[rlhf-reduces-closed-domain-hallucination]]'
  target_id: mechanism:rlhf-reduces-closed-domain-hallucination
  confidence: high
- type: related_to
  target: '[[factscore]]'
  target_id: metric:factscore
  confidence: high
---

By coupling automated factuality scoring (either FactScore-based or max-confidence-based) with DPO's contrastive loss, the model learns to prefer the completion style that produces verifiably correct atomic claims. Because the preference signal is derived from factual accuracy rather than human stylistic preference, the DPO update steers the policy specifically toward fact-conservative generation. Tian et al. show this produces at least 23% improvement in % Correct over RLHF models on biographies and at least 12% on medical QA, with the headline result being a 58% reduction in biography error rate relative to Llama-2-Chat at 7B scale (Table 2, Section 4.1).
