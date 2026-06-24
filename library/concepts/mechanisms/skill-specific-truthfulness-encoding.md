---
aliases:
- task-specific truthfulness features
- no universal truth representation
- multifaceted truthfulness encoding
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:skill-specific-truthfulness-encoding
  type: mechanism
  status: canonical
cause: "Probing classifiers trained on exact-answer-token representations of one task or skill cluster"
effect: "Failure to generalize to tasks requiring different underlying skills, with cross-task AUC advantage over logit-min-exact collapsing to near zero for most cross-cluster pairs"
polarity: prevents
related:
- '[[2410.02707--llms-know-more-than-they-show]]'
- '[[generation-discrimination-gap]]'
- '[[truth-direction]]'
- '[[exact-answer-token-probing]]'
- '[[p-ik-ood-generalization-gap]]'
- '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
relationships:
- type: supported_by
  target: '[[2410.02707--llms-know-more-than-they-show]]'
  target_id: paper:2410.02707
  confidence: high
- type: related_to
  target: '[[generation-discrimination-gap]]'
  target_id: term:generation-discrimination-gap
  confidence: high
- type: related_to
  target: '[[truth-direction]]'
  target_id: term:truth-direction
  confidence: high
- type: related_to
  target: '[[exact-answer-token-probing]]'
  target_id: method:exact-answer-token-probing
  confidence: high
- type: related_to
  target: '[[p-ik-ood-generalization-gap]]'
  target_id: mechanism:p-ik-ood-generalization-gap
  confidence: high
- type: related_to
  target: '[[verbalized-prob-generalizes-logit-overfits-distribution-shift]]'
  target_id: mechanism:verbalized-prob-generalizes-logit-overfits-distribution-shift
  confidence: high
---

Orgad et al. (2024) show that probing classifiers learn skill-specific truthfulness features rather than a universal internal truth representation. Within-cluster generalization (e.g., factual retrieval tasks: TriviaQA, HotpotQA, Movies; or commonsense tasks: Winobias, Winogrande, MNLI) does occur, but across clusters the apparent generalization is explained by output-logit correlation rather than deeper internal encoding. After subtracting the logit-min-exact baseline performance, the probe's advantage is near zero for most cross-cluster pairs (Figure 3b, §4). This contradicts Marks and Tegmark (2023) and Slobodkin et al. (2023), who argued for a universal truthfulness direction.
