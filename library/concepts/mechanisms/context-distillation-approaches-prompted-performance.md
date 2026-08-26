---
aliases:
- Context-distilled 52B model near-matches its own prompted version
tags:
- kg/mechanism
- concept
- mechanism
kg:
  id: mechanism:context-distillation-approaches-prompted-performance
  type: mechanism
  status: canonical
cause: "Applying [[context-distillation]] to internalize an HHH prompt into a 13B or 52B language model's weights, then comparing the context-distilled model against the same model with the prompt still present at inference time"
effect: "Human raters can weakly distinguish the two, preferring the prompted version only about 53% of the time, indicating the distilled model reproduces most but not quite all of the prompted model's behavior"
polarity: enables
related:
- '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
- '[[context-distillation]]'
- '[[hhh-helpful-honest-harmless]]'
relationships:
- type: supported_by
  target: '[[2112.00861--general-language-assistant-as-laboratory-alignment]]'
  target_id: paper:2112.00861
  confidence: high
- type: related_to
  target: '[[context-distillation]]'
  target_id: method:context-distillation
  confidence: high
- type: related_to
  target: '[[hhh-helpful-honest-harmless]]'
  target_id: term:hhh-helpful-honest-harmless
  confidence: high
---

Askell et al. (2021) compare fully HHH-prompted 13B and 52B models against context-distilled versions of the same models (the prompt's conditional distribution internalized via a KL-divergence fine-tuning loss) in a human-rated Elo-style comparison. Contractors preferred the fully prompted model over its context-distilled counterpart only about 53% of the time, giving weak evidence that context distillation degrades performance somewhat relative to keeping the prompt in context, but the two are close to indistinguishable to human raters (Section 2.2, discussion following Figure 9/10). A much shorter prompt (a single example conversation) performed noticeably worse than either the full prompt or its distillation, showing the degradation from distillation is small compared to the gap from an under-specified prompt. On the adversarial TruthfulQA MC1 evaluation, the context-distilled prompt also slightly improved performance for the largest models relative to no prompt (Section 2.2).
