---
aliases:
- correct-answer diversity determines majority-vote benefit
- collapsed correct outputs saturate majority voting
- diversity floor limits inference scaling
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:majority-voting-gain-scales-with-correct-answer-diversity
  type: mechanism
  status: canonical
cause: "Post-training collapses the distribution of correct outputs so that repeated samples are near-identical, providing no independent signal for majority voting"
effect: "Think gains only +0.4% from majority-vote@16 on GSM8K; Base gains +24% and RL-Zero +22-26% from the same sample budget; on tasks where the dominant mode is wrong (TruthfulQA), majority voting hurts all models"
polarity: decreases
related:
- '[[2604.16027--posttraining-diversity-collapse]]'
- '[[output-diversity-collapse]]'
- '[[self-consistency]]'
- '[[quality-filtered-diversity-decomposition]]'
- '[[vendi-score]]'
- '[[rlvr-post-training-degrades-abstention]]'
relationships:
- type: supported_by
  target: '[[2604.16027--posttraining-diversity-collapse]]'
  target_id: paper:2604.16027
  confidence: high
- type: related_to
  target: '[[output-diversity-collapse]]'
  target_id: term:output-diversity-collapse
  confidence: high
- type: related_to
  target: '[[self-consistency]]'
  target_id: method:self-consistency
  confidence: high
- type: related_to
  target: '[[quality-filtered-diversity-decomposition]]'
  target_id: method:quality-filtered-diversity-decomposition
  confidence: high
- type: related_to
  target: '[[vendi-score]]'
  target_id: metric:vendi-score
  confidence: high
- type: related_to
  target: '[[rlvr-post-training-degrades-abstention]]'
  target_id: mechanism:rlvr-post-training-degrades-abstention
  confidence: high
---

Correct-answer diversity, measured by D_correct (SBERT on correct outputs only) and V_correct (Vendi Score on correct outputs), determines how much additional samples contribute to majority voting. Think and Instruct converge to 1.3-1.6 effective Vendi modes among correct answers on most verifiable tasks. On MATH-Algebra, Think-not-thinking and RL-Zero-Math both reach 49% accuracy@1, but RL-Zero-Math has twice the correct-answer diversity and gains +15% from majority voting compared to +7% for Think-not-thinking. On TruthfulQA, the effect reverses: majority voting hurts all models because the model converges confidently onto the misconception the question was designed to test. High-accuracy models cluster near zero majority-vote gain; lower-accuracy models with diverse correct outputs benefit substantially.
