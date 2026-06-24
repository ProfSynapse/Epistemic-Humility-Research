---
aliases:
- RLHF mode collapse
- RL training collapses output diversity
- RLHF per-input diversity reduction
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:rlhf-rl-optimisation-collapses-per-input-diversity
  type: mechanism
  status: canonical
cause: "On-policy RL optimisation (PPO) of a language model against a reward model, as in RLHF fine-tuning"
effect: "Substantially reduced syntactic (EAD) and semantic (Sentence-BERT) diversity of outputs sampled for a single input; also reduced but smaller cross-input diversity reduction; NLI (logical) diversity unaffected"
polarity: decreases
related:
- '[[2310.06452--rlhf-generalisation-diversity]]'
- '[[reinforcement-learning-from-human-feedback]]'
- '[[supervised-finetuning]]'
- '[[best-of-n-sampling]]'
- '[[expectation-adjusted-distinct-ngrams]]'
- '[[kl-divergence-penalty]]'
- '[[rlhf-generalisation-advantage-scales-with-shift-severity]]'
- '[[proximal-policy-optimization]]'
relationships:
- type: supported_by
  target: '[[2310.06452--rlhf-generalisation-diversity]]'
  target_id: paper:2310.06452
  confidence: high
- type: related_to
  target: '[[reinforcement-learning-from-human-feedback]]'
  target_id: method:reinforcement-learning-from-human-feedback
  confidence: high
- type: related_to
  target: '[[supervised-finetuning]]'
  target_id: method:supervised-finetuning
  confidence: high
- type: related_to
  target: '[[best-of-n-sampling]]'
  target_id: method:best-of-n-sampling
  confidence: high
- type: related_to
  target: '[[expectation-adjusted-distinct-ngrams]]'
  target_id: metric:expectation-adjusted-distinct-ngrams
  confidence: high
- type: related_to
  target: '[[kl-divergence-penalty]]'
  target_id: term:kl-divergence-penalty
  confidence: high
- type: related_to
  target: '[[rlhf-generalisation-advantage-scales-with-shift-severity]]'
  target_id: mechanism:rlhf-generalisation-advantage-scales-with-shift-severity
  confidence: high
- type: related_to
  target: '[[proximal-policy-optimization]]'
  target_id: method:proximal-policy-optimization
  confidence: high
---

Kirk et al. (2023) measure per-input and across-input diversity for SFT, BoN, and RLHF on summarisation. RLHF has much lower per-input diversity than SFT on EAD and Sentence-BERT. The across-input gap is smaller. Critically, BoN (which uses the same reward model as RLHF but no RL training) shows similar or higher across-input diversity than SFT on both metrics, ruling out reward-model filtering as the cause of collapse. This implicates the RL optimisation step specifically. NLI diversity does not differ meaningfully. Increasing the KL penalty fails to recover diversity while also degrading performance (Section 6.3), suggesting the tension is not addressable via this regulariser.
