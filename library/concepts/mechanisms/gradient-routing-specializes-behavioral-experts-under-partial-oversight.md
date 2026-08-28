---
aliases:
- Gradient routing specializes behavioral experts under partial oversight
- Partial labels localize Diamond and Ghost policies
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:gradient-routing-specializes-behavioral-experts-under-partial-oversight
  type: mechanism
  status: canonical
cause: "Observed Diamond and Ghost terminal outcomes route policy gradients to separate experts while unlabeled episodes use ordinary REINFORCE updates."
effect: "The experts specialize by outcome, allowing fixed selection of the Diamond expert to avoid oversight-conditioned reward exploitation."
polarity: enables
related:
- '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
- '[[gradient-routing]]'
- '[[mixture-of-experts]]'
relationships:
- type: supported_by
  target: '[[2410.04332--gradient-routing-masking-gradients-localize-computation-neural]]'
  target_id: paper:2410.04332
  confidence: high
- type: related_to
  target: '[[gradient-routing]]'
  target_id: method:gradient-routing
  confidence: high
- type: related_to
  target: '[[mixture-of-experts]]'
  target_id: method:mixture-of-experts
  confidence: high
---

In the 5 by 5 gridworld, the routed policy remains effective at low oversight, while naive behavioral training changes behavior depending on whether oversight is present. This result is limited to the toy environment and a policy whose expert ablation remains coherent.
