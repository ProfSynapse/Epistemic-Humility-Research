---
aliases:
- TIAR outperforms static ternary reward on AbstentionBench
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:trajectory-informed-reweighting-improves-abstention-f1
  type: mechanism
  status: canonical
cause: "Replacing the static ternary-reward GRPO abstention objective ([[truthrl]], lambda=0) with [[trajectory-informed-advantage-reweighting]] at full inversion (lambda=1.0), holding the base checkpoint, training data, and GRPO configuration fixed"
effect: "Average abstention F1 across the AbstentionBench suite improves (71.9 vs. a lower average for the static baseline), outperforming the static ternary reward on 17 of 31 benchmark datasets for F1 and 11 of 24 for accuracy, while accuracy is nearly preserved (72.6 vs. 72.7)"
polarity: increases
related:
- '[[2605.25850--tiar-trajectory-informed-advantage-reweighting-llm-abstention]]'
- '[[trajectory-informed-advantage-reweighting]]'
- '[[truthrl]]'
- '[[abstentionbench]]'
relationships:
- type: supported_by
  target: '[[2605.25850--tiar-trajectory-informed-advantage-reweighting-llm-abstention]]'
  target_id: paper:2605.25850
  confidence: high
- type: related_to
  target: '[[trajectory-informed-advantage-reweighting]]'
  target_id: method:trajectory-informed-advantage-reweighting
  confidence: high
- type: related_to
  target: '[[truthrl]]'
  target_id: method:truthrl
  confidence: high
- type: related_to
  target: '[[abstentionbench]]'
  target_id: dataset:abstentionbench
  confidence: high
---

Pan et al. (2026) ablate the trajectory-inversion weight lambda in TIAR on Llama-3.1-8B-Instruct, where lambda=0 reduces exactly to the static ternary-reward baseline (TruthRL). Across the full AbstentionBench suite (31 dataset subsets), lambda=1.0 achieves the highest average abstention F1 (71.9) and nearly the highest average accuracy (72.6, versus 72.7 for lambda=0), outperforming lambda=0 on 17 of 31 datasets for F1 and 11 of 24 for accuracy (Section 5.2, Table 3). The relationship is non-monotonic: an intermediate weight (lambda=0.3) causes a collapse in both F1 and accuracy, showing a small inversion weight destabilizes training without providing sufficient signal, while full inversion (lambda=1.0) gives the best balance of abstention quality and accuracy preservation. Against the full baseline set (R-Tuning SFT, Rejection Fine-Tuning, DPO, and TruthRL, all on the same instruct checkpoint), the headline result is state-of-the-art abstention F1 in five of six AbstentionBench evaluation categories while fully preserving baseline accuracy (Abstract).
